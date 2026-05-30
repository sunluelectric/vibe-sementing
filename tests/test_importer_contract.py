from __future__ import annotations

from src.common.llm import parse_json_object
from src.common.rdf import parse_turtle
from src.importer.agent import ImporterAgent
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
