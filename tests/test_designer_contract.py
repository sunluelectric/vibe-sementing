from __future__ import annotations

import json

from src.common.llm import parse_json_object
from src.common.rdf import parse_turtle
from src.designer.agent import DesignerAgent, DesignFocus


VALID_DESIGN_RESPONSE = r'''
{
  "design_markdown": "# Test Design\n\nA minimal test design.",
  "ontology_turtle": "@prefix sw: <http://example.org/semantic-web#> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\nsw:Record a rdfs:Class ; rdfs:label \"Record\" ; rdfs:comment \"A source record.\" .\nsw:Source a rdfs:Class ; rdfs:label \"Source\" ; rdfs:comment \"An input source.\" .\nsw:Topic a rdfs:Class ; rdfs:label \"Topic\" ; rdfs:comment \"A described topic.\" .\nsw:hasSource a rdf:Property ; rdfs:label \"has source\" ; rdfs:comment \"Links a record to a source.\" ; rdfs:domain sw:Record ; rdfs:range sw:Source .\nsw:hasTopic a rdf:Property ; rdfs:label \"has topic\" ; rdfs:comment \"Links a record to a topic.\" ; rdfs:domain sw:Record ; rdfs:range sw:Topic .\nsw:name a rdf:Property ; rdfs:label \"name\" ; rdfs:comment \"A display name.\" ; rdfs:domain rdfs:Resource ; rdfs:range xsd:string .\n"
}
'''


def test_designer_response_contract_parses_json_and_turtle() -> None:
    payload = parse_json_object(VALID_DESIGN_RESPONSE)

    assert payload["design_markdown"].startswith("# Test Design")
    graph = parse_turtle(payload["ontology_turtle"])

    DesignerAgent("test-model")._validate_schema_graph(graph)


def test_designer_validation_rejects_property_without_domain() -> None:
    turtle = """
@prefix sw: <http://example.org/semantic-web#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

sw:Record a rdfs:Class .
sw:relatedTo a rdf:Property ; rdfs:range sw:Record .
"""
    graph = parse_turtle(turtle)

    try:
        DesignerAgent("test-model")._validate_schema_graph(graph)
    except ValueError as exc:
        assert "missing rdfs:domain" in str(exc)
    else:
        raise AssertionError("Expected schema validation to reject missing domain.")


def test_designer_agent_runs_with_stubbed_response() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            assert "Design a compact RDF/RDFS semantic web schema" in prompt
            assert "For CSV columns, treat profile datatypes as recommendations" in prompt
            assert "Prefer xsd:string for identifiers" in prompt
            return VALID_DESIGN_RESPONSE

    result = StubDesigner("test-model").run("requirements", "data", max_attempts=1)

    assert result.design_markdown.startswith("# Test Design")
    assert len(result.graph) >= 20


def test_designer_agent_uses_production_prompt() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            assert "Design a comprehensive RDF/RDFS semantic web schema" in prompt
            assert "Do not intentionally keep the ontology small" in prompt
            assert "For CSV columns, treat profile datatypes as recommendations" in prompt
            return VALID_DESIGN_RESPONSE

    result = StubDesigner("test-model", mode="production", ontology_triple_limit=2000).run(
        "requirements",
        "data",
        max_attempts=1,
    )

    assert result.design_markdown.startswith("# Test Design")


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


def test_designer_agent_rejects_test_mode_triple_limit() -> None:
    class LargeDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            turtle = _large_valid_ontology_turtle(class_count=50, property_count=50)
            return json.dumps({"design_markdown": "# Large", "ontology_turtle": turtle})

    try:
        LargeDesigner("test-model", ontology_triple_limit=260).run("requirements", "data", max_attempts=1)
    except RuntimeError as exc:
        assert "exceeds the configured 260 triple limit" in str(exc)
    else:
        raise AssertionError("Expected test mode ontology size limit to reject the output.")


def test_designer_agent_allows_larger_production_triple_limit() -> None:
    class LargeDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            turtle = _large_valid_ontology_turtle(class_count=50, property_count=50)
            return json.dumps({"design_markdown": "# Large", "ontology_turtle": turtle})

    result = LargeDesigner(
        "test-model",
        mode="production",
        ontology_triple_limit=2000,
    ).run("requirements", "data", max_attempts=1)

    assert len(result.graph) > 260


def test_designer_agent_plans_retrieval_focuses() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            assert "planning semantic-search work" in prompt
            return (
                '{"focuses": ['
                '{"query": "locations scenes exits", "purpose": "Model places."},'
                '{"query": "characters relationships", "purpose": "Model actors."}'
                "]}"
            )

    focuses = StubDesigner("test-model").plan_focuses(
        requirements="Design a schema.",
        data_inventory="sample inventory",
        max_focuses=3,
    )

    assert [focus.query for focus in focuses] == [
        "locations scenes exits",
        "characters relationships",
    ]


def test_designer_agent_drafts_schema_slice_notes() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            assert "drafting one small schema slice" in prompt
            assert "locations scenes exits" in prompt
            return '{"schema_notes": "- Candidate class: Scene\\n- Candidate property: hasExit"}'

    notes = StubDesigner("test-model").draft_schema_slice(
        requirements="Design a schema.",
        focus=DesignFocus(query="locations scenes exits", purpose="Model places."),
        context="Scene context.",
    )

    assert "Candidate class: Scene" in notes


def test_designer_agent_uses_raw_schema_slice_when_json_is_malformed() -> None:
    class StubDesigner(DesignerAgent):
        def _run_direct_design_call(self, prompt: str) -> str:
            return '{"schema_notes": "Candidate path C:\\bad\\escape"}'

    notes = StubDesigner("test-model").draft_schema_slice(
        requirements="Design a schema.",
        focus=DesignFocus(query="paths", purpose="Model paths."),
        context="Path context.",
    )

    assert "schema_notes" in notes
    assert "Candidate path" in notes


def _large_valid_ontology_turtle(class_count: int, property_count: int) -> str:
    lines = [
        "@prefix sw: <http://example.org/semantic-web#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]
    for index in range(class_count):
        lines.append(
            f"sw:Class{index} a rdfs:Class ; "
            f"rdfs:label \"Class {index}\" ; "
            f"rdfs:comment \"Generated class {index}.\" ."
        )
    for index in range(property_count):
        lines.append(
            f"sw:property{index} a rdf:Property ; "
            f"rdfs:label \"property {index}\" ; "
            f"rdfs:comment \"Generated property {index}.\" ; "
            f"rdfs:domain sw:Class{index % class_count} ; "
            f"rdfs:range xsd:string ."
        )
    return "\n".join(lines)
