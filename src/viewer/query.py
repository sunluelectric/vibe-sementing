from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.common.config import Settings
from src.common.fuseki import FusekiUnavailable
from src.common.graph_slice import GraphSliceService
from src.common.semantic_search import rows_to_chunks, search_chunks


class ViewerFusekiClient(Protocol):
    query_url: str

    def is_available(self) -> bool: ...

    def select(self, sparql: str) -> list[dict[str, str]]: ...

    def construct_turtle(self, sparql: str) -> str: ...


@dataclass(frozen=True)
class ViewerStatus:
    available: bool
    query_url: str
    triple_count: int | None
    message: str


class ViewerQueryService:
    def __init__(self, settings: Settings, client: ViewerFusekiClient):
        self.settings = settings
        self.client = client

    def status(self) -> ViewerStatus:
        if not self.client.is_available():
            return ViewerStatus(
                available=False,
                query_url=self.client.query_url,
                triple_count=None,
                message="Fuseki is not reachable. The viewer requires Fuseki data.",
            )
        try:
            count = self.triple_count()
        except FusekiUnavailable as exc:
            return ViewerStatus(
                available=False,
                query_url=self.client.query_url,
                triple_count=None,
                message=str(exc),
            )
        return ViewerStatus(
            available=True,
            query_url=self.client.query_url,
            triple_count=count,
            message="Fuseki is reachable.",
        )

    def select(self, sparql: str) -> list[dict[str, str]]:
        self._require_available()
        return self.client.select(sparql)

    def triple_count(self) -> int:
        rows = self.client.select(
            """
            SELECT (COUNT(*) AS ?count) WHERE {
              GRAPH ?graph { ?s ?p ?o . }
            }
            """
        )
        if not rows:
            return 0
        return int(rows[0].get("count", "0"))

    def classes(self, limit: int = 100) -> list[dict[str, str]]:
        return self.select(
            f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?class ?label ?comment WHERE {{
              GRAPH ?graph {{
                ?class a rdfs:Class .
                OPTIONAL {{ ?class rdfs:label ?label . }}
                OPTIONAL {{ ?class rdfs:comment ?comment . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?label, ?class)))
            LIMIT {int(limit)}
            """
        )

    def properties(self, limit: int = 100) -> list[dict[str, str]]:
        return self.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?property ?label ?comment ?domain ?range WHERE {{
              GRAPH ?graph {{
                ?property a rdf:Property .
                OPTIONAL {{ ?property rdfs:label ?label . }}
                OPTIONAL {{ ?property rdfs:comment ?comment . }}
                OPTIONAL {{ ?property rdfs:domain ?domain . }}
                OPTIONAL {{ ?property rdfs:range ?range . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?label, ?property)))
            LIMIT {int(limit)}
            """
        )

    def instances(self, limit: int = 100) -> list[dict[str, str]]:
        return self.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?instance ?class ?label WHERE {{
              GRAPH ?graph {{
                ?instance a ?class .
                FILTER NOT EXISTS {{ ?instance a rdfs:Class . }}
                FILTER NOT EXISTS {{ ?instance a rdf:Property . }}
                OPTIONAL {{ ?instance rdfs:label ?label . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?label, ?instance)))
            LIMIT {int(limit)}
            """
        )

    def class_instances_by_label(self, class_label: str, limit: int = 50) -> list[dict[str, str]]:
        label = _sparql_string(class_label)
        return self.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?instance ?class ?label ?predicate ?predicateLabel ?predicateComment ?object ?objectLabel ?objectComment WHERE {{
              GRAPH ?schemaGraph {{
                ?class a rdfs:Class .
                OPTIONAL {{ ?class rdfs:label ?classLabel . }}
              }}
              FILTER(
                LCASE(STR(?classLabel)) = LCASE({label}) ||
                LCASE(REPLACE(STRAFTER(STR(?class), "#"), "([a-z])([A-Z])", "$1 $2")) = LCASE({label}) ||
                LCASE(STRAFTER(STR(?class), "#")) = LCASE(REPLACE({label}, " ", ""))
              )
              GRAPH ?dataGraph {{
                ?instance a ?class .
                OPTIONAL {{ ?instance rdfs:label ?label . }}
                ?instance ?predicate ?object .
                OPTIONAL {{ ?predicate rdfs:label ?predicateLabel . }}
                OPTIONAL {{ ?predicate rdfs:comment ?predicateComment . }}
                OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
                OPTIONAL {{ ?object rdfs:comment ?objectComment . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?label, ?instance))) LCASE(STR(COALESCE(?predicateLabel, ?predicate)))
            LIMIT {int(limit)}
            """
        )

    def class_instance_count_by_label(self, class_label: str) -> int:
        label = _sparql_string(class_label)
        rows = self.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT (COUNT(DISTINCT ?instance) AS ?count) WHERE {{
              GRAPH ?schemaGraph {{
                ?class a rdfs:Class .
                OPTIONAL {{ ?class rdfs:label ?classLabel . }}
              }}
              FILTER(
                LCASE(STR(?classLabel)) = LCASE({label}) ||
                LCASE(REPLACE(STRAFTER(STR(?class), "#"), "([a-z])([A-Z])", "$1 $2")) = LCASE({label}) ||
                LCASE(STRAFTER(STR(?class), "#")) = LCASE(REPLACE({label}, " ", ""))
              )
              GRAPH ?dataGraph {{
                ?instance a ?class .
                FILTER NOT EXISTS {{ ?instance a rdfs:Class . }}
                FILTER NOT EXISTS {{ ?instance a rdf:Property . }}
              }}
            }}
            """
        )
        if not rows:
            return 0
        return int(rows[0].get("count", "0"))

    def graph_summary(self) -> dict[str, object]:
        return {
            "triple_count": self.triple_count(),
            "classes": self.classes(limit=200),
            "properties": self.properties(limit=200),
            "sample_instances": self.instances(limit=80),
        }

    def search_facts(self, question: str, limit: int = 80) -> list[dict[str, str]]:
        filters = " || ".join(
            f"CONTAINS(LCASE(STR(?text)), LCASE({_sparql_string(term)}))"
            for term in _search_terms(question)
        )
        if not filters:
            filters = "true"
        return self.select(
            f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?subject ?subjectLabel ?predicate ?predicateLabel ?predicateComment ?object ?objectLabel ?objectComment WHERE {{
              GRAPH ?matchGraph {{
                ?subject ?matchPredicate ?text .
                FILTER(isLiteral(?text))
                FILTER({filters})
              }}
              GRAPH ?factGraph {{
                ?subject ?predicate ?object .
                OPTIONAL {{ ?subject rdfs:label ?subjectLabel . }}
                OPTIONAL {{ ?predicate rdfs:label ?predicateLabel . }}
                OPTIONAL {{ ?predicate rdfs:comment ?predicateComment . }}
                OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
                OPTIONAL {{ ?object rdfs:comment ?objectComment . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?subjectLabel, ?subject))) LCASE(STR(COALESCE(?predicateLabel, ?predicate)))
            LIMIT {int(limit)}
            """
        )

    def subject_facts_matching_question_labels(self, question: str, limit: int = 120) -> list[dict[str, str]]:
        question_text = _sparql_string(question)
        return self.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?subject ?subjectLabel ?predicate ?predicateLabel ?predicateComment ?object ?objectLabel ?objectComment WHERE {{
              GRAPH ?labelGraph {{
                ?subject rdfs:label ?subjectLabel .
                FILTER(STRLEN(STR(?subjectLabel)) >= 4)
                FILTER(CONTAINS(LCASE({question_text}), LCASE(STR(?subjectLabel))))
                FILTER NOT EXISTS {{ ?subject a rdfs:Class . }}
                FILTER NOT EXISTS {{ ?subject a rdf:Property . }}
              }}
              GRAPH ?factGraph {{
                ?subject ?predicate ?object .
                OPTIONAL {{ ?predicate rdfs:label ?predicateLabel . }}
                OPTIONAL {{ ?predicate rdfs:comment ?predicateComment . }}
                OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
                OPTIONAL {{ ?object rdfs:comment ?objectComment . }}
              }}
            }}
            ORDER BY LCASE(STR(?subjectLabel)) LCASE(STR(COALESCE(?predicateLabel, ?predicate)))
            LIMIT {int(limit)}
            """
        )

    def semantic_search_facts(self, question: str, limit: int = 200) -> list[dict[str, str]]:
        self._require_available()
        rows, slice_result = GraphSliceService(self.settings, self.client).fact_rows(question, limit=limit)
        if slice_result.used:
            return rows
        rows = self.select(
            f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?subject ?subjectLabel ?predicate ?predicateLabel ?predicateComment ?object ?objectLabel ?objectComment WHERE {{
              GRAPH ?graph {{
                ?subject ?predicate ?object .
                OPTIONAL {{ ?subject rdfs:label ?subjectLabel . }}
                OPTIONAL {{ ?predicate rdfs:label ?predicateLabel . }}
                OPTIONAL {{ ?predicate rdfs:comment ?predicateComment . }}
                OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
                OPTIONAL {{ ?object rdfs:comment ?objectComment . }}
              }}
            }}
            ORDER BY LCASE(STR(COALESCE(?subjectLabel, ?subject))) LCASE(STR(COALESCE(?predicateLabel, ?predicate)))
            LIMIT {int(limit)}
            """
        )
        chunks = rows_to_chunks(rows, source="fuseki-facts")
        results = search_chunks(chunks, question, self.settings)
        return [result.chunk.metadata for result in results]

    def export_turtle(self) -> str:
        self._require_available()
        return self.client.construct_turtle(
            """
            CONSTRUCT { ?s ?p ?o }
            WHERE {
              GRAPH ?graph { ?s ?p ?o . }
            }
            """
        )

    def _require_available(self) -> None:
        if not self.client.is_available():
            raise FusekiUnavailable("Fuseki is not reachable. The viewer requires Fuseki data.")


def _sparql_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _search_terms(question: str) -> list[str]:
    terms: list[str] = []
    for raw in question.replace("?", " ").replace(",", " ").split():
        term = raw.strip().lower()
        if len(term) < 3:
            continue
        if term in {"what", "where", "when", "which", "with", "about", "from", "that", "this", "does", "have", "show", "list", "tell"}:
            continue
        if term not in terms:
            terms.append(term)
    return terms[:8]
