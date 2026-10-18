from PIL import Image

from lesson import Lesson, LessonSegment
from question import Question
from thumbnail_generator import THUMBNAIL_SIZE, generate_thumbnail


def sample_lesson(*, topic="Advanced Error Detection"):
    question = Question(
        subject="English",
        exam="Banking",
        topic=topic,
        difficulty="medium",
        question="Choose the sentence with the error.",
        choices=("He go to school.", "He goes to school.", "He going to school.", "He gone to school."),
        correct_answer="He goes to school.",
        explanation="The singular subject takes the verb 'goes'.",
        shortcut=None,
        source_type="original",
        source_reference=None,
    )
    return Lesson(
        lesson_type="practice",
        title=f"Banking English — {topic}: Practice",
        subject="English",
        exam="Banking",
        topic=topic,
        questions=(question,),
        segments=(
            LessonSegment(kind="question", question_index=0),
            LessonSegment(kind="answer", question_index=0),
        ),
    )


def test_generate_thumbnail_is_1280_by_720_png_below_upload_limit(tmp_path):
    path = generate_thumbnail(sample_lesson(), tmp_path / "thumbnail.png")

    assert path.exists()
    assert path.stat().st_size > 0
    assert path.stat().st_size < 2 * 1024 * 1024
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.size == THUMBNAIL_SIZE
        assert len(set(image.getdata())) > 10


def test_generate_thumbnail_handles_long_topic(tmp_path):
    lesson = sample_lesson(
        topic="Percentage and Successive Percentage Change with Shortcuts"
    )
    path = generate_thumbnail(lesson, tmp_path / "long-topic.png")

    with Image.open(path) as image:
        assert image.size == (1280, 720)


def test_generate_thumbnail_rejects_empty_questions(tmp_path):
    lesson = sample_lesson()
    lesson = Lesson(
        lesson_type=lesson.lesson_type,
        title=lesson.title,
        subject=lesson.subject,
        exam=lesson.exam,
        topic=lesson.topic,
        questions=(),
        segments=(),
    )

    import pytest

    with pytest.raises(ValueError, match="questions must not be empty"):
        generate_thumbnail(lesson, tmp_path / "bad.png")
