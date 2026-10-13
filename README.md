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
- Latest successful factory job: `20261014-021921-953424`, `SSC Maths — Simple Interest: Practice`. Long-form ID: `IYHW9v5uo9Y`; scheduled for 10:00 IST on October 14, 2026.
- Automatic recovery resumed the unfinished localization job without duplication. This run preserved original Hinglish in segments 9, 17, 21, and 28 after two failed targeted repairs, protecting numbers and answers.
- The snapshot did not visibly list the corresponding Simple Interest Short or its ID. Confirm via the next normal factory snapshot; do not start a separate run just to check, and do not create a duplicate.
- Metrics are available only through October 12. Shorts currently show more discovery than recent long-form, while two recent long-forms showed only 9–12 seconds average view duration in small samples. Do not delete videos or mass-retitle; investigate long-form opening/pacing before broad strategy changes.
- Routine operation: sync `main`, then run `python factory.py`; recovery, upload stages, analytics ingestion, and the read-only post-run snapshot are handled by the factory. Do not ask the user to run local tests.
- The post-run header formatting regression was validated by GitHub Actions run #30: 229 tests passed, with 5 non-fatal warnings. The local user does not need to run tests.

- Native Shorts “Related Video” controls are not exposed by the YouTube Data API; no undocumented automation is used.
