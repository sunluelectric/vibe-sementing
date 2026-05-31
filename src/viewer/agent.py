from __future__ import annotations

from dataclasses import dataclass

from src.common.llm import get_text_response
from src.viewer.query import ViewerQueryService


VIEWER_PROMPT = """You are the semantic web viewer chatbot for this project.

Answer for an end user, not for a tester or RDF engineer. The user wants a
useful domain answer, not raw semantic web query output.

Use only the graph facts supplied below, but translate them into ordinary
language:
- Start with the direct answer.
- Prefer names, labels, and short descriptions over URIs.
- Group repeated facts into readable lists.
- Do not say "there are N results in the semantic web".
- Avoid technical words like "dataset", "graph", "triple", or "semantic web"
  unless the user asks about technical implementation.
- Do not paste raw query rows, triples, predicate names, JSON, or SPARQL.
- Mention a URI only when no readable name or label exists.
- If the user uses an imprecise term, infer the closest graph concept from
  labels, class names, property names, descriptions, and conversation history.
- Pay attention to common abbreviations, acronyms, plural forms, and shortened
  labels when matching the user's wording to graph concepts.
- If the graph has a close concept but lacks instance facts, explain that in
  plain language and suggest 2 or 3 useful related questions the user can ask.
- If there is genuinely not enough evidence, say what you can tell from nearby
  facts and suggest what to search next. Do not invent missing source facts.
- Keep the answer concise unless the user asks for detail.

User question:
{question}

Conversation history:
{history}

Graph status:
{status}

Graph summary:
{summary}

Question-relevant graph facts:
{facts}
"""


@dataclass(frozen=True)
class ViewerAnswer:
    question: str
    answer: str
    facts: list[dict[str, str]]


class ViewerAgent:
    def __init__(self, model: str, timeout_seconds: int = 90):
        self.model = model
        self.timeout_seconds = timeout_seconds

    def answer(
        self,
        question: str,
        query_service: ViewerQueryService,
        history: str = "",
    ) -> ViewerAnswer:
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty.")

        status = query_service.status()
        if not status.available:
            raise RuntimeError(status.message)

        summary = query_service.graph_summary()
        facts = query_service.search_facts(question)
        facts.extend(_class_label_facts(question, summary, query_service))
        prompt = VIEWER_PROMPT.format(
            question=question,
            history=history or "- No previous turns in this chat session.",
            status=status,
            summary=_format_mapping(summary),
            facts=_format_rows(facts),
        )
        answer = get_text_response(self.model, prompt, self.timeout_seconds).strip()
        return ViewerAnswer(question=question, answer=answer, facts=facts)


def _format_mapping(mapping: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.append(_format_rows(value[:20]))
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines).strip()


def _format_rows(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "- No matching graph facts were returned."
    lines: list[str] = []
    for row in rows:
        parts = [f"{key}={value}" for key, value in sorted(row.items())]
        lines.append("- " + "; ".join(parts))
    return "\n".join(lines)


def _class_label_facts(
    question: str,
    summary: dict[str, object],
    query_service: ViewerQueryService,
) -> list[dict[str, str]]:
    question_text = question.lower()
    rows: list[dict[str, str]] = []
    classes = summary.get("classes", [])
    if not isinstance(classes, list):
        return rows
    for item in classes:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        class_uri = str(item.get("class") or "").strip()
        if not label and not class_uri:
            continue
        local_name = _local_name(class_uri)
        variants = _class_variants(label, local_name)
        if any(variant in question_text for variant in variants):
            rows.extend(query_service.class_instances_by_label(label or local_name, limit=30))
    return rows


def _class_variants(label: str, local_name: str) -> set[str]:
    variants: set[str] = set()
    for value in {label, local_name, _split_camel(local_name)}:
        cleaned = value.strip().lower()
        if not cleaned:
            continue
        variants.add(cleaned)
        variants.add(cleaned + "s")
        acronym = "".join(part[0] for part in cleaned.replace("-", " ").split() if part)
        if len(acronym) > 1:
            variants.add(acronym)
            variants.add(acronym + "s")
    return variants


def _local_name(uri: str) -> str:
    if "#" in uri:
        return uri.rsplit("#", 1)[1]
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _split_camel(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if index and char.isupper() and value[index - 1].islower():
            chars.append(" ")
        chars.append(char)
    return "".join(chars)
