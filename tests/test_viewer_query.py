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
        if "rdfs:Class" in sparql and "?class" in sparql:
            return [{"class": "http://example.org/schema#Scene", "label": "Scene"}]
        return [{"instance": "http://example.org/instances#scene1", "label": "Cave Entrance"}]

    def construct_turtle(self, sparql: str) -> str:
        self.constructed.append(sparql)
        return "@prefix ex: <http://example.org/> .\nex:s ex:p ex:o .\n"


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
    turtle = service.export_turtle()

    assert classes[0]["label"] == "Scene"
    assert instances[0]["label"] == "Scene"
    assert count == 11
    assert "CONSTRUCT" in client.constructed[0]
    assert "GRAPH ?graph" in client.selected[0]
    assert "GRAPH ?schemaGraph" in client.selected[-1]
    assert turtle.startswith("@prefix")


def test_viewer_query_select_fails_when_fuseki_unavailable() -> None:
    service = ViewerQueryService(get_settings(), FakeFusekiClient(available=False))

    with pytest.raises(FusekiUnavailable):
        service.select("SELECT * WHERE { ?s ?p ?o }")


def test_viewer_fuseki_smoke_queries_when_available() -> None:
    settings = get_settings()
    client = client_from_settings(settings)
    if not client.is_available():
        pytest.skip("Fuseki is not available.")

    service = ViewerQueryService(settings, client)
    status = service.status()

    assert status.available
    assert status.triple_count is not None
