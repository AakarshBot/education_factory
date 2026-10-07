import pytest

import pyq_source
from pyq_source import PYQDocument, VerifiedPYQSource, discover_official_pyq_documents, select_verified_pyq_questions
from question import Question


def question(reference, question_text):
    return Question(
        subject="maths",
        exam="SSC",
        topic="percentages",
        difficulty="medium",
        question=question_text,
        choices=("25", "50", "75", "100"),
        correct_answer="25",
        explanation="",
        shortcut=None,
        source_type="pyq",
        source_reference=reference,
    )


def source(reference, text):
    q = question(reference, text)
    return VerifiedPYQSource(
        question=q,
        source_reference=reference,
        rights_note="Reuse permission verified from source.",
    )


def test_official_document_requires_official_domain():
    with pytest.raises(ValueError, match="official exam domain"):
        PYQDocument(
            exam="SSC",
            title="Question paper",
            url="https://example.com/question.pdf",
            official=True,
            reuse_permitted=False,
            reuse_evidence="",
        )


def test_official_document_cannot_claim_reuse_without_evidence():
    with pytest.raises(ValueError, match="reuse evidence"):
        PYQDocument(
            exam="SSC",
            title="Question paper",
            url="https://ssc.gov.in/question.pdf",
            official=True,
            reuse_permitted=True,
            reuse_evidence="",
        )


def test_discovery_keeps_only_official_question_links(monkeypatch):
    html = """
    <a href="/question-paper.pdf">Final Question Paper</a>
    <a href="https://example.com/copy.pdf">Question Paper Copy</a>
    <a href="/notice.pdf">Exam Notice</a>
    """

    class Response:
        status_code = 200
        text = html

    monkeypatch.setattr(pyq_source.requests, "get", lambda *args, **kwargs: Response())

    results = discover_official_pyq_documents(["SSC"])

    assert len(results) == 1
    assert results[0].url == "https://ssc.gov.in/question-paper.pdf"
    assert results[0].reuse_permitted is False


def test_verified_pyq_source_requires_matching_reference():
    q = question("https://ssc.gov.in/q1", "A")
    with pytest.raises(ValueError, match="match"):
        VerifiedPYQSource(
            question=q,
            source_reference="https://ssc.gov.in/q2",
            rights_note="verified",
        )


def test_select_verified_pyq_questions_requires_enough_sources():
    with pytest.raises(ValueError, match="not enough"):
        select_verified_pyq_questions([source("a", "A")], count=2)


def test_select_verified_pyq_questions_returns_verified_questions():
    result = select_verified_pyq_questions(
        [source("a", "A"), source("b", "B")],
        count=2,
    )
    assert [item.source_reference for item in result] == ["a", "b"]
