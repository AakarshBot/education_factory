from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SIZE = (1920, 1080)

BACKGROUND = (15, 20, 29)
SURFACE = (24, 31, 43)
SURFACE_2 = (31, 40, 54)
INK = (244, 247, 250)
MUTED = (154, 166, 182)
ACCENT = (74, 222, 160)
INFO = (103, 142, 255)
SUCCESS = (74, 222, 160)
DANGER = (248, 113, 113)
BORDER = (54, 66, 82)
HIGHLIGHT = (43, 61, 77)
SUCCESS_SURFACE = (22, 56, 46)
DANGER_SURFACE = (58, 35, 40)
GRID = (21, 27, 38)
SHADOW = (9, 13, 20)

DEV = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf" if os.name != "nt" else "C:/Windows/Fonts/NirmalaUI.ttf"
DEV_B = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if os.name != "nt" else "C:/Windows/Fonts/NirmalaUI-Bold.ttf"
LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" if os.name != "nt" else "C:/Windows/Fonts/arial.ttf"
LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if os.name != "nt" else "C:/Windows/Fonts/arialbd.ttf"


def _installed_font_candidates(*names):
    if os.name != "nt":
        return names
    roots = [
        "C:/Windows/Fonts",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft/Windows/Fonts"),
    ]
    candidates = list(names)
    for root in roots:
        if not root:
            continue
        try:
            for entry in os.scandir(root):
                if entry.is_file() and entry.name.lower().endswith((".ttf", ".otf", ".ttc")):
                    candidates.append(entry.path)
        except OSError:
            continue
    return tuple(dict.fromkeys(candidates))


DEV_FONTS = _installed_font_candidates(
    DEV, "C:/Windows/Fonts/Mangal.ttf", "C:/Windows/Fonts/Nirmala.ttf"
)
DEV_B_FONTS = _installed_font_candidates(
    DEV_B, "C:/Windows/Fonts/Mangalb.ttf", "C:/Windows/Fonts/Nirmalab.ttf"
) + DEV_FONTS
LAT_FONTS = _installed_font_candidates(LAT, "C:/Windows/Fonts/segoeui.ttf")
LAT_B_FONTS = _installed_font_candidates(LAT_B, "C:/Windows/Fonts/segoeuib.ttf") + LAT_FONTS


def _dev(text):
    return any("ऀ" <= c <= "ॿ" for c in text)


def _font(size, bold=False, dev=False):
    candidates = DEV_B_FONTS if dev and bold else DEV_FONTS if dev else LAT_B_FONTS if bold else LAT_FONTS
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    raise OSError("No suitable font is installed for the requested text")


def _measure(draw, text, size, bold):
    words = text.split()
    return sum(
        draw.textlength(word, font=_font(size, bold, _dev(word)))
        for word in words
    ) + max(0, len(words) - 1) * draw.textlength(
        " ", font=_font(size, bold)
    )


def _wrap(draw, text, size, bold, width):
    out = []
    line = ""
    for word in text.strip().split():
        test = word if not line else line + " " + word
        if _measure(draw, test, size, bold) <= width:
            line = test
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def _lines(d, xy, text, size, bold, width, spacing=12, fill=INK):
    x, y = xy
    for line in _wrap(d, text, size, bold, width):
        cursor = x
        for word in line.split():
            font = _font(size, bold, _dev(word))
            token = word + " "
            d.text((cursor, y), token, font=font, fill=fill)
            cursor += d.textlength(token, font=font)
        y += size + spacing
    return y


def _canvas_base(image):
    d = ImageDraw.Draw(image)
    width, height = image.size
    for x in range(0, width, 80):
        d.line((x, 0, x, height), fill=GRID, width=1)
    for y in range(0, height, 80):
        d.line((0, y, width, y), fill=GRID, width=1)
    d.line((0, 0, width, 0), fill=ACCENT, width=5)


def _card(d, box, outline=BORDER, width=2, radius=24, fill=SURFACE):
    x1, y1, x2, y2 = box
    d.rounded_rectangle(
        (x1 + 8, y1 + 10, x2 + 8, y2 + 10),
        radius,
        fill=SHADOW,
    )
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def draw_question_card(image, question, box, *, question_number=None, total_questions=None):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    _card(d, box)
    d.rounded_rectangle((x1, y1, x1 + 8, y2), 4, fill=ACCENT)
    d.text((x1 + 42, y1 + 28), "QUESTION", font=_font(24, True), fill=ACCENT)

    if question_number is not None:
        label = (
            f"Q{question_number}/{total_questions}"
            if total_questions is not None
            else f"Q{question_number}"
        )
        font = _font(24, True)
        label_width = d.textlength(label, font=font)
        pill = (x2 - label_width - 56, y1 + 20, x2 - 24, y1 + 60)
        d.rounded_rectangle(pill, 20, fill=SURFACE_2, outline=BORDER, width=1)
        d.text((pill[0] + 16, pill[1] + 7), label, font=font, fill=MUTED)

    _lines(d, (x1 + 42, y1 + 94), question, 52, True, x2 - x1 - 84, 12)


def draw_choices(image, choices, box, *, selected_index=None, correct_index=None):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    gap = 14
    row = (y2 - y1 - gap * (len(choices) - 1)) / max(len(choices), 1)
    size = max(28, min(42, int(row * 0.29)))

    for i, choice in enumerate(choices):
        top = int(y1 + i * (row + gap))
        bottom = int(top + row)
        fill, outline, accent_fill = SURFACE, BORDER, HIGHLIGHT
        if i == correct_index:
            fill, outline, accent_fill = SUCCESS_SURFACE, SUCCESS, (34, 92, 69)
        elif i == selected_index:
            fill, outline, accent_fill = DANGER_SURFACE, DANGER, (91, 48, 56)

        _card(d, (x1, top, x2, bottom), outline=outline, width=2, radius=18, fill=fill)
        d.rounded_rectangle(
            (x1 + 20, top + 16, x1 + 78, bottom - 16),
            16,
            fill=accent_fill,
        )
        letter_font = _font(26, True)
        letter = chr(65 + i)
        bounds = d.textbbox((0, 0), letter, font=letter_font)
        d.text(
            (
                x1 + 49 - (bounds[2] - bounds[0]) / 2,
                top + (bottom - top - (bounds[3] - bounds[1])) / 2 - 3,
            ),
            letter,
            font=letter_font,
            fill=ACCENT if i not in (correct_index, selected_index) else INK,
        )
        _lines(d, (x1 + 104, top + 13), str(choice), size, False, x2 - x1 - 128, 6)

        if i == correct_index:
            d.text((x2 - 150, top + 20), "CORRECT", font=_font(20, True), fill=SUCCESS)
        elif i == selected_index:
            d.text((x2 - 150, top + 20), "INCORRECT", font=_font(20, True), fill=DANGER)


def draw_timer(image, seconds, center, *, radius=72):
    d = ImageDraw.Draw(image)
    cx, cy = center
    d.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=SURFACE_2,
        outline=BORDER,
        width=4,
    )
    d.arc(
        (cx - radius + 7, cy - radius + 7, cx + radius - 7, cy + radius - 7),
        220,
        40,
        fill=ACCENT,
        width=8,
    )
    font = _font(42, True)
    label = f"{seconds}s"
    bounds = d.textbbox((0, 0), label, font=font)
    d.text(
        (cx - (bounds[2] - bounds[0]) / 2, cy - (bounds[3] - bounds[1]) / 2 - 4),
        label,
        font=font,
        fill=INK,
    )


def draw_answer_reveal(image, answer, box, *, correct=True):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    status = SUCCESS if correct else DANGER
    fill = SUCCESS_SURFACE if correct else DANGER_SURFACE
    _card(d, box, status, 2, 24, fill=fill)
    d.rounded_rectangle((x1, y1, x1 + 8, y2), 4, fill=status)
    label = "ANSWER CONFIRMED" if correct else "CHECK THE ANSWER"
    d.text((x1 + 40, y1 + 28), label, font=_font(24, True), fill=status)
    _lines(d, (x1 + 40, y1 + 94), str(answer), 56, True, x2 - x1 - 80, 10, INK)


def draw_calculation_step(image, steps, box, *, step_number=None):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    _card(d, box)
    label = "SOLUTION" if step_number is None else f"STEP {step_number}"
    d.text((x1 + 40, y1 + 28), label, font=_font(24, True), fill=INFO)
    d.line((x1 + 40, y1 + 66, x2 - 40, y1 + 66), fill=BORDER, width=1)
    y = y1 + 92
    for position, step in enumerate(steps):
        d.ellipse((x1 + 40, y + 6, x1 + 68, y + 34), fill=HIGHLIGHT)
        d.text((x1 + 48, y + 6), str(position + 1), font=_font(18, True), fill=INFO)
        y = _lines(d, (x1 + 86, y), str(step), 42, False, x2 - x1 - 126, 7) + 16


def draw_highlighted_text(image, segments, box, *, font_size=46):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    x, y = x1, y1
    for text, highlighted in segments:
        for word in str(text).split():
            token = word + " "
            font = _font(font_size, False, _dev(word))
            w = d.textlength(token, font=font)
            if x + w > x2 and x > x1:
                x, y = x1, y + font_size + 16
            d.text((x, y), token, font=font, fill=INK)
            if highlighted:
                d.line((x, y + font_size + 5, x + w - 4, y + font_size + 5), fill=ACCENT, width=5)
            x += w


def draw_flow_diagram(image, nodes, edges):
    d = ImageDraw.Draw(image)
    for a, b in edges:
        p, q = nodes[a][1], nodes[b][1]
        d.line(
            (
                (p[0] + p[2]) / 2,
                (p[1] + p[3]) / 2,
                (q[0] + q[2]) / 2,
                (q[1] + q[3]) / 2,
            ),
            fill=MUTED,
            width=4,
        )
    for label, box in nodes:
        _card(d, box, ACCENT, 2, 18, fill=SURFACE_2)
        _lines(d, (box[0] + 18, box[1] + 20), label, 34, True, box[2] - box[0] - 36, 6)


def draw_progress(image, current, total, box):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    r = max(2, (y2 - y1) // 2)
    d.rounded_rectangle(box, r, fill=HIGHLIGHT)
    ratio = 0 if total <= 0 else max(0, min(1, current / total))
    filled = x1 + int((x2 - x1) * ratio)
    if filled > x1:
        d.rounded_rectangle((x1, y1, filled, y2), r, fill=ACCENT)
    d.text((x2 + 16, y1 - 4), f"{current}/{total}", font=_font(22, True), fill=MUTED)


def draw_score_result(image, score, total, box):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    _card(d, box)
    d.text((x1 + 40, y1 + 30), "SESSION RESULT", font=_font(24, True), fill=INFO)
    font = _font(88, True)
    label = f"{score}/{total}"
    bounds = d.textbbox((0, 0), label, font=font)
    d.text(
        (x1 + (x2 - x1 - (bounds[2] - bounds[0])) / 2, y1 + 118),
        label,
        font=font,
        fill=INK,
    )
    pct = 0 if total <= 0 else round(score / total * 100)
    pct_font = _font(34, True)
    pct_label = f"{pct}% accuracy"
    bounds = d.textbbox((0, 0), pct_label, font=pct_font)
    d.text(
        (x1 + (x2 - x1 - (bounds[2] - bounds[0])) / 2, y2 - 76),
        pct_label,
        font=pct_font,
        fill=SUCCESS if pct >= 50 else DANGER,
    )
