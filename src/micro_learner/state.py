import json
import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List

APP_DIR = Path.home() / ".micro_learner"
SYLLABI_DIR = APP_DIR / "syllabi"
NOTES_DIR = APP_DIR / "notes"
STATE_FILE = APP_DIR / "state.json"

class AppState(BaseModel):
    active_topic: Optional[str] = None
    current_lesson_index: int = 0
    total_lessons: int = 0
    syllabus: List[str] = Field(default_factory=list)

def bootstrap():
    """Initializes the ~/.micro_learner directory structure."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SYLLABI_DIR.mkdir(exist_ok=True)
    NOTES_DIR.mkdir(exist_ok=True)

    if not STATE_FILE.exists():
        initial_state = AppState()
        save_state(initial_state)

def load_state() -> AppState:
    """Loads the current state from the JSON file."""
    if not STATE_FILE.exists():
        return AppState()
    
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        return AppState(**data)

def save_state(state: AppState):
    """Saves the current state to the JSON file."""
    with open(STATE_FILE, "w") as f:
        f.write(state.model_dump_json(indent=4))

def initialize_topic(topic: str, syllabus: List[str]):
    """Resets the state with a new topic and syllabus."""
    new_state = AppState(
        active_topic=topic,
        current_lesson_index=0,
        total_lessons=len(syllabus),
        syllabus=syllabus
    )
    save_state(new_state)
