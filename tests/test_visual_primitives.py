from PIL import Image, ImageDraw
import visual_primitives
from visual_qa import check_image

def test_primitives_draw():
    image = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    visual_primitives.draw_question_card(image, "प्रतिशत का 25% कितना होगा?", (100,100,1800,400), question_number=1, total_questions=20)
    visual_primitives.draw_choices(image, ("60", "70", "80", "90"), (100,420,1800,900), selected_index=1, correct_index=2)
    visual_primitives.draw_timer(image, 15, (180,170))
    visual_primitives.draw_answer_reveal(image, "सही उत्तर: 60", (100,100,800,300))
    visual_primitives.draw_calculation_step(image, ("25/100 x 240 = 60", "Shortcut: 25% = 1/4"), (900,100,1800,400), step_number=1)
    visual_primitives.draw_highlighted_text(image, (("उत्तर ",False),("60",True)), (100,920,900,1020))
    visual_primitives.draw_flow_diagram(image, (("पढ़ो",(950,500,1200,620)),("हल करो",(1300,500,1550,620))), ((0,1),))
    visual_primitives.draw_progress(image, 7, 20, (100,1040,1600,1060))
    visual_primitives.draw_score_result(image, 17, 20, (1250,820,1800,1020))
    visual_primitives.draw_topic_visual(image, "syllogism", "All pens are books.", (1200,100,1800,400))
    assert len(set(image.getdata())) > 5
    assert visual_primitives.BACKGROUND != visual_primitives.SURFACE

def test_question_card_is_deterministic():
    a = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    b = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    args = ("प्रतिशत 25% of 240?", (100,100,1800,400))
    visual_primitives.draw_question_card(a, *args)
    visual_primitives.draw_question_card(b, *args)
    assert list(a.getdata()) == list(b.getdata())


def test_text_fitting_scales_long_text_to_box():
    image = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    draw = ImageDraw.Draw(image)
    lines, size = visual_primitives._fit_text(
        draw,
        "This is a deliberately long question that must fit inside a compact card without breaking its box.",
        360,
        110,
        52,
        min_size=24,
        bold=True,
        spacing=8,
    )
    assert size < 52
    assert len(lines) >= 2


def test_question_text_stays_inside_box():
    image = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    visual_primitives.draw_question_card(
        image,
        "A compact question.",
        (500, 200, 1200, 520),
    )
    assert all(image.getpixel((x, y)) == visual_primitives.BACKGROUND
               for x in range(0, 500, 25) for y in range(200, 520, 25))


def test_topic_visuals_do_not_bake_in_example_values():
    source = visual_primitives.Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    before = list(source.getdata())
    visual_primitives.draw_topic_visual(source, "Percentages", "25% of 240 is what?", (1200, 100, 1800, 400))
    after = list(source.getdata())
    assert after != before



def test_canvas_base_stays_inside_visual_qa_margin(tmp_path):
    image = Image.new("RGB", visual_primitives.DEFAULT_SIZE, visual_primitives.BACKGROUND)
    visual_primitives._canvas_base(image)
    path = tmp_path / "canvas.png"
    image.save(path, format="PNG")
    result = check_image(path, expected_size=visual_primitives.DEFAULT_SIZE)
    assert result.content_bbox[0] >= 8
    assert result.content_bbox[1] >= 8
    assert result.content_bbox[2] <= visual_primitives.DEFAULT_SIZE[0] - 8
    assert result.content_bbox[3] <= visual_primitives.DEFAULT_SIZE[1] - 8
