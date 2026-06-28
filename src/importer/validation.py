from __future__ import annotations

from dataclasses import dataclass

from rdflib import Graph, RDF, RDFS, URIRef


ALLOWED_NON_ONTOLOGY_PREDICATES = {
    RDF.type,
    RDFS.label,
    RDFS.comment,
}


@dataclass(frozen=True)
class OntologyTerms:
    classes: set[URIRef]
    properties: set[URIRef]
    labels: dict[URIRef, str]
    comments: dict[URIRef, str]
    domains: dict[URIRef, set[URIRef]]
    ranges: dict[URIRef, set[URIRef]]

    def summary(self) -> str:
        class_lines = "\n".join(self._term_summary(term) for term in sorted(self.classes, key=str))
        property_lines = "\n".join(self._property_summary(term) for term in sorted(self.properties, key=str))
        return f"Classes:\n{class_lines}\n\nProperties:\n{property_lines}".strip()

    def _term_summary(self, term: URIRef) -> str:
        parts = [f"- {term}"]
        label = self.labels.get(term)
        comment = self.comments.get(term)
        if label:
            parts.append(f"  label: {label}")
        if comment:
            parts.append(f"  comment: {comment}")
        return "\n".join(parts)

    def _property_summary(self, term: URIRef) -> str:
        parts = [self._term_summary(term)]
        for domain in sorted(self.domains.get(term, set()), key=str):
            parts.append(f"  domain: {domain}")
        for range_uri in sorted(self.ranges.get(term, set()), key=str):
            parts.append(f"  range: {range_uri}")
        return "\n".join(parts)


@dataclass(frozen=True)
class ImportValidationResult:
    ok: bool
    errors: list[str]

    def raise_for_errors(self) -> None:
        if not self.ok:
            raise ValueError("; ".join(self.errors))


def inspect_ontology_terms(ontology_graph: Graph) -> OntologyTerms:
    classes = {term for term in ontology_graph.subjects(RDF.type, RDFS.Class) if isinstance(term, URIRef)}
    properties = {term for term in ontology_graph.subjects(RDF.type, RDF.Property) if isinstance(term, URIRef)}
    terms = classes | properties
    return OntologyTerms(
        classes=classes,
        properties=properties,
        labels={term: _first_literal(ontology_graph, term, RDFS.label) for term in terms},
        comments={term: _first_literal(ontology_graph, term, RDFS.comment) for term in terms},
        domains={
            term: {value for value in ontology_graph.objects(term, RDFS.domain) if isinstance(value, URIRef)}
            for term in properties
        },
        ranges={
            term: {value for value in ontology_graph.objects(term, RDFS.range) if isinstance(value, URIRef)}
            for term in properties
        },
    )


def _first_literal(graph: Graph, term: URIRef, predicate: URIRef) -> str:
    for value in graph.objects(term, predicate):
        text = str(value).strip()
        if text:
            return text
    return ""


def validate_instance_graph(
    instance_graph: Graph,
    ontology_graph: Graph,
) -> ImportValidationResult:
    terms = inspect_ontology_terms(ontology_graph)
    errors: list[str] = []

    if not instance_graph:
        errors.append("Instance graph is empty.")

    for term in instance_graph.subjects(RDF.type, RDFS.Class):
        errors.append(f"Instance graph must not define rdfs:Class term {term}.")
    for term in instance_graph.subjects(RDF.type, RDF.Property):
        errors.append(f"Instance graph must not define rdf:Property term {term}.")

    uses_ontology = False
    for subject, predicate, obj in instance_graph:
        if predicate in terms.properties:
            uses_ontology = True
        elif predicate not in ALLOWED_NON_ONTOLOGY_PREDICATES:
            errors.append(f"Predicate {predicate} is not defined in the ontology.")

        if predicate == RDF.type and isinstance(obj, URIRef):
            if obj in terms.classes:
                uses_ontology = True
            elif obj not in {RDFS.Class, RDF.Property}:
                errors.append(f"Type {obj} is not defined as an ontology class.")

        if isinstance(subject, URIRef):
            if subject in terms.classes or subject in terms.properties:
                errors.append(f"Instance graph must not reuse ontology term {subject} as an instance.")

    if not uses_ontology:
        errors.append("Instance graph does not use any ontology classes or properties.")

    return ImportValidationResult(ok=not errors, errors=errors)
