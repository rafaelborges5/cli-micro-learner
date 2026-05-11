# Changelog

## [0.1.0] — 2026-05-11

### Phase 8 — Guided Lesson Briefs

- `start` now prompts for an optional long-form learning brief that steers what each lesson covers
- Syllabus generation produces structured steps with an AI-generated short title and a per-step brief; both are stored in the syllabus record
- Lesson and quiz cache generation uses the per-step brief as the primary instructional context instead of just the step title
- Status output and note export surface the generated brief; resume views stay compact using the short title
- The first third of every syllabus is forced to explanation lessons before quizzes are allowed, ensuring context is established before recall is tested

### Phase 7 — Progress Bar & Quiz Polish

- Extracted `_compute_toolbar_segments` as a shared layout helper; both the ANSI and `FormattedText` toolbar rendering paths now share a single source of truth for width-aware truncation and slot allocation
- Progress bar width scales dynamically with terminal width (8–20 chars); topic name and suffix are dropped gracefully at narrow widths
- Quiz answer copy tightened so revealed answers read as concise review guidance rather than appended explanation blocks
- Themed `render_answer` panel provides visual separation between question and answer with a `✓ Answer` title
- Regression tests added for answer reveal in CLI output, note export, and missing-answer fallback
- Added `__main__.py` so `python -m micro_learner` works without `PYTHONPATH=src`

### Phase 6 — REPL UX Polish

- Introduced a centralized `REPLSessionState` view-model so header state, cache state, prompt state, toast queue, and theme name are all managed in one place instead of scattered across shell methods
- `/start` and `/resume` tab-completion now suggests topics from learning history (deduped, recency-ordered)
- Toast notification system surfaces background cache warmup completion and note export outcomes inline without interrupting the REPL flow
- Bare `/resume` opens a `prompt-toolkit` live-search picker instead of a numbered list
- `/theme` command switches between Modern, Classic, and Matrix themes; selection is persisted to `~/.micro_learner/settings.json` and applied across Rich output, the toolbar, the prompt, and the resume dialog

### Phase 5 — Integrated REPL Shell

- Replaced per-command Click dispatch with a persistent `prompt-toolkit` REPL session; users launch `micro-learner` once and stay in the session
- Slash commands implemented: `/start`, `/next`, `/status`, `/resume`, `/help`, `/quit`
- Bottom toolbar always shows active topic and lesson progress; no need to run `/status` to orient
- Progressive cache warmup: first lesson is generated and displayed immediately, then remaining lessons are cached in an `asyncio` background task
- Core logic decoupled into `logic.py`, shared by both the Click CLI and the REPL
- Original Click commands kept as a thin wrapper for scripting and pipe-friendly use

### Phase 4 — Advanced Interactions

- Keyboard listener implemented so **E** and **D** can be pressed after any lesson or quiz
- **E** triggers a live LLM call to rewrite the current concept as a simpler analogy
- **D** triggers a live LLM call to provide a concrete code snippet for the current concept
- Intervention content rendered in dedicated Rich panels and appended to the lesson's note export entry

### Phase 3 — Knowledge Retention & Multi-Topic Management

- Each syllabus stored as its own JSON record under `~/.micro_learner/syllabi/`; global state is reduced to an active-syllabus pointer
- Completed lessons auto-exported to `~/.micro_learner/notes/<topic>.md` with YAML frontmatter (Obsidian/Notion compatible)
- Note files use per-session headers and per-lesson sections with timestamps and step metadata
- `start` generates and caches all 15 lesson artifacts up front; `next` reads from cache with no live LLM call
- `resume` lists stored syllabi with progress percentages and lets the user switch the active topic

### Phase 2 — UI & Formatting

- Lesson content rendered inside Rich `Panel` components with stylized headers and syntax-highlighted code blocks
- Dynamic progress bar shown in `status` and after `next`
- Lessons alternate between "Deep-Dive Explanation" and "Active Micro-Quiz" formats (30% quiz probability)
- Quiz answer hidden on first display; user presses a key to reveal it with an animated pause

### Phase 1 — Foundation

- Python project scaffolded with `pyproject.toml`, editable install, and console script entry point
- Pydantic-based state manager reads and writes `~/.micro_learner/state.json`
- GitHub Copilot SDK integration (`gpt-4.1`) for syllabus and lesson generation
- Syllabus generation prompt forces a clean JSON array of step objects with no conversational fluff
- `start` and `next` CLI commands implement the core learn loop
