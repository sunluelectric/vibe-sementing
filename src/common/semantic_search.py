from __future__ import annotations

import csv
import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from rdflib import Graph, Literal, RDF, RDFS, URIRef

from src.common.config import Settings
from src.common.files import read_text


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class SemanticChunk:
    id: str
    source: str
    kind: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticSearchResult:
    chunk: SemanticChunk
    score: float


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingProvider:
    """Deterministic lexical vectorizer used for tests and offline retrieval."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            index = _stable_index(token, self.dimensions)
            vector[index] += 1.0
            if len(token) > 4:
                stem = token[: max(4, len(token) - 1)]
                vector[_stable_index(stem, self.dimensions)] += 0.35
        return _normalize(vector)


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str | None, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embedding search.")
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]


class SemanticIndex:
    def __init__(self, chunks: list[SemanticChunk], embeddings: list[list[float]], provider: EmbeddingProvider):
        self.chunks = chunks
        self.embeddings = embeddings
        self.provider = provider

    @classmethod
    def from_chunks(cls, chunks: list[SemanticChunk], provider: EmbeddingProvider) -> "SemanticIndex":
        return cls(chunks=chunks, embeddings=provider.embed([chunk.text for chunk in chunks]), provider=provider)

    def search(self, query: str, top_k: int = 8) -> list[SemanticSearchResult]:
        if not self.chunks:
            return []
        query_embedding = self.provider.embed([query])[0]
        scored = [
            SemanticSearchResult(chunk=chunk, score=_cosine(query_embedding, embedding))
            for chunk, embedding in zip(self.chunks, self.embeddings, strict=True)
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]


def provider_from_settings(settings: Settings) -> EmbeddingProvider:
    if settings.semantic_search_provider.lower() == "openai":
        return OpenAIEmbeddingProvider(settings.openai_api_key, settings.embedding_model)
    return LocalEmbeddingProvider()


def select_context(
    chunks: list[SemanticChunk],
    query: str,
    settings: Settings,
    provider: EmbeddingProvider | None = None,
) -> str:
    results = search_chunks(chunks, query, settings, provider)
    return _join_chunks([result.chunk for result in results], settings.semantic_context_max_chars)


def search_chunks(
    chunks: list[SemanticChunk],
    query: str,
    settings: Settings,
    provider: EmbeddingProvider | None = None,
) -> list[SemanticSearchResult]:
    if not settings.semantic_search_enabled:
        return [SemanticSearchResult(chunk=chunk, score=0.0) for chunk in chunks[: settings.semantic_search_top_k]]
    provider = provider or provider_from_settings(settings)
    return SemanticIndex.from_chunks(chunks, provider).search(
        query,
        top_k=settings.semantic_search_top_k,
    )


def chunks_from_data_dir(data_dir: Path, max_chunk_chars: int = 3500, overlap_chars: int = 350) -> list[SemanticChunk]:
    chunks: list[SemanticChunk] = []
    for path in sorted(data_dir.glob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        if suffix in {".md", ".txt"}:
            chunks.extend(chunks_from_text(path.name, read_text(path), suffix.lstrip("."), max_chunk_chars, overlap_chars))
        elif suffix == ".csv":
            chunks.extend(chunks_from_csv(path, max_chunk_chars))
    return chunks


def chunks_from_text(
    source: str,
    text: str,
    kind: str = "text",
    max_chunk_chars: int = 3500,
    overlap_chars: int = 350,
) -> list[SemanticChunk]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[SemanticChunk] = []
    current = ""
    index = 1
    for paragraph in paragraphs or [text.strip()]:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chunk_chars:
            current = candidate
            continue
        if current:
            chunks.append(_chunk(source, kind, index, current))
            index += 1
        current = _overlap(current, overlap_chars, paragraph)
        while len(current) > max_chunk_chars:
            chunks.append(_chunk(source, kind, index, current[:max_chunk_chars]))
            index += 1
            current = current[max(0, max_chunk_chars - overlap_chars) :]
    if current:
        chunks.append(_chunk(source, kind, index, current))
    return chunks


def chunks_from_csv(path: Path, max_chunk_chars: int = 3500) -> list[SemanticChunk]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        columns = reader.fieldnames or []
    header = f"CSV file: {path.name}\nColumns: {', '.join(columns)}"
    chunks: list[SemanticChunk] = []
    current_rows: list[str] = []
    current_size = len(header)
    index = 1
    for row_number, row in enumerate(rows, start=1):
        line = f"Row {row_number}: " + "; ".join(
            f"{column}: {row.get(column, '')}" for column in columns
        )
        if current_rows and current_size + len(line) + 1 > max_chunk_chars:
            chunks.append(_chunk(path.name, "csv", index, header + "\n" + "\n".join(current_rows)))
            index += 1
            current_rows = []
            current_size = len(header)
        current_rows.append(line)
        current_size += len(line) + 1
    if current_rows or not rows:
        body = "\n".join(current_rows) if current_rows else "No rows."
        chunks.append(_chunk(path.name, "csv", index, header + "\n" + body))
    return chunks


def chunks_from_graph(graph: Graph, source: str = "rdf-graph") -> list[SemanticChunk]:
    label_map = {
        subject: str(label)
        for subject, label in graph.subject_objects(RDFS.label)
        if isinstance(subject, URIRef)
    }
    chunks: list[SemanticChunk] = []
    for index, subject in enumerate(sorted(set(graph.subjects()), key=str), start=1):
        lines = [f"Subject: {_term_text(subject, label_map)}"]
        for predicate, object_value in sorted(graph.predicate_objects(subject), key=lambda item: (str(item[0]), str(item[1]))):
            if predicate == RDFS.label:
                continue
            lines.append(f"{_term_text(predicate, label_map)}: {_term_text(object_value, label_map)}")
        chunks.append(
            SemanticChunk(
                id=f"{source}:{index}",
                source=source,
                kind="rdf",
                text="\n".join(lines),
                metadata={"subject": str(subject)},
            )
        )
    return chunks


def rows_to_chunks(rows: list[dict[str, str]], source: str, kind: str = "sparql-row") -> list[SemanticChunk]:
    chunks: list[SemanticChunk] = []
    for index, row in enumerate(rows, start=1):
        text = "\n".join(f"{key}: {value}" for key, value in sorted(row.items()))
        chunks.append(
            SemanticChunk(
                id=f"{source}:{index}",
                source=source,
                kind=kind,
                text=text,
                metadata={key: value for key, value in row.items()},
            )
        )
    return chunks


def format_context(chunks: list[SemanticChunk]) -> str:
    return _join_chunks(chunks, max_chars=10**9)


def _chunk(source: str, kind: str, index: int, text: str) -> SemanticChunk:
    return SemanticChunk(
        id=f"{source}:{index}",
        source=source,
        kind=kind,
        text=text.strip(),
    )


def _join_chunks(chunks: list[SemanticChunk], max_chars: int) -> str:
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        part = f"# Source chunk: {chunk.source} [{chunk.kind}]\n\n{chunk.text.strip()}"
        if not parts and len(part) > max_chars:
            return part[:max_chars].rstrip()
        if parts and total + len(part) + 2 > max_chars:
            break
        parts.append(part)
        total += len(part) + 2
    return "\n\n".join(parts).strip()


def _overlap(previous: str, overlap_chars: int, next_text: str) -> str:
    if not previous or overlap_chars <= 0:
        return next_text
    return f"{previous[-overlap_chars:]}\n\n{next_text}".strip()


def _term_text(value, labels: dict[URIRef, str]) -> str:
    if isinstance(value, Literal):
        return str(value)
    if isinstance(value, URIRef):
        label = labels.get(value)
        local = _local_name(str(value))
        if value == RDF.type:
            local = "type"
        return f"{label} ({local}, {value})" if label and label != local else f"{local} ({value})"
    return str(value)


def _local_name(uri: str) -> str:
    if "#" in uri:
        return uri.rsplit("#", 1)[1]
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def _stable_index(token: str, dimensions: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % dimensions


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))
