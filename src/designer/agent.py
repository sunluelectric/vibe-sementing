from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rdflib import Graph, RDF, RDFS, XSD

from src.common.llm import get_text_response, parse_json_object
from src.common.rdf import parse_turtle


DESIGNER_PROMPT = """You are the semantic web designer agent for this project.

Design a compact RDF/RDFS semantic web schema for the user's data and design
requirements. Do not make a complex or exhaustive ontology. The goal is a small,
correct, easy-to-import schema that can be loaded into Apache Jena Fuseki and
improved later. The schema must be driven by the supplied requirements and
project data, not by any built-in domain example.

Use RDF and RDFS only. Do not use OWL in this first version. You are designing
the schema; do not insert individual data instances.

Return exactly one JSON object with these keys:
- design_markdown: a complete design document for design.md.
- ontology_turtle: valid Turtle containing the ontology/schema.

Ontology requirements:
- Base namespace: {ontology_namespace}
- Prefixes must include sw, rdf, rdfs, xsd.
- Keep the ontology compact: about 10 to 16 classes and 15 to 28 properties.
- Keep the full Turtle under 220 triples.
- Do not model every detail in the source data. Model only the core concepts
  needed for importing the supplied data and answering basic questions.
- Choose class and property names from the supplied domain. Do not assume a
  particular sample domain unless it appears in the requirements or data.
- Include a shallow subclass hierarchy only where it is obvious from the input.
- Include practical object and datatype properties with rdfs:domain and
  rdfs:range.
- Use rdfs:label and rdfs:comment on important classes and properties.
- Prefer broad reusable properties over highly specific one-off properties.
- Avoid enumerating source facts as schema terms.
- Avoid blank nodes, RDF lists, restrictions, union classes, and complicated
  cardinality modeling.
- The Turtle must parse as Turtle with rdflib.

Design requirements:
{requirements}

Available project data:
{data}
"""


@dataclass
class DesignResult:
    design_markdown: str
    ontology_turtle: str
    graph: Graph
    progress_markdown: str = ""


class DesignerAgent:
    def __init__(
        self,
        model: str,
        timeout_seconds: int = 90,
        ontology_namespace: str = "http://example.org/semantic-web#",
    ):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.ontology_namespace = ontology_namespace
        self.progress_entries: list[str] = []

    def run(
        self,
        requirements: str,
        data: str,
        max_attempts: int = 3,
        progress_path: Path | None = None,
    ) -> DesignResult:
        feedback = ""
        self.progress_entries = []
        self._record_progress(
            progress_path,
            "# Semantic Web Designer Progress\n\n"
            f"- Model: `{self.model}`\n"
            f"- Max attempts: {max_attempts}\n"
            f"- Started: {self._timestamp()}\n",
        )
        for attempt in range(1, max_attempts + 1):
            prompt = DESIGNER_PROMPT.format(
                ontology_namespace=self.ontology_namespace,
                requirements=requirements,
                data=data,
            )
            if feedback:
                prompt += (
                    "\n\nYour previous response failed validation. Fix the problem and "
                    f"return the full JSON object again.\nValidation feedback:\n{feedback}"
                )
            self._record_progress(
                progress_path,
                f"## Attempt {attempt}\n\n"
                f"- Status: LLM request started\n"
                f"- Timestamp: {self._timestamp()}\n"
                f"- Retry feedback included: {'yes' if feedback else 'no'}\n",
            )
            try:
                text = self._run_direct_design_call(prompt)
            except Exception as exc:
                feedback = f"Attempt {attempt} failed during LLM call: {type(exc).__name__}: {exc}"
                self._record_progress(
                    progress_path,
                    f"## Attempt {attempt} Response\n\n"
                    f"- Status: LLM request failed\n"
                    f"- Timestamp: {self._timestamp()}\n"
                    f"- Feedback: {feedback}\n",
                )
                continue
            self._record_progress(
                progress_path,
                f"## Attempt {attempt} Response\n\n"
                f"- Status: LLM response received\n"
                f"- Timestamp: {self._timestamp()}\n"
                f"- Response characters: {len(text)}\n",
            )
            try:
                payload = parse_json_object(text)
                design_markdown = str(payload["design_markdown"]).strip()
                ontology_turtle = str(payload["ontology_turtle"]).strip()
                graph = parse_turtle(ontology_turtle)
                if len(graph) < 20:
                    raise ValueError("Ontology has fewer than 20 triples.")
                if len(graph) > 260:
                    raise ValueError("Ontology is too complex for the first version.")
                self._validate_schema_graph(graph)
                self._record_progress(
                    progress_path,
                    f"## Attempt {attempt} Validation\n\n"
                    f"- Status: passed\n"
                    f"- Triple count: {len(graph)}\n\n"
                    "### Candidate Design\n\n"
                    f"{design_markdown}\n",
                )
                return DesignResult(
                    design_markdown=design_markdown,
                    ontology_turtle=ontology_turtle,
                    graph=graph,
                    progress_markdown=self._progress_markdown(),
                )
            except Exception as exc:
                feedback = f"Attempt {attempt} failed: {type(exc).__name__}: {exc}"
                self._record_progress(
                    progress_path,
                    f"## Attempt {attempt} Validation\n\n"
                    f"- Status: failed\n"
                    f"- Feedback: {feedback}\n",
                )
        raise RuntimeError(f"Designer failed after {max_attempts} attempts. {feedback}")

    def _run_direct_design_call(self, prompt: str) -> str:
        return get_text_response(self.model, prompt, self.timeout_seconds)

    def _validate_schema_graph(self, graph: Graph) -> None:
        namespace_map = {prefix: str(namespace) for prefix, namespace in graph.namespaces()}
        expected_prefixes = {
            "sw": self.ontology_namespace,
            "rdf": str(RDF),
            "rdfs": str(RDFS),
            "xsd": str(XSD),
        }
        for prefix, namespace in expected_prefixes.items():
            if namespace_map.get(prefix) != namespace:
                raise ValueError(f"Missing or incorrect prefix {prefix}: expected {namespace}")

        class_terms = set(graph.subjects(RDF.type, RDFS.Class))
        property_terms = set(graph.subjects(RDF.type, RDF.Property))
        if not class_terms:
            raise ValueError("Ontology must define at least one rdfs:Class.")
        if not property_terms:
            raise ValueError("Ontology must define at least one rdf:Property.")

        for prop in sorted(property_terms, key=str):
            if (prop, RDFS.domain, None) not in graph:
                raise ValueError(f"Property {prop} is missing rdfs:domain.")
            if (prop, RDFS.range, None) not in graph:
                raise ValueError(f"Property {prop} is missing rdfs:range.")

    def _record_progress(self, progress_path: Path | None, entry: str) -> None:
        self.progress_entries.append(entry.strip())
        if progress_path is None:
            return
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(self._progress_markdown() + "\n", encoding="utf-8")

    def _progress_markdown(self) -> str:
        return "\n\n".join(self.progress_entries).strip()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat()
