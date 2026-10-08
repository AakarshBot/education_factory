import math
import struct
import subprocess
import wave

import pytest

from lesson import Lesson, LessonSegment
from question import Question
from shorts_renderer import SHORT_SIZE, render_short, _portrait_scene
from visual_qa import check_image


def lesson():
    q=Question(
        subject="maths", exam="SSC CGL", topic="percentages", difficulty="medium",
        question="25% of 240 is?", choices=("60","70","80","90"), correct_answer="60",
        explanation="25 percent is one fourth. One fourth of 240 is 60.",
        shortcut="25% means divide by four.", source_type="original", source_reference=None,
    )
    return Lesson(
        lesson_type="timed_test", title="Short", subject="maths", exam="SSC CGL", topic="percentages",
        questions=(q,),
        segments=(
            LessonSegment(kind="question",question_index=0),
            LessonSegment(kind="timer",question_index=0,duration_seconds=1),
            LessonSegment(kind="answer",question_index=0),
            LessonSegment(kind="explanation",question_index=0),
        ),
    )


def audio(path,duration=1.6):
    rate=8000
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        for i in range(int(rate*duration)):
            value=int(8000*math.sin(2*math.pi*440*i/rate))
            w.writeframesraw(struct.pack("<h",value))


def test_portrait_scenes_pass_visual_qa(tmp_path):
    sample = lesson()
    for index in range(len(sample.segments)):
        image = _portrait_scene(sample, index)
        path = tmp_path / f"scene_{index}.png"
        image.save(path, format="PNG", optimize=False)
        result = check_image(path, expected_size=SHORT_SIZE)
        assert result.content_bbox[0] >= 8
        assert result.content_bbox[1] >= 8
        assert result.content_bbox[2] <= SHORT_SIZE[0] - 8
        assert result.content_bbox[3] <= SHORT_SIZE[1] - 8


def test_render_short_creates_9_by_16_mp4(tmp_path):
    a=tmp_path/"audio.wav"; out=tmp_path/"short.mp4"
    audio(a,1.6)
    result=render_short(lesson(),a,out,[0,1,2,3],[0.4,0.4,0.4,0.4],fps=10)
    assert result==out and out.exists() and out.stat().st_size>0
    probe=subprocess.run(
        ["ffprobe","-v","error","-show_entries","stream=codec_type,width,height","-show_entries","format=duration","-of","default=noprint_wrappers=1",str(out)],
        capture_output=True,text=True,check=True)
    assert "codec_type=video" in probe.stdout
    assert "width=1080" in probe.stdout and "height=1920" in probe.stdout
    duration=float(next(x.split("=",1)[1] for x in probe.stdout.splitlines() if x.startswith("duration=")))
    assert abs(duration-1.6)<=0.15


def test_render_short_rejects_mismatched_scene_durations(tmp_path):
    a=tmp_path/"audio.wav"; audio(a,1.0)
    with pytest.raises(ValueError,match="scene_durations must match"):
        render_short(lesson(),a,tmp_path/"out.mp4",[0,1],[1.0])


def test_render_short_rejects_bad_segment_index(tmp_path):
    a=tmp_path/"audio.wav"; audio(a,0.5)
    with pytest.raises(IndexError,match="segment index"):
        render_short(lesson(),a,tmp_path/"out.mp4",[99],[0.5])


def test_render_short_rejects_empty_selection(tmp_path):
    a=tmp_path/"audio.wav"; audio(a,0.5)
    with pytest.raises(ValueError,match="segment_indices"):
        render_short(lesson(),a,tmp_path/"out.mp4",[],[])
