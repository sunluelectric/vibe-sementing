from __future__ import annotations

import json

import pytest

from src.viewer.chat import ChatStore, format_history


def test_chat_store_creates_session_file_and_appends_turn(tmp_path) -> None:
    store = ChatStore(tmp_path)

    session = store.create_session()
    updated = store.append_turn(
        session.session_id,
        question="What rewards exist?",
        answer="Two rewards exist.",
        facts=[{"subjectLabel": "Reward"}],
    )

    path = tmp_path / f"{session.session_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.exists()
    assert updated.session_id == session.session_id
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][1]["role"] == "assistant"
    assert payload["messages"][1]["facts"][0]["subjectLabel"] == "Reward"


def test_chat_store_rejects_invalid_session_id(tmp_path) -> None:
    store = ChatStore(tmp_path)

    with pytest.raises(ValueError):
        store.read_messages("../outside")


def test_format_history_uses_recent_messages(tmp_path) -> None:
    store = ChatStore(tmp_path)
    session = store.create_session()
    store.append_turn(session.session_id, "First question", "First answer", [])

    history = format_history(store.read_messages(session.session_id))

    assert "User: First question" in history
    assert "Assistant: First answer" in history
