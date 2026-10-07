from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image

from audio_qa import check_audio
from lesson import Lesson
from lesson_layouts import render_lesson_scene
from visual_qa import check_image, check_video

DEFAULT_FPS = 30


def _concat_path(path: Path) -> str:
    return "'" + path.as_posix().replace("'", "'\\''") + "'"


def render_long_form(
    lesson: Lesson,
    audio_path: str | Path,
    output_path: str | Path,
    scene_durations: list[float],
    *,
    size: tuple[int, int] = (1920, 1080),
    fps: int = DEFAULT_FPS,
) -> Path:
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if size[0] <= 0 or size[1] <= 0 or size[0] * 9 != size[1] * 16:
        raise ValueError("size must be 16:9")
    if fps <= 0:
        raise ValueError("fps must be positive")
    if len(scene_durations) != len(lesson.segments):
        raise ValueError("scene_durations must match lesson segment count")
    if any(duration <= 0 for duration in scene_durations):
        raise ValueError("scene durations must be positive")

    audio = Path(audio_path)
    output = Path(output_path)
    if not audio.exists() or audio.stat().st_size == 0:
        raise RuntimeError(f"audio file does not exist or is empty: {audio}")

    total_duration = round(sum(scene_durations), 6)
    check_audio(
        audio,
        expected_duration_seconds=total_duration,
        duration_tolerance_seconds=0.25,
    )

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="education_factory_video_") as work:
            work_dir = Path(work)
            concat_file = work_dir / "scenes.ffconcat"

            lines = ["ffconcat version 1.0"]
            for index in range(len(lesson.segments)):
                scene = render_lesson_scene(lesson, index, size=size)
                if scene.size != size:
                    raise RuntimeError(
                        f"scene {index} has wrong size: {scene.size}, expected {size}"
                    )
                scene_path = work_dir / f"scene_{index:04d}.png"
                scene.save(scene_path, format="PNG", optimize=False)
                check_image(scene_path, expected_size=size)
                lines.append(f"file {_concat_path(scene_path)}")
                lines.append(f"duration {scene_durations[index]:.6f}")

            last_scene = work_dir / f"scene_{len(lesson.segments) - 1:04d}.png"
            lines.append(f"file {_concat_path(last_scene)}")
            concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            temp_output = output.with_name(output.name + ".tmp.mp4")
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-i",
                str(audio),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                "-c:a",
                "aac",
                "-t",
                f"{total_duration:.6f}",
                "-movflags",
                "+faststart",
                str(temp_output),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                raise RuntimeError(f"Long-form render failed: {detail[:500]}")

            if not temp_output.exists() or temp_output.stat().st_size == 0:
                raise RuntimeError("Long-form render produced no video")

            check_video(temp_output, expected_size=size, expected_duration_seconds=total_duration)
            temp_output.replace(output)
    except OSError as exc:
        raise RuntimeError("Could not run FFmpeg for long-form rendering") from exc

    return output
