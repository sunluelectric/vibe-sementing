from __future__ import annotations

from dataclasses import replace

import pytest

from src.common.config import get_settings
from src.common.fuseki import client_from_settings
from src.common.rdf import load_graph, parse_turtle
from src.importer.agent import ImportResult
from src.importer.workflow import ImporterWorkflow
from tests.test_importer_contract import VALID_IMPORT_RESPONSE, VALID_ONTOLOGY_TURTLE
from src.common.llm import parse_json_object


class OfflineFusekiClient:
    graph_store_url = "http://example.invalid/data"
    query_url = "http://example.invalid/query"
    update_url = "http://example.invalid/update"

    def is_available(self) -> bool:
        return False


class OnlineFusekiClient(OfflineFusekiClient):
    def __init__(self) -> None:
        self.loaded: list[tuple[str, str]] = []

    def is_available(self) -> bool:
        return True

    def replace_graph(self, graph_uri: str, turtle: str) -> None:
        self.loaded.append((graph_uri, turtle))


def _workflow_with_temp_paths(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "source.md").write_text("# Source\n\nRecord 1 from Source 1.", encoding="utf-8")
    ontology_path = tmp_path / "ontology.ttl"
    ontology_path.write_text(VALID_ONTOLOGY_TURTLE, encoding="utf-8")
    design_path = tmp_path / "design.md"
    design_path.write_text("# Design", encoding="utf-8")
    settings = replace(
        get_settings(),
        data_dir=data_dir,
        design_doc_path=design_path,
        ontology_path=ontology_path,
        instances_path=tmp_path / "instances.ttl",
        combined_path=tmp_path / "semantic_web.ttl",
        db_dir=tmp_path,
    )
    return ImporterWorkflow(settings)


def _valid_import_result() -> ImportResult:
    payload = parse_json_object(VALID_IMPORT_RESPONSE)
    turtle = payload["instances_turtle"]
    return ImportResult(instances_turtle=turtle, graph=parse_turtle(turtle))


def test_importer_workflow_builds_agents_sdk_shell() -> None:
    workflow = ImporterWorkflow()

    agent = workflow.build_agent()

    assert agent.name == "Semantic Web Importer Workflow Agent"
    assert {tool.name for tool in agent.tools} == {
        "read_design_text",
        "read_source_data",
        "inspect_ontology",
        "run_iterative_import",
        "persist_and_load_instances",
    }


def test_importer_workflow_reads_inputs_and_inspects_ontology(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)

    assert workflow.read_design_text() == "# Design"
    assert "Record 1" in workflow.read_source_data()
    terms = workflow.inspect_ontology()
    assert terms["class_count"] == 2
    assert terms["property_count"] == 2


def test_importer_persistence_writes_instances_and_combined_fallback(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    workflow.fuseki_client = OfflineFusekiClient()
    workflow.last_import = _valid_import_result()

    result = workflow.persist_and_load_instances()

    assert result["load_target"] == "file"
    assert workflow.settings.instances_path.exists()
    assert workflow.settings.combined_path.exists()
    assert len(load_graph(workflow.settings.instances_path)) >= 4
    assert len(load_graph(workflow.settings.combined_path)) > len(load_graph(workflow.settings.instances_path))


def test_importer_persistence_loads_fuseki_when_available(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    client = OnlineFusekiClient()
    workflow.fuseki_client = client
    workflow.last_import = _valid_import_result()

    result = workflow.persist_and_load_instances()

    assert result["load_target"] == "fuseki"
    assert len(client.loaded) == 1
    graph_uri, turtle = client.loaded[0]
    assert graph_uri == workflow.settings.data_graph_uri
    assert len(parse_turtle(turtle)) >= 4


def test_importer_fuseki_smoke_loads_test_graph_when_available() -> None:
    settings = get_settings()
    client = client_from_settings(settings)
    if not client.is_available():
        pytest.skip("Fuseki is not available.")

    payload = parse_json_object(VALID_IMPORT_RESPONSE)
    graph = parse_turtle(payload["instances_turtle"])
    graph_uri = "http://example.org/semantic-web/test/importer-smoke"
    client.replace_graph(graph_uri, graph.serialize(format="turtle"))

    rows = client.select(
        f"""
        SELECT (COUNT(?s) AS ?count) WHERE {{
          GRAPH <{graph_uri}> {{
            ?s ?p ?o .
          }}
        }}
        """
    )

    assert int(rows[0]["count"]) >= len(graph)
