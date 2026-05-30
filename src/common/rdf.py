from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph


FENCE_RE = re.compile(r"```(?:turtle|ttl)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_turtle(text: str) -> str:
    matches = FENCE_RE.findall(text)
    if matches:
        return matches[-1].strip()
    return text.strip()


def parse_turtle(turtle: str) -> Graph:
    graph = Graph()
    graph.parse(data=turtle, format="turtle")
    return graph


def load_graph(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def serialize_graph(graph: Graph) -> str:
    return graph.serialize(format="turtle")


def combine_turtle_files(paths: list[Path], destination: Path) -> Graph:
    graph = Graph()
    for path in paths:
        if path.exists() and path.stat().st_size:
            graph.parse(path, format="turtle")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(serialize_graph(graph), encoding="utf-8")
    return graph


def run_select(graph: Graph, query: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in graph.query(query):
        row_dict: dict[str, str] = {}
        for key, value in row.asdict().items():
            row_dict[str(key)] = str(value)
        rows.append(row_dict)
    return rows
