import unittest
from unittest.mock import AsyncMock, patch

from micro_learner import state
from micro_learner.llm import LLMManager, choose_lesson_type


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    def on(self, callback):
        return None


class FakeCopilotClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def create_session(self, **kwargs):
        return FakeSession()


def syllabus_steps(*titles: str):
    return [state.SyllabusStep(title=title, brief=f"{title} brief") for title in titles]


class LLMManagerTests(unittest.IsolatedAsyncioTestCase):
    def test_choose_lesson_type_forces_first_step_to_lesson(self):
        with patch("micro_learner.llm.random.random", return_value=0.0) as random_mock:
            lesson_type = choose_lesson_type(1, 15)

        self.assertEqual(lesson_type, "lesson")
        random_mock.assert_not_called()

    def test_choose_lesson_type_forces_first_third_boundary_to_lesson(self):
        with patch("micro_learner.llm.random.random", return_value=0.0) as random_mock:
            lesson_type = choose_lesson_type(5, 15)

        self.assertEqual(lesson_type, "lesson")
        random_mock.assert_not_called()

    def test_choose_lesson_type_allows_quiz_after_warmup(self):
        with patch("micro_learner.llm.random.random", return_value=0.0):
            lesson_type = choose_lesson_type(6, 15)

        self.assertEqual(lesson_type, "quiz")

    def test_choose_lesson_type_forces_first_small_syllabus_step_to_lesson(self):
        with patch("micro_learner.llm.random.random", return_value=0.0) as random_mock:
            lesson_type = choose_lesson_type(1, 2)

        self.assertEqual(lesson_type, "lesson")
        random_mock.assert_not_called()

    async def test_generate_syllabus_parses_structured_steps(self):
        manager = LLMManager()
        raw_response = """
        ```json
        [
          {"title": "Associated Types", "brief": "Teach associated types with Iterator examples."},
          {"title": "Object Safety", "brief": "Explain object safety rules and tradeoffs."}
        ]
        ```
        """

        with patch.object(manager, "get_response", return_value=raw_response) as get_response_mock:
            syllabus = await manager.generate_syllabus("Advanced Rust Traits", "Focus on real library patterns.")

        self.assertEqual(len(syllabus), 2)
        self.assertEqual(syllabus[0].title, "Associated Types")
        self.assertEqual(syllabus[0].brief, "Teach associated types with Iterator examples.")
        get_response_mock.assert_awaited_once()

    async def test_generate_syllabus_rejects_missing_brief(self):
        manager = LLMManager()
        raw_response = '[{"title": "Associated Types"}]'

        with patch.object(manager, "get_response", return_value=raw_response):
            syllabus = await manager.generate_syllabus("Advanced Rust Traits", "Focus on real library patterns.")

        self.assertEqual(syllabus, [])

    async def test_generate_syllabus_rejects_empty_step_fields(self):
        manager = LLMManager()
        raw_response = '[{"title": "Associated Types", "brief": "   "}]'

        with patch.object(manager, "get_response", return_value=raw_response):
            syllabus = await manager.generate_syllabus("Advanced Rust Traits", "Focus on real library patterns.")

        self.assertEqual(syllabus, [])

    async def test_generate_cached_lessons_forces_warmup_step_to_lesson(self):
        manager = LLMManager()
        progress_events = []

        with patch("micro_learner.llm.CopilotClient", FakeCopilotClient), \
             patch("micro_learner.llm.random.random", return_value=0.0) as random_mock, \
             patch.object(manager, "_send_with_session", new=AsyncMock(return_value="Lesson body")):
            artifacts = await manager.generate_cached_lessons(
                "Advanced Rust Traits",
                syllabus_steps("Step 1"),
                progress_callback=lambda *args: progress_events.append(args),
            )

        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].lesson_type, "lesson")
        self.assertEqual(artifacts[0].content, "Lesson body")
        self.assertEqual(progress_events[0], (0, 1, "Step 1", "lesson"))
        self.assertEqual(progress_events[1], (1, 1, "Step 1", "lesson"))
        random_mock.assert_not_called()

    async def test_generate_cached_lessons_uses_full_position_for_background_warmup(self):
        manager = LLMManager()
        remainder = syllabus_steps(*(f"Step {number}" for number in range(2, 16)))

        with patch("micro_learner.llm.CopilotClient", FakeCopilotClient), \
             patch("micro_learner.llm.random.random", return_value=0.0), \
             patch.object(manager, "_send_with_session", new=AsyncMock(return_value="Generated body")):
            artifacts = await manager.generate_cached_lessons(
                "Advanced Rust Traits",
                remainder,
                start_step=2,
            )

        self.assertEqual([artifact.step_number for artifact in artifacts[:4]], [2, 3, 4, 5])
        self.assertEqual([artifact.lesson_type for artifact in artifacts[:4]], ["lesson"] * 4)
        self.assertEqual(artifacts[4].step_number, 6)
        self.assertEqual(artifacts[4].lesson_type, "quiz")

    async def test_generate_cached_lessons_can_generate_quiz_after_warmup(self):
        manager = LLMManager()

        with patch("micro_learner.llm.CopilotClient", FakeCopilotClient), \
             patch("micro_learner.llm.random.random", return_value=0.0), \
             patch.object(
                 manager,
                 "_send_with_session",
                 new=AsyncMock(return_value="Question?\nA. One\nB. Two\nANSWER: B - Two is correct."),
             ):
            artifacts = await manager.generate_cached_lessons(
                "Advanced Rust Traits",
                syllabus_steps("Step 6"),
                start_step=6,
            )

        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].step_number, 6)
        self.assertEqual(artifacts[0].lesson_type, "quiz")
        self.assertEqual(artifacts[0].content, "Question?\nA. One\nB. Two")
        self.assertEqual(artifacts[0].answer, "B - Two is correct.")


if __name__ == "__main__":
    unittest.main()
