import math
import struct
import subprocess
import wave

import pytest
from PIL import Image

from visual_qa import check_assets, check_image, check_video
from visual_primitives import BACKGROUND


def write_png(path, size=(320, 180), touch_edge=False):
    image = Image.new("RGB", size, BACKGROUND)
    pixels = image.load()
    for x in range(20, 100):
        for y in range(20, 80):
            pixels[x, y] = (255, 255, 255)
    if touch_edge:
        pixels[0, 20] = (255, 255, 255)
    image.save(path, format="PNG", optimize=False)


def write_wav(path, duration=0.5):
    rate = 8000
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for i in range(int(rate * duration)):
            value = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            wav.writeframesraw(struct.pack("<h", value))


def test_check_assets_and_image_bounds(tmp_path):
    path = tmp_path / "scene.png"
    write_png(path)
    assert check_assets((path,)) == (path,)
    result = check_image(path, expected_size=(320, 180))
    assert result.content_bbox == (20, 20, 100, 80)


def test_check_image_rejects_edge_content(tmp_path):
    path = tmp_path / "edge.png"
    write_png(path, touch_edge=True)
    with pytest.raises(RuntimeError, match="unsafe edge"):
        check_image(path, expected_size=(320, 180))


def test_check_assets_rejects_missing_and_invalid(tmp_path):
    with pytest.raises(RuntimeError, match="does not exist"):
        check_assets((tmp_path / "missing.png",))
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(RuntimeError, match="unreadable"):
        check_assets((bad,))


def test_check_video_validates_geometry_audio_and_duration(tmp_path):
    scene = tmp_path / "scene.png"
    audio = tmp_path / "audio.wav"
    video = tmp_path / "video.mp4"
    write_png(scene)
    write_wav(audio)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-i", str(scene), "-i", str(audio),
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(video),
        ],
        check=True,
    )
    result = check_video(video, expected_size=(320, 180), expected_duration_seconds=0.5)
    assert result.width == 320
    assert result.height == 180
    assert result.has_audio
    assert abs(result.duration_seconds - 0.5) <= 0.25


def test_check_video_rejects_missing_audio_stream(tmp_path):
    scene = tmp_path / "scene.png"
    video = tmp_path / "silent.mp4"
    write_png(scene)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-i", str(scene), "-t", "0.5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
        ],
        check=True,
    )
    with pytest.raises(RuntimeError, match="no audio stream"):
        check_video(video, expected_size=(320, 180))
