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
- [x] Test direct agent execution with a stubbed LLM response.
- [x] Test Agents SDK workflow configuration without requiring a live API call.

### 1.3 Designer RDF Validation

- [x] Validate generated Turtle with `rdflib`.
- [x] Validate required prefixes and base namespace.
- [x] Validate required high-level modeling coverage: adventure, quest, scene, location, character, NPC, monster, player option, item, weapon, encounter, check, reward, and victory condition.
- [x] Validate that core properties have `rdfs:domain` and `rdfs:range` where practical.
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

- [ ] Define importer input contract: design document, ontology Turtle, source data, and namespace policy.
- [ ] Define importer output contract: instance Turtle only, with no schema mutation.
- [ ] Add tests for importer output contract parsing using fixture responses.

### 2.2 Importer Agent Execution

- [ ] Implement an OpenAI Agents SDK importer agent.
- [ ] Provide agent tools for reading design text, reading source data, inspecting ontology terms, and returning Turtle.
- [ ] Add bounded timeout and retry feedback.
- [ ] Add command-line logging for model, source files, retries, and output locations.
- [ ] Test importer tool functions without a live API call.
- [ ] Test importer execution with a stubbed agent response.

### 2.3 Importer RDF Validation

- [ ] Validate generated instance Turtle with `rdflib`.
- [ ] Validate that instance graph imports or uses the ontology namespace.
- [ ] Validate that the importer does not create new `rdfs:Class` or `rdf:Property` terms outside the generated ontology.
- [ ] Validate that source data coverage includes named NPCs, monsters, items, scenes, loot, rewards, and XP awards.
- [ ] Add tests for valid importer output.
- [ ] Add tests that schema mutation triggers retry feedback.

### 2.4 Importer Persistence

- [ ] Write generated instances to `db/instances.ttl`.
- [ ] Combine ontology and instances into `db/semantic_web.ttl`.
- [ ] Load instance graph into Fuseki when Fuseki is available.
- [ ] Fall back to local Turtle files when Fuseki is unavailable.
- [ ] Add tests for local instance persistence and graph combination.
- [ ] Add a Fuseki smoke test that can be skipped when Fuseki is unavailable.

### 2.5 Importer Product Run

- [ ] Run `uv run python -m src.importer.main`.
- [ ] Inspect `db/instances.ttl` using RDF parsing and SPARQL checks.
- [ ] Ask source-coverage SPARQL questions against the combined graph.
- [ ] Revise importer code, prompts, tools, or validators if the product output is weak or invalid.
- [ ] Re-run importer after revisions until output passes checks.
- [ ] Update `README.md` with importer usage and behavior.
- [ ] Commit the importer milestone.

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

- Initial dependency installation succeeded with `uv sync --all-extras --dev`.
- A first live designer run was stopped because the model call took too long without progress output.
- The next implementation step is designer persistence tests and command-line logging before attempting another live model run.

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
  - `src/designer/validation.py`
  - `src/designer/workflow.py`
- The designer now has:
  - a structured input and output contract
  - direct LLM execution path
  - OpenAI Agents SDK workflow orchestration
  - tools for Fuseki status, Fuseki startup, iterative design, and ontology persistence/load
  - bounded LLM timeout configuration
  - retry feedback when generated output fails validation
  - RDF/Turtle parsing validation
  - required DnD ontology coverage validation
  - Jena Fuseki as the intended implementation target
  - Turtle as an intermediate artifact and fallback
- Initial tests were added:
  - `tests/test_foundation.py`
  - `tests/test_designer_contract.py`
  - `tests/test_designer_workflow.py`
- The lightweight test suite passes:
  - command: `uv run pytest`
  - result: `10 passed`

### Failed Or Stopped

- The first live designer run using the default CrewAI path was stopped because it produced no progress output for too long.
- CrewAI was removed from the designer plan, code, dependency metadata, and local environment.
- A second live designer run using the direct LLM path was also stopped because it still took too long without visible progress.
- A live designer run using model-decided Agents SDK orchestration was stopped because the first orchestration call took too long without visible progress.
- The designer workflow was revised to keep the Agents SDK shell and tools but execute the operational steps explicitly.
- A later explicit-workflow live designer run reached the design step but was stopped because the design prompt was still too broad.
- The designer prompt was revised to require a simple first-version RDF/RDFS ontology, with about 12 to 18 classes and 20 to 35 properties.
- Default designer validation attempts were reduced to 2 while stabilizing the product run.
- Fuseki startup initially failed because the default Fuseki base under `/opt` was not writable. The manager now sets `FUSEKI_BASE` to `db/fuseki-run`.
- Fuseki readiness initially failed because Fuseki 6 handles SPARQL availability by POST, not by GET. The client now uses `ASK { ?s ?p ?o }`.
- The designer product run completed successfully with `load_target: fuseki`.
- Final designer output: `design.md`, `db/ontology.ttl`, and a named Fuseki graph at `http://example.org/dnd-adventure/graph/ontology`.
- Final ontology verification: 224 triples, 15 classes, 35 properties, RDF validation passed, Fuseki SPARQL query returned 15 ontology classes.
- Final designer test command: `uv run pytest`, result `12 passed`.
- Work is paused after the semantic web designer milestone. The importer has not been started.
- No final `design.md`, `db/ontology.ttl`, `db/instances.ttl`, or `db/semantic_web.ttl` has been produced yet.
- The importer framework has not been implemented yet.
- The viewer framework has not been implemented yet.
- No semantic web design or data insertion has been completed by the product yet.
- No Fuseki load has been successfully performed yet.
- No milestone commit has been made yet.

### Immediate Next Step

- Add designer persistence tests for writing `design.md` and intermediate `db/ontology.ttl`.
- Add an Agents SDK workflow configuration smoke test that does not require a live API call.
- Only after those small tests pass, retry the live designer product run.
