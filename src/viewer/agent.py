from __future__ import annotations

from dataclasses import dataclass

from src.common.llm import LlmError, get_text_response, parse_json_object
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
- Avoid technical words like "database", "dataset", "graph", "triple",
  "semantic web", "node", "predicate", "subject", "object", "URI", or "label"
  unless the user asks about technical implementation.
- Do not say "the database says", "the graph contains", "there is a label",
  "a node has", or similar implementation-facing phrasing.
- Do not paste raw query rows, triples, predicate names, JSON, SPARQL, or field
  names.
- Mention a URI only when no readable name exists and the user needs an
  identifier.
- If information is missing, say "I cannot find that information in the
  records" or "I do not see that detail in the available records." It is fine
  to add "I did find X, which may be relevant."
- If the user uses an imprecise term, infer the closest graph concept from
  labels, class names, property names, descriptions, and conversation history.
- Pay attention to common abbreviations, acronyms, plural forms, and shortened
  labels when matching the user's wording to graph concepts.
- If the records have a close concept but lack specific facts, explain that in
  plain language and suggest 2 or 3 useful related questions the user can ask.
- If there is genuinely not enough evidence, say what you can tell from nearby
  facts and suggest what to search next. Do not invent missing source facts.
- If the user's wording contains an abbreviation, acronym, or term that you
  cannot confidently connect to the graph facts or conversation history, ask a
  brief clarification question such as "What does XXX mean in your question?"
  or "Can you be more specific about XXX?".
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


CLASS_MATCH_PROMPT = """You are helping a semantic web viewer choose which ontology classes to query.

The user may use ordinary words that do not exactly match designer-generated
class names. Choose classes from the provided class summary when they are
plausible semantic matches for the user's wording or conversation history.

Return exactly one JSON object:
- class_labels: an array of class labels from the class summary.

Rules:
- Use only labels that appear in the class summary.
- Return at most 3 labels.
- Include a class only when it is a plausible match for the user's question.
- Prefer classes that answer count/list/who/what questions about groups of
  instances.
- Return an empty array when no class is a plausible match.

User question:
{question}

Conversation history:
{history}

Class summary:
{classes}
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
        facts = []
        if hasattr(query_service, "subject_facts_matching_question_labels"):
            facts.extend(query_service.subject_facts_matching_question_labels(question))
        for fact in query_service.search_facts(question):
            if fact not in facts:
                facts.append(fact)
        if hasattr(query_service, "semantic_search_facts"):
            for fact in query_service.semantic_search_facts(question):
                if fact not in facts:
                    facts.append(fact)
        matched_labels: set[str] = set()
        class_facts, direct_labels = _class_label_facts(question, summary, query_service)
        facts.extend(class_facts)
        matched_labels.update(direct_labels)
        if not matched_labels:
            for fact in _llm_matched_class_facts(
                question=question,
                history=history or "- No previous turns in this chat session.",
                summary=summary,
                query_service=query_service,
                model=self.model,
                timeout_seconds=self.timeout_seconds,
            ):
                if fact not in facts:
                    facts.append(fact)
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
) -> tuple[list[dict[str, str]], set[str]]:
    question_text = question.lower()
    rows: list[dict[str, str]] = []
    matched_labels: set[str] = set()
    classes = summary.get("classes", [])
    if not isinstance(classes, list):
        return rows, matched_labels
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
            matched_label = label or local_name
            matched_labels.add(matched_label)
            if hasattr(query_service, "class_instance_count_by_label"):
                rows.append(
                    {
                        "class": class_uri,
                        "classLabel": matched_label,
                        "classInstanceCount": str(query_service.class_instance_count_by_label(matched_label)),
                    }
                )
            rows.extend(query_service.class_instances_by_label(matched_label, limit=200))
    return rows, matched_labels


def _llm_matched_class_facts(
    question: str,
    history: str,
    summary: dict[str, object],
    query_service: ViewerQueryService,
    model: str,
    timeout_seconds: int,
) -> list[dict[str, str]]:
    class_rows = _class_summary_rows(summary)
    if not class_rows:
        return []
    prompt = CLASS_MATCH_PROMPT.format(
        question=question,
        history=history,
        classes=_format_rows(class_rows),
    )
    try:
        payload = parse_json_object(get_text_response(model, prompt, timeout_seconds))
    except (LlmError, ValueError):
        return []
    requested = payload.get("class_labels", [])
    if not isinstance(requested, list):
        return []
    allowed = {row["label"] for row in class_rows if row.get("label")}
    rows: list[dict[str, str]] = []
    for raw_label in requested[:3]:
        label = str(raw_label).strip()
        if label not in allowed:
            continue
        if hasattr(query_service, "class_instance_count_by_label"):
            rows.append(
                {
                    "classLabel": label,
                    "classInstanceCount": str(query_service.class_instance_count_by_label(label)),
                    "matchSource": "llm_class_match",
                }
            )
        rows.extend(query_service.class_instances_by_label(label, limit=200))
    return rows


def _class_summary_rows(summary: dict[str, object]) -> list[dict[str, str]]:
    classes = summary.get("classes", [])
    if not isinstance(classes, list):
        return []
    rows: list[dict[str, str]] = []
    for item in classes[:80]:
        if not isinstance(item, dict):
            continue
        class_uri = str(item.get("class") or "").strip()
        label = str(item.get("label") or "").strip() or _split_camel(_local_name(class_uri))
        if not label:
            continue
        row = {
            "label": label,
            "localName": _local_name(class_uri),
        }
        comment = str(item.get("comment") or "").strip()
        if comment:
            row["comment"] = comment
        rows.append(row)
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
