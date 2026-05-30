# Semantic Web Processor

This project builds a semantic web from local structured and unstructured data,
stores it in Apache Jena Fuseki, and will provide an agentic importer and
browser-based viewer.

The current implemented milestone is the semantic web designer.

## Current Handoff State

- The semantic web designer milestone is complete, tested, documented, and
  committed.
- The importer has not been started.
- The viewer has not been started.
- Before starting importer work, confirm with the user.
- The next implementation milestone is `Milestone 2: Importer Framework` in
  `PROGRESS.md`.
- Do not manually change the ontology to make importer work easier. The importer
  must fit instances into the existing designer output unless the user approves
  a new designer run.

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

## Fuseki Usage Notes

Apache Jena Fuseki is installed at `/opt/apache-jena-fuseki-6.1.0`, but the
project should not use the default Fuseki runtime base under that installation
directory. The default base is `/opt/apache-jena-fuseki-6.1.0/run`, which may
not be writable by the project user.

Use a project-local Fuseki base instead:

```text
FUSEKI_BASE=db/fuseki-run
```

The designer sets this automatically through `src/common/fuseki_manager.py`.
Fuseki logs are written to:

```text
db/fuseki.log
```

The working command pattern is:

```bash
FUSEKI_BASE=/home/sunlu/Projects/semantic-web-processor/db/fuseki-run \
  /opt/apache-jena-fuseki-6.1.0/fuseki-server \
  --mem --update --localhost /semantic-web-processor
```

Important details:

- Use `--update`, otherwise graph loading and SPARQL updates may not work.
- Use `--localhost` for local development.
- Do not rely on `GET /semantic-web-processor/query` as a readiness check.
- Use a SPARQL `ASK` query through `POST` to check readiness.
- Load ontology data through the graph store endpoint.
- Query named graphs through SPARQL after loading.

The designer uses these endpoints by default:

```text
Query endpoint: http://localhost:3030/semantic-web-processor/query
Update endpoint: http://localhost:3030/semantic-web-processor/update
Graph store endpoint: http://localhost:3030/semantic-web-processor/data
Ontology graph: http://example.org/dnd-adventure/graph/ontology
```

Useful verification query:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class WHERE {
  GRAPH <http://example.org/dnd-adventure/graph/ontology> {
    ?class a rdfs:Class .
  }
}
ORDER BY ?class
```

Troubleshooting:

- If Fuseki exits with a writable-directory error, confirm `FUSEKI_BASE` points
  to `db/fuseki-run` or another writable directory.
- If Fuseki reports port `3030` is already bound, check for stale Fuseki
  processes with `pgrep -af fuseki`.
- If a browser or `curl` can reach the root UI but the query endpoint looks odd,
  test readiness with a SPARQL `ASK` POST instead of a GET request.
- If graph loading appears to fall back to file mode, check `db/fuseki.log` and
  confirm the dataset path is `/semantic-web-processor`.

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

Before starting importer work, pause and ask the user for approval.
