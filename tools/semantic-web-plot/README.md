Semantic Web Plot
=================

Interactive ontology graph generator for OWL/RDF Turtle files. The CLI reads
`semantic_web.ttl`, extracts meaningful semantic relationships, and writes a
self-contained pyvis/vis.js HTML graph to `output/ontology_graph.html`.

This tool is also importable from the main Vibe Semanting viewer. The
viewer exports Turtle from Fuseki at runtime, passes that Turtle to
`SemanticWebPlotter`, and serves the generated HTML from `/api/plot.html`.

Setup
-----

This project uses `uv` for dependency management.

```bash
uv sync
```

On networks with TLS inspection, use `uv --native-tls sync`.

Usage
-----

```bash
uv run python main.py
```

Useful options:

```bash
uv run python main.py --input semantic_web.ttl --output output/ontology_graph.html
uv run python main.py --max-edges 100
uv run python main.py --undirected
uv run python main.py --open-browser
```

The generated HTML file is self-contained and can be opened directly in a
browser.

Importable API
--------------

```python
from pathlib import Path

from semantic_web_plot import SemanticWebPlotter

html = SemanticWebPlotter().render_turtle_text(
    turtle,
    Path("output/ontology_graph.html"),
).html
```

What The Graph Shows
--------------------

The renderer interprets OWL/RDF patterns instead of dumping raw triples:

- Named `rdfs:subClassOf` relationships become dashed class hierarchy edges.
- Object properties with `rdfs:domain` and `rdfs:range` become semantic edges.
- `owl:unionOf` domains and restriction targets are expanded.
- OWL restrictions on `rdfs:subClassOf` become class-to-class property edges.
- Named individuals with class `rdf:type` declarations become instance edges.
- Datatype properties are shown in class node tooltips, not as graph nodes.

Testing
-------

```bash
uv run pytest -q
```
