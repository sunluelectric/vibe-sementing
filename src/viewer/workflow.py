from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from agents import Agent, function_tool

from src.common.config import Settings, get_settings
from src.common.files import read_text
from src.common.fuseki import client_from_settings
from src.common.fuseki_manager import FusekiManager
from src.viewer.agent import ViewerAgent, ViewerAnswer
from src.viewer.chat import ChatStore, format_history
from src.viewer.plot import ViewerPlotService
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
        self.fuseki_manager = FusekiManager(
            fuseki_home=self.settings.fuseki_home,
            fuseki_run_dir=self.settings.fuseki_run_dir,
            fuseki_data_dir=self.settings.fuseki_data_dir,
            fuseki_log_path=self.settings.fuseki_log_path,
            dataset=self.settings.fuseki_dataset,
            client=self.fuseki_client,
            start_timeout_seconds=self.settings.fuseki_start_timeout_seconds,
        )
        self.query_service = ViewerQueryService(self.settings, self.fuseki_client)
        self.plot_service = ViewerPlotService(self.settings)
        self.chat_store = ChatStore(self.settings.viewer_chat_dir)
        self.last_fuseki_start_result: dict[str, Any] | None = None
        self.last_fuseki_stop_result: dict[str, Any] | None = None

    def build_agent(self) -> Agent:
        return Agent(
            name="Vibe Semanting Viewer Workflow Agent",
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

    def answer_question(self, question: str, session_id: str | None = None) -> ViewerWorkflowResult:
        history = ""
        if session_id:
            history = format_history(self.chat_store.read_messages(session_id))
        result = ViewerAgent(
            model=self.settings.llm_model,
            timeout_seconds=self.settings.llm_timeout_seconds,
        ).answer(question, self.query_service, history=history, design_text=self.read_design_reference())
        if session_id:
            self.chat_store.append_turn(
                session_id=session_id,
                question=result.question,
                answer=result.answer,
                facts=result.facts,
            )
        return ViewerWorkflowResult(
            question=result.question,
            answer=result.answer,
            facts=result.facts,
        )

    def create_chat_session(self) -> dict[str, object]:
        session = self.chat_store.create_session()
        return asdict(session)

    def chat_history(self, session_id: str) -> dict[str, object]:
        return {
            "session_id": session_id,
            "messages": [asdict(message) for message in self.chat_store.read_messages(session_id)],
        }

    def graph_status(self) -> dict[str, Any]:
        return asdict(self.query_service.status())

    def start_fuseki_if_needed(self) -> dict[str, Any]:
        result = self.fuseki_manager.start()
        self.last_fuseki_start_result = {
            "status": result.status,
            "message": result.message,
            "pid": result.pid,
        }
        return self.last_fuseki_start_result

    def stop_fuseki_if_started(self) -> dict[str, Any]:
        result = self.fuseki_manager.stop_if_started()
        self.last_fuseki_stop_result = {
            "status": result.status,
            "message": result.message,
            "pid": result.pid,
        }
        return self.last_fuseki_stop_result

    def graph_summary(self) -> dict[str, object]:
        return self.query_service.graph_summary()

    def run_select(self, sparql: str) -> list[dict[str, str]]:
        return self.query_service.select(sparql)

    def search_facts(self, question: str) -> list[dict[str, str]]:
        return self.query_service.search_facts(question)

    def read_design_reference(self) -> str:
        if not self.settings.design_doc_path.exists():
            return ""
        return read_text(self.settings.design_doc_path)

    def export_turtle(self) -> str:
        return self.query_service.export_turtle()

    def plot_html(self) -> str:
        return self.plot_service.render_turtle(self.export_turtle())


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
