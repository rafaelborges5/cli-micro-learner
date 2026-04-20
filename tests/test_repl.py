import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from micro_learner import repl, state


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

    def test_shell_initializes_just_finished_lesson_flag(self):
        shell = repl.REPLShell()
        self.assertFalse(shell.just_finished_lesson)

    async def test_next_marks_just_finished_lesson_flag(self):
        shell = repl.REPLShell()

        with patch.object(repl, "execute_next", AsyncMock()) as execute_next_mock:
            await shell.cmd_next()

        execute_next_mock.assert_awaited_once()
        self.assertTrue(shell.just_finished_lesson)


if __name__ == "__main__":
    unittest.main()
