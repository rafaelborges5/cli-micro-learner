import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from prompt_toolkit.document import Document

from micro_learner import repl, state
from micro_learner.ui import (
    THEMES,
    _compute_toolbar_segments,
    build_prompt_message,
    build_prompt_style,
    get_current_theme,
    get_theme,
    render_toolbar,
    render_toolbar_formatted_text,
    resolve_theme_name,
    set_current_theme,
)


def configure_state_paths(base_dir: Path):
    state.APP_DIR = base_dir / ".micro_learner"
    state.SYLLABI_DIR = state.APP_DIR / "syllabi"
    state.LESSONS_DIR = state.APP_DIR / "lessons"
    state.NOTES_DIR = state.APP_DIR / "notes"
    state.STATE_FILE = state.APP_DIR / "state.json"
    state.SETTINGS_FILE = state.APP_DIR / "settings.json"


class REPLShellTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        configure_state_paths(Path(self.temp_dir.name))
        state.bootstrap()
        set_current_theme("Modern")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_shell_initializes_session_state(self):
        shell = repl.REPLShell()
        self.assertIsNone(shell.state.active_topic)
        self.assertTrue(shell.state.show_context_header)
        self.assertEqual(shell.state.prefetch.status, "idle")
        self.assertEqual(shell.state.pending_toasts, [])
        self.assertEqual(shell.state.theme_name, "Modern")

    def test_toolbar_shows_no_active_topic_message(self):
        shell = repl.REPLShell()
        toolbar = shell._get_toolbar()

        self.assertIn("No active topic", str(toolbar))

    def test_command_completion_still_works(self):
        shell = repl.REPLShell()

        completions = list(shell.completer.get_completions(Document("/st"), None))

        self.assertEqual([completion.text for completion in completions], ["/start", "/status"])

    def test_theme_name_resolution_is_case_insensitive(self):
        self.assertEqual(resolve_theme_name("matrix"), "Matrix")
        self.assertIsNone(resolve_theme_name("unknown"))

    def test_prompt_message_uses_current_theme_colors(self):
        state.save_settings(state.AppSettings(theme_name="Matrix"))
        shell = repl.REPLShell()

        prompt_message = build_prompt_message(shell.state.theme_name)

        self.assertIn('color="#00ff66"', prompt_message)
        self.assertIn('color="#99ff99"', prompt_message)

    def test_prompt_style_contains_modal_rules_for_active_theme(self):
        state.save_settings(state.AppSettings(theme_name="Classic"))
        shell = repl.REPLShell()

        prompt_style = build_prompt_style(shell.state.theme_name)

        self.assertIn(("dialog", "bg:#3b2f2f #efe6d1"), prompt_style.style_rules)
        self.assertEqual(get_current_theme().name, "Classic")

    def test_theme_registry_exposes_expected_semantic_styles(self):
        required_tokens = {"info", "warning", "error", "success", "header", "topic", "quiz_answer"}

        self.assertTrue(required_tokens.issubset(THEMES["Modern"].rich_styles))
        self.assertTrue(required_tokens.issubset(THEMES["Classic"].rich_styles))
        self.assertTrue(required_tokens.issubset(THEMES["Matrix"].rich_styles))

    def test_themes_render_distinct_toolbar_styles(self):
        set_current_theme("Modern")
        modern_toolbar = render_toolbar(1, 4, "Topic One", suffix="[Cache Ready]", suffix_style="success")

        set_current_theme("Classic")
        classic_toolbar = render_toolbar(1, 4, "Topic One", suffix="[Cache Ready]", suffix_style="success")

        set_current_theme("Matrix")
        matrix_toolbar = render_toolbar(1, 4, "Topic One", suffix="[Cache Ready]", suffix_style="success")

        self.assertNotEqual(modern_toolbar, classic_toolbar)
        self.assertNotEqual(classic_toolbar, matrix_toolbar)
        self.assertIn("■", classic_toolbar)
        self.assertIn("▓", matrix_toolbar)

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

    def test_build_resume_candidates_includes_status_metadata(self):
        shell = repl.REPLShell()
        active = state.initialize_cached_topic(
            "Active Topic",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        active.current_lesson_index = 1
        state.save_syllabus_record(active)
        state.activate_syllabus(active.id)
        state.create_syllabus_record("Broken Topic", ["Step 1"])

        shell._refresh_view_state()
        candidates = shell._build_resume_candidates()

        self.assertEqual(candidates[0].topic, "Broken Topic")
        self.assertFalse(candidates[0].resumable)
        self.assertIn("Cache Incomplete", candidates[0].label)
        self.assertTrue(candidates[1].is_active)
        self.assertTrue(candidates[1].is_completed)
        self.assertIn("Completed", candidates[1].label)

    def test_build_resume_candidates_treats_full_pending_cache_as_ready(self):
        shell = repl.REPLShell()
        record = state.create_syllabus_record("Topic One", ["Step 1", "Step 2"])
        state.save_lesson_artifacts(
            record.id,
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One"),
                state.LessonArtifact(step_number=2, sub_topic="Step 2", lesson_type="lesson", content="Two"),
            ],
        )

        candidates = shell._build_resume_candidates()

        self.assertTrue(candidates[0].resumable)
        self.assertNotIn("Cache Incomplete", candidates[0].label)

    def test_filter_resume_candidates_matches_live_query(self):
        shell = repl.REPLShell()
        candidates = [
            repl.ResumeCandidate("one", "Pending But Full", "A", True, False, False),
            repl.ResumeCandidate("two", "Topic Two", "B", True, True, False),
        ]

        filtered = shell._filter_resume_candidates(candidates, "pend")

        self.assertEqual([candidate.topic for candidate in filtered], ["Pending But Full"])

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
        self.assertIn("[9/15]", toolbar)

    def test_toolbar_preserves_topic_before_suffix_when_width_is_limited(self):
        toolbar = render_toolbar(
            9,
            15,
            "Topic One",
            suffix="[Caching 12/15]",
            max_width=38,
        )

        self.assertIn("[9/15]", toolbar)
        self.assertIn("Topic One", toolbar)
        self.assertNotIn("[Caching 12/15]", toolbar)

    def test_toolbar_drops_topic_before_progress_when_width_is_tight(self):
        toolbar = render_toolbar(
            9,
            15,
            "A very long topic name",
            suffix="[Cache Ready]",
            max_width=30,
        )

        self.assertIn("[9/15]", toolbar)
        self.assertNotIn("[Cache Ready]", toolbar)

    # --- _compute_toolbar_segments unit tests ---

    def test_segments_includes_all_at_wide_terminal(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(9, 15, "My Topic", "[Cache Ready]", 100, theme)
        self.assertEqual(seg.topic_segment, "My Topic")
        self.assertEqual(seg.suffix_segment, "[Cache Ready]")
        self.assertTrue(seg.include_percentage)

    def test_segments_drops_suffix_before_topic_at_medium_width(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(9, 15, "Topic One", "[Caching 12/15]", 38, theme)
        self.assertEqual(seg.topic_segment, "Topic One")
        self.assertEqual(seg.suffix_segment, "")

    def test_segments_count_label_always_present(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(9, 15, "A very long topic name", "[Cache Ready]", 30, theme)
        self.assertEqual(seg.count_label, "[9/15]")
        self.assertEqual(seg.suffix_segment, "")

    def test_segments_bar_width_scales_at_wide_terminal(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(5, 10, "Topic", "", 100, theme)
        self.assertEqual(len(seg.progress_bar), 20)

    def test_segments_bar_width_scales_at_medium_terminal(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(5, 10, "Topic", "", 60, theme)
        self.assertEqual(len(seg.progress_bar), 10)

    def test_segments_bar_width_clamps_at_narrow_terminal(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(5, 10, "Topic", "", 39, theme)
        self.assertEqual(len(seg.progress_bar), 8)

    def test_segments_fill_count_pads_to_available_width(self):
        theme = get_theme("Modern")
        seg = _compute_toolbar_segments(5, 10, "", "", 60, theme)
        # " " + bar + " " + count + optional_pct + fill_count == 60
        base = 1 + len(seg.progress_bar) + 1 + len(seg.count_label)
        pct = (1 + len(seg.percentage_label)) if seg.include_percentage else 0
        self.assertEqual(base + pct + seg.fill_count, 60)

    # --- render_toolbar_formatted_text tests ---

    def test_render_toolbar_formatted_text_contains_count_and_topic(self):
        set_current_theme("Modern")
        ft = render_toolbar_formatted_text(9, 15, "My Topic", max_width=80)
        plain = "".join(text for _, text in ft)
        self.assertIn("[9/15]", plain)
        self.assertIn("My Topic", plain)

    def test_render_toolbar_formatted_text_fills_to_max_width(self):
        set_current_theme("Modern")
        ft = render_toolbar_formatted_text(9, 15, "My Topic", max_width=80)
        plain = "".join(text for _, text in ft)
        self.assertEqual(len(plain), 80)

    def test_render_toolbar_formatted_text_all_fragments_have_noreverse(self):
        set_current_theme("Modern")
        ft = render_toolbar_formatted_text(9, 15, "My Topic", max_width=80)
        for style, _ in ft:
            self.assertIn("noreverse", style)

    # --- render_answer unit tests ---

    def test_render_answer_panel_has_check_title_and_content(self):
        from micro_learner.ui import render_answer, render_to_text
        set_current_theme("Modern")
        panel = render_answer("B — explanation text")
        plain = render_to_text(panel)
        self.assertIn("✓ Answer", plain)
        self.assertIn("B — explanation text", plain)

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

    async def test_theme_without_args_shows_current_theme(self):
        shell = repl.REPLShell()

        with patch.object(repl.console, "print") as print_mock:
            await shell.cmd_theme()

        print_mock.assert_called_once()
        self.assertFalse(shell.state.show_context_header)

    async def test_theme_command_applies_and_persists_theme(self):
        shell = repl.REPLShell()

        with patch.object(repl.console, "print") as print_mock:
            await shell.cmd_theme("matrix")

        print_mock.assert_called_once()
        self.assertEqual(shell.state.theme_name, "Matrix")
        self.assertEqual(state.load_settings().theme_name, "Matrix")

    async def test_theme_command_rejects_invalid_name(self):
        shell = repl.REPLShell()

        with patch.object(repl.console, "print") as print_mock:
            await shell.cmd_theme("neon")

        print_mock.assert_called_once()
        self.assertEqual(shell.state.theme_name, "Modern")

    def test_consume_context_header_flag_resets_to_default(self):
        shell = repl.REPLShell()
        shell._suppress_next_context_header()

        self.assertFalse(shell._consume_context_header_flag())
        self.assertTrue(shell.state.show_context_header)

    def test_toast_queue_is_consumed_once(self):
        shell = repl.REPLShell()
        shell._enqueue_toast("Saved", "success")

        toast = shell._consume_next_toast()

        self.assertIsNotNone(toast)
        self.assertEqual(toast.message, "Saved")
        self.assertIsNone(shell._consume_next_toast())

    def test_render_toast_prints_styled_message(self):
        shell = repl.REPLShell()
        toast = repl.REPLToast(message="Warmup complete", style="success")

        with patch.object(repl.console, "print") as print_mock:
            shell._render_toast(toast)

        print_mock.assert_called_once()

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
        self.assertEqual(shell.state.pending_toasts[0].message, "Background cache warmup complete.")

    async def test_background_prefetch_failure_enqueues_error_toast(self):
        shell = repl.REPLShell()
        record = state.create_syllabus_record("Topic One", ["Step 1", "Step 2"])

        async def fake_generate_cached_lessons(*args, **kwargs):
            raise RuntimeError("boom")

        with patch.object(repl, "LLMManager") as llm_mock:
            llm_mock.return_value.generate_cached_lessons = fake_generate_cached_lessons
            await shell._background_prefetch("Topic One", ["Step 2"], record.id)

        self.assertEqual(shell.state.prefetch.status, "failed")
        self.assertEqual(shell.state.pending_toasts[0].message, "Background cache warmup failed.")

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

    async def test_resume_without_args_uses_modal_selection(self):
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

        with patch.object(shell, "_show_resume_modal", AsyncMock(return_value=second.id)), \
             patch.object(repl, "execute_status") as execute_status_mock:
            await shell.cmd_resume()

        self.assertEqual(state.load_state().active_syllabus_id, second.id)
        execute_status_mock.assert_called_once_with(io=shell.io)

    async def test_resume_modal_cancel_keeps_active_state(self):
        shell = repl.REPLShell()
        first = state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One")],
        )
        state.activate_syllabus(first.id)

        with patch.object(shell, "_show_resume_modal", AsyncMock(return_value=None)):
            await shell.cmd_resume()

        self.assertEqual(state.load_state().active_syllabus_id, first.id)

    async def test_activate_resume_candidate_rejects_incomplete_record(self):
        shell = repl.REPLShell()
        broken = state.create_syllabus_record("Broken Topic", ["Step 1"])

        with patch.object(repl.console, "print") as print_mock:
            activated = shell._activate_resume_candidate(broken.id)

        self.assertFalse(activated)
        print_mock.assert_called()

    async def test_next_enqueues_note_export_success_toast(self):
        shell = repl.REPLShell()

        with patch.object(
            repl,
            "execute_next",
            AsyncMock(return_value=repl.ExecuteNextResult(note_exported=True, note_export_path="/tmp/note.md")),
        ):
            await shell.cmd_next()

        self.assertEqual(shell.state.pending_toasts[0].message, "Lesson note exported.")

    async def test_next_enqueues_note_export_failure_toast(self):
        shell = repl.REPLShell()

        with patch.object(
            repl,
            "execute_next",
            AsyncMock(return_value=repl.ExecuteNextResult(note_export_error="disk full")),
        ):
            await shell.cmd_next()

        self.assertEqual(shell.state.pending_toasts[0].message, "Lesson note export failed: disk full")

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
