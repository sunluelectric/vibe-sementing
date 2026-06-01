from __future__ import annotations

import pytest

from src.common.config import get_settings
from src.common.fuseki import FusekiUnavailable, client_from_settings
from src.viewer.query import ViewerQueryService


class FakeFusekiClient:
    query_url = "http://example.invalid/query"

    def __init__(self, available: bool = True):
        self.available = available
        self.selected: list[str] = []
        self.constructed: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def select(self, sparql: str) -> list[dict[str, str]]:
        self.selected.append(sparql)
        if "COUNT(DISTINCT ?instance)" in sparql:
            return [{"count": "11"}]
        if "COUNT(*)" in sparql:
            return [{"count": "12"}]
        if "subjectLabel" in sparql and "CONTAINS(LCASE" in sparql:
            return [
                {
                    "subject": "http://example.org/instances#scene1",
                    "subjectLabel": "Cave Entrance",
                    "predicateLabel": "name",
                    "object": "Cave Entrance",
                }
            ]
        if "rdfs:Class" in sparql and "?class" in sparql:
            return [{"class": "http://example.org/schema#Scene", "label": "Scene"}]
        return [{"instance": "http://example.org/instances#scene1", "label": "Cave Entrance"}]

    def construct_turtle(self, sparql: str) -> str:
        self.constructed.append(sparql)
        return "@prefix ex: <http://example.org/> .\nex:s ex:p ex:o .\n"


class GraphSliceFusekiClient(FakeFusekiClient):
    def select(self, sparql: str) -> list[dict[str, str]]:
        self.selected.append(sparql)
        if "fuseki-term-index" in sparql:
            return []
        if "SELECT DISTINCT ?term" in sparql:
            return [
                {
                    "term": "http://example.org/semantic-web/instance/graphdb",
                    "label": "GraphDB",
                    "comment": "Triplestore product.",
                    "kind": "labeled-resource",
                    "text": "GraphDB maintainer and license",
                },
                {
                    "term": "http://example.org/semantic-web#license",
                    "label": "license",
                    "comment": "Software license.",
                    "kind": "property",
                    "text": "license",
                },
            ]
        if "VALUES ?candidate" in sparql:
            return [
                {
                    "subject": "http://example.org/semantic-web/instance/graphdb",
                    "subjectLabel": "GraphDB",
                    "predicate": "http://example.org/semantic-web#license",
                    "predicateLabel": "license",
                    "object": "Commercial / Free Edition",
                }
            ]
        return super().select(sparql)


def test_viewer_query_status_requires_fuseki() -> None:
    service = ViewerQueryService(get_settings(), FakeFusekiClient(available=False))

    status = service.status()

    assert not status.available
    assert status.triple_count is None
    assert "requires Fuseki" in status.message


def test_viewer_query_status_reports_fuseki_triples() -> None:
    service = ViewerQueryService(get_settings(), FakeFusekiClient())

    status = service.status()

    assert status.available
    assert status.triple_count == 12


def test_viewer_query_helpers_execute_named_graph_queries() -> None:
    client = FakeFusekiClient()
    service = ViewerQueryService(get_settings(), client)

    classes = service.classes()
    instances = service.class_instances_by_label("Scene")
    count = service.class_instance_count_by_label("Scene")
    subject_facts = service.subject_facts_matching_question_labels("Tell me about Cave Entrance")
    turtle = service.export_turtle()

    assert classes[0]["label"] == "Scene"
    assert instances[0]["label"] == "Scene"
    assert count == 11
    assert subject_facts[0]["subjectLabel"] == "Cave Entrance"
    assert "CONSTRUCT" in client.constructed[0]
    assert "GRAPH ?graph" in client.selected[0]
    assert any("GRAPH ?schemaGraph" in query for query in client.selected)
    assert turtle.startswith("@prefix")


def test_viewer_query_select_fails_when_fuseki_unavailable() -> None:
    service = ViewerQueryService(get_settings(), FakeFusekiClient(available=False))

    with pytest.raises(FusekiUnavailable):
        service.select("SELECT * WHERE { ?s ?p ?o }")


def test_viewer_semantic_search_facts_uses_fuseki_graph_slice() -> None:
    client = GraphSliceFusekiClient()
    service = ViewerQueryService(get_settings(), client)

    rows = service.semantic_search_facts("What is the GraphDB license?")

    assert rows[0]["subjectLabel"] == "GraphDB"
    assert any("SELECT DISTINCT ?term" in query for query in client.selected)
    assert any("VALUES ?candidate" in query for query in client.selected)


def test_viewer_fuseki_smoke_queries_when_available() -> None:
    settings = get_settings()
    client = client_from_settings(settings)
    if not client.is_available():
        pytest.skip("Fuseki is not available.")

    service = ViewerQueryService(settings, client)
    status = service.status()

    assert status.available
    assert status.triple_count is not None
