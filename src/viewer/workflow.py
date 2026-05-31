from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from agents import Agent, function_tool

from src.common.config import Settings, get_settings
from src.common.fuseki import client_from_settings
from src.viewer.agent import ViewerAgent, ViewerAnswer
from src.viewer.query import ViewerQueryService


_active_workflow: "ViewerWorkflow | None" = None


@dataclass(frozen=True)
class ViewerWorkflowResult:
    question: str
    answer: str
    facts: list[dict[str, str]]


class ViewerWorkflow:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.fuseki_client = client_from_settings(self.settings)
        self.query_service = ViewerQueryService(self.settings, self.fuseki_client)

    def build_agent(self) -> Agent:
        return Agent(
            name="Semantic Web Viewer Workflow Agent",
            instructions=(
                "You answer semantic web questions by querying Fuseki through the "
                "provided tools. Fuseki is the runtime data source. Do not read local "
                "Turtle files as viewer data."
            ),
            model=self.settings.llm_model,
            tools=[
                get_graph_status,
                get_graph_summary,
                run_sparql_select,
                search_graph_facts,
            ],
        )

    def answer_question(self, question: str) -> ViewerWorkflowResult:
        result = ViewerAgent(
            model=self.settings.llm_model,
            timeout_seconds=self.settings.llm_timeout_seconds,
        ).answer(question, self.query_service)
        return ViewerWorkflowResult(
            question=result.question,
            answer=result.answer,
            facts=result.facts,
        )

    def graph_status(self) -> dict[str, Any]:
        return asdict(self.query_service.status())

    def graph_summary(self) -> dict[str, object]:
        return self.query_service.graph_summary()

    def run_select(self, sparql: str) -> list[dict[str, str]]:
        return self.query_service.select(sparql)

    def search_facts(self, question: str) -> list[dict[str, str]]:
        return self.query_service.search_facts(question)

    def export_turtle(self) -> str:
        return self.query_service.export_turtle()


def _workflow() -> ViewerWorkflow:
    if _active_workflow is None:
        raise RuntimeError("No active viewer workflow is registered.")
    return _active_workflow


@function_tool
def get_graph_status() -> dict[str, Any]:
    """Return Fuseki availability, query URL, and graph triple count."""
    return _workflow().graph_status()


@function_tool
def get_graph_summary() -> dict[str, object]:
    """Return a compact schema and sample-instance summary from Fuseki."""
    return _workflow().graph_summary()


@function_tool
def run_sparql_select(sparql: str) -> list[dict[str, str]]:
    """Run a SPARQL SELECT query against Fuseki."""
    return _workflow().run_select(sparql)


@function_tool
def search_graph_facts(question: str) -> list[dict[str, str]]:
    """Search Fuseki graph facts relevant to a natural language question."""
    return _workflow().search_facts(question)


def activate_workflow(workflow: ViewerWorkflow) -> None:
    global _active_workflow
    _active_workflow = workflow
