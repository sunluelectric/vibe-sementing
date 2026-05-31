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
    def graph_status(self) -> dict[str, object]:
        return {
            "available": True,
            "query_url": "http://example.invalid/query",
            "triple_count": 3,
            "message": "Fuseki is reachable.",
        }

    def answer_question(self, question: str) -> StubResult:
        return StubResult(
            question=question,
            answer="The graph contains Record 1.",
            facts=[{"subjectLabel": "Record 1"}],
        )

    def export_turtle(self) -> str:
        return "@prefix ex: <http://example.org/> .\nex:s ex:p ex:o .\n"


def test_viewer_index_loads_chatbot_page() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/")

    assert response.status_code == 200
    assert "Semantic Web Viewer" in response.text
    assert "/api/question" in response.text


def test_viewer_status_endpoint_reports_fuseki_status() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["triple_count"] == 3


def test_viewer_question_endpoint_returns_answer_and_facts() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.post("/api/question", json={"question": "What is in the graph?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "The graph contains Record 1."
    assert payload["facts"][0]["subjectLabel"] == "Record 1"


def test_viewer_export_endpoint_returns_turtle() -> None:
    client = TestClient(create_app(StubWorkflow()))

    response = client.get("/api/export.ttl")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/turtle")
    assert response.text.startswith("@prefix")
