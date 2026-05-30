# Semantic Web Processor

This project builds a semantic web from local structured and unstructured data,
stores it in Apache Jena Fuseki, and will provide an agentic importer and
browser-based viewer.

The current implemented milestone is the semantic web designer.

## Components

- `src/designer`: OpenAI Agents SDK workflow for semantic web design and Jena
  implementation.
- `src/importer`: planned OpenAI Agents SDK workflow for inserting instances.
- `src/viewer`: planned browser chatbot and export UI.
- `src/common`: shared configuration, RDF, Fuseki, file, and LLM utilities.

## Semantic Web Designer

The designer is intentionally simple in the first working version. It designs a
small RDF/RDFS ontology for the DnD adventure data, validates it, writes review
artifacts, and loads the ontology into Apache Jena Fuseki.

The designer workflow performs these steps:

1. Check whether Fuseki is reachable.
2. Start Fuseki if needed, using a project-local writable runtime directory.
3. Read `design-requirements.md` and files under `data/`.
4. Use a direct OpenAI API call to generate a simple RDF/RDFS design.
5. Validate the generated Turtle with `rdflib` and project-specific checks.
6. Retry with validation feedback when needed.
7. Write `design.md`.
8. Write `db/ontology.ttl` as an intermediate review and loading artifact.
9. Load the ontology into Fuseki as the named graph
   `http://example.org/dnd-adventure/graph/ontology`.

Turtle is not the final implementation target. It is used as a testable
serialization layer and fallback. The intended runtime target is Apache Jena
Fuseki.

## Configuration

Configuration is read from `.env` and defaults in `src/common/config.py`.

Important settings:

- `OPENAI_API_KEY`: required for the designer model call.
- `LLM_MODEL`: defaults to `gpt-5.5`.
- `LLM_TIMEOUT_SECONDS`: defaults to `90`.
- `DESIGNER_ITERATIONS`: defaults to `2`.
- `FUSEKI_BASE_URL`: defaults to `http://localhost:3030`.
- `FUSEKI_DATASET`: defaults to `semantic-web-processor`.
- `FUSEKI_HOME`: defaults to `/opt/apache-jena-fuseki-6.1.0`.

Fuseki runtime files are written under `db/fuseki-run/`, and Fuseki logs are
written to `db/fuseki.log`. These local runtime files are ignored by git.

## Usage

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

Expected designer outputs:

- `design.md`: human-readable ontology design document.
- `db/ontology.ttl`: validated intermediate Turtle ontology.
- Fuseki named graph: `http://example.org/dnd-adventure/graph/ontology`.

## Current Designer Result

The current generated DnD ontology is deliberately small:

- 224 RDF triples.
- 15 RDFS classes.
- 35 RDF properties.
- RDF validation passed.
- Fuseki SPARQL query returned 15 ontology classes from the named ontology graph.

## Next Milestones

- Implement the importer workflow to read `design.md`, inspect the ontology, and
  insert adventure instance data without changing the schema.
- Implement the viewer workflow and browser UI to query the semantic web and
  export it from Fuseki.
