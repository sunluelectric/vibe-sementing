# Semantic Web and Triplestore Ontology Design

## Purpose

This RDF/RDFS schema models the concepts introduced in the supplied Semantic Web and Ontology documents and provides an import-ready structure for the CSV of commonly seen triplestores. The ontology is designed for Apache Jena Fuseki and uses RDF/RDFS as the core representation, with limited OWL vocabulary for useful property semantics such as inverse and symmetric properties.

The schema does not include individual source rows. CSV rows such as GraphDB, Virtuoso, Blazegraph, and Amazon Neptune should be imported later as instances of `sw:Triplestore`.

## Namespace

Base namespace:

`http://example.org/semantic-web#`

Required prefixes are included in the ontology: `sw`, `rdf`, `rdfs`, and `xsd`. The ontology also includes the `owl` prefix for a small number of useful schema-level declarations.

## Main Modeling Areas

### 1. Semantic Web Concepts

The schema represents core concepts from the Semantic Web document, including:

- Web of Documents and Web of Data distinction.
- Resources, entities, documents, data resources, and web resources.
- RDF graphs, RDF triples, RDF terms, subjects, predicates, and objects.
- RDFS schemas and vocabularies.
- Semantic Web layers, including identifier, syntax, data model, ontology, query, logic, proof, and trust layers.
- Standards and technologies such as RDF, RDFS, OWL, SPARQL, SKOS, JSON-LD, Turtle, RDF/XML, URI, IRI, and Unicode as importable technology or standard resources.
- Semantic Web assumptions such as the Open World Assumption and Non-Unique Name Assumption.
- Linked Open Data, DBpedia/Wikidata-style hubs, Schema.org-style vocabularies, and enterprise knowledge graphs.

### 2. Ontology and Knowledge Representation Concepts

The schema models concepts from the ontology introduction, including:

- Ontology, taxonomy, and knowledge graph as related but distinct knowledge organization structures.
- Ontology components: classes, individuals, datatype properties, object properties, relationships, axioms, constraints, and rules.
- Logical profiles, including OWL profile concepts without enumerating specific instance facts.
- Reasoners and reasoning tasks, including classification and consistency checking.
- Foundational ontologies and reusable vocabularies.

### 3. Triplestore CSV Coverage

The CSV columns are represented directly with datatype properties for import fidelity:

| CSV column | Recommended ontology property | Range |
|---|---|---|
| Triplestore Name | `sw:triplestoreName` | `xsd:string` |
| Developer/Maintainer | `sw:developerMaintainerLiteral` | `xsd:string` |
| License Type | `sw:licenseTypeLiteral` | `xsd:string` |
| Primary API/Interfaces | `sw:primaryApiInterfacesLiteral` | `xsd:string` |
| Key Features/Specializations | `sw:keyFeaturesLiteral` | `xsd:string` |

All CSV-backed properties use `xsd:string` because the source profile shows mixed strings, names, codes, version-like values, and descriptive text. This preserves source values safely.

The ontology also supports normalized import when desired:

- `sw:developedBy` and `sw:maintainedBy` connect a triplestore to an `sw:Organization`.
- `sw:hasLicense` and `sw:hasLicenseType` connect to license resources or license categories.
- `sw:hasPrimaryInterface`, `sw:supportsAPI`, and `sw:supportsProtocol` connect products to API/interface resources.
- `sw:hasFeature` and `sw:specializesIn` connect products to features and specializations.
- `sw:supportsQueryLanguage`, `sw:supportsReasoning`, `sw:storesGraph`, and `sw:storesTriple` support typical triplestore query needs.

### 4. Important Classes

Key class families include:

- `sw:Concept`, `sw:SemanticWebConcept`, `sw:OntologyConcept`
- `sw:Resource`, `sw:Entity`, `sw:WebResource`, `sw:DocumentResource`, `sw:DataResource`
- `sw:RDFGraph`, `sw:RDFTriple`, `sw:RDFTerm`, `sw:SubjectTerm`, `sw:PredicateTerm`, `sw:ObjectTerm`
- `sw:Ontology`, `sw:Taxonomy`, `sw:KnowledgeGraph`, `sw:Axiom`, `sw:Constraint`, `sw:Rule`
- `sw:Technology`, `sw:Standard`, `sw:SerializationSyntax`, `sw:DataModel`, `sw:SchemaLanguage`, `sw:OntologyLanguage`, `sw:QueryLanguage`
- `sw:SoftwareSystem`, `sw:DatabaseManagementSystem`, `sw:GraphDatabase`, `sw:RDFDatabase`, `sw:Triplestore`
- `sw:Organization`, `sw:License`, `sw:LicenseCategory`, `sw:APIInterface`, `sw:Protocol`, `sw:Feature`, `sw:Specialization`

### 5. Query Needs Supported

The schema is designed to support SPARQL queries such as:

- Find all triplestores and their raw CSV attributes.
- Find triplestores that support a given query language or API.
- Find triplestores with reasoning, cloud, distributed analytics, data virtualization, or multi-model features.
- List developer or maintainer organizations for triplestores.
- Compare semantic web layers and the technologies contained in each layer.
- Retrieve ontology components such as classes, properties, axioms, constraints, and rules.
- Traverse from knowledge graphs to their governing ontologies.
- Query RDF triples by subject, predicate, object, and graph.

### 6. Import Guidance

For the CSV importer:

1. Create one `sw:Triplestore` instance per row.
2. Preserve the source columns using the five raw CSV datatype properties.
3. Optionally normalize developers into `sw:Organization` instances.
4. Optionally split interface strings into `sw:APIInterface`, `sw:Protocol`, or `sw:QueryLanguage` instances.
5. Optionally split feature strings into `sw:Feature` or subclasses such as `sw:ReasoningFeature`, `sw:CloudManagedFeature`, `sw:DataVirtualizationFeature`, `sw:DistributedAnalyticsFeature`, and `sw:MultiModelFeature`.
6. Keep all ambiguous identifiers, names, license expressions, and mixed-format values as strings unless downstream validation provides stronger typing.

## Constraint Philosophy

The ontology uses RDFS domains and ranges for practical guidance but does not over-constrain the data. This is appropriate for Semantic Web data integration because the source documents emphasize open-world modeling, decentralized identifiers, non-unique names, and incremental enrichment.

## OWL Usage

OWL is used sparingly:

- `owl:inverseOf` links `sw:hasPart` and `sw:partOf`.
- `owl:SymmetricProperty` is used for `sw:contrastsWith`.
- `owl:FunctionalProperty` is used for `sw:hasIRI`, because each resource should normally have one canonical IRI value in this project model.

The ontology remains loadable and queryable in Apache Jena Fuseki.

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5.5`
- Mode: `production`
- Max attempts: 3
- Started: 2026-06-01T10:24:45+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-06-01T10:24:45+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-06-01T10:27:20+00:00
- Response characters: 33908

## JSON Repair

- Status: started
- Reason: LlmError: The model did not return a JSON object.

## JSON Repair Result

- Status: received
- Response characters: 33719

## Attempt 1 Validation

- Status: passed
- Triple count: 541

### Candidate Design

# Semantic Web and Triplestore Ontology Design

## Purpose

This RDF/RDFS schema models the concepts introduced in the supplied Semantic Web and Ontology documents and provides an import-ready structure for the CSV of commonly seen triplestores. The ontology is designed for Apache Jena Fuseki and uses RDF/RDFS as the core representation, with limited OWL vocabulary for useful property semantics such as inverse and symmetric properties.

The schema does not include individual source rows. CSV rows such as GraphDB, Virtuoso, Blazegraph, and Amazon Neptune should be imported later as instances of `sw:Triplestore`.

## Namespace

Base namespace:

`http://example.org/semantic-web#`

Required prefixes are included in the ontology: `sw`, `rdf`, `rdfs`, and `xsd`. The ontology also includes the `owl` prefix for a small number of useful schema-level declarations.

## Main Modeling Areas

### 1. Semantic Web Concepts

The schema represents core concepts from the Semantic Web document, including:

- Web of Documents and Web of Data distinction.
- Resources, entities, documents, data resources, and web resources.
- RDF graphs, RDF triples, RDF terms, subjects, predicates, and objects.
- RDFS schemas and vocabularies.
- Semantic Web layers, including identifier, syntax, data model, ontology, query, logic, proof, and trust layers.
- Standards and technologies such as RDF, RDFS, OWL, SPARQL, SKOS, JSON-LD, Turtle, RDF/XML, URI, IRI, and Unicode as importable technology or standard resources.
- Semantic Web assumptions such as the Open World Assumption and Non-Unique Name Assumption.
- Linked Open Data, DBpedia/Wikidata-style hubs, Schema.org-style vocabularies, and enterprise knowledge graphs.

### 2. Ontology and Knowledge Representation Concepts

The schema models concepts from the ontology introduction, including:

- Ontology, taxonomy, and knowledge graph as related but distinct knowledge organization structures.
- Ontology components: classes, individuals, datatype properties, object properties, relationships, axioms, constraints, and rules.
- Logical profiles, including OWL profile concepts without enumerating specific instance facts.
- Reasoners and reasoning tasks, including classification and consistency checking.
- Foundational ontologies and reusable vocabularies.

### 3. Triplestore CSV Coverage

The CSV columns are represented directly with datatype properties for import fidelity:

| CSV column | Recommended ontology property | Range |
|---|---|---|
| Triplestore Name | `sw:triplestoreName` | `xsd:string` |
| Developer/Maintainer | `sw:developerMaintainerLiteral` | `xsd:string` |
| License Type | `sw:licenseTypeLiteral` | `xsd:string` |
| Primary API/Interfaces | `sw:primaryApiInterfacesLiteral` | `xsd:string` |
| Key Features/Specializations | `sw:keyFeaturesLiteral` | `xsd:string` |

All CSV-backed properties use `xsd:string` because the source profile shows mixed strings, names, codes, version-like values, and descriptive text. This preserves source values safely.

The ontology also supports normalized import when desired:

- `sw:developedBy` and `sw:maintainedBy` connect a triplestore to an `sw:Organization`.
- `sw:hasLicense` and `sw:hasLicenseType` connect to license resources or license categories.
- `sw:hasPrimaryInterface`, `sw:supportsAPI`, and `sw:supportsProtocol` connect products to API/interface resources.
- `sw:hasFeature` and `sw:specializesIn` connect products to features and specializations.
- `sw:supportsQueryLanguage`, `sw:supportsReasoning`, `sw:storesGraph`, and `sw:storesTriple` support typical triplestore query needs.

### 4. Important Classes

Key class families include:

- `sw:Concept`, `sw:SemanticWebConcept`, `sw:OntologyConcept`
- `sw:Resource`, `sw:Entity`, `sw:WebResource`, `sw:DocumentResource`, `sw:DataResource`
- `sw:RDFGraph`, `sw:RDFTriple`, `sw:RDFTerm`, `sw:SubjectTerm`, `sw:PredicateTerm`, `sw:ObjectTerm`
- `sw:Ontology`, `sw:Taxonomy`, `sw:KnowledgeGraph`, `sw:Axiom`, `sw:Constraint`, `sw:Rule`
- `sw:Technology`, `sw:Standard`, `sw:SerializationSyntax`, `sw:DataModel`, `sw:SchemaLanguage`, `sw:OntologyLanguage`, `sw:QueryLanguage`
- `sw:SoftwareSystem`, `sw:DatabaseManagementSystem`, `sw:GraphDatabase`, `sw:RDFDatabase`, `sw:Triplestore`
- `sw:Organization`, `sw:License`, `sw:LicenseCategory`, `sw:APIInterface`, `sw:Protocol`, `sw:Feature`, `sw:Specialization`

### 5. Query Needs Supported

The schema is designed to support SPARQL queries such as:

- Find all triplestores and their raw CSV attributes.
- Find triplestores that support a given query language or API.
- Find triplestores with reasoning, cloud, distributed analytics, data virtualization, or multi-model features.
- List developer or maintainer organizations for triplestores.
- Compare semantic web layers and the technologies contained in each layer.
- Retrieve ontology components such as classes, properties, axioms, constraints, and rules.
- Traverse from knowledge graphs to their governing ontologies.
- Query RDF triples by subject, predicate, object, and graph.

### 6. Import Guidance

For the CSV importer:

1. Create one `sw:Triplestore` instance per row.
2. Preserve the source columns using the five raw CSV datatype properties.
3. Optionally normalize developers into `sw:Organization` instances.
4. Optionally split interface strings into `sw:APIInterface`, `sw:Protocol`, or `sw:QueryLanguage` instances.
5. Optionally split feature strings into `sw:Feature` or subclasses such as `sw:ReasoningFeature`, `sw:CloudManagedFeature`, `sw:DataVirtualizationFeature`, `sw:DistributedAnalyticsFeature`, and `sw:MultiModelFeature`.
6. Keep all ambiguous identifiers, names, license expressions, and mixed-format values as strings unless downstream validation provides stronger typing.

## Constraint Philosophy

The ontology uses RDFS domains and ranges for practical guidance but does not over-constrain the data. This is appropriate for Semantic Web data integration because the source documents emphasize open-world modeling, decentralized identifiers, non-unique names, and incremental enrichment.

## OWL Usage

OWL is used sparingly:

- `owl:inverseOf` links `sw:hasPart` and `sw:partOf`.
- `owl:SymmetricProperty` is used for `sw:contrastsWith`.
- `owl:FunctionalProperty` is used for `sw:hasIRI`, because each resource should normally have one canonical IRI value in this project model.

The ontology remains loadable and queryable in Apache Jena Fuseki.

