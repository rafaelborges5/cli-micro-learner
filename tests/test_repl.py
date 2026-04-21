import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from prompt_toolkit.document import Document

from micro_learner import repl, state
from micro_learner.ui import render_toolbar


def configure_state_paths(base_dir: Path):
    state.APP_DIR = base_dir / ".micro_learner"
    state.SYLLABI_DIR = state.APP_DIR / "syllabi"
    state.LESSONS_DIR = state.APP_DIR / "lessons"
    state.NOTES_DIR = state.APP_DIR / "notes"
    state.STATE_FILE = state.APP_DIR / "state.json"


class REPLShellTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        configure_state_paths(Path(self.temp_dir.name))
        state.bootstrap()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_shell_initializes_session_state(self):
        shell = repl.REPLShell()
        self.assertIsNone(shell.state.active_topic)
        self.assertTrue(shell.state.show_context_header)
        self.assertEqual(shell.state.prefetch.status, "idle")

    def test_toolbar_shows_no_active_topic_message(self):
        shell = repl.REPLShell()
        toolbar = shell._get_toolbar()

        self.assertIn("No active topic", str(toolbar))

    def test_command_completion_still_works(self):
        shell = repl.REPLShell()

        completions = list(shell.completer.get_completions(Document("/st"), None))

        self.assertEqual([completion.text for completion in completions], ["/start", "/status"])

    def test_start_completion_suggests_deduplicated_topics_by_recency(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Python Typing",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        state.initialize_cached_topic(
            "Rust Ownership",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two")],
        )
        state.initialize_cached_topic(
            "Python Typing",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Three")],
        )

        completions = list(shell.completer.get_completions(Document("/start "), None))

        self.assertEqual([completion.text for completion in completions], ["Python Typing", "Rust Ownership"])

    def test_resume_completion_prioritizes_other_topics_before_active(self):
        shell = repl.REPLShell()
        active = state.initialize_cached_topic(
            "Active Topic",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        state.initialize_cached_topic(
            "Second Topic",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two")],
        )
        state.activate_syllabus(active.id)
        shell._refresh_view_state()

        completions = list(shell.completer.get_completions(Document("/resume "), None))

        self.assertEqual([completion.text for completion in completions], ["Second Topic", "Active Topic"])

    def test_completion_is_case_insensitive_prefix_based(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Advanced Rust Traits",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        state.initialize_cached_topic(
            "Rust Ownership",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two")],
        )

        completions = list(shell.completer.get_completions(Document("/start ad"), None))

        self.assertEqual([completion.text for completion in completions], ["Advanced Rust Traits"])

    def test_completion_handles_multi_word_topic_names(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Distributed Systems Design",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )

        completions = list(shell.completer.get_completions(Document("/start Distributed S"), None))

        self.assertEqual([completion.text for completion in completions], ["Distributed Systems Design"])

    def test_non_topic_commands_do_not_offer_topic_suggestions(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Python Typing",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )

        completions = list(shell.completer.get_completions(Document("/next "), None))

        self.assertEqual(completions, [])

    def test_render_toolbar_truncates_long_content(self):
        toolbar = render_toolbar(
            9,
            15,
            "A very long topic name that should not wrap in the prompt toolbar",
            suffix="[Caching 12/15]",
            max_width=40,
        )

        self.assertIn("\x1b", toolbar)
        self.assertNotIn("\n", toolbar)

    def test_context_header_without_active_topic_prints_hint(self):
        shell = repl.REPLShell()

        with patch.object(repl.console, "print") as print_mock:
            shell._print_context_header()

        print_mock.assert_called_once()

    def test_context_header_with_active_topic_prints_progress(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Body")],
        )

        with patch.object(repl.console, "print") as print_mock:
            shell._print_context_header()

        self.assertTrue(print_mock.called)

    async def test_next_suppresses_next_context_header_cycle(self):
        shell = repl.REPLShell()

        with patch.object(repl, "execute_next", AsyncMock()) as execute_next_mock:
            await shell.cmd_next()

        execute_next_mock.assert_awaited_once_with(io=shell.io)
        self.assertFalse(shell.state.show_context_header)

    async def test_status_routes_through_repl_io(self):
        shell = repl.REPLShell()

        with patch.object(repl, "execute_status") as execute_status_mock:
            await shell.cmd_status()

        execute_status_mock.assert_called_once_with(io=shell.io)
        self.assertFalse(shell.state.show_context_header)

    def test_consume_context_header_flag_resets_to_default(self):
        shell = repl.REPLShell()
        shell._suppress_next_context_header()

        self.assertFalse(shell._consume_context_header_flag())
        self.assertTrue(shell.state.show_context_header)

    async def test_background_prefetch_saves_artifacts_incrementally(self):
        shell = repl.REPLShell()
        record = state.create_syllabus_record("Topic One", ["Step 1", "Step 2"])

        async def fake_generate_cached_lessons(*args, **kwargs):
            artifact = state.LessonArtifact(
                step_number=2,
                sub_topic="Step 2",
                lesson_type="lesson",
                content="Second lesson",
            )
            kwargs["artifact_callback"](artifact)
            return [artifact]

        with patch.object(repl, "LLMManager") as llm_mock, \
             patch.object(repl.console, "print"):
            llm_mock.return_value.generate_cached_lessons = fake_generate_cached_lessons
            shell._mark_prefetch_started("1/2")
            await shell._background_prefetch("Topic One", ["Step 2"], record.id)

        self.assertIsNotNone(state.load_lesson_artifact(record.id, 2))
        self.assertEqual(shell.state.prefetch.status, "complete")

    async def test_resume_with_topic_argument_activates_matching_topic(self):
        shell = repl.REPLShell()
        first = state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        second = state.initialize_cached_topic(
            "Topic Two",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two")],
        )
        state.activate_syllabus(first.id)

        with patch.object(repl, "execute_status") as execute_status_mock:
            await shell.cmd_resume("topic", "two")

        self.assertEqual(state.load_state().active_syllabus_id, second.id)
        execute_status_mock.assert_called_once_with(io=shell.io)

    async def test_resume_with_unknown_topic_shows_error(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )

        with patch.object(repl.console, "print") as print_mock:
            await shell.cmd_resume("missing")

        print_mock.assert_called()

    async def test_next_shows_wait_message_when_prefetch_step_not_ready(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Topic One",
            ["Step 1", "Step 2"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Body")],
        )
        active = state.load_active_syllabus()
        active.current_lesson_index = 1
        active.cache_status = "pending"
        state.save_syllabus_record(active)

        loop = asyncio.get_running_loop()
        shell.prefetch_task = loop.create_future()
        shell._mark_prefetch_started("1/2")

        with patch.object(repl.console, "print") as print_mock, \
             patch.object(repl, "execute_next", AsyncMock()) as execute_next_mock:
            await shell.cmd_next()

        execute_next_mock.assert_not_awaited()
        self.assertTrue(print_mock.called)

    async def test_next_waits_briefly_for_artifact_to_appear(self):
        shell = repl.REPLShell()
        record = state.initialize_cached_topic(
            "Topic One",
            ["Step 1", "Step 2"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Body")],
        )
        active = state.load_active_syllabus()
        active.current_lesson_index = 1
        active.cache_status = "pending"
        state.save_syllabus_record(active)

        async def save_later():
            await asyncio.sleep(0.05)
            state.save_lesson_artifact(
                record.id,
                state.LessonArtifact(step_number=2, sub_topic="Step 2", lesson_type="lesson", content="Later"),
            )

        loop = asyncio.get_running_loop()
        shell.prefetch_task = loop.create_task(asyncio.sleep(1))
        shell._mark_prefetch_started("1/2")
        loop.create_task(save_later())

        with patch.object(repl, "execute_next", AsyncMock()) as execute_next_mock, \
             patch.object(repl.console, "print") as print_mock:
            await shell.cmd_next()

        execute_next_mock.assert_awaited_once_with(io=shell.io)
        print_mock.assert_not_called()

    def test_refresh_view_state_loads_active_topic_snapshot(self):
        shell = repl.REPLShell()
        record = state.initialize_cached_topic(
            "Topic One",
            ["Step 1", "Step 2"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Body")],
        )
        record.current_lesson_index = 1
        state.save_syllabus_record(record)

        shell._refresh_view_state()

        self.assertIsNotNone(shell.state.active_topic)
        self.assertEqual(shell.state.active_topic.topic, "Topic One")
        self.assertEqual(shell.state.active_topic.current_lesson_index, 1)

    def test_toolbar_uses_prefetch_view_state_suffix(self):
        shell = repl.REPLShell()
        state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Body")],
        )
        shell._mark_prefetch_started("1/1")

        toolbar = shell._get_toolbar()

        self.assertIn("Caching", str(toolbar))


if __name__ == "__main__":
    unittest.main()
