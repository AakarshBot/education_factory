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

## Current state — 2026-10-09

- **Live channel:** Exam Session India (@examsessionindia).
- YouTube OAuth, Data API uploads, and Analytics API access are operational through the existing factory authentication path.
- Two public long-form/Short pairs have been produced. The latest lesson is Railway Reasoning — Direction and Distance: Practice.
- Read-only analytics snapshot: `python youtube_analytics.py`.
- **Publishing schedule:** long-form at 10:00 IST, derived Short at 18:00 IST (8 hours later).
- The schedule correction is committed to `main`; pull the latest changes and rerun the focused preflight before another factory job. Do not publish another pair until that suite passes.
- Day 3 analytics are still too early to justify deleting videos, changing metadata, or altering the locked India-first SSC/Banking/Railway educational strategy.
- The native Shorts “Related Video” control is not exposed by the YouTube Data API, so no undocumented automation was added.