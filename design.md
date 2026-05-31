# Semantic Web Schema — design.md

## Purpose and scope

This small RDF/RDFS schema is a compact, practical starting ontology for the supplied project: two introductory documents about the semantic web/ontology and a CSV listing commonly seen triplestores and their features. The goal is to capture the core conceptual vocabulary needed to:

- represent basic ontology and dataset concepts described in the documents (resources, agents, concepts, simple food example used in the docs), and
- represent triplestore metadata (name, open-source flag, protocols, APIs, license, features, reasoning support) so the CSV can be imported into a Fuseki dataset and queried.

We intentionally keep the model lightweight, RDFS-only (no OWL), and practical for import into Apache Jena Fuseki. The schema is compact and designed to be extended later.

## Modeling decisions (summary)

- Use RDFS classes and properties only; avoid OWL constructs. This maximizes compatibility with many triplestores and keeps the schema simple.
- Represent triplestores as a subclass of Software and model their characteristics (supportsSPARQL, isOpenSource, supportsProtocol, exposesAPI, license, hasFeature, supportsReasoning, homepage, vendor, supportsTransactions, storageType). Features, Protocol, API, and License are modeled as simple resource classes so CSV columns that enumerate features or protocols can be linked to per-triplestore feature nodes.
- Keep a shallow taxonomy extracted from the documents: core modeling concepts (Resource, Agent, Dataset, Ontology, Concept) plus the illustrative food example (Dish, FoodItem, Meat, VegetarianDish) and software/triplestore concepts (Software, Triplestore). This follows the documents' examples and the CSV focus.
- Prefer broad reusable properties (sw:creator, sw:createdDate, sw:prefLabel, sw:hasConcept) over many tiny one-off predicates. Use sw:hasFeature to attach arbitrary feature nodes to triplestores.
- Provide rdfs:label/rdfs:comment on important classes and properties to aid human understanding and UI tooling.

## Classes (what they mean)

- sw:Resource — Generic information resource. Base class for datasets, software, etc.
- sw:Agent — Actor/agent (people or organizations).
- sw:Person — Person; subclass of Agent. (Reflects FOAF-like usage in the docs.)
- sw:Dataset — A collection of RDF data; subclass of Resource.
- sw:Ontology — An ontology or schema document; subclass of Dataset.
- sw:Concept — A conceptual term usable in taxonomies (SKOS-style concept); subclass of Resource.
- sw:Software — Software artifact; subclass of Resource.
- sw:Triplestore — RDF database / triplestore; subclass of Software.
- sw:Feature — Named feature or capability (string-labeled node).
- sw:Protocol — Protocol used to access the triplestore (e.g., HTTP, SPARQL protocol).
- sw:API — API exposed by the triplestore (e.g., REST, GraphQL wrapper).
- sw:License — License resource (e.g., "Apache-2.0").
- sw:Dish, sw:FoodItem, sw:Meat, sw:VegetarianDish — small illustrative food modeling taken from the docs to keep example vocabulary for import/education.

(There are 16 classes in this first version; they are intentionally broad so they can be reused.)

## Properties (core predicates and their domain/range)

All properties are plain RDF properties (rdf:Property) with rdfs:domain and rdfs:range where practical.

- sw:hasIngredient
  - domain: sw:Dish
  - range: sw:FoodItem
  - comment: links a Dish to FoodItems it contains (object property equivalent).

- sw:hasComponent
  - domain: sw:Dish
  - range: sw:FoodItem
  - comment: alternate/aliased predicate for ingredient lists; declared a subPropertyOf sw:hasIngredient to normalize ingestion.

- sw:creator
  - domain: sw:Resource
  - range: sw:Agent
  - comment: who created the resource (maps to dcterms:creator in origin docs).

- sw:publisher
  - domain: sw:Resource
  - range: sw:Agent
  - comment: publisher or distributing agent.

- sw:createdDate
  - domain: sw:Resource
  - range: xsd:date
  - comment: creation date; map CSV/metadata date columns here.

- sw:format
  - domain: sw:Resource
  - range: xsd:string
  - comment: textual format label (e.g., "Turtle", "JSON-LD").

- sw:prefLabel
  - domain: sw:Resource
  - range: xsd:string
  - comment: human-readable preferred label (skos:prefLabel-like convenience predicate).

- sw:hasConcept
  - domain: sw:Ontology
  - range: sw:Concept
  - comment: links an ontology to the concepts it defines.

- sw:broader
  - domain: sw:Concept
  - range: sw:Concept
  - comment: lightweight taxonomy relation (skos:broader style).

- sw:hasFeature
  - domain: sw:Triplestore
  - range: sw:Feature
  - comment: attach Feature nodes describing capabilities enumerated in the CSV.

- sw:featureName
  - domain: sw:Feature
  - range: xsd:string
  - comment: short name of the feature as string.

- sw:supportsSPARQL
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the store supports SPARQL query endpoint.

- sw:isOpenSource
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the product is open-source.

- sw:exposesAPI
  - domain: sw:Triplestore
  - range: sw:API
  - comment: link to API type nodes.

- sw:supportsProtocol
  - domain: sw:Triplestore
  - range: sw:Protocol
  - comment: protocol(s) supported (e.g., HTTP, SPARQL Protocol).

- sw:license
  - domain: sw:Triplestore
  - range: sw:License
  - comment: license node for the triplestore.

- sw:supportsReasoning
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the triplestore advertises built-in reasoning or inference support.

- sw:homepage
  - domain: sw:Triplestore
  - range: xsd:anyURI
  - comment: vendor or product homepage.

- sw:vendor
  - domain: sw:Triplestore
  - range: xsd:string
  - comment: vendor or organization name.

- sw:supportsTransactions
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the store supports transactional updates.

- sw:storageType
  - domain: sw:Triplestore
  - range: xsd:string
  - comment: textual label describing storage/persistence (e.g., "native", "federated").

(There are 20 properties in this version — broad, reusable, and closely aligned with the CSV columns.)

## Mapping CSV -> RDF guidance (practical)

When importing the triplestore CSV into Fuseki, map columns as follows (recommended):

- name -> rdfs:label or sw:prefLabel (create a sw:Triplestore resource per row)
- open_source -> sw:isOpenSource (xsd:boolean)
- supports_sparql -> sw:supportsSPARQL (xsd:boolean)
- api -> create or reuse sw:API nodes and link with sw:exposesAPI
- protocol -> create or reuse sw:Protocol nodes and link with sw:supportsProtocol
- license -> create sw:License node and link with sw:license
- features -> for each listed feature, create sw:Feature node (sw:featureName) and link with sw:hasFeature
- vendor -> sw:vendor (xsd:string)
- homepage -> sw:homepage (xsd:anyURI)
- supports_reasoning -> sw:supportsReasoning (xsd:boolean)
- supports_transactions -> sw:supportsTransactions (xsd:boolean)
- storage_type -> sw:storageType (xsd:string)

Prefer creating small URI-bearing nodes for Protocol/API/Feature/License so you can attach labels and later reconcile duplicates. Use a consistent URI pattern (for example: http://example.org/triplestore/feature/FeatureName) during import.

## Import notes for Apache Jena Fuseki

- Load the Turtle schema (this ontology) into a dedicated graph in Fuseki (e.g., `http://localhost:3030/dataset/data`) before or along with instance data so client tools can pick up rdfs:domain/range annotations.
- Convert the CSV into RDF (one triplestore resource per CSV row) using simple mapping tools (e.g., rdf-csv, custom Python script, or SPARQL INSERTs). Ensure boolean columns become xsd:boolean and dates xsd:date.
- If you need RDFS-based inference (e.g., to infer class membership from rdfs:domain), use Fuseki with TDB and enable the RDFS reasoner when running queries, or materialize domain/range typing during import (preferred for simple deployments).
- Keep instance URIs stable and dereferenceable when possible (use vendor or canonical product slugs).

## Extensibility

- This schema is intentionally minimal. Later versions can add more detail (e.g., separate properties for read/write endpoints, detailed API capability descriptors, SKOS integration for richer taxonomy modeling, or OWL axioms for intensional classes like VegetarianDish). For now, RDFS suffices for labeling, basic domain/range guidance, and SPARQL querying in Fuseki.

## Example queries you will be able to run after import

- List triplestores that are open source and support SPARQL:
  SELECT ?ts WHERE { ?ts a sw:Triplestore ; sw:isOpenSource true ; sw:supportsSPARQL true . }

- Find all features of a given triplestore:
  SELECT ?fname WHERE { ?ts a sw:Triplestore ; sw:hasFeature ?f . ?f sw:featureName ?fname . }

- List Ontologies and the Concepts they declare:
  SELECT ?ont ?c WHERE { ?ont a sw:Ontology ; sw:hasConcept ?c . }


---

This document and the accompanying Turtle provide a compact, usable starting point for the project's semantic schema. The schema models the core concepts mentioned in the supplied documents and the typical triplestore attributes in the CSV while remaining small and easy to import into Fuseki.

## Designer Generation Log

## Retrieval Focus Planning

- Status: LLM request started
- Timestamp: 2026-05-31T22:26:46+00:00
- Max focuses: 4

## Retrieval Focus Planning Result

- Status: passed
- Focus count: 4
- Query: Extract candidate classes, class labels, short definitions, and explicit subClassOf (hierarchy) statements from ontology.md
- Query: Find predicates/properties, their described semantics, intended domain and range, property types (object vs. datatype), and any logical axioms or constraints across ontology.md and semantic web.md
- Query: List RDF/RDFS constructs, example triple patterns, recommended serialization formats (e.g., Turtle, RDF/XML, JSON-LD), and common modeling patterns or best practices from semantic web.md
- Query: From commonly seen triplestores.csv, enumerate each triplestore name with developer/maintainer, license type, primary APIs/interfaces, and key features (reasoning, protocols, open-source status)

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T22:26:59+00:00
- Query: Extract candidate classes, class labels, short definitions, and explicit subClassOf (hierarchy) statements from ontology.md
- Context characters: 1684

## Schema Slice Draft Result

- Status: passed
- Query: Extract candidate classes, class labels, short definitions, and explicit subClassOf (hierarchy) statements from ontology.md
- Notes characters: 5885

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T22:27:31+00:00
- Query: Find predicates/properties, their described semantics, intended domain and range, property types (object vs. datatype), and any logical axioms or constraints across ontology.md and semantic web.md
- Context characters: 4928

## Schema Slice Draft Result

- Status: passed
- Query: Find predicates/properties, their described semantics, intended domain and range, property types (object vs. datatype), and any logical axioms or constraints across ontology.md and semantic web.md
- Notes characters: 8275

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T22:28:05+00:00
- Query: List RDF/RDFS constructs, example triple patterns, recommended serialization formats (e.g., Turtle, RDF/XML, JSON-LD), and common modeling patterns or best practices from semantic web.md
- Context characters: 3516

## Schema Slice Draft Result

- Status: passed
- Query: List RDF/RDFS constructs, example triple patterns, recommended serialization formats (e.g., Turtle, RDF/XML, JSON-LD), and common modeling patterns or best practices from semantic web.md
- Notes characters: 5939

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T22:28:38+00:00
- Query: From commonly seen triplestores.csv, enumerate each triplestore name with developer/maintainer, license type, primary APIs/interfaces, and key features (reasoning, protocols, open-source status)
- Context characters: 4261

## Schema Slice Draft Result

- Status: passed
- Query: From commonly seen triplestores.csv, enumerate each triplestore name with developer/maintainer, license type, primary APIs/interfaces, and key features (reasoning, protocols, open-source status)
- Notes characters: 8212

# Semantic Web Designer Progress

- Model: `gpt-5-mini`
- Max attempts: 2
- Started: 2026-05-31T22:29:17+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-05-31T22:29:17+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-05-31T22:30:21+00:00
- Response characters: 14752

## Attempt 1 Validation

- Status: failed
- Feedback: Attempt 1 failed: ValueError: Ontology must define at least one rdf:Property.

## Attempt 2

- Status: LLM request started
- Timestamp: 2026-05-31T22:30:21+00:00
- Retry feedback included: yes

## Attempt 2 Response

- Status: LLM response received
- Timestamp: 2026-05-31T22:31:41+00:00
- Response characters: 16413

## Attempt 2 Validation

- Status: passed
- Triple count: 165

### Candidate Design

# Semantic Web Schema — design.md

## Purpose and scope

This small RDF/RDFS schema is a compact, practical starting ontology for the supplied project: two introductory documents about the semantic web/ontology and a CSV listing commonly seen triplestores and their features. The goal is to capture the core conceptual vocabulary needed to:

- represent basic ontology and dataset concepts described in the documents (resources, agents, concepts, simple food example used in the docs), and
- represent triplestore metadata (name, open-source flag, protocols, APIs, license, features, reasoning support) so the CSV can be imported into a Fuseki dataset and queried.

We intentionally keep the model lightweight, RDFS-only (no OWL), and practical for import into Apache Jena Fuseki. The schema is compact and designed to be extended later.

## Modeling decisions (summary)

- Use RDFS classes and properties only; avoid OWL constructs. This maximizes compatibility with many triplestores and keeps the schema simple.
- Represent triplestores as a subclass of Software and model their characteristics (supportsSPARQL, isOpenSource, supportsProtocol, exposesAPI, license, hasFeature, supportsReasoning, homepage, vendor, supportsTransactions, storageType). Features, Protocol, API, and License are modeled as simple resource classes so CSV columns that enumerate features or protocols can be linked to per-triplestore feature nodes.
- Keep a shallow taxonomy extracted from the documents: core modeling concepts (Resource, Agent, Dataset, Ontology, Concept) plus the illustrative food example (Dish, FoodItem, Meat, VegetarianDish) and software/triplestore concepts (Software, Triplestore). This follows the documents' examples and the CSV focus.
- Prefer broad reusable properties (sw:creator, sw:createdDate, sw:prefLabel, sw:hasConcept) over many tiny one-off predicates. Use sw:hasFeature to attach arbitrary feature nodes to triplestores.
- Provide rdfs:label/rdfs:comment on important classes and properties to aid human understanding and UI tooling.

## Classes (what they mean)

- sw:Resource — Generic information resource. Base class for datasets, software, etc.
- sw:Agent — Actor/agent (people or organizations).
- sw:Person — Person; subclass of Agent. (Reflects FOAF-like usage in the docs.)
- sw:Dataset — A collection of RDF data; subclass of Resource.
- sw:Ontology — An ontology or schema document; subclass of Dataset.
- sw:Concept — A conceptual term usable in taxonomies (SKOS-style concept); subclass of Resource.
- sw:Software — Software artifact; subclass of Resource.
- sw:Triplestore — RDF database / triplestore; subclass of Software.
- sw:Feature — Named feature or capability (string-labeled node).
- sw:Protocol — Protocol used to access the triplestore (e.g., HTTP, SPARQL protocol).
- sw:API — API exposed by the triplestore (e.g., REST, GraphQL wrapper).
- sw:License — License resource (e.g., "Apache-2.0").
- sw:Dish, sw:FoodItem, sw:Meat, sw:VegetarianDish — small illustrative food modeling taken from the docs to keep example vocabulary for import/education.

(There are 16 classes in this first version; they are intentionally broad so they can be reused.)

## Properties (core predicates and their domain/range)

All properties are plain RDF properties (rdf:Property) with rdfs:domain and rdfs:range where practical.

- sw:hasIngredient
  - domain: sw:Dish
  - range: sw:FoodItem
  - comment: links a Dish to FoodItems it contains (object property equivalent).

- sw:hasComponent
  - domain: sw:Dish
  - range: sw:FoodItem
  - comment: alternate/aliased predicate for ingredient lists; declared a subPropertyOf sw:hasIngredient to normalize ingestion.

- sw:creator
  - domain: sw:Resource
  - range: sw:Agent
  - comment: who created the resource (maps to dcterms:creator in origin docs).

- sw:publisher
  - domain: sw:Resource
  - range: sw:Agent
  - comment: publisher or distributing agent.

- sw:createdDate
  - domain: sw:Resource
  - range: xsd:date
  - comment: creation date; map CSV/metadata date columns here.

- sw:format
  - domain: sw:Resource
  - range: xsd:string
  - comment: textual format label (e.g., "Turtle", "JSON-LD").

- sw:prefLabel
  - domain: sw:Resource
  - range: xsd:string
  - comment: human-readable preferred label (skos:prefLabel-like convenience predicate).

- sw:hasConcept
  - domain: sw:Ontology
  - range: sw:Concept
  - comment: links an ontology to the concepts it defines.

- sw:broader
  - domain: sw:Concept
  - range: sw:Concept
  - comment: lightweight taxonomy relation (skos:broader style).

- sw:hasFeature
  - domain: sw:Triplestore
  - range: sw:Feature
  - comment: attach Feature nodes describing capabilities enumerated in the CSV.

- sw:featureName
  - domain: sw:Feature
  - range: xsd:string
  - comment: short name of the feature as string.

- sw:supportsSPARQL
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the store supports SPARQL query endpoint.

- sw:isOpenSource
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the product is open-source.

- sw:exposesAPI
  - domain: sw:Triplestore
  - range: sw:API
  - comment: link to API type nodes.

- sw:supportsProtocol
  - domain: sw:Triplestore
  - range: sw:Protocol
  - comment: protocol(s) supported (e.g., HTTP, SPARQL Protocol).

- sw:license
  - domain: sw:Triplestore
  - range: sw:License
  - comment: license node for the triplestore.

- sw:supportsReasoning
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the triplestore advertises built-in reasoning or inference support.

- sw:homepage
  - domain: sw:Triplestore
  - range: xsd:anyURI
  - comment: vendor or product homepage.

- sw:vendor
  - domain: sw:Triplestore
  - range: xsd:string
  - comment: vendor or organization name.

- sw:supportsTransactions
  - domain: sw:Triplestore
  - range: xsd:boolean
  - comment: whether the store supports transactional updates.

- sw:storageType
  - domain: sw:Triplestore
  - range: xsd:string
  - comment: textual label describing storage/persistence (e.g., "native", "federated").

(There are 20 properties in this version — broad, reusable, and closely aligned with the CSV columns.)

## Mapping CSV -> RDF guidance (practical)

When importing the triplestore CSV into Fuseki, map columns as follows (recommended):

- name -> rdfs:label or sw:prefLabel (create a sw:Triplestore resource per row)
- open_source -> sw:isOpenSource (xsd:boolean)
- supports_sparql -> sw:supportsSPARQL (xsd:boolean)
- api -> create or reuse sw:API nodes and link with sw:exposesAPI
- protocol -> create or reuse sw:Protocol nodes and link with sw:supportsProtocol
- license -> create sw:License node and link with sw:license
- features -> for each listed feature, create sw:Feature node (sw:featureName) and link with sw:hasFeature
- vendor -> sw:vendor (xsd:string)
- homepage -> sw:homepage (xsd:anyURI)
- supports_reasoning -> sw:supportsReasoning (xsd:boolean)
- supports_transactions -> sw:supportsTransactions (xsd:boolean)
- storage_type -> sw:storageType (xsd:string)

Prefer creating small URI-bearing nodes for Protocol/API/Feature/License so you can attach labels and later reconcile duplicates. Use a consistent URI pattern (for example: http://example.org/triplestore/feature/FeatureName) during import.

## Import notes for Apache Jena Fuseki

- Load the Turtle schema (this ontology) into a dedicated graph in Fuseki (e.g., `http://localhost:3030/dataset/data`) before or along with instance data so client tools can pick up rdfs:domain/range annotations.
- Convert the CSV into RDF (one triplestore resource per CSV row) using simple mapping tools (e.g., rdf-csv, custom Python script, or SPARQL INSERTs). Ensure boolean columns become xsd:boolean and dates xsd:date.
- If you need RDFS-based inference (e.g., to infer class membership from rdfs:domain), use Fuseki with TDB and enable the RDFS reasoner when running queries, or materialize domain/range typing during import (preferred for simple deployments).
- Keep instance URIs stable and dereferenceable when possible (use vendor or canonical product slugs).

## Extensibility

- This schema is intentionally minimal. Later versions can add more detail (e.g., separate properties for read/write endpoints, detailed API capability descriptors, SKOS integration for richer taxonomy modeling, or OWL axioms for intensional classes like VegetarianDish). For now, RDFS suffices for labeling, basic domain/range guidance, and SPARQL querying in Fuseki.

## Example queries you will be able to run after import

- List triplestores that are open source and support SPARQL:
  SELECT ?ts WHERE { ?ts a sw:Triplestore ; sw:isOpenSource true ; sw:supportsSPARQL true . }

- Find all features of a given triplestore:
  SELECT ?fname WHERE { ?ts a sw:Triplestore ; sw:hasFeature ?f . ?f sw:featureName ?fname . }

- List Ontologies and the Concepts they declare:
  SELECT ?ont ?c WHERE { ?ont a sw:Ontology ; sw:hasConcept ?c . }


---

This document and the accompanying Turtle provide a compact, usable starting point for the project's semantic schema. The schema models the core concepts mentioned in the supplied documents and the typical triplestore attributes in the CSV while remaining small and easy to import into Fuseki.

