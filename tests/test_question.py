from question import Question


def test_question_contains_locked_fields():
    question = Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="A price of ₹800 is reduced by 10%. What is the new price?",
        choices=("₹700", "₹720", "₹740", "₹760"),
        correct_answer="₹720",
        explanation="10% of ₹800 is ₹80, so ₹800 - ₹80 = ₹720.",
        shortcut="Multiply by 0.90.",
        source_type="original",
        source_reference=None,
    )

    data = question.to_dict()

    assert set(data) == {
        "subject",
        "exam",
        "topic",
        "difficulty",
        "question",
        "choices",
        "correct_answer",
        "explanation",
        "shortcut",
        "source_type",
        "source_reference",
    }
    assert data["choices"] == ("₹700", "₹720", "₹740", "₹760")


def test_question_round_trips_from_dict():
    data = {
        "subject": "reasoning",
        "exam": "Banking",
        "topic": "coding-decoding",
        "difficulty": "easy",
        "question": "If CAT becomes DBU, how does DOG change?",
        "choices": ["EPH", "EPG", "FPH", "EOH"],
        "correct_answer": "EPH",
        "explanation": "Each letter moves forward by one.",
        "shortcut": None,
        "source_type": "original",
        "source_reference": None,
    }

    question = Question.from_dict(data)

    assert question.choices == ("EPH", "EPG", "FPH", "EOH")
    assert question.to_dict()["choices"] == question.choices
