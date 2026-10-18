from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError, version as installed_package_version
from pathlib import Path
from zoneinfo import ZoneInfo

from audio_qa import check_audio
from channel_history import DEFAULT_HISTORY_FILE, load_history, recent_topic_keys
from concept_generator import generate_concept_summary
from demand_discovery import discover_demand
from editorial_adaptation import build_editorial_adaptation
from factory_state import DEFAULT_STATE_FILE, load_state, record_run, save_state, validate_runs_per_day
from editorial_queue import EditorialJob, build_editorial_queue, has_recent_related_topic
from explanation_generator import generate_explanations
from english_narration_generator import generate_english_narration_segments
from format_analysis import analyze_formats
from job_manifest import (
    JobManifest,
    load_manifest,
    new_manifest,
    read_json,
    stage_complete,
    write_json,
)
from lesson import Lesson
from lesson_assembler import assemble_lesson
from long_form_renderer import render_long_form
from metadata_generator import VideoMetadata, generate_metadata
from config import ENGLISH_TTS_VOICE
from narration import synthesize_speech
from question import Question
from question_generator import generate_questions
from shorts_renderer import render_short
from subject_analysis import analyze_subjects
from topic_family_analysis import TopicFamilyPerformance, analyze_topic_families
from topic_scorer import score_topics
from youtube_analytics import ingest_metrics, print_snapshot
from youtube_auth import get_youtube_client
from production_backlog import (
    DEFAULT_BACKLOG_FILE,
    claim_job,
    complete_job,
    load_backlog,
    merge_jobs,
    pending_jobs,
    release_stale_claims,
    save_backlog,
)
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_thumbnail, upload_video

DEFAULT_OUTPUT_ROOT = Path("output")


def _require_supported_edge_tts() -> None:
    try:
        installed_version = installed_package_version("edge-tts")
    except PackageNotFoundError:
        installed_version = "not installed"

    version_match = re.match(r"^(\d+)\.(\d+)\.(\d+)", installed_version)
    version_parts = (
        tuple(int(part) for part in version_match.groups())
        if version_match is not None
        else None
    )
    if (
        version_parts is None
        or version_parts < (7, 3, 1)
        or version_parts >= (8, 0, 0)
    ):
        raise RuntimeError(
            "This factory requires edge-tts>=7.3.1,<8; "
            f"the installed version is {installed_version!r}. Older releases "
            "fail against Microsoft's current speech endpoint with HTTP 403. "
            'Upgrade it with: python -m pip install --upgrade "edge-tts>=7.3.1,<8"'
        )


DEFAULT_QUESTIONS = 10
DEFAULT_DIFFICULTY = "mixed"
DEFAULT_LANGUAGE = "Hinglish"
AUTO_LESSON_TYPES = ("practice", "timed_test", "concept_practice", "revision")
LOCAL_ZONE = ZoneInfo("Asia/Kolkata")
SHORT_MAX_DURATION_SECONDS = 180.0
SHORT_PUBLISH_DELAY = timedelta(hours=8)
_CANCELLED_FAILURE_STAGES = {
    "editorial_cancellation",
    "automatic_stale_cleanup",
    "automatic_abandonment",
}


def _cleanup_unfinished_jobs(
    output_root: str | Path,
    backlog_path: str | Path,
    *,
    now: datetime | None = None,
) -> None:
    """Discard every unfinished local job before starting a fresh production run.

    Jobs are never auto-resumed. If a job already recorded YouTube upload IDs,
    preserve a compact receipt outside the active jobs directory before deleting
    its working files. Uploads themselves are never deleted.
    """
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None or reference.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    jobs_dir = Path(output_root) / "jobs"
    abandoned_run_ids: set[str] = set()
    directories_to_delete: list[Path] = []
    archived_count = 0

    for manifest_path in sorted(jobs_dir.glob("*/job.json")):
        manifest = load_manifest(manifest_path)
        if manifest.status == "complete":
            continue

        abandoned_run_ids.add(manifest.run_id)
        directories_to_delete.append(manifest_path.parent)

        if manifest.upload_ids:
            receipt_path = (
                Path(output_root)
                / "abandoned_uploads"
                / f"{manifest_path.parent.name}.json"
            )
            write_json(
                receipt_path,
                {
                    "run_id": manifest.run_id,
                    "status": "abandoned",
                    "created_at": manifest.created_at,
                    "abandoned_at": reference.isoformat(),
                    "selected": {
                        key: manifest.selected[key]
                        for key in (
                            "exam",
                            "subject",
                            "topic",
                            "title",
                            "lesson_type",
                            "long_publish_at",
                            "short_publish_at",
                        )
                        if key in manifest.selected
                    },
                    "upload_ids": dict(manifest.upload_ids),
                    "previous_failure": manifest.failure,
                    "reason": (
                        "Unfinished jobs are discarded at startup and are never "
                        "resumed. Recorded YouTube uploads are preserved."
                    ),
                },
            )
            archived_count += 1

    removed_claims = 0
    if abandoned_run_ids:
        backlog_file = Path(backlog_path)
        entries = load_backlog(backlog_file)
        retained = [
            entry
            for entry in entries
            if not (
                entry.status == "claimed"
                and entry.claimed_run_id in abandoned_run_ids
            )
        ]
        removed_claims = len(entries) - len(retained)
        if removed_claims:
            save_backlog(retained, backlog_file)

    # Delete only after receipts and backlog changes have been saved. If any
    # filesystem operation fails, let startup fail closed before making a new job.
    for directory in directories_to_delete:
        shutil.rmtree(directory)

    if directories_to_delete or removed_claims:
        print(
            "Factory cleanup: "
            f"discarded {len(directories_to_delete)} unfinished job(s); "
            f"archived {archived_count} upload receipt(s); "
            f"removed {removed_claims} matching backlog claim(s)."
        )


def _new_run(output_root: Path) -> JobManifest:
    run_id = datetime.now(LOCAL_ZONE).strftime("%Y%m%d-%H%M%S-%f")
    run_dir = output_root / "jobs" / run_id
    return new_manifest(run_dir / "job.json", run_id)


def _output_path(manifest: JobManifest, filename: str) -> Path:
    path = manifest.path.parent / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _stored_output(manifest: JobManifest, key: str) -> Path:
    value = manifest.outputs.get(key)
    if not value:
        raise RuntimeError(f"manifest is missing output path: {key}")
    path = Path(value)
    if not path.exists():
        raise RuntimeError(f"completed stage artifact is missing: {path}")
    return path


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


def _short_segment_indices(lesson: Lesson) -> list[int]:
    for start, segment in enumerate(lesson.segments):
        if segment.kind != "question":
            continue
        indices = [start]
        for index in range(start + 1, len(lesson.segments)):
            if lesson.segments[index].kind == "question":
                break
            indices.append(index)
        return indices
    raise RuntimeError("lesson contains no question segment")


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
        key=lambda lesson_type: (
            available[lesson_type],
            -AUTO_LESSON_TYPES.index(lesson_type),
        ),
    )


def _select_job(
    jobs,
    adaptation,
    topic_families: tuple[TopicFamilyPerformance, ...] = (),
):
    if not jobs:
        raise RuntimeError("editorial queue produced no jobs")

    family_by_topic = {}
    for family in topic_families:
        subject = family.subject.strip().lower()
        weight = adaptation.topic_family_weights.get(
            (family.subject, family.family_name),
            1.0,
        )
        for topic in family.topics:
            family_by_topic[(subject, topic.strip().lower())] = weight

    def adjusted(job):
        subject = job.subject.strip().lower()
        family_weight = family_by_topic.get(
            (subject, job.topic.strip().lower()),
            1.0,
        )
        return (
            job.total_score
            * adaptation.subject_weights.get(subject, 1.0)
            * family_weight
        )

    return max(
        jobs,
        key=lambda job: (
            adjusted(job),
            job.total_score,
            -job.priority,
        ),
    )


def _explicit_editorial_job(exam: str, subject: str, topic: str) -> EditorialJob:
    exams = {"ssc": "SSC", "banking": "Banking", "railway": "Railway"}
    subjects = {"maths": "Maths", "reasoning": "Reasoning", "english": "English"}
    if not isinstance(exam, str) or exam.strip().lower() not in exams:
        raise ValueError("exam override must be SSC, Banking, or Railway")
    if not isinstance(subject, str) or subject.strip().lower() not in subjects:
        raise ValueError("subject override must be Maths, Reasoning, or English")
    if not isinstance(topic, str) or not topic.strip() or len(topic.strip()) > 120:
        raise ValueError("topic override must contain 1 to 120 characters")

    return EditorialJob(
        priority=1,
        exam=exams[exam.strip().lower()],
        subject=subjects[subject.strip().lower()],
        topic=topic.strip(),
        total_score=0.0,
        supporting_signal_indices=(),
        rationale="Explicit editorial override; no automatic demand score was assigned.",
    )


def _job_from_manifest(manifest: JobManifest) -> EditorialJob:
    selected = manifest.selected
    try:
        return EditorialJob(
            priority=int(selected["priority"]),
            exam=str(selected["exam"]),
            subject=str(selected["subject"]),
            topic=str(selected["topic"]),
            total_score=float(selected["total_score"]),
            supporting_signal_indices=tuple(selected["supporting_signal_indices"]),
            rationale=str(selected["rationale"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("manifest selection is invalid") from exc


def _history_upload_id(
    history_path: Path,
    lesson: Lesson,
    metadata: VideoMetadata,
    content_format: str,
) -> str | None:
    for entry in reversed(load_history(history_path)):
        if (
            entry.content_format == content_format
            and entry.status in {"published", "scheduled"}
            and entry.video_id
            and entry.exam.strip().lower() == lesson.exam.strip().lower()
            and entry.subject.strip().lower() == lesson.subject.strip().lower()
            and entry.topic.strip().lower() == lesson.topic.strip().lower()
            and entry.lesson_type.strip().lower() == lesson.lesson_type.strip().lower()
            and entry.title.strip() == metadata.primary_title.strip()
        ):
            return entry.video_id
    return None


def _record_publish_times(
    manifest: JobManifest,
    *,
    publish_mode: str,
    publish_at: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if "long_publish_at" in manifest.selected:
        long_at = (
            datetime.fromisoformat(manifest.selected["long_publish_at"])
            if manifest.selected["long_publish_at"]
            else None
        )
    else:
        long_at = publish_at
        if publish_mode == "scheduled" and long_at is None:
            long_at = _next_publish_time(datetime.now(LOCAL_ZONE))
        manifest.selected["long_publish_at"] = long_at.isoformat() if long_at else None
        short_at = (
            long_at + SHORT_PUBLISH_DELAY
            if publish_mode == "scheduled" and long_at is not None
            else None
        )
        manifest.selected["short_publish_at"] = short_at.isoformat() if short_at else None
        manifest.save()
        return long_at, short_at

    stored_short = manifest.selected.get("short_publish_at")
    short_at = datetime.fromisoformat(stored_short) if stored_short else None
    return long_at, short_at


def _next_publish_time(now: datetime) -> datetime:
    local_now = now.astimezone(LOCAL_ZONE)
    candidate = local_now.replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    )
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return candidate


def _print_post_run_analytics(history_path: str | Path) -> None:
    """Print a read-only channel performance snapshot after production completes."""
    print("\n=== Post-run YouTube snapshot (latest 10 uploads) ===")
    try:
        print_snapshot(history_path=history_path, limit=10)
    except Exception as exc:
        # A reporting failure must never turn a completed upload into a failed job.
        print(
            "Post-run analytics snapshot unavailable: "
            f"{exc}. Production is complete; do not rerun this job."
        )


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
    backlog_path: str | Path = DEFAULT_BACKLOG_FILE,
    factory_state_path: str | Path = DEFAULT_STATE_FILE,
    runs_per_day: int = 2,
    exam_override: str | None = None,
    subject_override: str | None = None,
    topic_override: str | None = None,
    resume: str | Path | None = None,
) -> Lesson:
    overrides = (exam_override, subject_override, topic_override)
    if any(value is not None for value in overrides) and not all(
        value is not None for value in overrides
    ):
        raise ValueError(
            "exam_override, subject_override, and topic_override must be supplied together"
        )
    if resume is not None and any(value is not None for value in overrides):
        raise ValueError("topic overrides are saved in the manifest and cannot be passed with resume")

    if resume is None:
        if max_jobs < 1:
            raise ValueError("max_jobs must be at least 1")
        if question_count < 1:
            raise ValueError("question_count must be at least 1")
        if not difficulty.strip():
            raise ValueError("difficulty must not be empty")
        if not language.strip():
            raise ValueError("language must not be empty")
        if publish_mode not in {"scheduled", "public"}:
            raise ValueError("publish_mode must be 'scheduled' or 'public'")
        validate_runs_per_day(runs_per_day)
        _cleanup_unfinished_jobs(output_root, backlog_path)
        _require_supported_edge_tts()
        manifest = _new_run(Path(output_root))
        manifest.selected["run_config"] = {
            "max_jobs": max_jobs,
            "question_count": question_count,
            "difficulty": difficulty,
            "language": language,
            "publish_mode": publish_mode,
            "history_path": str(Path(history_path).resolve()),
            "backlog_path": str(Path(backlog_path).resolve()),
            "factory_state_path": str(Path(factory_state_path).resolve()),
            "runs_per_day": runs_per_day,
            "exam_override": exam_override,
            "subject_override": subject_override,
            "topic_override": topic_override,
        }
        manifest.save()
    else:
        manifest = load_manifest(resume)
        if (manifest.failure or {}).get("stage") in _CANCELLED_FAILURE_STAGES:
            raise RuntimeError(
                "This job was cancelled or automatically closed and cannot be resumed."
            )
        if manifest.status == "complete":
            return Lesson.from_dict(read_json(_stored_output(manifest, "lesson")))

        config = manifest.selected.get("run_config")
        if not isinstance(config, dict):
            raise RuntimeError("resume manifest is missing run configuration")
        max_jobs = int(config["max_jobs"])
        question_count = int(config["question_count"])
        difficulty = str(config["difficulty"])
        language = str(config["language"])
        publish_mode = str(config["publish_mode"])
        history_path = config.get("history_path", history_path)
        backlog_path = config.get("backlog_path", backlog_path)
        factory_state_path = config.get("factory_state_path", factory_state_path)
        runs_per_day = int(config.get("runs_per_day", runs_per_day))
        exam_override = config.get("exam_override")
        subject_override = config.get("subject_override")
        topic_override = config.get("topic_override")
        restored_overrides = (exam_override, subject_override, topic_override)
        if any(value is not None for value in restored_overrides) and not all(
            value is not None for value in restored_overrides
        ):
            raise RuntimeError("resume manifest contains an incomplete topic override")
        validate_runs_per_day(runs_per_day)

    current_stage = "initialization"

    try:
        history_file = Path(history_path)
        factory_state_file = Path(factory_state_path)
        load_state(factory_state_file)

        if stage_complete(manifest, "editorial_selection"):
            job = _job_from_manifest(manifest)
            lesson_type = str(manifest.selected["lesson_type"])
        else:
            current_stage = "editorial_selection"
            if exam_override is not None:
                job = _explicit_editorial_job(
                    exam_override,
                    subject_override,
                    topic_override,
                )
                lesson_type = "practice"
                manifest.selected.update(
                    {
                        "priority": job.priority,
                        "exam": job.exam,
                        "subject": job.subject,
                        "topic": job.topic,
                        "total_score": job.total_score,
                        "supporting_signal_indices": [],
                        "rationale": job.rationale,
                        "lesson_type": lesson_type,
                        "selection_mode": "explicit_override",
                    }
                )
                manifest.checkpoint("editorial_selection")
            else:
                history = load_history(history_file)
                formats = analyze_formats(history)
                subjects = analyze_subjects(history)
                families = analyze_topic_families(history)
                adaptation = build_editorial_adaptation(formats, subjects, families)

                backlog_file = Path(backlog_path)
                backlog = release_stale_claims(load_backlog(backlog_file))
                recent_topics = recent_topic_keys(history)
                backlog = [
                    entry
                    for entry in backlog
                    if entry.key not in recent_topics
                    and not has_recent_related_topic(
                        entry.subject,
                        entry.topic,
                        history,
                    )
                ]

                pending_count = len(pending_jobs(backlog))
                if pending_count < max_jobs:
                    signals = discover_demand()
                    scores = score_topics(
                        signals,
                        recent_titles=tuple(
                            entry.title for entry in history if entry.title.strip()
                        ),
                        language=language,
                    )
                    jobs = build_editorial_queue(
                        scores,
                        max_jobs=max_jobs - pending_count,
                        history=history,
                        allow_related_fallback=pending_count == 0,
                    )
                    backlog = merge_jobs(backlog, jobs)

                jobs = pending_jobs(backlog)
                job = _select_job(jobs, adaptation, tuple(families))
                backlog = claim_job(
                    backlog,
                    job,
                    run_id=manifest.run_id,
                )
                save_backlog(backlog, backlog_file)

                lesson_type = _select_lesson_type(adaptation)
                manifest.selected.update(
                    {
                        "priority": job.priority,
                        "exam": job.exam,
                        "subject": job.subject,
                        "topic": job.topic,
                        "total_score": job.total_score,
                        "supporting_signal_indices": list(job.supporting_signal_indices),
                        "rationale": job.rationale,
                        "lesson_type": lesson_type,
                        "backlog_key": list(
                            (
                                job.exam.strip().lower(),
                                job.subject.strip().lower(),
                                job.topic.strip().lower(),
                            )
                        ),
                    }
                )
                manifest.checkpoint("editorial_selection")


        long_publish_at, short_publish_at = _record_publish_times(
            manifest,
            publish_mode=publish_mode,
            publish_at=publish_at,
        )

        if stage_complete(manifest, "concept"):
            concept_summary = read_json(_stored_output(manifest, "concept"))["concept_summary"]
        elif lesson_type == "concept_practice":
            current_stage = "concept"
            concept_summary = generate_concept_summary(
                subject=job.subject,
                exam=job.exam,
                topic=job.topic,
                language=language,
            )
            concept_path = _output_path(manifest, "concept.json")
            write_json(concept_path, {"concept_summary": concept_summary})
            manifest.checkpoint("concept", outputs={"concept": str(concept_path.resolve())})
        else:
            concept_summary = None

        if stage_complete(manifest, "questions_generated"):
            questions = [
                Question.from_dict(item)
                for item in read_json(_stored_output(manifest, "questions_generated"))
            ]
        else:
            current_stage = "questions_generated"
            questions = generate_questions(
                subject=job.subject,
                exam=job.exam,
                topic=job.topic,
                difficulty=difficulty,
                count=question_count,
                language=language,
            )
            questions_path = _output_path(manifest, "questions_generated.json")
            write_json(
                questions_path,
                [question.to_dict() for question in questions],
            )
            manifest.checkpoint(
                "questions_generated",
                outputs={"questions_generated": str(questions_path.resolve())},
            )

        if stage_complete(manifest, "questions_explained"):
            questions = [
                Question.from_dict(item)
                for item in read_json(_stored_output(manifest, "questions_explained"))
            ]
        else:
            current_stage = "questions_explained"
            questions = generate_explanations(questions, language=language)
            explained_path = _output_path(manifest, "questions_explained.json")
            write_json(
                explained_path,
                [question.to_dict() for question in questions],
            )
            manifest.checkpoint(
                "questions_explained",
                outputs={"questions_explained": str(explained_path.resolve())},
            )

        if stage_complete(manifest, "lesson"):
            lesson = Lesson.from_dict(read_json(_stored_output(manifest, "lesson")))
        else:
            current_stage = "lesson"
            lesson = assemble_lesson(
                questions,
                lesson_type=lesson_type,
                concept_summary=concept_summary,
            )
            lesson_path = _output_path(manifest, "lesson.json")
            write_json(lesson_path, lesson.to_dict())
            manifest.selected["title"] = lesson.title
            manifest.checkpoint("lesson", outputs={"lesson": str(lesson_path.resolve())})

        if stage_complete(manifest, "long_narration"):
            narration_segments = list(
                read_json(_stored_output(manifest, "long_narration"))["segments"]
            )
        else:
            current_stage = "long_narration"
            narration_segments = _narration_segments(lesson)
            narration_text = "\n\n".join(narration_segments)
            audio_path = _output_path(manifest, "narration.mp3")
            timing_path = _output_path(manifest, "word_timings.json")
            synthesize_speech(
                narration_text,
                audio_path,
                timing_path=timing_path,
            )
            narration_path = _output_path(manifest, "long_narration.json")
            write_json(
                narration_path,
                {"segments": narration_segments},
            )
            manifest.checkpoint(
                "long_narration",
                outputs={
                    "long_narration": str(narration_path.resolve()),
                    "narration_audio": str(audio_path.resolve()),
                    "narration_timing": str(timing_path.resolve()),
                },
            )

        english_segments_path = _output_path(manifest, "english_narration.json")
        if stage_complete(manifest, "english_localization"):
            english_narration_segments = list(
                read_json(english_segments_path)["segments"]
            )
        else:
            current_stage = "english_localization"
            english_narration_segments = generate_english_narration_segments(
                narration_segments,
                source_language=language,
            )
            write_json(
                english_segments_path,
                {"segments": english_narration_segments},
            )
            manifest.checkpoint(
                "english_localization",
                outputs={"english_narration": str(english_segments_path.resolve())},
            )

        audio_path = _stored_output(manifest, "narration_audio")
        if not stage_complete(manifest, "long_audio_qa"):
            current_stage = "long_audio_qa"
            audio_result = check_audio(audio_path)
            long_duration = audio_result.duration_seconds
            manifest.selected["long_duration"] = long_duration
            manifest.checkpoint("long_audio_qa")
        else:
            long_duration = float(manifest.selected["long_duration"])
            check_audio(audio_path, expected_duration_seconds=long_duration)

        duration_path = _output_path(manifest, "long_scene_durations.json")
        if stage_complete(manifest, "long_scene_durations"):
            durations = list(read_json(duration_path))
        else:
            current_stage = "long_scene_durations"
            durations = _scene_durations(narration_segments, long_duration)
            write_json(duration_path, durations)
            manifest.checkpoint(
                "long_scene_durations",
                outputs={"long_scene_durations": str(duration_path.resolve())},
            )

        video_path = _output_path(manifest, "long_form.mp4")
        if not stage_complete(manifest, "long_render"):
            current_stage = "long_render"
            render_long_form(
                lesson,
                audio_path,
                video_path,
                durations,
            )
            manifest.checkpoint(
                "long_render",
                outputs={"long_video": str(video_path.resolve())},
            )

        thumbnail_path = _output_path(manifest, "long_form_thumbnail.png")
        if not stage_complete(manifest, "long_thumbnail"):
            current_stage = "long_thumbnail"
            try:
                generate_thumbnail(lesson, thumbnail_path)
                manifest.selected["long_thumbnail_generated"] = True
                manifest.selected.pop("long_thumbnail_generation_error", None)
                manifest.checkpoint(
                    "long_thumbnail",
                    outputs={"long_thumbnail": str(thumbnail_path.resolve())},
                )
            except Exception as exc:
                warning = str(exc).strip()[:500] or type(exc).__name__
                manifest.selected["long_thumbnail_generated"] = False
                manifest.selected["long_thumbnail_generation_error"] = warning
                manifest.stages["long_thumbnail"] = {
                    "status": "warning",
                    "error": warning,
                }
                manifest.save()
                print(
                    "Warning: custom thumbnail could not be generated; "
                    f"video production will continue. {warning}"
                )
        else:
            thumbnail_path = _stored_output(manifest, "long_thumbnail")

        english_audio_path = _output_path(manifest, "english_narration.mp3")
        english_timing_path = _output_path(manifest, "english_word_timings.json")
        if not stage_complete(manifest, "english_audio"):
            current_stage = "english_audio"
            synthesize_speech(
                "\n\n".join(english_narration_segments),
                english_audio_path,
                voice=ENGLISH_TTS_VOICE,
                timing_path=english_timing_path,
            )
            manifest.checkpoint(
                "english_audio",
                outputs={
                    "english_audio": str(english_audio_path.resolve()),
                    "english_timing": str(english_timing_path.resolve()),
                },
            )
        else:
            english_audio_path = _stored_output(manifest, "english_audio")

        if not stage_complete(manifest, "english_audio_qa"):
            current_stage = "english_audio_qa"
            english_audio_result = check_audio(english_audio_path)
            manifest.selected["english_duration"] = english_audio_result.duration_seconds
            manifest.checkpoint("english_audio_qa")
        else:
            english_duration = float(manifest.selected["english_duration"])
            check_audio(
                english_audio_path,
                expected_duration_seconds=english_duration,
            )

        metadata_path = _output_path(manifest, "metadata.json")
        if stage_complete(manifest, "metadata"):
            metadata = VideoMetadata.from_dict(read_json(metadata_path))
        else:
            current_stage = "metadata"
            metadata = generate_metadata(lesson, language=language)
            write_json(metadata_path, metadata.to_dict())
            manifest.checkpoint(
                "metadata",
                outputs={"metadata": str(metadata_path.resolve())},
            )

        english_metadata_path = _output_path(manifest, "english_metadata.json")
        if stage_complete(manifest, "english_metadata"):
            english_metadata = VideoMetadata.from_dict(read_json(english_metadata_path))
        else:
            current_stage = "english_metadata"
            english_metadata = generate_metadata(lesson, language="English")
            write_json(english_metadata_path, english_metadata.to_dict())
            manifest.checkpoint(
                "english_metadata",
                outputs={"english_metadata": str(english_metadata_path.resolve())},
            )

        short_indices = _short_segment_indices(lesson)
        short_narration_segments = [
            narration_segments[index] for index in short_indices
        ]

        short_audio_path = _output_path(manifest, "short_narration.mp3")
        short_timing_path = _output_path(manifest, "short_word_timings.json")
        if not stage_complete(manifest, "short_narration"):
            current_stage = "short_narration"
            synthesize_speech(
                "\n\n".join(short_narration_segments),
                short_audio_path,
                timing_path=short_timing_path,
            )
            short_narration_path = _output_path(manifest, "short_narration.json")
            write_json(
                short_narration_path,
                {"segments": short_narration_segments, "indices": short_indices},
            )
            manifest.checkpoint(
                "short_narration",
                outputs={
                    "short_narration": str(short_narration_path.resolve()),
                    "short_audio": str(short_audio_path.resolve()),
                    "short_timing": str(short_timing_path.resolve()),
                },
            )
        else:
            short_narration_segments = list(
                read_json(_stored_output(manifest, "short_narration"))["segments"]
            )
            short_indices = list(
                read_json(_stored_output(manifest, "short_narration"))["indices"]
            )
            short_audio_path = _stored_output(manifest, "short_audio")

        if not stage_complete(manifest, "short_audio_qa"):
            current_stage = "short_audio_qa"
            short_audio_result = check_audio(short_audio_path)
            if short_audio_result.duration_seconds > SHORT_MAX_DURATION_SECONDS:
                raise RuntimeError("derived Short exceeds YouTube's 3-minute limit")
            manifest.selected["short_duration"] = short_audio_result.duration_seconds
            manifest.checkpoint("short_audio_qa")
        else:
            short_duration = float(manifest.selected["short_duration"])
            check_audio(
                short_audio_path,
                expected_duration_seconds=short_duration,
            )

        english_short_audio_path = _output_path(manifest, "english_short_narration.mp3")
        english_short_timing_path = _output_path(manifest, "english_short_word_timings.json")
        english_short_narration_segments = [
            english_narration_segments[index] for index in short_indices
        ]
        if not stage_complete(manifest, "english_short_audio"):
            current_stage = "english_short_audio"
            synthesize_speech(
                "\n\n".join(english_short_narration_segments),
                english_short_audio_path,
                voice=ENGLISH_TTS_VOICE,
                timing_path=english_short_timing_path,
            )
            manifest.checkpoint(
                "english_short_audio",
                outputs={
                    "english_short_audio": str(english_short_audio_path.resolve()),
                    "english_short_timing": str(english_short_timing_path.resolve()),
                },
            )
        else:
            english_short_audio_path = _stored_output(manifest, "english_short_audio")

        if not stage_complete(manifest, "english_short_audio_qa"):
            current_stage = "english_short_audio_qa"
            english_short_audio_result = check_audio(english_short_audio_path)
            if english_short_audio_result.duration_seconds > SHORT_MAX_DURATION_SECONDS:
                raise RuntimeError("English Short audio exceeds YouTube's 3-minute limit")
            manifest.selected["english_short_duration"] = english_short_audio_result.duration_seconds
            manifest.checkpoint("english_short_audio_qa")
        else:
            english_short_duration = float(manifest.selected["english_short_duration"])
            check_audio(
                english_short_audio_path,
                expected_duration_seconds=english_short_duration,
            )

        short_duration = float(manifest.selected["short_duration"])
        short_duration_path = _output_path(manifest, "short_scene_durations.json")
        if stage_complete(manifest, "short_scene_durations"):
            short_durations = list(read_json(short_duration_path))
        else:
            current_stage = "short_scene_durations"
            short_durations = _scene_durations(
                short_narration_segments,
                short_duration,
            )
            write_json(short_duration_path, short_durations)
            manifest.checkpoint(
                "short_scene_durations",
                outputs={"short_scene_durations": str(short_duration_path.resolve())},
            )

        short_video_path = _output_path(manifest, "short.mp4")
        if not stage_complete(manifest, "short_render"):
            current_stage = "short_render"
            render_short(
                lesson,
                short_audio_path,
                short_video_path,
                short_indices,
                short_durations,
            )
            manifest.checkpoint(
                "short_render",
                outputs={"short_video": str(short_video_path.resolve())},
            )

        short_metadata_path = _output_path(manifest, "short_metadata.json")
        if stage_complete(manifest, "short_metadata"):
            short_metadata = VideoMetadata.from_dict(read_json(short_metadata_path))
        else:
            current_stage = "short_metadata"
            if len(metadata.title_candidates) < 2:
                raise RuntimeError("metadata has no alternate title for the Short")
            short_metadata = VideoMetadata(
                primary_title=metadata.title_candidates[1],
                title_candidates=metadata.title_candidates,
                description=metadata.description,
                hashtags=metadata.hashtags,
                tags=metadata.tags,
                series_context=metadata.series_context,
                category_id=metadata.category_id,
                default_language=metadata.default_language,
            )
            write_json(short_metadata_path, short_metadata.to_dict())
            manifest.checkpoint(
                "short_metadata",
                outputs={"short_metadata": str(short_metadata_path.resolve())},
            )

        if not stage_complete(manifest, "youtube_auth"):
            current_stage = "youtube_auth"
            youtube = get_youtube_client()
            manifest.checkpoint("youtube_auth")
        else:
            youtube = get_youtube_client()

        if not stage_complete(manifest, "long_upload"):
            current_stage = "long_upload"
            existing_id = _history_upload_id(
                history_file,
                lesson,
                metadata,
                "long_form",
            )
            if existing_id:
                long_video_id = existing_id
            else:
                long_video_id = upload_video(
                    youtube,
                    lesson,
                    metadata,
                    video_path,
                    mode=publish_mode,
                    publish_at=long_publish_at,
                    history_path=history_file,
                    content_format="long_form",
                    english_metadata=english_metadata,
                )
            manifest.upload_ids["long_form"] = long_video_id
            manifest.checkpoint("long_upload")
        else:
            long_video_id = manifest.upload_ids["long_form"]

        if not stage_complete(manifest, "long_thumbnail_upload"):
            current_stage = "long_thumbnail_upload"
            if not thumbnail_path.is_file():
                warning = manifest.selected.get(
                    "long_thumbnail_generation_error",
                    "generated thumbnail file is unavailable",
                )
                manifest.selected["long_thumbnail_uploaded"] = False
                manifest.selected["long_thumbnail_error"] = warning
                manifest.stages["long_thumbnail_upload"] = {
                    "status": "warning",
                    "error": warning,
                }
                manifest.save()
            else:
                try:
                    upload_thumbnail(youtube, long_video_id, thumbnail_path)
                    manifest.selected["long_thumbnail_uploaded"] = True
                    manifest.selected.pop("long_thumbnail_error", None)
                    manifest.checkpoint("long_thumbnail_upload")
                    print(f"Custom thumbnail uploaded for long-form video {long_video_id}.")
                except Exception as exc:
                    warning = str(exc).strip()[:500] or type(exc).__name__
                    manifest.selected["long_thumbnail_uploaded"] = False
                    manifest.selected["long_thumbnail_error"] = warning
                    manifest.stages["long_thumbnail_upload"] = {
                        "status": "warning",
                        "error": warning,
                    }
                    manifest.save()
                    print(
                        f"Warning: custom thumbnail was not set for {long_video_id}; "
                        f"video production will continue. {warning}"
                    )

        if not stage_complete(manifest, "short_upload"):
            current_stage = "short_upload"
            existing_id = _history_upload_id(
                history_file,
                lesson,
                short_metadata,
                "shorts",
            )
            if existing_id:
                short_video_id = existing_id
            else:
                short_video_id = upload_video(
                    youtube,
                    lesson,
                    short_metadata,
                    short_video_path,
                    mode=publish_mode,
                    publish_at=short_publish_at,
                    history_path=history_file,
                    content_format="shorts",
                    english_metadata=VideoMetadata(
                        primary_title=english_metadata.title_candidates[1],
                        title_candidates=english_metadata.title_candidates,
                        description=english_metadata.description,
                        hashtags=english_metadata.hashtags,
                        tags=english_metadata.tags,
                        series_context=english_metadata.series_context,
                        category_id=english_metadata.category_id,
                        default_language=english_metadata.default_language,
                    ),
                )
            manifest.upload_ids["shorts"] = short_video_id
            manifest.checkpoint("short_upload")
        else:
            short_video_id = manifest.upload_ids["shorts"]

        if not stage_complete(manifest, "analytics"):
            current_stage = "analytics"
            ingest_metrics(history_path=history_file)
            manifest.checkpoint("analytics")

        if not stage_complete(manifest, "backlog_complete"):
            current_stage = "backlog_complete"
            backlog_key = manifest.selected.get("backlog_key")
            if backlog_key:
                if not isinstance(backlog_key, list) or len(backlog_key) != 3:
                    raise RuntimeError("manifest backlog key is invalid")
                backlog = load_backlog(Path(backlog_path))
                backlog = complete_job(
                    backlog,
                    exam=str(backlog_key[0]),
                    subject=str(backlog_key[1]),
                    topic=str(backlog_key[2]),
                    run_id=manifest.run_id,
                )
                save_backlog(backlog, Path(backlog_path))
            manifest.checkpoint("backlog_complete")

        state = load_state(factory_state_file)
        save_state(
            record_run(
                state,
                run_id=manifest.run_id,
                status="complete",
                now=datetime.now(timezone.utc),
                runs_per_day=runs_per_day,
            ),
            factory_state_file,
        )
        manifest.complete()
        _print_post_run_analytics(history_file)
        return lesson

    except Exception as exc:
        try:
            state = load_state(Path(factory_state_path))
            save_state(
                record_run(
                    state,
                    run_id=manifest.run_id,
                    status="failed",
                    now=datetime.now(timezone.utc),
                    runs_per_day=runs_per_day,
                ),
                Path(factory_state_path),
            )
        except Exception:
            pass
        manifest.fail(current_stage, exc)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one fresh autonomous education-factory production job."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--history-path", default=str(DEFAULT_HISTORY_FILE))
    parser.add_argument("--max-jobs", type=int, default=10)
    parser.add_argument("--question-count", type=int, default=DEFAULT_QUESTIONS)
    parser.add_argument("--difficulty", default=DEFAULT_DIFFICULTY)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument(
        "--publish-mode",
        choices=("scheduled", "public"),
        default="scheduled",
    )
    parser.add_argument("--backlog-path", default=str(DEFAULT_BACKLOG_FILE))
    parser.add_argument("--factory-state-path", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--runs-per-day", type=int, choices=(1, 2), default=2)
    parser.add_argument("--exam-override", choices=("SSC", "Banking", "Railway"), default=None)
    parser.add_argument("--subject-override", choices=("Maths", "Reasoning", "English"), default=None)
    parser.add_argument("--topic-override", default=None)
    args = parser.parse_args()

    lesson = run_factory(
        output_root=args.output_root,
        history_path=args.history_path,
        max_jobs=args.max_jobs,
        question_count=args.question_count,
        difficulty=args.difficulty,
        language=args.language,
        publish_mode=args.publish_mode,
        backlog_path=args.backlog_path,
        factory_state_path=args.factory_state_path,
        runs_per_day=args.runs_per_day,
        exam_override=args.exam_override,
        subject_override=args.subject_override,
        topic_override=args.topic_override,
    )
    print(f"Completed: {lesson.title}")


if __name__ == "__main__":
    main()
