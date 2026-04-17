import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from micro_learner import main, state


def configure_state_paths(base_dir: Path):
    state.APP_DIR = base_dir / ".micro_learner"
    state.SYLLABI_DIR = state.APP_DIR / "syllabi"
    state.LESSONS_DIR = state.APP_DIR / "lessons"
    state.NOTES_DIR = state.APP_DIR / "notes"
    state.STATE_FILE = state.APP_DIR / "state.json"


class InterventionsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        configure_state_paths(Path(self.temp_dir.name))
        state.bootstrap()
        self.runner = CliRunner()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_next_with_interventions_captures_and_exports_them(self):
        # 1. Setup a cached topic
        topic = "Intervention Topic"
        record = state.initialize_cached_topic(
            topic,
            ["Step 1"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Step 1",
                    lesson_type="lesson",
                    content="Original lesson content",
                )
            ],
        )

        # 2. Mock getchar to simulate: 'e' (Analogy), 'd' (Code), then '\n' (Continue)
        # Note: click.getchar() returns the character.
        getchar_mock = MagicMock(side_effect=['e', 'd', '\n'])

        # 3. Mock LLMManager methods
        with patch.object(main, 'LLMManager') as MockLLM:
            mock_llm_instance = MockLLM.return_value
            
            async def mock_gen_analogy(*args, **kwargs):
                return "This is a simple analogy."
            async def mock_gen_code(*args, **kwargs):
                return "```python\nprint('hello')\n```"
            
            mock_llm_instance.generate_analogy = mock_gen_analogy
            mock_llm_instance.generate_code_example = mock_gen_code

            with patch('click.getchar', getchar_mock):
                # We also need to patch time.sleep to speed up tests
                with patch('time.sleep', return_value=None):
                    result = self.runner.invoke(main.cli, ["next"])

        # 4. Verify results
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Simpler Analogy", result.output)
        self.assertIn("This is a simple analogy.", result.output)
        self.assertIn("Code Example", result.output)
        # We check for the content without worrying about ANSI colors
        self.assertIn("print", result.output)
        self.assertIn("hello", result.output)

        # 5. Verify the markdown file contains the interventions
        note_path = state.get_note_path(topic)
        self.assertTrue(note_path.exists())
        note_content = note_path.read_text(encoding="utf-8")
        
        self.assertIn("### 💡 Simpler Analogy", note_content)
        self.assertIn("This is a simple analogy.", note_content)
        self.assertIn("### 💻 Code Example", note_content)
        self.assertIn("print('hello')", note_content)

    def test_quiz_with_interventions_before_and_after_reveal(self):
        # Setup a quiz
        topic = "Quiz Topic"
        state.initialize_cached_topic(
            topic,
            ["Ownership"],
            [
                state.LessonArtifact(
                    step_number=1,
                    sub_topic="Ownership",
                    lesson_type="quiz",
                    content="What is ownership?",
                    answer="It is a Rust concept.",
                )
            ],
        )

        # Simulate: 
        # Before reveal: 'e' (Analogy), then ' ' (Reveal)
        # After reveal: 'd' (Code), then '\n' (Complete)
        getchar_mock = MagicMock(side_effect=['e', ' ', 'd', '\n'])

        with patch.object(main, 'LLMManager') as MockLLM:
            mock_llm_instance = MockLLM.return_value
            async def mock_gen_analogy(*args, **kwargs):
                return "Analogy before reveal."
            async def mock_gen_code(*args, **kwargs):
                return "Code after reveal."
            
            mock_llm_instance.generate_analogy = mock_gen_analogy
            mock_llm_instance.generate_code_example = mock_gen_code

            with patch('click.getchar', getchar_mock), patch('time.sleep', return_value=None):
                result = self.runner.invoke(main.cli, ["next"])

        self.assertEqual(result.exit_code, 0)
        
        note_path = state.get_note_path(topic)
        note_content = note_path.read_text(encoding="utf-8")
        
        self.assertIn("### 💡 Simpler Analogy", note_content)
        self.assertIn("Analogy before reveal.", note_content)
        self.assertIn("### 💻 Code Example", note_content)
        self.assertIn("Code after reveal.", note_content)


if __name__ == "__main__":
    unittest.main()
