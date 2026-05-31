from __future__ import annotations

from dataclasses import replace

import pytest

from src.common.config import get_settings
from src.common.fuseki import client_from_settings
from src.common.rdf import load_graph, parse_turtle
from src.importer.agent import ImportFocus, ImportResult
from src.importer.workflow import ImporterWorkflow
from tests.test_importer_contract import VALID_IMPORT_RESPONSE, VALID_ONTOLOGY_TURTLE
from src.common.llm import parse_json_object
from src.importer.csv_import import CsvColumnMapping, CsvFileMapping, CsvImportPlan, CsvRelationshipMapping


class OfflineFusekiClient:
    graph_store_url = "http://example.invalid/data"
    query_url = "http://example.invalid/query"
    update_url = "http://example.invalid/update"

    def is_available(self) -> bool:
        return False


class OnlineFusekiClient(OfflineFusekiClient):
    def __init__(self) -> None:
        self.loaded: list[tuple[str, str]] = []
        self.construct_response = VALID_ONTOLOGY_TURTLE

    def is_available(self) -> bool:
        return True

    def replace_graph(self, graph_uri: str, turtle: str) -> None:
        self.loaded.append((graph_uri, turtle))

    def construct_turtle(self, sparql: str) -> str:
        return self.construct_response


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
        import_doc_path=tmp_path / "import.md",
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
        "retrieve_import_context",
        "retrieve_schema_context",
        "inspect_ontology",
        "run_iterative_import",
        "persist_and_load_instances",
    }


def test_importer_workflow_reads_inputs_and_inspects_ontology(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    workflow.fuseki_client = OfflineFusekiClient()

    assert workflow.read_design_text() == "# Design"
    assert "Record 1" in workflow.read_source_data()
    terms = workflow.inspect_ontology()
    assert terms["source"] == "file"
    assert terms["class_count"] == 2
    assert terms["property_count"] == 2


def test_importer_retrieves_source_context_for_large_data(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    (workflow.settings.data_dir / "source.md").write_text(
        "# Source\n\n"
        + "Relevant records mention Record 1 and value details.\n\n" * 200
        + "Unrelated records mention archive storage.\n\n" * 200,
        encoding="utf-8",
    )
    workflow.settings = replace(
        workflow.settings,
        semantic_context_max_chars=900,
        semantic_search_top_k=2,
    )

    context = workflow.retrieve_import_context("Record 1 value details")

    assert len(context) <= 900
    assert "Relevant records" in context
    assert "Source chunk: source.md" in context
    assert workflow.last_retrieval_summary["source"]["used"] is True
    assert workflow.last_retrieval_summary["source"]["chunk_count"] > 1


def test_importer_retrieves_schema_context_for_large_ontology(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    extra_terms = "\n".join(
        f"sw:ExtraClass{index} a rdfs:Class ; rdfs:label \"Extra Class {index}\" ."
        for index in range(80)
    )
    workflow.settings.ontology_path.write_text(
        VALID_ONTOLOGY_TURTLE + "\n" + extra_terms,
        encoding="utf-8",
    )
    workflow.settings = replace(
        workflow.settings,
        semantic_context_max_chars=900,
        semantic_search_top_k=2,
    )
    workflow.fuseki_client = OfflineFusekiClient()

    context = workflow.retrieve_schema_context("record name value")

    assert len(context) <= 900
    assert "Record" in context
    assert "Source chunk: ontology" in context
    assert workflow.last_retrieval_summary["schema"]["used"] is True
    assert workflow.last_retrieval_summary["schema"]["chunk_count"] > 1


def test_importer_iterative_retrieval_merges_model_planned_slices(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    (workflow.settings.data_dir / "source.md").write_text(
        "# Source\n\n"
        + "Record 1 from Source 1 with value details.\n\n" * 120
        + "Record 2 from Source 2 with additional details.\n\n" * 120,
        encoding="utf-8",
    )
    workflow.settings = replace(
        workflow.settings,
        semantic_context_max_chars=900,
        importer_slice_context_max_chars=700,
        semantic_search_top_k=1,
        importer_retrieval_batches=3,
    )
    workflow.fuseki_client = OfflineFusekiClient()
    ontology_graph = parse_turtle(VALID_ONTOLOGY_TURTLE)

    class StubAgent:
        def __init__(self) -> None:
            self.calls = 0

        def plan_import_focus(
            self,
            design_text,
            ontology_graph,
            data_inventory,
            existing_instances,
            progress_path=None,
        ):
            self.calls += 1
            assert "source=source.md" in data_inventory
            if self.calls == 1:
                assert "No instances imported yet" in existing_instances
                return ImportFocus(False, "Record 1 Source 1", "Import first record.")
            if self.calls == 2:
                assert "record-1" in existing_instances
                return ImportFocus(False, "Record 2 Source 2", "Import second record.")
            return ImportFocus(True, "", "All visible records are imported.")

        def generate_instance_slice(
            self,
            design_text,
            ontology_turtle,
            ontology_graph,
            source_data,
            focus,
            existing_instances,
            max_attempts=2,
            progress_path=None,
        ):
            assert len(source_data) <= 700
            assert len(ontology_turtle) <= 700
            if "Record 1" in focus.query:
                turtle = parse_json_object(VALID_IMPORT_RESPONSE)["instances_turtle"]
            else:
                turtle = (
                    "@prefix sw: <http://example.org/semantic-web#> .\n"
                    "@prefix inst: <http://example.org/semantic-web/instance/> .\n"
                    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
                    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
                    "inst:record-2 a sw:Record ;\n"
                    "  rdfs:label \"Record 2\" ;\n"
                    "  sw:name \"Record 2\" ;\n"
                    "  sw:hasSource inst:source-2 .\n\n"
                    "inst:source-2 a sw:Source ;\n"
                    "  rdfs:label \"Source 2\" ;\n"
                    "  sw:name \"Source 2\" .\n"
                )
            return ImportResult(instances_turtle=turtle, graph=parse_turtle(turtle))

        def _progress_markdown(self):
            return ""

        def _record_progress(self, progress_path, entry):
            if progress_path is None:
                return
            existing = progress_path.read_text(encoding="utf-8") if progress_path.exists() else ""
            progress_path.write_text((existing + "\n\n" + entry.strip()).strip() + "\n", encoding="utf-8")

    result = workflow.run_iterative_retrieval_import(
        agent=StubAgent(),
        ontology_graph=ontology_graph,
    )

    assert len(result.graph) > len(_valid_import_result().graph)
    assert workflow.last_retrieval_summary["iterative"]["used"] is True
    assert workflow.last_retrieval_summary["iterative"]["stop_reason"] == "model_complete"
    assert workflow.last_retrieval_summary["iterative"]["batch_count"] == 2
    progress = workflow.settings.import_doc_path.read_text(encoding="utf-8")
    assert "Import Batch Retrieval" in progress
    assert "Record 1 Source 1" in progress


def test_importer_workflow_deterministically_imports_csv_with_stubbed_mapping(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "stores.csv").write_text(
        "Triplestore Name,Developer/Maintainer,License Type\n"
        "Apache Jena TDB,Apache Software Foundation,Apache 2.0\n"
        "GraphDB,Ontotext,Commercial / Free Edition\n",
        encoding="utf-8",
    )
    (data_dir / "notes.md").write_text("# Notes\n\nSemantic web notes.", encoding="utf-8")
    ontology_path = tmp_path / "ontology.ttl"
    ontology_path.write_text(
        """
@prefix sw: <http://example.org/semantic-web#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sw:Triplestore a rdfs:Class .
sw:Organization a rdfs:Class .
sw:Topic a rdfs:Class .
sw:name a rdf:Property ; rdfs:domain rdfs:Resource ; rdfs:range xsd:string .
sw:licenseType a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range xsd:string .
sw:maintainedBy a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range sw:Organization .
sw:summary a rdf:Property ; rdfs:domain sw:Topic ; rdfs:range xsd:string .
""",
        encoding="utf-8",
    )
    design_path = tmp_path / "design.md"
    design_path.write_text("# Design", encoding="utf-8")
    workflow = ImporterWorkflow(
        replace(
            get_settings(),
            data_dir=data_dir,
            design_doc_path=design_path,
            ontology_path=ontology_path,
            import_doc_path=tmp_path / "import.md",
            instances_path=tmp_path / "instances.ttl",
            combined_path=tmp_path / "semantic_web.ttl",
            importer_iterations=1,
            db_dir=tmp_path,
        )
    )
    workflow.fuseki_client = OfflineFusekiClient()

    class StubAgent:
        def __init__(self, model, timeout_seconds=90) -> None:
            self.model = model
            self.timeout_seconds = timeout_seconds

        def plan_csv_import(
            self,
            design_text,
            ontology_graph,
            csv_profiles,
            max_attempts=1,
            progress_path=None,
            validation_feedback="",
        ):
            assert "Apache Jena TDB" in csv_profiles
            return CsvImportPlan(
                mappings=(
                    CsvFileMapping(
                        csv_file="stores.csv",
                        row_class_uri="http://example.org/semantic-web#Triplestore",
                        subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                        label_template="{Triplestore Name}",
                        column_mappings=(
                            CsvColumnMapping(
                                column="Triplestore Name",
                                property_uri="http://example.org/semantic-web#name",
                                datatype="string",
                            ),
                            CsvColumnMapping(
                                column="License Type",
                                property_uri="http://example.org/semantic-web#licenseType",
                                datatype="string",
                            ),
                        ),
                        relationship_mappings=(
                            CsvRelationshipMapping(
                                column="Developer/Maintainer",
                                property_uri="http://example.org/semantic-web#maintainedBy",
                                target_class_uri="http://example.org/semantic-web#Organization",
                                target_uri_template="http://example.org/semantic-web/instance/organization/{Developer/Maintainer|slug}",
                                target_label_template="{Developer/Maintainer}",
                            ),
                        ),
                    ),
                )
            )

        def run(
            self,
            design_text,
            ontology_turtle,
            ontology_graph,
            source_data,
            max_attempts=1,
            progress_path=None,
            reset_progress=False,
        ):
            assert "stores.csv" not in source_data
            graph = parse_turtle(
                """
@prefix sw: <http://example.org/semantic-web#> .
@prefix inst: <http://example.org/semantic-web/instance/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

inst:semantic-web-notes a sw:Topic ;
  sw:summary "Semantic web notes." .
"""
            )
            return ImportResult(instances_turtle="", graph=graph)

        def _progress_markdown(self):
            return ""

        def _record_progress(self, progress_path, entry):
            if progress_path is None:
                return
            existing = progress_path.read_text(encoding="utf-8") if progress_path.exists() else ""
            progress_path.write_text((existing + "\n\n" + entry.strip()).strip() + "\n", encoding="utf-8")

    monkeypatch.setattr("src.importer.workflow.ImporterAgent", StubAgent)

    result = workflow.run_iterative_import()

    assert result["status"] == "success"
    assert workflow.last_retrieval_summary["csv"]["used"] is True
    assert workflow.last_import is not None
    assert len(workflow.last_import.graph) >= 10
    progress = workflow.settings.import_doc_path.read_text(encoding="utf-8")
    assert "Deterministic CSV Import" in progress


def test_importer_inspects_ontology_from_fuseki_when_available(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    workflow.fuseki_client = OnlineFusekiClient()

    terms = workflow.inspect_ontology()

    assert terms["source"] == "fuseki"
    assert terms["class_count"] == 2
    assert terms["property_count"] == 2


def test_importer_loads_file_ontology_to_available_fuseki_when_graph_is_empty(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    client = OnlineFusekiClient()
    client.construct_response = ""
    workflow.fuseki_client = client

    terms = workflow.inspect_ontology()

    assert terms["source"] == "file_loaded_to_fuseki"
    assert len(client.loaded) == 1
    graph_uri, turtle = client.loaded[0]
    assert graph_uri == workflow.settings.ontology_graph_uri
    assert len(parse_turtle(turtle)) >= 4


def test_importer_persistence_writes_instances_and_combined_fallback(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    workflow.fuseki_client = OfflineFusekiClient()
    workflow.last_import = _valid_import_result()

    result = workflow.persist_and_load_instances()

    assert result["load_target"] == "file"
    assert workflow.settings.instances_path.exists()
    assert workflow.settings.combined_path.exists()
    assert workflow.settings.import_doc_path.exists()
    assert "Import Persistence Summary" in workflow.settings.import_doc_path.read_text(encoding="utf-8")
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
    try:
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
    finally:
        client.delete_graph(graph_uri)
