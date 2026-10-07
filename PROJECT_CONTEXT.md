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

### Step 2.1 — Demand discovery
Build free/low-cost topic discovery around exam-related search intent and current learning needs.

### Step 2.2 — Topic scoring
Score:
- demand
- exam relevance
- novelty relative to our channel
- educational value
- visual potential
- production reliability

### Step 2.3 — Editorial queue
Automatically choose the next jobs.

### Step 2.4 — Historical memory
Store enough local channel history to avoid repetitive publishing and support learning from prior results.

---

## Phase 3 — Voice and audio

### Step 3.1 — Hindi/Hinglish narration pipeline
Generate speech using free/local tooling.

### Step 3.2 — Timing contract
Produce stable word/phrase timing data for rendering.

### Step 3.3 — Audio QA
Verify duration, silence, missing audio, and basic output integrity.

---

## Phase 4 — Visual engine

### Step 4.1 — Visual primitives
Create a small set of deterministic educational primitives:
- question card
- choices
- timer
- answer reveal
- calculation step
- highlighted text
- diagram/flow
- progress indicator
- score/result screen

### Step 4.2 — Lesson-specific layouts
Create several compositions that reuse primitives but are not identical templates.

### Step 4.3 — Long-form renderer
Render 16:9 educational sessions.

### Step 4.4 — Shorts renderer
Render 9:16 challenge/lesson cuts.

### Step 4.5 — Visual QA
Automated checks for cutoffs, overlaps, unreadable text, duration and missing assets.

---

## Phase 5 — Publishing

### Step 5.1 — Metadata generation
Generate title candidates, description, hashtags/keywords where useful, and series/context fields.

### Step 5.2 — YouTube OAuth
Connect the dedicated Google account/channel.

### Step 5.3 — Upload and scheduling
Upload to YouTube and schedule publication.

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

At the moment, because the repository is empty, the only external setup expected from the user is:

### Required later
1. Create the dedicated Google account/channel.
2. Complete any YouTube/Google identity, phone, advanced-feature, or verification steps Google requires.
3. Grant the factory the YouTube OAuth authorization once the uploader exists.
4. Optionally provide any channel branding assets once the design is selected.

The factory itself should perform everything else that is technically possible.

**Do not ask the user to perform any of these until the corresponding implementation step actually needs it.**

---

# 10. CURRENT BUILD STATE

Status: **FOUNDATION / STEP 0.2 COMPLETE**

Repository:
AakarshBot/education_factory

The repository was empty at the start of this project.

Completed:
- locked channel strategy recorded
- minimal repository skeleton created
- `.gitignore` added for Python caches, local environments, runtime output, and credentials
- `.env.example` added with YouTube credential placeholders only
- `README.md` added with the locked strategy and development rule
- India/Hindi-Hinglish market locked
- SSC + Banking + Railway focus locked
- Maths + Reasoning + English initial subjects locked
- long-form + Shorts strategy locked
- zero-cost constraint locked
- autonomous operating model locked
- build map recorded
- manual external actions documented

Not yet implemented:
- production application code
- dependency file
- question schema
- validators
- research/discovery
- renderer
- uploader
- analytics
- autonomous run command

## STEP 0.3 — LOCAL/FREE DEPENDENCY POLICY — **COMPLETE**

The factory uses a deliberately small Python stack. Production code should use the standard library wherever practical and add a package only for a concrete capability.

Locked direct dependencies:
- `Pillow` — deterministic educational graphics and image operations.
- `edge-tts` — free Microsoft Edge online TTS access without an API key; it also exposes speech timing/subtitle support. citeturn785269search1
- `requests` — direct HTTP access so we do not add an SDK merely to call a simple API.
- `python-dotenv` — local `.env` loading without embedding secrets in code.
- `google-api-python-client` — YouTube Data API upload, scheduling, metadata and channel operations.
- `google-auth` and `google-auth-oauthlib` — YouTube OAuth authorization.
- `pytest` — focused automated tests.

LLM policy:
- Use the Gemini API through direct HTTP rather than adding the Gemini Python SDK unless a later concrete capability requires the SDK.
- Default model for the initial text-generation implementation: `gemini-3.8-flash`, subject to the then-active free-tier availability. Google's current pricing page lists a free tier for this model, while current model documentation identifies it as stable. citeturn307393search0turn307393search1
- The factory must track and fail clearly on rate limits rather than silently switching to paid usage. Gemini limits are project/account dependent and can vary; the active limits are shown in AI Studio. citeturn202704search2
- Google Search grounding is not assumed for free production because current pricing states it is unavailable for Gemini 3.x free-tier requests. citeturn307393search0

Media policy:
- FFmpeg/ffprobe are required local executables for final audio/video assembly and duration checks. FFmpeg is free/open source; use only standard components so the default LGPL licensing remains applicable. citeturn785269search11
- Do not add MoviePy, OpenCV, Torch, Transformers, browser automation, image-generation libraries, or other heavyweight media/ML stacks unless an implemented stage proves the dependency necessary.

YouTube API policy:
- The production target is far below YouTube's default quota allocation. Current official documentation lists a default 10,000-unit/day allocation, plus specific limits around `search.list` and `videos.insert`. The uploader must still minimize calls and handle quota errors explicitly. citeturn785269search2

Security policy:
- Real credentials stay in `.env` or local OAuth files and are ignored by Git.
- Never print, commit, or persist API secrets in repository source.

The dependency file is now `requirements.txt`. No heavyweight Final-Shorts dependency set was carried over.

## CURRENT BUILD STATE — UPDATED

Status: **PHASE 1 / STEP 1.5 COMPLETE**

Completed in Phase 0:
- Step 0.1 — master project context
- Step 0.2 — minimal repository skeleton
- Step 0.3 — minimum local/free dependency policy and build stack
- Step 0.4 — configuration and secret handling

Completed in Phase 1:
- Step 1.1 — canonical question schema
- Step 1.2 — deterministic Maths/question validators
- Step 1.3 — structured original question generation
- Step 1.4 — answer-locked explanation generation
- Step 1.5 — deterministic lesson assembly

Current repository files:
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
- `tests/test_config.py`
- `tests/test_question.py`
- `tests/test_validators.py`
- `tests/test_question_generator.py`
- `tests/test_explanation_generator.py`
- `tests/test_lesson_assembler.py`

Test status:
- Step 1.5 dedicated tests: **9 passed locally**.
- The new lesson contract and assembler also passed Python syntax compilation.
- The full repository suite was not executed in this hosted session because the environment could not clone the GitHub repository; no broader full-suite pass is claimed.

Architecture note:
- Question generation creates and deterministically verifies the question/answer package.
- Explanation generation separately creates explanations from the verified answers.
- Lesson assembly then sequences those verified question/explanation packages into a selected learning experience.
- Rendering, audio, publishing, and topic discovery remain outside the lesson assembler.

## NEXT STEP

**Step 2.1 — Demand discovery.**

Build free/low-cost topic discovery around exam-related search intent and current learning needs.
