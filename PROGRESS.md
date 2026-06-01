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
- [x] Replace whole-graph prompting with Fuseki-backed relevant graph slices.
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

## Milestone 9: Non-DnD End-To-End Validation

Goal: verify that the product remains domain-neutral by replacing the DnD
sample with a non-DnD design requirement and non-DnD source data, then running
the full designer, importer, and viewer workflow from a clean generated-output
state.

- [x] Choose or create a non-DnD dataset, using a probability, statistics, and
  data-science notebook PDF as the source file.
- [x] Replace `design-requirements.md` and `data/*` with the non-DnD test case,
  keeping a way to restore the current DnD sample afterward if needed.
- [x] Stop Fuseki if it is running.
- [x] Delete generated outputs: `design.md`, `import.md`, and `db/*`.
- [x] Run the semantic web designer from the non-DnD inputs.
- [x] Run the semantic web importer from the designer output.
- [x] Run the semantic web viewer from Fuseki.
- [x] Ask representative non-DnD viewer questions, including follow-up and
  reasoning questions.
- [x] Verify Turtle export parses with `rdflib`.
- [x] Run `uv run pytest`.
- [x] Document the non-DnD validation result in `README.md` and `PROGRESS.md`.
- [x] Commit the non-DnD validation milestone.

## Milestone 10: CSV-Aware Design And Deterministic Import

Goal: validate and improve handling of structured CSV input before scaling up
long unstructured documents. The designer should inspect CSV headers, inferred
column types, row counts, and representative rows so it can reflect tabular
data structure in the ontology. The importer should not ask an LLM to convert
every CSV row into Turtle. Instead, the LLM should help produce a constrained
row-to-RDF mapping specification, and deterministic Python code should validate
that mapping against the generated ontology, loop over all CSV rows, and emit
instance Turtle.

Rationale:

- CSV files can contain thousands or millions of rows. Prompting all rows to an
  LLM is slow, expensive, and brittle.
- CSV is structured data, so the workflow should exploit headers, column
  datatypes, identifiers, foreign-key-like columns, and sample values.
- The designer needs only a CSV profile for ontology design: file name, row
  count, headers, inferred datatypes, null counts, distinct/example values, and
  a few representative rows, plus clues from `design-requirements.md`.
- The importer needs a repeatable mapping from rows to ontology classes,
  properties, datatypes, labels, URIs, and relationships. Once the mapping is
  validated, row conversion should be deterministic and testable.
- Product code must remain domain-neutral. CSV mapping logic should be driven
  by generated ontology terms, design requirements, source CSV profiles, and a
  structured mapping specification, not hardcoded domain-specific column names.

Suggested architecture:

- Add shared CSV profiling utilities under `src/common` or another suitable
  shared module. The profiler should summarize each CSV without reading every
  row into prompts.
- Equip the designer workflow with a CSV-profile context/tool so large CSVs are
  represented by schema/sample summaries rather than full CSV text.
- Add an importer CSV-mapping planner that asks the LLM for structured JSON, not
  executable code and not full Turtle. The JSON should describe row class,
  subject URI template, label template, column-to-property mappings, datatype
  casts, optional object relationships, missing-value behavior, and provenance.
- Add strict mapping validation against ontology classes/properties/ranges and
  reject mappings that introduce schema terms or reference missing ontology
  terms.
- Add deterministic CSV-to-RDF generation that applies a validated mapping to
  every row and emits Turtle. It should support stable URI generation,
  escaping/literal datatypes, skipped null values, row-level provenance, and
  duplicate prevention where practical.
- Keep retrieval-guided LLM import for unstructured markdown/text/PDF. Use
  deterministic mapping for CSV rows. Mixed datasets should support both paths
  in the same importer run.
- Treat the first CSV milestone as another domain-neutral end-to-end test, not
  as a domain-specific one-off.

Implementation checklist:

- [x] Choose or create a small but realistic non-DnD CSV test dataset, ideally
  with multiple columns, numeric/date/string fields, missing values, and at
  least one relationship-like column. Add matching `design-requirements.md`
  text that describes the desired semantic web in domain-neutral terms.
- [ ] Preserve or document how to restore the current PDF proof-of-concept
  input after CSV validation if needed.
- [x] Add a CSV profiler utility that reports file name, row count, column
  names, inferred datatype per column, null counts, distinct counts or capped
  example values, and the first few/sample rows.
- [x] Add focused tests for the CSV profiler, including numeric, date-like,
  string, boolean-like, missing-value, and high-cardinality columns.
- [x] Update designer data-loading/retrieval behavior so CSV profile summaries
  are available to the design prompt and large CSVs are not prompt-stuffed row
  by row.
- [x] Add focused designer workflow tests showing that CSV profile summaries are
  used in design context and that full large CSV contents are not sent wholesale
  when a profile is sufficient.
- [x] Define a constrained importer CSV mapping JSON schema. Include row class,
  URI template, label template, column mappings, datatype casts, relationship
  mappings, skipped-null behavior, source/provenance options, and optional
  fallback behavior for invalid rows.
- [x] Add an importer mapping-planning tool or internal step that asks the LLM
  to produce the mapping JSON from `design.md`, ontology terms, and CSV
  profiles. Do not ask the model to produce one Turtle block containing every
  CSV row.
- [x] Add mapping validation against the existing ontology graph. Validation
  must reject new classes/properties, unknown ontology terms, invalid datatype
  choices, invalid URI templates, and unsafe/free-form code.
- [x] Add deterministic CSV-to-RDF generation from a validated mapping. It
  should stream or iterate rows, generate stable instance URIs, emit literals
  with RDF datatypes, skip configured nulls, and serialize valid Turtle.
- [x] Add focused tests for mapping validation and CSV-to-RDF generation,
  including escaping special characters, null handling, datatype conversion,
  stable URI generation, duplicate prevention, and ontology-term enforcement.
- [x] Integrate deterministic CSV import into the importer workflow while
  keeping existing LLM/retrieval import for unstructured sources. Mixed
  CSV-plus-text/PDF datasets should combine both outputs and validate the merged
  instance graph.
- [x] Add importer workflow tests with stubbed mapping-planner output and a CSV
  fixture with enough rows to prove row conversion is deterministic and not
  model-per-row.
- [x] Run a clean CSV end-to-end validation: stop Fuseki, delete generated
  outputs, run designer, run importer, start viewer, ask representative CSV
  questions, verify Turtle export parses, and run `uv run pytest`.
- [x] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with CSV profiling,
  mapping, deterministic import behavior, configuration notes, limitations, and
  validation results.
- [x] Commit the CSV-aware design/import milestone.

## Milestone 11: Test And Production Modes

Goal: keep the current compact, stable workflow as the default test mode, while
adding an explicit production mode switch for comprehensive prompts, stronger
model defaults, and larger validation/retrieval budgets.

- [x] Add `.env` configuration for `SEMANTIC_WEB_MODE=test|production`,
  defaulting to `test`.
- [x] Keep test mode behavior equivalent to the current compact workflow:
  `gpt-5-mini`, compact designer prompt, low retrieval/batch counts, and the
  current ontology size validation.
- [x] Add production mode defaults: `gpt-5.5`, comprehensive designer prompt,
  higher retrieval/batch counts, larger context limits, longer timeout, and
  relaxed ontology size validation.
- [x] Keep explicit environment overrides such as `LLM_MODEL`,
  `DESIGNER_RETRIEVAL_FOCUSES`, and `IMPORTER_RETRIEVAL_BATCHES` working in
  both modes.
- [x] Add focused tests for mode defaults, designer prompt selection, and
  production ontology validation limits.
- [x] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with the mode switch.
- [x] Run `uv run pytest`.
- [x] Commit the test/production mode switch.

## Milestone 12: New CSV Example Mode Comparison

Goal: validate the product on a new, previously untested CSV-containing example
and compare the outputs from default test mode and production mode.

- [ ] Prepare a new example dataset under `data/*` with at least one CSV file
  and matching `design-requirements.md`. The example should be unrelated to
  the current semantic-web/ontology/triplestore data and unrelated to older DnD
  or probability/PDF examples.
- [ ] Preserve or document how to restore the current CSV-aware example if
  needed.
- [ ] Run a clean end-to-end test in default test mode:
  `SEMANTIC_WEB_MODE=test` or unset, delete generated outputs, run designer,
  run importer, start viewer, ask representative questions, verify Turtle
  export parses, and run `uv run pytest`.
- [ ] Record test-mode output metrics: model, designer focus count, ontology
  triples/classes/properties, CSV mapping count, deterministic CSV triples,
  total instance triples, combined triples, viewer answers, export parse count,
  runtime notes, and any weak answers.
- [ ] Run a clean end-to-end test in production mode:
  `SEMANTIC_WEB_MODE=production`, delete generated outputs, run designer,
  run importer, start viewer, ask the same representative questions, verify
  Turtle export parses, and run `uv run pytest`.
- [ ] Record production-mode output metrics with the same fields as test mode.
- [ ] Compare test and production mode outputs for schema richness, instance
  coverage, CSV mapping fidelity, viewer answer quality, runtime, cost/risk,
  and validation failures or retries.
- [ ] Decide whether production defaults need adjustment before long-document
  scale-up.
- [ ] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with the validation
  result and mode comparison.
- [ ] Commit the new CSV example mode comparison milestone.

## Milestone 13: README Setup And Run Guide

Goal: rewrite or substantially improve `README.md` so a user can set up and
run the application end to end on a machine without a vibe coding agent and
possibly without preliminary installations.

- [ ] Document prerequisites clearly: supported Python version, `uv`, git,
  Apache Jena Fuseki, Java requirements for Fuseki, OpenAI API key, and network
  access expectations.
- [ ] Document first-time setup from a fresh clone: dependency installation,
  `.env` creation, API key configuration, Fuseki location/configuration, and
  writable project-local Fuseki runtime/storage directories.
- [ ] Document `.env` settings in practical groups: OpenAI/model settings,
  test/production mode, retrieval limits, designer/importer iterations, Fuseki
  endpoints and graph URIs, viewer host/port, and semantic-search provider.
- [ ] Explain test mode versus production mode, including default model,
  prompt behavior, retrieval/batch budgets, ontology triple limits, expected
  runtime/cost tradeoffs, and how explicit overrides work.
- [ ] Document how to replace `design-requirements.md` and `data/*` with a new
  dataset, including CSV, markdown/text, and PDF inputs.
- [ ] Document clean end-to-end run commands: stop stale Fuseki, remove
  generated outputs, run designer, run importer, start viewer, ask questions,
  export Turtle, and run tests.
- [ ] Document troubleshooting for common failures: missing API key, unknown
  model, Fuseki port already bound, unwritable Fuseki base, graph load fallback,
  bad Turtle, invalid CSV mapping, viewer showing missing facts, and export
  parse failure.
- [ ] Document expected generated artifacts and which ones are runtime source
  of truth versus review/export/fallback files.
- [ ] Add a concise quick-start path and a more detailed setup/reference path.
- [ ] Run documentation sanity checks and `uv run pytest`.
- [ ] Commit the README setup/run guide update.

## Milestone 14: Long-Document Coverage Scale-Up

Goal: move beyond proof-of-concept semantic webs for long source documents by
improving coverage, structure extraction, iteration depth, and schema/instance
refinement while keeping Fuseki as the runtime source of truth.

- [ ] Add a coverage ledger for designer/importer runs that records source
  chapters, sections, page ranges, formulas, tables, code examples, tools,
  named concepts, and imported graph areas.
- [ ] Improve PDF preprocessing into section-aware chunks using extracted
  headings, table-of-contents structure, page numbers, formulas, tables, figure
  captions, and code blocks where available.
- [x] Add a scale-up configuration profile for long documents with higher
  `DESIGNER_RETRIEVAL_FOCUSES`, higher `IMPORTER_RETRIEVAL_BATCHES`, larger
  slice context caps, and optional stronger `LLM_MODEL` settings.
- [x] Add prompt modes that explicitly ask for comprehensive coverage instead
  of only a compact first-pass semantic web.
- [ ] Add ontology refinement passes that review uncovered evidence and propose
  schema additions only when the existing ontology cannot represent important
  content.
- [ ] Add importer continuation passes that resume from existing Fuseki data,
  avoid duplicates, and import uncovered sections until coverage is complete or
  a configured budget is reached.
- [ ] Add viewer or script-based coverage reports that summarize what the graph
  covers and what source areas remain missing.
- [ ] Validate the scale-up mode on `data/main.pdf` and compare graph coverage
  against the proof-of-concept result.
- [x] Run `uv run pytest`.
- [ ] Update `README.md` and `PROGRESS.md` with the scale-up validation result.
- [ ] Commit the scale-up milestone.

## Milestone 15: CSV Datatype Robustness

Goal: make CSV-aware design and import more robust when column datatypes are
ambiguous, dirty, or semantically different from their surface values. The
designer should receive conservative datatype guidance, and the deterministic
CSV importer should support safe datatype compatibility instead of failing on
avoidable integer/decimal/string mismatches.

- [x] Extend CSV profiling with datatype compatibility notes, including risky
  numeric-looking identifiers, leading-zero values, mixed examples, and safer
  string fallbacks.
- [x] Update designer CSV context and prompt guidance so uncertain CSV columns
  prefer `xsd:string`, and numeric/date/boolean ranges are used only when the
  profile and column semantics clearly support them.
- [x] Update CSV import validation to accept safe datatype widening, such as
  integer mappings for decimal ontology ranges and string-compatible ontology
  ranges for dirty values.
- [x] Update deterministic CSV literal generation to choose ontology-compatible
  literals and fall back to strings only when the ontology range permits it.
- [x] Add focused tests for conservative CSV profiling, designer CSV context,
  range compatibility, numeric widening, and safe string fallback.
- [x] Run `uv run pytest`.
- [x] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with the CSV datatype
  robustness behavior.
- [x] Commit the CSV datatype robustness milestone.

## Milestone 16: Viewer Semantic Class Matching

Goal: improve viewer chatbot recall when user wording does not lexically match
designer-generated class names. The viewer should use the model's language
ability to map user terms such as "kids" to ontology classes such as
`TenYearOld` when graph labels/comments make that match plausible, then query
those class instances before generating the final answer.

- [x] Add a viewer concept-matching prompt that receives the user question,
  chat history, and class summary, then returns candidate class labels.
- [x] Query class instance counts and instances for LLM-matched classes, while
  keeping the existing exact, lexical, and semantic fact retrieval paths.
- [x] Bound the matcher output and ignore classes not present in the graph
  summary.
- [x] Add focused tests for a non-lexical class match such as "kids" mapping to
  `TenYearOld`.
- [x] Run `uv run pytest`.
- [x] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with the viewer
  semantic class matching behavior.
- [x] Commit the viewer semantic class matching milestone.

## Milestone 17: Current Dataset Production End-To-End Validation

Goal: validate the current semantic-web/ontology/triplestore dataset in
`SEMANTIC_WEB_MODE=production` before the later Milestone 12 new-example mode
comparison.

- [x] Run the semantic web designer in production mode.
- [x] Run the semantic web importer in production mode.
- [x] Start or verify Fuseki against the persistent project-local TDB2 data.
- [x] Verify viewer status and Turtle export from Fuseki.
- [x] Ask a representative viewer question through the viewer workflow/API.
- [x] Run `uv run pytest`.
- [x] Record production-mode metrics and findings in `PROGRESS.md`.
- [x] Commit the current-dataset production validation.

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
- Product data ingestion and semantic-search chunking now support PDF source
  files through PyMuPDF, in addition to markdown, text, and CSV.
- Non-DnD end-to-end validation succeeded on 2026-06-01 using
  `data/main.pdf`, a probability, statistics, and data-science notebook.
  The designer produced 202 ontology triples, 22 RDFS classes, and 23 RDF
  properties. The importer produced 108 instance triples and 310 combined
  triples. Viewer workflow and FastAPI checks answered grounded notebook
  questions about distributions, Poisson facts, CLT/LLN assumptions, and sample
  mean reasoning. Fuseki Turtle export parsed with 310 triples, and
  `uv run pytest` reported 63 passed and 2 skipped.
- The non-DnD PDF semantic web is a proof of concept, not complete notebook
  coverage. The current prompts and limits intentionally favor a compact,
  validated graph over exhaustive extraction. Richer coverage should be possible
  by scaling up model strength, retrieval focus count, importer batches,
  context limits, coverage tracking, and schema/instance refinement loops.
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

- The designer still supports direct loading of markdown, text, PDF, and CSV files
  through `src/common/files.py` for small data.
- For larger inputs, the designer now uses shared semantic-search retrieval and
  model-planned focus queries before final ontology synthesis.
- Direct data loading is acceptable for small samples, while retrieval is the
  intended path for larger files or many files.
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
  `http://example.org/semantic-web/graph/ontology`
- Verify ontology implementation with a named-graph SPARQL query against the
  ontology graph, not only by checking that `db/ontology.ttl` exists.

### Future Scale-Up Requirements

- Retrieval support has been added to the designer and importer. Future work
  should validate it on larger and non-DnD datasets.
- The standalone `./tools/semantic-search` tool now supports markdown, text, and
  CSV in addition to PDF and HTML; the product workflows use the shared
  retrieval layer under `src/common/semantic_search.py`.
- Designer and importer workflow tools now retrieve relevant source/schema
  chunks instead of prompt-stuffing whole inputs when configured thresholds are
  exceeded.
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
- Historical lightweight test suite result:
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
- Historical designer output: `design.md`, `db/ontology.ttl`, and a named Fuseki graph.
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
- The latest clean iterative designer/importer end-to-end validation on
  2026-05-31 produced 148 ontology triples, 16 classes, 17 properties, 121
  instance triples, 269 combined triples, 269 Fuseki triples, and viewer
  answers for broad, follow-up, stateful, and reasoning questions. Turtle export
  parsed with rdflib, and `uv run pytest` reported 60 passed and 2 skipped.
- After adding progressive importer logging, `uv run pytest` reported 59 passed
  and 4 skipped without live Fuseki running.
- Non-DnD PDF end-to-end validation on 2026-06-01 succeeded. The current
  generated semantic web is based on `data/main.pdf`, not the older DnD sample:
  202 ontology triples, 108 instance triples, 310 combined/Fuseki triples,
  grounded viewer answers for distribution, theorem, and sample-mean questions,
  parsed Turtle export, and `uv run pytest` reported 63 passed and 2 skipped.
- CSV-aware end-to-end validation on 2026-06-01 succeeded. The current
  generated semantic web is based on semantic-web and ontology markdown files
  plus `data/commonly seen triplestores.csv`: 165 ontology triples, 16 RDFS
  classes, 21 RDF properties, 241 instance triples, 406 combined/Fuseki triples,
  11 triplestore instances, and 157 deterministic CSV triples from one
  validated CSV mapping. Viewer status, chat session creation, question
  answering about open-source triplestores and Apache Jena TDB APIs/protocols,
  and Turtle export passed. `uv run pytest` reported 72 passed and 2 skipped.
- Viewer follow-up fixes on 2026-06-01 added class-instance aggregate counts
  for class count questions, exact subject-label fact lookup for named entity
  questions, and stricter end-user answer phrasing that avoids implementation
  details unless explicitly requested. Manual API checks answered CSV-specific
  questions correctly: 11 triplestores, 4 open-source triplestores, Apache Jena
  TDB APIs, GraphDB maintainer/license, commercial-license triplestores, and
  Virtuoso's key feature. `uv run pytest` reported 74 passed and 2 skipped.
- Test/production mode switch was added on 2026-06-01. `SEMANTIC_WEB_MODE=test`
  remains the default compact workflow with `gpt-5-mini`. Setting
  `SEMANTIC_WEB_MODE=production` switches default model to `gpt-5.5`, uses the
  comprehensive designer prompt, raises retrieval/import budgets, lengthens the
  timeout, and relaxes the designer ontology triple limit. Explicit environment
  overrides still win in both modes. `uv run pytest` reported 78 passed and
  4 skipped.
- Fuseki-backed graph slicing was added on 2026-06-01. Importer schema prompt
  context can now be built from a Fuseki term index and targeted ontology
  `CONSTRUCT` slices instead of prompt-context retrieval depending on a full
  ontology Turtle serialization. Viewer semantic fact retrieval can now select
  relevant Fuseki terms first and then query facts around only those candidate
  terms. Local RDF chunking remains the fallback for offline and portable runs.
  `uv run pytest` reported 80 passed and 4 skipped.
- The baseline scale-up mechanism is in place through
  `SEMANTIC_WEB_MODE=production`: it switches the default model to `gpt-5.5`,
  uses the comprehensive designer prompt, raises retrieval and importer
  budgets, increases context limits, lengthens the timeout, and relaxes the
  ontology triple limit. Milestone 12 will use this mode for comparison.
- CSV datatype robustness was added on 2026-06-01. CSV profiles now include
  compatible datatype notes and warnings for risky columns such as identifiers,
  leading-zero values, and mixed numeric strings. Designer prompts now treat
  CSV profile datatypes as recommendations and prefer strings for uncertain
  columns. Deterministic CSV import now accepts safe datatype widening and can
  fall back to string literals when the ontology range permits it. `uv run
  pytest` reported 83 passed and 4 skipped.
- Viewer semantic class matching was added on 2026-06-01. Before final answer
  generation, the viewer can ask the model to map user wording to class labels
  from the graph summary when lexical matching misses designer-generated class
  names. Matched classes are then queried for instance counts and facts. `uv
  run pytest` reported 84 passed and 4 skipped.
- Current-dataset production end-to-end validation succeeded on 2026-06-01
  after deleting `design.md`, `import.md`, and all files under `db/`.
  `SEMANTIC_WEB_MODE=production` used `gpt-5.5`, the comprehensive designer
  prompt, larger context limits, and production retrieval/import budgets. The
  first production designer attempt returned long non-JSON output; a JSON
  repair fallback was added and tested, after which the designer produced 541
  ontology triples, 94 RDFS classes, and 30 RDF properties. The importer
  inspected ontology terms from Fuseki, retried CSV mapping once after range
  validation feedback, produced 480 instance triples, and wrote 1,021 combined
  triples. Deterministic CSV import produced 77 triples from one validated CSV
  mapping. Viewer status reported 1,021 Fuseki triples, Turtle export parsed
  with 1,021 triples, and the viewer answered that 11 triplestores are listed,
  naming examples including AllegroGraph, Amazon Neptune, Apache Jena TDB,
  Blazegraph, GraphDB, Stardog, and Virtuoso. `uv run pytest` reported 87
  passed and 2 skipped. Note: `gpt-5.5` was capable of richer ontology output
  but less reliable at strict JSON formatting, so production mode now includes
  a designer JSON repair fallback; future production comparisons may still
  evaluate explicit `LLM_MODEL` overrides for structured-output reliability.
- The designer milestone commit has been made.
- The importer milestone commit has been made.
- The viewer milestone commit has been made.

### Immediate Next Step

- Start `Milestone 12: New CSV Example Mode Comparison`, then continue to
  `Milestone 13: README Setup And Run Guide`.

## Handoff For Next Codex Instance

- Start by reading `AGENTS.md`, `README.md`, and this file.
- The semantic web designer is complete and committed.
- The semantic web importer is complete and committed.
- Current generated outputs are:
  - `design.md`
  - `import.md`
  - `db/ontology.ttl`
  - `db/instances.ttl`
  - `db/semantic_web.ttl`
  - Fuseki ontology graph `http://example.org/semantic-web/graph/ontology`
  - Fuseki data graph `http://example.org/semantic-web/graph/data` unless overridden by `.env`
- Current tests:
  - `uv run pytest`
  - latest local result after current-dataset production validation:
    `87 passed, 2 skipped`
- Current runtime notes:
  - Fuseki may already be running on port `3030`.
  - If not, use the project-local Fuseki base `db/fuseki-run`.
  - Persistent Fuseki data is stored in `db/fuseki-data`.
  - Do not use `/opt/apache-jena-fuseki-6.1.0/run` as the runtime base.
  - Use SPARQL `ASK` via `POST` for readiness checks.
- Current development boundary:
  - Designer, importer, and viewer milestones are implemented.
  - Designer uses iterative model-planned semantic-search focuses for large
    data.
  - `SEMANTIC_WEB_MODE=test` is the default compact workflow. Set
    `SEMANTIC_WEB_MODE=production` in `.env` to use comprehensive designer
    prompts, `gpt-5.5` by default, larger retrieval/import budgets, and a
    relaxed ontology triple limit.
  - Importer uses iterative model-planned import batches for large data and
    writes progressive run status to `import.md`.
  - Importer uses deterministic CSV import for CSV sources: profile the CSV,
    plan a constrained mapping JSON, validate the mapping, loop over every row
    in Python, and merge those triples with unstructured-source imports.
  - The viewer uses Fuseki as its runtime data source and does not read
    `db/semantic_web.ttl` directly.
  - The viewer now uses exact subject-label lookup, class-instance aggregate
    counts, and LLM-assisted semantic class matching before generic relevance
    search, and its answer prompt is tuned for end-user wording rather than
    database or RDF implementation wording.
  - The next implementation priority is validating a new CSV-containing example
    in both test and production modes, then improving README setup/run
    instructions for users without a vibe coding agent.
  - The current semantic-web/ontology/triplestore graph validates the
    CSV-aware architecture, while unstructured markdown/PDF extraction remains
    compact and should be expanded through the long-document coverage milestone.
