# Semantic Web Processor Progress

This file is the working plan and progress log. A checkbox is marked only after
the related implementation has been tested.

## Ground Rules

- The product code must perform semantic web design and instance insertion.
- Manual work may revise prompts, validators, retries, tests, and framework code.
- Manual work must not hand-author the final ontology or final instance graph.
- RDF/RDFS is the primary target. OWL is optional and should stay simple.
- Turtle files are allowed as validated intermediate artifacts for testing,
  review, and fallback. The intended implementation target is Apache Jena
  Fuseki, loaded through Jena-compatible graph operations.
- Each small task must have a focused test before it is checked off.
- Milestone documentation updates go into `README.md`.
- Milestone changes are committed with `git add` and `git commit`.
- Documents must not contain emoji.

## Milestone 0: Project Foundation

- [x] Inspect the current repository structure, project instructions, sample data, and semantic-search tool.
- [x] Create a detailed implementation plan in `PROGRESS.md`.
- [x] Add baseline Python dependencies for RDF, SPARQL, OpenAI, HTTP access, tests, and the browser UI.
- [x] Add shared configuration utilities.
- [x] Add shared project data loading utilities for markdown, text, and CSV files.
- [x] Add shared RDF parsing, serialization, graph combination, and local SPARQL utilities.
- [x] Add shared Fuseki client utilities with local file fallback.
- [x] Add shared LLM response utilities with validation-friendly text extraction.
- [x] Test foundation code with `python -m compileall src`.

## Milestone 1: Designer Framework

Goal: the semantic web designer reads `design-requirements.md` and `data/*`,
then uses an OpenAI Agents SDK workflow to produce `design.md`, validate an
intermediate `db/ontology.ttl`, and implement the ontology in Apache Jena
Fuseki when available.

### 1.1 Designer Contracts

- [x] Define the exact designer input contract: requirements text, project data summary, namespace policy, and output schema.
- [x] Define the exact designer output contract: design markdown plus Turtle ontology.
- [x] Add tests for designer output contract parsing using small fixture responses.

### 1.2 Designer Agent Execution

- [x] Implement a direct LLM designer agent path with bounded timeout and retry feedback.
- [x] Remove CrewAI from the designer path.
- [x] Implement an OpenAI Agents SDK designer workflow shell.
- [x] Add designer tools for Fuseki status, Fuseki startup, iterative design, and ontology persistence/load.
- [x] Use explicit designer workflow tool sequencing so operational steps are controllable and visible.
- [x] Add command-line logging that reports model, iterations, Fuseki dataset, output locations, and load target.
- [x] Add progressive `design.md` logging so active LLM attempts, failures, and validation status are visible while the designer is running.
- [x] Test direct agent execution with a stubbed LLM response.
- [x] Test Agents SDK workflow configuration without requiring a live API call.

### 1.3 Designer RDF Validation

- [x] Validate generated Turtle with `rdflib`.
- [x] Validate required prefixes and base namespace.
- [x] Validate generic RDF/RDFS schema shape without hardcoded domain classes.
- [x] Validate that generated properties have `rdfs:domain` and `rdfs:range` where practical.
- [x] Add tests for valid ontology output.
- [x] Add tests that malformed Turtle triggers retry feedback.

### 1.4 Designer Persistence

- [x] Write generated design documentation to `design.md`.
- [x] Write generated ontology to `db/ontology.ttl` as an intermediate artifact.
- [x] Load ontology into Fuseki when Fuseki is available using Jena graph operations.
- [x] Fall back to local Turtle files only when Fuseki is unavailable.
- [x] Add tests for local ontology persistence.
- [x] Add a Fuseki smoke test that can be skipped when Fuseki is unavailable.

### 1.5 Designer Product Run

- [x] Run `uv run python -m src.designer.main`.
- [x] Inspect the generated `design.md` for importer usability.
- [x] Inspect `db/ontology.ttl` using RDF parsing and SPARQL checks.
- [x] Revise designer code, prompts, or validators if the product output is weak or invalid.
- [x] Re-run designer after revisions until output passes checks.
- [x] Update `README.md` with designer usage and behavior.
- [x] Commit the designer milestone.

## Milestone 2: Importer Framework

Goal: the semantic web importer reads `design.md`, `db/ontology.ttl`, and
`data/*`, then uses an OpenAI Agents SDK workflow to produce and load
`db/instances.ttl` without changing the ontology.

### 2.1 Importer Contracts

- [x] Define importer input contract: design document, ontology Turtle, source data, and namespace policy.
- [x] Define importer output contract: instance Turtle only, with no schema mutation.
- [x] Add tests for importer output contract parsing using fixture responses.

### 2.2 Importer Agent Execution

- [x] Implement an OpenAI Agents SDK importer agent.
- [x] Provide agent tools for reading design text, reading source data, inspecting ontology terms, and returning Turtle.
- [x] Add bounded timeout and retry feedback.
- [x] Add command-line logging for model, source files, retries, and output locations.
- [x] Test importer tool functions without a live API call.
- [x] Test importer execution with a stubbed agent response.

### 2.3 Importer RDF Validation

- [x] Validate generated instance Turtle with `rdflib`.
- [x] Validate that instance graph imports or uses the ontology namespace.
- [x] Validate that the importer does not create new `rdfs:Class` or `rdf:Property` terms outside the generated ontology.
- [x] Validate sample source coverage in `tests/*` for named NPCs, monsters, items, scenes, loot, rewards, and XP awards.
- [x] Add tests for valid importer output.
- [x] Add tests that schema mutation triggers retry feedback.

### 2.4 Importer Persistence

- [x] Write generated instances to `db/instances.ttl`.
- [x] Combine ontology and instances into `db/semantic_web.ttl`.
- [x] Load instance graph into Fuseki when Fuseki is available.
- [x] Fall back to local Turtle files when Fuseki is unavailable.
- [x] Add tests for local instance persistence and graph combination.
- [x] Add a Fuseki smoke test that can be skipped when Fuseki is unavailable.

### 2.5 Importer Product Run

- [x] Run `uv run python -m src.importer.main`.
- [x] Inspect `db/instances.ttl` using RDF parsing and SPARQL checks.
- [x] Ask source-coverage SPARQL questions against the combined graph.
- [x] Revise importer code, prompts, tools, or validators if the product output is weak or invalid.
- [x] Re-run importer after revisions until output passes checks.
- [x] Update `README.md` with importer usage and behavior.
- [x] Commit the importer milestone.

### 2.x Future Importer Improvement

- [x] Add optional ontology inspection by querying Fuseki when available.
- [x] Keep `db/ontology.ttl` as the portable fallback and cross-machine handoff artifact.
- [x] Add tests for Fuseki ontology inspection with local Turtle fallback.
- [ ] Replace whole-graph prompting with Fuseki-backed relevant graph slices.
  Build a semantic-web embedding strategy: render ontology/data triples into
  plain-text chunks, embed those chunks with semantic-search technology, use
  vector search to identify relevant classes/properties/facts for a task, then
  query Fuseki for bounded graph slices around those terms. Keep local
  RDF/SPARQL fallback for portability and tests.
- [x] Move inter-application handoff to persistent Fuseki storage. Designer and
  importer may still generate Turtle as internal validation/loading artifacts,
  but Fuseki should become the durable source of truth that bridges designer,
  importer, and viewer. `design.md` remains reference documentation for the
  importer; Turtle should not be the primary cross-application contract.

## Milestone 3: Viewer Framework

Goal: the semantic web viewer starts a browser-based chatbot UI that answers
questions by querying the semantic web and supports Turtle export.

Viewer runtime boundary: Fuseki is the source of data for the semantic web
viewer. The viewer must query and export through Fuseki endpoints instead of
reading `db/semantic_web.ttl` directly at runtime. Turtle files remain useful
as generated artifacts, tests, handoff files, and fallbacks for designer or
importer workflows, but not as the viewer's data source.

### 3.1 Viewer Query Layer

- [x] Define viewer input contract: user question plus available semantic web graph.
- [x] Implement Fuseki-backed graph query support for the configured dataset.
- [x] Implement Fuseki query support when Fuseki is available.
- [x] Add reusable query helpers for classes, instances, labels, scenes, NPCs, monsters, items, rewards, and XP.
- [x] Add tests for Fuseki-backed SPARQL query helpers.
- [x] Add a Fuseki query smoke test that can be skipped when Fuseki is unavailable.

### 3.2 Viewer Agent Execution

- [x] Implement an OpenAI Agents SDK viewer agent.
- [x] Provide agent tools for SPARQL query execution, schema inspection, and graph summary retrieval.
- [x] Require answers to cite queried graph facts in concise natural language.
- [x] Add bounded timeout and retry/error handling.
- [x] Test viewer tools without a live API call.
- [x] Test viewer execution with a stubbed agent response.

### 3.3 Viewer Web UI

- [x] Implement a FastAPI app with a browser chatbot page.
- [x] Add endpoint to submit questions and return chatbot answers.
- [x] Add endpoint to export the semantic web as Turtle.
- [x] Add endpoint to report graph status and triple counts.
- [x] Add simple, dense UI styling suitable for a utility tool.
- [x] Test API endpoints with FastAPI test client.

### 3.4 Viewer Product Run

- [x] Run `uv run python -m src.viewer.main`.
- [x] Verify the page loads in a browser or via HTTP checks.
- [x] Ask representative questions about the generated DnD semantic web.
- [x] Verify exported Turtle parses with `rdflib`.
- [x] Revise viewer code, prompts, tools, or queries if answers are weak or invalid.
- [x] Re-run viewer after revisions until output passes checks.
- [x] Update `README.md` with viewer usage and behavior.
- [x] Commit the viewer milestone.

## Milestone 4: End-To-End Product Validation

- [x] Run designer from a clean generated-output state.
- [x] Run importer from the designer output.
- [x] Run viewer from Fuseki.
- [x] Verify ontology, instances, combined graph, chatbot answer, and Turtle export.
- [x] Document known limitations and configuration options in `README.md`.
- [x] Commit the end-to-end milestone.

## Milestone 5: Semantic Search And Graph Slicing

Goal: improve the standalone semantic-search tool and integrate retrieval-backed
context selection into the designer, importer, and viewer without removing the
current small-data full-context path.

- [x] Add a reusable semantic-search foundation for chunking text files, CSV
  files, and RDF graph content.
- [x] Add deterministic local vector search for tests and optional OpenAI
  embedding search for configured product runs.
- [x] Improve `tools/semantic-search` so it can index markdown, text, and CSV
  files in addition to PDF and HTML.
- [x] Integrate retrieval-backed source context into the designer workflow.
- [x] Integrate retrieval-backed source and ontology context into the importer
  workflow.
- [x] Integrate retrieval-backed graph fact context into the viewer answer path.
- [x] Add focused tests for semantic chunking, search ranking, and workflow
  retrieval integration.
- [x] Update `README.md` with semantic-search configuration and behavior.
- [x] Run `uv run pytest`.
- [x] Commit the semantic-search improvement milestone.

## Milestone 6: Iterative Retrieval-Guided Designer

Goal: improve the semantic web designer so large-data ontology design is guided
by multiple model-planned semantic-search rounds instead of one retrieval pass.

- [x] Add designer configuration for iterative retrieval focus count and slice
  context limits.
- [x] Add a designer planning step that asks the model for focused semantic
  search queries derived from `design-requirements.md` and a data inventory.
- [x] Add per-focus schema-slice drafting so each retrieved context packet
  produces concise design notes before final ontology synthesis.
- [x] Update the designer workflow so large-data runs use planned retrieval
  rounds, while small-data and disabled-search runs keep the existing path.
- [x] Record focus queries, retrieved context sizes, and slice-note sizes in the
  designer retrieval summary and progressive `design.md` log.
- [x] Add focused tests for query planning, schema-slice drafting, and workflow
  iterative retrieval behavior.
- [x] Update `README.md` with the iterative designer retrieval flow.
- [x] Run `uv run pytest`.
- [x] Commit the iterative designer improvement.

## Milestone 7: Iterative Retrieval-Guided Importer

Goal: improve the semantic web importer so large-data instance insertion can be
performed as validated, model-planned import slices instead of one full
instance graph response.

- [x] Add importer configuration for maximum import batches and per-slice
  context limits.
- [x] Add an importer planning step that asks the model whether import coverage
  is complete or which semantic-search focus should be imported next.
- [x] Add per-focus instance-slice generation using retrieved source and schema
  context.
- [x] Update the importer workflow so large-data runs iteratively retrieve,
  generate, validate, and merge instance slices, while small-data and
  disabled-search runs keep the existing one-shot path.
- [x] Validate each slice and the merged instance graph against the full
  ontology graph.
- [x] Record batch queries, retrieved context sizes, slice triple counts, and
  stop reason in importer retrieval summary.
- [x] Add focused tests for import planning, slice generation, graph merging,
  and workflow iterative import behavior.
- [x] Update `README.md` with the iterative importer retrieval flow.
- [x] Run `uv run pytest`.
- [x] Commit the iterative importer improvement.

## Milestone 8: Importer Progressive Logging

Goal: make the slower iterative importer observable by writing progressive
status, planning, retrieval, generation, validation, and final summary details
to `import.md` during the run.

- [x] Add importer configuration for the progressive import log path.
- [x] Write `import.md` at importer start with model, retry, batch, and
  retrieval settings.
- [x] Update `import.md` for each planned import batch and each generated
  instance slice.
- [x] Record final importer persistence/load summary in `import.md`.
- [x] Add tests for importer progress logging.
- [x] Update `README.md` with importer progress-log behavior.
- [x] Run `uv run pytest`.
- [x] Commit the importer progressive logging improvement.

## Current Notes

- Initial dependency installation succeeded.
- CrewAI was tried early, then removed from the designer architecture.
- The semantic web designer milestone is complete, tested, documented, and committed.
- Later verification updates changed the default designer model to `gpt-5-mini`,
  tightened the compact ontology prompt, and added progressive `design.md`
  logging. These updates have been committed.
- The semantic web importer milestone is complete, tested, documented, and committed.
- Designer and importer are independent executables. The importer can run on a
  different machine from a handoff package containing `design.md`,
  `db/ontology.ttl`, and `data/*`.
- The importer now prefers ontology terms from Fuseki when available, with
  `db/ontology.ttl` fallback for portability and graph reload.
- Long-term graph handoff should be database/query-first rather than
  whole-Turtle-prompt-first. Turtle remains useful for review, export, tests,
  portability, and fallback, but agents should consume relevant graph slices
  through Fuseki or local RDF/SPARQL queries when graphs become large.

## Current Designer Limitations And Scale-Up Notes

The semantic web designer milestone is intentionally a workflow-first MVP. The
goal was to prove that the product can read inputs, generate a semantic web
design, validate it, write `design.md`, write an intermediate Turtle ontology,
start or connect to Apache Jena Fuseki, and load the ontology into Fuseki.

### Deliberate Simplifications

- The designer currently reads `./data/*` directly.
- The designer does not yet use `./tools/semantic-search`.
- The designer supports direct loading of markdown, text, and CSV files through
  `src/common/files.py`.
- Direct data loading is acceptable for the current small DnD sample, but it
  will not scale to large files or many files.
- The ontology prompt explicitly asks the model to keep the schema simple.
- The current prompt says to avoid complex or exhaustive modeling.
- The current prompt asks for RDF/RDFS only and explicitly avoids OWL in the
  first version.
- The current prompt asks for about 10 to 16 classes and 15 to 28 properties.
- The current prompt asks the model to keep the full Turtle under 220 triples.
- The current validation rejects ontologies over 260 triples as too complex for
  the first version.
- These simplicity constraints were added because earlier broader design prompts
  made the designer take too long and made the workflow harder to stabilize.

### Workarounds Taken

- CrewAI was removed from the designer because it added orchestration overhead
  and made execution less predictable.
- The designer now uses an OpenAI Agents SDK workflow shell, but operational
  steps are executed explicitly instead of asking the model to decide the full
  workflow sequence.
- The direct OpenAI API design call is still model-driven, but it is constrained
  by a small prompt, validation, and retry feedback.
- The default model is now `gpt-5-mini`, which replaced the earlier `gpt-5.5`
  default after `gpt-5.5-mini` was rejected by the API as an unknown model.
- `design.md` is written progressively during designer runs. It records run
  start, each attempt start, LLM response or failure, validation status, and the
  accepted candidate design. After success, the final design is written at the
  top and the progress history is appended as `Designer Generation Log`.
- Turtle is used as a validated intermediate artifact for review, tests, and
  Fuseki loading. It is not the final runtime target.
- Fuseki startup needed a project-local writable runtime base. The manager now
  sets `FUSEKI_BASE` to `db/fuseki-run`.
- Fuseki readiness needed a SPARQL `ASK` POST request. A GET request to the
  query endpoint was not reliable for Fuseki 6.
- Fuseki cleanup now stops workflow-owned Fuseki processes after designer and
  importer runs. If Fuseki was already running before the workflow, it is
  treated as externally owned and left running.

### Fuseki Usage Instructions For Future Work

- Fuseki is installed at `/opt/apache-jena-fuseki-6.1.0`.
- Do not use the default Fuseki base under
  `/opt/apache-jena-fuseki-6.1.0/run` for this project. It may not be writable.
- Use the project-local runtime base `db/fuseki-run`.
- The working startup pattern is:

```bash
FUSEKI_BASE=/home/sunlu/Projects/semantic-web-processor/db/fuseki-run \
  /opt/apache-jena-fuseki-6.1.0/fuseki-server \
  --tdb2 \
  --loc=/home/sunlu/Projects/semantic-web-processor/db/fuseki-data \
  --update --localhost /semantic-web-processor
```

- Keep `--update` enabled so graph loading and SPARQL updates work.
- Keep `--tdb2 --loc=.../db/fuseki-data` enabled so Fuseki persists graph data
  across shutdowns.
- Keep `--localhost` for local development.
- Logs should go to `db/fuseki.log`.
- Designer and importer cleanup stops only workflow-owned Fuseki processes.
  Existing Fuseki processes are left alone.
- If Fuseki reports port `3030` is already bound, check for stale Fuseki
  processes with `pgrep -af fuseki`.
- Do not use `GET /semantic-web-processor/query` as the main readiness check.
- Use a SPARQL `ASK { ?s ?p ?o }` request through `POST` to check readiness.
- Load ontology data through:
  `http://localhost:3030/semantic-web-processor/data`
- Query data through:
  `http://localhost:3030/semantic-web-processor/query`
- The designer ontology graph URI is:
  `http://example.org/dnd-adventure/graph/ontology`
- Verify ontology implementation with a named-graph SPARQL query against the
  ontology graph, not only by checking that `db/ontology.ttl` exists.

### Future Scale-Up Requirements

- Add retrieval support to the designer before using large or numerous data
  files.
- Add retrieval support to the importer before using large or numerous data
  files.
- Integrate `./tools/semantic-search` into designer and importer workflows as a
  tool or adapter.
- Extend or wrap `./tools/semantic-search` so it supports the project data
  formats, especially markdown and CSV.
- Add a designer workflow tool such as `retrieve_design_context` that retrieves
  only relevant source chunks for ontology design.
- Add importer workflow tools such as `retrieve_import_context` and
  `retrieve_schema_context` that retrieve source facts and relevant ontology
  slices for instance insertion.
- Replace whole-data prompt stuffing with retrieval over relevant chunks in
  both designer and importer.
- Relax the current prompt limits only after retrieval and validation are strong
  enough.
- Do not remove all simplicity guidance at once. A better scale-up path is:
  first generate a small core ontology, then run one or more refinement stages
  that expand the ontology only when retrieved data proves the need.
- Replace the current fixed size limits with quality-oriented constraints, such
  as importer usability, clear class/property hierarchy, validation coverage,
  and avoiding overfitting to one sample file.
- Consider adding a separate schema review/refinement agent step that evaluates
  whether new classes or properties are justified by the data.
- Treat Fuseki as the long-term source of truth for implemented ontology and
  instance graphs. Fuseki now starts with project-local persistent TDB2 storage
  by default, so graph data can survive machine shutdown. `design.md` should
  remain reference documentation for humans and agents, not the only
  machine-readable contract.
- Future importer/viewer agents should query Fuseki for relevant graph slices
  when available, with local RDF/Turtle fallback for portability and tests.
  For large graphs, use a semantic-web embedding index over text-rendered
  triples to find candidate classes, properties, and facts before issuing
  targeted Fuseki queries.

## Current Status Summary

### Successful

- Repository structure and project instructions were inspected.
- The project goal was clarified as three separate executables:
  - semantic web designer in `src/designer`
  - semantic web importer in `src/importer`
  - semantic web viewer in `src/viewer`
- The broad initial implementation checklist was replaced with this detailed milestone plan.
- Baseline dependencies were added to `pyproject.toml`.
- Dependencies were installed successfully with `uv sync --all-extras --dev`.
- A shared foundation layer was added:
  - `src/common/config.py`
  - `src/common/files.py`
  - `src/common/rdf.py`
  - `src/common/fuseki.py`
  - `src/common/llm.py`
- The first designer framework pieces were added:
  - `src/designer/agent.py`
  - `src/designer/main.py`
  - `src/designer/workflow.py`
- The designer now has:
  - a structured input and output contract
  - direct LLM execution path
  - OpenAI Agents SDK workflow orchestration
  - tools for Fuseki status, Fuseki startup, iterative design, and ontology persistence/load
  - bounded LLM timeout configuration
  - retry feedback when generated output fails validation
  - RDF/Turtle parsing validation
  - generic RDF/RDFS schema validation
  - Jena Fuseki as the intended implementation target
  - Turtle as an intermediate artifact and fallback
- The importer framework was added:
  - `src/importer/agent.py`
  - `src/importer/main.py`
  - `src/importer/validation.py`
  - `src/importer/workflow.py`
- The importer now has:
  - a structured input and output contract
  - direct LLM execution path
  - OpenAI Agents SDK workflow orchestration
  - tools for reading design text, reading source data, inspecting ontology terms, iterative import, and instance persistence/load
  - bounded LLM timeout configuration
  - retry feedback when generated output fails validation
  - RDF/Turtle parsing validation
  - ontology-driven no-schema-mutation validation
  - Jena Fuseki as the intended implementation target
  - Turtle as an intermediate artifact and fallback
- Initial tests were added:
  - `tests/test_foundation.py`
  - `tests/test_designer_contract.py`
  - `tests/test_designer_workflow.py`
  - `tests/test_importer_contract.py`
  - `tests/test_importer_workflow.py`
  - `tests/test_importer_product_output.py`
- The lightweight test suite passes:
  - command: `uv run pytest`
  - result: `28 passed`

### Historical Issues And Fixes

- The first live designer run using the early CrewAI path was stopped because it produced no progress output for too long.
- CrewAI was removed from the designer plan, code, dependency metadata, and local environment.
- A second live designer run using the direct LLM path was also stopped because it still took too long without visible progress.
- A live designer run using model-decided Agents SDK orchestration was stopped because the first orchestration call took too long without visible progress.
- The designer workflow was revised to keep the Agents SDK shell and tools but execute the operational steps explicitly.
- A later explicit-workflow live designer run reached the design step but was stopped because the design prompt was still too broad.
- The designer prompt was revised to require a simple first-version RDF/RDFS ontology, first with about 12 to 18 classes and 20 to 35 properties, then later tightened to about 10 to 16 classes and 15 to 28 properties with fewer than 220 triples requested.
- Default designer validation attempts were reduced to 2 while stabilizing the product run.
- The designer default model was changed from `gpt-5.5` to `gpt-5-mini` to reduce cost and latency for the compact design task. An attempted `gpt-5.5-mini` default was rejected by the API as an unknown model.
- Progressive `design.md` logging was added after a long LLM call made it hard to tell whether the workflow was still active. LLM request failures and timeouts are now recorded in `design.md` and can feed retry attempts.
- Fuseki startup initially failed because the default Fuseki base under `/opt` was not writable. The manager now sets `FUSEKI_BASE` to `db/fuseki-run`.
- Fuseki readiness initially failed because Fuseki 6 handles SPARQL availability by POST, not by GET. The client now uses `ASK { ?s ?p ?o }`.
- The designer product run completed successfully with `load_target: fuseki`.
- Final designer output: `design.md`, `db/ontology.ttl`, and a named Fuseki graph at `http://example.org/dnd-adventure/graph/ontology`.
- Latest ontology verification after the compact prompt and `gpt-5-mini` rerun: 188 triples, 15 classes, 28 properties, RDF validation passed, Fuseki SPARQL query returned 15 ontology classes.
- Final designer test command: `uv run pytest`, result `14 passed`.
- Importer work was approved by the user and completed.
- `design.md` and `db/ontology.ttl` have been produced by the designer.
- `db/instances.ttl` and `db/semantic_web.ttl` have been produced by the importer.
- The importer framework has been implemented.
- The importer now prefers Fuseki ontology inspection and falls back to
  `db/ontology.ttl` when Fuseki is unavailable or the ontology graph is empty.
- Fuseki startup now uses persistent project-local TDB2 storage under
  `db/fuseki-data` instead of `--mem`.
- The semantic web viewer framework has been implemented and verified against
  Fuseki as the runtime data source.
- Viewer chat sessions are persisted as JSON files under `chat/viewer/`.
  Opening or refreshing the browser creates a new transcript file, and later
  questions in the same page session include recent conversation history.
- Semantic web design and data insertion have been completed by the product.
- Fuseki ontology loading has been successfully performed.
- Fuseki instance loading has been successfully performed.
- End-to-end validation from a clean generated-output state succeeded on
  2026-05-31. Fresh output: 185 ontology triples, 13 classes, 28 properties,
  178 instance triples, 363 combined triples, 363 Fuseki triples, chatbot answer
  verified through the viewer API, and Fuseki Turtle export parsed with rdflib.
- A later clean forced-retrieval end-to-end validation on 2026-05-31 succeeded
  after adding robust schema-slice fallback parsing. The iterative designer used
  two model-planned semantic-search focuses, produced 148 ontology triples, the
  importer produced 57 instance triples and 205 combined triples, the viewer
  answered through the API, exported Turtle parsed with rdflib, and
  `uv run pytest` reported 56 passed and 2 skipped.
- The designer milestone commit has been made.
- The importer milestone commit has been made.
- The viewer milestone commit has been made.

### Immediate Next Step

- Continue future scale-up work: semantic-web graph slicing, semantic-search
  integration for designer/importer, and ontology refinement workflow.

## Handoff For Next Codex Instance

- Start by reading `AGENTS.md`, `README.md`, and this file.
- The semantic web designer is complete and committed.
- The semantic web importer is complete and committed.
- Current generated outputs are:
  - `design.md`
  - `db/ontology.ttl`
  - `db/instances.ttl`
  - `db/semantic_web.ttl`
  - Fuseki ontology graph `http://example.org/semantic-web/graph/ontology`
  - Fuseki data graph `http://example.org/semantic-web/graph/data` unless overridden by `.env`
- Current tests:
  - `uv run pytest`
  - expected result after fresh end-to-end run: `45 passed, 2 skipped`
- Current runtime notes:
  - Fuseki may already be running on port `3030`.
  - If not, use the project-local Fuseki base `db/fuseki-run`.
  - Persistent Fuseki data is stored in `db/fuseki-data`.
  - Do not use `/opt/apache-jena-fuseki-6.1.0/run` as the runtime base.
  - Use SPARQL `ASK` via `POST` for readiness checks.
- Current development boundary:
  - Designer, importer, and viewer milestones are implemented.
  - The viewer uses Fuseki as its runtime data source and does not read
    `db/semantic_web.ttl` directly.
