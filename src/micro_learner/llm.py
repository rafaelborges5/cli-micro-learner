import asyncio
import json
import math
import random
import re
from typing import Callable, List, Optional
from copilot import CopilotClient
from copilot.session import PermissionHandler
from pydantic import ValidationError
from micro_learner.state import LessonArtifact, SyllabusStep
from micro_learner.ui import console


def choose_lesson_type(step_number: int, total_lessons: int) -> str:
    """Chooses whether a generated step should be an explanation lesson or quiz."""
    warmup_boundary = max(1, math.ceil(total_lessons / 3))
    if step_number <= warmup_boundary:
        return "lesson"
    return "quiz" if random.random() < 0.3 else "lesson"


class LLMManager:
    """Session-based LLM client; reuses a single Copilot session across a batch to reduce cold-start latency."""

    def __init__(self, model: str = "gpt-5.3-codex"):
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

    async def generate_syllabus(self, topic: str, brief: str) -> List[SyllabusStep]:
        """Generates a 15-step syllabus from a topic and long-form learning brief."""
        system_prompt = (
            "You are a master educator. Your task is to generate a progressive, 15-step syllabus for a topic, "
            "using the user's long-form learning brief as the source of truth for scope, depth, constraints, and emphasis. "
            "The syllabus should start from foundational context and move toward advanced mastery. "
            "Return ONLY a JSON array of objects. Each object must have exactly two string fields: "
            "'title' for a concise lesson title, and 'brief' for the specific teaching brief that lesson should follow. "
            "Every title and brief must be non-empty. "
            "Do not include any conversational text, headers, or markdown code blocks."
        )
        
        prompt = f"Topic: {topic}\n\nUser learning brief:\n{brief}"
        
        raw_response = await self.get_response(prompt, system_prompt)
        
        # Clean the response in case the LLM included markdown code blocks
        clean_json = re.sub(r"```json|```", "", raw_response).strip()
        
        try:
            syllabus_data = json.loads(clean_json)
            if not isinstance(syllabus_data, list) or len(syllabus_data) == 0:
                raise ValueError("Response was not a valid non-empty list.")

            syllabus = [SyllabusStep(**step) for step in syllabus_data]
            if any(not step.title.strip() or not step.brief.strip() for step in syllabus):
                raise ValueError("Every syllabus step must include a non-empty title and brief.")
            return syllabus
        except (json.JSONDecodeError, ValueError, ValidationError) as e:
            console.print(f"[error]Failed to parse syllabus: {e}[/error]")
            console.print(f"[warning]Raw response was: {raw_response}[/warning]")
            return []

    async def generate_lesson(self, topic: str, sub_topic: str) -> str:
        """Generates a micro-lesson for a specific sub-topic."""
        system_prompt = (
            "You are a master educator. Explain the provided sub-topic within the broader context of the main topic. "
            "Keep the explanation concise (approximately 200 words), high-impact, and clear. "
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

    async def generate_analogy(self, topic: str, subtopic: str, lesson_content: str) -> str:
        """Generates a simple analogy for the given lesson content."""
        system_prompt = (
            "You are a master educator. The user is stuck on a concept. "
            "Explain the provided sub-topic using a simpler, everyday analogy. "
            "Keep the explanation concise (approximately 100 words), high-impact, and clear. "
            "Use Markdown for formatting."
        )
        prompt = f"Main Topic: {topic}\nSub-Topic: {subtopic}\nOriginal Lesson:\n{lesson_content}"
        return await self.get_response(prompt, system_prompt)

    async def generate_code_example(self, topic: str, subtopic: str, lesson_content: str) -> str:
        """Generates a concrete code example for the given lesson content."""
        system_prompt = (
            "You are a master educator. The user is stuck on a concept. "
            "Provide a concrete, minimal code snippet demonstrating the provided sub-topic. "
            "Keep the explanation very brief and focus on the code. "
            "Use Markdown for formatting, including appropriate language tags for code blocks."
        )
        prompt = f"Main Topic: {topic}\nSub-Topic: {subtopic}\nOriginal Lesson:\n{lesson_content}"
        return await self.get_response(prompt, system_prompt)

    async def generate_answer(
        self,
        topic: str,
        sub_topic: str,
        lesson_content: str,
        question: str,
    ) -> str:
        """Answers a student's ad-hoc question using the current lesson as context."""
        system_prompt = (
            "You are a patient tutor. The student has a question about the lesson they just read. "
            "Answer thoroughly (6-8 sentences). Stay focused on the lesson context. "
            "Use Markdown for formatting."
        )
        prompt = (
            f"Main Topic: {topic}\nSub-Topic: {sub_topic}\n"
            f"Lesson Content:\n{lesson_content}\n\n"
            f"Student question: {question}"
        )
        return await self.get_response(prompt, system_prompt)

    async def derive_topic_from_brief(self, brief: str) -> str:
        """Derives a short topic title from a long-form learning brief."""
        system_prompt = (
            "You are a curriculum designer. Given a learning brief, output a concise topic title. "
            "3 to 7 words, no punctuation, no quotes. Return only the title."
        )
        return (await self.get_response(brief, system_prompt)).strip()

    async def generate_cached_lessons(
        self,
        topic: str,
        syllabus: List[SyllabusStep],
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        artifact_callback: Optional[Callable[[LessonArtifact], None]] = None,
        start_step: int = 1,
    ) -> List[LessonArtifact]:
        """Pre-generates lesson artifacts for a syllabus subset."""
        artifacts: List[LessonArtifact] = []
        total_steps = len(syllabus)
        full_total_lessons = max(total_steps, start_step + total_steps - 1)

        async with CopilotClient() as client:
            async with await client.create_session(
                model=self.model,
                on_permission_request=PermissionHandler.approve_all
            ) as session:
                session.on(self._on_session_event)
                for i, step in enumerate(syllabus):
                    step_number = start_step + i
                    sub_topic = step.title
                    lesson_brief = step.brief
                    lesson_type = choose_lesson_type(step_number, full_total_lessons)
                    if progress_callback:
                        progress_callback(i, total_steps, sub_topic, lesson_type)

                    if lesson_type == "quiz":
                        raw_quiz = await self._send_with_session(
                            session,
                            f"Main Topic: {topic}\nLesson Title: {sub_topic}\nLesson Brief:\n{lesson_brief}",
                            (
                                "You are a master educator. Create a challenging micro-quiz for the provided lesson brief within the broader main topic. "
                                "The quiz should test understanding, not just recall. "
                                "Format: 1 Question followed by 3-4 multiple choice options. "
                                "At the very end, write the correct answer and a one-sentence explanation of why it is correct, prefixed with 'ANSWER: '. "
                                "Example: 'ANSWER: B — This is correct because...' "
                                "Do not use conversational filler."
                            ),
                        )
                        if not raw_quiz:
                            raise ValueError(f"Failed to generate cached quiz for step {step_number}.")

                        if "ANSWER:" in raw_quiz:
                            question_part, answer_part = raw_quiz.rsplit("ANSWER:", 1)
                        else:
                            question_part, answer_part = raw_quiz, "No answer key provided."

                        artifact = LessonArtifact(
                            step_number=step_number,
                            sub_topic=sub_topic,
                            lesson_type="quiz",
                            content=question_part.strip(),
                            answer=answer_part.strip(),
                        )
                        artifacts.append(artifact)
                        if artifact_callback:
                            artifact_callback(artifact)
                    else:
                        lesson_text = await self._send_with_session(
                            session,
                            f"Main Topic: {topic}\nLesson Title: {sub_topic}\nLesson Brief:\n{lesson_brief}",
                            (
                                "You are a master educator. Explain the provided lesson brief within the broader context of the main topic. "
                                "Keep the explanation concise (approximately 200 words), high-impact, and clear. "
                                "Use Markdown for formatting (bold, code blocks, lists). "
                                "Do not use conversational filler like 'Sure!' or 'Here is your lesson'."
                            ),
                        )
                        if not lesson_text:
                            raise ValueError(f"Failed to generate cached lesson for step {step_number}.")

                        artifact = LessonArtifact(
                            step_number=step_number,
                            sub_topic=sub_topic,
                            lesson_type="lesson",
                            content=lesson_text.strip(),
                        )
                        artifacts.append(artifact)
                        if artifact_callback:
                            artifact_callback(artifact)

                    if progress_callback:
                        progress_callback(i + 1, total_steps, sub_topic, lesson_type)

        return artifacts
