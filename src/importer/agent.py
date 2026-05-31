from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rdflib import Graph

from src.common.llm import get_text_response, parse_json_object
from src.common.rdf import parse_turtle
from src.importer.validation import inspect_ontology_terms, validate_instance_graph


IMPORTER_PROMPT = """You are the semantic web importer agent for this project.

Create RDF instance data from the supplied source data using the supplied
semantic web design and ontology. The application is general-purpose: do not
assume any sample domain unless it appears in the input.

Return exactly one JSON object with this key:
- instances_turtle: valid Turtle containing instance data only.

Importer requirements:
- Use the existing ontology classes and properties from the ontology Turtle.
- Do not change the ontology or define new rdfs:Class or rdf:Property terms.
- Do not add schema triples such as rdfs:domain, rdfs:range, or rdfs:subClassOf.
- Create stable, readable instance URIs in the ontology namespace or another
  clearly related instance namespace.
- Use rdf:type for instance classes and ontology-defined properties for facts.
- Use rdfs:label where helpful for human-readable names.
- Preserve source facts faithfully. Prefer concise literal text when the
  ontology does not model a detail structurally.
- If the ontology cannot represent a detail exactly, use the closest existing
  ontology property. Do not invent a new schema property.
- The Turtle must parse with rdflib.

Semantic web design document:
{design_text}

Ontology terms:
{ontology_terms}

Ontology Turtle:
{ontology_turtle}

Source data:
{source_data}
"""


IMPORT_FOCUS_PLANNER_PROMPT = """You are planning the next semantic-search batch for a semantic web importer.

The importer has a fixed ontology and must create instance data from source
facts without changing the schema. Decide whether import coverage appears
complete. If not complete, propose one focused semantic-search query for the
next import batch.

Return exactly one JSON object with these keys:
- complete: true or false.
- query: a concise semantic-search query for the next batch, or an empty string
  if complete is true.
- purpose: why this batch should be imported next, or why coverage is complete.

Rules:
- Use the design document, ontology terms, data inventory, and existing
  imported instance summary.
- Focus on source facts that can be represented by the existing ontology.
- Avoid duplicate batches already represented in existing instances.
- If the existing instances already cover the relevant source facts visible in
  the inventory and design, set complete to true.

Semantic web design document:
{design_text}

Ontology terms:
{ontology_terms}

Data inventory:
{data_inventory}

Existing imported instance summary:
{existing_instances}
"""


IMPORT_SLICE_PROMPT = """You are generating one validated slice of RDF instance data.

Create instance Turtle for only the current import focus using the retrieved
source facts and retrieved ontology context. Do not repeat facts that already
appear in the existing imported instance summary. Do not define new classes,
properties, domains, ranges, or subclass relationships.

Return exactly one JSON object with this key:
- instances_turtle: valid Turtle containing instance data for this slice only.

Importer requirements:
- Use only existing ontology classes and properties.
- Do not change the ontology or define new rdfs:Class or rdf:Property terms.
- Use rdf:type for instance classes and ontology-defined properties for facts.
- Use rdfs:label where helpful.
- Preserve source facts faithfully.
- If a fact cannot be represented with the retrieved ontology context, skip it.
- The Turtle must parse with rdflib.

Semantic web design document:
{design_text}

Ontology terms:
{ontology_terms}

Current import focus query:
{query}

Current import focus purpose:
{purpose}

Retrieved ontology context:
{ontology_turtle}

Retrieved source data:
{source_data}

Existing imported instance summary:
{existing_instances}
"""


@dataclass(frozen=True)
class ImportFocus:
    complete: bool
    query: str
    purpose: str


@dataclass
class ImportResult:
    instances_turtle: str
    graph: Graph
    progress_markdown: str = ""


class ImporterAgent:
    def __init__(self, model: str, timeout_seconds: int = 90):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.progress_entries: list[str] = []

    def plan_import_focus(
        self,
        design_text: str,
        ontology_graph: Graph,
        data_inventory: str,
        existing_instances: str,
        progress_path: Path | None = None,
    ) -> ImportFocus:
        ontology_terms = inspect_ontology_terms(ontology_graph).summary()
        prompt = IMPORT_FOCUS_PLANNER_PROMPT.format(
            design_text=design_text,
            ontology_terms=ontology_terms,
            data_inventory=data_inventory,
            existing_instances=existing_instances,
        )
        self._record_progress(
            progress_path,
            "## Import Focus Planning\n\n"
            f"- Status: LLM request started\n"
            f"- Timestamp: {self._timestamp()}\n",
        )
        text = self._run_direct_import_call(prompt)
        payload = parse_json_object(text)
        focus = ImportFocus(
            complete=bool(payload.get("complete", False)),
            query=str(payload.get("query", "")).strip(),
            purpose=str(payload.get("purpose", "")).strip(),
        )
        if not focus.complete and not focus.query:
            focus = ImportFocus(
                complete=False,
                query=design_text[:500],
                purpose="Fallback import coverage from the design document.",
            )
        self._record_progress(
            progress_path,
            "## Import Focus Planning Result\n\n"
            f"- Status: passed\n"
            f"- Complete: {focus.complete}\n"
            f"- Query: {focus.query}\n"
            f"- Purpose: {focus.purpose}\n",
        )
        return focus

    def generate_instance_slice(
        self,
        design_text: str,
        ontology_turtle: str,
        ontology_graph: Graph,
        source_data: str,
        focus: ImportFocus,
        existing_instances: str,
        max_attempts: int = 2,
        progress_path: Path | None = None,
    ) -> ImportResult:
        feedback = ""
        ontology_terms = inspect_ontology_terms(ontology_graph).summary()
        for attempt in range(1, max_attempts + 1):
            prompt = IMPORT_SLICE_PROMPT.format(
                design_text=design_text,
                ontology_terms=ontology_terms,
                query=focus.query,
                purpose=focus.purpose,
                ontology_turtle=ontology_turtle,
                source_data=source_data,
                existing_instances=existing_instances,
            )
            if feedback:
                prompt += (
                    "\n\nYour previous slice failed validation. Fix the problem and "
                    f"return the full JSON object again.\nValidation feedback:\n{feedback}"
                )
            self._record_progress(
                progress_path,
                "## Import Slice Generation\n\n"
                f"- Status: LLM request started\n"
                f"- Timestamp: {self._timestamp()}\n"
                f"- Query: {focus.query}\n"
                f"- Attempt: {attempt}\n",
            )
            try:
                text = self._run_direct_import_call(prompt)
                payload = parse_json_object(text)
                instances_turtle = str(payload["instances_turtle"]).strip()
                graph = parse_turtle(instances_turtle)
                validate_instance_graph(graph, ontology_graph).raise_for_errors()
                self._record_progress(
                    progress_path,
                    "## Import Slice Validation\n\n"
                    f"- Status: passed\n"
                    f"- Query: {focus.query}\n"
                    f"- Triple count: {len(graph)}\n",
                )
                return ImportResult(
                    instances_turtle=instances_turtle,
                    graph=graph,
                    progress_markdown=self._progress_markdown(),
                )
            except Exception as exc:
                feedback = f"Attempt {attempt} failed: {type(exc).__name__}: {exc}"
                self._record_progress(
                    progress_path,
                    "## Import Slice Validation\n\n"
                    f"- Status: failed\n"
                    f"- Query: {focus.query}\n"
                    f"- Feedback: {feedback}\n",
                )
        raise RuntimeError(f"Import slice failed after {max_attempts} attempts. {feedback}")

    def run(
        self,
        design_text: str,
        ontology_turtle: str,
        ontology_graph: Graph,
        source_data: str,
        max_attempts: int = 3,
        progress_path: Path | None = None,
    ) -> ImportResult:
        feedback = ""
        self.progress_entries = []
        self._record_progress(
            progress_path,
            "# Semantic Web Importer Progress\n\n"
            f"- Model: `{self.model}`\n"
            f"- Max attempts: {max_attempts}\n"
            f"- Started: {self._timestamp()}\n",
        )
        ontology_terms = inspect_ontology_terms(ontology_graph).summary()
        for attempt in range(1, max_attempts + 1):
            prompt = IMPORTER_PROMPT.format(
                design_text=design_text,
                ontology_terms=ontology_terms,
                ontology_turtle=ontology_turtle,
                source_data=source_data,
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
                text = self._run_direct_import_call(prompt)
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
                instances_turtle = str(payload["instances_turtle"]).strip()
                graph = parse_turtle(instances_turtle)
                validate_instance_graph(graph, ontology_graph).raise_for_errors()
                self._record_progress(
                    progress_path,
                    f"## Attempt {attempt} Validation\n\n"
                    f"- Status: passed\n"
                    f"- Triple count: {len(graph)}\n",
                )
                return ImportResult(
                    instances_turtle=instances_turtle,
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
        raise RuntimeError(f"Importer failed after {max_attempts} attempts. {feedback}")

    def _run_direct_import_call(self, prompt: str) -> str:
        return get_text_response(self.model, prompt, self.timeout_seconds)

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
