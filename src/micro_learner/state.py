import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

APP_DIR = Path.home() / ".micro_learner"
SYLLABI_DIR = APP_DIR / "syllabi"
LESSONS_DIR = APP_DIR / "lessons"
NOTES_DIR = APP_DIR / "notes"
STATE_FILE = APP_DIR / "state.json"


class GlobalState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active_syllabus_id: Optional[str] = None


class SyllabusRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    topic: str
    created_at: str
    updated_at: str
    current_lesson_index: int = 0
    total_lessons: int
    cache_status: str = "pending"
    syllabus: List[str] = Field(default_factory=list)


class LessonArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_number: int
    sub_topic: str
    lesson_type: str
    content: str
    answer: Optional[str] = None


class NoteEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    syllabus_id: str
    lesson_type: str
    topic: str
    sub_topic: str
    step_number: int
    total_lessons: int
    completed_at: str
    content: str
    answer: Optional[str] = None
    interventions: List[dict] = Field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify_topic(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return slug or "topic"


def _syllabus_path(record_id: str) -> Path:
    return SYLLABI_DIR / f"{record_id}.json"


def _lesson_dir(record_id: str) -> Path:
    return LESSONS_DIR / record_id


def _lesson_path(record_id: str, step_number: int) -> Path:
    return _lesson_dir(record_id) / f"step-{step_number:03d}.json"


def _note_path(topic: str) -> Path:
    return NOTES_DIR / f"{_slugify_topic(topic)}.md"


def _topic_tag(topic: str) -> str:
    slug = _slugify_topic(topic)
    return f"topic/{slug}"


def _new_global_state() -> GlobalState:
    return GlobalState()


def bootstrap():
    """Initializes the ~/.micro_learner directory structure."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SYLLABI_DIR.mkdir(exist_ok=True)
    LESSONS_DIR.mkdir(exist_ok=True)
    NOTES_DIR.mkdir(exist_ok=True)

    try:
        load_state()
    except (json.JSONDecodeError, ValidationError):
        save_state(_new_global_state())


def load_state() -> GlobalState:
    """Loads the global state from the JSON file."""
    if not STATE_FILE.exists():
        state = _new_global_state()
        save_state(state)
        return state

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return GlobalState(**data)


def save_state(state: GlobalState):
    """Saves the global state to the JSON file."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=4))


def save_syllabus_record(record: SyllabusRecord):
    """Persists an individual syllabus record to disk."""
    with open(_syllabus_path(record.id), "w", encoding="utf-8") as f:
        f.write(record.model_dump_json(indent=4))


def load_syllabus_record(record_id: str) -> Optional[SyllabusRecord]:
    """Loads a syllabus record by its identifier."""
    path = _syllabus_path(record_id)
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SyllabusRecord(**data)


def load_active_syllabus() -> Optional[SyllabusRecord]:
    """Loads the currently active syllabus record."""
    state = load_state()
    if not state.active_syllabus_id:
        return None
    return load_syllabus_record(state.active_syllabus_id)


def list_syllabus_records() -> List[SyllabusRecord]:
    """Returns all stored syllabi sorted by most recently updated."""
    records: List[SyllabusRecord] = []
    for path in SYLLABI_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            records.append(SyllabusRecord(**data))
        except (json.JSONDecodeError, ValidationError):
            continue

    return sorted(records, key=lambda record: record.updated_at, reverse=True)


def is_syllabus_resumable(record: SyllabusRecord) -> bool:
    """Returns whether a syllabus record can be resumed safely."""
    lesson_dir = get_lesson_cache_dir(record.id)
    if not lesson_dir.exists():
        return False
    if record.cache_status == "complete":
        return True

    for step_number in range(1, record.total_lessons + 1):
        if load_lesson_artifact(record.id, step_number) is None:
            return False

    mark_syllabus_cache_complete(record)
    return True


def create_syllabus_record(topic: str, syllabus: List[str]) -> SyllabusRecord:
    """Creates and persists a new syllabus record for a topic."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    now_iso = _now_iso()
    record = SyllabusRecord(
        id=f"{_slugify_topic(topic)}-{timestamp}",
        topic=topic,
        created_at=now_iso,
        updated_at=now_iso,
        current_lesson_index=0,
        total_lessons=len(syllabus),
        cache_status="pending",
        syllabus=syllabus,
    )
    save_syllabus_record(record)
    return record


def activate_syllabus(record_id: str):
    """Marks a syllabus record as the active topic."""
    save_state(GlobalState(active_syllabus_id=record_id))


def mark_syllabus_cache_complete(record: SyllabusRecord):
    """Marks a syllabus record as fully cached and saves it."""
    record.cache_status = "complete"
    record.updated_at = _now_iso()
    save_syllabus_record(record)


def get_lesson_cache_dir(record_id: str) -> Path:
    """Returns the directory containing cached lesson artifacts for a syllabus."""
    return _lesson_dir(record_id)


def save_lesson_artifact(record_id: str, artifact: LessonArtifact):
    """Persists a single lesson artifact to the syllabus cache."""
    lesson_dir = _lesson_dir(record_id)
    lesson_dir.mkdir(parents=True, exist_ok=True)
    with open(_lesson_path(record_id, artifact.step_number), "w", encoding="utf-8") as f:
        f.write(artifact.model_dump_json(indent=4))


def save_lesson_artifacts(record_id: str, artifacts: List[LessonArtifact]):
    """Persists all lesson artifacts for a syllabus."""
    for artifact in artifacts:
        save_lesson_artifact(record_id, artifact)


def load_lesson_artifact(record_id: str, step_number: int) -> Optional[LessonArtifact]:
    """Loads a cached lesson artifact by syllabus id and step number."""
    path = _lesson_path(record_id, step_number)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LessonArtifact(**data)
    except (json.JSONDecodeError, ValidationError):
        return None


def delete_syllabus_cache(record_id: str):
    """Removes cached lesson artifacts for a syllabus."""
    shutil.rmtree(_lesson_dir(record_id), ignore_errors=True)


def delete_syllabus_record(record_id: str):
    """Deletes a syllabus record and its cached lessons."""
    _syllabus_path(record_id).unlink(missing_ok=True)
    delete_syllabus_cache(record_id)


def initialize_cached_topic(
    topic: str,
    syllabus: List[str],
    lesson_artifacts: List[LessonArtifact],
) -> SyllabusRecord:
    """Creates, fully caches, and activates a new syllabus."""
    record = create_syllabus_record(topic, syllabus)
    save_lesson_artifacts(record.id, lesson_artifacts)
    mark_syllabus_cache_complete(record)
    activate_syllabus(record.id)
    return record


def get_note_path(topic: str) -> Path:
    """Returns the markdown notes path for a topic."""
    return _note_path(topic)


def _session_heading(entry: NoteEntry) -> str:
    session_time = datetime.fromisoformat(entry.completed_at).astimezone(timezone.utc)
    return f"## Session {session_time.strftime('%Y-%m-%d %H:%M UTC')} ({entry.syllabus_id})"


def _format_lesson_entry(entry: NoteEntry) -> str:
    """Formats a completed lesson within a session section."""
    heading_prefix = "Quiz: " if entry.lesson_type == "quiz" else ""
    lines = [
        f"### {heading_prefix}Step {entry.step_number}: {entry.sub_topic}",
        f"- Completed: {entry.completed_at}",
        f"- Topic: {entry.topic} | Progress: {entry.step_number}/{entry.total_lessons}",
        "",
        entry.content.strip(),
    ]

    if entry.lesson_type == "quiz" and entry.answer:
        lines.extend(["", "### Answer", "", entry.answer.strip()])

    for intervention in entry.interventions:
        if intervention.get("type") == "analogy":
            lines.extend(["", "### 💡 Simpler Analogy", "", intervention.get("content", "").strip()])
        elif intervention.get("type") == "code":
            lines.extend(["", "### 💻 Code Example", "", intervention.get("content", "").strip()])

    lines.append("")
    return "\n".join(lines)


def _build_frontmatter(topic: str, created_at: str, updated_at: str) -> str:
    return "\n".join(
        [
            "---",
            f'title: "{topic}"',
            f'topic: "{topic}"',
            'source: "micro-learner"',
            f"created: {created_at}",
            f"updated: {updated_at}",
            "tags:",
            '  - "micro-learner"',
            f'  - "{_topic_tag(topic)}"',
            "---",
            "",
            f"# {topic}",
            "",
        ]
    )


def _split_frontmatter(content: str) -> tuple[Optional[dict], str]:
    if not content.startswith("---\n"):
        return None, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return None, content

    frontmatter_block = content[4:end]
    body = content[end + 5 :]
    metadata: dict[str, object] = {}
    current_list_key: Optional[str] = None
    current_list: list[str] = []

    for raw_line in frontmatter_block.splitlines():
        line = raw_line.rstrip()
        if line.startswith("  - ") and current_list_key:
            current_list.append(line[4:].strip().strip('"'))
            metadata[current_list_key] = current_list
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            current_list_key = key
            current_list = []
            metadata[key] = current_list
        else:
            metadata[key] = value.strip('"')

    return metadata, body


def _replace_frontmatter_updated(content: str, updated_at: str) -> str:
    metadata, body = _split_frontmatter(content)
    if metadata is None:
        return content
    metadata["updated"] = updated_at
    return _serialize_note_document(metadata, body)


def _serialize_note_document(metadata: dict, body: str) -> str:
    lines = [
        "---",
        f'title: "{metadata["title"]}"',
        f'topic: "{metadata["topic"]}"',
        f'source: "{metadata["source"]}"',
        f'created: {metadata["created"]}',
        f'updated: {metadata["updated"]}',
        "tags:",
    ]
    for tag in metadata.get("tags", []):
        lines.append(f'  - "{tag}"')
    lines.extend(["---", "", body.lstrip("\n")])
    return "\n".join(lines).rstrip() + "\n"


def _upgrade_legacy_note(topic: str, existing_content: str, now_iso: str) -> str:
    legacy_body = existing_content.strip()
    body_lines = [f"# {topic}", ""]
    if legacy_body:
        body_lines.extend(["## Legacy Notes", "", legacy_body, ""])
    metadata = {
        "title": topic,
        "topic": topic,
        "source": "micro-learner",
        "created": now_iso,
        "updated": now_iso,
        "tags": ["micro-learner", _topic_tag(topic)],
    }
    return _serialize_note_document(metadata, "\n".join(body_lines))


def format_note_entry(entry: NoteEntry) -> str:
    """Formats a completed lesson block for insertion into a session."""
    return _format_lesson_entry(entry)


def append_note_entry(entry: NoteEntry) -> Path:
    """Appends a formatted note entry to the topic markdown file."""
    path = _note_path(entry.topic)
    now_iso = entry.completed_at
    existing_content = path.read_text(encoding="utf-8") if path.exists() else ""

    if not existing_content:
        document = _build_frontmatter(entry.topic, now_iso, now_iso)
    else:
        metadata, _ = _split_frontmatter(existing_content)
        if metadata is None:
            document = _upgrade_legacy_note(entry.topic, existing_content, now_iso)
        else:
            document = _replace_frontmatter_updated(existing_content, now_iso)

    _, body = _split_frontmatter(document)
    session_heading = _session_heading(entry)
    lesson_block = format_note_entry(entry).strip()

    if session_heading in body:
        updated_body = body.replace(session_heading, f"{session_heading}\n\n{lesson_block}", 1)
    else:
        separator = "" if body.rstrip().endswith("\n") or not body.strip() else "\n"
        updated_body = f"{body.rstrip()}{separator}\n{session_heading}\n\n{lesson_block}\n"

    metadata, _ = _split_frontmatter(document)
    final_content = _serialize_note_document(metadata, updated_body)
    with open(path, "w", encoding="utf-8") as f:
        f.write(final_content)
    return path
