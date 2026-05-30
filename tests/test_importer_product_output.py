from __future__ import annotations

import pytest
from rdflib import Graph, Namespace, RDF

from src.common.config import get_settings
from src.common.rdf import load_graph
from src.importer.validation import validate_instance_graph


def _load_current_output() -> tuple[Graph, Graph]:
    settings = get_settings()
    if not settings.ontology_path.exists() or not settings.instances_path.exists():
        pytest.skip("Generated ontology or instance output is not available.")
    ontology_graph = load_graph(settings.ontology_path)
    instance_graph = load_graph(settings.instances_path)
    dnd = Namespace("http://example.org/dnd-adventure#")
    if (dnd.Adventure, RDF.type, None) not in ontology_graph:
        pytest.skip("Current generated output is not the DnD sample ontology.")
    return ontology_graph, instance_graph


def test_current_importer_output_does_not_mutate_schema() -> None:
    ontology_graph, instance_graph = _load_current_output()

    validation = validate_instance_graph(instance_graph, ontology_graph)

    validation.raise_for_errors()


def test_current_importer_output_covers_dnd_sample_sources() -> None:
    _, graph = _load_current_output()
    dnd = Namespace("http://example.org/dnd-adventure#")

    assert len(set(graph.subjects(RDF.type, dnd.Npc))) >= 2
    assert len(set(graph.subjects(RDF.type, dnd.Monster))) >= 7
    assert len(set(graph.subjects(RDF.type, dnd.Scene))) >= 4
    assert len(set(graph.subjects(RDF.type, dnd.Check))) >= 4
    assert len(set(graph.subjects(RDF.type, dnd.Reward))) >= 2

    graph_text = graph.serialize(format="turtle")
    for expected in [
        "Aldric Thorn",
        "Elder Mira",
        "Grix",
        "Heirloom Dagger",
        "Healing Potion",
        "Gold Chest",
        "50",
        "100",
        "200",
    ]:
        assert expected in graph_text
