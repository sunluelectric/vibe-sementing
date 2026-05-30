from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests
from rdflib import Graph

from src.common.rdf import serialize_graph


class FusekiUnavailable(RuntimeError):
    """Raised when Fuseki cannot be reached."""


@dataclass
class FusekiClient:
    graph_store_url: str
    query_url: str
    update_url: str
    timeout_seconds: int = 10

    def is_available(self) -> bool:
        try:
            response = requests.post(
                self.query_url,
                data={"query": "ASK { ?s ?p ?o }"},
                headers={"Accept": "application/sparql-results+json"},
                timeout=self.timeout_seconds,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def replace_graph(self, graph_uri: str, turtle: str) -> None:
        response = requests.put(
            self.graph_store_url,
            params={"graph": graph_uri},
            data=turtle.encode("utf-8"),
            headers={"Content-Type": "text/turtle"},
            timeout=self.timeout_seconds,
        )
        if response.status_code not in {200, 201, 204}:
            raise FusekiUnavailable(
                f"Fuseki graph load failed with {response.status_code}: {response.text[:500]}"
            )

    def select(self, sparql: str) -> list[dict[str, str]]:
        response = requests.post(
            self.query_url,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise FusekiUnavailable(
                f"Fuseki query failed with {response.status_code}: {response.text[:500]}"
            )
        data = response.json()
        return [
            {key: value["value"] for key, value in row.items()}
            for row in data.get("results", {}).get("bindings", [])
        ]


def client_from_settings(settings) -> FusekiClient:
    return FusekiClient(
        graph_store_url=settings.graph_store_url,
        query_url=settings.sparql_query_url,
        update_url=settings.sparql_update_url,
    )


def load_graph_to_fuseki_or_file(
    client: FusekiClient, graph_uri: str, graph: Graph, path: Path
) -> str:
    turtle = serialize_graph(graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(turtle, encoding="utf-8")
    if not client.is_available():
        return "file"
    client.replace_graph(graph_uri, turtle)
    return "fuseki"
