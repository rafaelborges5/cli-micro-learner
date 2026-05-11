# Contributing to micro-learner

## Setup

```bash
git clone <repo-url>
cd cli-micro-learner
pip install -e .
./venv/bin/python -m unittest discover -s tests -v
```

Python 3.10 or later is required. The editable install makes `micro-learner`, `python -m micro_learner`, and the test suite all work without any `PYTHONPATH` prefix.

---

## Architecture

The application is split across six modules. Each module owns a strict slice of responsibility — keep that separation when adding features.

### `main.py`
Click command group and console-script entry point. When invoked with no subcommand, it calls `asyncio.run(start_repl())` to drop into the REPL automatically. The `coro` decorator bridges Click's synchronous command dispatch and async handlers.

### `logic.py`
Shared command logic used by both Click commands and REPL slash-command handlers. All state reads and writes go through `state.py`; all LLM calls go through `llm.py`. `execute_start` has a `background` flag: when `True` it generates only the first lesson and returns the remaining steps for async pre-caching; when `False` it blocks until the full cache is ready (used by the non-REPL `start` command).

### `state.py`
Pydantic models, JSON persistence, and all filesystem path constants. Nothing outside this module should construct paths under `~/.micro_learner/` directly. `initialize_cached_topic` is the convenience entry point for tests and production code that needs a fully-cached, activated record in one call.

### `llm.py`
GitHub Copilot SDK wrapper (`from copilot import CopilotClient`). `LLMManager` reuses a single Copilot session across all `generate_cached_lessons` iterations to avoid per-lesson cold-start latency. The default model is `gpt-4.1`.

### `ui.py`
All Rich rendering, theme registry, and prompt_toolkit style builders. No rendering code belongs in `logic.py`, `repl.py`, or `main.py`. `set_current_theme` mutates the module-level `console` object's theme stack directly so already-open consoles pick up the change immediately.

### `repl.py`
The prompt_toolkit shell, slash-command handlers, `REPLSessionState` view-model, background prefetch task, and resume modal. View state is computed by `_refresh_view_state()` and stored in `shell.state`. Command handlers must call that method after any state-changing operation rather than updating display fields ad hoc.

---

## Data Flow

### `/start <topic>`

1. `cmd_start` → `execute_start(background=True)`
2. Prompts the user for a long-form learning brief
3. `LLMManager.generate_syllabus(topic, brief)` → `List[SyllabusStep]`
4. `create_syllabus_record` → `SyllabusRecord` with `cache_status="pending"`
5. Generates step 1 lesson → saves artifact → `activate_syllabus(record.id)`
6. Returns remaining steps to the REPL background task
7. `generate_cached_lessons` fills the rest asynchronously; `PrefetchViewState.status` moves `idle → warming → complete`
8. REPL displays the first lesson immediately without waiting for the full cache

### `/next`

1. `cmd_next` → `execute_next()`
2. Loads active `SyllabusRecord` → reads `LessonArtifact` from disk (`step-NNN.json`)
3. Renders lesson panel; calls `interactive_wait()` to collect E/D key presses
4. For quizzes: waits for reveal keypress, renders answer panel, calls `interactive_wait()` again
5. `append_note_entry()` writes to `~/.micro_learner/notes/<slug>.md`
6. Increments `current_lesson_index`; saves the updated record

---

## State Layout

```
~/.micro_learner/
├── state.json              # GlobalState { active_syllabus_id }
├── settings.json           # AppSettings { theme_name }
├── syllabi/
│   └── {slug}-{ts}.json    # SyllabusRecord (syllabus steps, progress index, cache_status)
├── lessons/
│   └── {syllabus_id}/
│       └── step-001.json   # LessonArtifact (content, answer, lesson_type)
└── notes/
    └── {topic-slug}.md     # Append-only Markdown with YAML frontmatter
```

Path constants are defined at the top of `state.py` and are module-level variables. Tests redirect them by reassigning those variables in `configure_state_paths(tmp_dir)` — see the pattern used in every test `setUp`.

---

## LLM Prompt Contracts

Three machine-parseable contracts must be preserved when editing prompts:

**Syllabus** — `generate_syllabus` must return a raw JSON array with no markdown fences and no prose. Each element must have exactly two string fields: `title` and `brief`. Validated by Pydantic; returns `[]` on failure.

**Quiz split** — `generate_quiz` (and the quiz branch of `generate_cached_lessons`) output must contain the literal string `ANSWER:`. Everything before is the question; everything after is the answer text. If `ANSWER:` is absent, the full response becomes the question and `answer` is set to `None`.

**Lesson format** — no structural contract; content is rendered verbatim as Markdown via Rich.

---

## Caching Strategy

- All lessons are pre-generated after `/start` and stored as individual `step-NNN.json` files.
- `/next` reads exclusively from disk and never makes a live LLM call.
- `choose_lesson_type(step_number, total_lessons)` forces the first third of every syllabus to `"lesson"` type so context is established before quizzes test recall.
- `is_syllabus_resumable` checks that the cache directory exists **and** either `cache_status == "complete"` or all `total_lessons` artifact files are present on disk. This handles records where `cache_status` was not written correctly due to an interrupted generation.

---

## How to Add a Theme

1. Open `src/micro_learner/ui.py`.
2. Copy an existing `UITheme(...)` block (Modern, Classic, or Matrix).
3. Set `name` to your new theme name.
4. Populate all 13 fields. Required `rich_styles` keys: `info`, `warning`, `error`, `success`, `header`, `topic`, `quiz_answer`, `panel_surface`, `answer_surface`, `toolbar_back`, `toolbar_box`, `toolbar_topic`, `toolbar_suffix_success`, `toolbar_suffix_warning`, `toolbar_suffix_error`, `toolbar_suffix_info`. Required `prompt_toolkit_styles` keys: `dialog`, `dialog.body`, `dialog frame.label`, `dialog shadow`, `bottom-toolbar`, `label`, `radio`, `radio-selected`, `radio-checked`, `radio-checked-selected`, `textarea`, `search`, `search-field`, `search-field.prompt`.
5. Add the entry to the `THEMES: dict[str, UITheme]` dict.
6. Test with `/theme <YourThemeName>` in the REPL.

All 13 `UITheme` fields are required (frozen dataclass with no defaults). A missing field raises `TypeError` at import time. There is no partial-theme fallback.

---

## Running Tests

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Rules to follow when writing or modifying tests:

- **Mock LLM calls** — patch `LLMManager` methods (`generate_syllabus`, `generate_cached_lessons`, etc.) rather than making live Copilot calls.
- **Redirect state paths** — call `configure_state_paths(Path(tmp_dir))` in `setUp` and `tmp_dir.cleanup()` in `tearDown`. Never write to the real `~/.micro_learner/`.
- **Test REPL helpers directly** — for toolbar, completion, and toast behavior, test the underlying state objects and formatting helpers. Do not test live `PromptSession` interaction.
- **Use `initialize_cached_topic`** when a test needs a fully-cached syllabus — it creates the record, saves all artifacts, and activates it in one call.
