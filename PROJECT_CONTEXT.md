**THIS IS CHATGPT'S CHANNEL AND FACTORY**

# Education Factory — Master Context

## 0. Governing ownership and workflow

This repository is the factory for ChatGPT's new YouTube channel. The user owns the external Google/YouTube account and can operate the channel normally, but editorial, production, publishing, testing, analytics, and iteration decisions belong to the factory unless the user explicitly overrides them.

The user's desired operating model is:

**USER RUNS THE FACTORY ONCE OR TWICE PER DAY → FACTORY DOES EVERYTHING ELSE AUTOMATICALLY.**

The user should not need to perform backend work for normal production. Manual actions must be limited to unavoidable external account setup, authorization, verification, or platform actions that cannot be performed through the factory.

### Interaction rule for future chats

### Current live state — 2026-10-09

- **This is ChatGPT's channel and factory.**
- The real YouTube channel is **Exam Session India (@examsessionindia)**.
- The first two long-form/Short pairs are real public launch assets. The corrected publishing slots are **10:00 IST for long-form and 18:00 IST for the derived Short** (8-hour spacing).
- YouTube OAuth, the YouTube Data API, and the YouTube Analytics API are operational through the existing factory authentication path.
- The existing local `data/channel_history.json` is the production ledger for videos created by the factory.
- **New in this step:** `python youtube_analytics.py` is the direct, read-only live-performance snapshot command. It uses current YouTube Data API counters for views/likes/comments and YouTube Analytics metrics for engaged views, watch time, average view metrics, and subscribers gained; it also reports publication age and views/hour.
- The snapshot command does **not** write to channel history, change production state, or alter editorial decisions.
- The current public sample is two long-form videos plus two derived Shorts. It is still too small for reliable editorial adaptation; do not delete or repackage videos from these early view counts alone.
- The fresh-render audit is now complete. The current main renderer satisfies the existing visual edge-QA contract, and regression coverage now exercises the production long-form scenes plus rendered Short scenes.
- The immediate next manual action is to sync the local checkout to main and run the focused preflight pytest command before any factory job; no editorial or analytics-driven strategy change is being made.
Every implementation step must leave this context file current enough that a new chat can continue from the repository state without relying on prior conversation memory.

After each completed step:
1. Update this file with what was implemented, what is tested, what remains, and the exact next step.
2. Commit the context/code changes to GitHub.
3. Tell the user either the exact manual action required from them, or **"No manual action. Reply: yes, continue."**
4. The default next user message should be only **"yes, continue"**.
5. Do not ask the user to restate project context that is already recorded here.

---

# 1. LOCKED CHANNEL STRATEGY

## Channel concept

**Primary market:** India / Indian subcontinent.

**Primary language:** Hindi/Hinglish.

**Secondary accessibility:** English text/metadata where useful and YouTube automatic dubbing may be evaluated later.

**Audience:** people preparing for Indian competitive examinations, initially focusing on:
- SSC
- Banking
- Railway

## Core subjects

Initial subject mix:
- Quantitative Aptitude / Maths
- Reasoning
- English

The initial emphasis is Maths + Reasoning because these are especially suitable for deterministic validation and highly visual explanation. English is part of the launch mix but does not control the architecture.

## What the channel is NOT

Do not build this as:
- current-affairs/news recap content
- generic GK/facts slideshow content
- motivational quote content
- an AI-avatar teacher channel
- copied previous-paper compilations without meaningful original teaching
- repetitive "question → answer" clones with superficial changes
- mass-produced template videos whose substantive value is nearly identical

The channel must create genuine educational value and materially different learning experiences.

## Core product

The channel is an **exam-session factory**, not a slideshow factory.

Primary long-form products:
1. **Practice sessions** — focused question sets with explanations.
2. **Timed tests / mini mocks** — viewers participate, answer, then see the solution.
3. **Concept + practice lessons** — concise teaching followed by worked questions.
4. **Previous-year-question analysis** — used only when source/use rights and attribution are appropriate; add original explanation and context.
5. **Revision / marathon sessions** — longer study sessions when the material justifies the length.

Shorts are derived from the same educational system:
- challenge questions
- common mistakes
- fast methods
- short explanations
- mini test moments
- high-value exam patterns

Shorts should normally connect viewers to a relevant long-form session when appropriate.

## Visual identity

The finished videos should feel like a credible digital exam/practice product, not an AI slideshow.

Core visual language:
- premium digital examination-product aesthetic
- soft warm exam canvas with a subtle grid and restrained green/teal signals
- strong information hierarchy rather than oversized generic cards
- readable question typography with compact question/progress rails
- exam-style answer rows with explicit correct/incorrect states
- worked solutions with numbered reasoning steps
- progress and result indicators that feel native to the learning product
- lesson-type-specific composition rather than one universal frame
- subtle depth, borders, and spacing instead of decorative clutter
- visuals should support the teaching task, not merely fill the frame

Avoid:
- generic white-and-blue quiz templates
- excessive rounded-card stacking
- stock-photo filler
- generic AI-generated images for decoration
- fake classroom backgrounds
- talking-head avatars
- excessive TikTok-style motion
- identical frame choreography in every upload
- permanent decorative UI that adds no instructional value

The design system may be consistent, but the instructional composition and visual hierarchy must vary with the content. Visual variation is not a substitute for substantive educational variation.

Current visual implementation: the v4 soft product palette is active in both long-form and Shorts canvases. The warm canvas uses quieter grid spacing, lighter shadows, tighter card geometry, and restrained green/teal signals. Question states include a dedicated instructional visual panel driven directly from subject/topic keywords, using deterministic diagrams rather than decorative filler. The next visual batch should refine instructional composition only when the rendered preview shows a concrete problem.

Developer visual QA tool — 2026-10-08
Added `visual_preview.py`, a zero-dependency local preview utility that calls the real long-form and Shorts renderers with representative lesson types and state scenes. It produces `output/visual_preview/visual_preview_long.png` and `visual_preview_short.png`. This is development-only and is not part of the production pipeline.

Visual correction — 2026-10-08
The first preview exposed two concrete problems: the dark blue background was visually wrong for the channel, and the preview contained layout cards without a genuine instructional visual layer. The palette was changed to a soft warm ivory/sage system while retaining the product theme. A deterministic `draw_topic_visual()` primitive was added and wired into long-form and Shorts question scenes. It renders instructional diagrams for syllogism/logic, percentages, ratio/proportion, averages, directions, probability, English grammar, plus a useful given→rule→check fallback. The preview now includes both a reasoning visual and a percentage visual so visual QA covers actual instructional imagery rather than only typography/cards.

The visual layer is deliberately deterministic and dependency-free; it is part of the production renderer, not decorative preview-only scaffolding.

Visual polish — 2026-10-08
After manual review, the user rated the new soft theme about 7/10 and asked for polish without changing its identity. The canvas was softened further: lower-contrast 96px grid spacing, a thinner top accent, lighter shadow material, slightly tighter card radii, and cleaner visual-panel headers. No new dependency, motion system, or parallel renderer was introduced.

Text layout polish — 2026-10-08
Shared text primitives now size content against the actual available box height and width instead of depending on fixed font sizes alone. Question, answer, choice, solution, and highlighted-text blocks scale down when needed and keep consistent box-relative insets. Choice text also reserves space for status labels so long choices cannot run underneath CORRECT/INCORRECT. The behavior is centralized in `visual_primitives.py`, so long-form and Shorts inherit the same text fitting and indentation rules.

Instructional visual accuracy polish — 2026-10-08
Topic visuals no longer embed arbitrary example values that could conflict with the real question. Percentage, ratio/proportion, and average visuals are now conceptual diagrams without hard-coded question answers/numbers; the syllogism visual likewise presents unlabeled relationship sets rather than asserting a specific relationship. This keeps the visual layer useful while remaining truthful for arbitrary generated questions.
---

# 2. MONETIZATION STRATEGY

## Primary YPP target

Target the current full YPP threshold before the February 2027 change:

**1,000 subscribers + 4,000 qualified public watch hours**

rather than relying on the Shorts-only route.

The factory is aiming to become application-ready well before the deadline and should not plan around a last-minute January application.

## Why long-form is essential

Long-form is the watch-hour engine and supports the stronger monetization path.

Shorts are the discovery/subscriber engine.

The factory will deliberately operate both formats.

## Additional revenue path

Explore YouTube Shopping / affiliate opportunities as the channel becomes eligible, but affiliate selection must never determine editorial winners. Products/tools should only be recommended when they are genuinely relevant to the viewer's educational/decision need.

The factory must maintain clear separation between:
- educational/editorial decision
- commercial monetization opportunity

No undisclosed commercial bias.

---

# 3. ZERO-COST CONSTRAINT

The factory must be buildable and operable with **₹0 paid production spend**.

No required paid:
- AI model subscription
- TTS service
- stock footage library
- image library
- editing suite
- cloud rendering service
- analytics subscription
- automation platform

Free-tier APIs/services are acceptable only when they can support the expected workload reliably.

Local computation is preferred where practical.

The architecture must minimize API calls and avoid unnecessary dependencies.

---

# 4. AUTONOMOUS OPERATING MODEL

## User action

Normal production should require only:

**Run factory** once or twice per day.

## Factory responsibilities

The factory should eventually:
1. discover demand/opportunities
2. evaluate topic usefulness and novelty
3. choose the day's production queue
4. avoid duplicating recent channel content
5. generate questions
6. validate answers deterministically wherever possible
7. generate explanations
8. assemble lesson structure
9. generate Hindi/Hinglish narration
10. create long-form visuals
11. derive Shorts
12. generate titles/descriptions/metadata
13. upload to YouTube
14. schedule publication
15. collect available analytics
16. evaluate what worked
17. update the next production queue
18. retire weak formats/topics
19. expand winning topic families

No normal human approval step is part of the intended production path.

## Safety / failure behavior

The factory should fail closed for:
- unverified question answers
- unusable narration
- rendering failures
- missing required media
- invalid metadata
- upload failures

A failed job should not silently publish bad educational content.

---

# 5. EDITORIAL PRINCIPLES

The factory optimizes for:
1. Viewer usefulness.
2. Search/discovery demand.
3. Retention.
4. Subscriber conversion.
5. Watch hours.
6. Originality.
7. Production reliability.
8. Commercial relevance.
9. Policy safety.

Do NOT optimize solely for upload volume.

High frequency is useful in this market, but repetitive low-value output is a liability.

### YouTube YPP authenticity guard — LOCKED 2026-10-08
YouTube's current monetization policy states that channels must be original/authentic and not mass-produced, generic, or repetitive. Similar formats are allowed when the substance is materially varied and provides educational or other value; AI-assisted production is not itself disqualifying. The factory therefore must optimize for genuine instructional differentiation, not cosmetic randomness. Source: https://support.google.com/youtube/answer/1311392

The unit of production is an **educational experience**, not a video template.

One source lesson may legitimately produce multiple distinct outputs, but each published output must have its own clear viewer purpose.

---

# 6. INITIAL PUBLISHING TARGETS

Initial working target:
- **3 long-form videos/week**
- **1–2 Shorts/day**

The factory may build ahead of schedule so production runs can happen once or twice daily without requiring an upload every time.

First test period:

**14 days**

Initial content coverage:
- Maths
- Reasoning
- English
- Mixed/mini-mock

The exact distribution remains data-driven after the first meaningful analytics sample.

Initial month target:
- roughly 12 long-form videos
- roughly 30 Shorts

These are operating targets, not guarantees.

---

# 7. BUILD MAP

The build must happen in direct, independently testable steps.

## Phase 0 — Foundation

### Step 0.1 — Project context — **COMPLETE**
Created and maintained as the single source of truth for the factory.

### Step 0.2 — Minimal repository skeleton — **COMPLETE**
Created only repository-level hygiene/documentation needed before production code: `.gitignore`, `.env.example`, and `README.md`. No placeholder application code or speculative dependencies were added.

### Step 0.3 — Local/free dependency policy — **COMPLETE**
Locked the minimum dependency set to the current direct Python stack; no heavyweight ML stack or unnecessary dependency was added.

### Step 0.4 — Config and secret handling — **COMPLETE**
Added one direct `config.py` boundary that loads `.env`, exposes the small set of runtime settings currently needed, and validates secrets only when a concrete stage requires them. Updated `.env.example` with Gemini, YouTube OAuth, and TTS settings. Added focused `tests/test_config.py` coverage for defaults, environment overrides, and required-setting failures. No credentials are committed.

---

## Phase 1 — Educational content engine

### Step 1.1 — Question schema — **COMPLETE**
Added `question.py` with one canonical immutable `Question` dataclass containing exactly the locked question contract:
- subject
- exam
- topic
- difficulty
- question
- choices when applicable
- correct answer
- explanation
- shortcut/method
- source type
- source reference when applicable

The schema is JSON-safe through `to_dict()` and can be reconstructed through `from_dict()`. It contains no LLM calls, provider logic, rendering logic, or business rules.
Added `tests/test_question.py` covering the complete field set and dict round-trip behavior.

### Step 1.2 — Deterministic validators — **COMPLETE**
Added `validators.py` with a deliberately narrow deterministic validation layer.

Implemented:
- safe arithmetic-expression evaluation using Python AST with only numeric constants, unary signs, addition, subtraction, multiplication, division, and bounded integer powers
- exact numeric answer parsing using `Fraction` / `Decimal`
- Maths answer verification by comparing the generated answer against a machine-checkable expression
- multiple-choice validation for minimum choice count, uniqueness, and membership of the correct answer
- fail-closed validation when a Maths question has no machine-checkable expression

Important design decision:
- The canonical `Question` schema remains unchanged.
- A machine-checkable Maths expression is supplied to validation as generation metadata rather than stored as another public question field.
- The validator does not attempt to "prove" arbitrary natural-language Maths questions from prose. That would be brittle and unsafe.
- No LLM retry, generation, explanation validation, or topic rules were added at this stage.

Added `tests/test_validators.py` covering exact arithmetic, number parsing, mismatched answers, unsafe expressions, required Maths expressions, and multiple-choice integrity.

### Step 1.3 — Question generation — **COMPLETE**
Added `question_generator.py` with one direct `generate_questions()` path using Gemini's REST `generateContent` endpoint and structured JSON output. Google's current API documentation confirms Gemini 3.8 Flash is a stable production model and supports structured JSON responses through a response schema. citeturn875388search2turn931795search1turn875388search3

The generator:
- makes one Gemini request for a requested question batch
- requests exactly the requested count through structured output
- generates original questions only
- requires `source_type="original"` and no source reference
- requires a machine-checkable arithmetic expression for Maths
- converts returned records into the canonical `Question` objects
- runs the deterministic validator on every generated question before returning anything
- rejects wrong counts, malformed structured responses, HTTP/API failures, and validation failures
- performs no hidden regeneration loop

The public `Question` schema remains unchanged; `math_expression` is generation-time validation metadata and is removed before a `Question` object is returned.

Added `tests/test_question_generator.py` covering successful structured generation, deterministic rejection of a wrong Maths answer, invalid count handling, and HTTP failure handling.

Model/cost note:
- The active Google pricing page currently lists `gemini-3.8-flash` as free-tier for standard text input/output. citeturn875388search0
- The generator therefore remains within the locked ₹0 production constraint, subject to the provider's active free-tier limits.

### Step 1.4 — Explanation generation — **COMPLETE**
Added `explanation_generator.py` with one direct batch function, `generate_explanations()`.

The stage:
- accepts only the existing `Question` objects and treats `correct_answer` as immutable
- sends the question, choices, and verified answer to Gemini
- requests only indexed explanation strings through structured JSON
- returns new `Question` objects with only `explanation` changed
- ignores any unexpected model fields such as attempted answer changes
- rejects missing, duplicate, out-of-range, or empty explanations
- uses one model call for the whole batch
- does not add a retry/rewrite loop

Efficiency correction made during Step 1.4:
- `question_generator.py` no longer asks Gemini to write explanations. It now sets `explanation` to an empty string so explanation generation occurs exactly once in the dedicated stage.
- `tests/test_question_generator.py` now asserts that the question stage leaves explanation empty.

Added `tests/test_explanation_generator.py` covering answer preservation, structured request handling, rejection of missing explanations, and empty-input handling.

Current Gemini REST implementation remains based on the documented `generateContent` endpoint and structured JSON response configuration. Google's current API documentation explicitly recommends validating structured output values in application code. citeturn723793search1turn723793search4

### Step 1.5 — Lesson assembler — **COMPLETE**
Added `lesson.py` as the canonical immutable lesson contract and `lesson_assembler.py` as the deterministic sequencing stage.

The assembler:
- accepts only `Question` objects that already contain verified answers and non-empty explanations
- creates one explicit sequence of renderable `LessonSegment` records
- supports the five locked learning experiences: practice, timed test, concept + practice, PYQ analysis, and revision/marathon
- never calls Gemini and never changes question data
- adds a 15-second timed phase only for timed tests
- requires explicit concept text for concept + practice rather than inventing a concept with an LLM
- requires `source_type="pyq"` and a non-empty `source_reference` for PYQ analysis
- exposes shortcuts as separate segments when a question has one
- preserves the original question order
- supports an explicit title override while otherwise deriving a deterministic title

Added `tests/test_lesson_assembler.py` covering all five lesson types, sequencing, source requirements, concept requirements, missing explanations, invalid input, and custom titles.

Important architecture decision:
- Lesson assembly is intentionally deterministic. It does not introduce a generation stage or attempt to infer missing teaching content.
- Concept + practice accepts `concept_summary` as an input contract; a future concept-writing stage may supply it before assembly.
- PYQ analysis only assembles already-sourced PYQs and carries the source reference into the lesson sequence for later rendering/attribution.

---

## Phase 2 — Research and topic selection

### Step 2.1 — Demand discovery — **COMPLETE**
Added `demand_discovery.py` as the first research-stage module.

The discovery stage:
- uses the public YouTube Data API directly over HTTP; no SDK or new dependency
- searches the locked exam/subject matrix: SSC, Banking, Railway × Maths, Reasoning, English
- adds the current year to the default queries
- collects two independent signals per query: YouTube relevance ordering and recent-video view-count ordering
- restricts results to videos published within the requested recent window
- records raw video/title/channel/date/description/rank/query/order data without assigning an editorial score
- uses the India region by default
- makes two `search.list` calls per query and no extra statistics calls
- validates all inputs before any network request
- fails clearly on missing API configuration, invalid arguments, HTTP errors, and malformed responses

The YouTube Data API documentation currently lists `search.list` at 1 quota unit per request in its dedicated search quota bucket and supports `relevance`, `date`, and `viewCount` ordering. Public searches require an API key but not OAuth.  citeturn342974search0turn342974search4

Configuration:
- Added `YOUTUBE_API_KEY` to `config.py` and `.env.example`.
- OAuth credentials remain separate and are still reserved for authenticated channel operations.

Added `tests/test_demand_discovery.py` covering default query coverage, the two discovery signals, configuration errors, invalid inputs, and HTTP failures.

The discovery layer intentionally does **not** score topics, call Gemini, infer search volume, or choose what to publish. Those decisions belong to Step 2.2.

### Step 2.2 — Topic scoring — **COMPLETE**
Added `topic_scorer.py` as the scoring stage between raw demand discovery and editorial queue selection.

The scorer:
- accepts the raw `DemandSignal` records from Step 2.1
- uses one structured Gemini batch call to identify concrete educational topic candidates and score five qualitative dimensions
- computes `demand_score` itself from the supplied YouTube ranks, so the model cannot invent popularity data
- combines six dimensions into one weighted `total_score`:
  - demand 25%
  - exam relevance 20%
  - novelty 15%
  - educational value 20%
  - visual potential 10%
  - production reliability 10%
- supports recent channel titles as optional novelty context; when history is empty, novelty is forced to a neutral 50 rather than fabricated
- validates exams, subjects, signal references, score ranges, duplicate candidates, and rationales before returning results
- returns candidates sorted by total score
- does not choose the publishing queue, generate questions, or modify channel history

Added `tests/test_topic_scorer.py` covering demand/weighted-score calculation, context forwarding, neutral novelty without history, invalid inputs, invalid model candidates, duplicate candidates, and HTTP failures.

---

### Step 2.3 — Editorial queue — **COMPLETE**
Added `editorial_queue.py` as the deterministic handoff from scored topics to production jobs.

The queue:
- orders candidates by `total_score` descending
- uses exam/subject/topic lexical ordering only as a deterministic tie-break
- carries the evidence indexes and scoring rationale into each `EditorialJob`
- removes duplicate exam/subject/topic keys
- respects an explicit `max_jobs` limit
- does not invent a minimum score, content format, subject rotation, or historical-duplication rule
- performs no LLM calls

Added `tests/test_editorial_queue.py` covering score-first ordering, evidence preservation, limits, deterministic ties, deduplication, and invalid input.

Because historical channel memory is deliberately deferred to Step 2.4, this queue does not pretend to know what has already been published.

### Step 2.4 — Historical memory — **COMPLETE**
Added `channel_history.py` as a lightweight local JSON history store.

The history layer:
- stores exam, subject, topic, lesson type, title, status, timestamps, optional YouTube video ID/publication time, and optional numeric metrics
- loads a missing history file as empty history
- writes under the ignored `data/` directory without adding a dependency
- supports appending new production records
- identifies recent active topics from `published` and `scheduled` entries
- ignores failed entries when deciding whether a topic should be avoided
- fails closed on malformed history or invalid time windows

Updated `editorial_queue.py` so it can directly receive history and exclude recently published/scheduled topics while preserving the existing score-first ordering.

Added `tests/test_channel_history.py` and expanded `tests/test_editorial_queue.py` for persistence, recent-topic filtering, failed-topic recovery, and existing queue behavior.

The history store is deliberately local and small. Analytics-specific interpretation remains in Phase 6; the `metrics` field is only a persistence slot for later measurements.



---

## Phase 3 — Voice and audio

### Step 3.1 — Hindi/Hinglish narration pipeline — **COMPLETE**
Added `narration.py` as the direct speech-synthesis stage using the existing `edge-tts` dependency.

The narration stage:
- accepts the final narration text and writes an audio file directly
- defaults to the currently supported Hindi neural voice `hi-IN-MadhurNeural`
- allows the configured `TTS_VOICE` or an explicit voice override
- supports rate, volume, and pitch settings without adding another service
- creates the output directory when needed
- fails closed when input text is empty, synthesis errors, or no audio file is produced
- does not create timing metadata yet; timing is intentionally reserved for Step 3.2

Configuration:
- `TTS_VOICE` now defaults to `hi-IN-MadhurNeural` in `config.py` and `.env.example`.

The current edge-tts project exposes Python `Communicate` with voice/rate/volume/pitch parameters and saves synthesized audio directly. citeturn264207search0turn264207search5
Microsoft currently lists `hi-IN-MadhurNeural` as a supported Hindi (India) standard neural voice. citeturn187269search1

Added `tests/test_narration.py` covering default/configured/explicit voice selection, audio-setting forwarding, empty input, and missing output.

### Step 3.2 — Timing contract — **COMPLETE**
Extended `narration.py` so the same Edge-TTS synthesis call can optionally produce stable word timing metadata.

The timing path:
- requests Edge-TTS `WordBoundary` events
- writes the exact generated audio and timing data from the same synthesis stream
- converts Edge-TTS 100-nanosecond offsets/durations into seconds
- preserves spoken word text alongside each timing
- validates monotonic timings and positive word durations
- records overall spoken timing duration
- fails closed when no word-boundary events or no timing file are produced
- does not rewrite, split, or otherwise modify narration text
- does not add a second TTS call or a timing dependency

Added timing-specific tests to `tests/test_narration.py`.

The current Edge-TTS Python implementation exposes `Communicate.stream()` with `WordBoundary` events containing text, offset, and duration; the offsets are represented in 100-nanosecond ticks. citeturn556359search1turn556359search4

### Step 3.3 — Audio QA — **COMPLETE**
Added `audio_qa.py` as the final audio gate before rendering.

The QA stage:
- uses local `ffprobe` to verify an audio stream, positive duration, sample rate, and channel count
- uses local `ffmpeg` `volumedetect` to detect audio that is effectively silent
- rejects missing files, empty files, unreadable media, unusably short audio, and incomplete metadata
- can compare actual audio duration with an expected narration/timing duration using an explicit tolerance
- performs no repair, normalization, regeneration, or hidden retry
- adds no new Python dependency

Added `tests/test_audio_qa.py`, using real generated WAV files and real FFmpeg/FFprobe execution for valid, silent, short, missing, empty, and mismatched audio cases.

### Step 4.1 — Visual primitives

---

## Phase 4 — Visual engine

### Step 4.1 — Visual primitives — **COMPLETE**
Added `visual_primitives.py` using the locked Pillow dependency.

The module provides direct deterministic drawing primitives for:
- question cards with question numbering
- choices with selected/correct states
- timers
- answer reveals
- worked calculation / solution steps
- highlighted text
- simple instructional flow diagrams
- progress indicators
- score/result screens

The primitives share one visual language: clean exam-product cards, readable type, neutral surfaces, and restrained instructional accents. Text rendering supports Devanagari and Latin text so Hindi/Hinglish content can be rendered without adding a font package to the project.

The primitives draw onto caller-provided Pillow images so later renderers can compose lesson-specific scenes without adding a wrapper framework or duplicate visual pipeline.

### Step 4.2 — Lesson-specific layouts — **COMPLETE**
Added `lesson_layouts.py` as the direct composition layer between lesson segments and the future renderers.

Implemented distinct question compositions for:
- practice — question-first card with choices underneath
- timed test — progress + question + timer + choices
- concept + practice — question/choice layout reserved below the concept segment
- PYQ analysis — source context plus a two-column question/choice treatment
- revision — compact centered question with progress

Also implemented segment scenes for concept text, source attribution, answer reveal, explanation/solution, shortcut, timer, and score/result.

The layouts reuse the Step 4.1 primitives rather than creating a second visual system. No animation engine, media dependency, or template framework was added.

### Step 4.3 — Long-form renderer — **COMPLETE**
Added `long_form_renderer.py` as the direct 16:9 video assembly stage.

The renderer:
- accepts an assembled `Lesson`, its already-generated audio, an output path, and one positive duration per lesson segment
- requires a 16:9 canvas
- validates that scene durations exactly match the lesson segment count
- checks the supplied narration audio through the existing Audio QA gate and requires the total scene duration to match the audio within the existing tolerance
- renders each lesson segment through `lesson_layouts.py`
- writes deterministic PNG scenes to a temporary workspace
- uses the local FFmpeg concat demuxer to assemble the scenes
- muxes the validated audio as the MP4 soundtrack
- produces H.264/YUV420P output with fast-start metadata
- replaces the destination only after a successful render
- fails closed on invalid durations, bad scene sizes, media-tool errors, or missing output

No animation framework, video Python wrapper, or new dependency was added.

The renderer deliberately receives scene durations explicitly. The lesson/narration orchestration stage can supply those durations from its final timing contract without embedding timing guesses inside the video renderer.

### Step 4.4 — Shorts renderer — **COMPLETE**
Added `shorts_renderer.py` as the direct portrait rendering stage.

The Shorts renderer:
- renders selected lesson segments into a 1080x1920 canvas
- reuses the same Step 4.1 educational primitives rather than creating a second design system
- uses portrait-specific compositions so question, choices, timer, answer, explanation, shortcut, concept, source, and result scenes remain readable on a Shorts canvas
- accepts an explicit segment selection and one duration per selected scene
- validates selection, duration, and timing inputs before rendering
- reuses the existing Audio QA gate before video assembly
- assembles scenes with local FFmpeg into H.264/YUV420P MP4
- replaces the destination only after a successful render
- fails closed on invalid selections, media errors, or missing output

No new dependency or animation/video framework was added.

### Step 4.5 — Visual QA — **COMPLETE**
Added `visual_qa.py` as the automated visual gate before publishing.

Implemented:
- required visual-asset existence, non-empty, and image-readability checks
- exact scene geometry checks for the requested output canvas
- pixel-content bounding checks so rendered content cannot touch the unsafe outer edge
- final-video geometry checks
- final-video positive-duration checks
- final-video audio-stream checks
- expected-duration comparison with a small explicit tolerance

Integrated the QA gate directly into both renderers:
- `long_form_renderer.py` validates every generated 16:9 scene and validates the temporary MP4 before replacing the final output.
- `shorts_renderer.py` validates every generated 9:16 scene and validates the temporary MP4 before replacing the final output.

The QA layer does not attempt to repair, crop, resize, regenerate, or silently continue. A failed visual gate stops the render.

No new dependency was added.

---

## Phase 5 — Publishing

### Step 5.1 — Metadata generation — **COMPLETE**
Added `metadata_generator.py` as the direct publishing-metadata stage.

The metadata stage:
- uses one structured Gemini batch call
- receives only the completed `Lesson` contract plus the requested output language
- produces exactly 5 distinct title candidates, with the first treated as the primary publishing title
- generates a unique viewer-facing description grounded only in supplied lesson facts
- generates 3-5 directly relevant hashtags
- generates a small set of precise keyword tags rather than stuffing
- generates a short recurring series-context label
- sets the YouTube Education category deterministically to category `27`
- sets the primary metadata language to Hindi (`hi`), consistent with the channel's Hindi/Hinglish strategy
- rejects oversized/empty titles, descriptions beyond the current API limit, malformed hashtags, oversized tag sets, URLs, angle brackets, duplicates, and empty metadata fields
- does not invent dates, scores, instructors, certifications, outcomes, downloads, or guarantees
- performs no second generation/rewrite loop

Current platform constraints reflected in the stage:
- YouTube titles are limited to 100 characters.
- Video descriptions are limited to 5,000 bytes in the API.
- Video keyword tags have a 500-character total limit.
- YouTube warns against misleading metadata and excessive/unrelated tags/hashtags. citeturn127069search0turn127069search2turn290784search1turn290784search2turn127069search3

### Step 5.2 — YouTube OAuth — **COMPLETE**
Added `youtube_auth.py` as the direct authentication boundary for the publishing client.

The OAuth stage:
- uses Google's installed/desktop OAuth flow through the already-locked `google-auth-oauthlib` dependency
- requests only `https://www.googleapis.com/auth/youtube.upload`, the minimum scope required for the planned video-upload/scheduling stage
- loads an existing authorized-user token from the configured token file when it is still valid
- refreshes an expired token locally when a refresh token is available
- opens a local browser authorization flow only when a usable token is unavailable
- saves the resulting authorized-user credentials to the ignored token file for future unattended runs
- builds the YouTube Data API v3 client through the existing `google-api-python-client` dependency
- exposes a direct `python youtube_auth.py` setup command without adding a wrapper application

Security:
- OAuth client secrets and the authorized-user token remain local and are already ignored by Git.
- No credentials are printed, committed, or embedded in repository source.

Google's current YouTube documentation recommends a Desktop app OAuth client for command-line/installed applications and identifies `youtube.upload` as an authorization scope for video uploads. citeturn686940search0turn686940search1

### Step 5.3 — Upload and scheduling — **COMPLETE**
Added `youtube_uploader.py` as the direct video upload/scheduling stage.

The upload stage:
- consumes the completed `Lesson`, `VideoMetadata`, and rendered MP4 directly
- uses the existing authenticated YouTube client and `videos.insert` with the minimum existing OAuth scope
- uses one resumable upload request and does not add an SDK or wrapper layer
- publishes immediately in `public` mode or schedules in `scheduled` mode
- forces scheduled videos to `private` with an ISO 8601 `publishAt` value, as required by the YouTube API
- appends the generated hashtags to the supplied description and passes the generated keyword tags, category, and Hindi default language directly to YouTube
- validates the final combined description against YouTube's 5,000 UTF-8-byte limit before making a network request
- validates the video file, mode, and schedule time before making a network request
- fails closed on upload errors or responses without a YouTube video ID
- records the returned video ID, publication/schedule status, lesson identity, and title in the local channel history
- reports a history-write failure explicitly after a successful upload rather than silently treating the upload as complete

Added `tests/test_youtube_uploader.py` covering immediate publish metadata, scheduled/private `publishAt`, invalid modes, missing schedule times, past schedule times, upload failures, missing video IDs, and missing video files.

Current platform note:
- YouTube's current `videos.insert` documentation supports the `youtube.upload` scope and `status.publishAt` for private, never-before-published videos. The current API revision history also states that video uploads use a separate upload quota bucket and the upload cost was reduced to 1 unit per call in the current documentation. citeturn706286search0turn706286search2
- Unverified API projects created after July 28, 2020 have uploaded videos restricted to private viewing until the project completes YouTube's required audit. The factory therefore does not treat a requested public upload as proof that YouTube has made the video public. citeturn706286search0turn706286search1

### Step 5.4 — Shorts → long-form linking — **PLATFORM LIMITATION**
Reviewed the current supported YouTube interfaces before adding code.

Finding:
- YouTube Studio supports a native **Related Video** field on Shorts, which creates a clickable link below the channel handle.
- The supported YouTube Data API video resource does **not** expose a corresponding related-video ID field for `videos.insert` or `videos.update`.
- Shorts descriptions and comments are explicitly non-clickable, so the factory must not pretend that adding a YouTube URL there is equivalent.
- The factory therefore does **not** add an undocumented/browser-automation workaround or a second publishing pipeline.

This step is complete as an API-capability boundary. Native Related Video assignment remains a platform/Studio action unless YouTube exposes a supported API in the future. citeturn372775search0turn372775search1turn999992search1

---

## Phase 6 — Analytics and self-improvement

### Step 6.1 — Metrics ingestion — **COMPLETE**
Added `youtube_analytics.py` as the direct analytics ingestion stage.

The analytics stage:
- uses the supported YouTube Analytics API v2 reports endpoint through the existing Google API dependency
- queries video-level metrics for all known video IDs using one report per batch, up to the API's documented 500-video filter limit
- collects views, engaged views, estimated minutes watched, average view duration, average view percentage, likes, comments, and subscribers gained
- accepts an explicit date window, with a default 30-day window ending on the previous day to avoid intentionally querying an incomplete current day
- converts report values into numeric metrics and fails closed on malformed responses or API errors
- writes the newest metrics back into the existing local channel-history entries rather than creating a second production ledger
- makes no editorial decisions; interpretation belongs to later Phase 6 steps
- performs no hidden retry loop

OAuth correction required by the current Analytics API:
- `youtube_auth.py` requests all three required scopes: `youtube.upload`, `youtube.readonly`, and `yt-analytics.readonly`
- the current `reports.query` documentation requires the Analytics read scope for Analytics queries
- installed-app OAuth does not support incremental authorization, so the final launch authorization should request all required scopes together. citeturn866611search0turn866611search5

Added `tests/test_youtube_analytics.py` covering normal metric retrieval, 500-ID batching, history persistence, default windows, empty histories, date validation, duplicate IDs, API failures, and malformed reports.

The real Analytics API cannot be exercised yet because the dedicated YouTube channel/account has not been created.

### Step 6.2 — Format analysis — **COMPLETE**
Added `format_analysis.py` as the deterministic comparison layer for the five locked learning formats.

The analysis:
- reads existing `HistoryEntry` records and uses only published videos with a video ID and measured view data
- groups results by lesson format and normalizes the canonical names for timed test, concept + practice, and PYQ analysis
- reports measured-video count, total/average/median views, total/average/median watch minutes, average view percentage, engagement rate, and subscribers gained per 1,000 views
- uses median per-video values alongside totals so one unusually large or small video does not dominate the descriptive comparison
- marks a format `comparison_ready` only after 3 measured videos; smaller samples remain visible but are explicitly insufficient for a format-level conclusion
- performs no ranking, reweighting, topic selection, or strategy change

YouTube Analytics supports video-level dimensions and metrics including views, estimated minutes watched, average view duration, average view percentage, likes, comments, and subscribers gained, which are the measurements already persisted by Step 6.1. citeturn484122search0turn484122search4

Added `tests/test_format_analysis.py` covering grouping, median handling, exclusion of scheduled/unmeasured entries, engagement/subscriber rates, lesson-type normalization, empty history, and insufficient-sample handling.

The real channel is now live; this remains a descriptive analysis contract until its existing minimum-sample rule is met.

### Step 6.3 — Subject analysis — **COMPLETE**
Added `subject_analysis.py` as the deterministic comparison layer for the three locked launch subjects.

The analysis:
- reports **Maths, Reasoning, and English** in a stable order even when a subject has no measured videos yet
- normalizes common subject labels such as `math`, `mathematics`, `quantitative aptitude`, and `reason` into the locked subject names
- uses only published videos with a YouTube video ID and measured view data
- reports measured-video count, total/average/median views, total/average/median watch minutes, average view percentage, engagement rate, and subscribers gained per 1,000 views
- ignores scheduled entries and subjects outside the three core launch subjects
- marks a subject `comparison_ready` only after 3 measured videos
- performs no ranking, editorial reweighting, topic selection, or automatic strategy change

Added `tests/test_subject_analysis.py` covering subject normalization, stable three-subject output, filtering, rate calculations, empty history, and the minimum-sample threshold.

The real channel has no analytics data yet, so this remains a ready-to-run comparison contract rather than a live subject verdict.

### Step 6.4 — Topic-family analysis — **COMPLETE**
Added `topic_family_analysis.py` as the deterministic topic-clustering layer over published channel history.

The analysis:
- clusters related topic names **within the same subject**, avoiding false merges across Maths, Reasoning, and English
- removes generic learning-format words such as “questions”, “practice”, and “test” from the family signal
- normalizes simple plural variants so topic names such as “Percentage”, “Percentages”, and “Percentage shortcuts” can belong to one family
- uses lexical token overlap only; it does not add embeddings, another API, or an LLM dependency
- reports the member topic names, measured-video count, total/average/median views, total/average/median watch minutes, average view percentage, engagement rate, and subscribers gained per 1,000 views
- marks a family `comparison_ready` only after 3 measured videos
- orders comparison-ready families ahead of insufficient-sample families, using median views as the descriptive ordering signal
- performs no editorial reweighting or automatic strategy change

Added `tests/test_topic_family_analysis.py` covering lexical clustering, plural normalization, subject separation, filtering, rate calculations, insufficient samples, and empty history.

The real channel is now live; this remains a descriptive family analysis contract until its existing minimum-sample rule is met.
### Step 6.5 — Automatic editorial adaptation — **COMPLETE**
Added `editorial_adaptation.py` as the conservative decision layer over the format, subject, and topic-family analyses.

The adaptation policy:
- changes nothing unless at least **2 comparable groups** are each `comparison_ready` (3+ measured videos)
- uses the existing median-view evidence rather than a single video's performance
- computes relative performance against the mean median-view level of the comparable groups
- caps every evidence-based multiplier at **0.90–1.10**
- leaves groups with insufficient evidence at exactly **1.0**
- returns separate weights for learning format, core subject, and subject-specific topic family
- performs no LLM calls and does not mutate historical records
- produces a reusable adaptation profile for the production/orchestration stage to consume; it does not silently alter the current strategy outside that pipeline

This deliberately makes early-channel adaptation gradual: one anomalous video cannot change the editorial mix, and a single measured category cannot establish a winner.

Added `tests/test_editorial_adaptation.py` covering minimum evidence, conservative weight changes, preservation of neutral weights for non-ready groups, and adaptation bounds.

The adaptation profile remains neutral unless its existing minimum-evidence rule is satisfied by measured published videos.

---

### Step 6.6 — Read-only live snapshot — **COMPLETE**

Added the direct read-only live-performance command in `youtube_analytics.py`.

The command:
- runs as `python youtube_analytics.py` with optional `--limit` and `--days` flags
- reads the factory's existing local channel-history video IDs
- uses the existing YouTube Data API client for current views, likes, comments, and publication time
- uses the existing YouTube Analytics API client for engaged views, watch time, average view metrics, and subscribers gained
- reports long-form and Shorts separately, with publication age and views/hour for early-stage comparison
- never writes channel history and never changes production or editorial state

The implementation uses the existing OAuth path and adds no dependency or dashboard.

Focused tests cover the new Data API counter retrieval, Analytics `engagedViews`, snapshot merging, publication-age calculation, and the read-only history guarantee.

Interpretation rule: YouTube Analytics is not real-time and official documentation says processing can introduce 48–72 hours of latency. Current per-video counters therefore come from the YouTube Data API, while watch/engagement metrics are treated as delayed analytics evidence. citeturn201681search5

Analytics snapshot visibility correction — 2026-10-09
The live snapshot now includes each returned video's YouTube `privacyStatus` and scheduled `publishAt` so a missing view count can be distinguished from a private/scheduled asset. This is a readout-only correction; production/editorial logic is unchanged.

## Phase 7 — Autonomous daily operation


Runtime correction — 2026-10-09
The new read-only analytics CLI was missing its `argparse` import, causing a `NameError` on launch. Added the missing standard-library import only; no analytics behavior changed. Targeted tests remain the verification gate before the next manual run.

### Step 7.1 — One-click / one-command factory run — **COMPLETE**

Added `factory.py` as the direct production entry point and `tests/test_factory.py` for orchestration coverage.

The command connects the existing stages in one path:
1. load channel history
2. analyze format, subject, and topic-family performance
3. build conservative editorial adaptation
4. discover current YouTube demand
5. score topics
6. build the editorial queue and apply subject evidence
7. choose an available lesson format using the format evidence
8. generate verified questions
9. generate explanations
10. assemble the lesson
11. build narration directly from the educational lesson
12. synthesize Hindi/Hinglish speech
13. run audio QA
14. derive scene durations from the narration
15. render and QA the 16:9 long-form video
16. generate and save metadata
17. authenticate YouTube only at the publishing boundary
18. upload/schedule and persist channel history
19. ingest available analytics

Important fail-closed boundary:
- The command does not publish until question validation, explanations, narration, audio QA, rendering/video QA, and metadata validation have all succeeded.
- Upload failures remain hard failures.
- A successful upload is recorded in channel history before the analytics refresh.

Initial automatic lesson types are deliberately limited to the formats the current upstream generation engine can instantiate without hidden inputs:
- practice
- timed_test
- revision

`concept_practice` still requires explicit concept text, and `pyq_analysis` requires sourced PYQ questions. The factory does not fabricate either input.

Default command behavior:
- one production lesson per run
- 10 questions
- mixed difficulty
- Hinglish
- scheduled publishing by default
- absent an explicit publish time, scheduled publication defaults to the next 10:00 India time; its derived Short is scheduled at 18:00 India time

No new dependency or wrapper framework was added.

Testing:
- Added focused orchestration tests covering lesson-format selection, default behavior, publish-time calculation, scene-duration accounting, and end-to-end mocked stage ordering.
- The factory source was syntax-checked and core helper logic was executed successfully in isolation.
- A full repository pytest run remains unavailable because this environment cannot resolve GitHub from the shell.
### Step 7.2 — Daily queue generation — **COMPLETE**
Implemented by the persistent production backlog in Phase 8 / Step 8.2; future jobs are now separated from current production execution.

### Step 7.3 — Complete the remaining locked lesson products — **COMPLETE**

Added automatic concept generation through `concept_generator.py`. When the conservative format adaptation selects `concept_practice`, the factory generates a concise teaching concept for the chosen exam/subject/topic and passes it directly into the deterministic lesson assembler.

Added `pyq_source.py` as the explicit PYQ provenance and reuse gate. A PYQ can enter the lesson system only when:
- the question identifies `source_type="pyq"`
- the source reference matches the verified source record
- the source is on the expected official HTTPS domain
- an explicit reuse-permission flag is true
- a rights note is present
- duplicate questions are rejected

The automatic factory still excludes PYQ from its lesson-format selector because current official-source behavior does not provide a sufficiently reliable public, reusable, machine-readable question feed for all three launch exams. SSC currently exposes answer-key/question-paper materials through its official site, while RRB materials can be candidate/login-limited, and IBPS explicitly states that it does not provide question papers or right-answer keys. citeturn867560search3turn867560search26turn964187search0

This is an intentional safety boundary, not missing plumbing: the factory will not scrape a third-party PYQ repository and assume that copying the question text is permitted.

Testing:
- Added focused concept-generation tests for structured output, empty responses, and invalid input.
- Added PYQ provenance/reuse tests for official-domain checking, explicit reuse evidence, reference matching, minimum source counts, duplicate protection, and verified-question selection.
- Added factory coverage for automatic `concept_practice` selection.
- No new dependency was added.
- A full repository pytest run remains unavailable because this environment cannot resolve GitHub from the shell.
## Phase 8 — Reliability and autonomous execution

### Step 8.1 — Production job manifest and resume-safe execution — **COMPLETE**

Added `job_manifest.py` and integrated it directly into `factory.py`.

Every production run now creates a compact JSON manifest containing:
- unique run ID and creation time
- run configuration, including the original history path
- selected exam, subject, topic, editorial score, lesson format, and rationale
- per-stage completion/failure status
- output artifact paths
- long-form and Short YouTube video IDs
- exact long-form/Short publish times
- current failure stage and error text

The factory checkpoints after each meaningful production stage and restores successful stages from saved artifacts rather than regenerating them.

Persisted/recoverable artifacts include:
- concept summary
- generated questions
- explained/verified questions
- assembled lesson
- narration text and word-timing audio
- long-form scene durations and MP4
- metadata
- Short narration/timing audio
- Short scene durations and MP4
- Short metadata

Resume behavior:
- `python factory.py --resume <path-to-job.json>` continues a failed/incomplete run.
- A completed job returns directly from its saved lesson artifact.
- The original topic, format, run settings, history path, and publish schedule are preserved.
- A successful long/Short upload is skipped on resume when its stage is already checkpointed; the history ledger is also checked to avoid an obvious duplicate upload after a normal post-upload checkpoint interruption.
- Missing artifacts for a checkpointed stage fail closed instead of silently regenerating or publishing partial output.
- Manifest writes and JSON artifact writes use atomic replacement so ordinary process interruption does not leave half-written JSON files.

External side-effect boundary:
- There remains an unavoidable tiny failure window between a successful YouTube upload and the local checkpoint/history write. The uploader already persists history immediately after upload, and the factory also checks history before retrying. The system therefore minimizes duplicate-upload risk but cannot provide mathematically exactly-once behavior across a remote API side effect and a local filesystem without a transactional external service.

Testing:
- Added focused manifest tests for round-tripping, failure persistence, completion, missing/invalid manifests, and atomic checkpoint writes.
- Reworked factory tests around deterministic lesson selection and a mocked render failure/resume cycle.
- The resume test verifies question generation and the first narration synthesis are not repeated after a failed render.
- Added artifact-restore support to the existing Lesson and VideoMetadata contracts.
- A full repository pytest run remains unavailable because this environment cannot resolve GitHub from the shell; committed tests were reviewed for the new recovery path.

### Step 8.2 — Automated daily queue generation and backlog management — **COMPLETE**

Added `production_backlog.py` and integrated it directly into `factory.py`.

The production backlog:
- persists a small ranked pool in `data/production_backlog.json`
- stores the same editorial job fields used by the factory, without duplicating lesson-generation logic
- deduplicates by exam + subject + topic
- refreshes an existing pending topic when newer demand research returns it
- never rewrites a claimed job from a live run
- marks the selected job as claimed with the run ID before production continues
- removes the claimed job only after the full run completes, through an explicit `backlog_complete` manifest stage
- automatically releases claims older than 7 days so abandoned jobs can return to the pool
- drops backlog topics that are now active in channel history, preventing recently scheduled/published topics from resurfacing
- writes the backlog atomically

Factory behavior:
- normal runs first consume the highest-scoring pending backlog job using the current editorial adaptation
- demand discovery/scoring/research runs only when pending backlog falls below the configured queue target (`max_jobs`)
- the queue is replenished, saved, and then one job is claimed for the current run
- resume uses the existing manifest selection and does not reselect or re-research the job
- backlog completion is idempotent, so interruption after removal but before manifest checkpoint does not recreate the job
- the backlog path is persisted in run configuration and is configurable for tests/alternate deployments

This separates **future editorial planning** from **current production execution**. There is still only one production pipeline.

Testing:
- Added focused `tests/test_production_backlog.py` coverage for persistence, pending-job refresh, claimed-job protection, claim/completion ownership, stale-claim release, idempotent completion, and atomic replacement.
- Extended factory resume coverage to persist the backlog path and require the final `backlog_complete` checkpoint.
- A full repository pytest run remains unavailable because this environment cannot resolve GitHub from the shell.

### Step 8.3 — Autonomous scheduling cadence and daily operating state — **COMPLETE**

Added `factory_state.py` as the single operational cadence state for the existing factory.

The state:
- persists the last run time, last run status, run ID, next run time, and configured runs-per-day
- supports exactly **1 or 2 runs per day**, matching the locked operating model
- computes the next run as a 24-hour or 12-hour interval from the completed/failed run
- uses timezone-aware timestamps and stores state atomically
- is local under `data/factory_state.json`, alongside the existing local backlog/history; it is intentionally not Git-tracked
- records both successful and failed runs without blocking an operator from starting another run early

Factory behavior:
- `run_factory` loads the state before production so a malformed state file fails closed at initialization
- the selected cadence and state-file path are persisted in the job manifest and restored on resume
- successful completion records the next eligible run state
- failures record a failed run and next cadence window while preserving the original production exception
- CLI now exposes `--runs-per-day 1|2` and `--factory-state-path`
- no second runner, duplicate production path, or external scheduler was introduced; the same `factory.py` remains the only production entry point

Important scope boundary:
- this step makes the cadence explicit and durable for the user's once/twice-daily operating model
- it does **not** prevent an intentional early run and does not silently create a hosted scheduler before the factory is fully built and the external YouTube account exists

Testing:
- Added `tests/test_factory_state.py` for persistence, 1/day and 2/day cadence, invalid cadence, timezone-aware timestamps, and required run/status fields.
- Extended factory resume/failure coverage to verify cadence configuration persistence and failed/complete state recording.
- A full repository pytest run remains unavailable because this environment cannot resolve GitHub from the shell; focused tests and source paths were reviewed for this step.

### Step 8.4 — Final factory audit and launch readiness — **COMPLETE**

Audited the repository as one production system instead of adding another pipeline.

Audit findings and corrections:
- Confirmed there are no TODO, FIXME, placeholder, legacy-wrapper, compatibility-layer, or NotImplemented remnants.
- Confirmed the repository has one production entry point: `factory.py`.
- Confirmed there is no GitHub Actions workflow currently providing a hidden second runner; the factory remains intentionally operator-invoked once or twice per day until the external account is ready.
- Confirmed long-form and Shorts renderers both execute audio and video QA before the upload boundary.
- Confirmed question, explanation, and metadata generation use structured Gemini responses and existing deterministic validation/contract checks.
- Confirmed YouTube OAuth requests both required scopes: upload and Analytics read-only.
- Confirmed analytics excludes Shorts from long-form performance comparisons through the persisted `content_format` field.
- Confirmed resume manifests restore saved artifacts rather than regenerating completed stages and preserve selection/publish configuration.
- Confirmed the persistent backlog deduplicates, claims, releases stale claims, and only removes a job after the production run reaches `backlog_complete`.
- Fixed the final substantive integration gap: automatic topic-family adaptation was being computed but not applied to editorial job selection. `factory._select_job` now applies both subject and matching topic-family evidence.
- Added a regression test proving topic-family adaptation can change the selected job when the evidence-supported weight justifies it.
- Removed the unused `_slug` helper from `factory.py` and the unused `PIL.Image` import from `long_form_renderer.py`.
- Reviewed the dependency list; no new dependency was needed.

Testing state:
- The repository contains focused tests covering the production modules and the new factory/backlog/cadence paths.
- A full pytest run has **not** been executed in this environment because the repository cannot be mounted as a normal local checkout and there is no configured GitHub Actions workflow to run it remotely.
- Source and test contracts were reviewed directly against the current `main` tree. This is a code-level readiness review, not a claim that the complete suite is green.

Engineering completion:
**The factory build is complete.**

Operational launch is intentionally separate from engineering completion.

## 8.5 — CURRENT POST-BUILD STATE / LAUNCH GATE

The engineering project is now finished. The repository is at the external-platform launch boundary.

### Completed factory capabilities
The factory now has one direct production pipeline covering:
1. demand discovery
2. topic scoring and editorial adaptation
3. historical channel memory
4. validated question generation
5. verified explanations
6. deterministic lesson assembly
7. Hindi/Hinglish narration and word timing
8. audio QA
9. instructional long-form rendering
10. Shorts derivation and rendering
11. visual/video QA
12. metadata generation
13. YouTube OAuth/upload/scheduling
14. analytics ingestion
15. analytics-driven format/subject/topic-family adaptation
16. persistent editorial backlog
17. resume-safe production manifests
18. persistent once/twice-daily cadence state

### Current repository state
- Current branch target: `main`
- Final engineering audit committed to GitHub.
- Latest known completion commits include the final audit/context/README updates plus the topic-family adaptation fix and its regression test.
- `PROJECT_CONTEXT.md` remains the source of truth.
- `README.md` reflects engineering completion and the external launch gate.
- No dedicated YouTube channel has been created yet.
- No YouTube OAuth authorization has been performed yet.
- No real YouTube upload has been performed yet.
- No real channel analytics have been ingested yet.
- No `client_secrets.json` or `token.json` should be created/authorized until the launch setup chat explicitly reaches that point.
- Local runtime files such as `data/` and `output/` remain intentionally Git-ignored.

### Launch gate — what remains
The remaining work is not factory engineering. It is external Google/YouTube account setup and first live execution.

The next chat must walk the user through the complete setup from the beginning, starting with:
1. creating a new dedicated Gmail/Google account for the channel
2. setting up the dedicated YouTube channel
3. choosing/locking the channel identity and basic public settings
4. checking current YouTube Studio/channel settings relevant to a new education channel
5. setting up the required Google Cloud project and YouTube API access
6. creating the correct OAuth client/credentials
7. placing the credential/config files in the local factory environment
8. authorizing the factory with the exact scopes it needs
9. verifying the local auth/token path without prematurely publishing
10. performing the first real end-to-end factory test
11. checking the generated lesson, audio, rendered long-form video, derived Short, metadata, scheduling, and YouTube result
12. verifying analytics access
13. handling any platform/account/API failure before scaling
14. only after the first end-to-end run works, moving to the normal once/twice-daily operating model

Important launch-workflow rule:
- The new setup chat should use current official Google/YouTube documentation and current platform UI/API requirements because account, OAuth, verification, channel, and monetization procedures can change.
- It should not assume a past UI layout or old Google Cloud wording.
- The user should perform only the unavoidable browser/account actions. The assistant/factory should handle all reasoning, configuration guidance, verification, code-side checks, and launch decisions.
- Do not ask the user to repeat repository context. Read this file and continue from the launch gate.
- Do not modify the legacy `viral-shorts-factory` repository.
- Do not create a second production pipeline.
- Do not add manual editorial approval gates that contradict the locked autonomous operating model.
- Keep the user-facing setup instructions focused on the exact manual action required at that moment, then wait for the user's confirmation before proceeding to the next external gate.

## NEXT STEP

**Launch Gate — start the complete external Google/YouTube setup from a brand-new Gmail account.**

The engineering build should be treated as complete unless a real first-run test reveals an actual defect.

## Launch-gate correction — current YouTube Analytics OAuth requirement

During external launch setup, the current official YouTube Analytics API documentation was checked against the production authentication code. Google currently requires the `https://www.googleapis.com/auth/youtube.readonly` scope for `reports.query`, in addition to the existing Analytics read-only scope. The factory's `youtube_auth.py` was therefore updated on 2026-10-08 to request exactly these three scopes:

- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/yt-analytics.readonly`

This is a platform-compatibility correction, not a new production pipeline or redesign. The user must add the new `youtube.readonly` scope to Google Auth Platform → Data Access before reauthorizing the local factory. A prior token with only the older two scopes must not be treated as sufficient.

Current external launch status:
- Google account: created and secured
- YouTube channel: created
- Channel phone verification / Intermediate features: enabled
- Google Cloud project: created
- YouTube Data API v3: enabled
- YouTube Analytics API: enabled
- OAuth app: configured as External in Testing
- Desktop OAuth client: created
- YouTube API key: created for public demand discovery
- Gemini API key: created
- local factory: cloned and dependencies installed
- `client_secrets.json`: placed locally
- `.env`: configured locally
- OAuth reauthorization: pending after adding the new `youtube.readonly` scope
- first real factory run: pending
- first real upload: pending
- real analytics ingestion: pending

The full repository pytest suite remains unclaimed as green, consistent with the final engineering audit.

## Launch incident — transient Gemini API 503

The first real factory launch run reached `topic_scorer.py` and received HTTP 503 `UNAVAILABLE` from Gemini with the provider message that the model was experiencing high demand. This was a transient provider-side failure, not an account, API-key, OAuth, or YouTube configuration failure. Google’s current Gemini troubleshooting guidance recommends exponential backoff for transient 503/429 responses.

Launch fix completed on 2026-10-08:
- `topic_scorer._request_candidates` now retries transient HTTP 429/503 responses up to three times with 1s, 2s, and 4s delays.
- Non-transient HTTP errors still fail immediately.
- Added a focused regression test proving a pair of 503 responses can recover on the next successful request.
- No new dependency, wrapper, pipeline, or editorial gate was added.

Current next action:
- Pull the latest `main` into the local factory and rerun the same first real factory command.
- If another real launch defect appears at a later stage, diagnose and fix only that defect.

## Launch audit — full pre-rerun review completed

The first real launch attempt exposed a sequence of provider/runtime integration defects. Before asking the user to run the factory again, the production code was reviewed across the Gemini generation stages, YouTube authentication/Analytics, upload scheduling, rendering, and media QA.

Corrections now committed to main:
- All five Gemini structured-output stages now use the current `generationConfig.responseFormat.text` contract documented by Google for `generateContent`; deprecated `responseSchema` and the raw `responseJsonSchema` path are no longer sent.
- Gemini JSON Schema remains valid for the current API, including nullable fields where still required.
- Question generation now requires exactly four unique choices because the existing long-form/Short renderers require four-choice question cards. The canonical `Question` schema was not changed.
- All five Gemini generation stages now retry transient HTTP 429/503 provider failures before failing closed.
- The default Gemini model is `gemini-3.1-flash-lite`, a current GA high-volume model; the local `.env` is already set to the same model.
- Fixed malformed FFmpeg volume-detection regular expressions in `audio_qa.py` that would have caused the first rendered job to fail during audio QA.
- Added regression coverage for the Gemini response-format contract, four-choice generation contract, transient topic-scoring recovery, and FFmpeg volume parsing.
- Removed the accidental `docs/` OAuth website detour files from the repository; the factory has no website/pipeline dependency.

Current verification status:
- YouTube OAuth token contains all three required scopes.
- YouTube Data API access was verified against the real channel.
- YouTube Analytics API access was verified against the real channel.
- The first factory run did not reach rendering or upload; it failed first in topic scoring, then later reached question generation before the Gemini schema correction.
- No real video was uploaded by the failed runs.
- Full pytest has still not been executed and must not be represented as green.

Critical current platform boundary identified:
- Google documents that videos uploaded through `videos.insert` by an unverified API project created after July 28, 2020 are restricted to private viewing until the API project passes YouTube's compliance audit. Therefore the factory's intended public/scheduled publishing behavior must not be declared operational until the project's YouTube API compliance/audit status is resolved. citeturn665925search0turn665925search1turn665925search2

Next step before another full production run:
1. Pull current main into the local factory.
2. Run the focused regression tests for the corrected Gemini and audio- QA paths.
3. Run one real Gemini structured-output smoke test locally.
4. Complete/resolve the current YouTube API compliance-audit requirement needed for public publication.
5. Only after those checks, run the first complete production job again.

The user's locked operating model remains unchanged: USER RUNS THE FACTORY ONCE OR TWICE PER DAY → FACTORY DOES EVERYTHING ELSE AUTOMATICALLY.

## Pre-rerun audit continuation — 2026-10-08

The next launch attempt was stopped after pytest collection failed with `ModuleNotFoundError` for repository modules. This was a test-runner path issue, not missing production modules: invoking the standalone `pytest` executable on Windows did not place the repository root on `sys.path`.

Correction:
- Added root-level `pytest.ini` with `pythonpath = .`.
- No production dependency or runtime wrapper was added.

The full production code was then reviewed again before another real run. The review covered all Gemini generation stages, demand discovery, editorial selection/backlog/state, lesson assembly, both renderers, audio/video QA, YouTube OAuth/Analytics, and upload/scheduling boundaries.

Current Gemini contract:
- All five Gemini generation stages use `generationConfig.responseFormat.text.mimeType/schema`, matching Google's current REST structured-output documentation.
- No Gemini stage still sends deprecated `responseSchema`, `responseJsonSchema`, or duplicate `responseMimeType` fields.
- All five stages retry transient 429/503 responses.
- Model default is `gemini-3.1-flash-lite`, currently listed by Google as a stable high-throughput model.
- Question generation requires exactly four choices because the existing production visual primitives/renderers are four-choice layouts.

Current YouTube/Google launch status remains:
- OAuth token: valid and contains all three required scopes.
- YouTube Data API: verified.
- YouTube Analytics API: verified.
- Local `.env`: configured.
- Local `client_secrets.json`: present.
- No production video has been uploaded by any failed run.

Do not ask the user to rerun `factory.py` until the focused/full pytest pass and one real Gemini structured-output smoke test are clean.

Full pytest has still not been claimed as green because the repository is not available as a directly executable local checkout in this environment; the user's local checkout is the authoritative runtime copy.

## Pytest collection fix — 2026-10-08

After adding the root pytest.ini, the user's full-suite run progressed past the earlier repository-path import failure. The next collection error exposed one stale test import:
- tests/test_editorial_adaptation.py imported the old module name adaptation.
- Production code correctly uses editorial_adaptation.py.
- Updated the test to import from editorial_adaptation.
- Searched the repository for remaining from adaptation import and import adaptation references; none remain.

Current state:
- This was a test-suite naming mismatch, not a production runtime defect.
- The full pytest suite has still not been rerun after this correction.
- Do not run factory.py yet; rerun the full pytest suite first.

## Full pytest audit — 17 failures resolved — 2026-10-08

The user's full local pytest run reached 183 tests and reported 17 failures. All failures were traced individually.

Production corrections:
- format_analysis.py: published long-form entries with missing view metrics are treated as unmeasured and skipped; negative views remain a hard error. Result groups with zero measured videos are omitted.
- topic_family_analysis.py: only measured published long-form entries participate in topic-family grouping; scheduled, Shorts, empty-topic, and missing-view entries no longer create empty analysis groups. Negative views remain a hard error.
- metadata_generator.py: title length is checked before duplicate-title validation so an oversized title reliably fails with the intended limit error.
- pyq_source.py: exam input normalization is now case-insensitive and maps user input to canonical SSC, Railway, or Banking names.
- question_generator.py: the separate explanation stage remains authoritative; any explanation returned by the question-generation model is discarded and stored as an empty string. The existing exact-four-choice contract remains unchanged.
- validators.py: Maths answer validation runs before choice-membership validation, so a machine-checkable answer mismatch is detected deterministically even when the bad answer is absent from the choices.
- visual_primitives.py: missing Windows bold-font files now fall back to the regular font instead of failing render-time font loading. No new dependency was added.

Test corrections:
- tests/test_config.py: isolates the default-value test from the local .env and updates the expected Gemini default to gemini-3.1-flash-lite.
- tests/test_editorial_adaptation.py: uses pytest.approx for the floating-point constant comparison.
- tests/test_long_form_renderer.py: fake scenes now leave a safe visual margin so they exercise the renderer without violating the real edge-safety QA rule.
- tests/test_pyq_source.py: verified-source fixtures now use valid HTTPS official SSC URLs.
- tests/test_topic_scorer.py: the DemandSignal fixture now supplies its required rank field.
- tests/test_validators.py: numeric answer fixture matches the formatted choice representation.

The root pytest.ini remains in place with pythonpath = ., resolving the earlier Windows collection-path problem.

Current verification:
- These fixes are committed to main.
- The full suite has NOT yet been rerun after this batch.
- Do not run factory.py yet.
- Next manual action is one full python -m pytest -q run from the local checkout. If it is green, proceed to the real Gemini structured-output smoke test before the first production job.

## Final pytest cleanup — 2026-10-08

The next full-suite run reduced the remaining failures from 17 to 4.

Resolved in main:
- tests/test_editorial_adaptation.py now imports pytest for the approximate floating-point constant assertion.
- tests/test_question_generator.py now follows the actual nested Gemini schema path: questions -> items -> properties -> choices.
- visual_primitives.py now searches a small built-in list of Windows font locations for Devanagari and Latin fonts, including Nirmala UI, Mangal, Nirmala, Arial, and Segoe UI fallbacks. No font file or dependency is bundled.

The four previous failures therefore represented two stale test expectations plus one genuine Windows font-path portability defect. All changes are committed to main.

Current gate:
- Do not run factory.py.
- Run the full pytest suite once more after pulling main. A green result is required before the real Gemini smoke test.

## Windows font discovery final correction — 2026-10-08

The final two pytest failures were isolated to Devanagari font discovery on the production Windows machine. The previous fallback only checked a few hard-coded system filenames.

Correction committed to main:
- visual_primitives.py now searches both C:/Windows/Fonts and the Windows per-user font directory under %LOCALAPPDATA%/Microsoft/Windows/Fonts.
- It considers TTF, OTF, and TTC files and tolerates individual font-load failures while searching.
- No font file, dependency, or manual installation was added to the repository.

The latest suite result before this correction was 181 passed, 2 failed. Do not run factory.py yet. Pull main and rerun the full pytest suite; this is the final test gate before the real Gemini smoke test.

## Full pytest green — 2026-10-08

The user's local full suite completed successfully after the final Windows font-discovery correction:
- 183 passed in 19.57s.
- No pytest failures remain.
- The full engineering regression gate is now green.

Next gate:
- Run one real Gemini structured-output smoke test locally using the configured production API key/model.
- Do not run the full factory yet.
- After the Gemini smoke test is clean, resolve the documented YouTube API compliance-audit boundary before declaring public/scheduled publication operational.
## Gemini live smoke-test contract correction — 2026-10-08

The first real Gemini structured-output smoke test exposed an API contract detail that mocked pytest requests could not detect.

Google's current GenerateContent REST documentation defines responseFormat.text.mimeType as the enum `APPLICATION_JSON`, not the MIME string `application/json`. The live endpoint rejected the lowercase string with HTTP 400.

Correction committed to main:
- Updated all five Gemini production stages to send `generationConfig.responseFormat.text.mimeType = APPLICATION_JSON`.
- Updated payload regression tests in question, topic-scoring, and explanation generation to assert the live enum value.
- The structured JSON schema remains nested under responseFormat.text.schema.
- No dependency, wrapper, pipeline, or manual configuration change was added.

Current gate:
- The previous full suite was 183 passed before this live-contract correction.
- Pull main and rerun the full pytest suite once more.
- Do not run factory.py yet.
- After pytest is green, rerun the real Gemini one-question smoke test. A successful response is required before proceeding to the first complete production job.
## Gemini contract regression suite green — 2026-10-08

After correcting the live Gemini REST mime enum to APPLICATION_JSON, the user's local full pytest suite is green again:
- 183 passed in 21.60s.
- No pytest failures remain.

Current gate:
- The next required check is the real one-question Gemini structured-output smoke test against the configured production API key/model.
- Do not run factory.py yet.
- If the real smoke test succeeds, the next platform gate is YouTube API compliance/public-publication status before the first complete production run.
## Real Gemini smoke test passed — 2026-10-08

The user's real live Gemini structured-output smoke test succeeded after the APPLICATION_JSON correction.
- One Maths/SSC CGL/Percentages question was generated successfully.
- The response contained four choices and a valid correct answer.
- The machine-checkable Maths expression validation passed inside the generation stage.
- No factory production run has been started from this successful smoke test.

Current launch gate:
- Engineering regression suite: 183 passed.
- Real Gemini generation: verified.
- YouTube Data API and Analytics API: previously verified.
- Remaining platform gate: YouTube API compliance audit/public-upload restriction.

Next manual action: open the official YouTube Data API Services Audit and Quota Extension Form and begin the compliance-audit request. Do not submit anything until the factory supplies the exact answers/evidence for each field.
## YouTube audit compliance site — 2026-10-08

Google's current YouTube Data API audit form requires a publicly accessible organization website, privacy-policy URL, Terms documentation, homepage/privacy screenshots, and conditional evidence depending on the selected API use case. A minimal compliance-only static site has therefore been added under `/docs`.

Site files committed to main:
- docs/index.html — factory overview with links to privacy policy and terms.
- docs/privacy.html — YouTube API data handling, local storage, revocation, and Google Privacy Policy information.
- docs/terms.html — Terms of Service for the local factory.

Important boundary:
- This site is only for the external YouTube compliance audit and evidence. It is not a runtime dependency of the factory and does not change the production pipeline.

Next manual action:
- Enable GitHub Pages for AakarshBot/education_factory from main branch `/docs` so the compliance pages become publicly reachable.
- After the site is live, verify the homepage and privacy page in a browser before filling the corresponding audit-form URLs/evidence.
## Compliance detour corrected — 2026-10-08

The user correctly identified that viral-shorts-factory and Final-Shorts already use the normal YouTube `videos.insert` upload mechanism to publish public videos. The uploader implementation itself is not the reason public publishing is restricted.

Official YouTube documentation confirms the restriction is attached to the API project: uploads made via `videos.insert` from an unverified API project created after July 28, 2020 are restricted to private. The `videos.insert` endpoint itself accepts the normal youtube.upload scope.

Therefore:
- Do not add a compliance website, compliance code, or special publishing wrapper to education_factory.
- The compliance website detour has been fully removed from main.
- The next task is to identify the existing audited/eligible Google Cloud API project used by the working Final-Shorts/legacy upload setup and determine whether the new channel can use that existing project/client instead of creating a new unverified project.
- Do not submit the YouTube audit form or create any further compliance assets unless this existing-project route is unavailable.

Factory architecture remains unchanged.
## Existing YouTube upload project identified — 2026-10-08

The working Final-Shorts and legacy factory use the standard YouTube videos.insert path with public privacy status. Final-Shorts client_secrets.json identifies the existing Google Cloud project `amazing-sunset-504916-c4` and client ID `930842317060-mpfhnnc9jm748mvcg3m945dfqo6bubrs.apps.googleusercontent.com`.

Architecture decision:
- Do not build or submit a new YouTube compliance website/audit workflow.
- Reuse the existing working YouTube project/client for video upload authorization rather than creating a new upload project.
- Keep the new education_factory Google Cloud project for Gemini and the existing Analytics OAuth setup unless the existing upload project can safely cover Analytics without triggering unrelated verification changes.
- No production pipeline duplication or wrapper layer is required.

Completed external gate:
- In Google Auth Platform -> Audience for project `amazing-sunset-504916-c4`, the OAuth app is in Testing and `education.factory.india@gmail.com` was added as a test user.
- The proven Final-Shorts desktop OAuth client secret was copied locally into education_factory as `client_secrets.json`.
- education_factory `token.json` was removed locally so the new channel account will authorize against the existing project/client instead of reusing another channel's token.

Completed launch gate:
- In Google Auth Platform -> Audience for project `amazing-sunset-504916-c4`, the OAuth app is in Testing and `education.factory.india@gmail.com` was added as a test user.
- The proven Final-Shorts desktop OAuth client secret was copied locally into education_factory as `client_secrets.json`.
- education_factory `token.json` was removed before authorization.
- The factory's YouTube auth flow was authorized with the new channel account and the identity check is expected to show `Exam Session India`.
- `youtube_uploader.py` uses the standard `videos.insert` upload path and does not add a compliance/publishing wrapper.

Current launch gate:
- Engineering regression suite: 183 passed.
- Real Gemini structured-output smoke test: passed.
- YouTube Data API and Analytics API: previously verified.
- Existing working YouTube upload project/client: reused.

Next manual action:
- Pull the latest `main` into `C:\Users\aakar\Desktop\education_factory` and run the first complete production job with the default scheduled mode.
- Do not run with `--publish-mode public` yet; scheduled mode is the safer first production path.

## TTS launch defect — 2026-10-08

The first complete factory run reached narration and failed on `RuntimeError: TTS word timings are not monotonic` from `narration.py`.

Root cause:
- The repository allowed any `edge-tts` 7.x release.
- Upstream edge-tts 7.2.8 specifically fixed word-boundary offset compensation by replacing metadata-based compensation with CBR audio-byte timing. citeturn939354search0turn125075search2

Correction committed to main:
- `requirements.txt` now requires `edge-tts>=7.2.8,<8`.
- No wrapper, fallback timing algorithm, or new dependency was added.

The failed run produced no evidence of a YouTube upload; failure occurred before upload during narration.

Next manual action:
- From `C:\\Users\\aakar\\Desktop\\education_factory`, upgrade the installed edge-tts version with the command supplied in chat, then rerun `python factory.py`.

## TTS timing validator correction — 2026-10-08

The first production run failed in `narration.py` with `TTS word timings are not monotonic` even though the installed edge-tts requirement was already satisfied.

Root cause found in factory code:
- `_validate_timing()` incorrectly required each word's `start_seconds` to be at or after the previous word's `start + duration`.
- Edge TTS word-boundary data provides an offset and duration for each word; overlapping spans are not by themselves invalid. The relevant ordering invariant is that word start offsets are nondecreasing. citeturn613786search1

Correction committed to main:
- `narration.py` now validates nondecreasing word starts and positive durations.
- Added a regression test proving overlapping word spans are accepted when starts remain ordered.
- Reverted the unnecessary `edge-tts` minimum-version change; `requirements.txt` remains `edge-tts>=7,<8`.
- No wrapper, dependency, or fallback timing algorithm was added.

The failed production run stopped during narration before rendering or YouTube upload.

Next manual action:
- Pull latest main and rerun `python factory.py`. Do not install or change dependencies for this issue.


## YouTube demand-search quota defect — 2026-10-08

The next production run failed in `demand_discovery.py` because the YouTube API project exhausted its Search Queries daily quota (HTTP 429, project number 573156959102).

Current discovery behavior had 9 default exam/subject queries and performed two `search.list` requests per query (`relevance` and `viewCount`), so one fresh discovery consumed 18 search calls. YouTube's current documentation confirms `search.list` has a dedicated default quota of 100 calls/day. Correction committed to main:
- Added a direct 24-hour disk cache at `data/demand_cache.json` keyed by the discovery inputs.
- A fresh successful discovery still collects the full 9-query × 2-order signal pool.
- Repeated factory reruns within 24 hours reuse the cached result instead of consuming another 18 search calls.
- Cache read/write failures fail open and do not become a new production dependency.
- Added regression coverage for cache reuse.
- No topic queries, result pool, or editorial scoring behavior was removed.

Important immediate launch note:
- The previous successful run already created pending editorial backlog entries before its later narration failure.
- The current 429 occurred while trying to top up that backlog, not because no production job exists.
- Run the next manual command with `--max-jobs 1` so the factory uses the existing pending backlog and does not call `discover_demand()`.

Next manual action:
- Pull latest main and run `python factory.py --max-jobs 1`.

## Maths answer-source correction — 2026-10-08

The next production run reached question generation and failed correctly on a Gemini inconsistency: the model supplied `math_expression=100/3` but `correct_answer=3333/100`.

Root cause:
- Gemini was independently generating both `correct_answer` and `math_expression`, creating two competing answer sources.
- The deterministic validator correctly rejected the mismatch before any content could continue to rendering or upload.

Correction committed to main:
- `question_generator.py` now asks Gemini for `correct_choice_index` (0-3) instead of a separate `correct_answer`.
- The factory derives `Question.correct_answer` directly from the selected choice.
- For Maths, the derived choice is then validated against the machine-checkable `math_expression`.
- The Maths prompt explicitly requires exact choice matches and avoids rounding/repeating-decimal ambiguity.
- Existing canonical `Question` schema is unchanged.
- Updated regression tests cover the new choice-index contract.

The YouTube demand quota/cache fix remains in main; the current failed run did not reach YouTube upload.

Next manual action:
- Pull latest main and run `python factory.py --max-jobs 1` again.

## Post-green launch audit — 2026-10-08

After the user requested that code defects be fixed before any more testing, the complete diff since the last known-green 183-test state was audited.

Defects found and fixed:
- `question_generator.py` had a stale JSON-schema required field for `correct_answer` after changing Gemini output to `correct_choice_index`; the required field now matches the actual schema.
- `question_generator.py` raised `ValidationError` without importing it; the import is now explicit.
- `demand_discovery.py` cache write placement was incorrect and referenced cache variables from inside `_search()`; the cache write now occurs once after the complete discovery loop.

Verified post-green changed production areas:
- Gemini mime enum changes remain consistent across all five generation stages.
- TTS timing validator now checks ordered word starts and positive durations.
- Demand cache preserves the full 9-query × 2-order signal pool and only avoids repeated calls within 24 hours.
- Maths answer source is now choice-index-driven, with deterministic arithmetic verification.

No new dependency or wrapper was added by these corrections.

Current status:
- The repository's last user-reported full suite was 183 passed before this launch sequence.
- The subsequent launch-sequence defects above have now been statically corrected and audited against the post-green diff.
- No further user test run is required merely to inspect these fixes; the next useful step is the real production rerun.

Next manual action:
- Pull latest main and run `python factory.py --max-jobs 1`.


## First complete production run succeeded — 2026-10-08

The first complete production job completed successfully from the local factory:
- Job: `SSC Reasoning — Counting of Figures: Practice`
- The `factory.py --max-jobs 1` command returned `Completed`, which means the direct pipeline reached its completion path after production, scheduled upload stages, analytics ingestion, and backlog completion.
- This is the first successful end-to-end run after the launch-sequence Gemini, TTS, quota, schema, and OAuth defects were corrected.

Current launch status:
- Factory engineering path: operational on the user's local machine.
- Gemini live generation: operational.
- TTS/narration: operational.
- Rendering: operational.
- YouTube OAuth/upload path: operational through the existing working project/client.
- Scheduled publishing mode: completed successfully in the first production run.

Next manual action:
- Open YouTube Studio -> Content -> Scheduled and confirm the newly scheduled long-form video and Short are present. Do not change their visibility or edit metadata yet.


## Final-file visual/content audit — 2026-10-08

The first successful production files (`long_form.mp4` and `short.mp4`) were inspected directly.

Confirmed objective defects:
- Several generated Counting of Figures questions referred to a figure/diagram or a specific shape arrangement that was not rendered in the final video. This is a content-usability defect, not a styling preference.
- The long-form explanation scene rendered an orphan `Why it works` label with no content beneath it, leaving unnecessary dead space.

Corrections now present on main:
- `question_generator.py` requires every generated question to be self-contained in text and explicitly forbids missing-visual references in the generation prompt.
- `lesson_layouts.py` explanation scenes use the reclaimed lower area for the existing progress indicator instead of the orphan label.

## Maths generation contract hardening — 2026-10-08

A production run failed correctly during deterministic Maths validation because Gemini returned a `math_expression` using syntax outside the evaluator's supported arithmetic AST. The validator itself was not weakened.

Correction committed to main:
- `question_generator.py` now explicitly restricts generated Maths expressions to numbers, parentheses, +, -, *, /, and **.
- Common unambiguous mathematical symbols `×`, `÷`, and `^` are normalized to `*`, `/`, and `**` before deterministic validation.
- The evaluator remains fail-closed for functions, unsafe syntax, and unsupported operators.
- Added regression coverage for caret exponent notation.

This fixes the model/evaluator contract at the generation boundary while preserving deterministic answer verification.

Next manual action: pull latest main and rerun `python factory.py --max-jobs 1`.

## Dual-audio production stage — 2026-10-08

Dual-audio production is now wired for both published formats.

Current behavior:
- Hinglish remains the primary/default narration and is unchanged.
- After the existing Hinglish narration is checkpointed, the factory localizes the exact same narration segments into English through `english_narration_generator.py`.
- The English localization is checkpointed as `english_narration.json`, so resume does not repeat the translation call.
- The localization stage deterministically rejects changed numeric content, changed explicit answer text, and removed option structure before English audio is synthesized.
- After long-form rendering succeeds, the factory synthesizes one full English narration track using `ENGLISH_TTS_VOICE` (default `en-IN-PrabhatNeural`) and checkpoints the MP3 plus word timings as `english_narration.mp3` and `english_word_timings.json`.
- English long-form audio is QA-checked before metadata generation/upload continues.
- The Short derives its English narration from the same already-localized full-lesson segments and the exact same Short segment indices; it does not call Gemini again for translation.
- The English Short track is synthesized with the same `ENGLISH_TTS_VOICE` and checkpointed as `english_short_narration.mp3` plus `english_short_word_timings.json`.
- English Short audio is QA-checked and fails closed if it exceeds YouTube's 3-minute limit.
- No second video is uploaded and no English rendering pipeline was introduced.
- The factory also generates one English metadata package from the same lesson and supplies it as YouTube's `localizations.en` at upload time for both long-form and Short videos; the English Short uses the second title candidate without another Gemini metadata call.
- Localized title/description use the standard YouTube Data API upload resource; only the audio-track attachment remains a YouTube Studio-only operation.
- The upload explicitly marks Hindi (`hi`) as the default spoken-audio language, matching the primary Hinglish narration; `defaultLanguage` continues to describe the metadata language.

The remaining platform action is attaching the English MP3 as the additional audio track to each uploaded video in YouTube Studio. YouTube's official Multi-language Audio flow requires creator-side audio upload in Studio; the Data API does not expose that audio-track attachment operation.

## Dual-audio production run verification — 2026-10-08

A real local production run was completed successfully after the dual-audio implementation:
- Command: `python factory.py --max-jobs 1`
- Lesson: `Banking Reasoning — Syllogism: Practice`
- The factory returned `Completed`.
- This verifies the integrated production path reached its normal completion path with English localization, long-form English audio, Short English audio, metadata localization, scheduled uploads, analytics ingestion, and backlog completion.
- No code defect was observed in this run.
- The remaining manual platform gate is attaching each generated English MP3 as the additional audio track in YouTube Studio while the uploaded video remains private/scheduled.

Next implementation step: lock the exact YouTube Studio attachment workflow and then perform that one manual platform action.


## Long-form explanation layout verification — 2026-10-08

The final-render audit fix is present in the production layout:
- `_explanation_scene()` renders the verified answer at left.
- The explanation content occupies the right-side solution area.
- The lower strip uses the existing progress indicator.
- There is no `Why it works` label or unused replacement section in the current code.
- A regression test now asserts that an explanation scene invokes the progress indicator exactly once.

No visual redesign was introduced.


## YouTube Studio multi-language audio gate — verified 2026-10-08

The remaining dual-audio platform action has been verified against YouTube's current official desktop workflow:
- Open YouTube Studio on a computer.
- Go to **Content** and select the scheduled/private video.
- Open **Languages**.
- Click **Add language** → **English**.
- Next to **Dub**, click **Add**.
- Choose **Select file** and upload the factory-generated English audio-only MP3.
- Click **Publish** for the audio track.
- YouTube states that custom multi-language audio requires Advanced features, supports existing videos, and the audio file should be roughly the same length as the video.
- If an automatic English dub already exists for that video, delete it before uploading the factory's custom English dub.

Factory files:
- Long-form: `english_narration.mp3`
- Short: `english_short_narration.mp3`

This is a YouTube Studio-only platform operation. The factory already generates and QA-checks the English tracks and supplies English title/description localization during upload. The Data API is not used for the audio-track attachment.

Official source checked 2026-10-08: https://support.google.com/youtube/answer/13338784

## Channel launch decision — 2026-10-08

The factory is moving from engineering/testing into actual channel launch.

Decision:
- **Publish the previously rendered long-form video and derived Short today**, after the channel storefront is completed.
- Do not wait for Advanced features before publishing. Advanced features are useful for later operations, but they are not the prerequisite for establishing the channel with normal uploads. YouTube currently states that advanced access can be earned through channel history or eligible ID/video verification, and channel history includes channel activity such as uploads and audience engagement.
- Do not manufacture a fake warm-up routine. The channel's warm-up is legitimate setup plus real educational publishing and normal audience activity.
- The first published content should use the existing successful Banking Reasoning — Syllogism: Practice production pair rather than regenerate or redesign it.
- Keep primary Hinglish audio and current metadata. The English audio tracks can be attached later when the channel has Advanced features; lack of that feature is not a reason to delay the first publication.
- Use the first publication as a real launch/learning sample. Do not change the content merely to create artificial novelty.

Launch order:
1. Complete channel storefront: profile logo, banner, channel description, handle/name confirmation, and basic channel links/details.
2. Verify the channel's Feature eligibility status and confirm there is no active restriction beyond Advanced features.
3. Publish the existing long-form video.
4. Publish the derived Short later the same day rather than simultaneously, so the two formats have separate initial testing windows.
5. Attach the Short to the long-form manually through YouTube's available related-video control when the Studio UI exposes it.
6. Review first-day impressions, views, CTR/engagement, audience retention, and traffic source before deciding the next production mix.

The objective is not to "warm up" an algorithm with empty activity. The objective is to make the channel look and behave like a real educational product from its first day while collecting genuine audience signals.

Official feature source checked 2026-10-08:
https://support.google.com/youtube/answer/9891124

## Channel storefront launch layout — 2026-10-08

Home-tab decision for launch:
- Turn the **Home tab ON**.
- Do not create a channel trailer yet; there is no separate trailer asset and the first long-form upload is better treated as the actual launch content.
- Do not set a returning-subscriber Spotlight video yet; there are no returning subscribers and this can be assigned after the first meaningful library exists.
- Keep the initial Home layout minimal. Use **Uploads** as the primary content section and **Short videos** as the second section once the first uploads are public. Do not add "For you" or community-oriented sections at launch because the channel has no audience history yet.
- Revisit the Home layout after the channel has a real content library and first analytics sample.
- Use the same logo uploaded for the profile image as the channel video watermark when Studio offers the watermark control; keep it unobtrusive.

This is a storefront decision, not a factory pipeline change.

Official YouTube customization guidance checked 2026-10-08:
https://support.google.com/youtube/answer/3219384

## Channel-level discovery and audience settings — 2026-10-08

Launch settings decision:
- **Country/region:** India.
- **Channel keywords:** keep these tightly aligned to actual launch content:
  `SSC, SSC CGL, SSC CHSL, Banking Exams, Bank PO, IBPS, SBI PO, Railway Exams, RRB, Quantitative Aptitude, Maths for Competitive Exams, Reasoning for Competitive Exams, English for Competitive Exams, competitive exam preparation`
- Do not stuff unrelated trending terms or competitor/channel names.
- **Audience:** set the channel to **not made for kids** because the intended content is competitive-exam preparation for aspirants, not content primarily directed to children. Individual videos remain able to override the channel-level audience setting if a future lesson genuinely requires different treatment.
- **Channel links:** none at launch unless an owned, genuinely useful destination exists. Do not invent or add placeholder social links.
- **Business/contact email:** leave empty for now; add it only when the channel has a real public business-contact workflow.

YouTube currently exposes Country/region, Keywords, and Audience under Studio -> Settings -> Channel. Channel-level audience settings can apply to existing and future videos, while individual videos can override the channel setting.

Official sources checked 2026-10-08:
https://support.google.com/youtube/answer/2976814
https://support.google.com/youtube/answer/9527654

## First public launch execution — 2026-10-08

Launch execution decision:
- The existing Banking Reasoning — Syllogism: Practice long-form is the first public channel video.
- The derived Short is the second public launch asset and should be published later the same day, not simultaneously with the long-form.
- Historical launch spacing (superseded 2026-10-09): **12 hours between the long-form and derived Short**. This was the earlier operating choice, not a YouTube requirement; current target is 10:00 IST / 18:00 IST.
- The Short should be published normally as a public Short; no special warm-up activity is required.
- The Short's YouTube Studio Related Video link should be added to the long-form only after Advanced feature access becomes available. YouTube's current help states that adding a Related Video to a Short requires Advanced feature access and that the linked video must be public or unlisted.
- Do not create a duplicate upload, altered copy, or artificial linking workaround while Advanced features are unavailable.
- The first public launch is now considered real production, not testing. Analytics from the long-form and Short become the initial channel learning sample.

Immediate manual state:
- Long-form: public.
- Short: waiting for its planned later-today public release.
- English multi-language audio: waiting for Advanced feature access; do not delay publication because of it.

## Short publish timing alignment — 2026-10-08

Historical note, superseded 2026-10-09: `SHORT_PUBLISH_DELAY` was set to 12 hours at launch. The current target is 8 hours so the Short publishes at 18:00 IST after the 10:00 long-form.


Analytics source-of-truth correction — 2026-10-09
The read-only snapshot now enumerates the authenticated channel's own Uploads playlist before reading video statistics, rather than assuming every history ID is currently exposed by `videos.list(id=...)`. This keeps live channel discovery inside the existing YouTube Data API path, avoids `search.list`, and reports history IDs that are missing from the channel upload list. Official YouTube documentation identifies the Uploads playlist as the channel's uploaded-video source. citeturn723241search2turn723241search10


Renderer regression fix — 2026-10-09
The second production run reached long-form rendering but failed `visual_qa.check_image()` because `_canvas_base()` drew intentional grid/accent pixels directly on the image edges. The base canvas now keeps those decorative lines 10px inside the frame, preserving the visual design while satisfying the existing 8px unsafe-edge QA rule. A regression test covers the canvas base against `check_image()`. A local isolated Pillow harness verified the corrected edge bounding box; full repository pytest could not be executed from this environment because GitHub/network access is unavailable.

## Channel-state correction — 2026-10-09

Authoritative current channel state:
- The real channel **Exam Session India (@examsessionindia)** currently has exactly **1 public long-form and 1 public Short**.
- The user deleted the earlier first long-form because its design was poor; that deleted upload must not be treated as a live channel asset or part of the learning sample.
- The user confirms no additional videos have been published since the current public pair.
- IDs appearing in local factory history but not representing current published channel assets are stale production history and must not be treated as evidence that additional public videos exist.
- The public learning sample therefore remains exactly the current one long-form + one Short.
- Do not ask the user to inspect or explain nonexistent additional uploads again.

Production decision after the first live sample:
- Do not change topic, subject, format, or editorial strategy from one long-form + one Short; the sample is too small.
- The next production run should be **one job at a time**, primarily to maintain the planned learning cadence rather than because of performance evidence.
- No blind multi-job production and no analytics-driven overreaction.

## Live analytics decision — 2026-10-09

The first real public-channel analytics sample contains exactly:
- **1 public long-form:** Banking Reasoning — Syllogism Practice with 10 Questions — 3 views at roughly 19 hours, 0 likes/comments.
- **1 public Short:** Syllogism Practice Questions for Banking Exams — 28 views at roughly 5 hours, 0 likes/comments.
- YouTube Analytics watch/retention/subscriber metrics are not yet available for these 2026-10-08 uploads because the reported Analytics window currently ends on 2026-10-07. Blank Analytics fields must not be interpreted as zero performance.

The factory's next successful production job also created an SSC Counting of Figures long-form and derived Short in local channel history, but the user confirms these have **not been published**. They are not part of the public launch sample and should not drive editorial conclusions.

Production decision:
- **Do not run another factory job yet.** The next SSC pair already exists from the previous production run; creating another job would stack additional unobserved content.
- Do not change subject mix, lesson format, topic selection, or editorial adaptation from the first public pair. The existing 3-measured-video minimum for comparative adaptation has not been met.
- Keep one-job-at-a-time production as the default.
- Reassess after the existing next pair becomes public and enough analytics data accumulates to support a meaningful comparison.

No manual YouTube Studio inspection is required for this decision. The public sample and production state provided by the user are sufficient.

## Intermediate feature gate — 2026-10-08

The next channel-platform gate is **Intermediate features**, not Advanced features.

Reason:
- YouTube currently places **custom thumbnails** under Intermediate features.
- Phone verification unlocks Intermediate features and is also the first step toward Advanced features.
- The channel should use custom thumbnails for long-form packaging as soon as Intermediate access is available.
- Advanced access remains separately required for multi-language audio attachment and the Short Related Video control.

Manual action:
- In YouTube Studio -> Settings -> Channel -> Feature eligibility, inspect **Intermediate features**.
- If **Verify phone number** is available, complete that verification.
- Do not perform ID/video verification for Advanced yet unless YouTube specifically offers it and the user chooses to use it; channel-history access remains acceptable.
- Once Intermediate features are active, the next factory work is the direct long-form thumbnail system.

Official source checked 2026-10-08:
https://support.google.com/youtube/answer/9891124
https://support.google.com/youtube/answer/72431

## Fresh-render regression audit — 2026-10-09

The second production attempt failed at the long-form render call (factory.py -> render_long_form() -> visual_qa.check_image()); the traceback lines in factory.py are call-stack locations, not three separate failures. The actual failure was visual content touching the unsafe edge from visual_qa.py.

Root cause confirmed by comparing against the last successful production-render state (558d1a90dc3b13e333467f93a6dc0c0fde0cbdab):
- The successful production code used the earlier plain canvas and did not have _canvas_base().
- The later visual-system rewrite added _canvas_base() and changed both long-form and Shorts canvases to draw a grid and top accent.
- _canvas_base() initially drew those intentional decorative pixels at x=0/y=0, while the existing QA rule rejects any non-background pixel within 8px of an edge.
- The first public launch did not exercise this fresh renderer because it used a previously rendered known-good asset from before the visual-system rewrite.

The direct fix on main moves the decorative canvas lines 10px inside the frame. It keeps the existing 8px QA rule unchanged; no wrapper or compatibility layer was added.

Coverage hardening then added renderer-level regression tests:
- every assembled long-form lesson type (practice, timed_test, concept_practice, pyq_analysis, revision) now renders its production scenes at 1920x1080 and passes visual_qa.check_image();
- the production Shorts scene path is also exercised through visual_qa.check_image() before the real MP4 test;
- the isolated _canvas_base() regression test remains in place.

The code-level audit found no second unsafe-edge defect in the current lesson/Short layouts. The remaining validation limitation is environmental: full repository pytest cannot be executed from this environment, so the renderer review relies on direct code inspection, the existing isolated Pillow QA harness, and the expanded regression tests committed to main.

Audit decision: do not weaken visual QA, add another renderer, or change educational/editorial logic. The current renderer should be retried exactly as implemented.


## English localization regression audit — 2026-10-09

The next fresh production attempt reached English localization and failed with "English narration changed numeric content in segment 1". The renderer had already passed the previously failing visual edge gate.

Root cause:
- The existing English-localization validator required digit sequences to remain textually identical.
- Gemini can legitimately turn spoken numeric content such as 25 into "twenty-five" during English localization even when the underlying value is unchanged.
- This was a validator false-positive, not a content-generation answer error.

Direct fix committed to main:
- Numeric tokens, generated answer values, and the "Options:" structure are replaced with protected placeholders before the localization request.
- The localization prompt requires protected placeholders to remain exact, including order.
- Returned text is rejected when protected tokens are missing, duplicated, added, or reordered.
- Original protected values are restored deterministically before the existing numeric/answer/option fidelity checks run.
- No fallback translation, retry loop, wrapper, or parallel localization pipeline was added.

Regression coverage:
- valid numeric localization/restoration is covered;
- changed numeric content is rejected;
- changed answer content is rejected;
- missing protected tokens are rejected;
- existing structured-response and segment-count tests remain covered.
Offline simulation confirmed the placeholder ordering and restoration behavior.

Commits:
- 631fc035a486fb75c61343daad09b5286e3e04de8 — protect invariant content during English localization
- 4e60352662777d7b3979d1a7930f6d21a627de8b — test protected English localization invariants

The fresh-render audit also remains current: the only other production regression found after the last known-good production render was the canvas edge issue already fixed on main. Current production rendering and English localization now have direct regression coverage.

Validation limitation:
- Full repository pytest still cannot be executed from this environment.
- The localization helper logic was executed in an offline simulation covering token ordering and exact restoration.
- Do not spend another production run until the local checkout is synced to main with these two commits.


## Full factory preflight coverage — 2026-10-09

After the English-localization regression fix, the production path was audited beyond the previously failing stage. The remaining downstream path is structurally sound: English audio is generated and checked with the existing audio QA gate; long-form and Shorts both render through their real renderers; metadata is validated before upload; YouTube upload remains fail-closed; final analytics ingestion and backlog/state completion happen only after both uploads succeed.

A new offline factory preflight regression test now exercises the actual long-form and Short renderers inside the factory orchestration, while mocking only external/network services such as demand discovery, Gemini, TTS, YouTube upload, and analytics ingestion. It uses real media files and therefore exercises the real image QA, FFmpeg render, video QA, stage ordering, manifest completion, and dual-upload path.

The test suite also now covers the hardened English placeholder invariants and the renderer edge-QA fixes.

Validation limitation remains explicit: the full repository pytest suite cannot be executed from this environment. The current main state has been verified by direct code inspection, focused offline simulations, and the expanded regression tests committed to the repository.

Latest implementation commits:
- a5f90f9c779e2762520091a4d98d6293dacb374b — corrected protected localization regression test
- 3222ac715c651d44da73e4b23470ce9e8148e681 — real media pipeline factory preflight test
- b1466e5197fbbde9c9a382f7b51a07679e104427 — hardened localization audit/context


## Preflight test corrections — 2026-10-09

The first local focused preflight run found five failures. None indicated a new production-stage API, narration, upload, or rendering defect at the factory's production size:
- the publish-time resume test still expected the old 2-hour Short delay; it now expects the locked 12-hour delay;
- the structured English-localization test returned an unprotected response even though the production contract now requires protected invariant tokens;
- the reordered-token regression test incorrectly unpacked the per-segment replacement structure;
- the canvas-background test expected the grid color at a coordinate that is now intentionally background after the 10px edge inset; it now checks both background and an actual grid pixel;
- the assembled-scene smoke test used 1280x720 even though the production renderer is built and QA-checked at 1920x1080; the regression test now exercises all segment kinds at the actual production size.

These are test-alignment fixes only; no production behavior was weakened or changed to make the tests pass.

Latest test-fix commits:
- 84bb0b2e02eb45a3c68851083fa5d21c9c45c019
- 4f53241f6f10e154bc82dac2e030c661ba950992
- 5cbe197a48aa9b998864c4a12701c7e069ae0f95

Next manual step: pull main and rerun the focused preflight pytest command. Do not run the factory until that suite passes.

## Preflight assertion correction — 2026-10-09

The focused preflight rerun exposed one remaining test-only mismatch in `tests/test_lesson_layouts.py`: `test_all_assembled_segment_kinds_render` correctly called the renderer at the production size of 1920x1080 but still asserted the obsolete 1280x720 size. The assertion has been corrected to 1920x1080.

Commit:
- ca1fe6f418ba1df1ed56cd7029fa4671c7a3abe9 — fixed assembled scene size assertion

No production pipeline logic was changed.

Next manual step: pull main and rerun the focused preflight pytest command. Do not run the factory until the suite passes.

## Focused preflight passed — 2026-10-09

The required focused preflight suite was run locally after syncing main:

```
python -m pytest tests/test_factory.py tests/test_english_narration_generator.py tests/test_lesson_layouts.py tests/test_shorts_renderer.py tests/test_visual_primitives.py tests/test_visual_qa.py -q
```

Result: **39 passed in 21.26s**.

This clears the pre-factory engineering gate. No production logic was changed by the final test correction. The next step is the first real factory run using the already-operational YouTube OAuth/Data/Analytics path; editorial strategy remains unchanged because the live sample is still only one long-form plus one Short.

## Second production-run question-generation failure — 2026-10-09

The first real second production attempt was stopped before media rendering or YouTube upload. The factory failed in `question_generator.generate_questions()` during deterministic Maths validation because Gemini returned a correct choice that was not parseable as a numeric answer (`validators.ValidationError: answer is not numeric`). The fail-closed validator behavior is correct; the resilience gap was that one malformed structured generation response aborted the entire daily job.

Direct hardening committed to main:
- Maths generation instructions now require all four Maths choices to contain numeric values only, allowing the existing currency/percent/fraction notation, and explicitly forbid units, labels, or words in choices.
- Question generation now makes at most one automatic regeneration after a deterministic `ValidationError`, passing the validation reason back into the retry prompt. The validator remains fail-closed; there is no fallback acceptance or answer rewriting.
- Regression coverage verifies an invalid Maths choice causes one regeneration and that the corrected response is accepted.

Commits:
- 582de5cea56b80db04f81f0b474efbd75cdb3291 — retry deterministically invalid question generation
- c4f3f6bdba093fe4094ba506ec1e950cf424e2aa — test question generation retry on validation failure
- 8191671b7204bddc006573951d47a8eaea7fa1f2 — clean question generation prompt escaping

No video was uploaded by the failed run.

Next manual step: pull main and rerun the focused preflight pytest command. Do not run the factory until the suite passes.

## Post-hardening preflight passed — 2026-10-09

The focused preflight suite was rerun after the question-generation hardening:

```
python -m pytest tests/test_factory.py tests/test_english_narration_generator.py tests/test_lesson_layouts.py tests/test_shorts_renderer.py tests/test_visual_primitives.py tests/test_visual_qa.py -q
```

Result: **39 passed in 23.35s**.

The question-generation resilience fix is therefore covered by the local focused suite. Deterministic Maths validation remains fail-closed, with at most one automatic regeneration for a malformed generated response.

Next manual step: rerun the factory for the second real production upload. If the generation retry succeeds, the factory should continue through the existing production path; if another stage fails, stop before upload and diagnose that stage rather than bypassing its QA gate.

## Second successful production run — 2026-10-09

The second real factory run completed successfully:

```
Completed: Railway Reasoning — Direction and Distance: Practice
```

The production orchestration prints `Completed` only after the long-form upload stage, Short upload stage, analytics ingestion, backlog completion, and final run-state completion succeed. Therefore this run cleared the full production path without a QA bypass or manual intervention.

The factory's default publish mode remains `scheduled`. On 2026-10-09 the actual second pair was observed public at 10:00 IST (long-form) and 18:00 IST (Short). The scheduler had not yet caught up with this intended schedule; the correction below updates defaults for future jobs only. Existing scheduled/public videos and resume manifests are not rewritten.

Editorial state remains unchanged: do not immediately stack another job while the second Short has only minutes of exposure. The early sample shows 58 views on the first Short after 22.4 hours, 4 views on the first long-form after 36.3 hours, and 2 views on the second Short after 0.4 hours; the second long-form has 0 views after 8.4 hours. Likes and comments are 0. The Analytics report was requested only through 2026-10-08, so engaged views, watch time, average view metrics, and subscribers gained are not yet available for the 2026-10-09 pair. This sample does not yet justify deleting videos, changing metadata, or altering topic strategy.


## Day 3 publishing schedule correction — 2026-10-09

The actual channel schedule is **10:00 IST long-form / 18:00 IST Short**. The prior factory defaults (18:00 / 12 hours later) were inconsistent with the actual schedule and are superseded.

Implementation: `factory.py` now selects the next 10:00 Asia/Kolkata long-form slot and schedules the derived Short 8 hours later at 18:00. Resume stability is preserved: previously recorded publication times remain unchanged. `tests/test_factory.py` now checks the 10:00 slot, rollover to the next day after the slot, and same-day 18:00 Short timing.

Validation status: code and regression tests have been updated, but the repository's focused pytest suite has not yet been run in this session. Do not run another production job until the focused preflight passes after pulling `main`.

Day 3 decision: do not produce another pair yet. Keep the channel strategy and existing videos unchanged, allow the second Short to receive meaningful exposure, then collect a fresh snapshot after the Analytics date range includes 2026-10-09 and metrics have populated.