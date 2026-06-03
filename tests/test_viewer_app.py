from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from src.viewer.app import create_app


@dataclass(frozen=True)
class StubResult:
    question: str
    answer: str
    facts: list[dict[str, str]]


class StubWorkflow:
    def __init__(self) -> None:
        self.questions: list[tuple[str, str | None]] = []
        self.started = False
        self.stopped = False

    def start_fuseki_if_needed(self) -> dict[str, object]:
        self.started = True
        return {"status": "already_running", "message": "Fuseki is already reachable.", "pid": None}

    def stop_fuseki_if_started(self) -> dict[str, object]:
        self.stopped = True
        return {"status": "not_started", "message": "Fuseki was not started by this workflow.", "pid": None}

    def graph_status(self) -> dict[str, object]:
        return {
            "available": True,
            "query_url": "http://example.invalid/query",
            "triple_count": 3,
            "message": "Fuseki is reachable.",
        }

    def create_chat_session(self) -> dict[str, object]:
        return {"session_id": "test-session", "path": "/tmp/test-session.json", "messages": []}

    def chat_history(self, session_id: str) -> dict[str, object]:
        return {"session_id": session_id, "messages": []}

    def answer_question(self, question: str, session_id: str | None = None) -> StubResult:
        self.questions.append((question, session_id))
        return StubResult(
            question=question,
            answer="The graph contains Record 1.",
            facts=[{"subjectLabel": "Record 1"}],
        )

    def export_turtle(self) -> str:
        return "@prefix ex: <http://example.org/> .\nex:s ex:p ex:o .\n"

    def plot_html(self) -> str:
        return "<!doctype html><html><body>Semantic graph</body></html>"


def test_viewer_index_loads_chatbot_page() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/")

    assert response.status_code == 200
    assert "Vibe Semanting Viewer" in response.text
    assert "/api/question" in response.text
    assert "/api/chat/session" in response.text
    assert "/api/plot.html" in response.text


def test_viewer_status_endpoint_reports_fuseki_status() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["triple_count"] == 3


def test_viewer_app_lifespan_starts_and_stops_fuseki() -> None:
    workflow = StubWorkflow()

    with TestClient(create_app(workflow)) as client:
        assert workflow.started is True
        assert workflow.stopped is False
        assert client.get("/api/status").status_code == 200

    assert workflow.stopped is True


def test_viewer_question_endpoint_returns_answer_and_facts() -> None:
    workflow = StubWorkflow()
    client = TestClient(create_app(workflow))

    response = client.post(
        "/api/question",
        json={"question": "What is in the graph?", "session_id": "test-session"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "test-session"
    assert payload["answer"] == "The graph contains Record 1."
    assert payload["facts"][0]["subjectLabel"] == "Record 1"
    assert workflow.questions == [("What is in the graph?", "test-session")]


def test_viewer_chat_session_endpoint_creates_session() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.post("/api/chat/session")

    assert response.status_code == 200
    assert response.json()["session_id"] == "test-session"


def test_viewer_export_endpoint_returns_turtle() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/api/export.ttl")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/turtle")
    assert response.text.startswith("@prefix")


def test_viewer_plot_endpoint_returns_html() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/api/plot.html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Semantic graph" in response.text
