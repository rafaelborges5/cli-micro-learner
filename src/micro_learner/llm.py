import asyncio
import json
import random
import re
from typing import Callable, List, Optional
from copilot import CopilotClient
from copilot.session import PermissionHandler
from micro_learner.state import LessonArtifact
from micro_learner.ui import console

class LLMManager:
    def __init__(self, model: str = "gpt-4.1"):
        self.model = model
        self._session_request = None

    async def _send_with_session(self, session, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends one prompt over an existing Copilot session."""
        self._session_request = {
            "full_response": [],
            "done": asyncio.Event(),
        }
        combined_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        await session.send(combined_prompt)

        try:
            await asyncio.wait_for(self._session_request["done"].wait(), timeout=60)
        except asyncio.TimeoutError:
            console.print("[error]LLM request timed out.[/error]")

        result = "".join(self._session_request["full_response"])
        self._session_request = None
        return result

    async def get_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends a prompt to GitHub Copilot and returns the combined response text."""
        async with CopilotClient() as client:
            async with await client.create_session(
                model=self.model,
                on_permission_request=PermissionHandler.approve_all
            ) as session:
                session.on(self._on_session_event)
                return await self._send_with_session(session, prompt, system_prompt)

    def _on_session_event(self, event):
        """Routes Copilot session events to the active request collector."""
        if self._session_request is None:
            return
        if event.type.value == "assistant.message":
            self._session_request["full_response"].append(event.data.content)
        elif event.type.value == "session.idle":
            self._session_request["done"].set()
        elif event.type.value == "error":
            console.print(f"[error]Copilot Error: {event.data.message}[/error]")
            self._session_request["done"].set()

    async def generate_syllabus(self, topic: str) -> List[str]:
        """Generates a 15-step syllabus for the given topic."""
        system_prompt = (
            "You are a master educator. Your task is to generate a progressive, 15-step syllabus for a given topic. "
            "The syllabus should start from foundational concepts and move to advanced mastery. "
            "Return ONLY a JSON array of strings, where each string is a concise title for a lesson. "
            "Do not include any conversational text, headers, or markdown code blocks."
        )
        
        prompt = f"Topic: {topic}"
        
        raw_response = await self.get_response(prompt, system_prompt)
        
        # Clean the response in case the LLM included markdown code blocks
        clean_json = re.sub(r"```json|```", "", raw_response).strip()
        
        try:
            syllabus = json.loads(clean_json)
            if isinstance(syllabus, list) and len(syllabus) > 0:
                return syllabus
            else:
                raise ValueError("Response was not a valid non-empty list.")
        except (json.JSONDecodeError, ValueError) as e:
            console.print(f"[error]Failed to parse syllabus: {e}[/error]")
            console.print(f"[warning]Raw response was: {raw_response}[/warning]")
            return []

    async def generate_lesson(self, topic: str, sub_topic: str) -> str:
        """Generates a micro-lesson for a specific sub-topic."""
        system_prompt = (
            "You are a master educator. Explain the provided sub-topic within the broader context of the main topic. "
            "Keep the explanation concise (approximately 150 words), high-impact, and clear. "
            "Use Markdown for formatting (bold, code blocks, lists). "
            "Do not use conversational filler like 'Sure!' or 'Here is your lesson'."
        )
        
        prompt = f"Main Topic: {topic}\nSub-Topic: {sub_topic}"
        
        return await self.get_response(prompt, system_prompt)

    async def generate_quiz(self, topic: str, sub_topic: str) -> str:
        """Generates a micro-quiz for a specific sub-topic."""
        system_prompt = (
            "You are a master educator. Create a challenging micro-quiz for the provided sub-topic within the broader main topic. "
            "The quiz should test understanding, not just recall. "
            "Format: 1 Question followed by 3-4 multiple choice options. "
            "At the very end, include the correct answer prefixed with 'ANSWER: '. "
            "Do not use conversational filler."
        )
        
        prompt = f"Main Topic: {topic}\nSub-Topic: {sub_topic}"
        
        return await self.get_response(prompt, system_prompt)

    async def generate_cached_lessons(
        self,
        topic: str,
        syllabus: List[str],
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    ) -> List[LessonArtifact]:
        """Pre-generates all lesson artifacts for a syllabus."""
        artifacts: List[LessonArtifact] = []
        total_steps = len(syllabus)

        async with CopilotClient() as client:
            async with await client.create_session(
                model=self.model,
                on_permission_request=PermissionHandler.approve_all
            ) as session:
                session.on(self._on_session_event)
                for step_number, sub_topic in enumerate(syllabus, start=1):
                    lesson_type = "quiz" if random.random() < 0.3 else "lesson"
                    if progress_callback:
                        progress_callback(step_number - 1, total_steps, sub_topic, lesson_type)

                    if lesson_type == "quiz":
                        raw_quiz = await self._send_with_session(
                            session,
                            f"Main Topic: {topic}\nSub-Topic: {sub_topic}",
                            (
                                "You are a master educator. Create a challenging micro-quiz for the provided sub-topic within the broader main topic. "
                                "The quiz should test understanding, not just recall. "
                                "Format: 1 Question followed by 3-4 multiple choice options. "
                                "At the very end, include the correct answer prefixed with 'ANSWER: '. "
                                "Do not use conversational filler."
                            ),
                        )
                        if not raw_quiz:
                            raise ValueError(f"Failed to generate cached quiz for step {step_number}.")

                        if "ANSWER:" in raw_quiz:
                            question_part, answer_part = raw_quiz.rsplit("ANSWER:", 1)
                        else:
                            question_part, answer_part = raw_quiz, "No answer key provided."

                        artifacts.append(
                            LessonArtifact(
                                step_number=step_number,
                                sub_topic=sub_topic,
                                lesson_type="quiz",
                                content=question_part.strip(),
                                answer=answer_part.strip(),
                            )
                        )
                    else:
                        lesson_text = await self._send_with_session(
                            session,
                            f"Main Topic: {topic}\nSub-Topic: {sub_topic}",
                            (
                                "You are a master educator. Explain the provided sub-topic within the broader context of the main topic. "
                                "Keep the explanation concise (approximately 150 words), high-impact, and clear. "
                                "Use Markdown for formatting (bold, code blocks, lists). "
                                "Do not use conversational filler like 'Sure!' or 'Here is your lesson'."
                            ),
                        )
                        if not lesson_text:
                            raise ValueError(f"Failed to generate cached lesson for step {step_number}.")

                        artifacts.append(
                            LessonArtifact(
                                step_number=step_number,
                                sub_topic=sub_topic,
                                lesson_type="lesson",
                                content=lesson_text.strip(),
                            )
                        )

                    if progress_callback:
                        progress_callback(step_number, total_steps, sub_topic, lesson_type)

        return artifacts
