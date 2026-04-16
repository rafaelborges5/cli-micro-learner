import asyncio
import json
import re
from typing import List, Optional
from copilot import CopilotClient
from copilot.session import PermissionHandler
from micro_learner.ui import console

class LLMManager:
    def __init__(self, model: str = "gpt-4.1"):
        self.model = model

    async def get_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends a prompt to GitHub Copilot and returns the combined response text."""
        full_response = []
        
        async with CopilotClient() as client:
            # Create a session with the specified model and auto-approve permissions
            async with await client.create_session(
                model=self.model,
                on_permission_request=PermissionHandler.approve_all
            ) as session:
                
                done = asyncio.Event()
                
                def on_event(event):
                    if event.type.value == "assistant.message":
                        content = event.data.content
                        full_response.append(content)
                    elif event.type.value == "session.idle":
                        done.set()
                    elif event.type.value == "error":
                        console.print(f"[error]Copilot Error: {event.data.message}[/error]")
                        done.set()

                session.on(on_event)

                combined_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                
                await session.send(combined_prompt)
                
                # Wait for response with a longer timeout and ensure we don't return too early
                try:
                    await asyncio.wait_for(done.wait(), timeout=60)
                except asyncio.TimeoutError:
                    console.print("[error]LLM request timed out.[/error]")
                
        result = "".join(full_response)
        return result

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
