from __future__ import annotations

from dataclasses import replace

from src.common.config import get_settings
from src.common.rdf import parse_turtle
from src.designer.agent import DesignFocus, DesignResult
from src.designer.workflow import DesignerWorkflow
from tests.test_designer_contract import VALID_DESIGN_RESPONSE
from src.common.llm import parse_json_object


def test_designer_workflow_builds_agents_sdk_shell() -> None:
    workflow = DesignerWorkflow()

    agent = workflow.build_agent()

    assert agent.name == "Semantic Web Designer Workflow Agent"
    assert {tool.name for tool in agent.tools} == {
        "check_fuseki_status",
        "start_fuseki",
        "retrieve_design_context",
        "run_iterative_design",
        "persist_and_load_ontology",
    }


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
    settings = replace(
        get_settings(),
        design_doc_path=tmp_path / "design.md",
        ontology_path=tmp_path / "ontology.ttl",
        db_dir=tmp_path,
    )
    return DesignerWorkflow(settings)


def _valid_design_result() -> DesignResult:
    payload = parse_json_object(VALID_DESIGN_RESPONSE)
    turtle = payload["ontology_turtle"]
    return DesignResult(
        design_markdown=payload["design_markdown"],
        ontology_turtle=turtle,
        graph=parse_turtle(turtle),
    )


def test_designer_persistence_writes_design_and_turtle_fallback(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    workflow.fuseki_client = OfflineFusekiClient()
    workflow.last_design = _valid_design_result()

    result = workflow.persist_and_load_ontology()

    assert result["load_target"] == "file"
    assert workflow.settings.design_doc_path.read_text(encoding="utf-8").startswith("# Test Design")
    assert len(parse_turtle(workflow.settings.ontology_path.read_text(encoding="utf-8"))) >= 20


def test_designer_persistence_loads_fuseki_when_available(tmp_path) -> None:
    workflow = _workflow_with_temp_paths(tmp_path)
    client = OnlineFusekiClient()
    workflow.fuseki_client = client
    workflow.last_design = _valid_design_result()

    result = workflow.persist_and_load_ontology()

    assert result["load_target"] == "fuseki"
    assert len(client.loaded) == 1
    graph_uri, turtle = client.loaded[0]
    assert graph_uri == workflow.settings.ontology_graph_uri
    assert len(parse_turtle(turtle)) >= 20


def test_designer_retrieves_context_for_large_data(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "places.md").write_text(
        "# Places\n\n"
        + "Harbor records describe docks, boats, and tides.\n\n" * 200
        + "Archive records describe invoices and unrelated accounting.\n\n" * 200,
        encoding="utf-8",
    )
    requirements = tmp_path / "design-requirements.md"
    requirements.write_text("Design an ontology for harbor docks and boats.", encoding="utf-8")
    settings = replace(
        get_settings(),
        data_dir=data_dir,
        design_requirements_path=requirements,
        semantic_context_max_chars=900,
        semantic_search_top_k=2,
    )
    workflow = DesignerWorkflow(settings)

    context = workflow.retrieve_design_context("harbor docks boats tides")

    assert len(context) <= 900
    assert "Harbor records" in context
    assert "Source chunk: places.md" in context
    assert workflow.last_retrieval_summary["used"] is True
    assert workflow.last_retrieval_summary["chunk_count"] > 1


def test_designer_iterative_retrieval_uses_model_planned_focuses(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "world.md").write_text(
        "# World\n\n"
        + "Harbor scenes include docks, boats, tides, and exits.\n\n" * 120
        + "Character notes include captains, merchants, and relationships.\n\n" * 120,
        encoding="utf-8",
    )
    requirements = tmp_path / "design-requirements.md"
    requirements.write_text("Design an ontology for scenes and characters.", encoding="utf-8")
    settings = replace(
        get_settings(),
        data_dir=data_dir,
        design_requirements_path=requirements,
        design_doc_path=tmp_path / "design.md",
        semantic_context_max_chars=1600,
        designer_slice_context_max_chars=700,
        semantic_search_top_k=1,
        designer_retrieval_focuses=2,
    )
    workflow = DesignerWorkflow(settings)

    class StubAgent:
        def __init__(self) -> None:
            self.slice_queries: list[str] = []

        def plan_focuses(self, requirements, data_inventory, max_focuses, progress_path=None):
            assert "source=world.md" in data_inventory
            return [
                DesignFocus("harbor scenes docks exits", "Model places."),
                DesignFocus("captains merchants relationships", "Model characters."),
            ]

        def draft_schema_slice(self, requirements, focus, context, progress_path=None):
            self.slice_queries.append(focus.query)
            assert len(context) <= 700
            return f"Notes for {focus.query}"

    agent = StubAgent()

    context = workflow.retrieve_design_context(
        "Design an ontology for scenes and characters.",
        agent=agent,
    )

    assert workflow.last_retrieval_summary["used"] is True
    assert workflow.last_retrieval_summary["iterative"] is True
    assert workflow.last_retrieval_summary["focus_count"] == 2
    assert agent.slice_queries == [
        "harbor scenes docks exits",
        "captains merchants relationships",
    ]
    assert "Retrieved Design Focus 1" in context
    assert "Schema Slice Notes" in context
    assert len(context) <= 1600
