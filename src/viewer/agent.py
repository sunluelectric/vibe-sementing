from __future__ import annotations

from dataclasses import dataclass

from src.common.llm import get_text_response
from src.viewer.query import ViewerQueryService


VIEWER_PROMPT = """You are the semantic web viewer agent for this project.

Answer the user's question using only the graph facts supplied below. The
application is general-purpose, so do not assume a sample domain unless it is
present in the facts. Be concise and cite the graph resources or labels that
support the answer. If the facts are insufficient, say what is missing and do
not invent an answer.

User question:
{question}

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

    def answer(self, question: str, query_service: ViewerQueryService) -> ViewerAnswer:
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
        label = str(item.get("label") or item.get("class") or "").strip()
        if not label:
            continue
        variants = {label.lower(), label.lower() + "s"}
        if any(variant in question_text for variant in variants):
            rows.extend(query_service.class_instances_by_label(label, limit=30))
    return rows
