# Semantic Web Processor

Semantic Web Processor turns local documents and tables into a queryable
semantic web.

It is built for the painful part of semantic-web work: starting from long,
messy, mixed input data and getting to a usable RDF/RDFS graph. You provide a
plain-language design requirement plus source files such as markdown, text,
PDF, and CSV. The application uses AI workflows to design an ontology, import
instances, store the result in Apache Jena Fuseki, and expose a browser chatbot
that answers questions by querying that semantic web.

If you are new to the topic, these W3C pages are good starting points:

- Semantic Web standards: <https://www.w3.org/standards/semanticweb/>
- OWL, the Web Ontology Language: <https://www.w3.org/OWL/>

This project focuses mainly on RDF and RDFS. OWL can appear in future schema
work, but complex OWL reasoning is not required for the current product.

## 1. Install Fuseki First

Apache Jena Fuseki is the triplestore used by this project. It stores the
ontology and imported data, answers SPARQL queries, and provides Turtle export.
The designer and importer can start Fuseki automatically when it is installed
in the expected location.

Official Fuseki documentation:

- Fuseki overview and download: <https://jena.apache.org/documentation/fuseki2/>
- Fuseki quickstart: <https://jena.apache.org/documentation/fuseki2/fuseki-quick-start.html>

### Linux Setup Used By This Project

The project expects Fuseki at:

```text
/opt/apache-jena-fuseki-6.1.0
```

Install Java first. On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install default-jre unzip
java -version
```

Download Apache Jena Fuseki from the official Jena download page, unzip it, and
place the unpacked folder under `/opt`. The downloaded version may be newer
than `6.1.0`; if so, either rename the folder or set `FUSEKI_HOME` in `.env`.

Example:

```bash
cd /tmp
# Download apache-jena-fuseki-VER.zip from the Apache Jena website.
unzip apache-jena-fuseki-VER.zip
sudo mv apache-jena-fuseki-VER /opt/apache-jena-fuseki-6.1.0
sudo chmod +x /opt/apache-jena-fuseki-6.1.0/fuseki-server
```

This project does not use Fuseki's default runtime directory under `/opt`.
Instead it uses writable project-local directories:

```text
db/fuseki-run
db/fuseki-data
db/fuseki.log
```

That matters because `/opt/apache-jena-fuseki-6.1.0/run` may not be writable by
your user account.

You do not normally need to start Fuseki yourself. The designer and importer
check whether Fuseki is reachable and start it when needed. If you want to test
Fuseki manually, run this from the project root after setup:

```bash
FUSEKI_BASE=/home/sunlu/Projects/semantic-web-processor/db/fuseki-run \
  /opt/apache-jena-fuseki-6.1.0/fuseki-server \
  --tdb2 \
  --loc=/home/sunlu/Projects/semantic-web-processor/db/fuseki-data \
  --update --localhost /semantic-web-processor
```

Then open:

```text
http://localhost:3030
```

Stop the manual server with `Ctrl+C` in that terminal.

## 2. What This Project Does

Semantic Web Processor has three independent applications.

| Application | Command | Job |
| --- | --- | --- |
| Designer | `uv run python -m src.designer.main` | Reads your requirements and data, designs an RDF/RDFS ontology, writes `design.md`, writes `db/ontology.ttl`, and loads the ontology into Fuseki. |
| Importer | `uv run python -m src.importer.main` | Reads the design and data, imports instances without changing the ontology, writes `import.md`, `db/instances.ttl`, and `db/semantic_web.ttl`, then loads instances into Fuseki. |
| Viewer | `uv run python -m src.viewer.main` | Starts a browser UI where you can ask questions and export the semantic web as Turtle. |

The key feature is mixed-data semantic-web generation:

- Long markdown, text, and PDF inputs can be chunked and retrieved instead of
  stuffed into one prompt.
- CSV files are profiled, mapped, validated, and imported deterministically row
  by row.
- Fuseki is the runtime source of truth shared by the designer, importer, and
  viewer.
- Turtle files are still written for review, validation, portability, export,
  and fallback.

## 3. What Problem It Solves

Building a semantic web by hand usually requires several hard steps:

1. Read a lot of source material.
2. Decide what classes and properties the ontology needs.
3. Convert many facts into valid RDF.
4. Keep structured tables consistent with the ontology.
5. Load the result into a triplestore.
6. Write SPARQL queries to use the data.

This project automates that workflow. The AI parts make design and extraction
decisions; Python validates the RDF, validates CSV mappings, performs
deterministic CSV conversion, and loads the result into Fuseki.

The result is not just a summary of documents. It is a semantic graph that can
be queried, exported, tested, and extended.

## 4. Install The Project

### Prerequisites

You need:

- Python 3.12 or newer.
- `uv` for Python dependency management.
- `git`.
- Java for Fuseki.
- Apache Jena Fuseki.
- An OpenAI API key.
- Internet access for OpenAI API calls and first-time dependency installation.

If `uv` is not installed yet, install it from the official uv instructions:

```text
https://docs.astral.sh/uv/getting-started/installation/
```

After installing it, check that your terminal can find it:

```bash
uv --version
```

### Get The Code

```bash
git clone <repository-url>
cd semantic-web-processor
```

If you already have the project folder, open a terminal in:

```text
/home/sunlu/Projects/semantic-web-processor
```

### Install Python Dependencies

This project uses `uv` to create and manage the Python environment. Run this
once after cloning the project, and again whenever `pyproject.toml` or
`uv.lock` changes:

```bash
uv sync --dev
```

The `--dev` option installs the normal application packages plus developer
tools such as `pytest`.

### Create `.env`

Create a file named `.env` in the project root.

Minimum example:

```text
OPENAI_API_KEY=your_api_key_here
```

Recommended local example:

```text
OPENAI_API_KEY=your_api_key_here
SEMANTIC_WEB_MODE=test
FUSEKI_HOME=/opt/apache-jena-fuseki-6.1.0
FUSEKI_BASE_URL=http://localhost:3030
FUSEKI_DATASET=semantic-web-processor
FUSEKI_DATA_DIR=db/fuseki-data
VIEWER_HOST=127.0.0.1
VIEWER_PORT=8000
```

Do not commit `.env`. It contains secrets.

## 5. Frameworks And Main Packages

This project is a Python application built from three agentic AI workflows plus
a browser viewer. The same environment is managed by `uv`.

### Whole Project

| Package | Used For |
| --- | --- |
| `uv` | Creates the Python environment, installs packages, and runs commands inside the project environment. |
| `python-dotenv` | Loads `.env` settings such as `OPENAI_API_KEY`, Fuseki URLs, model names, and mode settings. |
| `pytest` | Runs the automated test suite. |

### Designer

The designer combines an agent workflow with strict RDF validation.

| Package or tool | Used For |
| --- | --- |
| `openai-agents` | Provides the OpenAI Agents SDK workflow shell and workflow tools. |
| `openai` | Makes controlled model calls for ontology design and JSON repair. |
| `rdflib` | Parses and validates generated Turtle, counts triples, and handles RDF/RDFS graphs. |
| `requests` | Talks to Fuseki HTTP endpoints for graph loading and status checks. |
| Apache Jena Fuseki | Stores the generated ontology as a named graph. |
| `pymupdf` | Extracts text from PDF source files before design/retrieval. |

### Importer

The importer uses the same agent framework, but its job is instance generation
without ontology mutation.

| Package or tool | Used For |
| --- | --- |
| `openai-agents` | Provides the importer workflow shell and tool structure. |
| `openai` | Plans import slices and constrained CSV mapping JSON. |
| `rdflib` | Validates instance Turtle, checks ontology-term usage, merges graphs, and serializes Turtle. |
| `requests` | Queries and updates Fuseki through HTTP. |
| Apache Jena Fuseki | Supplies ontology terms and stores imported instance data. |
| Python CSV handling | Reads CSV files and deterministically emits RDF rows after mapping validation. |
| `pandas` | Installed for tabular-data work and future CSV/dataframe utilities. |

### Viewer

The viewer is a web app backed by Fuseki queries.

| Package or tool | Used For |
| --- | --- |
| `fastapi` | Provides the browser UI and API endpoints. |
| `uvicorn` | Runs the FastAPI web server. |
| `pydantic` | Validates API request and response objects. |
| `openai-agents` | Provides the viewer workflow shell and query tools. |
| `openai` | Generates final natural-language answers from queried facts. |
| `rdflib` | Parses and validates RDF/Turtle in tests and fallback paths. |
| `requests` | Sends SPARQL and graph-store requests to Fuseki. |
| Apache Jena Fuseki | Runtime data source for chatbot answers and Turtle export. |

## 6. First Run

The current repository already contains example input:

```text
design-requirements.md
data/semantic web.md
data/ontology.md
data/commonly seen triplestores.csv
```

Run the full pipeline in this order.

All commands below use `uv run`. That means `uv` runs the command inside the
project's managed Python environment, so you do not need to manually activate a
virtual environment.

### Step 1: Run The Designer

```bash
uv run python -m src.designer.main
```

Expected outputs:

```text
design.md
db/ontology.ttl
```

The designer also loads the ontology into Fuseki graph:

```text
http://example.org/semantic-web/graph/ontology
```

### Step 2: Run The Importer

```bash
uv run python -m src.importer.main
```

Expected outputs:

```text
import.md
db/instances.ttl
db/semantic_web.ttl
```

The importer also loads instance data into Fuseki graph:

```text
http://example.org/semantic-web/graph/data
```

### Step 3: Run The Viewer

```bash
uv run python -m src.viewer.main
```

Open this URL in a browser:

```text
http://127.0.0.1:8000
```

Try questions such as:

```text
How many triplestores are listed?
Which listed triplestores are open source?
What APIs or protocols are mentioned for Apache Jena TDB?
What is the difference between semantic web and ontology?
```

The viewer can also export the semantic web as Turtle.

## 7. Use Your Own Data

To use a new dataset:

1. Edit `design-requirements.md`.
2. Replace the top-level files in `data/`.
3. Remove generated artifacts from the previous run.
4. Run designer.
5. Run importer.
6. Run viewer.

Clean generated artifacts:

```bash
rm -f design.md import.md db/ontology.ttl db/instances.ttl db/semantic_web.ttl db/export.ttl
```

Do not delete `db/fuseki-run/` or `db/fuseki-data/` while Fuseki is running.

Supported source file types under `data/`:

- `.md`
- `.txt`
- `.pdf`
- `.csv`

Current product data loading reads top-level files under `data/`; it does not
recursively load nested folders.

### Writing `design-requirements.md`

Use plain language. Describe what semantic web you want and what the data
means.

Example:

```text
The data contains policy documents, technical notes, and a CSV of systems.
Design a semantic web that captures the main concepts, organizations,
standards, systems, features, relationships, and evidence from the files.
```

You do not need to write RDF or SPARQL in the requirement file.

## 8. Test Mode And Production Mode

The default mode is `test`.

```text
SEMANTIC_WEB_MODE=test
```

Test mode is cheaper and faster. It uses a compact designer prompt, smaller
retrieval budgets, and `gpt-5-mini` by default.

Production mode is for richer runs:

```text
SEMANTIC_WEB_MODE=production
```

Production mode uses more comprehensive prompts, larger retrieval and importer
budgets, longer timeouts, a relaxed ontology triple limit, and `gpt-5.5` by
default.

You can override the model in either mode:

```text
LLM_MODEL=gpt-5.5
```

Important settings:

| Setting | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | API key for OpenAI calls. |
| `SEMANTIC_WEB_MODE` | `test` or `production`. |
| `LLM_MODEL` | Override the default model. |
| `LLM_TIMEOUT_SECONDS` | Timeout for LLM calls. |
| `DESIGNER_ITERATIONS` | Designer validation/retry attempts. |
| `IMPORTER_ITERATIONS` | Importer validation/retry attempts. |
| `SEMANTIC_SEARCH_ENABLED` | Enable retrieval for large inputs. |
| `SEMANTIC_SEARCH_PROVIDER` | `local` or `openai`. |
| `EMBEDDING_MODEL` | OpenAI embedding model when provider is `openai`. |
| `SEMANTIC_CONTEXT_MAX_CHARS` | Max prompt context before retrieval is used. |
| `DESIGNER_RETRIEVAL_FOCUSES` | Number of model-planned designer retrieval focuses. |
| `IMPORTER_RETRIEVAL_BATCHES` | Number of model-planned importer batches. |
| `FUSEKI_HOME` | Fuseki installation directory. |
| `FUSEKI_BASE_URL` | Fuseki server URL. |
| `FUSEKI_DATASET` | Fuseki dataset path name. |
| `FUSEKI_DATA_DIR` | Persistent Fuseki TDB2 storage directory. |
| `ONTOLOGY_GRAPH_URI` | Named graph for ontology triples. |
| `DATA_GRAPH_URI` | Named graph for imported instance triples. |
| `VIEWER_HOST` | Viewer web server host. |
| `VIEWER_PORT` | Viewer web server port. |

## 9. How Data Moves Through The System

Fuseki is the main machine-readable handoff between applications.

```text
design-requirements.md + data/*
        |
        v
Designer
        |
        +--> design.md
        +--> db/ontology.ttl
        +--> Fuseki ontology graph
                 |
                 v
Importer
        |
        +--> import.md
        +--> db/instances.ttl
        +--> db/semantic_web.ttl
        +--> Fuseki data graph
                 |
                 v
Viewer
        |
        +--> chatbot answers
        +--> Turtle export
```

Artifact roles:

| Artifact | Role |
| --- | --- |
| `design.md` | Human-readable ontology design, importer reference, and viewer reference for interpreting schema labels. |
| `import.md` | Importer progress log. |
| `db/ontology.ttl` | Validated ontology Turtle, review file, portable fallback, and reload artifact. |
| `db/instances.ttl` | Validated instance Turtle. |
| `db/semantic_web.ttl` | Combined ontology and instance graph for review and fallback. |
| Fuseki ontology graph | Runtime ontology source of truth. |
| Fuseki data graph | Runtime instance data source of truth. |
| `chat/viewer/` | Runtime viewer chat transcripts. |

The viewer queries and exports through Fuseki. It does not use
`db/semantic_web.ttl` as its runtime data source. It may read `design.md` as
reference context when mapping ordinary user wording to ontology labels, but
answers must still be grounded in facts queried from Fuseki.

## 10. CSV Handling

CSV files are treated as structured data.

The designer receives a CSV profile, not the entire table as raw prompt text.
The profile includes column names, row count, inferred datatypes, compatible
datatypes, null counts, examples, and warnings for risky columns such as
numeric-looking identifiers or leading-zero values.

The importer uses the model to plan a constrained mapping, then Python converts
the rows:

1. Profile CSV files.
2. Ask the model for mapping JSON.
3. Validate the mapping against the ontology and CSV headers.
4. Validate datatype choices and safe widening.
5. Iterate over every CSV row in Python.
6. Emit RDF triples.
7. Merge CSV triples with unstructured-source triples.

This makes CSV import repeatable and testable.

## 11. Large Documents And Semantic Search

The project supports retrieval-backed runs when source data or graph context is
too large for one prompt.

The shared semantic-search layer can chunk:

- Markdown.
- Plain text.
- PDF text.
- CSV profiles and rows.
- RDF graph content.
- SPARQL result rows.

By default, retrieval uses deterministic local vector search. For larger real
datasets, set:

```text
SEMANTIC_SEARCH_PROVIDER=openai
```

The current long-document behavior is useful but still a proof of concept for
exhaustive coverage. Future scale-up work should add coverage ledgers, better
PDF section extraction, ontology refinement passes, importer continuation
passes, and coverage reports.

## 12. Viewer API

The viewer starts a FastAPI app.

When a user asks with ordinary wording that does not match ontology labels, the
viewer first queries schema labels and comments from Fuseki, then uses the
generated `design.md` as reference context for semantic class matching. If one
likely class is found, it queries that class. If several labels are plausible,
it asks the user to clarify or choose among likely labels instead of silently
guessing.

Useful endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Browser chatbot page. |
| `GET /api/status` | Fuseki availability and triple count. |
| `POST /api/chat/session` | Create a chat session. |
| `GET /api/chat/{session_id}` | Read a chat session. |
| `POST /api/question` | Ask a question. |
| `GET /api/export.ttl` | Export Turtle from Fuseki. |

Example API request:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/session
```

Then use the returned `session_id`:

```bash
curl -X POST http://127.0.0.1:8000/api/question \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"SESSION_ID_HERE","question":"How many triplestores are listed?"}'
```

## 13. Run Tests

Run the test suite:

```bash
uv run pytest
```

Some Fuseki smoke tests may be skipped when Fuseki is not available. That is
expected for offline or lightweight test runs.

## 14. Troubleshooting

### Missing OpenAI API Key

Symptom: the designer or importer fails before model generation.

Fix: create `.env` and set:

```text
OPENAI_API_KEY=your_api_key_here
```

### Unknown Model

Symptom: OpenAI rejects the configured model.

Fix: remove `LLM_MODEL` from `.env` to use the default for the selected mode, or
set it to a model your account can use.

### Fuseki Port Already Bound

Symptom: Fuseki cannot start because port `3030` is already in use.

Check for running Fuseki processes:

```bash
pgrep -af fuseki
```

If it is a stale process, stop it:

```bash
kill -TERM <PID>
```

### Fuseki Base Is Not Writable

Symptom: Fuseki exits with an error about runtime files or permissions.

Fix: use the project-local runtime base. The workflow sets this automatically,
but manual runs should set:

```text
FUSEKI_BASE=db/fuseki-run
```

### Graph Load Falls Back To File Mode

Symptom: output files are written but Fuseki does not contain the graph.

Fix:

1. Confirm Fuseki is running at `http://localhost:3030`.
2. Confirm `.env` uses the expected `FUSEKI_DATASET`.
3. Confirm the server was started with `--update`.
4. Check `db/fuseki.log`.

### Viewer Starts But Answers Are Empty

Symptom: the browser loads, but questions return missing or weak facts.

Fix:

1. Run the designer.
2. Run the importer.
3. Confirm `/api/status` reports triples.
4. Ask a question that matches the current dataset.

### Invalid CSV Mapping

Symptom: importer retries or fails during CSV mapping validation.

Fix:

1. Check `import.md` for validation feedback.
2. Confirm the CSV headers are clear.
3. Confirm `design-requirements.md` explains what the table represents.
4. Rerun the designer if the ontology lacks terms needed for the table.

### Bad Turtle Or Export Parse Failure

Symptom: RDF parsing fails for generated or exported Turtle.

Fix:

1. Rerun the failed workflow.
2. Check `design.md` or `import.md` for validation feedback.
3. Confirm Fuseki is reachable and the correct dataset is configured.
4. Run `uv run pytest` after regeneration.

## 15. Current Example Result

The current repository example uses:

```text
data/semantic web.md
data/ontology.md
data/commonly seen triplestores.csv
```

The latest documented production validation used `SEMANTIC_WEB_MODE=production`
with `gpt-5.5`. It produced:

- 541 ontology triples.
- 94 RDFS classes.
- 30 RDF properties.
- 480 instance triples.
- 1,021 combined Fuseki/export triples.
- 77 deterministic CSV triples from one validated CSV mapping.
- Viewer answers grounded in Fuseki data.
- Turtle export that parsed successfully.
- Test result: `87 passed, 2 skipped`.

This validates the architecture outside the original DnD example. It is still a
proof of concept for comprehensive unstructured-document coverage; CSV rows are
fully converted after mapping, but markdown and PDF extraction remain bounded
by configured retrieval and validation budgets.
