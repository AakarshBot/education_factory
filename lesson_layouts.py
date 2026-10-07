from __future__ import annotations

from PIL import Image, ImageDraw

from lesson import Lesson, LessonSegment
from visual_primitives import (
    ACCENT,
    BACKGROUND,
    BORDER,
    DEFAULT_SIZE,
    MUTED,
    SURFACE,
    draw_answer_reveal,
    _font,
    draw_calculation_step,
    draw_choices,
    draw_highlighted_text,
    draw_progress,
    draw_question_card,
    draw_score_result,
    draw_timer,
)

def _canvas(size):
    return Image.new("RGB", size, BACKGROUND)

def _question(lesson, segment, image):
    question = lesson.questions[segment.question_index]
    return question, ImageDraw.Draw(image)

def _explanation_lines(text):
    parts = []
    for piece in text.replace("।", ".").split("."):
        piece = piece.strip()
        if piece:
            parts.append(piece)
    return parts or [text]

def _draw_label(draw, text, xy, size=28, fill=ACCENT):
    draw.text(xy, text, fill=fill, font=_font(size, True))

def _question_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    q, draw = _question(lesson, segment, image)
    total = len(lesson.questions)
    index = segment.question_index + 1

    if lesson.lesson_type == "practice":
        draw_question_card(image, q.question, (110, 90, size[0] - 110, 500), question_number=index, total_questions=total)
        draw_choices(image, q.choices, (110, 545, size[0] - 110, 980))
    elif lesson.lesson_type == "timed_test":
        draw_progress(image, index - 1, total, (110, 48, size[0] - 270, 70))
        draw_question_card(image, q.question, (110, 110, 1450, 515), question_number=index, total_questions=total)
        draw_timer(image, 15, (1660, 190), radius=92)
        draw_choices(image, q.choices, (110, 555, size[0] - 110, 1000))
    elif lesson.lesson_type == "concept_practice":
        draw_question_card(image, q.question, (110, 310, size[0] - 110, 690), question_number=index, total_questions=total)
        draw_choices(image, q.choices, (110, 720, size[0] - 110, 1010))
    elif lesson.lesson_type == "pyq_analysis":
        _draw_label(draw, "PREVIOUS-YEAR QUESTION", (110, 55), 30, ACCENT)
        _draw_label(draw, q.source_reference or "Source", (110, 92), 24, MUTED)
        draw_question_card(image, q.question, (110, 145, 1060, 690), question_number=index, total_questions=total)
        draw_choices(image, q.choices, (1110, 145, size[0] - 110, 690))
        draw_progress(image, index, total, (110, 780, 1600, 815))
    else:
        draw_progress(image, index - 1, total, (180, 55, 1660, 82))
        draw_question_card(image, q.question, (180, 135, size[0] - 180, 570), question_number=index, total_questions=total)
        draw_choices(image, q.choices, (300, 635, size[0] - 300, 1000))
    return image

def _answer_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    q, draw = _question(lesson, segment, image)
    draw_question_card(image, q.question, (120, 90, size[0] - 120, 430), question_number=segment.question_index + 1, total_questions=len(lesson.questions))
    draw_answer_reveal(image, f"Correct answer: {q.correct_answer}", (360, 510, size[0] - 360, 820))
    draw_progress(image, segment.question_index + 1, len(lesson.questions), (360, 890, size[0] - 430, 920))
    return image

def _explanation_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    q, _ = _question(lesson, segment, image)
    draw_answer_reveal(image, f"Answer: {q.correct_answer}", (110, 80, 760, 330))
    draw_calculation_step(image, _explanation_lines(q.explanation), (820, 80, size[0] - 110, 860))
    draw_progress(image, segment.question_index + 1, len(lesson.questions), (110, 930, size[0] - 280, 960))
    return image

def _shortcut_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    q, draw = _question(lesson, segment, image)
    _draw_label(draw, "QUICK METHOD", (150, 115), 34, ACCENT)
    draw_highlighted_text(
        image,
        (("Remember: ", False), (q.shortcut or "", True)),
        (150, 200, size[0] - 150, 430),
        font_size=52,
    )
    draw_answer_reveal(image, f"Answer: {q.correct_answer}", (520, 530, 1400, 820))
    return image

def _concept_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((130, 150, size[0] - 130, 760), 28, fill=SURFACE, outline=BORDER, width=2)
    _draw_label(d, "CONCEPT", (172, 188), 28, ACCENT)
    draw_highlighted_text(image, ((segment.text or "", False),), (172, 265, size[0] - 172, 700), font_size=52)
    draw_highlighted_text(image, (("Concept first -> then practice", False),), (300, 850, 1620, 930), font_size=32)
    return image

def _source_scene(lesson: Lesson, segment: LessonSegment, size):
    image = _canvas(size)
    draw_highlighted_text(
        image,
        (("SOURCE", True), ("  ", False), (segment.source_reference or "Unavailable", False)),
        (160, 150, size[0] - 160, 300),
        font_size=46,
    )
    draw_highlighted_text(
        image,
        (("This question is being analysed with its source context.", False),),
        (220, 430, size[0] - 220, 620),
        font_size=40,
    )
    return image

def render_lesson_scene(lesson: Lesson, segment_index: int, *, size=DEFAULT_SIZE) -> Image.Image:
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if not 0 <= segment_index < len(lesson.segments):
        raise IndexError("segment_index is out of range")

    segment = lesson.segments[segment_index]
    if segment.kind == "question":
        return _question_scene(lesson, segment, size)
    if segment.kind == "answer":
        return _answer_scene(lesson, segment, size)
    if segment.kind == "explanation":
        return _explanation_scene(lesson, segment, size)
    if segment.kind == "shortcut":
        return _shortcut_scene(lesson, segment, size)
    if segment.kind == "concept":
        return _concept_scene(lesson, segment, size)
    if segment.kind == "source":
        return _source_scene(lesson, segment, size)
    if segment.kind == "timer":
        image = _canvas(size)
        draw_timer(image, segment.duration_seconds or 15, (size[0] // 2, size[1] // 2), radius=min(size) // 8)
        draw_progress(image, segment.question_index + 1, len(lesson.questions), (300, size[1] - 100, size[0] - 400, size[1] - 70))
        return image
    if segment.kind == "score":
        image = _canvas(size)
        draw_score_result(image, 0, len(lesson.questions), (size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4))
        return image
    raise ValueError(f"unsupported lesson segment kind: {segment.kind}")
