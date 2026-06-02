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
- If the supplied facts include probable class labels but no matching instance
  facts, ask the user which label they mean and list the likely labels in plain
  language.
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

Design document excerpt:
{design}
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
        design_text: str = "",
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
            llm_class_facts, llm_labels = _llm_matched_class_facts(
                question=question,
                history=history or "- No previous turns in this chat session.",
                summary=summary,
                design_text=design_text,
                query_service=query_service,
                model=self.model,
                timeout_seconds=self.timeout_seconds,
            )
            matched_labels.update(llm_labels)
            for fact in llm_class_facts:
                if fact not in facts:
                    facts.append(fact)
        if not matched_labels:
            for fact in _probable_class_label_facts(question, summary):
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
    design_text: str,
    query_service: ViewerQueryService,
    model: str,
    timeout_seconds: int,
) -> tuple[list[dict[str, str]], set[str]]:
    class_rows = _class_summary_rows(summary)
    if not class_rows:
        return [], set()
    prompt = CLASS_MATCH_PROMPT.format(
        question=question,
        history=history,
        classes=_format_rows(class_rows),
        design=_design_excerpt(design_text),
    )
    try:
        payload = parse_json_object(get_text_response(model, prompt, timeout_seconds))
    except (LlmError, ValueError):
        return [], set()
    requested = payload.get("class_labels", [])
    if not isinstance(requested, list):
        return [], set()
    allowed = {row["label"] for row in class_rows if row.get("label")}
    labels = []
    for raw_label in requested[:3]:
        label = str(raw_label).strip()
        if label in allowed and label not in labels:
            labels.append(label)
    rows: list[dict[str, str]] = []
    if len(labels) > 1:
        for label in labels:
            rows.append({"probableClassLabel": label, "matchSource": "llm_class_ambiguity"})
        return rows, set()
    matched_labels: set[str] = set()
    for label in labels:
        matched_labels.add(label)
        if hasattr(query_service, "class_instance_count_by_label"):
            rows.append(
                {
                    "classLabel": label,
                    "classInstanceCount": str(query_service.class_instance_count_by_label(label)),
                    "matchSource": "llm_class_match",
                }
            )
        rows.extend(query_service.class_instances_by_label(label, limit=200))
    return rows, matched_labels


def _probable_class_label_facts(question: str, summary: dict[str, object], limit: int = 3) -> list[dict[str, str]]:
    class_rows = _class_summary_rows(summary)
    if not class_rows:
        return []
    question_terms = set(_tokens(question))
    scored: list[tuple[int, dict[str, str]]] = []
    for row in class_rows:
        haystack = " ".join(str(row.get(key, "")) for key in ("label", "localName", "comment"))
        score = len(question_terms.intersection(_tokens(haystack)))
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], item[1].get("label", "")))
    facts: list[dict[str, str]] = []
    for _score, row in scored[:limit]:
        fact = {
            "probableClassLabel": row["label"],
            "matchSource": "probable_class_label",
        }
        if row.get("comment"):
            fact["comment"] = row["comment"]
        if row.get("localName"):
            fact["localName"] = row["localName"]
        facts.append(fact)
    return facts


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


def _design_excerpt(design_text: str, max_chars: int = 4000) -> str:
    text = design_text.strip()
    if not text:
        return "- No design document was available."
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[truncated]"


def _tokens(text: str) -> list[str]:
    normalized = []
    for char in text.lower():
        normalized.append(char if char.isalnum() else " ")
    terms: list[str] = []
    for term in "".join(normalized).split():
        if len(term) < 3:
            continue
        if term in {"the", "and", "for", "with", "about", "from", "that", "this", "what", "which", "list"}:
            continue
        terms.append(term)
    return terms


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
