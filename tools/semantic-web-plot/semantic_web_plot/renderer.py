from __future__ import annotations

import argparse
import webbrowser
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pyvis.network import Network
from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD


DEFAULT_INPUT = Path("semantic_web.ttl")
DEFAULT_OUTPUT = Path("output/ontology_graph.html")
DEFAULT_MAX_EDGES = 500

CLASS_TYPES = {OWL.Class, RDFS.Class}
PROPERTY_TYPES = {OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property}
GENERIC_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.Restriction,
    OWL.Ontology,
    RDFS.Class,
    RDF.Property,
}

NODE_CLASS = "class"
NODE_INDIVIDUAL = "individual"
NODE_OTHER = "other"

EDGE_SUBCLASS = "subClassOf"
EDGE_OBJECT_PROPERTY = "object_property"
EDGE_INSTANCE_OF = "instance_of"


@dataclass(frozen=True)
class SemanticEdge:
    source: URIRef
    target: URIRef
    label: str
    edge_type: str
    property_uri: URIRef | None = None


@dataclass(frozen=True)
class DataProperty:
    name: str
    range_type: str


@dataclass
class ExtractionResult:
    edges: list[SemanticEdge]
    data_properties: dict[URIRef, list[DataProperty]]
    classes: set[URIRef]
    individuals: set[URIRef]


@dataclass(frozen=True)
class RenderResult:
    input_label: str
    output_path: Path
    triple_count: int
    semantic_edge_count: int
    nodes_rendered: int
    edges_rendered: int
    edge_type_counts: dict[str, int]
    html: str


class SemanticWebPlotter:
    def __init__(self, max_edges: int = DEFAULT_MAX_EDGES, directed: bool = True):
        self.max_edges = max_edges
        self.directed = directed

    def render_turtle_text(self, turtle: str, output_path: Path, input_label: str = "Fuseki export") -> RenderResult:
        graph = Graph()
        graph.parse(data=turtle, format="turtle")
        return self.render_graph(graph, output_path, input_label=input_label)

    def render_turtle_file(self, input_path: Path, output_path: Path) -> RenderResult:
        graph = Graph()
        graph.parse(input_path, format="turtle")
        return self.render_graph(graph, output_path, input_label=str(input_path))

    def render_graph(self, graph: Graph, output_path: Path, input_label: str) -> RenderResult:
        result = extract_semantics(graph)
        nodes_rendered, edges_rendered = render_html(
            graph,
            result,
            output_path,
            max_edges=self.max_edges,
            directed=self.directed,
        )
        edge_counts = Counter(edge.edge_type for edge in result.edges[:edges_rendered])
        html = output_path.read_text(encoding="utf-8")
        return RenderResult(
            input_label=input_label,
            output_path=output_path,
            triple_count=len(graph),
            semantic_edge_count=len(result.edges),
            nodes_rendered=nodes_rendered,
            edges_rendered=edges_rendered,
            edge_type_counts=dict(sorted(edge_counts.items())),
            html=html,
        )


def is_named_uri(term: object) -> bool:
    return isinstance(term, URIRef)


def is_xsd_uri(term: URIRef) -> bool:
    return str(term).startswith(str(XSD))


def shorten_term(graph: Graph, term: object) -> str:
    if not isinstance(term, URIRef):
        return str(term)

    try:
        normalized = graph.namespace_manager.normalizeUri(term)
        if normalized and not normalized.startswith("<"):
            return normalized
    except Exception:
        pass

    text = str(term)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def expand_union_or_term(graph: Graph, term: object) -> list[URIRef]:
    if isinstance(term, URIRef):
        return [term]
    if isinstance(term, BNode):
        union = graph.value(term, OWL.unionOf)
        if union is not None:
            return [member for member in Collection(graph, union) if isinstance(member, URIRef)]
    return []


def declared_classes(graph: Graph) -> set[URIRef]:
    classes: set[URIRef] = set()
    for class_type in CLASS_TYPES:
        classes.update(subject for subject in graph.subjects(RDF.type, class_type) if isinstance(subject, URIRef))
    for child, parent in graph.subject_objects(RDFS.subClassOf):
        if isinstance(child, URIRef):
            classes.add(child)
        if isinstance(parent, URIRef):
            classes.add(parent)
    return classes


def declared_properties(graph: Graph) -> set[URIRef]:
    properties: set[URIRef] = set()
    for property_type in PROPERTY_TYPES:
        properties.update(subject for subject in graph.subjects(RDF.type, property_type) if isinstance(subject, URIRef))
    return properties


def add_edge(edges: list[SemanticEdge], seen: set[tuple[str, str, str]], edge: SemanticEdge) -> None:
    key = (str(edge.source), str(edge.target), edge.label)
    if key not in seen:
        seen.add(key)
        edges.append(edge)


def extract_subclass_edges(graph: Graph, edges: list[SemanticEdge], seen: set[tuple[str, str, str]]) -> None:
    for child, parent in graph.subject_objects(RDFS.subClassOf):
        if isinstance(child, URIRef) and isinstance(parent, URIRef):
            add_edge(edges, seen, SemanticEdge(child, parent, "subClassOf", EDGE_SUBCLASS, RDFS.subClassOf))


def extract_object_property_edges(graph: Graph, edges: list[SemanticEdge], seen: set[tuple[str, str, str]]) -> None:
    candidates = set(graph.subjects(RDF.type, OWL.ObjectProperty)) | set(graph.subjects(RDF.type, RDF.Property))
    for prop in candidates:
        if not isinstance(prop, URIRef):
            continue
        label = shorten_term(graph, prop)
        domains = [source for domain in graph.objects(prop, RDFS.domain) for source in expand_union_or_term(graph, domain)]
        ranges = [target for range_term in graph.objects(prop, RDFS.range) for target in expand_union_or_term(graph, range_term)]
        for source in domains:
            for target in ranges:
                if not is_xsd_uri(target):
                    add_edge(edges, seen, SemanticEdge(source, target, label, EDGE_OBJECT_PROPERTY, prop))


def restriction_targets(graph: Graph, restriction: BNode) -> Iterable[URIRef]:
    for predicate in (OWL.onClass, OWL.someValuesFrom, OWL.allValuesFrom):
        for target in graph.objects(restriction, predicate):
            yield from expand_union_or_term(graph, target)


def extract_restriction_edges(graph: Graph, edges: list[SemanticEdge], seen: set[tuple[str, str, str]]) -> None:
    for class_uri, restriction in graph.subject_objects(RDFS.subClassOf):
        if not isinstance(class_uri, URIRef) or not isinstance(restriction, BNode):
            continue
        prop = graph.value(restriction, OWL.onProperty)
        if not isinstance(prop, URIRef):
            continue
        label = shorten_term(graph, prop)
        for target in restriction_targets(graph, restriction):
            if not is_xsd_uri(target):
                add_edge(edges, seen, SemanticEdge(class_uri, target, label, EDGE_OBJECT_PROPERTY, prop))


def extract_individual_edges(
    graph: Graph,
    classes: set[URIRef],
    properties: set[URIRef],
    edges: list[SemanticEdge],
    seen: set[tuple[str, str, str]],
) -> set[URIRef]:
    individuals: set[URIRef] = set()
    for subject, object_type in graph.subject_objects(RDF.type):
        if not isinstance(subject, URIRef) or not isinstance(object_type, URIRef):
            continue
        if subject in classes or subject in properties or object_type in GENERIC_TYPES:
            continue
        if object_type in classes:
            individuals.add(subject)
            add_edge(edges, seen, SemanticEdge(subject, object_type, "a", EDGE_INSTANCE_OF, RDF.type))
    return individuals


def collect_data_properties(graph: Graph) -> dict[URIRef, list[DataProperty]]:
    data_properties: dict[URIRef, list[DataProperty]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    candidates = set(graph.subjects(RDF.type, OWL.DatatypeProperty)) | set(graph.subjects(RDF.type, RDF.Property))
    for prop in candidates:
        if not isinstance(prop, URIRef):
            continue
        domains = [source for domain in graph.objects(prop, RDFS.domain) for source in expand_union_or_term(graph, domain)]
        ranges = [target for range_term in graph.objects(prop, RDFS.range) for target in expand_union_or_term(graph, range_term)]
        ranges = [range_uri for range_uri in ranges if is_xsd_uri(range_uri)]
        if not ranges:
            continue
        for class_uri in domains:
            for range_uri in ranges:
                key = (str(class_uri), str(prop), str(range_uri))
                if key in seen:
                    continue
                seen.add(key)
                data_properties[class_uri].append(DataProperty(shorten_term(graph, prop), shorten_term(graph, range_uri)))

    return {class_uri: sorted(values, key=lambda item: item.name) for class_uri, values in data_properties.items()}


def extract_semantics(graph: Graph) -> ExtractionResult:
    classes = declared_classes(graph)
    properties = declared_properties(graph)
    edges: list[SemanticEdge] = []
    seen: set[tuple[str, str, str]] = set()

    extract_subclass_edges(graph, edges, seen)
    extract_object_property_edges(graph, edges, seen)
    extract_restriction_edges(graph, edges, seen)
    individuals = extract_individual_edges(graph, classes, properties, edges, seen)
    data_properties = collect_data_properties(graph)

    classes.update(data_properties)

    return ExtractionResult(edges, data_properties, classes, individuals)


def node_kind(node_id: URIRef, result: ExtractionResult) -> str:
    if node_id in result.classes:
        return NODE_CLASS
    if node_id in result.individuals:
        return NODE_INDIVIDUAL
    return NODE_OTHER


def node_title(graph: Graph, node_id: URIRef, result: ExtractionResult) -> str:
    label = shorten_term(graph, node_id)
    lines = [label, str(node_id)]
    properties = result.data_properties.get(node_id, [])
    if properties:
        lines.extend(["", "Data properties:"])
        lines.extend(f"{prop.name} : {prop.range_type}" for prop in properties)
    return "\n".join(lines)


def node_style(kind: str, has_data_properties: bool) -> dict[str, object]:
    if kind == NODE_CLASS:
        border = "#1e3a5f" if has_data_properties else "#2563eb"
        return {
            "shape": "dot",
            "size": 20,
            "color": {"background": "#2563eb", "border": border},
            "borderWidth": 4 if has_data_properties else 1,
        }
    if kind == NODE_INDIVIDUAL:
        return {
            "shape": "dot",
            "size": 14,
            "color": {"background": "#0891b2", "border": "#0891b2"},
            "borderWidth": 1,
        }
    return {
        "shape": "dot",
        "size": 14,
        "color": {"background": "#64748b", "border": "#64748b"},
        "borderWidth": 1,
    }


def edge_style(edge: SemanticEdge, directed: bool) -> dict[str, object]:
    arrows = "to" if directed else ""
    if edge.edge_type == EDGE_SUBCLASS:
        return {"color": "#94a3b8", "dashes": True, "arrows": arrows}
    if edge.edge_type == EDGE_INSTANCE_OF:
        return {"color": "#f59e0b", "dashes": False, "arrows": arrows}
    return {"color": "#7c3aed", "dashes": False, "arrows": arrows}


def build_network(graph: Graph, result: ExtractionResult, max_edges: int, directed: bool) -> Network:
    rendered_edges = result.edges[:max_edges]
    node_ids = {edge.source for edge in rendered_edges} | {edge.target for edge in rendered_edges}
    node_ids.update(result.data_properties)

    net = Network(height="820px", width="100%", directed=directed, bgcolor="#ffffff", cdn_resources="in_line")
    net.barnes_hut(gravity=-8000, spring_length=250, spring_strength=0.015, damping=0.3)

    for node_id in sorted(node_ids, key=str):
        kind = node_kind(node_id, result)
        style = node_style(kind, node_id in result.data_properties)
        net.add_node(
            str(node_id),
            label=shorten_term(graph, node_id),
            title=node_title(graph, node_id, result),
            **style,
        )

    for edge in rendered_edges:
        net.add_edge(
            str(edge.source),
            str(edge.target),
            label=edge.label,
            title=f"{shorten_term(graph, edge.source)} --{edge.label}--> {shorten_term(graph, edge.target)}",
            **edge_style(edge, directed),
        )

    return net


def render_html(graph: Graph, result: ExtractionResult, output_path: Path, max_edges: int, directed: bool) -> tuple[int, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    net = build_network(graph, result, max_edges, directed)
    net.write_html(str(output_path), open_browser=False, notebook=False)
    return len(net.nodes), len(net.edges)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render an OWL/RDF Turtle ontology as an interactive semantic graph.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Turtle ontology file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output HTML path")
    parser.add_argument("--max-edges", type=int, default=DEFAULT_MAX_EDGES, help="Cap on rendered edges")
    parser.add_argument("--undirected", action="store_true", help="Remove arrow heads")
    parser.add_argument("--open-browser", action="store_true", help="Auto-open HTML after generation")
    return parser.parse_args()


def print_summary(
    input_path: Path,
    output_path: Path,
    graph: Graph,
    result: ExtractionResult,
    nodes_rendered: int,
    edges_rendered: int,
) -> None:
    edge_counts = Counter(edge.edge_type for edge in result.edges[:edges_rendered])
    print("Ontology graph generated successfully.")
    print(f"  Input:    {input_path}")
    print(f"  Output:   {output_path}")
    print(f"  Total triples in file:       {len(graph)}")
    print(f"  Semantic edges extracted:    {len(result.edges)}")
    print(f"  Nodes rendered:              {nodes_rendered}")
    print(f"  Edges rendered:              {edges_rendered}")
    print("  Edge type breakdown:")
    for edge_type, count in sorted(edge_counts.items()):
        print(f"    {edge_type}: {count}")


def main() -> None:
    args = parse_args()
    render_result = SemanticWebPlotter(
        max_edges=args.max_edges,
        directed=not args.undirected,
    ).render_turtle_file(args.input, args.output)
    graph = Graph()
    graph.parse(args.input, format="turtle")
    result = extract_semantics(graph)
    print_summary(args.input, args.output, graph, result, render_result.nodes_rendered, render_result.edges_rendered)

    if args.open_browser:
        webbrowser.open(args.output.resolve().as_uri())


if __name__ == "__main__":
    main()
