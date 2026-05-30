from __future__ import annotations

from dataclasses import dataclass

from rdflib import Graph

from src.common.llm import get_text_response, parse_json_object
from src.common.rdf import parse_turtle
from src.designer.validation import validate_ontology_graph


DESIGNER_PROMPT = """You are the semantic web designer agent for this project.

Design a deliberately simple RDF/RDFS semantic web schema for the user's data
and design requirements. Do not make a complex or exhaustive ontology. The goal
of this first version is a small, correct, easy-to-import schema that can be
loaded into Apache Jena Fuseki and improved later.

Use RDF and RDFS only. Do not use OWL in this first version. You are designing
the schema; do not insert individual adventure instances.

Return exactly one JSON object with these keys:
- design_markdown: a complete design document for design.md.
- ontology_turtle: valid Turtle containing the ontology/schema.

Ontology requirements:
- Base namespace: http://example.org/dnd-adventure#
- Prefixes must include dnd, rdf, rdfs, xsd.
- Keep the ontology around 12 to 18 classes and 20 to 35 properties.
- Include simple classes for Adventure, Quest, Scene, Location, Character, Npc,
  Monster, PlayerOption, Item, Weapon, Encounter, Check, Reward, and
  VictoryCondition.
- Include a shallow subclass hierarchy only where obvious, such as Npc and
  Monster as subclasses of Character, and Weapon as a subclass of Item.
- Include practical object and datatype properties with rdfs:domain and
  rdfs:range.
- Use rdfs:label and rdfs:comment on important classes and properties.
- Prefer broad reusable properties over highly specific one-off properties.
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


class DesignerAgent:
    def __init__(self, model: str, timeout_seconds: int = 90):
        self.model = model
        self.timeout_seconds = timeout_seconds

    def run(self, requirements: str, data: str, max_attempts: int = 3) -> DesignResult:
        feedback = ""
        for attempt in range(1, max_attempts + 1):
            prompt = DESIGNER_PROMPT.format(requirements=requirements, data=data)
            if feedback:
                prompt += (
                    "\n\nYour previous response failed validation. Fix the problem and "
                    f"return the full JSON object again.\nValidation feedback:\n{feedback}"
                )
            text = self._run_direct_design_call(prompt)
            try:
                payload = parse_json_object(text)
                design_markdown = str(payload["design_markdown"]).strip()
                ontology_turtle = str(payload["ontology_turtle"]).strip()
                graph = parse_turtle(ontology_turtle)
                if len(graph) < 20:
                    raise ValueError("Ontology has fewer than 20 triples.")
                if len(graph) > 260:
                    raise ValueError("Ontology is too complex for the first version.")
                validate_ontology_graph(graph).raise_for_errors()
                return DesignResult(design_markdown, ontology_turtle, graph)
            except Exception as exc:
                feedback = f"Attempt {attempt} failed: {type(exc).__name__}: {exc}"
        raise RuntimeError(f"Designer failed after {max_attempts} attempts. {feedback}")

    def _run_direct_design_call(self, prompt: str) -> str:
        return get_text_response(self.model, prompt, self.timeout_seconds)
