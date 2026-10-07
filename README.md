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

**Step 4.3 — Long-form renderer**

The factory now renders the assembled 16:9 lesson scenes into an MP4 with validated narration audio, local FFmpeg, and no new dependency.