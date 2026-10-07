from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from audio_qa import check_audio
from channel_history import DEFAULT_HISTORY_FILE, load_history
from demand_discovery import discover_demand
from editorial_adaptation import build_editorial_adaptation
from editorial_queue import build_editorial_queue
from explanation_generator import generate_explanations
from format_analysis import analyze_formats
from lesson import Lesson
from lesson_assembler import assemble_lesson
from long_form_renderer import render_long_form
from metadata_generator import generate_metadata
from narration import synthesize_speech
from question_generator import generate_questions
from subject_analysis import analyze_subjects
from topic_family_analysis import analyze_topic_families
from topic_scorer import score_topics
from youtube_analytics import ingest_metrics
from youtube_auth import get_youtube_client
from youtube_uploader import upload_video

DEFAULT_OUTPUT_ROOT = Path("output")
DEFAULT_QUESTIONS = 10
DEFAULT_DIFFICULTY = "mixed"
DEFAULT_LANGUAGE = "Hinglish"
DEFAULT_LESSON_TYPE = "practice"
AUTO_LESSON_TYPES = ("practice", "timed_test", "revision")
LOCAL_ZONE = ZoneInfo("Asia/Kolkata")


def _slug(value: str) -> str:
    clean = re.sub(r"[^\w]+", "-", value.strip().lower(), flags=re.UNICODE)
    return clean.strip("-") or "lesson"


def _narration_segments(lesson: Lesson) -> list[str]:
    texts: list[str] = []

    for index, segment in enumerate(lesson.segments):
        question = (
            lesson.questions[segment.question_index]
            if segment.question_index is not None
            else None
        )

        if segment.kind == "concept":
            text = segment.text or ""
        elif segment.kind == "source":
            text = f"Source: {segment.source_reference or 'Unavailable'}."
        elif segment.kind == "question":
            if question is None:
                raise RuntimeError("question segment is missing its question")
            choices = ""
            if question.choices:
                labels = "ABCD"
                choices = " Options: " + " ".join(
                    f"{labels[position]}. {choice}"
                    for position, choice in enumerate(question.choices)
                )
            text = f"Question {segment.question_index + 1}. {question.question}.{choices}"
        elif segment.kind == "timer":
            text = "Take a moment and solve it."
        elif segment.kind == "answer":
            if question is None:
                raise RuntimeError("answer segment is missing its question")
            text = f"The correct answer is {question.correct_answer}."
        elif segment.kind == "explanation":
            if question is None:
                raise RuntimeError("explanation segment is missing its question")
            text = question.explanation
        elif segment.kind == "shortcut":
            if question is None:
                raise RuntimeError("shortcut segment is missing its question")
            text = f"Quick method: {question.shortcut}."
        elif segment.kind == "score":
            text = "Review the result and keep practicing."
        else:
            raise RuntimeError(f"unsupported narration segment: {segment.kind}")

        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"empty narration segment at index {index}")
        texts.append(text.strip())

    return texts


def _scene_durations(texts: list[str], total_duration: float) -> list[float]:
    if not texts:
        raise ValueError("texts must not be empty")
    if total_duration <= 0:
        raise ValueError("total_duration must be positive")

    weights = [max(1, len(re.findall(r"\S+", text))) for text in texts]
    total_weight = sum(weights)
    durations = [
        round(total_duration * weight / total_weight, 6)
        for weight in weights
    ]
    durations[-1] = round(total_duration - sum(durations[:-1]), 6)

    if any(duration <= 0 for duration in durations):
        raise RuntimeError("narration produced invalid scene durations")
    return durations


def _select_lesson_type(adaptation) -> str:
    available = {
        lesson_type: adaptation.format_weights.get(lesson_type, 1.0)
        for lesson_type in AUTO_LESSON_TYPES
    }
    return max(
        AUTO_LESSON_TYPES,
        key=lambda lesson_type: (available[lesson_type], -AUTO_LESSON_TYPES.index(lesson_type)),
    )


def _select_job(jobs, adaptation):
    if not jobs:
        raise RuntimeError("editorial queue produced no jobs")

    def adjusted(job):
        return (
            job.total_score
            * adaptation.subject_weights.get(job.subject.strip().lower(), 1.0)
        )

    return max(
        jobs,
        key=lambda job: (
            adjusted(job),
            job.total_score,
            -job.priority,
        ),
    )


def _next_publish_time(now: datetime) -> datetime:
    local_now = now.astimezone(LOCAL_ZONE)
    candidate = local_now.replace(
        hour=18,
        minute=0,
        second=0,
        microsecond=0,
    )
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return candidate


def run_factory(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    history_path: str | Path = DEFAULT_HISTORY_FILE,
    max_jobs: int = 10,
    question_count: int = DEFAULT_QUESTIONS,
    difficulty: str = DEFAULT_DIFFICULTY,
    language: str = DEFAULT_LANGUAGE,
    publish_mode: str = "scheduled",
    publish_at: datetime | None = None,
) -> Lesson:
    if max_jobs < 1:
        raise ValueError("max_jobs must be at least 1")
    if question_count < 1:
        raise ValueError("question_count must be at least 1")
    if not difficulty.strip():
        raise ValueError("difficulty must not be empty")
    if not language.strip():
        raise ValueError("language must not be empty")

    output = Path(output_root)
    history_file = Path(history_path)
    history = load_history(history_file)

    formats = analyze_formats(history)
    subjects = analyze_subjects(history)
    families = analyze_topic_families(history)
    adaptation = build_editorial_adaptation(formats, subjects, families)

    signals = discover_demand()
    scores = score_topics(
        signals,
        recent_titles=tuple(entry.title for entry in history if entry.title.strip()),
        language=language,
    )
    jobs = build_editorial_queue(scores, max_jobs=max_jobs, history=history)
    job = _select_job(jobs, adaptation)

    lesson_type = _select_lesson_type(adaptation)
    questions = generate_questions(
        subject=job.subject,
        exam=job.exam,
        topic=job.topic,
        difficulty=difficulty,
        count=question_count,
        language=language,
    )
    questions = generate_explanations(questions, language=language)
    lesson = assemble_lesson(questions, lesson_type=lesson_type)

    lesson_dir = output / _slug(lesson.title)
    lesson_dir.mkdir(parents=True, exist_ok=True)

    audio_path = lesson_dir / "narration.mp3"
    timing_path = lesson_dir / "word_timings.json"
    video_path = lesson_dir / "long_form.mp4"
    metadata_path = lesson_dir / "metadata.json"

    narration_segments = _narration_segments(lesson)
    narration_text = "\n\n".join(narration_segments)
    synthesize_speech(
        narration_text,
        audio_path,
        timing_path=timing_path,
    )
    audio_result = check_audio(audio_path)
    durations = _scene_durations(narration_segments, audio_result.duration_seconds)
    render_long_form(
        lesson,
        audio_path,
        video_path,
        durations,
    )

    metadata = generate_metadata(lesson, language=language)
    metadata_path.write_text(
        json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if publish_mode not in {"scheduled", "public"}:
        raise ValueError("publish_mode must be 'scheduled' or 'public'")

    youtube = get_youtube_client()
    selected_publish_at = publish_at
    if publish_mode == "scheduled" and selected_publish_at is None:
        selected_publish_at = _next_publish_time(datetime.now(LOCAL_ZONE))

    upload_video(
        youtube,
        lesson,
        metadata,
        video_path,
        mode=publish_mode,
        publish_at=selected_publish_at,
        history_path=history_file,
    )

    try:
        ingest_metrics(history_path=history_file)
    except RuntimeError:
        raise

    return lesson


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one autonomous education-factory production job.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_HISTORY_FILE))
    parser.add_argument("--max-jobs", type=int, default=10)
    parser.add_argument("--question-count", type=int, default=DEFAULT_QUESTIONS)
    parser.add_argument("--difficulty", default=DEFAULT_DIFFICULTY)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--publish-mode", choices=("scheduled", "public"), default="scheduled")
    args = parser.parse_args()

    lesson = run_factory(
        output_root=args.output_root,
        history_path=args.history_path,
        max_jobs=args.max_jobs,
        question_count=args.question_count,
        difficulty=args.difficulty,
        language=args.language,
        publish_mode=args.publish_mode,
    )
    print(f"Completed: {lesson.title}")


if __name__ == "__main__":
    main()
