from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    timestamp: str
    facts: list[dict[str, str]] | None = None


@dataclass(frozen=True)
class ChatSession:
    session_id: str
    path: str
    messages: list[ChatMessage]


class ChatStore:
    def __init__(self, chat_dir: Path):
        self.chat_dir = chat_dir
        self.chat_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> ChatSession:
        session_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12]
        path = self._path(session_id)
        payload = {
            "session_id": session_id,
            "created_at": _timestamp(),
            "messages": [],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return ChatSession(session_id=session_id, path=str(path), messages=[])

    def read_messages(self, session_id: str) -> list[ChatMessage]:
        payload = self._read_payload(session_id)
        messages: list[ChatMessage] = []
        for item in payload.get("messages", []):
            if not isinstance(item, dict):
                continue
            messages.append(
                ChatMessage(
                    role=str(item.get("role", "")),
                    content=str(item.get("content", "")),
                    timestamp=str(item.get("timestamp", "")),
                    facts=item.get("facts"),
                )
            )
        return messages

    def append_turn(
        self,
        session_id: str,
        question: str,
        answer: str,
        facts: list[dict[str, str]],
    ) -> ChatSession:
        payload = self._read_payload(session_id)
        payload.setdefault("messages", [])
        payload["messages"].append(
            asdict(ChatMessage(role="user", content=question, timestamp=_timestamp()))
        )
        payload["messages"].append(
            asdict(
                ChatMessage(
                    role="assistant",
                    content=answer,
                    timestamp=_timestamp(),
                    facts=facts,
                )
            )
        )
        payload["updated_at"] = _timestamp()
        path = self._path(session_id)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return ChatSession(
            session_id=session_id,
            path=str(path),
            messages=self.read_messages(session_id),
        )

    def _read_payload(self, session_id: str) -> dict[str, object]:
        path = self._path(session_id)
        if not path.exists():
            raise ValueError(f"Unknown chat session: {session_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _path(self, session_id: str) -> Path:
        if not SESSION_ID_RE.match(session_id):
            raise ValueError("Invalid chat session id.")
        return self.chat_dir / f"{session_id}.json"


def format_history(messages: list[ChatMessage], max_messages: int = 12) -> str:
    if not messages:
        return "- No previous turns in this chat session."
    lines: list[str] = []
    for message in messages[-max_messages:]:
        role = "User" if message.role == "user" else "Assistant"
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines)


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
