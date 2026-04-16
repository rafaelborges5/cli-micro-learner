import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from micro_learner import main, state


def configure_state_paths(base_dir: Path):
    state.APP_DIR = base_dir / ".micro_learner"
    state.SYLLABI_DIR = state.APP_DIR / "syllabi"
    state.LESSONS_DIR = state.APP_DIR / "lessons"
    state.NOTES_DIR = state.APP_DIR / "notes"
    state.STATE_FILE = state.APP_DIR / "state.json"


class CliPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        configure_state_paths(Path(self.temp_dir.name))
        state.bootstrap()
        self.runner = CliRunner()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_creates_new_active_syllabus_without_overwriting_existing_records(self):
        with patch.object(main.LLMManager, "generate_syllabus", return_value=["Step 1", "Step 2"]), \
             patch.object(
                 main.LLMManager,
                 "generate_cached_lessons",
                 return_value=[
                     state.LessonArtifact(
                         step_number=1,
                         sub_topic="Step 1",
                         lesson_type="lesson",
                         content="Lesson 1",
                     ),
                     state.LessonArtifact(
                         step_number=2,
                         sub_topic="Step 2",
                         lesson_type="lesson",
                         content="Lesson 2",
                     ),
                 ],
             ):
            first = self.runner.invoke(main.cli, ["start", "Topic One"])
            second = self.runner.invoke(main.cli, ["start", "Topic Two"])

        self.assertEqual(first.exit_code, 0)
        self.assertEqual(second.exit_code, 0)

        records = state.list_syllabus_records()
        topics = {record.topic for record in records}

        self.assertEqual(topics, {"Topic One", "Topic Two"})
        self.assertEqual(len(records), 2)
        self.assertEqual(state.load_active_syllabus().topic, "Topic Two")
        self.assertEqual(state.load_active_syllabus().cache_status, "complete")

    def test_next_exports_explanation_and_advances_progress(self):
        record = state.initialize_cached_topic(
            "Topic One",
            ["Step 1", "Step 2"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Step 1",
                    lesson_type="lesson",
                    content="**Lesson body**",
                ),
                state.LessonArtifact(
                    step_number=2,
                    sub_topic="Step 2",
                    lesson_type="lesson",
                    content="Second body",
                ),
            ],
        )

        with patch.object(main.LLMManager, "generate_lesson", side_effect=AssertionError("should not call live lesson generation")), \
             patch.object(main.click, "pause", return_value=None):
            result = self.runner.invoke(main.cli, ["next"])

        self.assertEqual(result.exit_code, 0)
        note_content = state.get_note_path("Topic One").read_text(encoding="utf-8")
        self.assertIn('source: "micro-learner"', note_content)
        self.assertIn(f"## Session ", note_content)
        self.assertIn(f"({record.id})", note_content)
        self.assertIn("### Step 1: Step 1", note_content)
        self.assertIn("**Lesson body**", note_content)
        self.assertEqual(state.load_active_syllabus().current_lesson_index, 1)
        self.assertIsNotNone(state.load_lesson_artifact(record.id, 1))

    def test_next_exports_quiz_question_and_answer(self):
        state.initialize_cached_topic(
            "Topic Quiz",
            ["Ownership"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Ownership",
                    lesson_type="quiz",
                    content="What is ownership?\nA. One\nB. Two",
                    answer="B. Two",
                )
            ],
        )

        with patch.object(main.LLMManager, "generate_quiz", side_effect=AssertionError("should not call live quiz generation")), \
             patch.object(main.click, "pause", return_value=None):
            result = self.runner.invoke(main.cli, ["next"])

        self.assertEqual(result.exit_code, 0)
        note_content = state.get_note_path("Topic Quiz").read_text(encoding="utf-8")
        self.assertIn("### Quiz: Step 1: Ownership", note_content)
        self.assertIn("What is ownership?", note_content)
        self.assertIn("### Answer", note_content)
        self.assertIn("B. Two", note_content)
        self.assertEqual(state.load_active_syllabus().current_lesson_index, 1)

    def test_next_does_not_advance_when_note_export_fails(self):
        state.initialize_cached_topic(
            "Topic Failure",
            ["Broken Export"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Broken Export",
                    lesson_type="lesson",
                    content="Body",
                )
            ],
        )

        with patch.object(main.click, "pause", return_value=None), \
             patch.object(main, "append_note_entry", side_effect=OSError("disk full")):
            result = self.runner.invoke(main.cli, ["next"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Failed to export lesson notes", result.output)
        self.assertEqual(state.load_active_syllabus().current_lesson_index, 0)

    def test_start_failure_does_not_leave_active_partial_cache(self):
        with patch.object(main.LLMManager, "generate_syllabus", return_value=["Step 1"]), \
             patch.object(main.LLMManager, "generate_cached_lessons", side_effect=ValueError("boom")):
            result = self.runner.invoke(main.cli, ["start", "Topic Broken"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Failed to initialize cached lessons", result.output)
        self.assertEqual(state.load_state().active_syllabus_id, None)
        self.assertEqual(state.list_syllabus_records(), [])

    def test_next_errors_when_cached_artifact_is_missing(self):
        record = state.initialize_cached_topic(
            "Topic Missing",
            ["Step 1"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Step 1",
                    lesson_type="lesson",
                    content="Body",
                )
            ],
        )
        (state.get_lesson_cache_dir(record.id) / "step-001.json").unlink()

        result = self.runner.invoke(main.cli, ["next"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Failed to load the cached lesson artifact", result.output)
        self.assertEqual(state.load_active_syllabus().current_lesson_index, 0)

    def test_resume_shows_message_when_no_syllabi_exist(self):
        result = self.runner.invoke(main.cli, ["resume"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("No saved syllabi available", result.output)

    def test_resume_activates_selected_in_progress_syllabus(self):
        first = state.initialize_cached_topic(
            "Topic One",
            ["Step 1", "Step 2"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One"),
                state.LessonArtifact(step_number=2, sub_topic="Step 2", lesson_type="lesson", content="Two"),
            ],
        )
        second = state.initialize_cached_topic(
            "Topic Two",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two"),
            ],
        )
        first.current_lesson_index = 1
        state.save_syllabus_record(first)

        result = self.runner.invoke(main.cli, ["resume"], input="2\n")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Resumed topic:", result.output)
        self.assertEqual(state.load_state().active_syllabus_id, first.id)

    def test_resume_activates_completed_syllabus(self):
        record = state.initialize_cached_topic(
            "Finished Topic",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Done"),
            ],
        )
        record.current_lesson_index = 1
        state.save_syllabus_record(record)

        result = self.runner.invoke(main.cli, ["resume"], input="1\n")

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(state.load_state().active_syllabus_id, record.id)
        self.assertIn("Completed", result.output)

    def test_resume_start_new_topic_option_does_not_change_active_state(self):
        record = state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One"),
            ],
        )

        result = self.runner.invoke(main.cli, ["resume"], input="2\n")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("micro-learner start <topic>", result.output)
        self.assertEqual(state.load_state().active_syllabus_id, record.id)

    def test_resume_rejects_incomplete_syllabus(self):
        good = state.initialize_cached_topic(
            "Good Topic",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One"),
            ],
        )
        bad = state.create_syllabus_record("Broken Topic", ["Step 1"])
        state.activate_syllabus(good.id)

        result = self.runner.invoke(main.cli, ["resume"], input="1\n")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("cannot be resumed", result.output)
        self.assertEqual(state.load_state().active_syllabus_id, good.id)
        self.assertEqual(bad.cache_status, "pending")

    def test_resume_reprompts_on_invalid_selection(self):
        first = state.initialize_cached_topic(
            "Topic One",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="One"),
            ],
        )
        second = state.initialize_cached_topic(
            "Topic Two",
            ["Step 1"],
            [
                state.LessonArtifact(step_number=1, sub_topic="Step 1", lesson_type="lesson", content="Two"),
            ],
        )

        result = self.runner.invoke(main.cli, ["resume"], input="99\n1\n")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("is not in the range", result.output)
        self.assertEqual(state.load_state().active_syllabus_id, second.id)


if __name__ == "__main__":
    unittest.main()
