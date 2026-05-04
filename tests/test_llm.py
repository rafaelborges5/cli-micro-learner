import unittest
from unittest.mock import patch

from micro_learner.llm import LLMManager


class LLMManagerTests(unittest.IsolatedAsyncioTestCase):
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


if __name__ == "__main__":
    unittest.main()
