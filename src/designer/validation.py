from __future__ import annotations

from dataclasses import dataclass

from rdflib import Graph, Namespace, RDF, RDFS, URIRef


DND = Namespace("http://example.org/dnd-adventure#")

REQUIRED_CLASSES = {
    "Adventure",
    "Quest",
    "Scene",
    "Location",
    "Character",
    "Npc",
    "Monster",
    "PlayerOption",
    "Item",
    "Weapon",
    "Encounter",
    "Check",
    "Reward",
    "VictoryCondition",
}

REQUIRED_PREFIXES = {
    "dnd": str(DND),
    "rdf": str(RDF),
    "rdfs": str(RDFS),
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]

    def raise_for_errors(self) -> None:
        if not self.ok:
            raise ValueError("; ".join(self.errors))


def validate_ontology_graph(graph: Graph) -> ValidationResult:
    errors: list[str] = []
    namespace_map = {prefix: str(namespace) for prefix, namespace in graph.namespaces()}

    for prefix, namespace in REQUIRED_PREFIXES.items():
        if namespace_map.get(prefix) != namespace:
            errors.append(f"Missing or incorrect prefix {prefix}: expected {namespace}")

    for class_name in sorted(REQUIRED_CLASSES):
        term = DND[class_name]
        if (term, RDF.type, RDFS.Class) not in graph:
            errors.append(f"Missing required class dnd:{class_name}")

    property_terms = set(graph.subjects(RDF.type, RDF.Property))
    for prop in sorted(property_terms, key=str):
        if (prop, RDFS.domain, None) not in graph:
            errors.append(f"Property {prop} is missing rdfs:domain")
        if (prop, RDFS.range, None) not in graph:
            errors.append(f"Property {prop} is missing rdfs:range")

    return ValidationResult(ok=not errors, errors=errors)
