import json
import tempfile
import unittest
from pathlib import Path

from micro_learner import state


def configure_state_paths(base_dir: Path):
    state.APP_DIR = base_dir / ".micro_learner"
    state.SYLLABI_DIR = state.APP_DIR / "syllabi"
    state.LESSONS_DIR = state.APP_DIR / "lessons"
    state.NOTES_DIR = state.APP_DIR / "notes"
    state.STATE_FILE = state.APP_DIR / "state.json"
    state.SETTINGS_FILE = state.APP_DIR / "settings.json"


class StatePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        configure_state_paths(Path(self.temp_dir.name))
        state.bootstrap()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bootstrap_creates_global_state_and_directories(self):
        self.assertTrue(state.APP_DIR.exists())
        self.assertTrue(state.SYLLABI_DIR.exists())
        self.assertTrue(state.LESSONS_DIR.exists())
        self.assertTrue(state.NOTES_DIR.exists())
        self.assertTrue(state.STATE_FILE.exists())
        self.assertTrue(state.SETTINGS_FILE.exists())
        self.assertEqual(state.load_state().active_syllabus_id, None)
        self.assertEqual(state.load_settings().theme_name, "Modern")

    def test_initialize_cached_topic_creates_record_cache_and_active_pointer(self):
        record = state.initialize_cached_topic(
            "Advanced Rust Traits",
            ["Associated Types", "GATs"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Associated Types",
                    lesson_type="lesson",
                    content="Lesson 1",
                ),
                state.LessonArtifact(
                    step_number=2,
                    sub_topic="GATs",
                    lesson_type="quiz",
                    content="Question",
                    answer="Answer",
                ),
            ],
        )

        loaded_state = state.load_state()
        self.assertEqual(loaded_state.active_syllabus_id, record.id)

        loaded_record = state.load_active_syllabus()
        self.assertIsNotNone(loaded_record)
        self.assertEqual(loaded_record.topic, "Advanced Rust Traits")
        self.assertEqual(loaded_record.total_lessons, 2)
        self.assertEqual(loaded_record.current_lesson_index, 0)
        self.assertEqual(loaded_record.cache_status, "complete")
        self.assertTrue((state.SYLLABI_DIR / f"{record.id}.json").exists())
        self.assertTrue((state.get_lesson_cache_dir(record.id) / "step-001.json").exists())

    def test_new_topic_does_not_overwrite_previous_syllabus(self):
        first = state.initialize_cached_topic(
            "Python Typing",
            ["Basics"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Basics",
                    lesson_type="lesson",
                    content="First lesson",
                )
            ],
        )
        second = state.initialize_cached_topic(
            "Rust Ownership",
            ["Borrowing"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Borrowing",
                    lesson_type="lesson",
                    content="Second lesson",
                )
            ],
        )

        records = state.list_syllabus_records()
        record_ids = {record.id for record in records}

        self.assertEqual(state.load_state().active_syllabus_id, second.id)
        self.assertIn(first.id, record_ids)
        self.assertIn(second.id, record_ids)
        self.assertEqual(len(records), 2)

    def test_bootstrap_resets_legacy_state_format_to_fresh_global_state(self):
        state.STATE_FILE.write_text(
            json.dumps(
                {
                    "active_topic": "Legacy Topic",
                    "current_lesson_index": 3,
                    "total_lessons": 5,
                    "syllabus": ["One", "Two"],
                }
            ),
            encoding="utf-8",
        )

        state.bootstrap()

        self.assertEqual(state.load_state().active_syllabus_id, None)

    def test_load_settings_returns_saved_theme(self):
        state.save_settings(state.AppSettings(theme_name="Matrix"))

        loaded = state.load_settings()

        self.assertEqual(loaded.theme_name, "Matrix")

    def test_bootstrap_resets_invalid_settings_format_to_default(self):
        state.SETTINGS_FILE.write_text(json.dumps({"theme": "broken"}), encoding="utf-8")

        state.bootstrap()

        self.assertEqual(state.load_settings().theme_name, "Modern")

    def test_get_note_path_slugifies_topic_name(self):
        path = state.get_note_path("Advanced Rust Traits!!!")
        self.assertEqual(path.name, "advanced-rust-traits.md")

    def test_append_note_entry_reuses_same_topic_file(self):
        first = state.NoteEntry(
            syllabus_id="session-one",
            lesson_type="lesson",
            topic="Python Typing",
            sub_topic="Annotations",
            step_number=1,
            total_lessons=2,
            completed_at="2026-04-16T10:00:00+00:00",
            content="First body",
        )
        second = state.NoteEntry(
            syllabus_id="session-one",
            lesson_type="lesson",
            topic="Python Typing",
            sub_topic="Protocols",
            step_number=2,
            total_lessons=2,
            completed_at="2026-04-16T11:00:00+00:00",
            content="Second body",
        )

        first_path = state.append_note_entry(first)
        second_path = state.append_note_entry(second)

        self.assertEqual(first_path, second_path)
        content = first_path.read_text(encoding="utf-8")
        self.assertIn("---", content)
        self.assertIn('source: "micro-learner"', content)
        self.assertIn("## Session 2026-04-16 10:00 UTC (session-one)", content)
        self.assertIn("### Step 1: Annotations", content)
        self.assertIn("### Step 2: Protocols", content)
        self.assertIn("First body", content)
        self.assertIn("Second body", content)

    def test_load_lesson_artifact_returns_cached_step(self):
        record = state.initialize_cached_topic(
            "Topic Cache",
            ["Step 1"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Step 1",
                    lesson_type="quiz",
                    content="Question",
                    answer="Answer",
                )
            ],
        )

        artifact = state.load_lesson_artifact(record.id, 1)

        self.assertIsNotNone(artifact)
        self.assertEqual(artifact.lesson_type, "quiz")
        self.assertEqual(artifact.answer, "Answer")

    def test_append_note_entry_creates_new_session_for_new_syllabus(self):
        first = state.NoteEntry(
            syllabus_id="session-one",
            lesson_type="lesson",
            topic="Systems Design",
            sub_topic="Caching",
            step_number=1,
            total_lessons=2,
            completed_at="2026-04-16T10:00:00+00:00",
            content="First session",
        )
        second = state.NoteEntry(
            syllabus_id="session-two",
            lesson_type="lesson",
            topic="Systems Design",
            sub_topic="Queues",
            step_number=1,
            total_lessons=2,
            completed_at="2026-04-17T10:00:00+00:00",
            content="Second session",
        )

        state.append_note_entry(first)
        path = state.append_note_entry(second)
        content = path.read_text(encoding="utf-8")

        self.assertIn("## Session 2026-04-16 10:00 UTC (session-one)", content)
        self.assertIn("## Session 2026-04-17 10:00 UTC (session-two)", content)

    def test_append_note_entry_upgrades_legacy_flat_file_in_place(self):
        path = state.get_note_path("Legacy Topic")
        path.write_text("## Step 1: Old Lesson\n\nLegacy body\n", encoding="utf-8")

        state.append_note_entry(
            state.NoteEntry(
                syllabus_id="session-new",
                lesson_type="lesson",
                topic="Legacy Topic",
                sub_topic="New Lesson",
                step_number=2,
                total_lessons=3,
                completed_at="2026-04-18T12:00:00+00:00",
                content="Fresh body",
            )
        )

        content = path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("## Legacy Notes", content)
        self.assertIn("Legacy body", content)
        self.assertIn("## Session 2026-04-18 12:00 UTC (session-new)", content)
        self.assertIn("### Step 2: New Lesson", content)


if __name__ == "__main__":
    unittest.main()
