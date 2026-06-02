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
- [x] Preserve or document how to restore the current PDF proof-of-concept
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

- [x] Prepare a new example dataset under `data/*` with at least one CSV file
  and matching `design-requirements.md`. The example should be unrelated to
  the current semantic-web/ontology/triplestore data and unrelated to older DnD
  or probability/PDF examples.
- [x] Preserve or document how to restore the current CSV-aware example if
  needed.
- [x] Run a clean end-to-end test in default test mode:
  `SEMANTIC_WEB_MODE=test` or unset, delete generated outputs, run designer,
  run importer, start viewer, ask representative questions, verify Turtle
  export parses, and run `uv run pytest`.
- [x] Record test-mode output metrics: model, designer focus count, ontology
  triples/classes/properties, CSV mapping count, deterministic CSV triples,
  total instance triples, combined triples, viewer answers, export parse count,
  runtime notes, and any weak answers.
- [x] Run a clean end-to-end test in production mode:
  `SEMANTIC_WEB_MODE=production`, delete generated outputs, run designer,
  run importer, start viewer, ask the same representative questions, verify
  Turtle export parses, and run `uv run pytest`.
- [x] Record production-mode output metrics with the same fields as test mode.
- [x] Compare test and production mode outputs for schema richness, instance
  coverage, CSV mapping fidelity, viewer answer quality, runtime, cost/risk,
  and validation failures or retries.
- [x] Decide whether production defaults need adjustment before long-document
  scale-up.
- [x] Update `README.md`, `PROGRESS.md`, and `AGENTS.md` with the validation
  result and mode comparison.
- [x] Commit the new CSV example mode comparison milestone.

## Milestone 13: README Setup And Run Guide

Goal: rewrite or substantially improve `README.md` so a user can set up and
run the application end to end on a machine without a vibe coding agent and
possibly without preliminary installations.

- [x] Document prerequisites clearly: supported Python version, `uv`, git,
  Apache Jena Fuseki, Java requirements for Fuseki, OpenAI API key, and network
  access expectations.
- [x] Document first-time setup from a fresh clone: dependency installation,
  `.env` creation, API key configuration, Fuseki location/configuration, and
  writable project-local Fuseki runtime/storage directories.
- [x] Document `.env` settings in practical groups: OpenAI/model settings,
  test/production mode, retrieval limits, designer/importer iterations, Fuseki
  endpoints and graph URIs, viewer host/port, and semantic-search provider.
- [x] Explain test mode versus production mode, including default model,
  prompt behavior, retrieval/batch budgets, ontology triple limits, expected
  runtime/cost tradeoffs, and how explicit overrides work.
- [x] Document how to replace `design-requirements.md` and `data/*` with a new
  dataset, including CSV, markdown/text, and PDF inputs.
- [x] Document clean end-to-end run commands: stop stale Fuseki, remove
  generated outputs, run designer, run importer, start viewer, ask questions,
  export Turtle, and run tests.
- [x] Document troubleshooting for common failures: missing API key, unknown
  model, Fuseki port already bound, unwritable Fuseki base, graph load fallback,
  bad Turtle, invalid CSV mapping, viewer showing missing facts, and export
  parse failure.
- [x] Document expected generated artifacts and which ones are runtime source
  of truth versus review/export/fallback files.
- [x] Add a concise quick-start path and a more detailed setup/reference path.
- [x] Run documentation sanity checks and `uv run pytest`.
- [x] Commit the README setup/run guide update.

## Milestone 14: Long-Document Coverage Completion

Goal: move beyond proof-of-concept semantic webs for long source documents by
improving coverage tracking, source structure extraction, and refinement loops
while keeping Fuseki as the runtime source of truth. The baseline scale-up
mechanism is already complete through production mode, larger budgets,
comprehensive prompts, Fuseki-backed graph slicing, and JSON repair. This
milestone tracks only the remaining long-document coverage work.

- [ ] Add a coverage ledger for designer/importer runs that records source
  chapters, sections, page ranges, formulas, tables, code examples, tools,
  named concepts, and imported graph areas.
- [ ] Improve PDF preprocessing into section-aware chunks using extracted
  headings, table-of-contents structure, page numbers, formulas, tables, figure
  captions, and code blocks where available.
- [ ] Add ontology refinement passes that review uncovered evidence and propose
  schema additions only when the existing ontology cannot represent important
  content.
- [ ] Add importer continuation passes that resume from existing Fuseki data,
  avoid duplicates, and import uncovered sections until coverage is complete or
  a configured budget is reached.
- [ ] Add viewer or script-based coverage reports that summarize what the graph
  covers and what source areas remain missing.
- [ ] Validate long-document coverage improvements on a representative PDF
  dataset, such as a restored `data/main.pdf`, and compare graph coverage
  against the earlier proof-of-concept result.
- [ ] Run `uv run pytest`.
- [ ] Update `README.md` and `PROGRESS.md` with the long-document coverage
  validation result.
- [ ] Commit the long-document coverage milestone.

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
`SEMANTIC_WEB_MODE=production` and record the current production baseline.

- [x] Run the semantic web designer in production mode.
- [x] Run the semantic web importer in production mode.
- [x] Start or verify Fuseki against the persistent project-local TDB2 data.
- [x] Verify viewer status and Turtle export from Fuseki.
- [x] Ask a representative viewer question through the viewer workflow/API.
- [x] Run `uv run pytest`.
- [x] Record production-mode metrics and findings in `PROGRESS.md`.
- [x] Commit the current-dataset production validation.

## Current Status

- The designer, importer, and viewer are implemented, tested, documented, and
  committed.
- Fuseki is the runtime source of truth between applications. Turtle files
  remain validation, review, export, portability, and fallback artifacts.
- `design.md` is a human-readable design and importer reference, not the main
  machine-readable handoff when Fuseki is available.
- The active dataset is `data/semantic web.md`, `data/ontology.md`, and
  `data/commonly seen triplestores.csv`.
- The latest documented production validation used `SEMANTIC_WEB_MODE=production`
  and `gpt-5.5`, producing 541 ontology triples, 480 instance triples, and
  1,021 combined/export triples.
- The latest local test result is `uv run pytest`: 85 passed, 4 skipped.
- Recent documentation commits:
  - `3dff973 Improve project setup documentation`
  - `a4ef360 Document uv commands and framework packages`

## Active Plan

The next implementation work is `Milestone 14: Long-Document Coverage
Completion`.

Immediate priorities:

1. Add a designer/importer coverage ledger.
2. Improve PDF preprocessing into section-aware chunks.
3. Add ontology refinement and importer continuation passes.
4. Add coverage reports.
5. Validate on a representative long PDF dataset.

## Handoff For Next Coding Agent

Start by reading `AGENTS.md`, `README.md`, and this file.

Important runtime facts:

- Python dependencies are managed with `uv`.
- Run tests with `uv run pytest`.
- Fuseki may already be running on port `3030`.
- If Fuseki is not running, workflows use project-local runtime/storage:
  `db/fuseki-run`, `db/fuseki-data`, and `db/fuseki.log`.
- Do not use `/opt/apache-jena-fuseki-6.1.0/run` as this project's Fuseki base.
- Fuseki readiness should use SPARQL `ASK` through `POST`, not `GET` on the
  query endpoint.

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

Current behavior to preserve:

- Product code must remain domain-neutral.
- Designer uses OpenAI Agents SDK orchestration with direct OpenAI design calls,
  RDF validation, JSON repair fallback, progressive `design.md` logging, and
  Fuseki ontology loading.
- Importer uses Fuseki ontology inspection when available, `db/ontology.ttl`
  fallback, deterministic CSV import, retrieval-guided unstructured import, and
  progressive `import.md` logging.
- Viewer uses Fuseki at runtime and does not read `db/semantic_web.ttl`
  directly. It uses exact subject lookup, class counts, LLM-assisted class
  matching, and relevant fact retrieval before final answer generation.
- `SEMANTIC_WEB_MODE=test` is the default compact workflow. Production mode
  uses stronger defaults and larger budgets for richer runs.

Open item:

- Long unstructured markdown/PDF coverage is still proof-of-concept level.
  Milestone 14 should improve coverage tracking, PDF chunking, schema
  refinement, importer continuation, and coverage reporting.
