from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from rdflib import Namespace, RDF, RDFS

from src.common.config import get_settings
from src.common.rdf import parse_turtle
from src.common.semantic_search import (
    LocalEmbeddingProvider,
    SemanticIndex,
    chunks_from_data_dir,
    chunks_from_graph,
    select_context,
)


def test_semantic_search_chunks_markdown_text_and_csv(tmp_path) -> None:
    (tmp_path / "notes.md").write_text("# Harbor\n\nDocks and boats.", encoding="utf-8")
    (tmp_path / "plain.txt").write_text("Plain tide observations.", encoding="utf-8")
    (tmp_path / "table.csv").write_text("name,value\nBoat,Skiff\n", encoding="utf-8")

    chunks = chunks_from_data_dir(tmp_path)

    assert {chunk.kind for chunk in chunks} == {"md", "txt", "csv-profile"}
    assert any("Docks and boats" in chunk.text for chunk in chunks)
    assert any("Row 1: name: Boat" in chunk.text for chunk in chunks)


def test_semantic_search_chunks_pdf(tmp_path, monkeypatch) -> None:
    class Document:
        def __iter__(self):
            return iter([SimpleNamespace(get_text=lambda: "Bayesian inference notes.")])

        def close(self):
            pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "fitz",
        SimpleNamespace(open=lambda path: Document()),
    )
    (tmp_path / "notebook.pdf").write_bytes(b"%PDF fixture")

    chunks = chunks_from_data_dir(tmp_path)

    assert [chunk.kind for chunk in chunks] == ["pdf"]
    assert "Bayesian inference notes." in chunks[0].text


def test_local_semantic_index_ranks_matching_chunk_first() -> None:
    chunks = chunks_from_data_dir_fixture(
        {
            "harbor.md": "Harbor docks contain skiffs and tide tables.",
            "archive.md": "Invoices and procurement notes for office supplies.",
        }
    )

    results = SemanticIndex.from_chunks(chunks, LocalEmbeddingProvider()).search(
        "Which docks have skiffs?",
        top_k=1,
    )

    assert results[0].chunk.source == "harbor.md"


def test_select_context_respects_character_limit(tmp_path) -> None:
    (tmp_path / "large.md").write_text(
        "Harbor docks contain skiffs.\n\n" * 100
        + "Archive invoices are unrelated.\n\n" * 100,
        encoding="utf-8",
    )
    settings = replace(
        get_settings(),
        semantic_context_max_chars=500,
        semantic_search_top_k=1,
    )

    context = select_context(chunks_from_data_dir(tmp_path), "skiffs docks", settings)

    assert len(context) <= 500
    assert "skiffs" in context


def test_graph_chunks_include_readable_terms() -> None:
    sw = Namespace("http://example.org/semantic-web#")
    graph = parse_turtle(
        """
        @prefix sw: <http://example.org/semantic-web#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        sw:Record a rdfs:Class ;
          rdfs:label "Record" .
        sw:record1 a sw:Record ;
          rdfs:label "Record 1" .
        """
    )

    chunks = chunks_from_graph(graph)

    assert (sw.record1, RDF.type, sw.Record) in graph
    assert (sw.Record, RDFS.label, None) in graph
    assert any("Record 1" in chunk.text for chunk in chunks)


def chunks_from_data_dir_fixture(files: dict[str, str]):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        for name, content in files.items():
            (path / name).write_text(content, encoding="utf-8")
        return chunks_from_data_dir(path)
