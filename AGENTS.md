# AGENTS.md

Guidance for AI agents working in this repository.

## Project Snapshot

`cli-micro-learner` is a Python 3.10+ terminal app for structured micro-learning. It generates a progressive syllabus for a topic, caches lesson or quiz artifacts, plays them back through a Rich/prompt-toolkit CLI and REPL, and exports completed lessons to local Markdown notes.

The current product direction lives in:

- `dev-plan.md`: roadmap and phase planning. Treat this as the main product map.
- `AI_WORKFLOW_SUMMARY.md`: handoff/status summary for AI agents. Use this for operational context, known architecture, and validation baseline.

If those two files disagree, inspect the current code and tests before updating roadmap status. Prefer updating both docs in the same change when you complete roadmap work.

## Setup

This repo already uses a local virtual environment at `venv/`.

Common commands:

```bash
./venv/bin/pip install -e .
./venv/bin/micro-learner
./venv/bin/micro-learner shell
./venv/bin/micro-learner status
./venv/bin/micro-learner start "Advanced Rust Traits"
./venv/bin/python -m micro_learner
./venv/bin/python -m unittest discover -s tests -v
```

Do not rely on `PYTHONPATH=src`; the package is expected to work through editable install, console script, and `python -m micro_learner`.

## Architecture Map

- `src/micro_learner/main.py`: Click command group, console script entry point, and default REPL launcher.
- `src/micro_learner/repl.py`: persistent prompt-toolkit shell, slash commands, completion, resume modal, background cache warmup, toolbar state, and theme command.
- `src/micro_learner/logic.py`: shared command logic used by both Click commands and the REPL.
- `src/micro_learner/state.py`: Pydantic models, JSON persistence, syllabus records, lesson cache files, notes, settings, and resumability checks.
- `src/micro_learner/llm.py`: GitHub Copilot SDK integration, syllabus generation, lesson/quiz generation, interventions, and cache generation.
- `src/micro_learner/ui.py`: Rich rendering, themes, progress bars, toolbar formatting, lesson panels, quiz answers, and intervention panels.
- `tests/`: unittest suite covering CLI, state, REPL behavior, interventions, packaging entry points, quiz reveal, and note export behavior.

## Runtime State

The app writes user state outside the repo under `~/.micro_learner/`:

- `state.json`: global state with `active_syllabus_id`.
- `settings.json`: UI settings such as the selected theme.
- `syllabi/`: per-topic syllabus records.
- `lessons/`: cached lesson artifacts, grouped by syllabus id.
- `notes/`: exported Markdown notes by topic.

Tests should redirect these paths to temporary directories, following the existing `configure_state_paths` pattern.

## Product Workflow

Current roadmap focus is after the completed REPL/theme/cache work. Check `dev-plan.md` before starting feature work. At the time this file was last updated, the active planned areas are:

- Phase 8: guided lesson briefs; long-form syllabus input, AI-generated titles, and lesson prompting from generated briefs are implemented, while UI/state polish and first-lesson structure rules remain.
- Phase 9: README, developer guide, changelog, docstrings, and examples.
- Phase 10: continuous `/flow` lesson sessions.

Keep features aligned with the core philosophy:

- Structured progression over random facts.
- Cache-first lesson playback where possible.
- REPL-first UX while preserving scriptable Click commands.
- Rich terminal presentation without making tests depend on live terminal behavior.
- Local JSON state that remains resumable and recoverable.

## LLM Notes

The AI provider is GitHub Copilot SDK, imported as:

```python
from copilot import CopilotClient
```

The default model is currently `gpt-4.1`. Tests should mock `LLMManager` methods rather than making live Copilot calls.

When changing prompts, preserve machine-parseable contracts:

- Syllabus generation should return only a JSON array of `{title, brief}` step objects.
- Quiz generation stores question content separately from the answer by splitting on `ANSWER:`.
- Cached lesson artifacts should remain valid `LessonArtifact` Pydantic objects.

## Development Rules

- Preserve both entry styles: REPL-first default launch and explicit Click commands.
- Keep core behavior in `logic.py` when it needs to be shared by CLI and REPL.
- Keep persistence changes in `state.py`; avoid scattering filesystem paths through other modules.
- Keep rendering concerns in `ui.py`; do not duplicate style decisions in command logic.
- For REPL changes, update view/session state deliberately rather than reading global state ad hoc from many places.
- Avoid live network or LLM calls in tests.
- Avoid destructive operations against `~/.micro_learner/` during development; use temporary test paths.
- Do not overwrite unrelated user changes in this working tree.

## Commit Instructions

- Use prefixed commit messages, such as `feat:`, `fix:`, `test:`, `docs:`, or `chore:`.
- Keep commit messages to 10 words or fewer.
- Do not pass an explicit author or co-author option.
- Split unrelated changes into separate commits.

## Validation

Run the full baseline before handing off substantial changes:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

For entrypoint or packaging work, also verify:

```bash
./venv/bin/micro-learner --help
./venv/bin/python -m micro_learner --help
```

For REPL/UI work, prefer focused unit tests around state, rendering helpers, command handlers, and toolbar/formatted-text builders. Manual REPL checks are useful, but they are not a substitute for regression coverage.
