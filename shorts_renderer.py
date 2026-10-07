from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from audio_qa import check_audio
from lesson import Lesson
from visual_qa import check_image, check_video
from visual_primitives import (
    ACCENT,
    BACKGROUND,
    BORDER,
    DEFAULT_SIZE,
    INK,
    MUTED,
    SURFACE,
    _font,
    draw_answer_reveal,
    draw_calculation_step,
    draw_choices,
    draw_highlighted_text,
    draw_progress,
    draw_question_card,
    draw_score_result,
    draw_timer,
)

SHORT_SIZE = (1080, 1920)
DEFAULT_FPS = 30


def _canvas():
    return Image.new("RGB", SHORT_SIZE, BACKGROUND)


def _label(draw, text, xy, *, size=30, fill=ACCENT):
    draw.text(xy, text, font=_font(size, True), fill=fill)


def _explanation_lines(text):
    pieces = [piece.strip() for piece in text.replace("।", ".").split(".") if piece.strip()]
    return pieces or [text]


def _portrait_scene(lesson: Lesson, segment_index: int) -> Image.Image:
    segment = lesson.segments[segment_index]
    image = _canvas()
    width, height = SHORT_SIZE
    total = len(lesson.questions)
    question = (
        lesson.questions[segment.question_index]
        if segment.question_index is not None
        else None
    )

    if segment.kind == "question":
        draw_question_card(
            image,
            question.question,
            (60, 120, width - 60, 700),
            question_number=segment.question_index + 1,
            total_questions=total,
        )
        draw_choices(image, question.choices, (60, 760, width - 60, 1550))
        draw_progress(image, segment.question_index + 1, total, (80, 1660, 820, 1692))
        return image

    if segment.kind == "timer":
        draw_timer(image, segment.duration_seconds or 15, (width // 2, 760), radius=150)
        draw_highlighted_text(
            image,
            (("Think before the answer.", False),),
            (180, 1030, width - 180, 1140),
            font_size=42,
        )
        draw_progress(image, segment.question_index + 1, total, (120, 1450, 820, 1482))
        return image

    if segment.kind == "answer":
        draw_answer_reveal(image, f"Correct answer: {question.correct_answer}", (80, 360, width - 80, 1050))
        draw_highlighted_text(
            image,
            (("Now see why it works.", False),),
            (140, 1190, width - 140, 1320),
            font_size=42,
        )
        draw_progress(image, segment.question_index + 1, total, (120, 1500, 820, 1532))
        return image

    if segment.kind == "explanation":
        draw_calculation_step(
            image,
            _explanation_lines(question.explanation),
            (60, 260, width - 60, 1300),
        )
        draw_answer_reveal(image, f"Answer: {question.correct_answer}", (100, 1400, width - 100, 1740))
        return image

    if segment.kind == "shortcut":
        _label(ImageDraw.Draw(image), "QUICK METHOD", (90, 260), size=36)
        draw_highlighted_text(
            image,
            (("Remember: ", False), (question.shortcut or "", True)),
            (90, 390, width - 90, 850),
            font_size=48,
        )
        draw_answer_reveal(image, f"Answer: {question.correct_answer}", (100, 1040, width - 100, 1390))
        return image

    if segment.kind == "concept":
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((60, 180, width - 60, 1500), 30, fill=SURFACE, outline=BORDER, width=2)
        _label(draw, "CONCEPT", (105, 230), size=32)
        draw_highlighted_text(
            image,
            ((segment.text or "", False),),
            (105, 340, width - 105, 1350),
            font_size=48,
        )
        return image

    if segment.kind == "source":
        draw = ImageDraw.Draw(image)
        _label(draw, "SOURCE", (90, 360), size=36)
        draw_highlighted_text(
            image,
            ((segment.source_reference or "Unavailable", False),),
            (90, 500, width - 90, 900),
            font_size=46,
        )
        return image

    if segment.kind == "score":
        draw_score_result(image, 0, total, (80, 520, width - 80, 1400))
        return image

    raise ValueError(f"unsupported lesson segment kind: {segment.kind}")


def render_short(
    lesson: Lesson,
    audio_path: str | Path,
    output_path: str | Path,
    segment_indices: list[int],
    scene_durations: list[float],
    *,
    fps: int = DEFAULT_FPS,
) -> Path:
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if not segment_indices:
        raise ValueError("segment_indices must not be empty")
    if len(segment_indices) != len(scene_durations):
        raise ValueError("scene_durations must match segment_indices")
    if any(index < 0 or index >= len(lesson.segments) for index in segment_indices):
        raise IndexError("segment index is out of range")
    if any(duration <= 0 for duration in scene_durations):
        raise ValueError("scene durations must be positive")
    if fps <= 0:
        raise ValueError("fps must be positive")

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
        with tempfile.TemporaryDirectory(prefix="education_factory_short_") as work:
            work_dir = Path(work)
            concat_file = work_dir / "scenes.ffconcat"
            lines = ["ffconcat version 1.0"]

            for position, index in enumerate(segment_indices):
                scene = _portrait_scene(lesson, index)
                scene_path = work_dir / f"scene_{position:04d}.png"
                scene.save(scene_path, format="PNG", optimize=False)
                check_image(scene_path, expected_size=SHORT_SIZE)
                lines.append(f"file '{scene_path.as_posix()}'")
                lines.append(f"duration {scene_durations[position]:.6f}")

            last_scene = work_dir / f"scene_{len(segment_indices) - 1:04d}.png"
            lines.append(f"file '{last_scene.as_posix()}'")
            concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            temp_output = output.with_name(output.name + ".tmp.mp4")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-i", str(audio),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", str(fps),
                    "-c:a", "aac",
                    "-t", f"{total_duration:.6f}",
                    "-movflags", "+faststart",
                    str(temp_output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                raise RuntimeError(f"Short render failed: {detail[:500]}")
            if not temp_output.exists() or temp_output.stat().st_size == 0:
                raise RuntimeError("Short render produced no video")
            check_video(temp_output, expected_size=SHORT_SIZE, expected_duration_seconds=total_duration)
            temp_output.replace(output)
    except OSError as exc:
        raise RuntimeError("Could not run FFmpeg for Shorts rendering") from exc

    return output
