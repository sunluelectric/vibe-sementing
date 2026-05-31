from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from agents import Agent, function_tool, trace

from src.common.config import Settings, get_settings
from src.common.files import load_project_data, read_text
from src.common.files import write_text
from src.common.fuseki import client_from_settings, load_graph_to_fuseki_or_file
from src.common.fuseki_manager import FusekiManager
from rdflib import Graph

from src.common.rdf import combine_turtle_files, load_graph, parse_turtle, serialize_graph
from src.common.semantic_search import SemanticChunk, chunks_from_data_dir, chunks_from_graph, select_context
from src.importer.csv_import import csv_profiles_for_prompt, generate_csv_instances, validate_csv_import_plan
from src.importer.agent import ImporterAgent, ImportFocus, ImportResult
from src.importer.validation import inspect_ontology_terms
from src.importer.validation import validate_instance_graph


_active_workflow: "ImporterWorkflow | None" = None


@dataclass
class ImporterWorkflowResult:
    instances_path: str
    combined_path: str
    triple_count: int
    combined_triple_count: int
    load_target: str
    retrieval_summary: dict[str, Any]
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
        self.last_retrieval_summary: dict[str, Any] = {}

    def record_import_progress(self, entry: str) -> None:
        existing = ""
        if self.settings.import_doc_path.exists():
            existing = self.settings.import_doc_path.read_text(encoding="utf-8").strip()
        content = f"{existing}\n\n{entry.strip()}" if existing else entry.strip()
        write_text(self.settings.import_doc_path, content + "\n")

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
                retrieve_import_context,
                retrieve_schema_context,
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
                self.start_import_progress_log()
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
                retrieval_summary=self.last_retrieval_summary,
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

    def read_source_data(self, include_csv: bool = True) -> str:
        return load_project_data(self.settings.data_dir, include_csv=include_csv)

    def retrieve_import_context(self, query: str | None = None, include_csv: bool = True) -> str:
        full_data = self.read_source_data(include_csv=include_csv)
        if not self.settings.semantic_search_enabled:
            self.last_retrieval_summary["source"] = {
                "used": False,
                "reason": "disabled",
                "full_context_chars": len(full_data),
                "context_chars": len(full_data),
            }
            return full_data
        if len(full_data) <= self.settings.semantic_context_max_chars:
            self.last_retrieval_summary["source"] = {
                "used": False,
                "reason": "below_threshold",
                "full_context_chars": len(full_data),
                "context_chars": len(full_data),
                "max_chars": self.settings.semantic_context_max_chars,
            }
            return full_data
        chunks = chunks_from_data_dir(self.settings.data_dir, include_csv=include_csv)
        search_query = query or self.read_design_text()
        context = select_context(chunks, search_query, self.settings)
        selected = context or full_data[: self.settings.semantic_context_max_chars]
        self.last_retrieval_summary["source"] = {
            "used": True,
            "reason": "above_threshold",
            "full_context_chars": len(full_data),
            "context_chars": len(selected),
            "chunk_count": len(chunks),
            "top_k": self.settings.semantic_search_top_k,
            "max_chars": self.settings.semantic_context_max_chars,
        }
        return selected

    def retrieve_schema_context(self, query: str | None = None) -> str:
        ontology_graph, _source = self.load_ontology_graph_for_import()
        ontology_turtle = serialize_graph(ontology_graph)
        if not self.settings.semantic_search_enabled:
            self.last_retrieval_summary["schema"] = {
                "used": False,
                "reason": "disabled",
                "full_context_chars": len(ontology_turtle),
                "context_chars": len(ontology_turtle),
            }
            return ontology_turtle
        if len(ontology_turtle) <= self.settings.semantic_context_max_chars:
            self.last_retrieval_summary["schema"] = {
                "used": False,
                "reason": "below_threshold",
                "full_context_chars": len(ontology_turtle),
                "context_chars": len(ontology_turtle),
                "max_chars": self.settings.semantic_context_max_chars,
            }
            return ontology_turtle
        chunks = chunks_from_graph(ontology_graph, source="ontology")
        search_query = query or self.retrieve_import_context()
        context = select_context(chunks, search_query, self.settings)
        selected = context or ontology_turtle[: self.settings.semantic_context_max_chars]
        self.last_retrieval_summary["schema"] = {
            "used": True,
            "reason": "above_threshold",
            "full_context_chars": len(ontology_turtle),
            "context_chars": len(selected),
            "chunk_count": len(chunks),
            "top_k": self.settings.semantic_search_top_k,
            "max_chars": self.settings.semantic_context_max_chars,
        }
        return selected

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
        agent = ImporterAgent(
            model=self.settings.llm_model,
            timeout_seconds=self.settings.llm_timeout_seconds,
        )
        csv_graph = self.run_csv_import(agent, ontology_graph)
        unstructured_graph = Graph()
        include_csv_in_llm_import = not bool(csv_graph)
        if self.has_unstructured_sources() or include_csv_in_llm_import:
            if self.should_use_iterative_import(ontology_graph, include_csv=include_csv_in_llm_import):
                unstructured_import = self.run_iterative_retrieval_import(
                    agent=agent,
                    ontology_graph=ontology_graph,
                    include_csv=include_csv_in_llm_import,
                )
            else:
                source_data = self.retrieve_import_context(include_csv=include_csv_in_llm_import)
                ontology_turtle = self.retrieve_schema_context(source_data)
                unstructured_import = agent.run(
                    design_text=self.read_design_text(),
                    ontology_turtle=ontology_turtle,
                    ontology_graph=ontology_graph,
                    source_data=source_data,
                    max_attempts=self.settings.importer_iterations,
                    progress_path=self.settings.import_doc_path,
                    reset_progress=False,
                )
            unstructured_graph = unstructured_import.graph
        merged_graph = Graph()
        for triple in csv_graph:
            merged_graph.add(triple)
        for triple in unstructured_graph:
            merged_graph.add(triple)
        validate_instance_graph(merged_graph, ontology_graph).raise_for_errors()
        self.last_import = ImportResult(
            instances_turtle=serialize_graph(merged_graph),
            graph=merged_graph,
            progress_markdown=agent._progress_markdown(),
        )
        result = {
            "status": "success",
            "triple_count": len(self.last_import.graph),
            "iterations_allowed": self.settings.importer_iterations,
            "ontology_source": ontology_source,
        }
        self.record_import_progress(
            "## Import Generation Summary\n\n"
            f"- Status: success\n"
            f"- Triple count: {len(self.last_import.graph)}\n"
            f"- Ontology source: {ontology_source}\n"
            f"- Retrieval summary: `{self.last_retrieval_summary}`\n"
        )
        return result

    def run_csv_import(self, agent: ImporterAgent, ontology_graph: Graph) -> Graph:
        csv_profiles = csv_profiles_for_prompt(self.settings.data_dir)
        if not csv_profiles:
            self.last_retrieval_summary["csv"] = {"used": False, "reason": "no_csv_files"}
            return Graph()
        feedback = ""
        plan = None
        for attempt in range(1, self.settings.importer_iterations + 1):
            plan = agent.plan_csv_import(
                design_text=self.read_design_text(),
                ontology_graph=ontology_graph,
                csv_profiles=csv_profiles,
                max_attempts=1,
                progress_path=self.settings.import_doc_path,
                validation_feedback=feedback,
            )
            validation = validate_csv_import_plan(plan, ontology_graph, self.settings.data_dir)
            if validation.ok:
                break
            feedback = f"Attempt {attempt} failed validation: {'; '.join(validation.errors)}"
            agent._record_progress(
                self.settings.import_doc_path,
                "## CSV Mapping Validation\n\n"
                f"- Status: failed\n"
                f"- Attempt: {attempt}\n"
                f"- Feedback: {feedback}\n"
            )
        if plan is None:
            raise RuntimeError("CSV mapping planning did not produce a plan.")
        validate_csv_import_plan(plan, ontology_graph, self.settings.data_dir).raise_for_errors()
        graph = generate_csv_instances(plan, ontology_graph, self.settings.data_dir)
        self.last_retrieval_summary["csv"] = {
            "used": True,
            "mapping_count": len(plan.mappings),
            "triple_count": len(graph),
        }
        agent._record_progress(
            self.settings.import_doc_path,
            "## Deterministic CSV Import\n\n"
            f"- Status: success\n"
            f"- Mapping count: {len(plan.mappings)}\n"
            f"- Triple count: {len(graph)}\n"
        )
        return graph

    def has_unstructured_sources(self) -> bool:
        return any(
            path.is_file() and path.suffix.lower() in {".md", ".txt", ".pdf"}
            for path in self.settings.data_dir.glob("*")
        )

    def start_import_progress_log(self) -> None:
        write_text(
            self.settings.import_doc_path,
            "# Semantic Web Importer Progress\n\n"
            f"- Model: `{self.settings.llm_model}`\n"
            f"- Mode: `{self.settings.semantic_web_mode}`\n"
            f"- Max validation attempts per generation: {self.settings.importer_iterations}\n"
            f"- Semantic search enabled: {self.settings.semantic_search_enabled}\n"
            f"- Semantic search provider: `{self.settings.semantic_search_provider}`\n"
            f"- Semantic context max chars: {self.settings.semantic_context_max_chars}\n"
            f"- Importer retrieval batch limit: {self.settings.importer_retrieval_batches}\n"
            f"- Importer slice context max chars: {self.settings.importer_slice_context_max_chars}\n",
        )

    def should_use_iterative_import(self, ontology_graph: Graph, include_csv: bool = True) -> bool:
        if not self.settings.semantic_search_enabled:
            return False
        source_data = self.read_source_data(include_csv=include_csv)
        ontology_turtle = serialize_graph(ontology_graph)
        return (
            len(source_data) > self.settings.semantic_context_max_chars
            or len(ontology_turtle) > self.settings.semantic_context_max_chars
        )

    def run_iterative_retrieval_import(
        self,
        agent: ImporterAgent,
        ontology_graph: Graph,
        include_csv: bool = True,
    ) -> ImportResult:
        design_text = self.read_design_text()
        source_chunks = chunks_from_data_dir(self.settings.data_dir, include_csv=include_csv)
        schema_chunks = chunks_from_graph(ontology_graph, source="ontology")
        slice_settings = replace(
            self.settings,
            semantic_context_max_chars=self.settings.importer_slice_context_max_chars,
        )
        merged_graph = Graph()
        batch_summaries: list[dict[str, Any]] = []
        stop_reason = "batch_limit"
        for batch_number in range(1, self.settings.importer_retrieval_batches + 1):
            existing_summary = _instance_graph_summary(merged_graph)
            focus = agent.plan_import_focus(
                design_text=design_text,
                ontology_graph=ontology_graph,
                data_inventory=_data_inventory(source_chunks),
                existing_instances=existing_summary,
                progress_path=self.settings.import_doc_path,
            )
            if focus.complete:
                stop_reason = "model_complete"
                batch_summaries.append(
                    {
                        "batch": batch_number,
                        "complete": True,
                        "query": focus.query,
                        "purpose": focus.purpose,
                    }
                )
                break
            source_data = select_context(source_chunks, focus.query, slice_settings)
            ontology_turtle = select_context(schema_chunks, focus.query, slice_settings)
            self.record_import_progress(
                "## Import Batch Retrieval\n\n"
                f"- Batch: {batch_number}\n"
                f"- Query: {focus.query}\n"
                f"- Purpose: {focus.purpose}\n"
                f"- Source context characters: {len(source_data)}\n"
                f"- Schema context characters: {len(ontology_turtle)}\n"
            )
            slice_result = agent.generate_instance_slice(
                design_text=design_text,
                ontology_turtle=ontology_turtle,
                ontology_graph=ontology_graph,
                source_data=source_data,
                focus=focus,
                existing_instances=existing_summary,
                max_attempts=self.settings.importer_iterations,
                progress_path=self.settings.import_doc_path,
            )
            for triple in slice_result.graph:
                merged_graph.add(triple)
            validate_instance_graph(merged_graph, ontology_graph).raise_for_errors()
            batch_summaries.append(
                {
                    "batch": batch_number,
                    "complete": False,
                    "query": focus.query,
                    "purpose": focus.purpose,
                    "source_context_chars": len(source_data),
                    "schema_context_chars": len(ontology_turtle),
                    "slice_triples": len(slice_result.graph),
                    "merged_triples": len(merged_graph),
                }
            )
        if not merged_graph:
            source_data = self.retrieve_import_context(include_csv=include_csv)
            ontology_turtle = self.retrieve_schema_context(source_data)
            fallback = agent.run(
                design_text=design_text,
                ontology_turtle=ontology_turtle,
                ontology_graph=ontology_graph,
                source_data=source_data,
                max_attempts=self.settings.importer_iterations,
                progress_path=self.settings.import_doc_path,
                reset_progress=False,
            )
            self.last_retrieval_summary["iterative"] = {
                "used": False,
                "reason": "no_valid_slices_fallback",
                "stop_reason": stop_reason,
                "batches": batch_summaries,
            }
            return fallback
        validate_instance_graph(merged_graph, ontology_graph).raise_for_errors()
        self.last_retrieval_summary["iterative"] = {
            "used": True,
            "reason": "above_threshold",
            "stop_reason": stop_reason,
            "batch_limit": self.settings.importer_retrieval_batches,
            "batch_count": len([batch for batch in batch_summaries if not batch.get("complete")]),
            "source_chunk_count": len(source_chunks),
            "schema_chunk_count": len(schema_chunks),
            "batches": batch_summaries,
        }
        return ImportResult(
            instances_turtle=serialize_graph(merged_graph),
            graph=merged_graph,
            progress_markdown=agent._progress_markdown(),
        )

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
        result = {
            "status": "success",
            "instances_path": str(self.settings.instances_path),
            "combined_path": str(self.settings.combined_path),
            "triple_count": len(self.last_import.graph),
            "combined_triple_count": self.last_combined_triple_count,
            "load_target": self.last_load_target,
        }
        self.record_import_progress(
            "## Import Persistence Summary\n\n"
            f"- Status: success\n"
            f"- Instances path: `{self.settings.instances_path}`\n"
            f"- Combined path: `{self.settings.combined_path}`\n"
            f"- Instance triples: {len(self.last_import.graph)}\n"
            f"- Combined triples: {self.last_combined_triple_count}\n"
            f"- Load target: {self.last_load_target}\n"
        )
        return result


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
def retrieve_import_context(query: str = "") -> str:
    """Retrieve source-data context relevant to instance import."""
    return _workflow().retrieve_import_context(query or None)


@function_tool
def retrieve_schema_context(query: str = "") -> str:
    """Retrieve ontology context relevant to instance import."""
    return _workflow().retrieve_schema_context(query or None)


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


def _data_inventory(chunks: list[SemanticChunk]) -> str:
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        preview = " ".join(chunk.text.split())[:350]
        lines.append(
            f"{index}. source={chunk.source}; kind={chunk.kind}; "
            f"characters={len(chunk.text)}; preview={preview}"
        )
    return "\n".join(lines)


def _instance_graph_summary(graph: Graph) -> str:
    if not graph:
        return "- No instances imported yet."
    rows: list[str] = []
    for index, subject in enumerate(sorted(set(graph.subjects()), key=str), start=1):
        if index > 80:
            rows.append("- Additional instances omitted from summary.")
            break
        predicates = sorted(
            {
                _local_name(str(predicate))
                for predicate, _object_value in graph.predicate_objects(subject)
            }
        )
        rows.append(f"- {subject}: {', '.join(predicates)}")
    return "\n".join(rows)


def _local_name(uri: str) -> str:
    if "#" in uri:
        return uri.rsplit("#", 1)[1]
    return uri.rstrip("/").rsplit("/", 1)[-1]
