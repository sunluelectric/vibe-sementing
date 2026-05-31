from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import Agent, function_tool, trace

from src.common.config import Settings, get_settings
from src.common.files import load_project_data, read_text, write_text
from src.common.fuseki import client_from_settings, load_graph_to_fuseki_or_file
from src.common.fuseki_manager import FusekiManager
from src.designer.agent import DesignerAgent, DesignResult


_active_workflow: "DesignerWorkflow | None" = None


@dataclass
class DesignerWorkflowResult:
    design_path: str
    ontology_path: str
    triple_count: int
    load_target: str
    fuseki_status: dict[str, Any]
    fuseki_stop_result: dict[str, Any]


class DesignerWorkflow:
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
        self.last_design: DesignResult | None = None
        self.last_load_target: str | None = None
        self.last_stop_result: dict[str, Any] | None = None

    def build_agent(self) -> Agent:
        return Agent(
            name="Semantic Web Designer Workflow Agent",
            instructions=(
                "You orchestrate semantic web design and implementation for Apache Jena Fuseki. "
                "Follow this sequence: check Fuseki status, try to start Fuseki if needed, "
                "run iterative semantic web design, persist the design and ontology, load the "
                "ontology into Fuseki or local fallback, then report the final status. "
                "Do not manually write ontology content yourself; use the provided tools."
            ),
            model=self.settings.llm_model,
            tools=[
                check_fuseki_status,
                start_fuseki,
                run_iterative_design,
                persist_and_load_ontology,
            ],
        )

    def run(self) -> DesignerWorkflowResult:
        global _active_workflow
        _active_workflow = self
        result: DesignerWorkflowResult | None = None
        try:
            self.build_agent()
            with trace("Semantic Web Designer Workflow"):
                print("Designer step: checking Fuseki status", flush=True)
                status_before = self.check_fuseki_status()
                print(f"Designer Fuseki status: {status_before}", flush=True)

                if not status_before["available"]:
                    print("Designer step: trying to start Fuseki", flush=True)
                    start_result = self.start_fuseki()
                    print(f"Designer Fuseki start result: {start_result}", flush=True)

                print("Designer step: running iterative semantic web design", flush=True)
                design_result = self.run_iterative_design()
                print(f"Designer design result: {design_result}", flush=True)

                print("Designer step: persisting and loading ontology", flush=True)
                load_result = self.persist_and_load_ontology()
                print(f"Designer load result: {load_result}", flush=True)

            if self.last_design is None or self.last_load_target is None:
                raise RuntimeError("Designer workflow ended before ontology persistence completed.")
            result = DesignerWorkflowResult(
                design_path=str(self.settings.design_doc_path),
                ontology_path=str(self.settings.ontology_path),
                triple_count=len(self.last_design.graph),
                load_target=self.last_load_target,
                fuseki_status=self.fuseki_manager.status(),
                fuseki_stop_result={},
            )
        finally:
            self.last_stop_result = self.stop_fuseki_if_started()
            print(f"Designer Fuseki stop result: {self.last_stop_result}", flush=True)
            _active_workflow = None
        result.fuseki_stop_result = self.last_stop_result
        return result

    def run_sync(self) -> DesignerWorkflowResult:
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

    def run_iterative_design(self) -> dict[str, Any]:
        requirements = read_text(self.settings.design_requirements_path)
        data = load_project_data(self.settings.data_dir)
        self.last_design = DesignerAgent(
            model=self.settings.llm_model,
            timeout_seconds=self.settings.llm_timeout_seconds,
            ontology_namespace=self.settings.ontology_namespace,
        ).run(
            requirements=requirements,
            data=data,
            max_attempts=self.settings.designer_iterations,
            progress_path=self.settings.design_doc_path,
        )
        return {
            "status": "success",
            "triple_count": len(self.last_design.graph),
            "iterations_allowed": self.settings.designer_iterations,
        }

    def persist_and_load_ontology(self) -> dict[str, Any]:
        if self.last_design is None:
            raise RuntimeError("No design is available to persist.")
        design_markdown = self.last_design.design_markdown
        if self.last_design.progress_markdown:
            design_markdown = (
                f"{design_markdown}\n\n"
                "## Designer Generation Log\n\n"
                f"{self.last_design.progress_markdown}\n"
            )
        write_text(self.settings.design_doc_path, design_markdown + "\n")
        self.last_load_target = load_graph_to_fuseki_or_file(
            client=self.fuseki_client,
            graph_uri=self.settings.ontology_graph_uri,
            graph=self.last_design.graph,
            path=self.settings.ontology_path,
        )
        return {
            "status": "success",
            "design_path": str(self.settings.design_doc_path),
            "ontology_path": str(self.settings.ontology_path),
            "triple_count": len(self.last_design.graph),
            "load_target": self.last_load_target,
        }


def _workflow() -> DesignerWorkflow:
    if _active_workflow is None:
        raise RuntimeError("No active designer workflow is registered.")
    return _active_workflow


@function_tool
def check_fuseki_status() -> dict[str, Any]:
    """Check whether Apache Jena Fuseki is reachable."""
    return _workflow().check_fuseki_status()


@function_tool
def start_fuseki() -> dict[str, Any]:
    """Start Apache Jena Fuseki for the configured dataset if it is not reachable."""
    return _workflow().start_fuseki()


@function_tool
def run_iterative_design() -> dict[str, Any]:
    """Run the direct OpenAI semantic web design call with validation and retry iterations."""
    return _workflow().run_iterative_design()


@function_tool
def persist_and_load_ontology() -> dict[str, Any]:
    """Write design.md and ontology.ttl, then load the ontology into Fuseki or local fallback."""
    return _workflow().persist_and_load_ontology()
