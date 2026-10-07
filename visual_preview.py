from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from lesson import Lesson, LessonSegment
from lesson_assembler import assemble_lesson
from lesson_layouts import render_lesson_scene
from question import Question
from shorts_renderer import SHORT_SIZE, _portrait_scene
from visual_primitives import BACKGROUND, INK, _font


SHEET_BACKGROUND = BACKGROUND
LANDSCAPE_THUMB = (560, 315)
PORTRAIT_THUMB = (360, 640)


def _sample_question() -> Question:
    return Question(
        subject="Reasoning",
        exam="Banking",
        topic="Syllogism",
        difficulty="medium",
        question="Statements: All pens are books. Some books are files. Which conclusion is definitely true?",
        choices=(
            "All pens are books",
            "All books are pens",
            "Some pens are files",
            "No book is a file",
        ),
        correct_answer="All pens are books",
        explanation="The first statement directly says every pen belongs to the group of books. The second statement only establishes that some books are files, so nothing definite connects pens to files.",
        shortcut="Lock the universal statement first. Do not assume overlap unless the statements force it.",
        source_type="original",
        source_reference=None,
    )


def _lessons() -> dict[str, Lesson]:
    question = _sample_question()
    pyq = Question(
        **{**question.to_dict(), "source_type": "pyq", "source_reference": "Banking exam — sample PYQ"}
    )
    return {
        "Practice": assemble_lesson((question,), lesson_type="practice"),
        "Timed test": assemble_lesson((question,), lesson_type="timed_test"),
        "Concept + practice": assemble_lesson(
            (question,),
            lesson_type="concept_practice",
            concept_summary="In syllogism, accept only conclusions that are forced by the statements. Never assume extra relationships.",
        ),
        "PYQ analysis": assemble_lesson((pyq,), lesson_type="pyq_analysis"),
        "Revision": assemble_lesson((question,), lesson_type="revision"),
    }


def _first_index(lesson: Lesson, kind: str) -> int:
    for index, segment in enumerate(lesson.segments):
        if segment.kind == kind:
            return index
    raise RuntimeError(f"sample lesson has no {kind} segment")


def _labelled_canvas(size: tuple[int, int], label: str) -> Image.Image:
    canvas = Image.new("RGB", size, SHEET_BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    font = _font(24, True)
    draw.text((20, 14), label, font=font, fill=INK)
    return canvas


def _sheet(items: list[tuple[str, Image.Image]], thumbnail: tuple[int, int], columns: int) -> Image.Image:
    label_height = 48
    rows = (len(items) + columns - 1) // columns
    width = columns * thumbnail[0]
    height = rows * (thumbnail[1] + label_height)
    sheet = Image.new("RGB", (width, height), SHEET_BACKGROUND)
    draw = ImageDraw.Draw(sheet)

    for position, (label, source) in enumerate(items):
        row, column = divmod(position, columns)
        x = column * thumbnail[0]
        y = row * (thumbnail[1] + label_height)
        draw.text((x + 12, y + 10), label, font=_font(22, True), fill=INK)
        fitted = ImageOps.contain(source, thumbnail)
        px = x + (thumbnail[0] - fitted.width) // 2
        py = y + label_height + (thumbnail[1] - fitted.height) // 2
        sheet.paste(fitted, (px, py))

    return sheet


def build_preview(output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    lessons = _lessons()

    long_items: list[tuple[str, Image.Image]] = []
    for name, lesson in lessons.items():
        index = _first_index(lesson, "question")
        long_items.append((f"{name} / question", render_lesson_scene(lesson, index)))

    practice = lessons["Practice"]
    for kind in ("answer", "explanation", "shortcut"):
        long_items.append(
            (f"Practice / {kind}", render_lesson_scene(practice, _first_index(practice, kind)))
        )

    timed = lessons["Timed test"]
    long_items.append(
        ("Timed test / timer", render_lesson_scene(timed, _first_index(timed, "timer")))
    )

    pyq = lessons["PYQ analysis"]
    long_items.append(
        ("PYQ / source", render_lesson_scene(pyq, _first_index(pyq, "source")))
    )

    revision = lessons["Revision"]
    long_items.append(
        ("Revision / result", render_lesson_scene(revision, _first_index(revision, "question")))
    )

    short_items = []
    for name, lesson in lessons.items():
        index = _first_index(lesson, "question")
        short_items.append((f"{name} / question", _portrait_scene(lesson, index)))

    for kind in ("answer", "explanation", "shortcut"):
        short_items.append(
            (f"Practice / {kind}", _portrait_scene(practice, _first_index(practice, kind)))
        )

    long_path = output / "visual_preview_long.png"
    short_path = output / "visual_preview_short.png"
    _sheet(long_items, LANDSCAPE_THUMB, 3).save(long_path, "PNG", optimize=False)
    _sheet(short_items, PORTRAIT_THUMB, 2).save(short_path, "PNG", optimize=False)
    return long_path, short_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a visual QA contact sheet from the real lesson renderers."
    )
    parser.add_argument("--output-dir", default="output/visual_preview")
    args = parser.parse_args()

    long_path, short_path = build_preview(args.output_dir)
    print(f"Long-form preview: {long_path}")
    print(f"Shorts preview: {short_path}")


if __name__ == "__main__":
    main()
