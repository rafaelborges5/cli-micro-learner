# AI Workflow Summary: Micro-Learner CLI

This document serves as a persistent state and progress record for AI agents working on the Micro-Learner CLI project.

## 🚀 Project Overview
A terminal-based micro-learning application that generates structured 15-step syllabi using GitHub Copilot and delivers bite-sized lessons or quizzes.

## 🛠 Technical Stack
- **Language:** Python 3.10+
- **UI:** `rich` (Panels, Progress Bars, Markdown)
- **AI:** GitHub Copilot SDK (Module: `copilot`)
- **State:** `pydantic` for JSON persistence in `~/.micro_learner/state.json`

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
- [x] **End-to-End Verification:** Comprehensive test suite implemented and verified (23/23 tests passing).

### Phase 5: Integrated REPL Shell (COMPLETED)
- [x] **Interactive Loop:** Persistent `prompt_toolkit` session with history and tab auto-completion.
- [x] **Slash Commands:** Integrated `/start`, `/next`, `/status`, `/resume`, `/help`, and `/quit`.
- [x] **Persistent Context Bar:** Bottom toolbar showing live progress and topic info with `rich` styling.
- [x] **Progressive Cache Warmup:** First lesson is generated instantly; remaining 14 are cached in an `asyncio` background task.
- [x] **Unified Architecture:** Core logic decoupled into `logic.py`, shared between Click CLI and REPL.
- [x] **Verified Stability:** All 23 tests passing with new architecture.

### Phase 6: Advanced REPL Experience & UX Polish (PLANNED)
- [ ] **Dynamic Layouts:** Persistent dashboard-style UI using `rich.layout`.
- [ ] **Contextual Completion:** Smart suggestions for topic names and history.
- [ ] **Notification System:** Inline alerts for background task completions.
- [ ] **Interactive Modals:** Use dialog boxes for complex selections (e.g., resuming syllabi).

### Phase 7: Gamification (ON THE FENCE)
- [ ] **"Boss Fight" Checkpoints:** Integrated practical challenges every 5 lessons.

## 📂 Key Architecture
- `src/micro_learner/main.py`: CLI entry point; launches REPL by default.
- `src/micro_learner/repl.py`: Interactive shell loop, history, and auto-completion.
- `src/micro_learner/logic.py`: Core application logic (the "brain" of the app).
- `src/micro_learner/state.py`: Persistence, syllabus records, and note export.
- `src/micro_learner/llm.py`: Copilot SDK wrapper and cache generation.
- `src/micro_learner/ui.py`: Centralized `rich` rendering and ANSI toolbar bridge.

## ⚠️ Important Context for Future Agents
- **SDK Import:** The GitHub Copilot SDK is imported as `from copilot import CopilotClient`.
- **Model:** The default model used is `gpt-4.1` (verified as supported for this account).
- **Environment:** Always run via `./venv/bin/python3 -m micro_learner.main`.
- **Cache Layout:** Syllabus metadata is stored in `~/.micro_learner/syllabi/`, lesson artifacts in `~/.micro_learner/lessons/`, and notes in `~/.micro_learner/notes/`.
- **Active Topic Model:** `state.json` now stores `active_syllabus_id`, not inline lesson progress/content.
- **Resume Safety:** Only syllabi with `cache_status == "complete"` and a present lesson cache directory should be treated as resumable.
