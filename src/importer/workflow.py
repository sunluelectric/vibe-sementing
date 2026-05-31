from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import Agent, function_tool, trace

from src.common.config import Settings, get_settings
from src.common.files import load_project_data, read_text
from src.common.fuseki import client_from_settings, load_graph_to_fuseki_or_file
from src.common.fuseki_manager import FusekiManager
from rdflib import Graph

from src.common.rdf import combine_turtle_files, load_graph, parse_turtle, serialize_graph
from src.importer.agent import ImporterAgent, ImportResult
from src.importer.validation import inspect_ontology_terms


_active_workflow: "ImporterWorkflow | None" = None


@dataclass
class ImporterWorkflowResult:
    instances_path: str
    combined_path: str
    triple_count: int
    combined_triple_count: int
    load_target: str
    fuseki_status: dict[str, Any]
    fuseki_stop_result: dict[str, Any]


class ImporterWorkflow:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.fuseki_client = client_from_settings(self.settings)
        self.fuseki_manager = FusekiManager(
            fuseki_home=self.settings.fuseki_home,
            fuseki_run_dir=self.settings.fuseki_run_dir,
            fuseki_data_dir=self.settings.fuseki_data_dir,
            fuseki_log_path=self.settings.fuseki_log_path,
            dataset=self.settings.fuseki_dataset,
            client=self.fuseki_client,
            start_timeout_seconds=self.settings.fuseki_start_timeout_seconds,
        )
        self.last_import: ImportResult | None = None
        self.last_load_target: str | None = None
        self.last_combined_triple_count: int | None = None
        self.last_stop_result: dict[str, Any] | None = None

    def build_agent(self) -> Agent:
        return Agent(
            name="Semantic Web Importer Workflow Agent",
            instructions=(
                "You orchestrate semantic web instance import for Apache Jena Fuseki. "
                "Follow this sequence: read design text, read source data, inspect ontology "
                "terms, run iterative instance generation, persist instance data, load the "
                "instance graph into Fuseki or local fallback, then report final status. "
                "Do not change ontology/schema terms; use the provided tools."
            ),
            model=self.settings.llm_model,
            tools=[
                read_design_text,
                read_source_data,
                inspect_ontology,
                run_iterative_import,
                persist_and_load_instances,
            ],
        )

    def run(self) -> ImporterWorkflowResult:
        global _active_workflow
        _active_workflow = self
        result: ImporterWorkflowResult | None = None
        try:
            self.build_agent()
            with trace("Semantic Web Importer Workflow"):
                print("Importer step: checking Fuseki status", flush=True)
                status_before = self.check_fuseki_status()
                print(f"Importer Fuseki status: {status_before}", flush=True)

                if not status_before["available"]:
                    print("Importer step: trying to start Fuseki", flush=True)
                    start_result = self.start_fuseki()
                    print(f"Importer Fuseki start result: {start_result}", flush=True)

                print("Importer step: reading design, data, and ontology", flush=True)
                print(f"Importer design characters: {len(self.read_design_text())}", flush=True)
                print(f"Importer source characters: {len(self.read_source_data())}", flush=True)
                print(f"Importer ontology terms: {self.inspect_ontology()}", flush=True)

                print("Importer step: running iterative instance import", flush=True)
                import_result = self.run_iterative_import()
                print(f"Importer result: {import_result}", flush=True)

                print("Importer step: persisting and loading instances", flush=True)
                load_result = self.persist_and_load_instances()
                print(f"Importer load result: {load_result}", flush=True)

            if self.last_import is None or self.last_load_target is None:
                raise RuntimeError("Importer workflow ended before instance persistence completed.")
            result = ImporterWorkflowResult(
                instances_path=str(self.settings.instances_path),
                combined_path=str(self.settings.combined_path),
                triple_count=len(self.last_import.graph),
                combined_triple_count=self.last_combined_triple_count or 0,
                load_target=self.last_load_target,
                fuseki_status=self.fuseki_manager.status(),
                fuseki_stop_result={},
            )
        finally:
            self.last_stop_result = self.stop_fuseki_if_started()
            print(f"Importer Fuseki stop result: {self.last_stop_result}", flush=True)
            _active_workflow = None
        result.fuseki_stop_result = self.last_stop_result
        return result

    def run_sync(self) -> ImporterWorkflowResult:
        return self.run()

    def check_fuseki_status(self) -> dict[str, Any]:
        return self.fuseki_manager.status()

    def start_fuseki(self) -> dict[str, Any]:
        result = self.fuseki_manager.start()
        return {
            "status": result.status,
            "message": result.message,
            "pid": result.pid,
        }

    def stop_fuseki_if_started(self) -> dict[str, Any]:
        result = self.fuseki_manager.stop_if_started()
        return {
            "status": result.status,
            "message": result.message,
            "pid": result.pid,
        }

    def read_design_text(self) -> str:
        return read_text(self.settings.design_doc_path)

    def read_source_data(self) -> str:
        return load_project_data(self.settings.data_dir)

    def inspect_ontology(self) -> dict[str, Any]:
        ontology_graph, source = self.load_ontology_graph_for_import()
        terms = inspect_ontology_terms(ontology_graph)
        return {
            "source": source,
            "class_count": len(terms.classes),
            "property_count": len(terms.properties),
            "classes": [str(term) for term in sorted(terms.classes, key=str)],
            "properties": [str(term) for term in sorted(terms.properties, key=str)],
        }

    def run_iterative_import(self) -> dict[str, Any]:
        ontology_graph, ontology_source = self.load_ontology_graph_for_import()
        ontology_turtle = serialize_graph(ontology_graph)
        self.last_import = ImporterAgent(
            model=self.settings.llm_model,
            timeout_seconds=self.settings.llm_timeout_seconds,
        ).run(
            design_text=self.read_design_text(),
            ontology_turtle=ontology_turtle,
            ontology_graph=ontology_graph,
            source_data=self.read_source_data(),
            max_attempts=self.settings.importer_iterations,
        )
        return {
            "status": "success",
            "triple_count": len(self.last_import.graph),
            "iterations_allowed": self.settings.importer_iterations,
            "ontology_source": ontology_source,
        }

    def load_ontology_graph_for_import(self) -> tuple[Graph, str]:
        if self.fuseki_client.is_available():
            try:
                graph = self.read_ontology_graph_from_fuseki()
                if graph:
                    return graph, "fuseki"
            except Exception as exc:
                print(f"Importer Fuseki ontology inspection failed: {exc}", flush=True)

        graph = load_graph(self.settings.ontology_path)
        if self.fuseki_client.is_available() and graph:
            self.fuseki_client.replace_graph(
                self.settings.ontology_graph_uri,
                serialize_graph(graph),
            )
            return graph, "file_loaded_to_fuseki"
        return graph, "file"

    def read_ontology_graph_from_fuseki(self) -> Graph:
        turtle = self.fuseki_client.construct_turtle(
            f"""
            CONSTRUCT {{ ?s ?p ?o }}
            WHERE {{
              GRAPH <{self.settings.ontology_graph_uri}> {{
                ?s ?p ?o .
              }}
            }}
            """
        )
        if not turtle.strip():
            return Graph()
        return parse_turtle(turtle)

    def persist_and_load_instances(self) -> dict[str, Any]:
        if self.last_import is None:
            raise RuntimeError("No imported instance graph is available to persist.")
        self.last_load_target = load_graph_to_fuseki_or_file(
            client=self.fuseki_client,
            graph_uri=self.settings.data_graph_uri,
            graph=self.last_import.graph,
            path=self.settings.instances_path,
        )
        combined_graph = combine_turtle_files(
            [self.settings.ontology_path, self.settings.instances_path],
            self.settings.combined_path,
        )
        self.last_combined_triple_count = len(combined_graph)
        return {
            "status": "success",
            "instances_path": str(self.settings.instances_path),
            "combined_path": str(self.settings.combined_path),
            "triple_count": len(self.last_import.graph),
            "combined_triple_count": self.last_combined_triple_count,
            "load_target": self.last_load_target,
        }


def _workflow() -> ImporterWorkflow:
    if _active_workflow is None:
        raise RuntimeError("No active importer workflow is registered.")
    return _active_workflow


@function_tool
def read_design_text() -> str:
    """Read the generated semantic web design document."""
    return _workflow().read_design_text()


@function_tool
def read_source_data() -> str:
    """Read structured and unstructured project source data."""
    return _workflow().read_source_data()


@function_tool
def inspect_ontology() -> dict[str, Any]:
    """Inspect ontology classes and properties available for instance import."""
    return _workflow().inspect_ontology()


@function_tool
def run_iterative_import() -> dict[str, Any]:
    """Run the direct OpenAI instance import call with validation and retry iterations."""
    return _workflow().run_iterative_import()


@function_tool
def persist_and_load_instances() -> dict[str, Any]:
    """Write instances and combined graph, then load instances into Fuseki or local fallback."""
    return _workflow().persist_and_load_instances()
