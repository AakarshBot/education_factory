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

**Phase 6 / Step 6.5 — Conservative automatic editorial adaptation**

The factory now has direct YouTube upload/scheduling, analytics ingestion, format comparison, subject comparison, topic-family analysis, and conservative editorial-adaptation stages, with production state stored in local channel history.

The dedicated YouTube channel has not been created yet, so real OAuth, upload, and analytics execution remain intentionally deferred until the factory is fully built.

The native Shorts “Related Video” control was also checked against the supported API surface and is not exposed by the YouTube Data API, so no undocumented automation was added.