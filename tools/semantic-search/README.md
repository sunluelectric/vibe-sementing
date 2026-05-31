# Semantic Search Document Tool

This project is a local document semantic-search and question-answering tool built with the OpenAI Agents SDK. It is intended to be used by another agentic AI as a callable tool over a folder of local PDF/HTML documents.

## Tool Contract

Use this project when an agent needs to answer questions from local documents.

Input:

- Documents in `DOC_PATH`, default `./docs`.
- A natural-language question.
- `OPENAI_API_KEY` and model configuration in `.env`.

Output:

- A concise natural-language answer grounded in the indexed documents.
- Optional generated records for unknown questions or improvement suggestions.

Persistent state:

- `parsed_chunks.json`: extracted text chunks.
- `embeddings.npy`: OpenAI embedding vectors for those chunks.
- `history.json`: CLI conversation history.
- `unknown_questions.json`: questions the agent could not answer from the documents.
- `suggestions.json`: improvement suggestions recorded by the agent.

## What It Does

1. Scans `DOC_PATH` for top-level `.pdf`, `.html`, `.htm`, `.md`, `.txt`, and
   `.csv` files.
2. Extracts PDF text with PyMuPDF, HTML text with BeautifulSoup, markdown and
   text files directly, and CSV content with pandas.
3. Splits text into chunks using `tiktoken`.
4. Embeds chunks with the configured OpenAI embedding model.
5. Caches chunks and embeddings locally.
6. Runs an OpenAI Agents SDK agent that can call semantic-search tools over the cached document chunks.
7. Returns a structured `SearchAgentOutput` object with one field:

```json
{
  "search_result": "answer text"
}
```

## Requirements

- Python 3.12+
- `uv` recommended
- OpenAI API key

Install dependencies:

```bash
uv sync
```

## Configuration

Create `.env` in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-5-mini
EMBEDDING_MODEL=text-embedding-3-small
DOC_PATH=./docs
TOP_N_DEFAULT=10
TOP_N_MAX=25
SEMANTIC_SEARCH_MAX=5
EMBEDDING_MAX_TOKENS=2000
EMBEDDING_OVERLAP=200
```

Configuration fields:

- `OPENAI_API_KEY`: required for embeddings and LLM calls.
- `LLM_MODEL`: model used by the answer agent.
- `EMBEDDING_MODEL`: model used to embed documents and search queries.
- `DOC_PATH`: directory containing source documents.
- `TOP_N_DEFAULT`: number of chunks returned by default in each semantic search.
- `TOP_N_MAX`: maximum chunks returnable after `request_increasing_top_n`.
- `SEMANTIC_SEARCH_MAX`: maximum semantic searches per user question.
- `EMBEDDING_MAX_TOKENS`: approximate max tokens per chunk.
- `EMBEDDING_OVERLAP`: overlap size used when creating chunks.

## Document Setup

Place documents directly inside `DOC_PATH`:

```text
docs/
├── paper.pdf
├── manual.html
├── notes.htm
├── requirements.md
├── records.csv
└── notes.txt
```

Current limitation: `DOC_PATH` is not scanned recursively. Put files directly in `./docs`, or set `DOC_PATH` to the exact directory containing the files.

## CLI Usage

Run the interactive command-line app:

```bash
uv run python document_explainer.py
```

Then ask questions:

```text
You: What is the main contribution of this paper?
Bot:
...
---
You: quit
```

The first run may be slow because it extracts text and creates embeddings. Later runs reuse `parsed_chunks.json` and `embeddings.npy`.

## Programmatic Usage For Agents

An agentic AI or vibe-coding agent can import and call the tool from Python.

```python
import asyncio
import document_explainer as de

async def ask_document(question: str, history: list[dict] | None = None) -> str:
    if history is None:
        history = []

    # Required because the tool functions resolve the active instance
    # through the module-level `explainer` variable.
    de.explainer = de.DocumentExplainer()

    de.explainer.semantic_search_num = 0
    de.explainer.top_n = de.TOP_N_DEFAULT

    response = await de.explainer.chat(question, history)
    return response.search_result

answer = asyncio.run(ask_document("What are the key results in the document?"))
print(answer)
```

For multiple questions in one session, reuse the same `DocumentExplainer` instance and keep a history list:

```python
import asyncio
import document_explainer as de

QUESTIONS = [
    "What problem does the document address?",
    "What method does it propose?",
    "What evidence or benchmarks support the claims?",
]

async def main():
    de.explainer = de.DocumentExplainer()
    history = []

    for question in QUESTIONS:
        de.explainer.semantic_search_num = 0
        de.explainer.top_n = de.TOP_N_DEFAULT

        response = await de.explainer.chat(question, history)
        answer = response.search_result

        print(f"Q: {question}")
        print(f"A: {answer}\n")

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

asyncio.run(main())
```

## Internal Agent Tools

The OpenAI Agents SDK search agent receives these tool functions:

- `semantic_search(query: str)`: embeds `query`, compares it against cached document embeddings using cosine similarity, and returns the top chunks.
- `request_increasing_top_n()`: increases the retrieval count by 5 until `TOP_N_MAX`.
- `record_unknown_question(question: str)`: appends a JSON line to `unknown_questions.json`.
- `record_suggestion(suggestion: str)`: appends a JSON line to `suggestions.json`.

Agents should usually call `chat(...)`, not these tools directly. The internal agent decides when to call them.

## Cache Behavior

The cache is keyed only by file existence, not by document content hashes.

If documents change, are added, or are removed, delete the cache before running again:

```bash
rm -f parsed_chunks.json embeddings.npy
```

Otherwise the tool may keep answering from old chunks.

## Expected Behavior

Good questions:

- "Summarize the main contribution of the paper."
- "What method is proposed?"
- "Which experiments or benchmarks are reported?"
- "What limitations does the document mention?"
- "Compare section X and section Y."

Poor questions:

- Questions requiring current internet knowledge.
- Questions about files outside `DOC_PATH`.
- Questions that require unsupported file formats such as `.docx`, `.txt`, or `.md`.

If the document evidence is missing, the agent should say so and may record the question with `record_unknown_question`.

## Troubleshooting

`ModuleNotFoundError`:

```bash
uv sync
uv run python document_explainer.py
```

No documents found or zero chunks:

- Confirm `DOC_PATH` points to the intended folder.
- Confirm files are directly in that folder.
- Confirm files use `.pdf`, `.html`, or `.htm` extensions.
- Delete `parsed_chunks.json` and `embeddings.npy` after changing documents.

OpenAI errors:

- Confirm `OPENAI_API_KEY` is set in `.env`.
- Confirm the account has access to `LLM_MODEL` and `EMBEDDING_MODEL`.
- Confirm there is enough API quota.

Stale answers:

- Delete `parsed_chunks.json` and `embeddings.npy`, then rerun the tool.

## Project Files

- `document_explainer.py`: main implementation and CLI.
- `main.py`: placeholder package scaffold entry point.
- `pyproject.toml`: Python package metadata and dependencies.
- `uv.lock`: locked dependencies.
- `.python-version`: Python version hint.
- `.gitignore`: ignores secrets, document inputs, generated caches, and local editor files.

## Non-Goals

- No internet search.
- No online cross-checking.
- No Serper dependency.
- No recursive document discovery.
- No vector database server.

## License

MIT License. See `LICENSE`.
