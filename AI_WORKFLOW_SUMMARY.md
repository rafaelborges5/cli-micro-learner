# AI Workflow Summary: Micro-Learner CLI

This document serves as a persistent state and progress record for AI agents working on the Micro-Learner CLI project.

## 🚀 Project Overview
A terminal-based micro-learning application that generates structured 15-step syllabi using GitHub Copilot and delivers bite-sized lessons or quizzes.

## 🛠 Technical Stack
- **Language:** Python 3.10+
- **UI:** `rich` (Panels, Progress Bars, Markdown)
- **AI:** GitHub Copilot SDK (Module: `copilot`)
- **State:** `pydantic` for JSON persistence in `~/.micro_learner/state.json`, `~/.micro_learner/settings.json`, and per-syllabus cache directories

## 📈 Progress Dashboard

### Phase 1: Foundation (COMPLETED)
- [x] **Scaffolding:** Project structure with `pyproject.toml` and `venv`.
- [x] **State Manager:** Pydantic-based state for tracking topics, syllabus, and progress.
- [x] **LLM Integration:** Async client for GitHub Copilot (`gpt-4.1`).
- [x] **Syllabus Generation:** Prompt logic to force clean JSON arrays for curriculum.
- [x] **Core Loop:** `start` and `next` commands implemented.

### Phase 2: UI & Formatting (COMPLETED)
- [x] **Aesthetic Layouts:** Lessons wrapped in `rich.panel.Panel` with stylized headers.
- [x] **Progress Tracking:** Dynamic progress bars in `status` and `next` outputs.
- [x] **Format Alternation:** 30% chance of generating an "Active Micro-Quiz" instead of an explanation.
- [x] **Interaction Polish:** Rotating status messages and delayed "Reveal" logic for quizzes.

### Phase 3: Knowledge Retention & Multi-Topic Management (COMPLETED)
- [x] **Multi-Topic Persistence:** Each syllabus now lives as its own JSON record under `~/.micro_learner/syllabi/`, with global state reduced to an active syllabus pointer.
- [x] **Auto-Export:** Completed lessons are exported to `~/.micro_learner/notes/{topic}.md` after successful lesson completion.
- [x] **Vault Formatting:** Topic notes now use YAML frontmatter plus per-syllabus session sections for Obsidian/Notion-friendly organization.
- [x] **Batch Lesson Pre-Generation:** `start` generates and caches all lesson artifacts up front under `~/.micro_learner/lessons/`.
- [x] **Cache-First Playback:** `next` reads cached lesson artifacts instead of making live LLM calls.
- [x] **Syllabus Browser / Resume:** `resume` lists stored syllabi, shows progress, and switches the active syllabus safely.

### Phase 4: Advanced Interactions (COMPLETED)
- [x] **"I'm Stuck" Keys:** Implemented interactive `getchar()` loop for analogies (`E`) and code snippets (`D`).
- [x] **LLM Interventions:** Added live asynchronous LLM calls for simpler explanations and concrete examples.
- [x] **UI Rendering:** Beautifully rendered intervention panels using `rich` styling.
- [x] **Enhanced Note Export:** Dynamically generated interventions are now persisted in the Markdown notes.
- [x] **End-to-End Verification:** Comprehensive test suite implemented and verified.

### Phase 5: Integrated REPL Shell (COMPLETED)
- [x] **Interactive Loop:** Persistent `prompt_toolkit` session with history and tab auto-completion.
- [x] **Slash Commands:** Integrated `/start`, `/next`, `/status`, `/resume`, `/help`, and `/quit`.
- [x] **Persistent Context Bar:** Bottom toolbar showing live progress and topic info with `rich` styling.
- [x] **Progressive Cache Warmup:** First lesson is generated instantly; remaining 14 are cached in an `asyncio` background task.
- [x] **Unified Architecture:** Core logic decoupled into `logic.py`, shared between Click CLI and REPL.
- [x] **Verified Stability:** REPL-first architecture is covered by the active unittest suite.

### Phase 6: Advanced REPL Experience & UX Polish (COMPLETED)
- [x] **UI State Layer:** Added a centralized REPL session/view-state layer for active topic, cache state, prompt state, completion topics, and transient toasts.
- [x] **Contextual Completion:** `/start` and `/resume` now complete against learning history with deduped, recency-ordered topic suggestions.
- [x] **Notification System:** REPL-only inline toasts now surface background cache warmup and lesson note export outcomes.
- [x] **Interactive Resume Modal:** Bare `/resume` opens a prompt-toolkit live-search picker instead of the older numbered list flow.
- [x] **Theme System:** `/theme` switches between `Modern`, `Classic`, and `Matrix`, persists the selection, and applies it across Rich output, toolbar, prompt, and resume UI.

### Phase 7: Gamification (COMPLETED)
- [x] **7.1 Progress Bar Information Design:** Simplify what the bottom status bar should prioritize before changing its visuals.
- [x] **7.2 Progress Bar Rendering + Visual Pass:** Extracted `_compute_toolbar_segments` shared layout logic; bar width scales with terminal width; `FormattedText` and ANSI paths unified across all three themes.
- [x] **7.3 Quiz Answer Copy + Structure Rewrite:** Tightened answer copy and export structure so revealed answers read as concise review guidance.
- [x] **7.4 Quiz Answer Display Implementation:** Themed reveal separator and `render_answer` panel give clear visual weight to the question-versus-answer split.
- [x] **7.5 Quiz Answer Regression Tests:** Regression coverage for answer reveal in CLI output and note export; missing-answer fallback covered.
- [x] **7.6 Entrypoint/Packaging Cleanup:** Added `__main__.py`; `PYTHONPATH=src` no longer required; editable install, console script, and `python -m micro_learner` all verified.

### Phase 8: Guided Lesson Briefs (COMPLETE)
- [x] **Long-Form Lesson Inputs:** New syllabus creation now prompts for a long-form learning brief and stores generated structured syllabus steps.
- [x] **AI-Generated Step Titles:** Syllabus generation returns concise AI-generated titles for progress UI, menus, and notes.
- [x] **Prompting from Briefs:** Lesson and quiz cache generation uses the generated per-step brief as the main instructional context.
- [x] **UI/State Updates:** Status output and notes expose generated briefs, while resume views stay compact with generated titles.
- [x] **Lesson Structure Rules:** Cached generation forces the first third of a syllabus to explanation lessons before allowing quiz/question-first formatting.

### Phase 9-A: User-Facing Documentation (COMPLETE)
- [x] **9.1 README:** `README.md` at project root — purpose, install, CLI commands, REPL slash commands, keyboard shortcuts, note export format, theme options.
- [x] **9.3 CHANGELOG:** `CHANGELOG.md` at project root — milestone-by-milestone summary of phases 1–8.
- [x] **9.5 Code Examples:** ASCII screenshots embedded in README illustrating REPL, progress bar, theme switching, and quiz reveal.

### Phase 9-B: Developer Documentation (COMPLETE)
- [x] **9.2 Developer Guide:** `CONTRIBUTING.md` — architecture, data flow, state layout, LLM prompt contracts, caching strategy, how to add a theme, how to run tests.
- [x] **9.4 Inline Docstrings:** 26 public symbols documented across all 6 source modules (25 originally missing + `ExecuteNextResult` updated); all docstrings verified via `help()`.

### Phase 10-A: Core Continuous Lesson Flow (COMPLETE)
- [x] **10.1 /flow Command:** `/flow [n]` slash command runs up to n lessons back-to-back (default: all remaining); returns to REPL when done or syllabus ends.
- [x] **10.2 Clean Lesson Transitions:** Screen clears between lessons via `clear_screen()` in `ui.py`.
- [x] **10.3 Session Progress Header:** `render_flow_header()` prints a themed Rule (`Flow: Lesson N of M`) above each lesson.

### Phase 10-B: Flow Controls & State (COMPLETE)
- [x] **10.4 ESC-to-Pause:** Pressing Esc mid-lesson in `interactive_wait()` returns `(interventions, True)`; `execute_next()` returns `ExecuteNextResult(paused=True)` without advancing the index or exporting notes. Re-running `/flow` or `/next` resumes from the same lesson.
- [x] **10.5 Flow State in Toolbar:** `REPLSessionState` tracks `flow_active`, `flow_current`, `flow_total`; `_toolbar_suffix()` shows `[Flow: N/M]` while a flow session is active; `_set_flow_state()` clears it in a `finally` block so it always reverts on exit or exception.

## 📂 Key Architecture
- `src/micro_learner/main.py`: CLI entry point; launches REPL by default.
- `src/micro_learner/repl.py`: Interactive shell loop, contextual completion, notifications, theme switching, and resume modal flow.
- `src/micro_learner/logic.py`: Core application logic (the "brain" of the app).
- `src/micro_learner/state.py`: Persistence, syllabus records, note export, resumability checks, and app settings.
- `src/micro_learner/llm.py`: Copilot SDK wrapper and cache generation.
- `src/micro_learner/ui.py`: Theme registry, centralized `rich` rendering, prompt styling, and ANSI toolbar bridge.

## ⚠️ Important Context for Future Agents
- **SDK Import:** The GitHub Copilot SDK is imported as `from copilot import CopilotClient`.
- **Model:** The default model used is `gpt-4.1` (verified as supported for this account).
- **Environment:** The package is installed in editable mode (`pip install -e .`). Run via `./venv/bin/micro-learner` (console script) or `./venv/bin/python3 -m micro_learner` (module). No `PYTHONPATH` prefix needed.
- **Cache Layout:** Syllabus metadata is stored in `~/.micro_learner/syllabi/`, lesson artifacts in `~/.micro_learner/lessons/`, notes in `~/.micro_learner/notes/`, and UI settings in `~/.micro_learner/settings.json`.
- **Active Topic Model:** `state.json` now stores `active_syllabus_id`, not inline lesson progress/content.
- **Syllabus Step Model:** New syllabus records use structured steps with `title` and `brief`; legacy string-syllabus records are removed during bootstrap rather than migrated.
- **Resume Safety:** Resumability is based on actual lesson artifacts on disk, not only the stored `cache_status`; fully cached records may be upgraded to `complete` lazily.
- **Current Validation Baseline:** `./venv/bin/python3 -m unittest discover -s tests -v` — suite is green at 105 tests.
