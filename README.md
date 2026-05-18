# micro-learner

A terminal micro-learning tool that turns idle developer time into structured, AI-driven lessons.

Instead of random facts, `micro-learner` generates a 15-step progressive syllabus for any topic you choose, caches every lesson up front, and delivers them one at a time through a clean REPL shell — no waiting, no context-switching, no doomscrolling.

## Features

- **Structured syllabi** — AI generates a logical 15-step curriculum so lessons build on each other rather than repeating or jumping around
- **Cache-first playback** — all lessons are pre-generated after `/start`, so `/next` is instant with no per-command LLM latency
- **Guided learning briefs** — optionally provide a long-form brief when starting a topic to steer exactly what each lesson covers
- **Explanations and quizzes** — lessons alternate between deep-dive explanations and active micro-quizzes with a hidden reveal
- **In-lesson interventions** — press **E** for a simpler analogy or **D** for a concrete code example at any point during a lesson
- **Persistent REPL shell** — single `micro-learner` launch with tab-completion, history, and a live progress toolbar
- **Three terminal themes** — Modern, Classic, and Matrix; persisted across sessions
- **Auto-export to Markdown** — completed lessons are appended to `~/.micro_learner/notes/<topic>.md` in Obsidian-compatible format
- **Multi-topic management** — start new topics without losing prior progress; resume any saved syllabus from an interactive search picker

## Prerequisites

This tool uses **GitHub Copilot** as its LLM backend via the [GitHub Copilot SDK](https://github.com/github/copilot-sdk). Before installing, you need:

1. An active **GitHub Copilot subscription** (Individual, Business, or Enterprise).
2. The **GitHub CLI** installed and authenticated:

```bash
# Install the GitHub CLI (https://cli.github.com)
gh auth login
```

3. The **GitHub Copilot CLI extension**:

```bash
gh extension install github/gh-copilot
```

Verify everything is working:

```bash
gh copilot --version
```

If that command succeeds, `micro-learner` will be able to reach Copilot automatically — no further auth setup is needed.

## Installation

Requires Python 3.10 or later.

```bash
git clone <repo-url>
cd cli-micro-learner
pip install -e .
```

Runtime dependencies (`rich`, `pydantic`, `click`, `prompt-toolkit`, `github-copilot-sdk`) are installed automatically.

## Quick Start

```bash
micro-learner        # launch REPL (default)
```

Inside the REPL:

```
/start "Advanced Rust Traits"
/next
/next
```

## CLI Commands

These commands work outside the REPL for scripting and shell-friendly use:

| Command | Description |
|---------|-------------|
| `micro-learner` | Launch the interactive REPL (default when no subcommand is given) |
| `micro-learner shell` | Explicitly launch the REPL |
| `micro-learner start <topic>` | Generate a new syllabus for `<topic>` and make it active |
| `micro-learner next` | Display the next cached lesson or quiz |
| `micro-learner status` | Show active topic and current lesson progress |
| `micro-learner resume` | Open the syllabus browser to switch active topics |

## REPL Slash Commands

Once inside the REPL session:

| Command | Description |
|---------|-------------|
| `/start <topic>` | Generate a new syllabus and begin learning |
| `/next` | Fetch the next lesson or quiz |
| `/status` | Show current topic and lesson progress inline |
| `/resume [topic]` | Open the interactive syllabus picker; optionally pass a topic name to jump directly |
| `/theme [name]` | Show current theme or switch to `Modern`, `Classic`, or `Matrix` |
| `/help` | List all available commands |
| `/quit` or `/exit` | Exit the session |

## Keyboard Shortcuts During a Lesson

After a lesson or quiz is displayed, the following keys are active before you advance:

| Key | Action |
|-----|--------|
| **E** | Request a simpler analogy for the current concept |
| **D** | Request a concrete code example for the current concept |
| Any other key | Advance to the next step |

The prompt reads: `(E: Analogy, D: Code, Any other key: Continue)`

Intervention content is also appended to your notes for later review.

## Themes

Switch themes with `/theme <name>` inside the REPL. The selection persists across sessions.

| Theme | Description |
|-------|-------------|
| **Modern** (default) | Dark background with blue, pink, and cyan accents; `█░` progress bar |
| **Classic** | Warm beige and brown palette; `■·` progress bar |
| **Matrix** | Green-on-black monochrome; `▓·` progress bar |

## Note Export

Lessons are saved automatically to `~/.micro_learner/notes/<topic-slug>.md` after each `/next`.

Each file uses YAML frontmatter for Obsidian/Notion compatibility:

```yaml
---
title: "Advanced Rust Traits"
topic: "Advanced Rust Traits"
source: "micro-learner"
created: 2026-05-11T10:00:00Z
updated: 2026-05-11T10:45:00Z
tags:
  - micro-learner
  - topic/advanced-rust-traits
---
```

The body contains session headers, per-lesson sections with step numbers and briefs, quiz answers marked as `**Answer:** …`, and any analogy or code-example interventions you triggered.

## Data Directory

```
~/.micro_learner/
├── state.json       # active syllabus pointer
├── settings.json    # theme preference
├── syllabi/         # per-topic syllabus records (JSON)
├── lessons/         # cached lesson artifacts grouped by syllabus ID
└── notes/           # exported Markdown notes by topic slug
```

---

## Examples

### Starting a new topic

```
micro-learner > /start "Advanced Rust Traits"
  Learning brief (optional — press Enter to skip):
  > Focus on associated types and where clauses in real-world APIs.

  Generating syllabus...  ✓
  Caching lessons in background...

  ╭─ Advanced Rust Traits — Step 1 ────────────────────────╮
  │                                                        │
  │  ## What Are Traits?                                   │
  │                                                        │
  │  A trait defines shared behaviour across types.        │
  │  Think of it as a contract: any type that impl-        │
  │  ements a trait promises to provide certain            │
  │  methods ...                                           │
  │                                                        │
  ╰────────────────────────────────────────────────────────╯

  (E: Analogy, D: Code, Any other key: Continue)

 ██████░░░░░░░░░░░░░░ [1/15]  7%  Advanced Rust Traits
micro-learner >
```

### Quiz reveal

```
  ╭─ Quiz: Step 4 — Associated Types ─────────────────────╮
  │                                                       │
  │  What keyword introduces an associated type inside    │
  │  a trait definition?                                  │
  │                                                       │
  │  A. impl    B. type    C. where    D. self            │
  │                                                       │
  ╰───────────────────────────────────────────────────────╯

  Think about your answer, then press any key to reveal...

  ╭─ ✓ Answer ────────────────────────────────────────────╮
  │  B. `type` — associated types are declared with      │
  │  `type Name;` inside the trait body. The impl block  │
  │  then specifies the concrete type.                   │
  ╰───────────────────────────────────────────────────────╯
```

### Switching themes

```
micro-learner > /theme Matrix
  Theme set to Matrix.

 ▓▓▓▓▓▓▓▓·············· [4/15] 27%  Advanced Rust Traits
micro-learner >
```

### Resuming a prior topic

```
micro-learner > /resume

  Search: rust▌

  > Advanced Rust Traits       4 / 15   27%  Active
    Async Rust Patterns        0 / 15    0%
    Python Decorators         15 / 15  100%  Completed
```
