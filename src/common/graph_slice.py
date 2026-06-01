from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.common.config import Settings
from src.common.semantic_search import rows_to_chunks, search_chunks


class GraphSliceClient(Protocol):
    def is_available(self) -> bool: ...

    def select(self, sparql: str) -> list[dict[str, str]]: ...

    def construct_turtle(self, sparql: str) -> str: ...


@dataclass(frozen=True)
class GraphSliceResult:
    used: bool
    context: str
    candidate_count: int
    selected_count: int
    query_count: int


class GraphSliceService:
    def __init__(self, settings: Settings, client: GraphSliceClient):
        self.settings = settings
        self.client = client

    def ontology_context(self, graph_uri: str, query: str, max_chars: int | None = None) -> GraphSliceResult:
        if not self.client.is_available():
            return GraphSliceResult(False, "", 0, 0, 0)
        try:
            candidates = self._select_candidate_terms(
                self._ontology_term_index(graph_uri),
                query,
            )
            context = self._construct_term_slice(graph_uri, candidates.terms, max_chars or self.settings.semantic_context_max_chars)
        except Exception:
            return GraphSliceResult(False, "", 0, 0, 0)
        return GraphSliceResult(
            used=bool(context),
            context=context,
            candidate_count=len(candidates.index_rows),
            selected_count=len(candidates.terms),
            query_count=2 if context else 1,
        )

    def fact_rows(self, question: str, limit: int = 80) -> tuple[list[dict[str, str]], GraphSliceResult]:
        if not self.client.is_available():
            return [], GraphSliceResult(False, "", 0, 0, 0)
        try:
            candidates = self._select_candidate_terms(self._fact_term_index(), question)
            if not candidates.terms:
                return [], GraphSliceResult(False, "", len(candidates.index_rows), 0, 1)
            rows = self.client.select(_fact_slice_query(candidates.terms, limit))
        except Exception:
            return [], GraphSliceResult(False, "", 0, 0, 0)
        return rows, GraphSliceResult(
            used=bool(rows),
            context="",
            candidate_count=len(candidates.index_rows),
            selected_count=len(candidates.terms),
            query_count=2,
        )

    def _ontology_term_index(self, graph_uri: str) -> list[dict[str, str]]:
        return self.client.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?term ?label ?comment ?kind WHERE {{
              GRAPH <{_escape_uri(graph_uri)}> {{
                {{
                  ?term a rdfs:Class .
                  BIND("class" AS ?kind)
                }}
                UNION
                {{
                  ?term a rdf:Property .
                  BIND("property" AS ?kind)
                }}
                OPTIONAL {{ ?term rdfs:label ?label . }}
                OPTIONAL {{ ?term rdfs:comment ?comment . }}
              }}
            }}
            LIMIT {_index_limit(self.settings)}
            """
        )

    def _fact_term_index(self) -> list[dict[str, str]]:
        return self.client.select(
            f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?term ?label ?comment ?kind ?text WHERE {{
              GRAPH ?graph {{
                {{
                  ?term rdfs:label ?label .
                  BIND("labeled-resource" AS ?kind)
                }}
                UNION
                {{
                  ?term a rdfs:Class .
                  BIND("class" AS ?kind)
                }}
                UNION
                {{
                  ?term a rdf:Property .
                  BIND("property" AS ?kind)
                }}
                UNION
                {{
                  ?term ?p ?text .
                  FILTER(isLiteral(?text))
                  BIND("literal-subject" AS ?kind)
                }}
                OPTIONAL {{ ?term rdfs:comment ?comment . }}
              }}
            }}
            LIMIT {_index_limit(self.settings) * 2}
            """
        )

    def _select_candidate_terms(self, rows: list[dict[str, str]], query: str) -> "_Candidates":
        if not rows:
            return _Candidates([], [])
        chunks = rows_to_chunks(rows, source="fuseki-term-index", kind="graph-term")
        results = search_chunks(chunks, query, self.settings)
        terms: list[str] = []
        for result in results:
            term = result.chunk.metadata.get("term", "")
            if term.startswith("http://") or term.startswith("https://"):
                terms.append(term)
        return _Candidates(rows, _dedupe(terms))

    def _construct_term_slice(self, graph_uri: str, terms: list[str], max_chars: int) -> str:
        if not terms:
            return ""
        turtle = self.client.construct_turtle(_ontology_slice_query(graph_uri, terms))
        turtle = turtle.strip()
        if not turtle:
            return ""
        header = "# Source chunk: Fuseki ontology graph [rdf-slice]\n\n"
        return (header + turtle)[:max_chars].rstrip()


@dataclass(frozen=True)
class _Candidates:
    index_rows: list[dict[str, str]]
    terms: list[str]


def _ontology_slice_query(graph_uri: str, terms: list[str]) -> str:
    values = _values(terms)
    return f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    CONSTRUCT {{
      ?term ?p ?o .
      ?s ?sp ?term .
      ?related ?rp ?ro .
    }}
    WHERE {{
      GRAPH <{_escape_uri(graph_uri)}> {{
        VALUES ?term {{ {values} }}
        {{
          ?term ?p ?o .
        }}
        UNION
        {{
          ?s ?sp ?term .
        }}
        UNION
        {{
          ?term rdfs:domain|rdfs:range ?related .
          ?related ?rp ?ro .
        }}
      }}
    }}
    """


def _fact_slice_query(terms: list[str], limit: int) -> str:
    values = _values(terms)
    return f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?subject ?subjectLabel ?predicate ?predicateLabel ?object ?objectLabel WHERE {{
      GRAPH ?graph {{
        VALUES ?candidate {{ {values} }}
        {{
          ?candidate ?predicate ?object .
          BIND(?candidate AS ?subject)
        }}
        UNION
        {{
          ?subject ?predicate ?candidate .
          BIND(?candidate AS ?object)
        }}
        UNION
        {{
          ?subject a ?candidate .
          ?subject ?predicate ?object .
        }}
        OPTIONAL {{ ?subject rdfs:label ?subjectLabel . }}
        OPTIONAL {{ ?predicate rdfs:label ?predicateLabel . }}
        OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
        FILTER NOT EXISTS {{ ?subject a rdfs:Class . }}
        FILTER NOT EXISTS {{ ?subject a rdf:Property . }}
      }}
    }}
    ORDER BY LCASE(STR(COALESCE(?subjectLabel, ?subject))) LCASE(STR(COALESCE(?predicateLabel, ?predicate)))
    LIMIT {int(limit)}
    """


def _values(terms: list[str]) -> str:
    return " ".join(f"<{_escape_uri(term)}>" for term in terms)


def _escape_uri(uri: str) -> str:
    return uri.replace("\\", "\\\\").replace(">", "%3E").replace("<", "%3C")


def _index_limit(settings: Settings) -> int:
    return max(settings.semantic_search_top_k * 80, 200)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
