from __future__ import annotations

from dataclasses import replace

from src.common.config import get_settings
from src.viewer.agent import ViewerAgent
from src.viewer.workflow import ViewerWorkflow


class FakeQueryService:
    def status(self):
        class Status:
            available = True
            query_url = "http://example.invalid/query"
            triple_count = 3
            message = "Fuseki is reachable."

        return Status()

    def graph_summary(self) -> dict[str, object]:
        return {
            "triple_count": 3,
            "classes": [{"class": "http://example.org/schema#Record", "label": "Record"}],
            "properties": [],
            "sample_instances": [],
        }

    def search_facts(self, question: str) -> list[dict[str, str]]:
        return [
            {
                "subject": "http://example.org/instances#record1",
                "subjectLabel": "Record 1",
                "predicateLabel": "name",
                "object": "Record 1",
            }
        ]

    def class_instances_by_label(self, class_label: str, limit: int = 50) -> list[dict[str, str]]:
        return [
            {
                "instance": "http://example.org/instances#record1",
                "label": "Record 1",
                "predicateLabel": "name",
                "object": "Record 1",
            }
        ]


def test_viewer_workflow_builds_agents_sdk_shell() -> None:
    workflow = ViewerWorkflow()

    agent = workflow.build_agent()

    assert agent.name == "Semantic Web Viewer Workflow Agent"
    assert {tool.name for tool in agent.tools} == {
        "get_graph_status",
        "get_graph_summary",
        "run_sparql_select",
        "search_graph_facts",
    }


def test_viewer_agent_uses_fuseki_query_service(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        prompts.append(prompt)
        return "Record 1 is present, supported by http://example.org/instances#record1."

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)

    result = ViewerAgent(model="test-model").answer("What records exist?", FakeQueryService())

    assert "Record 1 is present" in result.answer
    assert result.facts[0]["subjectLabel"] == "Record 1"
    assert "Question-relevant graph facts" in prompts[0]


def test_viewer_workflow_answer_question_with_stubbed_agent(monkeypatch, tmp_path) -> None:
    settings = replace(get_settings(), db_dir=tmp_path)
    workflow = ViewerWorkflow(settings)
    workflow.query_service = FakeQueryService()

    def fake_answer(self, question, query_service):
        from src.viewer.agent import ViewerAnswer

        return ViewerAnswer(
            question=question,
            answer="Stub answer.",
            facts=[{"subjectLabel": "Record 1"}],
        )

    monkeypatch.setattr("src.viewer.workflow.ViewerAgent.answer", fake_answer)

    result = workflow.answer_question("What records exist?")

    assert result.answer == "Stub answer."
    assert result.facts[0]["subjectLabel"] == "Record 1"
