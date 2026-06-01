from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rdflib import Graph, RDF, RDFS, XSD

from src.common.llm import get_text_response, parse_json_object
from src.common.rdf import parse_turtle


TEST_DESIGNER_PROMPT = """You are the semantic web designer agent for this project.

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
- For CSV columns, treat profile datatypes as recommendations rather than
  guarantees. Prefer xsd:string for identifiers, codes, leading-zero values,
  mixed-format values, high-risk columns, and any column whose meaning is not
  clearly numeric/date/boolean. Use xsd:integer, xsd:decimal, xsd:boolean,
  xsd:date, or xsd:dateTime only when the profile and column semantics both
  clearly support that datatype. Prefer xsd:decimal over xsd:integer when a
  numeric column may contain fractional values.
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

PRODUCTION_DESIGNER_PROMPT = """You are the semantic web designer agent for this project.

Design a comprehensive RDF/RDFS semantic web schema for the user's data and
design requirements. The schema must be driven by the supplied requirements and
project data, not by any built-in domain example.

Use RDF/RDFS as the core representation. OWL terms may be used sparingly when
they clearly improve the schema, but the output must remain loadable and
queryable in Apache Jena Fuseki. You are designing the schema; do not insert
individual data instances.

Return exactly one JSON object with these keys:
- design_markdown: a complete design document for design.md.
- ontology_turtle: valid Turtle containing the ontology/schema.

Ontology requirements:
- Base namespace: {ontology_namespace}
- Prefixes must include sw, rdf, rdfs, xsd.
- Cover the important concepts, entities, structured fields, relationships,
  identifiers, constraints, and query needs visible in the requirements and
  source data.
- Do not intentionally keep the ontology small. Add classes and properties when
  the evidence shows they are needed for coverage, import fidelity, or useful
  viewer queries.
- Include meaningful class and property hierarchy where the source material
  supports it.
- Include practical object and datatype properties with rdfs:domain and
  rdfs:range where practical.
- For CSV columns, treat profile datatypes as recommendations rather than
  guarantees. Prefer xsd:string for identifiers, codes, leading-zero values,
  mixed-format values, high-risk columns, and any column whose meaning is not
  clearly numeric/date/boolean. Use xsd:integer, xsd:decimal, xsd:boolean,
  xsd:date, or xsd:dateTime only when the profile and column semantics both
  clearly support that datatype. Prefer xsd:decimal over xsd:integer when a
  numeric column may contain fractional values.
- Use rdfs:label and rdfs:comment on important classes and properties.
- Prefer reusable modeling patterns, but do not collapse distinct source
  concepts merely to stay brief.
- Avoid enumerating source facts as schema terms; instance facts belong in the
  importer output, not the ontology.
- Avoid blank nodes and RDF lists unless they are clearly necessary.
- The Turtle must parse as Turtle with rdflib.

Design requirements:
{requirements}

Available project data:
{data}
"""


DESIGN_FOCUS_PLANNER_PROMPT = """You are planning semantic-search work for a semantic web designer.

Create focused search queries that cover the design requirements and the
available data inventory. The queries should help discover the core concepts,
relationships, identifiers, and source facts needed for an RDF/RDFS ontology.

Return exactly one JSON object with this key:
- focuses: an array of objects. Each object has:
  - query: a concise semantic-search query.
  - purpose: why this query matters for ontology design.

Rules:
- Return at most {max_focuses} focuses.
- Cover different conceptual areas. Do not make duplicate queries.
- Keep queries domain-neutral in wording except for domain terms found in the
  requirements or data inventory.
- Do not design the ontology yet.

Design requirements:
{requirements}

Data inventory:
{data_inventory}
"""


DESIGN_SLICE_PROMPT = """You are drafting one small schema slice for a semantic web designer.

Use the retrieved context for this focus area to write concise schema-design
notes. Do not output Turtle. Do not define the final ontology. Identify likely
classes, properties, hierarchy hints, datatype facts, object relationships, and
importer considerations that may be useful when the final ontology is
synthesized.

Return exactly one JSON object with this key:
- schema_notes: concise markdown notes for this focus area.

Design requirements:
{requirements}

Focus query:
{query}

Focus purpose:
{purpose}

Retrieved source context:
{context}
"""


DESIGN_JSON_REPAIR_PROMPT = """Convert the semantic web designer response below into the required JSON object.

Return exactly one JSON object and no other text.

Required JSON keys:
- design_markdown: markdown documentation for design.md.
- ontology_turtle: valid Turtle containing only the ontology/schema.

Do not redesign the ontology. Preserve the design content and Turtle from the
response as closely as possible. If the response contains markdown and Turtle
sections instead of JSON, place the markdown in design_markdown and the Turtle
in ontology_turtle.

Designer response:
{text}
"""


@dataclass(frozen=True)
class DesignFocus:
    query: str
    purpose: str


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
        mode: str = "test",
        ontology_triple_limit: int = 260,
    ):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.ontology_namespace = ontology_namespace
        self.mode = "production" if mode == "production" else "test"
        self.ontology_triple_limit = ontology_triple_limit
        self.progress_entries: list[str] = []

    def plan_focuses(
        self,
        requirements: str,
        data_inventory: str,
        max_focuses: int,
        progress_path: Path | None = None,
    ) -> list[DesignFocus]:
        prompt = DESIGN_FOCUS_PLANNER_PROMPT.format(
            requirements=requirements,
            data_inventory=data_inventory,
            max_focuses=max_focuses,
        )
        self._record_progress(
            progress_path,
            "## Retrieval Focus Planning\n\n"
            f"- Status: LLM request started\n"
            f"- Timestamp: {self._timestamp()}\n"
            f"- Max focuses: {max_focuses}\n",
        )
        text = self._run_direct_design_call(prompt)
        payload = parse_json_object(text)
        focuses: list[DesignFocus] = []
        for item in payload.get("focuses", []):
            if not isinstance(item, dict):
                continue
            query = str(item.get("query", "")).strip()
            purpose = str(item.get("purpose", "")).strip()
            if query:
                focuses.append(DesignFocus(query=query, purpose=purpose or "Ontology design coverage."))
            if len(focuses) >= max_focuses:
                break
        if not focuses:
            focuses = [DesignFocus(query=requirements[:500], purpose="Fallback requirements coverage.")]
        self._record_progress(
            progress_path,
            "## Retrieval Focus Planning Result\n\n"
            f"- Status: passed\n"
            f"- Focus count: {len(focuses)}\n"
            + "\n".join(f"- Query: {focus.query}" for focus in focuses),
        )
        return focuses

    def draft_schema_slice(
        self,
        requirements: str,
        focus: DesignFocus,
        context: str,
        progress_path: Path | None = None,
    ) -> str:
        prompt = DESIGN_SLICE_PROMPT.format(
            requirements=requirements,
            query=focus.query,
            purpose=focus.purpose,
            context=context,
        )
        self._record_progress(
            progress_path,
            "## Schema Slice Draft\n\n"
            f"- Status: LLM request started\n"
            f"- Timestamp: {self._timestamp()}\n"
            f"- Query: {focus.query}\n"
            f"- Context characters: {len(context)}\n",
        )
        text = self._run_direct_design_call(prompt)
        try:
            payload = parse_json_object(text)
            notes = str(payload["schema_notes"]).strip()
        except Exception:
            notes = text.strip()
        self._record_progress(
            progress_path,
            "## Schema Slice Draft Result\n\n"
            f"- Status: passed\n"
            f"- Query: {focus.query}\n"
            f"- Notes characters: {len(notes)}\n",
        )
        return notes

    def run(
        self,
        requirements: str,
        data: str,
        max_attempts: int = 3,
        progress_path: Path | None = None,
        reset_progress: bool = True,
    ) -> DesignResult:
        feedback = ""
        if reset_progress:
            self.progress_entries = []
        self._record_progress(
            progress_path,
            "# Semantic Web Designer Progress\n\n"
            f"- Model: `{self.model}`\n"
            f"- Mode: `{self.mode}`\n"
            f"- Max attempts: {max_attempts}\n"
            f"- Started: {self._timestamp()}\n",
        )
        for attempt in range(1, max_attempts + 1):
            prompt = self._designer_prompt().format(
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
                payload = self._parse_design_payload(text, progress_path)
                design_markdown = str(payload["design_markdown"]).strip()
                ontology_turtle = str(payload["ontology_turtle"]).strip()
                graph = parse_turtle(ontology_turtle)
                if len(graph) < 20:
                    raise ValueError("Ontology has fewer than 20 triples.")
                if len(graph) > self.ontology_triple_limit:
                    raise ValueError(
                        f"Ontology has {len(graph)} triples, which exceeds the "
                        f"configured {self.ontology_triple_limit} triple limit for {self.mode} mode."
                    )
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

    def _parse_design_payload(self, text: str, progress_path: Path | None = None) -> dict:
        try:
            return parse_json_object(text)
        except Exception as exc:
            self._record_progress(
                progress_path,
                "## JSON Repair\n\n"
                f"- Status: started\n"
                f"- Reason: {type(exc).__name__}: {exc}\n",
            )
            repaired = get_text_response(
                self.model,
                DESIGN_JSON_REPAIR_PROMPT.format(text=text),
                self.timeout_seconds,
            )
            self._record_progress(
                progress_path,
                "## JSON Repair Result\n\n"
                f"- Status: received\n"
                f"- Response characters: {len(repaired)}\n",
            )
            return parse_json_object(repaired)

    def _designer_prompt(self) -> str:
        if self.mode == "production":
            return PRODUCTION_DESIGNER_PROMPT
        return TEST_DESIGNER_PROMPT

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
