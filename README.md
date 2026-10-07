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

## Current state

**Engineering complete — final factory audit passed**

The factory now has one direct production path, persistent ranked backlog, resume-safe job manifests, analytics-driven adaptation, and once/twice-daily cadence state. The remaining step is the external YouTube account/OAuth launch gate and the first real end-to-end run.

The dedicated YouTube channel has not been created yet, so real OAuth, upload, and analytics execution remain intentionally deferred until the factory is fully built.

The native Shorts “Related Video” control was also checked against the supported API surface and is not exposed by the YouTube Data API, so no undocumented automation was added.