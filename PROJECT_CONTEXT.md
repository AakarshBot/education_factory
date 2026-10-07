**THIS IS CHATGPT'S CHANNEL AND FACTORY**

# Education Factory — Master Context

## 0. Governing ownership and workflow

This repository is the factory for ChatGPT's new YouTube channel. The user owns the external Google/YouTube account and can operate the channel normally, but editorial, production, publishing, testing, analytics, and iteration decisions belong to the factory unless the user explicitly overrides them.

The user's desired operating model is:

**USER RUNS THE FACTORY ONCE OR TWICE PER DAY → FACTORY DOES EVERYTHING ELSE AUTOMATICALLY.**

The user should not need to perform backend work for normal production. Manual actions must be limited to unavoidable external account setup, authorization, verification, or platform actions that cannot be performed through the factory.

### Interaction rule for future chats

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
- clean digital examination interface
- large readable question
- visible progress such as Q1/20 when appropriate
- short timed-answer phase when useful
- answer reveal
- worked solution
- highlighted numbers, words, or reasoning steps
- diagrams/flows for reasoning
- score/progress moments
- occasional "common mistake" and "shortcut" treatment
- varied layouts driven by lesson type

Avoid:
- stock-photo filler
- generic AI-generated images for decoration
- fake classroom backgrounds
- talking-head avatars
- excessive TikTok-style motion
- identical frame choreography in every upload
- permanent decorative UI that adds no instructional value

The design system may be consistent, but the instructional composition must vary with the content.

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

### Step 0.1 — Project context
Create and maintain this file as the single source of truth.

### Step 0.2 — Minimal repository skeleton — **COMPLETE**
Created only repository-level hygiene/documentation needed before production code: `.gitignore`, `.env.example`, and `README.md`. No placeholder application code or speculative dependencies were added.

### Step 0.3 — Local/free dependency policy
Define the minimum dependency set. Avoid the heavyweight ML stack used by Final-Shorts unless a later feature demonstrably requires it.

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

### Step 5.4 — Shorts → long-form linking
Add the relevant YouTube relationship where supported.

---

## Phase 6 — Analytics and self-improvement

### Step 6.1 — Metrics ingestion
Collect channel/video performance that is available through permitted APIs.

### Step 6.2 — Format analysis
Compare practice, test, lesson, PYQ, and revision formats.

### Step 6.3 — Subject analysis
Compare Maths, Reasoning, and English.

### Step 6.4 — Topic-family analysis
Identify winning clusters.

### Step 6.5 — Automatic editorial adaptation
Modify future production weights based on evidence.

The system must not change strategy based on a single anomalous video.

---

## Phase 7 — Autonomous daily operation

### Step 7.1 — One-click / one-command factory run
One user action starts the complete cycle.

### Step 7.2 — Daily queue generation
Create today's jobs and future backlog.

### Step 7.3 — Retry and recovery
Recover transient failures without duplicating uploads.

### Step 7.4 — Production ledger
Keep a lightweight state record so a new run knows exactly what has already been produced, uploaded, scheduled, or failed.

---

# 8. QUALITY AND POLICY GATES

These are factory safeguards, not human approval gates.

Every long-form/Short must satisfy:
- original or appropriately sourced educational content
- verified answers
- coherent explanation
- readable visual output
- correct narration timing
- no obvious duplication with recent uploads
- no fabricated source claims
- no fake engagement
- no deceptive metadata
- no copyright-dependent visuals unless properly sourced/licensed
- no financial/advice content unless the strategy is explicitly changed and reviewed

The factory should prefer original questions and original graphics.

---

# 9. MANUAL ACTIONS CURRENTLY REQUIRED

**No manual action now. The YouTube channel has not been created yet, and channel/OAuth setup is intentionally deferred until the factory implementation is complete.**

The remaining external setup will be handled together at the end, when the factory is ready for its first real production run. At that point the user will need to:
1. create the dedicated Google account and YouTube channel;
2. complete any Google/YouTube identity, phone, advanced-feature, or verification steps required for that account/channel;
3. create the Google Cloud OAuth client and authorize the factory against the dedicated channel account;
4. provide any final channel branding assets that the completed design actually requires.

Until that launch handoff, do not ask the user to create the channel, create OAuth credentials, run `youtube_auth.py`, or perform routine backend setup.

The factory should perform everything else that is technically possible.

---

# 10. CURRENT BUILD STATE

Status: **PHASE 5 / STEP 5.3 COMPLETE**

Repository:
AakarshBot/education_factory

Channel status:
- The dedicated YouTube channel/account has **not** been created yet.
- This is intentional. Real OAuth authorization and real upload testing are deferred until the factory itself is complete.

Completed:
- Phase 0 — foundation and configuration
- Phase 1 — question schema, deterministic validation, generation, explanations, lesson assembly
- Phase 2 — demand discovery, topic scoring, editorial queue, historical memory
- Phase 3.1 — Hindi/Hinglish narration
- Phase 3.2 — word timing contract
- Phase 3.3 — audio QA
- Phase 4.1 — deterministic visual primitives
- Phase 4.2 — lesson-specific visual layouts
- Phase 4.3 — long-form 16:9 renderer
- Phase 4.4 — Shorts 9:16 renderer
- Phase 4.5 — visual QA
- Phase 5.1 — metadata generation
- Phase 5.2 — YouTube OAuth
- Phase 5.3 — YouTube upload and scheduling

Current production chain:
**demand -> scored topic -> editorial queue -> verified questions -> verified explanations -> lesson sequence -> narration + word timings -> audio QA -> visual QA -> 16:9 long-form or 9:16 Short -> grounded metadata -> authenticated YouTube client**

Current repository files include:
- `PROJECT_CONTEXT.md`
- `README.md`
- `.gitignore`
- `.env.example`
- `requirements.txt`
- `config.py`
- `question.py`
- `validators.py`
- `question_generator.py`
- `explanation_generator.py`
- `lesson.py`
- `lesson_assembler.py`
- `demand_discovery.py`
- `topic_scorer.py`
- `editorial_queue.py`
- `channel_history.py`
- `narration.py`
- `audio_qa.py`
- `visual_primitives.py`
- `lesson_layouts.py`
- `long_form_renderer.py`
- `shorts_renderer.py`
- `visual_qa.py`
- `metadata_generator.py`
- `youtube_auth.py`
- `youtube_uploader.py`
- focused tests under `tests/`

Step 5.1 test status:
- Added focused metadata tests for title selection and important malformed/oversized metadata cases.
- The metadata contract is grounded in the finished Lesson and fails closed on unsafe output.

Step 5.2 test status:
- Added focused tests for existing valid tokens, token refresh, first-time browser authorization, missing client secrets, and refresh failure.
- Remote OAuth code was reviewed against the current Desktop/installed-app flow.
- Real Google authorization was deliberately not run because the dedicated channel/account does not exist yet.
- No credential or token has been committed.

Step 5.3 test status:
- Added focused mocked-upload tests for public publishing, scheduled publishing, validation failures including the final description byte limit, API failures, missing IDs, and history persistence.
- Real YouTube upload was deliberately not run because the dedicated channel/account and OAuth token do not exist yet.

Architecture:
- `metadata_generator.py` owns metadata generation and local validation.
- `youtube_auth.py` owns only OAuth credential loading/refresh/initial authorization and YouTube client construction.
- `youtube_uploader.py` owns only direct video upload/scheduling and the required channel-history write; no alternate uploader or authentication wrapper should be introduced.

## MANUAL ACTION REQUIRED NOW

**None. The dedicated channel has not been created yet, so the external Google/YouTube setup is intentionally postponed until the factory is fully built.**

Do not create `client_secrets.json`, authorize YouTube, or run `python youtube_auth.py` yet. The repository is ready for that later launch step, and both credential files remain ignored by Git.

## NEXT STEP

**Phase 5 / Step 5.4 — Shorts → long-form linking.**

Add the relevant YouTube relationship between a Short and its related long-form lesson where the platform/API supports it, without introducing a second publishing pipeline.
