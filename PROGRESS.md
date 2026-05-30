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

- [ ] Add optional ontology inspection by querying Fuseki when available.
- [ ] Keep `db/ontology.ttl` as the portable fallback and cross-machine handoff artifact.
- [ ] Add tests for Fuseki ontology inspection with local Turtle fallback.
- [ ] Replace whole-ontology Turtle prompt input with query-based ontology summaries and relevant schema slices so large ontologies do not have to fit in the LLM context.
- [ ] Prefer Fuseki query inspection for large graphs, with local RDF/SPARQL fallback when Fuseki is unavailable.

## Milestone 3: Viewer Framework

Goal: the semantic web viewer starts a browser-based chatbot UI that answers
questions by querying the semantic web and supports Turtle export.

### 3.1 Viewer Query Layer

- [ ] Define viewer input contract: user question plus available semantic web graph.
- [ ] Implement local graph query support from `db/semantic_web.ttl`.
- [ ] Implement Fuseki query support when Fuseki is available.
- [ ] Add reusable query helpers for classes, instances, labels, scenes, NPCs, monsters, items, rewards, and XP.
- [ ] Add tests for local SPARQL query helpers.
- [ ] Add a Fuseki query smoke test that can be skipped when Fuseki is unavailable.

### 3.2 Viewer Agent Execution

- [ ] Implement an OpenAI Agents SDK viewer agent.
- [ ] Provide agent tools for SPARQL query execution, schema inspection, and graph summary retrieval.
- [ ] Require answers to cite queried graph facts in concise natural language.
- [ ] Add bounded timeout and retry/error handling.
- [ ] Test viewer tools without a live API call.
- [ ] Test viewer execution with a stubbed agent response.

### 3.3 Viewer Web UI

- [ ] Implement a FastAPI app with a browser chatbot page.
- [ ] Add endpoint to submit questions and return chatbot answers.
- [ ] Add endpoint to export the semantic web as Turtle.
- [ ] Add endpoint to report graph status and triple counts.
- [ ] Add simple, dense UI styling suitable for a utility tool.
- [ ] Test API endpoints with FastAPI test client.

### 3.4 Viewer Product Run

- [ ] Run `uv run python -m src.viewer.main`.
- [ ] Verify the page loads in a browser or via HTTP checks.
- [ ] Ask representative questions about the generated DnD semantic web.
- [ ] Verify exported Turtle parses with `rdflib`.
- [ ] Revise viewer code, prompts, tools, or queries if answers are weak or invalid.
- [ ] Re-run viewer after revisions until output passes checks.
- [ ] Update `README.md` with viewer usage and behavior.
- [ ] Commit the viewer milestone.

## Milestone 4: End-To-End Product Validation

- [ ] Run designer from a clean generated-output state.
- [ ] Run importer from the designer output.
- [ ] Run viewer from the combined semantic web.
- [ ] Verify ontology, instances, combined graph, chatbot answer, and Turtle export.
- [ ] Document known limitations and configuration options in `README.md`.
- [ ] Commit the end-to-end milestone.

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
- The portable ontology handoff artifact is `db/ontology.ttl` or an equivalent
  export, not the in-memory Fuseki process state.
- Future importer improvement: optionally inspect ontology terms from Fuseki
  when Fuseki is available, with `db/ontology.ttl` fallback for portability.
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
  --mem --update --localhost /semantic-web-processor
```

- Keep `--update` enabled so graph loading and SPARQL updates work.
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
  instance graphs. `design.md` should remain reference documentation for humans
  and agents, not the only machine-readable contract.
- Future importer/viewer agents should query Fuseki for relevant graph slices
  when available, with local RDF/Turtle fallback for portability and tests.

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
- The viewer framework has not been implemented yet.
- Semantic web design and data insertion have been completed by the product.
- Fuseki ontology loading has been successfully performed.
- Fuseki instance loading has been successfully performed.
- The designer milestone commit has been made.
- The importer milestone commit has been made.

### Immediate Next Step

- Start Milestone 3 with viewer query-layer contracts and tests.

## Handoff For Next Codex Instance

- Start by reading `AGENTS.md`, `README.md`, and this file.
- The semantic web designer is complete and committed.
- The semantic web importer is complete and committed.
- Current generated outputs are:
  - `design.md`
  - `db/ontology.ttl`
  - `db/instances.ttl`
  - `db/semantic_web.ttl`
  - Fuseki named graph `http://example.org/dnd-adventure/graph/ontology`
  - Fuseki data graph `http://example.org/semantic-web/graph/data` unless overridden by `.env`
- Current tests:
  - `uv run pytest`
  - expected result: `28 passed`
- Current runtime notes:
  - Fuseki may already be running on port `3030`.
  - If not, use the project-local Fuseki base `db/fuseki-run`.
  - Do not use `/opt/apache-jena-fuseki-6.1.0/run` as the runtime base.
  - Use SPARQL `ASK` via `POST` for readiness checks.
- Current development boundary:
  - The viewer has not been started.
