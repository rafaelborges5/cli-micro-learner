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

### Phase 7: Gamification (ON THE FENCE)
- [x] **7.1 Progress Bar Information Design:** Simplify what the bottom status bar should prioritize before changing its visuals.
- [ ] **7.2 Progress Bar Rendering + Visual Pass:** Refactor toolbar/progress rendering and apply the redesigned bar across themes and tighter terminal widths.
- [ ] **7.3 Quiz Answer Copy + Structure Rewrite:** Make revealed answers shorter, clearer, and more obviously review-oriented.
- [ ] **7.4 Quiz Answer Display Implementation:** Improve the visual separation and formatting of question versus answer content in the active lesson flow.
- [ ] **7.5 Quiz Answer Regression Tests:** Add coverage for updated reveal behavior across CLI, REPL, and note export flows.
- [ ] **7.6 Entrypoint/Packaging Cleanup:** Remove the current repo-root dependency on `PYTHONPATH=src` and verify development and installed entrypaths behave consistently.

### Phase 8: Guided Lesson Briefs (PLANNED)
- [ ] **Long-Form Lesson Inputs:** Allow syllabus steps to store richer user-provided lesson briefs.
- [ ] **AI-Generated Step Titles:** Generate concise titles for use in progress UI, menus, and notes.
- [ ] **Prompting from Briefs:** Use the longer brief as the main generation context for lessons.
- [ ] **UI/State Updates:** Carry both long descriptions and short titles through storage, resume, and notes.
- [ ] **Lesson Structure Rules:** Early lessons should establish context before switching to question-first formatting.

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
- **Environment:** Repo-root module execution currently needs `PYTHONPATH=src ./venv/bin/python3 -m micro_learner.main`; cleaning that up is now tracked in Phase 7.
- **Cache Layout:** Syllabus metadata is stored in `~/.micro_learner/syllabi/`, lesson artifacts in `~/.micro_learner/lessons/`, notes in `~/.micro_learner/notes/`, and UI settings in `~/.micro_learner/settings.json`.
- **Active Topic Model:** `state.json` now stores `active_syllabus_id`, not inline lesson progress/content.
- **Resume Safety:** Resumability is based on actual lesson artifacts on disk, not only the stored `cache_status`; fully cached records may be upgraded to `complete` lazily.
- **Current Validation Baseline:** `PYTHONPATH=src ./venv/bin/python3 -m unittest discover -s tests -v` is the current project-wide verification command, and the suite is green at 65 tests.
