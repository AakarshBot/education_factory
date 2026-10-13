# Education Factory

**This is ChatGPT's channel and factory.**

This repository builds the autonomous YouTube education factory defined in `PROJECT_CONTEXT.md`.

## Operating model

**Run the factory once or twice per day -> the factory handles production, publishing, scheduling, and learning.**

The user should not perform routine backend work.

## Locked channel strategy

- India-first audience
- Hindi/Hinglish
- SSC, Banking, Railway competitive-exam preparation
- Maths, Reasoning, English
- Long-form + Shorts
- ₹0 paid production requirement
- Original educational experiences rather than repetitive slideshow content
- Full YPP target before the February 1, 2027 threshold change

## Development rule

Build only the next required function.

No speculative wrappers, compatibility layers, duplicate pipelines, placeholder implementations, or unnecessary dependencies.

The project context is the source of truth for the current build state and exact next step.

## Current state — 2026-10-14

- **Live channel:** Exam Session India (@examsessionindia).
- YouTube OAuth, Data API uploads, and Analytics API access are operational.
- Publishing schedule: long-form at 10:00 IST, derived Short at 18:00 IST (8 hours later).
- Latest complete production run: SSC Reasoning — Coding-Decoding: Alphabet Shifts and Position Patterns. Both uploads are scheduled; manifest: `output/jobs/20261012-015646-925002/job.json`.
- **Normal operation:** run `python factory.py`. On startup, the factory automatically resumes a recent recoverable job, closes abandoned incomplete jobs older than six hours, and removes only backlog claims belonging to those abandoned runs. An intentionally cancelled job is never resumed. English localization makes two targeted correction attempts and then falls back to the exact source segment if a protected-token violation persists. At successful completion, it prints a read-only snapshot of the latest 10 uploads, with current visibility/counters and available Analytics metrics. No standalone analytics command, manual manifest scan, `--resume`, or local pytest run is part of routine operation.
- Analytics ingestion runs as a factory stage. Scheduled videos should be checked by the next normal production run after their release slots; do not launch a second run just to inspect publication status.
- Factory startup recovery and the cancelled-job resume guard passed **226 tests, 5 non-fatal warnings** in GitHub Actions run #23: https://github.com/AakarshBot/education_factory/actions/runs/38174482822. October 14 changes add a post-run snapshot and a more deliberate split between long-form and Short title candidates. GitHub Actions run #25 passed **228 tests, 5 non-fatal warnings**: https://github.com/AakarshBot/education_factory/actions/runs/38467616985.
- The early video sample is too small to justify deleting videos, changing metadata, or altering the locked India-first SSC/Banking/Railway educational strategy.
- Native Shorts “Related Video” controls are not exposed by the YouTube Data API; no undocumented automation is used.
