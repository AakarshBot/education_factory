import math
import struct
import wave

import pytest
from PIL import Image

import long_form_renderer
from lesson import Lesson, LessonSegment
from question import Question
from visual_primitives import BACKGROUND


def _lesson():
    q = Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="25% of 240 is?",
        choices=("60", "70", "80", "90"),
        correct_answer="60",
        explanation="25 percent is one fourth.",
        shortcut="Divide by four.",
        source_type="original",
        source_reference=None,
    )
    return Lesson(
        lesson_type="practice",
        title="Percentages Practice",
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        questions=(q,),
        segments=(
            LessonSegment(kind="question", question_index=0),
            LessonSegment(kind="answer", question_index=0),
        ),
    )


def _audio(path, duration=0.8):
    rate = 8000
    frames = int(rate * duration)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for i in range(frames):
            value = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            wav.writeframesraw(struct.pack("<h", value))


def test_render_long_form_creates_real_mp4(monkeypatch, tmp_path):
    lesson = _lesson()
    audio = tmp_path / "audio.wav"
    output = tmp_path / "lesson.mp4"
    _audio(audio)

    def fake_scene(_lesson, index, *, size):
        image = Image.new("RGB", size, BACKGROUND)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        inset = 12
        draw.rectangle(
            (inset, inset, size[0] - inset, size[1] - inset),
            fill=(255 if index == 0 else 240, 255, 255),
        )
        return image

    monkeypatch.setattr(long_form_renderer, "render_lesson_scene", fake_scene)
    result = long_form_renderer.render_long_form(
        lesson,
        audio,
        output,
        [0.4, 0.4],
        size=(320, 180),
        fps=10,
    )

    assert result == output
    assert output.exists() and output.stat().st_size > 0

    import subprocess

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "codec_type=video" in probe.stdout
    assert "width=320" in probe.stdout
    assert "height=180" in probe.stdout
    duration = float(next(line.split("=", 1)[1] for line in probe.stdout.splitlines() if line.startswith("duration=")))
    assert abs(duration - 0.8) <= 0.15


def test_render_long_form_rejects_scene_count_mismatch(tmp_path):
    lesson = _lesson()
    audio = tmp_path / "audio.wav"
    _audio(audio)
    with pytest.raises(ValueError, match="scene_durations must match"):
        long_form_renderer.render_long_form(lesson, audio, tmp_path / "out.mp4", [0.8])


def test_render_long_form_rejects_non_16_by_9_size(tmp_path):
    lesson = _lesson()
    audio = tmp_path / "audio.wav"
    _audio(audio)
    with pytest.raises(ValueError, match="16:9"):
        long_form_renderer.render_long_form(
            lesson, audio, tmp_path / "out.mp4", [0.4, 0.4], size=(320, 200)
        )
