from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from audio_qa import check_audio
from channel_history import DEFAULT_HISTORY_FILE, load_history, recent_topic_keys
from concept_generator import generate_concept_summary
from demand_discovery import discover_demand
from editorial_adaptation import build_editorial_adaptation
from factory_state import DEFAULT_STATE_FILE, load_state, record_run, save_state, validate_runs_per_day
from editorial_queue import EditorialJob, build_editorial_queue
from explanation_generator import generate_explanations
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
from narration import synthesize_speech
from question import Question
from question_generator import generate_questions
from shorts_renderer import render_short
from subject_analysis import analyze_subjects
from topic_family_analysis import analyze_topic_families
from topic_scorer import score_topics
from youtube_analytics import ingest_metrics
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
from youtube_uploader import upload_video

DEFAULT_OUTPUT_ROOT = Path("output")
DEFAULT_QUESTIONS = 10
DEFAULT_DIFFICULTY = "mixed"
DEFAULT_LANGUAGE = "Hinglish"
AUTO_LESSON_TYPES = ("practice", "timed_test", "concept_practice", "revision")
LOCAL_ZONE = ZoneInfo("Asia/Kolkata")
SHORT_MAX_DURATION_SECONDS = 180.0
SHORT_PUBLISH_DELAY = timedelta(hours=2)


def _slug(value: str) -> str:
    clean = re.sub(r"[^\w]+", "-", value.strip().lower(), flags=re.UNICODE)
    return clean.strip("-") or "lesson"


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
    backlog_path: str | Path = DEFAULT_BACKLOG_FILE,
    factory_state_path: str | Path = DEFAULT_STATE_FILE,
    runs_per_day: int = 2,
    resume: str | Path | None = None,
) -> Lesson:
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
        }
        manifest.save()
    else:
        manifest = load_manifest(resume)
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
                )
                backlog = merge_jobs(backlog, jobs)

            jobs = pending_jobs(backlog)
            job = _select_job(jobs, adaptation)
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
                )
            manifest.upload_ids["long_form"] = long_video_id
            manifest.checkpoint("long_upload")
        else:
            long_video_id = manifest.upload_ids["long_form"]

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
        description="Run or resume one autonomous education-factory production job."
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
    parser.add_argument("--resume", default=None)
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
        resume=args.resume,
    )
    print(f"Completed: {lesson.title}")


if __name__ == "__main__":
    main()
