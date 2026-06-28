# Vibe Semanting Progress

This file is the working plan and handoff log. It has two jobs:

- Give the coding agent a clear step-by-step plan so implementation and tests
  happen in small, verifiable increments.
- Preserve enough handoff context for the next coding agent to continue without
  rereading the whole project history.

A checkbox is marked only after the related work has been tested.

## Ground Rules

- Product code must stay domain-neutral.
- Product code must not hardcode the current example dataset, old DnD examples,
  or other source-specific classes, properties, graph URIs, prompts, SPARQL
  queries, importer behavior, or viewer behavior.
- Manual work may revise prompts, validators, retries, tests, and framework
  code.
- Manual work must not hand-author the final ontology or final instance graph.
- RDF/RDFS is the primary target. OWL is optional and should stay simple.
- Apache Jena Fuseki is the intended runtime implementation target.
- Turtle files are validated intermediate artifacts for testing, review,
  portability, export, and fallback.
- Each small task must have a focused test before it is checked off.
- Milestone documentation updates go into `README.md`.
- Milestone changes are committed with `git add` and `git commit`.
- Documents must not contain emoji.

## Finished Tasks

The following work is complete, tested, documented, and committed.

- Project foundation:
  configuration, file loading, RDF utilities, Fuseki utilities, LLM utilities,
  dependencies, and baseline tests.
- Semantic web designer:
  OpenAI Agents SDK workflow shell, direct OpenAI design calls, compact and
  production prompts, RDF/RDFS validation, JSON repair fallback, progressive
  `design.md` logging, ontology Turtle output, and Fuseki ontology loading.
- Semantic web importer:
  OpenAI Agents SDK workflow shell, ontology inspection from Fuseki with
  `db/ontology.ttl` fallback, no-schema-mutation validation, progressive
  `import.md` logging, instance Turtle output, combined graph output, and
  Fuseki data loading.
- Semantic web viewer:
  FastAPI browser chatbot, chat sessions, Fuseki-backed status, question
  answering, exact subject lookup, class counts, LLM-assisted semantic class
  matching, `design.md` reference context for schema-label interpretation,
  ambiguity clarification, relevant fact retrieval, Turtle export, and
  interactive graph rendering through the standalone semantic-web plot tool.
- Semantic search and graph slicing:
  shared retrieval layer for markdown, text, PDF, CSV, RDF graph chunks, and
  SPARQL result rows; deterministic local search; optional OpenAI embeddings;
  Fuseki-backed term selection and targeted graph slices.
- Iterative retrieval-guided designer:
  model-planned retrieval focuses, per-focus schema notes, and large-data
  prompt-context selection.
- Iterative retrieval-guided importer:
  model-planned import batches, per-slice validation, graph merging, and stop
  summaries.
- CSV-aware design and deterministic import:
  CSV profiling, conservative datatype notes, constrained mapping JSON,
  mapping validation, safe datatype compatibility, and deterministic row-to-RDF
  generation.
- Test and production modes:
  `SEMANTIC_WEB_MODE=production` as the richer default with `gpt-5.4`, and
  `SEMANTIC_WEB_MODE=test` as the compact mode with `gpt-5.4-mini`.
- Domain-neutral validations:
  non-DnD PDF validation, CSV-aware validation, mode comparison, current
  dataset production validation, viewer workflow/API checks, and Turtle export
  parsing.
- Documentation:
  `AGENTS.md` rewritten as a requirements/handoff document; `README.md`
  rewritten for end users with Fuseki setup, `uv` usage, package/framework
  overview, first run, custom data, modes, artifacts, CSV handling, semantic
  search, viewer API, tests, and troubleshooting.

Latest completed validation:

- Current active dataset:
  `data/semantic web.md`, `data/ontology.md`, and
  `data/commonly seen triplestores.csv`.
- Latest production run:
  `SEMANTIC_WEB_MODE=production`, `gpt-5.4`, 444 ontology triples, 62 RDFS
  classes, 38 RDF properties, 0 class/property terms missing required labels or
  comments, 500 instance triples, and 944 combined/export triples. The run
  included 201 deterministic CSV triples from one validated CSV mapping.
- Latest viewer validation:
  `/api/status` reported 944 triples; the viewer answered three
  schema-interpretation questions about reasoning-oriented systems,
  API/query-interface interoperability, and open-source learning tradeoffs;
  exported Turtle parsed successfully with 944 triples; and `/api/plot.html`
  returned graph HTML.
- Latest local test result:
  `uv run pytest` reported 101 passed and 4 skipped after ontology annotation
  validation, importer annotation summaries, CSV suggestion annotations, and
  viewer schema-context updates.
- Recent documentation commits:
  `3dff973 Improve project setup documentation`,
  `a4ef360 Document uv commands and framework packages`,
  `fd9ec0f Clean progress handoff notes`.

## Milestone 1: Viewer Graph Plot Integration

Goal: integrate the standalone semantic-web plot tool into the viewer while
keeping the tool reusable from `./tools/semantic-web-plot`.

- [x] Refactor `tools/semantic-web-plot` so the existing renderer is available
  through an importable `SemanticWebPlotter` class while preserving the
  standalone CLI.
- [x] Add `pyvis` to the main project dependencies so the viewer can render
  graph HTML at runtime.
- [x] Add a Fuseki-backed viewer plot endpoint, `GET /api/plot.html`, and a
  browser UI control that opens the graph.
- [x] Start Fuseki automatically on viewer startup when it is not already
  reachable, and stop it on shutdown only when the viewer started it.
- [x] Add focused tests for the viewer plot service and FastAPI endpoint.
- [x] Run `uv run pytest`.
- [x] Update `AGENTS.md`, `README.md`, `PROGRESS.md`, and the plot tool README.
- [x] Commit the viewer graph plot integration.

## Milestone 2: Clean End-To-End Regeneration

Goal: delete generated design/import/RDF artifacts and Fuseki runtime data,
then regenerate the semantic web from the current dataset using the renamed
Vibe Semanting defaults.

- [x] Stop the running viewer and viewer-started Fuseki process.
- [x] Remove generated `design.md`, `import.md`, `db/*.ttl`,
  `db/semantic_web_plot.html`, and Fuseki runtime/storage directories.
- [x] Run the designer from scratch in production mode.
- [x] Fix importer CSV behavior by adding concrete replacement suggestions for
  failed model-planned mappings and partial deterministic repair for any
  mappings that remain invalid after retries.
- [x] Run the importer from scratch in production mode.
- [x] Start the viewer and validate `/api/status`, `/api/export.ttl`,
  `/api/plot.html`, and a live chatbot count question.
- [x] Parse the exported Turtle successfully.
- [x] Run `uv run pytest`.
- [x] Commit the clean end-to-end regeneration milestone.

## Milestone 3: Ontology Labels And Comments

Goal: improve importer and viewer schema interpretation by requiring generated
ontology classes and properties to carry human-readable annotation metadata.
RDFS supports `rdfs:label` and `rdfs:comment`, and OWL ontologies commonly use
those annotation properties as well. This milestone should make annotation
metadata a validation contract, not only a prompt preference.

Implementation plan:

- [x] Add focused designer validation tests for ontology annotations:
  reject a generated `rdfs:Class` without `rdfs:label`, reject one without
  `rdfs:comment`, reject an `rdf:Property` without `rdfs:label`, reject one
  without `rdfs:comment`, and accept terms with non-empty useful annotations.
- [x] Implement the ontology annotation validator in the designer validation
  path so every generated `rdfs:Class` and `rdf:Property` must have at least
  one non-empty `rdfs:label` and one non-empty `rdfs:comment`.
- [x] Wire annotation validation into designer retry feedback so the model gets
  concrete messages naming exactly which class or property is missing a label
  or comment.
- [x] Tighten both test and production designer prompts so labels and comments
  are required for every class and property, not just important terms.
- [x] Add importer tests for ontology term inspection that assert class and
  property summaries expose URI, label, comment, domain, and range when present.
- [x] Update importer ontology inspection and CSV mapping prompts so model
  planning sees labels and comments alongside raw URIs, preserving domain-neutral
  behavior and existing fallback behavior when comments are absent.
- [x] Add importer CSV mapping feedback tests showing invalid model-planned
  properties receive replacement suggestions that include existing labels and
  comments, not only URI strings.
- [x] Add viewer schema-context tests that confirm Fuseki-backed labels and
  comments are included in schema summaries before `design.md` is used as
  supplemental reference.
- [x] Update viewer schema/query context generation if needed so labels and
  comments are consistently available for exact lookup, semantic class matching,
  ambiguity clarification, and relevant fact retrieval.
- [x] Run targeted tests after each implementation slice, then run
  `uv run pytest`.
- [x] Regenerate the current dataset in production mode with the updated
  designer and importer, then validate `db/ontology.ttl`,
  `db/instances.ttl`, `db/semantic_web.ttl`, viewer `/api/status`,
  `/api/export.ttl`, `/api/plot.html`, and at least three viewer questions that
  depend on schema-label interpretation.
- [x] Update `README.md` with the annotation contract and validation behavior.
- [x] Update `README.md` with the latest post-change regeneration result.
- [x] Update this `PROGRESS.md` milestone with completed validation numbers.
- [x] Commit the ontology labels/comments milestone.

## Milestone 4: Long-Document Coverage Completion

Goal: move beyond proof-of-concept semantic webs for long unstructured source
documents by improving coverage tracking, source structure extraction, and
refinement loops while keeping Fuseki as the runtime source of truth.

The baseline scale-up mechanism is already complete through production mode,
larger budgets, comprehensive prompts, retrieval-guided designer/importer
flows, Fuseki-backed graph slicing, and JSON repair. This milestone tracks the
remaining work needed for richer long-document coverage.

- [ ] Add a coverage ledger for designer/importer runs that records source
  chapters, sections, page ranges, formulas, tables, code examples, tools,
  named concepts, and imported graph areas.
- [ ] Add tests for the coverage ledger, including append/update behavior and
  summaries of covered versus uncovered source areas.
- [ ] Improve PDF preprocessing into section-aware chunks using extracted
  headings, table-of-contents structure, page numbers, formulas, tables, figure
  captions, and code blocks where available.
- [ ] Add tests for section-aware PDF/text chunking using small fixtures.
- [ ] Add ontology refinement passes that review uncovered evidence and propose
  schema additions only when the existing ontology cannot represent important
  content.
- [ ] Add tests for ontology refinement control flow with stubbed model
  responses and validation feedback.
- [ ] Add importer continuation passes that resume from existing Fuseki data,
  avoid duplicates, and import uncovered sections until coverage is complete or
  a configured budget is reached.
- [ ] Add tests for importer continuation, duplicate avoidance, and merge
  validation.
- [ ] Add viewer or script-based coverage reports that summarize what the graph
  covers and what source areas remain missing.
- [ ] Add tests for coverage report generation.
- [ ] Validate long-document coverage improvements on a representative PDF
  dataset, such as a restored `data/main.pdf` or a new representative PDF, and
  compare graph coverage against the earlier proof-of-concept result.
- [ ] Run `uv run pytest`.
- [ ] Update `README.md` and `PROGRESS.md` with the long-document coverage
  validation result.
- [ ] Commit the long-document coverage milestone.

## Handoff For Next Coding Agent

Start by reading `AGENTS.md`, `README.md`, and this file.

Current generated outputs:

- `design.md`
- `import.md`
- `db/ontology.ttl`
- `db/instances.ttl`
- `db/semantic_web.ttl`
- Fuseki ontology graph:
  `http://example.org/semantic-web/graph/ontology`
- Fuseki data graph:
  `http://example.org/semantic-web/graph/data`, unless overridden by `.env`

Runtime notes:

- Python dependencies are managed with `uv`.
- Run tests with `uv run pytest`.
- Fuseki may already be running on port `3030`.
- If Fuseki is not running, workflows use project-local runtime/storage:
  `db/fuseki-run`, `db/fuseki-data`, and `db/fuseki.log`.
- Do not use `/opt/apache-jena-fuseki-6.1.0/run` as this project's Fuseki base.
- Fuseki readiness should use SPARQL `ASK` through `POST`, not `GET` on the
  query endpoint.

Behavior to preserve:

- Designer, importer, and viewer are independent executables.
- Fuseki is the runtime source of truth between applications.
- `design.md` remains a human-readable design and importer reference.
- Turtle files remain validation, review, export, portability, and fallback
  artifacts.
- Viewer uses Fuseki at runtime and does not read `db/semantic_web.ttl`
  directly.
- Viewer may read `design.md` as reference context for mapping ordinary user
  wording to ontology labels, but must still ground answers in Fuseki facts.
- Viewer starts Fuseki when needed and possible, but stops it only when the
  viewer started that Fuseki process.
- Viewer graph rendering uses Fuseki-exported Turtle and the reusable renderer
  under `tools/semantic-web-plot`.
- `SEMANTIC_WEB_MODE=production` is the default workflow and uses `gpt-5.4`.
  Test mode is the compact workflow and uses `gpt-5.4-mini`.

Open item:

- Long unstructured markdown/PDF coverage is still proof-of-concept level.
  Milestone 4 should improve coverage tracking, PDF chunking, schema
  refinement, importer continuation, and coverage reporting.
