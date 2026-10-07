from PIL import Image

from lesson_assembler import assemble_lesson
from question import Question
from lesson_layouts import render_lesson_scene

def question(source_type="original", source_reference=None):
    return Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="25% of 240 is what?",
        choices=("60", "70", "80", "90"),
        correct_answer="60",
        explanation="25 percent is one fourth. One fourth of 240 is 60.",
        shortcut="25% means divide by four.",
        source_type=source_type,
        source_reference=source_reference,
    )

def test_all_lesson_question_layouts_have_distinct_compositions():
    lessons = [
        assemble_lesson([question()], lesson_type="practice"),
        assemble_lesson([question()], lesson_type="timed_test"),
        assemble_lesson([question()], lesson_type="concept_practice", concept_summary="Percent means per hundred."),
        assemble_lesson([question("pyq", "SSC CGL 2024 Tier 1")], lesson_type="pyq_analysis"),
        assemble_lesson([question()], lesson_type="revision"),
    ]
    images = [render_lesson_scene(lesson, next(i for i,s in enumerate(lesson.segments) if s.kind=="question")) for lesson in lessons]
    assert all(image.size == (1920, 1080) for image in images)
    assert len({image.tobytes() for image in images}) == 5

def test_all_assembled_segment_kinds_render():
    lessons = [
        assemble_lesson([question()], lesson_type="practice"),
        assemble_lesson([question()], lesson_type="timed_test"),
        assemble_lesson([question()], lesson_type="concept_practice", concept_summary="Percent means per hundred."),
        assemble_lesson([question("pyq", "SSC CGL 2024 Tier 1")], lesson_type="pyq_analysis"),
    ]
    for lesson in lessons:
        for index in range(len(lesson.segments)):
            image = render_lesson_scene(lesson, index, size=(1280, 720))
            assert isinstance(image, Image.Image)
            assert image.size == (1280, 720)
