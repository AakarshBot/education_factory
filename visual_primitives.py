from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SIZE = (1920, 1080)

BACKGROUND = (248, 247, 243)
SURFACE = (255, 254, 250)
SURFACE_2 = (245, 243, 237)
INK = (34, 40, 39)
MUTED = (104, 111, 108)
ACCENT = (48, 137, 103)
INFO = (82, 111, 112)
SUCCESS = (48, 137, 103)
DANGER = (184, 83, 83)
BORDER = (220, 217, 208)
HIGHLIGHT = (232, 240, 234)
SUCCESS_SURFACE = (232, 242, 235)
DANGER_SURFACE = (249, 235, 235)
GRID = (240, 238, 232)
SHADOW = (228, 224, 216)

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
    for word in str(text).strip().split():
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


def _fit_text(draw, text, max_width, max_height, max_size, min_size=24, bold=False, spacing=10):
    value = str(text).strip()
    if not value:
        return [], max_size
    upper = max(min_size, int(max_size))
    for size in range(upper, min_size - 1, -1):
        lines = _wrap(draw, value, size, bold, max_width)
        if lines and len(lines) * (size + spacing) - spacing <= max_height:
            return lines, size
    return _wrap(draw, value, min_size, bold, max_width), min_size


def _lines(d, xy, text, size, bold, width, spacing=12, fill=INK, *, max_height=None, min_size=24):
    x, y = xy
    if max_height is not None:
        lines, size = _fit_text(
            d, text, width, max_height, size, min_size=min_size,
            bold=bold, spacing=spacing,
        )
    else:
        lines = _wrap(d, text, size, bold, width)

    for line in lines:
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
    inset = 10
    for x in range(inset, width - inset, 96):
        d.line((x, inset, x, height - inset), fill=GRID, width=1)
    for y in range(inset, height - inset, 96):
        d.line((inset, y, width - inset, y), fill=GRID, width=1)
    d.line((inset, inset, width - inset, inset), fill=ACCENT, width=3)


def _card(d, box, outline=BORDER, width=2, radius=20, fill=SURFACE):
    x1, y1, x2, y2 = box
    d.rounded_rectangle(
        (x1 + 6, y1 + 7, x2 + 6, y2 + 7),
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

    content_x = x1 + 42
    content_y = y1 + 94
    content_width = x2 - x1 - 84
    content_height = max(1, y2 - content_y - 24)
    _lines(
        d, (content_x, content_y), question,
        min(52, max(32, int(content_height * 0.30))),
        True, content_width, 10,
        max_height=content_height, min_size=30,
    )


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
        right_pad = 174 if correct_index is not None or selected_index is not None else 24
        choice_x = x1 + 104
        choice_y = top + 13
        choice_width = max(40, x2 - choice_x - right_pad)
        choice_height = max(1, bottom - choice_y - 13)
        _lines(
            d, (choice_x, choice_y), str(choice), size, False,
            choice_width, 5, max_height=choice_height, min_size=24,
        )

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
    content_x = x1 + 40
    content_y = y1 + 94
    content_width = x2 - x1 - 80
    content_height = max(1, y2 - content_y - 24)
    _lines(
        d, (content_x, content_y), str(answer),
        min(56, max(32, int(content_height * 0.34))),
        True, content_width, 8, INK,
        max_height=content_height, min_size=30,
    )


def draw_calculation_step(image, steps, box, *, step_number=None):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    _card(d, box)
    label = "SOLUTION" if step_number is None else f"STEP {step_number}"
    d.text((x1 + 40, y1 + 28), label, font=_font(24, True), fill=INFO)
    d.line((x1 + 40, y1 + 66, x2 - 40, y1 + 66), fill=BORDER, width=1)
    steps = tuple(str(step).strip() for step in steps if str(step).strip())
    if not steps:
        return
    content_x = x1 + 86
    content_y = y1 + 92
    content_width = x2 - content_x - 40
    content_height = max(1, y2 - content_y - 24)
    size = min(42, max(28, int(content_height / max(len(steps) * 2.2, 1))))
    wrapped = []
    for size_candidate in range(size, 23, -1):
        candidate = [_wrap(d, step, size_candidate, False, content_width) for step in steps]
        total_height = sum(len(lines) * (size_candidate + 7) for lines in candidate) + (len(steps) - 1) * 9
        if total_height <= content_height:
            size = size_candidate
            wrapped = candidate
            break
    if not wrapped:
        wrapped = [_wrap(d, step, size, False, content_width) for step in steps]
    y = content_y
    for position, lines in enumerate(wrapped):
        d.ellipse((x1 + 40, y + 6, x1 + 68, y + 34), fill=HIGHLIGHT)
        d.text((x1 + 48, y + 6), str(position + 1), font=_font(18, True), fill=INFO)
        for line in lines:
            _lines(d, (content_x, y), line, size, False, content_width, 7)
            y += size + 7
        y += 9


def draw_highlighted_text(image, segments, box, *, font_size=46):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    tokens = []
    for text, highlighted in segments:
        tokens.extend((word, highlighted) for word in str(text).split())
    if not tokens:
        return

    width = max(1, x2 - x1)
    height = max(1, y2 - y1)
    size = min(font_size, max(28, int(height * 0.28)))
    chosen = []
    for size_candidate in range(size, 23, -1):
        lines = []
        current = []
        current_width = 0
        space = d.textlength(" ", font=_font(size_candidate, False))
        for word, highlighted in tokens:
            word_width = d.textlength(word, font=_font(size_candidate, False))
            required = word_width if not current else space + word_width
            if current and current_width + required > width:
                lines.append(current)
                current = []
                current_width = 0
            current.append((word, highlighted))
            current_width += required
        if current:
            lines.append(current)
        if len(lines) * (size_candidate + 12) - 12 <= height:
            chosen = lines
            size = size_candidate
            break
    if not chosen:
        chosen = [tokens]

    y = y1
    for line in chosen:
        x = x1
        for word, highlighted in line:
            token = word + " "
            font = _font(size, False, _dev(word))
            w = d.textlength(token, font=font)
            d.text((x, y), token, font=font, fill=INK)
            if highlighted:
                d.line((x, y + size + 5, x + w - 4, y + size + 5), fill=ACCENT, width=4)
            x += w
        y += size + 12


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


def _topic_key(topic):
    return str(topic or "").lower().replace("-", " ").replace("_", " ")


def _visual_panel(d, box, title):
    _card(d, box, outline=BORDER, width=1, radius=24, fill=SURFACE)
    x1, y1, x2, y2 = box
    d.rounded_rectangle((x1 + 24, y1 + 22, x1 + 64, y1 + 26), 2, fill=ACCENT)
    d.text((x1 + 78, y1 + 14), title, font=_font(19, True), fill=MUTED)
    return x1 + 28, y1 + 66, x2 - 28, y2 - 24


def draw_topic_visual(image, topic, question=None, box=(1200, 100, 1800, 500)):
    d = ImageDraw.Draw(image)
    x1, y1, x2, y2 = _visual_panel(d, box, "LEARNING VISUAL")
    key = _topic_key(topic)
    w, h = x2 - x1, y2 - y1

    if any(token in key for token in ("syllog", "logic", "conclusion")):
        r = min(w, h) // 6
        cy = y1 + h // 2 + 4
        centers = (x1 + w // 3, x1 + w // 2, x1 + 2 * w // 3)
        labels = ("SET A", "SET B", "SET C")
        for cx, label in zip(centers, labels):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=INFO, width=4)
            bounds = d.textbbox((0, 0), label, font=_font(20, True))
            d.text((cx - (bounds[2] - bounds[0]) / 2, cy - 12), label, font=_font(20, True), fill=INK)
        d.text((x1, y2 - 18), "Check only relationships forced by the statements.", font=_font(19, False), fill=MUTED)
        return

    if "percent" in key:
        cx, cy = x1 + w * 0.30, y1 + h * 0.50
        r = min(w, h) // 4
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=SURFACE_2, outline=BORDER, width=2)
        for start, end, fill in ((-90, 0, ACCENT), (0, 90, HIGHLIGHT), (90, 180, HIGHLIGHT), (180, 270, HIGHLIGHT)):
            d.pieslice((cx-r, cy-r, cx+r, cy+r), start, end, fill=fill)
        d.ellipse((cx-r//2, cy-r//2, cx+r//2, cy+r//2), fill=SURFACE)
        d.text((cx-34, cy-16), "PART", font=_font(22, True), fill=INFO)
        bx1, by = x1 + w * 0.56, y1 + h * 0.34
        d.rounded_rectangle((bx1, by, x2 - 6, by + 34), 17, fill=HIGHLIGHT)
        d.rounded_rectangle((bx1, by, bx1 + int((x2 - bx1 - 6) * 0.58), by + 34), 17, fill=ACCENT)
        d.text((bx1, by + 50), "PART OF A WHOLE", font=_font(22, True), fill=INK)
        return

    if any(token in key for token in ("ratio", "proportion")):
        base = y1 + h * 0.52
        left = x1 + 24
        d.line((left, base, x2 - 24, base), fill=BORDER, width=3)
        d.rounded_rectangle((x1 + 54, base - 52, x1 + w * 0.46, base - 8), 14, fill=HIGHLIGHT)
        d.rounded_rectangle((x1 + w * 0.54, base - 86, x2 - 54, base - 8), 14, fill=ACCENT)
        d.text((x1 + 54, base + 20), "PART A", font=_font(22, True), fill=INFO)
        d.text((x1 + w * 0.54, base + 20), "PART B", font=_font(22, True), fill=ACCENT)
        d.text((x1, y2 - 34), "Compare relative parts.", font=_font(21, False), fill=MUTED)
        return

    if any(token in key for token in ("average", "mean", "median")):
        base_y = y1 + h * 0.67
        left, right = x1 + 24, x2 - 24
        d.line((left, base_y, right, base_y), fill=BORDER, width=4)
        points = (0.12, 0.28, 0.54, 0.78, 0.90)
        for p in points:
            px = left + int((right-left)*p)
            d.ellipse((px-10, base_y-10, px+10, base_y+10), fill=INFO)
        mean_x = left + int((right-left)*0.54)
        d.line((mean_x, y1+24, mean_x, base_y-18), fill=ACCENT, width=5)
        d.text((mean_x-34, y1+4), "MEAN", font=_font(19, True), fill=ACCENT)
        return

    if any(token in key for token in ("direction", "distance", "coordinate")):
        cx, cy = x1 + w // 2, y1 + h // 2 + 12
        d.line((cx, y1+26, cx, y2-20), fill=BORDER, width=3)
        d.line((x1+22, cy, x2-22, cy), fill=BORDER, width=3)
        d.polygon((cx, y1+8, cx-10, y1+34, cx+10, y1+34), fill=ACCENT)
        d.text((cx-10, y1-2), "N", font=_font(22, True), fill=ACCENT)
        d.text((x2-24, cy-14), "E", font=_font(22, True), fill=INFO)
        d.text((x1+8, cy-14), "W", font=_font(22, True), fill=INFO)
        d.text((cx-10, y2-20), "S", font=_font(22, True), fill=INFO)
        return

    if any(token in key for token in ("probability", "chance")):
        mid = (x1 + w // 2, y1 + h // 2 + 20)
        left_box = (x1 + 70, y1 + 70, x1 + 180, y1 + 132)
        right_box = (x2 - 180, y1 + 70, x2 - 70, y1 + 132)
        d.line((mid[0], mid[1], left_box[2], left_box[1] + 31), fill=BORDER, width=4)
        d.line((mid[0], mid[1], right_box[0], right_box[1] + 31), fill=BORDER, width=4)
        for box2, label in ((left_box, "YES"), (right_box, "NO")):
            d.rounded_rectangle(box2, 16, fill=HIGHLIGHT, outline=BORDER, width=2)
            d.text((box2[0]+20, box2[1]+16), label, font=_font(22, True), fill=INK)
        d.ellipse((mid[0]-34, mid[1]-34, mid[0]+34, mid[1]+34), fill=ACCENT)
        d.text((mid[0]-12, mid[1]-14), "?", font=_font(26, True), fill=INK)
        return

    if any(token in key for token in ("grammar", "english", "tenses", "sentence")):
        y = y1 + h * 0.48
        words = ("SUBJECT", "VERB", "OBJECT")
        widths = (0.28, 0.22, 0.30)
        cursor = x1
        fills = (HIGHLIGHT, (231, 238, 236), HIGHLIGHT)
        for label, frac, fill in zip(words, widths, fills):
            bw = int(w * frac)
            d.rounded_rectangle((cursor, y, cursor+bw, y+70), 16, fill=fill, outline=BORDER, width=2)
            d.text((cursor+18, y+20), label, font=_font(20, True), fill=INK)
            cursor += bw + 12
        return

    centers = (x1 + w // 6, x1 + w // 2, x1 + 5 * w // 6)
    labels = ("GIVEN", "RULE", "CHECK")
    for cx, label in zip(centers, labels):
        box2 = (cx - 72, y1 + h // 2 - 34, cx + 72, y1 + h // 2 + 34)
        d.rounded_rectangle(box2, 18, fill=HIGHLIGHT, outline=BORDER, width=2)
        bounds = d.textbbox((0, 0), label, font=_font(20, True))
        d.text((cx-(bounds[2]-bounds[0])/2, box2[1]+19), label, font=_font(20, True), fill=INK)
    d.line((centers[0]+72, y1+h//2, centers[1]-72, y1+h//2), fill=ACCENT, width=4)
    d.line((centers[1]+72, y1+h//2, centers[2]-72, y1+h//2), fill=ACCENT, width=4)
