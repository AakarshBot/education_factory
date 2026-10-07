from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urljoin, urlparse

import requests

from question import Question

OFFICIAL_SOURCE_PAGES = {
    "SSC": "https://ssc.gov.in/home/answer-key",
    "Railway": "https://www.rrbcdg.gov.in/",
    "Banking": "https://www.ibps.in/index.php/faq/",
}

_DISCOVERY_TERMS = (
    "question paper",
    "question papers",
    "answer key",
    "final answer key",
    "response sheet",
)

_ALLOWED_HOSTS = {
    "SSC": ("ssc.gov.in",),
    "Railway": ("rrbcdg.gov.in",),
    "Banking": ("ibps.in",),
}


@dataclass(frozen=True)
class PYQDocument:
    exam: str
    title: str
    url: str
    official: bool
    reuse_permitted: bool
    reuse_evidence: str

    def __post_init__(self) -> None:
        if self.exam not in OFFICIAL_SOURCE_PAGES:
            raise ValueError("unsupported exam source")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS[self.exam]:
            raise ValueError("PYQ document URL is not on the official exam domain")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("PYQ document title must not be empty")
        if not self.official:
            raise ValueError("PYQ document must be official")
        if self.reuse_permitted and not self.reuse_evidence.strip():
            raise ValueError("reuse evidence is required when reuse is permitted")

    def to_dict(self) -> dict[str, object]:
        return {
            "exam": self.exam,
            "title": self.title,
            "url": self.url,
            "official": self.official,
            "reuse_permitted": self.reuse_permitted,
            "reuse_evidence": self.reuse_evidence,
        }


@dataclass(frozen=True)
class VerifiedPYQSource:
    question: Question
    source_reference: str
    rights_note: str
    reuse_permitted: bool

    def __post_init__(self) -> None:
        if not isinstance(self.question, Question):
            raise TypeError("question must be a Question")
        if self.question.source_type.strip().lower() != "pyq":
            raise ValueError("question source_type must be pyq")
        if not self.question.source_reference or not self.question.source_reference.strip():
            raise ValueError("question must contain source_reference")
        if self.question.source_reference.strip() != self.source_reference.strip():
            raise ValueError("source_reference must match the question")
        if not isinstance(self.rights_note, str) or not self.rights_note.strip():
            raise ValueError("rights_note must not be empty")
        if not self.reuse_permitted:
            raise ValueError("PYQ reuse permission is required")
        parsed = urlparse(self.source_reference.strip())
        if parsed.scheme != "https":
            raise ValueError("PYQ source_reference must use HTTPS")


def _official_url(exam: str, href: str) -> str | None:
    source = OFFICIAL_SOURCE_PAGES[exam]
    absolute = urljoin(source, href)
    parsed = urlparse(absolute)
    if parsed.scheme != "https":
        return None
    if parsed.netloc.lower() not in _ALLOWED_HOSTS[exam]:
        return None
    return absolute


def _discover_page(exam: str, page_url: str) -> list[PYQDocument]:
    response = requests.get(page_url, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"PYQ source discovery failed ({response.status_code})")

    html = response.text
    links = re.findall(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    documents: list[PYQDocument] = []
    seen: set[str] = set()
    for href, raw_text in links:
        title = re.sub(r"<[^>]+>", " ", raw_text)
        title = re.sub(r"\s+", " ", title).strip()
        combined = f"{title} {href}".casefold()
        if not any(term in combined for term in _DISCOVERY_TERMS):
            continue

        url = _official_url(exam, href)
        if not url or url in seen:
            continue
        seen.add(url)

        documents.append(
            PYQDocument(
                exam=exam,
                title=title or url,
                url=url,
                official=True,
                reuse_permitted=False,
                reuse_evidence="",
            )
        )

    return documents


def discover_official_pyq_documents(
    exams: Sequence[str] = tuple(OFFICIAL_SOURCE_PAGES),
) -> tuple[PYQDocument, ...]:
    if not exams:
        raise ValueError("exams must not be empty")

    cleaned = tuple(exam.strip().title() for exam in exams)
    if any(exam not in OFFICIAL_SOURCE_PAGES for exam in cleaned):
        raise ValueError("exams contains an unsupported source")

    documents: list[PYQDocument] = []
    for exam in cleaned:
        documents.extend(_discover_page(exam, OFFICIAL_SOURCE_PAGES[exam]))

    return tuple(documents)


def select_verified_pyq_questions(
    sources: Sequence[VerifiedPYQSource],
    *,
    count: int,
) -> list[Question]:
    if count < 1:
        raise ValueError("count must be at least 1")
    if not sources:
        raise ValueError("verified PYQ sources are required")
    if len(sources) < count:
        raise ValueError("not enough verified PYQ sources")

    questions = []
    seen: set[tuple[str, str, str]] = set()
    for source in sources[:count]:
        question = source.question
        key = (
            question.exam.strip().lower(),
            question.topic.strip().lower(),
            question.question.strip().lower(),
        )
        if key in seen:
            raise RuntimeError("verified PYQ sources contain duplicate questions")
        seen.add(key)
        questions.append(question)
    return questions
