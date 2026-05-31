from __future__ import annotations

from src.common.llm import parse_json_object
from src.common.rdf import parse_turtle
from src.importer.agent import ImportFocus, ImporterAgent
from src.importer.validation import validate_instance_graph


VALID_ONTOLOGY_TURTLE = """
@prefix sw: <http://example.org/semantic-web#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sw:Record a rdfs:Class .
sw:Source a rdfs:Class .
sw:hasSource a rdf:Property ;
    rdfs:domain sw:Record ;
    rdfs:range sw:Source .
sw:name a rdf:Property ;
    rdfs:domain rdfs:Resource ;
    rdfs:range xsd:string .
"""

VALID_IMPORT_RESPONSE = r'''
{
  "instances_turtle": "@prefix sw: <http://example.org/semantic-web#> .\n@prefix inst: <http://example.org/semantic-web/instance/> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\ninst:record-1 a sw:Record ;\n    rdfs:label \"Record 1\" ;\n    sw:name \"Record 1\" ;\n    sw:hasSource inst:source-1 .\n\ninst:source-1 a sw:Source ;\n    rdfs:label \"Source 1\" ;\n    sw:name \"Source 1\" .\n"
}
'''


def test_importer_response_contract_parses_json_and_turtle() -> None:
    payload = parse_json_object(VALID_IMPORT_RESPONSE)
    ontology_graph = parse_turtle(VALID_ONTOLOGY_TURTLE)
    instance_graph = parse_turtle(payload["instances_turtle"])

    validation = validate_instance_graph(instance_graph, ontology_graph)

    validation.raise_for_errors()
    assert len(instance_graph) >= 4


def test_importer_validation_rejects_schema_mutation() -> None:
    ontology_graph = parse_turtle(VALID_ONTOLOGY_TURTLE)
    instance_graph = parse_turtle(
        """
@prefix sw: <http://example.org/semantic-web#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

sw:NewClass a rdfs:Class .
sw:newProperty a rdf:Property .
"""
    )

    validation = validate_instance_graph(instance_graph, ontology_graph)

    assert not validation.ok
    assert "must not define rdfs:Class" in "; ".join(validation.errors)
    assert "must not define rdf:Property" in "; ".join(validation.errors)


def test_importer_validation_rejects_unknown_predicate() -> None:
    ontology_graph = parse_turtle(VALID_ONTOLOGY_TURTLE)
    instance_graph = parse_turtle(
        """
@prefix sw: <http://example.org/semantic-web#> .
@prefix inst: <http://example.org/semantic-web/instance/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

inst:record-1 a sw:Record ;
    sw:unknownPredicate "bad" .
"""
    )

    validation = validate_instance_graph(instance_graph, ontology_graph)

    assert not validation.ok
    assert "not defined in the ontology" in "; ".join(validation.errors)


def test_importer_agent_runs_with_stubbed_response() -> None:
    class StubImporter(ImporterAgent):
        def _run_direct_import_call(self, prompt: str) -> str:
            return VALID_IMPORT_RESPONSE

    result = StubImporter("test-model").run(
        design_text="# Design",
        ontology_turtle=VALID_ONTOLOGY_TURTLE,
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        source_data="source",
        max_attempts=1,
    )

    assert len(result.graph) >= 4


def test_importer_agent_retries_after_schema_mutation() -> None:
    class RetryImporter(ImporterAgent):
        def __init__(self) -> None:
            super().__init__("test-model")
            self.calls = 0
            self.prompts: list[str] = []

        def _run_direct_import_call(self, prompt: str) -> str:
            self.calls += 1
            self.prompts.append(prompt)
            if self.calls == 1:
                return (
                    '{"instances_turtle": "@prefix sw: '
                    '<http://example.org/semantic-web#> .\\n'
                    '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\\n'
                    'sw:Bad a rdfs:Class .\\n"}'
                )
            return VALID_IMPORT_RESPONSE

    agent = RetryImporter()
    result = agent.run(
        design_text="# Design",
        ontology_turtle=VALID_ONTOLOGY_TURTLE,
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        source_data="source",
        max_attempts=2,
    )

    assert len(result.graph) >= 4
    assert agent.calls == 2
    assert "previous response failed validation" in agent.prompts[1]


def test_importer_agent_plans_next_import_focus() -> None:
    class StubImporter(ImporterAgent):
        def _run_direct_import_call(self, prompt: str) -> str:
            assert "planning the next semantic-search batch" in prompt
            return (
                '{"complete": false, '
                '"query": "records and sources", '
                '"purpose": "Import record/source instances."}'
            )

    focus = StubImporter("test-model").plan_import_focus(
        design_text="# Design",
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        data_inventory="source.md contains records",
        existing_instances="- No instances imported yet.",
    )

    assert focus.complete is False
    assert focus.query == "records and sources"


def test_importer_agent_generates_valid_instance_slice() -> None:
    class StubImporter(ImporterAgent):
        def _run_direct_import_call(self, prompt: str) -> str:
            assert "generating one validated slice" in prompt
            assert "records and sources" in prompt
            return VALID_IMPORT_RESPONSE

    result = StubImporter("test-model").generate_instance_slice(
        design_text="# Design",
        ontology_turtle=VALID_ONTOLOGY_TURTLE,
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        source_data="Record 1 from Source 1.",
        focus=ImportFocus(
            complete=False,
            query="records and sources",
            purpose="Import record/source instances.",
        ),
        existing_instances="- No instances imported yet.",
        max_attempts=1,
    )

    assert len(result.graph) >= 4


def test_importer_agent_writes_progress_for_planning_and_slice(tmp_path) -> None:
    class StubImporter(ImporterAgent):
        def __init__(self) -> None:
            super().__init__("test-model")
            self.calls = 0

        def _run_direct_import_call(self, prompt: str) -> str:
            self.calls += 1
            if self.calls == 1:
                return '{"complete": false, "query": "records", "purpose": "Import records."}'
            return VALID_IMPORT_RESPONSE

    progress_path = tmp_path / "import.md"
    agent = StubImporter()
    focus = agent.plan_import_focus(
        design_text="# Design",
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        data_inventory="source.md contains records",
        existing_instances="- No instances imported yet.",
        progress_path=progress_path,
    )
    agent.generate_instance_slice(
        design_text="# Design",
        ontology_turtle=VALID_ONTOLOGY_TURTLE,
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        source_data="Record 1 from Source 1.",
        focus=focus,
        existing_instances="- No instances imported yet.",
        max_attempts=1,
        progress_path=progress_path,
    )

    progress = progress_path.read_text(encoding="utf-8")
    assert "Import Focus Planning" in progress
    assert "Import Slice Generation" in progress
    assert "Import Slice Validation" in progress


def test_importer_agent_retries_invalid_instance_slice() -> None:
    class StubImporter(ImporterAgent):
        def __init__(self) -> None:
            super().__init__("test-model")
            self.calls = 0

        def _run_direct_import_call(self, prompt: str) -> str:
            self.calls += 1
            if self.calls == 1:
                return '{"instances_turtle": "not turtle"}'
            assert "previous slice failed validation" in prompt
            return VALID_IMPORT_RESPONSE

    agent = StubImporter()
    result = agent.generate_instance_slice(
        design_text="# Design",
        ontology_turtle=VALID_ONTOLOGY_TURTLE,
        ontology_graph=parse_turtle(VALID_ONTOLOGY_TURTLE),
        source_data="Record 1 from Source 1.",
        focus=ImportFocus(
            complete=False,
            query="records and sources",
            purpose="Import record/source instances.",
        ),
        existing_instances="- No instances imported yet.",
        max_attempts=2,
    )

    assert agent.calls == 2
    assert len(result.graph) >= 4
