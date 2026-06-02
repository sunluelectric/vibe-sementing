from __future__ import annotations

from dataclasses import replace

from src.common.config import get_settings
from src.viewer.agent import ViewerAgent
from src.viewer.workflow import ViewerWorkflow


class FakeQueryService:
    def __init__(self) -> None:
        self.class_lookups: list[str] = []

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
            "classes": [
                {"class": "http://example.org/schema#Record", "label": "Record"},
                {"class": "http://example.org/schema#Npc", "label": "Non-Player Character"},
            ],
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

    def subject_facts_matching_question_labels(self, question: str) -> list[dict[str, str]]:
        if "Record 1" not in question:
            return []
        return [
            {
                "subject": "http://example.org/instances#record1",
                "subjectLabel": "Record 1",
                "predicateLabel": "description",
                "object": "Exact record facts are prioritized.",
            }
        ]

    def class_instances_by_label(self, class_label: str, limit: int = 50) -> list[dict[str, str]]:
        self.class_lookups.append(class_label)
        return [
            {
                "instance": "http://example.org/instances#record1",
                "label": "Record 1",
                "predicateLabel": "name",
                "object": "Record 1",
            }
        ]

    def class_instance_count_by_label(self, class_label: str) -> int:
        return 1


class SemanticClassQueryService(FakeQueryService):
    def graph_summary(self) -> dict[str, object]:
        return {
            "triple_count": 3,
            "classes": [
                {
                    "class": "http://example.org/schema#TenYearOld",
                    "label": "Ten Year Old",
                    "comment": "Children who are ten years old.",
                },
            ],
            "properties": [],
            "sample_instances": [],
        }

    def search_facts(self, question: str) -> list[dict[str, str]]:
        return []

    def class_instances_by_label(self, class_label: str, limit: int = 50) -> list[dict[str, str]]:
        self.class_lookups.append(class_label)
        return [
            {
                "instance": "http://example.org/instances#alice",
                "label": "Alice",
                "predicateLabel": "age",
                "object": "10",
            }
        ]

    def class_instance_count_by_label(self, class_label: str) -> int:
        return 1


class AmbiguousClassQueryService(SemanticClassQueryService):
    def graph_summary(self) -> dict[str, object]:
        return {
            "triple_count": 3,
            "classes": [
                {
                    "class": "http://example.org/schema#TenYearOld",
                    "label": "Ten Year Old",
                    "comment": "Children who are ten years old.",
                },
                {
                    "class": "http://example.org/schema#YouthGroup",
                    "label": "Youth Group",
                    "comment": "Groups for young people.",
                },
            ],
            "properties": [],
            "sample_instances": [],
        }


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

    query_service = FakeQueryService()
    result = ViewerAgent(model="test-model").answer(
        "What records exist?",
        query_service,
        history="User: Previous question\nAssistant: Previous answer",
    )

    assert "Record 1 is present" in result.answer
    assert result.facts[0]["subjectLabel"] == "Record 1"
    assert "Question-relevant graph facts" in prompts[0]
    assert "Previous question" in prompts[0]
    assert "Answer for an end user" in prompts[0]
    assert "Do not paste raw query rows" in prompts[0]
    assert "brief clarification question" in prompts[0]


def test_viewer_agent_matches_acronym_class_requests(monkeypatch) -> None:
    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        return "The NPCs are listed by name with short descriptions."

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)
    query_service = FakeQueryService()

    ViewerAgent(model="test-model").answer("What are the NPCs?", query_service)

    assert "Non-Player Character" in query_service.class_lookups


def test_viewer_agent_includes_class_instance_count_for_count_questions(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        prompts.append(prompt)
        return "There is 1 record."

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)
    query_service = FakeQueryService()

    ViewerAgent(model="test-model").answer("How many records are there?", query_service)

    assert "classInstanceCount=1" in prompts[0]


def test_viewer_agent_uses_llm_to_match_nonlexical_class_terms(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        prompts.append(prompt)
        if "choose which ontology classes to query" in prompt:
            assert "kids" in prompt
            assert "Ten Year Old" in prompt
            return '{"class_labels": ["Ten Year Old"]}'
        return "There is 1 kid: Alice."

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)
    query_service = SemanticClassQueryService()

    result = ViewerAgent(model="test-model").answer(
        "How many kids are stored?",
        query_service,
        design_text="# Design\nTen Year Old represents kids in the records.",
    )

    assert result.answer == "There is 1 kid: Alice."
    assert "Ten Year Old" in query_service.class_lookups
    assert any(fact.get("matchSource") == "llm_class_match" for fact in result.facts)
    assert "classInstanceCount=1" in prompts[-1]
    assert "Design document excerpt" in prompts[0]
    assert "Ten Year Old represents kids" in prompts[0]


def test_viewer_agent_treats_multiple_llm_class_matches_as_clarification(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        prompts.append(prompt)
        if "choose which ontology classes to query" in prompt:
            return '{"class_labels": ["Ten Year Old", "Youth Group"]}'
        assert "probableClassLabel=Ten Year Old" in prompt
        assert "probableClassLabel=Youth Group" in prompt
        return "I found two likely meanings: Ten Year Old and Youth Group. Which one do you mean?"

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)
    query_service = AmbiguousClassQueryService()

    result = ViewerAgent(model="test-model").answer("List the kids.", query_service)

    assert "Which one do you mean" in result.answer
    assert query_service.class_lookups == []
    assert {fact.get("probableClassLabel") for fact in result.facts} == {"Ten Year Old", "Youth Group"}
    assert all(fact.get("matchSource") == "llm_class_ambiguity" for fact in result.facts)


def test_viewer_agent_prioritizes_exact_subject_label_facts(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_get_text_response(model: str, prompt: str, timeout_seconds: int) -> str:
        prompts.append(prompt)
        return "Record 1 has exact facts."

    monkeypatch.setattr("src.viewer.agent.get_text_response", fake_get_text_response)

    result = ViewerAgent(model="test-model").answer("Tell me about Record 1", FakeQueryService())

    assert result.facts[0]["predicateLabel"] == "description"
    assert "Exact record facts are prioritized" in prompts[0]


def test_viewer_workflow_answer_question_with_stubbed_agent(monkeypatch, tmp_path) -> None:
    settings = replace(
        get_settings(),
        db_dir=tmp_path,
        viewer_chat_dir=tmp_path / "chat",
        design_doc_path=tmp_path / "design.md",
    )
    settings.design_doc_path.write_text("# Design", encoding="utf-8")
    workflow = ViewerWorkflow(settings)
    workflow.query_service = FakeQueryService()
    session = workflow.create_chat_session()

    def fake_answer(self, question, query_service, history="", design_text=""):
        from src.viewer.agent import ViewerAnswer

        assert design_text == "# Design"
        return ViewerAnswer(
            question=question,
            answer="Stub answer.",
            facts=[{"subjectLabel": "Record 1"}],
        )

    monkeypatch.setattr("src.viewer.workflow.ViewerAgent.answer", fake_answer)

    result = workflow.answer_question("What records exist?", session_id=session["session_id"])

    assert result.answer == "Stub answer."
    assert result.facts[0]["subjectLabel"] == "Record 1"
    history = workflow.chat_history(session["session_id"])
    assert len(history["messages"]) == 2
