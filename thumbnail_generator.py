from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from lesson import Lesson
from visual_primitives import (
    ACCENT,
    BACKGROUND,
    BORDER,
    HIGHLIGHT,
    INK,
    MUTED,
    SURFACE,
    _fit_text,
    _font,
    draw_topic_visual,
)

THUMBNAIL_SIZE = (1280, 720)
MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024


def generate_thumbnail(lesson: Lesson, output_path: str | Path) -> Path:
    """Create a legible, topic-specific 16:9 thumbnail for a long-form lesson."""
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if not lesson.exam.strip() or not lesson.subject.strip() or not lesson.topic.strip():
        raise ValueError("lesson exam, subject, and topic must not be empty")
    if not lesson.questions:
        raise ValueError("lesson questions must not be empty")

    target = Path(output_path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", THUMBNAIL_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, THUMBNAIL_SIZE[0], 12), fill=ACCENT)
    draw.rounded_rectangle(
        (48, 42, 748, 675),
        radius=30,
        fill=SURFACE,
        outline=BORDER,
        width=2,
    )

    exam_label = f"{lesson.exam.strip().upper()} EXAM"
    draw.rounded_rectangle((82, 78, 590, 135), radius=20, fill=HIGHLIGHT)
    badge_lines, badge_size = _fit_text(
        draw, exam_label, 460, 37, 28, min_size=22, bold=True, spacing=3
    )
    y = 91
    for line in badge_lines:
        draw.text((108, y), line, font=_font(badge_size, True), fill=ACCENT)
        y += badge_size + 3

    subject_label = f"{lesson.subject.strip().upper()} PRACTICE"
    draw.text((86, 166), subject_label, font=_font(23, True), fill=MUTED)

    topic_lines, topic_size = _fit_text(
        draw,
        lesson.topic.strip(),
        594,
        255,
        74,
        min_size=42,
        bold=True,
        spacing=7,
    )
    y = 215
    for line in topic_lines:
        draw.text((84, y), line, font=_font(topic_size, True), fill=INK)
        y += topic_size + 7

    draw.rounded_rectangle((86, 500, 218, 509), radius=4, fill=ACCENT)
    draw.rounded_rectangle(
        (82, 535, 714, 635),
        radius=22,
        fill=HIGHLIGHT,
        outline=BORDER,
        width=1,
    )
    count_label = f"{len(lesson.questions)} QUESTIONS"
    draw.text((108, 550), count_label, font=_font(36, True), fill=INK)
    draw.text((110, 597), "SOLVED STEP BY STEP", font=_font(21, True), fill=ACCENT)

    draw_topic_visual(
        image,
        f"{lesson.subject.strip()} {lesson.topic.strip()}",
        lesson.questions[0].question,
        box=(780, 125, 1222, 575),
    )
    footer = "EXAM PRACTICE"
    footer_font = _font(20, True)
    footer_width = draw.textlength(footer, font=footer_font)
    draw.text(
        ((780 + 1222 - footer_width) / 2, 610),
        footer,
        font=footer_font,
        fill=MUTED,
    )

    image.save(target, format="PNG", optimize=True)
    if target.stat().st_size > MAX_THUMBNAIL_BYTES:
        target.unlink(missing_ok=True)
        raise RuntimeError("generated thumbnail exceeds YouTube's 2 MiB upload limit")

    with Image.open(target) as check:
        if check.format != "PNG" or check.size != THUMBNAIL_SIZE:
            raise RuntimeError("generated thumbnail has invalid format or dimensions")

    return target
