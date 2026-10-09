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

## Current state — 2026-10-10

- **Live channel:** Exam Session India (@examsessionindia).
- YouTube OAuth, Data API uploads, and Analytics API access are operational through the existing factory authentication path.
- Two public long-form/Short pairs have been produced. The latest lesson is Railway Reasoning — Direction and Distance: Practice.
- Read-only analytics snapshot: `python youtube_analytics.py`.
- **Publishing schedule:** long-form at 10:00 IST, derived Short at 18:00 IST (8 hours later).
- The third production job is saved as failed at English localization (segment 19); it stopped before rendering/upload. Resume that same manifest after syncing `main`; do not start a new factory job.
- English localization now performs a single targeted repair request for invalid protected-token segments, then applies the same strict invariant checks.
- Automated GitHub Actions testing is live. The full suite passed at commit `2e036bc8cc43287aa1fe2815bd8b48b9ec6a2954`: **216 passed, 5 warnings**. Check [Actions](https://github.com/AakarshBot/education_factory/actions) for current validation; do not ask the user to run tests.
- The early four-video sample is too small to justify deleting videos, changing metadata, or altering the locked India-first SSC/Banking/Railway educational strategy.
- The native Shorts “Related Video” control is not exposed by the YouTube Data API, so no undocumented automation was added.