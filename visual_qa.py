from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

from visual_primitives import BACKGROUND


@dataclass(frozen=True)
class ImageQAResult:
    width: int
    height: int
    content_bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class VideoQAResult:
    width: int
    height: int
    duration_seconds: float
    has_audio: bool


def check_assets(paths) -> tuple[Path, ...]:
    checked = []
    for value in paths:
        path = Path(value)
        if not path.exists():
            raise RuntimeError(f"visual asset does not exist: {path}")
        if path.stat().st_size == 0:
            raise RuntimeError(f"visual asset is empty: {path}")
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:
            raise RuntimeError(f"visual asset is unreadable: {path}") from exc
        checked.append(path)
    return tuple(checked)


def check_image(
    path,
    *,
    expected_size: tuple[int, int],
    margin: int = 8,
    background=BACKGROUND,
) -> ImageQAResult:
    image_path = Path(path)
    if margin < 0:
        raise ValueError("margin must not be negative")
    if expected_size[0] <= 0 or expected_size[1] <= 0:
        raise ValueError("expected_size must be positive")

    check_assets((image_path,))
    with Image.open(image_path) as image:
        if image.size != expected_size:
            raise RuntimeError(
                f"visual size mismatch: got={image.size} expected={expected_size}"
            )
        rgb = image.convert("RGB")
        background_image = Image.new("RGB", rgb.size, background)
        bbox = ImageChops.difference(rgb, background_image).getbbox()
        if bbox is None:
            raise RuntimeError(f"visual scene is blank: {image_path}")
        left, top, right, bottom = bbox
        width, height = rgb.size
        if left < margin or top < margin or right > width - margin or bottom > height - margin:
            raise RuntimeError(
                f"visual content touches unsafe edge: {path}"
            )
        return ImageQAResult(
            width=width,
            height=height,
            content_bbox=(left, top, right, bottom),
        )


def _probe_video(path: Path) -> tuple[int, int, float, bool]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type,width,height",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError("Could not run ffprobe") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"ffprobe failed: {detail[:500]}")

    values = {}
    stream_types = set()
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "codec_type":
            stream_types.add(value.strip())
        else:
            values[key.strip()] = value.strip()

    try:
        width = int(values["width"])
        height = int(values["height"])
        duration = float(values["duration"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError("ffprobe returned incomplete video metadata") from exc

    if width <= 0 or height <= 0 or duration <= 0:
        raise RuntimeError("video metadata is invalid")
    return width, height, duration, "audio" in stream_types


def check_video(
    path,
    *,
    expected_size: tuple[int, int],
    expected_duration_seconds: float | None = None,
    duration_tolerance_seconds: float = 0.25,
) -> VideoQAResult:
    video_path = Path(path)
    if not video_path.exists():
        raise RuntimeError(f"video file does not exist: {video_path}")
    if video_path.stat().st_size == 0:
        raise RuntimeError(f"video file is empty: {video_path}")
    if duration_tolerance_seconds < 0:
        raise ValueError("duration_tolerance_seconds must not be negative")
    width, height, duration, has_audio = _probe_video(video_path)
    if (width, height) != expected_size:
        raise RuntimeError(
            f"video size mismatch: got={(width, height)} expected={expected_size}"
        )
    if not has_audio:
        raise RuntimeError("final video has no audio stream")
    if expected_duration_seconds is not None and abs(duration - expected_duration_seconds) > duration_tolerance_seconds:
        raise RuntimeError(
            f"video duration mismatch: video={duration:.3f}s expected={expected_duration_seconds:.3f}s"
        )
    return VideoQAResult(width, height, round(duration, 6), has_audio)
