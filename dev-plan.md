🧠 Micro-Learner CLI: Project Roadmap

1. Project Overview

A terminal-based CLI application designed to turn idle developer time into structured micro-learning. Instead of doomscrolling or losing focus, the user can run this lightweight tool in their current terminal window to learn bite-sized, highly relevant concepts.

Key Design Philosophies:

Structured Progression: Uses a generated "Curriculum Index" rather than random facts to ensure logical learning steps and prevent duplicate content.

Format Variety: Alternates between deep-dive explanations and active micro-quizzes to keep cognitive engagement high.

Standalone CLI: Runs natively in the current terminal window on demand (no forced Tmux pane orchestration).

Aesthetic UI: Utilizes terminal styling (e.g., Python's Rich library) for a clean, distraction-free reading experience.

2. Technical Stack

Language: Python 3

UI/Styling: Rich (for Markdown rendering, progress bars, and colored text)

AI Integration: Any LLM API (OpenAI, Anthropic, Gemini) or local via Ollama.

State Management: Local JSON files (~/.micro_learner/state.json and ~/.micro_learner/syllabi/).

3. Core Mechanics & The "Curriculum Index"

To avoid LLM amnesia and duplicated teachings, the app uses a Curriculum Index approach:

Topic Initialization: User runs the app and inputs a new topic (e.g., "Advanced Rust Traits").

Syllabus Generation: The app asks the LLM to generate a 15-20 step syllabus/outline on this topic and saves it as a JSON array.

Step-by-Step Execution: Each time the user requests a lesson, the app looks at the current index (e.g., Step 4: "Associated Types"), prompts the LLM to teach specifically that sub-topic, and increments the tracker to Step 5.

4. Implementation Phases

Phase 1: Foundation (The MVP)

Goal: Get the core loop working with local state and API calls.

[x] Setup: Initialize the Python project and necessary directories (~/.micro_learner/).

[x] State Manager: Write the logic to read/write a current_state.json file (tracking the active topic and current lesson index).

[x] LLM Prompts: * Write Prompt 1: Generate a JSON array of 15 sub-topics based on user input.

Write Prompt 2: Generate a 150-word lesson based on a specific sub-topic.

[x] Basic CLI: Create the loop: Check state -> If no topic, ask for one -> Fetch current lesson -> Display plain text -> Wait for Enter -> Increment index.

Phase 2: User Interface & Formatting

Goal: Make it beautiful and engaging.

[x] Rich Markdown Integration: Pass the LLM's output through Rich to render bold text, code blocks, and syntax highlighting.

[x] Format Alternation: Modify the prompt logic to randomly (or sequentially) ask the LLM to format the output as either a "Deep-Dive Explanation" or an "Active Micro-Quiz" (where the answer is hidden until the user presses a key).

[x] The Progress Bar: Implement the Rich progress bar at the bottom of the screen: [████░░░] 40% | Topic: Advanced Rust | Lesson 4/10.

Phase 3: Knowledge Retention & Multi-Topic Management

Goal: Save what you learn and manage multiple syllabi over time.

[x] Export Directory: Create a ~/.micro_learner/notes/ directory.

[x] Save Logic: After the user presses Enter to complete a lesson, silently append the markdown text to a file named {Topic_Name}.md.

[x] Formatting the Vault: Ensure the exported markdown includes timestamps and clean headers so it can be directly imported into tools like Obsidian or Notion.

[x] Multi-Topic State: Persist each syllabus as its own JSON file under ~/.micro_learner/syllabi/ (keyed by topic name + timestamp) so starting a new topic no longer overwrites the previous one.

[x] Batch Lesson Pre-generation: Immediately after the syllabus is created, generate and cache all 15 lessons to disk in one go. `next` then just reads from the cache — instant, no LLM call. This also eliminates the 10-20s per-command latency caused by cold-starting a new LLM session each time.

[x] Syllabus Browser (Resume): On launch, if prior syllabi exist, show an interactive menu (using Rich's prompt or a simple numbered list) that mirrors the feel of `gemini --resume` — each entry shows the topic name, lesson progress (e.g. "7 / 15"), and completion percentage. The user can pick one to resume or choose to start something new.

Phase 4: Advanced Interactions

Goal: Add interactive safety valves mid-lesson.

[x] The "I'm Stuck" Keys: Implement a keyboard listener (like the keyboard or pynput library, or standard tty manipulation).

[x] Press E: Triggers a new LLM call to rewrite the current lesson using a simpler analogy.

[x] Press D: Triggers a new LLM call to provide a concrete code snippet for the current concept.

Phase 5: Integrated REPL Shell

Goal: Replace the separate CLI commands with a single, persistent interactive session — a modern "AI CLI" feel where the user never leaves the tool.


[ ] Interactive Loop: Replace the Click command dispatch with a prompt-driven REPL loop (e.g. using prompt_toolkit or a simple input() loop styled with Rich). The user launches `micro-learner` once and stays inside the session.

[ ] Slash Commands: Implement in-session commands that mirror the current CLI verbs:
    /start <topic>  — generate and load a new syllabus
    /next           — fetch the next lesson or quiz
    /status         — show current progress inline
    /resume         — open the syllabus browser (from Phase 3) without exiting
    /quit           — cleanly exit the session

[ ] Persistent Context Bar: Render a persistent header or footer (using Rich Live or a static top panel) that always shows the active topic and lesson progress — no need to run /status to know where you are.

[ ] Progressive Cache Warmup: Generate and display the first lesson or quiz immediately, then continue generating the remaining cached lessons in the background so the user can begin learning without waiting for the full cache build to finish.

[ ] Graceful Fallback: Keep the original Click commands working as a thin wrapper so the tool is still scriptable and pipe-friendly even after the REPL is the primary UX.

Phase 6: Gamification (On The Fence)

Goal: Add challenge checkpoints for retention — not yet committed to this direction.

[ ] "Boss Fight" Checkpoints: Add logic to the State Manager. If current_lesson % 5 == 0, prompt the LLM to generate a practical challenge incorporating the last 4 lessons instead of a standard teaching.

5. Next Steps

To begin development, the first technical hurdle will be drafting the System Prompts that force the LLM to reliably return the JSON syllabus without any conversational fluff.
