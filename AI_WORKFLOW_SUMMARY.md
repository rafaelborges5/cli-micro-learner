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

### Phase 3: Knowledge Retention (PENDING)
- [ ] **Auto-Export:** Logic to append lessons to `~/.micro_learner/notes/{Topic}.md`.
- [ ] **Vault Formatting:** Ensure Markdown export is compatible with Obsidian/Notion.

## 📂 Key Architecture
- `src/micro_learner/main.py`: CLI Entry point (using `click`).
- `src/micro_learner/state.py`: Persistence and directory bootstrapping.
- `src/micro_learner/llm.py`: Copilot SDK wrapper and prompt engineering.
- `src/micro_learner/ui.py`: Centralized `rich` rendering helpers.

## ⚠️ Important Context for Future Agents
- **SDK Import:** The GitHub Copilot SDK is imported as `from copilot import CopilotClient`.
- **Model:** The default model used is `gpt-4.1` (verified as supported for this account).
- **Environment:** Always run via `./venv/bin/python3 -m micro_learner.main`.
