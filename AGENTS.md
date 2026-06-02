# Semantic Web Processor

This file is the high-level requirements and handoff document for a coding
agent. It describes the system that should be built, the required features, the
expected setup, and the main technology choices. Detailed implementation
history belongs in `PROGRESS.md`; user-facing setup and operation details
belong in `README.md`.

## Product Goal

Build a Python application that can design, import, query, and export a
semantic web from local user-provided data.

The application should support both structured and unstructured input files
placed directly under `./data/*`:

- Markdown files.
- Plain text files.
- PDF files.
- CSV files.

The system should produce an RDF/RDFS semantic web, store it in Apache Jena
Fuseki, and provide a browser-based chatbot viewer that answers user questions
by querying the stored semantic web.

## Domain Boundary

The product must be domain-neutral.

- Do not hardcode DnD-specific classes, properties, namespaces, validation
  rules, prompts, graph URIs, SPARQL queries, importer behavior, or viewer
  behavior in `./src/*`.
- Do not hardcode assumptions from the current semantic-web, ontology, or
  triplestore example into product modules.
- Product code in `./src/*` should derive ontology terms and instance mappings
  from `./design-requirements.md`, `./data/*`, generated `./design.md`,
  generated ontology files, Fuseki contents, and runtime configuration.
- Domain-specific examples may appear in documentation, generated artifacts, or
  tests, but reusable product code must remain general-purpose.
- If example-specific checks are needed, put them in `./tests/*` or scripts,
  not in reusable product modules.

## Main Executables

The project should contain three independent executable applications.

### Semantic Web Designer

Location: `./src/designer/*`

The designer reads `./design-requirements.md` and `./data/*`, designs a compact
RDF/RDFS ontology, validates it, writes human-readable documentation, and loads
the ontology into Fuseki.

Required behavior:

- Use the OpenAI Agents SDK as the workflow framework.
- Do not use CrewAI for the designer.
- The actual ontology generation step may use direct OpenAI API calls, but it
  must be controlled by the designer workflow.
- Check whether Apache Jena Fuseki is available.
- Start Fuseki when needed and possible.
- Read the design requirements and top-level source files under `./data/*`.
- Use semantic-search retrieval instead of prompt-stuffing when the source data
  is large.
- Generate a compact first-pass RDF/RDFS ontology.
- Validate generated Turtle with RDF parsing and project-specific checks.
- Retry with validation feedback when the ontology is invalid.
- Write `./design.md` progressively while the run is active.
- Leave the final design at the top of `./design.md` and append a generation
  log for human review and importer reference.
- Write `./db/ontology.ttl` as a validated intermediate artifact for review,
  portability, tests, fallback, and Fuseki loading.
- Load the ontology into Fuseki as a named graph.

The designer should focus mainly on RDF and RDFS. OWL may be used if helpful,
but complex OWL reasoning is not required.

### Semantic Web Importer

Location: `./src/importer/*`

The importer reads the generated design, the ontology, and source data, then
inserts instance data into the semantic web without changing the ontology.

Required behavior:

- Use the OpenAI Agents SDK as the workflow framework.
- Understand the semantic web design by querying Fuseki when available and by
  reading `./design.md` as human-readable reference.
- Use `./db/ontology.ttl` as a portable fallback and reload artifact.
- Read top-level source files from `./data/*`.
- Do not change the ontology produced by the designer.
- Validate that importer output does not define new `rdfs:Class` or
  `rdf:Property` terms outside the generated ontology.
- Write `./import.md` progressively during long runs.
- Write `./db/instances.ttl` as a validated intermediate artifact.
- Write `./db/semantic_web.ttl` as a combined review/export/fallback artifact.
- Load the instance graph into Fuseki as a named graph.

CSV import should be deterministic after mapping:

- Profile CSV files instead of sending every row to the model.
- Ask the model for a constrained row-to-RDF mapping JSON.
- Validate the mapping against CSV headers and existing ontology terms.
- Apply safe datatype compatibility rules.
- Use Python to iterate over all rows and emit RDF instances.
- Merge deterministic CSV triples with LLM-assisted imports from unstructured
  markdown, text, and PDF sources.

For large unstructured sources, the importer should use retrieval-guided import
batches, validate each slice, merge valid triples, and continue until coverage
is complete or the configured budget is reached.

### Semantic Web Viewer

Location: `./src/viewer/*`

The viewer provides a FastAPI browser UI with chatbot and export controls.

Required behavior:

- Use Fuseki as the runtime data source.
- Do not read `./db/semantic_web.ttl` directly at viewer runtime.
- Query Fuseki to answer user questions.
- Use exact entity lookup, class-instance counts, semantic class matching, and
  relevant fact retrieval before final answer generation.
- Keep answers end-user-facing. Avoid database, RDF, URI, predicate, graph, or
  raw query wording unless the user asks implementation-level questions.
- Provide an export endpoint or UI control for Turtle export.
- Use Fuseki's graph/query capability for export rather than serializing a
  local file as the runtime source.
- Persist browser chat sessions under `./chat/viewer/` as runtime artifacts.

Expected endpoints:

- `GET /`: browser chatbot page.
- `GET /api/status`: Fuseki status and graph triple count.
- `POST /api/chat/session`: create a viewer chat session.
- `GET /api/chat/{session_id}`: read a persisted chat session.
- `POST /api/question`: answer a question for a session.
- `GET /api/export.ttl`: export the semantic web as Turtle.

## Data And Handoff Model

Fuseki is the primary machine-readable source of truth between the designer,
importer, and viewer.

Expected data flow:

1. User provides `./design-requirements.md` and source files under `./data/*`.
2. Designer creates `./design.md` and `./db/ontology.ttl`.
3. Designer loads the ontology into Fuseki named graph
   `http://example.org/semantic-web/graph/ontology`, unless overridden.
4. Importer reads `./design.md`, inspects ontology terms from Fuseki when
   available, and falls back to `./db/ontology.ttl` when needed.
5. Importer creates `./db/instances.ttl` and `./db/semantic_web.ttl`.
6. Importer loads instances into Fuseki named graph
   `http://example.org/semantic-web/graph/data`, unless overridden.
7. Viewer queries and exports through Fuseki.

Artifact roles:

- `./design.md`: human-readable design and importer reference.
- `./import.md`: progressive importer run log.
- `./db/ontology.ttl`: portable ontology artifact, validation artifact, and
  Fuseki reload fallback.
- `./db/instances.ttl`: portable instance artifact and validation artifact.
- `./db/semantic_web.ttl`: combined review/export/fallback artifact.
- Fuseki named graphs: intended runtime source of truth.

Designer and importer workflows should stop Fuseki only when that workflow
started Fuseki itself. If Fuseki was already running before the workflow, leave
it running.

For large graphs, agents should consume relevant graph slices from Fuseki or
local RDF/SPARQL fallback instead of prompt-stuffing whole Turtle files.

## Setup Assumptions

The project is developed in Python.

Expected local prerequisites:

- `git`.
- `uv`.
- Python 3.12 or newer.
- Java suitable for Apache Jena Fuseki.
- Apache Jena Fuseki.
- OpenAI API key.

Apache Jena Fuseki is expected at:

```text
/opt/apache-jena-fuseki-6.1.0
```

Use project-local Fuseki runtime and storage directories:

```text
db/fuseki-run
db/fuseki-data
db/fuseki.log
```

Do not use `/opt/apache-jena-fuseki-6.1.0/run` as the project runtime base,
because it may not be writable.

The project reads configuration from `.env`. Important settings include:

- `OPENAI_API_KEY`.
- `SEMANTIC_WEB_MODE`.
- `LLM_MODEL`.
- `FUSEKI_BASE_URL`.
- `FUSEKI_DATASET`.
- `FUSEKI_HOME`.
- `FUSEKI_DATA_DIR`.
- `ONTOLOGY_GRAPH_URI`.
- `DATA_GRAPH_URI`.
- `VIEWER_HOST`.
- `VIEWER_PORT`.
- Semantic-search and retrieval budget settings.

Default mode should be `SEMANTIC_WEB_MODE=test`, using a compact workflow and a
smaller default model. `SEMANTIC_WEB_MODE=production` should use richer prompts,
larger retrieval/import budgets, longer timeouts, and a stronger default model.
Explicit environment overrides should work in both modes.

## Semantic Search And Scaling Requirements

The system must support data that is too large to fit safely into one prompt.

Required behavior:

- Use shared semantic-search utilities for markdown, text, PDF, CSV, RDF graph
  chunks, and SPARQL result rows.
- Use deterministic local vector search for tests and optional OpenAI
  embeddings for larger product runs.
- Represent CSV files to the designer as conservative profiles.
- Use model-planned retrieval focuses for large designer runs.
- Use model-planned retrieval batches for large importer runs.
- Use Fuseki-backed term selection and targeted graph slices for importer and
  viewer context when Fuseki is available.
- Keep local RDF/SPARQL retrieval as a portable fallback.

Future scale-up work should improve long-document coverage with:

- Coverage ledgers for source sections, page ranges, formulas, tables, code
  examples, tools, named concepts, and imported graph areas.
- Better PDF preprocessing for headings, table-of-contents structure, page
  numbers, equations, tables, captions, and code blocks.
- Ontology refinement passes based on uncovered evidence.
- Importer continuation passes that resume from existing Fuseki data and avoid
  duplicate instances.
- Viewer or script-based coverage reports.

## Brief Usage

Install dependencies:

```bash
uv sync --dev
```

Run tests:

```bash
uv run pytest
```

Run the designer:

```bash
uv run python -m src.designer.main
```

Run the importer:

```bash
uv run python -m src.importer.main
```

Run the viewer:

```bash
uv run python -m src.viewer.main
```

The viewer should start a browser-accessible FastAPI application, defaulting to
`http://127.0.0.1:8000` unless configured otherwise. A user can open that URL
in a browser.

To use a new dataset:

1. Replace `./design-requirements.md`.
2. Replace top-level files under `./data/*`.
3. Remove generated review/fallback artifacts from the previous run.
4. Run designer.
5. Run importer.
6. Run viewer.
7. Export and validate Turtle when needed.

Do not delete Fuseki runtime directories while Fuseki is running.

## Development Requirements

- Plan then implement. Save the active plan in `./PROGRESS.md`.
- Carry out steps one by one according to the plan.
- After finishing each step, test it before checking the box in
  `./PROGRESS.md`.
- Update `README.md` with detailed setup, usage, implementation, and milestone
  explanations.
- Commit completed milestones with `git add` and `git commit`.
- Do not use emoji in any project document.
- Intermediate files and testing scripts may be saved under `./tests/*`.
