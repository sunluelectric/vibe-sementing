from __future__ import annotations

from src.common.llm import parse_json_object
from src.common.rdf import parse_turtle
from src.designer.agent import DesignerAgent
from src.designer.validation import validate_ontology_graph


VALID_DESIGN_RESPONSE = r'''
{
  "design_markdown": "# Test Design\n\nA minimal test design.",
  "ontology_turtle": "@prefix dnd: <http://example.org/dnd-adventure#> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\ndnd:Adventure a rdfs:Class .\ndnd:Quest a rdfs:Class .\ndnd:Scene a rdfs:Class .\ndnd:Location a rdfs:Class .\ndnd:Character a rdfs:Class .\ndnd:Npc a rdfs:Class ; rdfs:subClassOf dnd:Character .\ndnd:Monster a rdfs:Class ; rdfs:subClassOf dnd:Character .\ndnd:PlayerOption a rdfs:Class .\ndnd:Item a rdfs:Class .\ndnd:Weapon a rdfs:Class ; rdfs:subClassOf dnd:Item .\ndnd:Encounter a rdfs:Class .\ndnd:Check a rdfs:Class .\ndnd:Reward a rdfs:Class .\ndnd:VictoryCondition a rdfs:Class .\ndnd:hasScene a rdf:Property ; rdfs:domain dnd:Adventure ; rdfs:range dnd:Scene .\n"
}
'''


def test_designer_response_contract_parses_json_and_turtle() -> None:
    payload = parse_json_object(VALID_DESIGN_RESPONSE)

    assert payload["design_markdown"].startswith("# Test Design")
    graph = parse_turtle(payload["ontology_turtle"])

    validation = validate_ontology_graph(graph)
    validation.raise_for_errors()


def test_designer_validation_rejects_missing_required_class() -> None:
    turtle = """
@prefix dnd: <http://example.org/dnd-adventure#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

dnd:Adventure a rdfs:Class .
"""
    graph = parse_turtle(turtle)

    validation = validate_ontology_graph(graph)

    assert not validation.ok
    assert "Missing required class dnd:Scene" in validation.errors


def test_designer_agent_runs_with_stubbed_response() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            return VALID_DESIGN_RESPONSE

    result = StubDesigner("test-model").run("requirements", "data", max_attempts=1)

    assert result.design_markdown.startswith("# Test Design")
    assert len(result.graph) >= 20


def test_designer_agent_writes_progress_after_stubbed_call(tmp_path) -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            return VALID_DESIGN_RESPONSE

    progress_path = tmp_path / "design.md"
    result = StubDesigner("test-model").run(
        "requirements",
        "data",
        max_attempts=1,
        progress_path=progress_path,
    )

    progress = progress_path.read_text(encoding="utf-8")
    assert "Semantic Web Designer Progress" in progress
    assert "Attempt 1" in progress
    assert "LLM request started" in progress
    assert "LLM response received" in progress
    assert "Status: passed" in progress
    assert "# Test Design" in progress
    assert result.progress_markdown == progress.strip()


def test_designer_agent_records_llm_call_failure(tmp_path) -> None:
    class TimeoutDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            raise TimeoutError("test timeout")

    progress_path = tmp_path / "design.md"

    try:
        TimeoutDesigner("test-model").run(
            "requirements",
            "data",
            max_attempts=1,
            progress_path=progress_path,
        )
    except RuntimeError:
        pass

    progress = progress_path.read_text(encoding="utf-8")
    assert "LLM request started" in progress
    assert "LLM request failed" in progress
    assert "TimeoutError: test timeout" in progress


def test_designer_agent_retries_after_invalid_turtle() -> None:
    class RetryDesigner(DesignerAgent):
        def __init__(self) -> None:
            super().__init__("test-model")
            self.calls = 0
            self.prompts: list[str] = []

        def _run_with_optional_crewai(self, prompt: str) -> str:
            raise AssertionError("Designer should use direct design calls only.")

        def _run_direct_design_call(self, prompt: str) -> str:
            self.calls += 1
            self.prompts.append(prompt)
            if self.calls == 1:
                return '{"design_markdown": "# Bad", "ontology_turtle": "not turtle"}'
            return VALID_DESIGN_RESPONSE

    agent = RetryDesigner()
    result = agent.run("requirements", "data", max_attempts=2)

    assert result.design_markdown.startswith("# Test Design")
    assert agent.calls == 2
    assert "previous response failed validation" in agent.prompts[1]
