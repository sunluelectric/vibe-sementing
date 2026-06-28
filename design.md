# Semantic Web Schema Design

## 1. Purpose and scope

This ontology models the concepts introduced in the provided documents about the Semantic Web and ontology engineering, while also supporting structured import of the CSV about commonly seen triplestores.

The design therefore covers two connected areas:

1. **Conceptual knowledge about the Semantic Web**
   - Semantic Web architecture layers
   - RDF, RDFS, OWL, SPARQL, rules, proof, trust
   - ontology primitives such as classes, individuals, attributes, relationships, and axioms
   - key principles such as the Open World Assumption and Non-Unique Name Assumption
   - major semantic artifacts such as ontologies, knowledge graphs, taxonomies, datasets, serializations, identifiers, and standards bodies

2. **Operational knowledge about triplestores**
   - triplestore products/systems
   - maintainers/developers
   - license descriptions
   - APIs/interfaces/protocols
   - key features/specializations

The ontology is intended to be practical for Apache Jena Fuseki and RDF query use. It is built primarily in RDF/RDFS with limited OWL usage only where clearly useful.

## 2. Design goals

The schema is designed to:

- provide a coherent vocabulary for the project knowledge domain
- preserve the distinctions made in the source documents
- support importing the triplestore CSV without forcing lossy flattening
- enable useful SPARQL queries over both conceptual and catalog-style data
- remain simple enough for Jena/Fuseki loading and querying
- avoid overcommitting to strict datatypes where the CSV indicates mixed text values

## 3. Modeling approach

### 3.1 Core strategy

The ontology separates:

- **knowledge artifacts and concepts** such as `sw:Ontology`, `sw:KnowledgeGraph`, `sw:SemanticWebLayer`, `sw:Reasoner`
- **technology artifacts** such as `sw:Triplestore`, `sw:SerializationFormat`, `sw:QueryLanguage`, `sw:Protocol`, `sw:APIInterface`
- **organizational actors** such as `sw:Organization` and `sw:StandardsBody`
- **descriptive records** such as `sw:LicenseModel`, `sw:Feature`, and `sw:Principle`

### 3.2 CSV-oriented modeling

The CSV contains text fields whose values may mention multiple interfaces or mixed human-readable descriptions. To support both fidelity and future normalization:

- raw CSV values are modeled with datatype properties such as:
  - `sw:developerMaintainerName`
  - `sw:licenseTypeText`
  - `sw:primaryAPIInterfacesText`
  - `sw:keyFeaturesText`
- normalized links are also supported with object properties such as:
  - `sw:hasMaintainer`
  - `sw:hasLicenseModel`
  - `sw:supportsInterface`
  - `sw:hasFeature`

This allows an importer to preserve source strings while also creating reusable linked entities when desired.

### 3.3 RDF/RDFS first, OWL sparingly

RDFS provides the main structure through:

- `rdfs:Class`
- `rdfs:subClassOf`
- `rdfs:domain`
- `rdfs:range`
- labels and comments

OWL is used only for a few practical semantics:

- `owl:Ontology`
- `owl:disjointWith` where the source clearly distinguishes categories
- `owl:inverseOf` for a few highly useful bidirectional relations

## 4. Main conceptual areas

## 4.1 Knowledge organization and semantic artifacts

### Key classes

- `sw:KnowledgeArtifact` — general superclass for formal semantic artifacts
- `sw:Ontology` — formal explicit specification of a shared conceptualization
- `sw:Taxonomy` — hierarchical classification scheme
- `sw:KnowledgeGraph` — graph of entities and relationships
- `sw:Dataset` — a structured collection of semantic data
- `sw:Vocabulary` — controlled set of terms
- `sw:FoundationalOntology` — upper or domain-neutral ontology reused across domains

### Rationale

The documents explicitly distinguish taxonomy, knowledge graph, and ontology. These are therefore modeled as separate classes rather than collapsed into one broad class.

## 4.2 Ontology primitives and schema components

### Key classes

- `sw:OntologyComponent`
- `sw:ClassConcept`
- `sw:Individual`
- `sw:AttributeProperty`
- `sw:RelationshipProperty`
- `sw:Axiom`
- `sw:Constraint`

### Rationale

The ontology introduction identifies classes, individuals, attributes, relationships, and axioms as core primitives. These become explicit schema classes so the knowledge base can describe ontology structure itself.

## 4.3 Semantic Web architecture layers

### Key classes

- `sw:ArchitectureLayer`
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofTrustLayer`

### Related technology classes

- `sw:IdentifierScheme`
- `sw:SerializationFormat`
- `sw:DataModel`
- `sw:OntologyLanguage`
- `sw:QueryLanguage`
- `sw:RuleLanguage`

### Rationale

The Semantic Web document gives a clear layer-cake architecture. Modeling these layers directly supports educational queries and visualizations.

## 4.4 Standards, languages, protocols, and interfaces

### Key classes

- `sw:Standard`
- `sw:Language`
- `sw:Protocol`
- `sw:APIInterface`
- `sw:QueryLanguage`
- `sw:OntologyLanguage`
- `sw:SerializationFormat`

### Notable distinctions

- SPARQL is modeled primarily as a `sw:QueryLanguage`
- RDF and RDFS are modeled as `sw:DataModel` and schema technology concepts
- OWL and SKOS are modeled as ontology/knowledge-organization languages
- APIs and interfaces from the CSV are not forced into one type; `sw:APIInterface` acts as a broad parent usable for SPARQL endpoints, JDBC, REST, GraphQL, Java APIs, native APIs, and workbenches

## 4.5 Reasoning, logic, and assumptions

### Key classes

- `sw:ReasoningCapability`
- `sw:Reasoner`
- `sw:InferenceTask`
- `sw:Principle`
- `sw:Assumption`
- `sw:LogicalProfile`

### Important subclasses

- `sw:ClassificationTask`
- `sw:ConsistencyCheckingTask`
- `sw:OpenWorldAssumption`
- `sw:NonUniqueNameAssumption`
- `sw:OWL2ELProfile`
- `sw:OWL2QLProfile`
- `sw:OWL2RLProfile`

### Rationale

These concepts are central in the source documents and are useful for educational graph queries, such as listing assumptions, reasoners, and logical profiles.

## 4.6 Organizations and ecosystems

### Key classes

- `sw:Agent`
- `sw:Organization`
- `sw:StandardsBody`
- `sw:Community`
- `sw:Person`

### Rationale

The documents reference communities, W3C, and prominent engineers. The CSV references maintainers/developers. A lightweight actor model is therefore needed.

## 4.7 Triplestore catalog modeling

### Key classes

- `sw:SoftwareSystem`
- `sw:DatabaseManagementSystem`
- `sw:GraphDatabase`
- `sw:Triplestore`
- `sw:ManagedService`
- `sw:LicenseModel`
- `sw:Feature`
- `sw:Capability`

### CSV field mapping

| CSV Column | Ontology representation |
|---|---|
| Triplestore Name | `sw:name` on `sw:Triplestore` |
| Developer/Maintainer | raw text via `sw:developerMaintainerName`; normalized org via `sw:hasMaintainer` |
| License Type | raw text via `sw:licenseTypeText`; normalized entity via `sw:hasLicenseModel` |
| Primary API/Interfaces | raw text via `sw:primaryAPIInterfacesText`; normalized links via `sw:supportsInterface` |
| Key Features/Specializations | raw text via `sw:keyFeaturesText`; normalized links via `sw:hasFeature` |

### Rationale

The CSV contains compound descriptive strings. A hybrid raw-plus-normalized model preserves import fidelity and still supports richer graph linking.

## 5. Class hierarchy summary

A simplified hierarchy:

- `sw:Entity`
  - `sw:Agent`
    - `sw:Person`
    - `sw:Organization`
      - `sw:StandardsBody`
      - `sw:Community`
  - `sw:KnowledgeArtifact`
    - `sw:Ontology`
      - `sw:FoundationalOntology`
    - `sw:Taxonomy`
    - `sw:KnowledgeGraph`
    - `sw:Dataset`
    - `sw:Vocabulary`
    - `sw:OntologyComponent`
      - `sw:ClassConcept`
      - `sw:Individual`
      - `sw:PropertyConcept`
        - `sw:AttributeProperty`
        - `sw:RelationshipProperty`
      - `sw:Axiom`
        - `sw:Constraint`
  - `sw:TechnologyArtifact`
    - `sw:Standard`
    - `sw:Language`
      - `sw:OntologyLanguage`
      - `sw:QueryLanguage`
      - `sw:RuleLanguage`
    - `sw:SerializationFormat`
    - `sw:IdentifierScheme`
    - `sw:DataModel`
    - `sw:APIInterface`
    - `sw:Protocol`
    - `sw:SoftwareSystem`
      - `sw:DatabaseManagementSystem`
        - `sw:GraphDatabase`
          - `sw:Triplestore`
          - `sw:ManagedService`
    - `sw:Reasoner`
  - `sw:ConceptualTopic`
    - `sw:Principle`
      - `sw:Assumption`
    - `sw:ReasoningCapability`
    - `sw:InferenceTask`
      - `sw:ClassificationTask`
      - `sw:ConsistencyCheckingTask`
    - `sw:LogicalProfile`
    - `sw:Feature`
    - `sw:Capability`
    - `sw:ArchitectureLayer`
      - `sw:IdentifierLayer`
      - `sw:SyntaxLayer`
      - `sw:DataModelLayer`
      - `sw:OntologyLayer`
      - `sw:QueryLayer`
      - `sw:RulesLayer`
      - `sw:ProofTrustLayer`
    - `sw:LicenseModel`

## 6. Properties

## 6.1 Generic descriptive properties

- `sw:name` — general human-readable name
- `sw:description` — general textual description
- `sw:homepage` — optional URL/IRI as string for software or organizations
- `sw:identifierValue` — generic external or internal identifier text

## 6.2 Structural and conceptual relations

- `sw:definesConcept` — ontology defines a class, property, or axiom
- `sw:describesDomain` — ontology concerns a domain/topic
- `sw:organizesAsSubclassOf` — taxonomy-like broader/narrower conceptual relation
- `sw:implementsDataModel` — software supports RDF-like data model
- `sw:usesSerializationFormat` — dataset/tool exchanges data in Turtle, JSON-LD, etc.
- `sw:usesIdentifierScheme` — technology or dataset uses URI/IRI
- `sw:supportsQueryLanguage` — software or endpoint supports SPARQL or similar
- `sw:supportsInterface` — software exposes API/interface/protocol
- `sw:implementsStandard` — software or language implements a standard
- `sw:publishedBy` — artifact published by organization
- `sw:maintainedBy` / `sw:hasMaintainer` — software maintained by organization
- `sw:developedBy` — software developed by organization or person

## 6.3 Architecture and dependency relations

- `sw:hasLayer` — Semantic Web architecture contains a layer
- `sw:precedesLayer` — one layer is lower than another
- `sw:dependsOnLayer` — upper layer depends on lower layer
- `sw:usesTechnology` — layer or software uses a technology artifact

## 6.4 Reasoning and logic relations

- `sw:supportsReasoningCapability` — ontology/triplestore supports a reasoning feature
- `sw:performsInferenceTask` — reasoner performs classification or consistency checking
- `sw:followsPrinciple` — artifact or model follows OWA-like principles
- `sw:hasLogicalProfile` — ontology language or ontology uses an OWL profile
- `sw:detectsConstraintViolationAgainst` — reasoner or validation process checks a constraint

## 6.5 Triplestore and catalog relations

- `sw:hasLicenseModel` — triplestore linked to normalized license concept
- `sw:hasFeature` — triplestore linked to a feature/specialization
- `sw:hasCapability` — triplestore linked to capability
- `sw:canStoreArtifact` — triplestore stores graphs/datasets/ontologies
- `sw:providesManagedService` — organization provides managed semantic service

## 6.6 Datatype properties for CSV fidelity

- `sw:developerMaintainerName`
- `sw:licenseTypeText`
- `sw:primaryAPIInterfacesText`
- `sw:keyFeaturesText`

All of these are strings because the source values are mixed, compound, and presentation-oriented.

## 7. Datatype decisions

Per the CSV guidance, text-heavy columns are modeled as `xsd:string`.

### Explicit `xsd:string` choices

- triplestore names
- organization names
- license expressions
- API/interface descriptions
- feature descriptions
- identifiers/codes
- URLs kept as strings where strict IRI validation is not guaranteed by source data

### Why not numeric or boolean?

The CSV does not provide dedicated boolean columns such as `isOpenSource`. That meaning may be derivable from text like `Commercial / Free Edition` or `Open Source (GPLv2) / Commercial`, but the source does not guarantee normalized values. Therefore the schema preserves the source text and allows optional normalized modeling.

## 8. Constraints and limited OWL semantics

The ontology uses a few lightweight semantics:

- `sw:AttributeProperty` disjoint with `sw:RelationshipProperty`
- inverse links where highly practical:
  - `sw:hasMaintainer` / `sw:maintains`
  - `sw:hasFeature` / `sw:isFeatureOf`
  - `sw:hasLayer` / `sw:isLayerOfArchitecture`

These improve query ergonomics without making the ontology overly complex.

## 9. Example query needs supported

### 9.1 Educational/conceptual queries

- List all Semantic Web architecture layers in dependency order.
- Find the technologies associated with the ontology layer.
- Retrieve the core components of an ontology.
- List the logical profiles of OWL 2 and their intended use focus.
- Find principles such as Open World Assumption and the technologies that follow them.
- Find foundational ontologies or vocabularies described in the project.

### 9.2 Triplestore catalog queries

- List all triplestores and their maintainers.
- Find triplestores supporting SPARQL.
- Find triplestores exposing GraphQL, JDBC, REST, or native APIs.
- List triplestores with reasoning-related features.
- Compare triplestores by license text.
- Find graph databases that are managed services.

### 9.3 Cross-domain queries

- Find triplestores that support query languages used in the Semantic Web architecture.
- Find software systems that implement or support standards introduced in the documentation.
- Find technologies associated with RDF, RDFS, OWL, and SPARQL.

## 10. Import guidance

### 10.1 For markdown-derived knowledge

Create individuals later for:

- RDF, RDFS, OWL, SPARQL, SKOS, Turtle, JSON-LD, RDF/XML
- W3C, FOAF, Dublin Core, BFO, Gene Ontology, DBpedia, Wikidata
- OWA and NUNA
- OWL 2 EL, QL, RL
- reasoners such as HermiT, Pellet, Openllet if desired

The schema already provides the classes and relations needed.

### 10.2 For CSV import

Each CSV row should become an instance of `sw:Triplestore`.

Recommended import pattern:

- assign `sw:name`
- preserve exact source strings in:
  - `sw:developerMaintainerName`
  - `sw:licenseTypeText`
  - `sw:primaryAPIInterfacesText`
  - `sw:keyFeaturesText`
- optionally create linked `sw:Organization`, `sw:LicenseModel`, `sw:APIInterface`, and `sw:Feature` resources
- use `sw:hasMaintainer`, `sw:hasLicenseModel`, `sw:supportsInterface`, and `sw:hasFeature` for normalization

## 11. Design tradeoffs

### Chosen

- broader but practical class coverage
- hybrid raw-string plus normalized graph modeling
- explicit architecture-layer classes
- separate classes for ontology, taxonomy, and knowledge graph

### Avoided

- overly strict cardinality constraints not supported by source evidence
- exhaustive OWL restrictions that would complicate simple Fuseki use
- enumerating instance facts in the ontology itself

## 12. Result

The resulting ontology is a comprehensive RDF/RDFS schema tailored to the provided documents and CSV. It can serve both as:

- a conceptual semantic model of Semantic Web and ontology knowledge
- a practical schema for importing and querying a triplestore catalog

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5.4`
- Mode: `production`
- Max attempts: 3
- Started: 2026-06-28T23:42:03+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-06-28T23:42:03+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-06-28T23:43:05+00:00
- Response characters: 39053

## Attempt 1 Validation

- Status: passed
- Triple count: 444

### Candidate Design

# Semantic Web Schema Design

## 1. Purpose and scope

This ontology models the concepts introduced in the provided documents about the Semantic Web and ontology engineering, while also supporting structured import of the CSV about commonly seen triplestores.

The design therefore covers two connected areas:

1. **Conceptual knowledge about the Semantic Web**
   - Semantic Web architecture layers
   - RDF, RDFS, OWL, SPARQL, rules, proof, trust
   - ontology primitives such as classes, individuals, attributes, relationships, and axioms
   - key principles such as the Open World Assumption and Non-Unique Name Assumption
   - major semantic artifacts such as ontologies, knowledge graphs, taxonomies, datasets, serializations, identifiers, and standards bodies

2. **Operational knowledge about triplestores**
   - triplestore products/systems
   - maintainers/developers
   - license descriptions
   - APIs/interfaces/protocols
   - key features/specializations

The ontology is intended to be practical for Apache Jena Fuseki and RDF query use. It is built primarily in RDF/RDFS with limited OWL usage only where clearly useful.

## 2. Design goals

The schema is designed to:

- provide a coherent vocabulary for the project knowledge domain
- preserve the distinctions made in the source documents
- support importing the triplestore CSV without forcing lossy flattening
- enable useful SPARQL queries over both conceptual and catalog-style data
- remain simple enough for Jena/Fuseki loading and querying
- avoid overcommitting to strict datatypes where the CSV indicates mixed text values

## 3. Modeling approach

### 3.1 Core strategy

The ontology separates:

- **knowledge artifacts and concepts** such as `sw:Ontology`, `sw:KnowledgeGraph`, `sw:SemanticWebLayer`, `sw:Reasoner`
- **technology artifacts** such as `sw:Triplestore`, `sw:SerializationFormat`, `sw:QueryLanguage`, `sw:Protocol`, `sw:APIInterface`
- **organizational actors** such as `sw:Organization` and `sw:StandardsBody`
- **descriptive records** such as `sw:LicenseModel`, `sw:Feature`, and `sw:Principle`

### 3.2 CSV-oriented modeling

The CSV contains text fields whose values may mention multiple interfaces or mixed human-readable descriptions. To support both fidelity and future normalization:

- raw CSV values are modeled with datatype properties such as:
  - `sw:developerMaintainerName`
  - `sw:licenseTypeText`
  - `sw:primaryAPIInterfacesText`
  - `sw:keyFeaturesText`
- normalized links are also supported with object properties such as:
  - `sw:hasMaintainer`
  - `sw:hasLicenseModel`
  - `sw:supportsInterface`
  - `sw:hasFeature`

This allows an importer to preserve source strings while also creating reusable linked entities when desired.

### 3.3 RDF/RDFS first, OWL sparingly

RDFS provides the main structure through:

- `rdfs:Class`
- `rdfs:subClassOf`
- `rdfs:domain`
- `rdfs:range`
- labels and comments

OWL is used only for a few practical semantics:

- `owl:Ontology`
- `owl:disjointWith` where the source clearly distinguishes categories
- `owl:inverseOf` for a few highly useful bidirectional relations

## 4. Main conceptual areas

## 4.1 Knowledge organization and semantic artifacts

### Key classes

- `sw:KnowledgeArtifact` — general superclass for formal semantic artifacts
- `sw:Ontology` — formal explicit specification of a shared conceptualization
- `sw:Taxonomy` — hierarchical classification scheme
- `sw:KnowledgeGraph` — graph of entities and relationships
- `sw:Dataset` — a structured collection of semantic data
- `sw:Vocabulary` — controlled set of terms
- `sw:FoundationalOntology` — upper or domain-neutral ontology reused across domains

### Rationale

The documents explicitly distinguish taxonomy, knowledge graph, and ontology. These are therefore modeled as separate classes rather than collapsed into one broad class.

## 4.2 Ontology primitives and schema components

### Key classes

- `sw:OntologyComponent`
- `sw:ClassConcept`
- `sw:Individual`
- `sw:AttributeProperty`
- `sw:RelationshipProperty`
- `sw:Axiom`
- `sw:Constraint`

### Rationale

The ontology introduction identifies classes, individuals, attributes, relationships, and axioms as core primitives. These become explicit schema classes so the knowledge base can describe ontology structure itself.

## 4.3 Semantic Web architecture layers

### Key classes

- `sw:ArchitectureLayer`
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofTrustLayer`

### Related technology classes

- `sw:IdentifierScheme`
- `sw:SerializationFormat`
- `sw:DataModel`
- `sw:OntologyLanguage`
- `sw:QueryLanguage`
- `sw:RuleLanguage`

### Rationale

The Semantic Web document gives a clear layer-cake architecture. Modeling these layers directly supports educational queries and visualizations.

## 4.4 Standards, languages, protocols, and interfaces

### Key classes

- `sw:Standard`
- `sw:Language`
- `sw:Protocol`
- `sw:APIInterface`
- `sw:QueryLanguage`
- `sw:OntologyLanguage`
- `sw:SerializationFormat`

### Notable distinctions

- SPARQL is modeled primarily as a `sw:QueryLanguage`
- RDF and RDFS are modeled as `sw:DataModel` and schema technology concepts
- OWL and SKOS are modeled as ontology/knowledge-organization languages
- APIs and interfaces from the CSV are not forced into one type; `sw:APIInterface` acts as a broad parent usable for SPARQL endpoints, JDBC, REST, GraphQL, Java APIs, native APIs, and workbenches

## 4.5 Reasoning, logic, and assumptions

### Key classes

- `sw:ReasoningCapability`
- `sw:Reasoner`
- `sw:InferenceTask`
- `sw:Principle`
- `sw:Assumption`
- `sw:LogicalProfile`

### Important subclasses

- `sw:ClassificationTask`
- `sw:ConsistencyCheckingTask`
- `sw:OpenWorldAssumption`
- `sw:NonUniqueNameAssumption`
- `sw:OWL2ELProfile`
- `sw:OWL2QLProfile`
- `sw:OWL2RLProfile`

### Rationale

These concepts are central in the source documents and are useful for educational graph queries, such as listing assumptions, reasoners, and logical profiles.

## 4.6 Organizations and ecosystems

### Key classes

- `sw:Agent`
- `sw:Organization`
- `sw:StandardsBody`
- `sw:Community`
- `sw:Person`

### Rationale

The documents reference communities, W3C, and prominent engineers. The CSV references maintainers/developers. A lightweight actor model is therefore needed.

## 4.7 Triplestore catalog modeling

### Key classes

- `sw:SoftwareSystem`
- `sw:DatabaseManagementSystem`
- `sw:GraphDatabase`
- `sw:Triplestore`
- `sw:ManagedService`
- `sw:LicenseModel`
- `sw:Feature`
- `sw:Capability`

### CSV field mapping

| CSV Column | Ontology representation |
|---|---|
| Triplestore Name | `sw:name` on `sw:Triplestore` |
| Developer/Maintainer | raw text via `sw:developerMaintainerName`; normalized org via `sw:hasMaintainer` |
| License Type | raw text via `sw:licenseTypeText`; normalized entity via `sw:hasLicenseModel` |
| Primary API/Interfaces | raw text via `sw:primaryAPIInterfacesText`; normalized links via `sw:supportsInterface` |
| Key Features/Specializations | raw text via `sw:keyFeaturesText`; normalized links via `sw:hasFeature` |

### Rationale

The CSV contains compound descriptive strings. A hybrid raw-plus-normalized model preserves import fidelity and still supports richer graph linking.

## 5. Class hierarchy summary

A simplified hierarchy:

- `sw:Entity`
  - `sw:Agent`
    - `sw:Person`
    - `sw:Organization`
      - `sw:StandardsBody`
      - `sw:Community`
  - `sw:KnowledgeArtifact`
    - `sw:Ontology`
      - `sw:FoundationalOntology`
    - `sw:Taxonomy`
    - `sw:KnowledgeGraph`
    - `sw:Dataset`
    - `sw:Vocabulary`
    - `sw:OntologyComponent`
      - `sw:ClassConcept`
      - `sw:Individual`
      - `sw:PropertyConcept`
        - `sw:AttributeProperty`
        - `sw:RelationshipProperty`
      - `sw:Axiom`
        - `sw:Constraint`
  - `sw:TechnologyArtifact`
    - `sw:Standard`
    - `sw:Language`
      - `sw:OntologyLanguage`
      - `sw:QueryLanguage`
      - `sw:RuleLanguage`
    - `sw:SerializationFormat`
    - `sw:IdentifierScheme`
    - `sw:DataModel`
    - `sw:APIInterface`
    - `sw:Protocol`
    - `sw:SoftwareSystem`
      - `sw:DatabaseManagementSystem`
        - `sw:GraphDatabase`
          - `sw:Triplestore`
          - `sw:ManagedService`
    - `sw:Reasoner`
  - `sw:ConceptualTopic`
    - `sw:Principle`
      - `sw:Assumption`
    - `sw:ReasoningCapability`
    - `sw:InferenceTask`
      - `sw:ClassificationTask`
      - `sw:ConsistencyCheckingTask`
    - `sw:LogicalProfile`
    - `sw:Feature`
    - `sw:Capability`
    - `sw:ArchitectureLayer`
      - `sw:IdentifierLayer`
      - `sw:SyntaxLayer`
      - `sw:DataModelLayer`
      - `sw:OntologyLayer`
      - `sw:QueryLayer`
      - `sw:RulesLayer`
      - `sw:ProofTrustLayer`
    - `sw:LicenseModel`

## 6. Properties

## 6.1 Generic descriptive properties

- `sw:name` — general human-readable name
- `sw:description` — general textual description
- `sw:homepage` — optional URL/IRI as string for software or organizations
- `sw:identifierValue` — generic external or internal identifier text

## 6.2 Structural and conceptual relations

- `sw:definesConcept` — ontology defines a class, property, or axiom
- `sw:describesDomain` — ontology concerns a domain/topic
- `sw:organizesAsSubclassOf` — taxonomy-like broader/narrower conceptual relation
- `sw:implementsDataModel` — software supports RDF-like data model
- `sw:usesSerializationFormat` — dataset/tool exchanges data in Turtle, JSON-LD, etc.
- `sw:usesIdentifierScheme` — technology or dataset uses URI/IRI
- `sw:supportsQueryLanguage` — software or endpoint supports SPARQL or similar
- `sw:supportsInterface` — software exposes API/interface/protocol
- `sw:implementsStandard` — software or language implements a standard
- `sw:publishedBy` — artifact published by organization
- `sw:maintainedBy` / `sw:hasMaintainer` — software maintained by organization
- `sw:developedBy` — software developed by organization or person

## 6.3 Architecture and dependency relations

- `sw:hasLayer` — Semantic Web architecture contains a layer
- `sw:precedesLayer` — one layer is lower than another
- `sw:dependsOnLayer` — upper layer depends on lower layer
- `sw:usesTechnology` — layer or software uses a technology artifact

## 6.4 Reasoning and logic relations

- `sw:supportsReasoningCapability` — ontology/triplestore supports a reasoning feature
- `sw:performsInferenceTask` — reasoner performs classification or consistency checking
- `sw:followsPrinciple` — artifact or model follows OWA-like principles
- `sw:hasLogicalProfile` — ontology language or ontology uses an OWL profile
- `sw:detectsConstraintViolationAgainst` — reasoner or validation process checks a constraint

## 6.5 Triplestore and catalog relations

- `sw:hasLicenseModel` — triplestore linked to normalized license concept
- `sw:hasFeature` — triplestore linked to a feature/specialization
- `sw:hasCapability` — triplestore linked to capability
- `sw:canStoreArtifact` — triplestore stores graphs/datasets/ontologies
- `sw:providesManagedService` — organization provides managed semantic service

## 6.6 Datatype properties for CSV fidelity

- `sw:developerMaintainerName`
- `sw:licenseTypeText`
- `sw:primaryAPIInterfacesText`
- `sw:keyFeaturesText`

All of these are strings because the source values are mixed, compound, and presentation-oriented.

## 7. Datatype decisions

Per the CSV guidance, text-heavy columns are modeled as `xsd:string`.

### Explicit `xsd:string` choices

- triplestore names
- organization names
- license expressions
- API/interface descriptions
- feature descriptions
- identifiers/codes
- URLs kept as strings where strict IRI validation is not guaranteed by source data

### Why not numeric or boolean?

The CSV does not provide dedicated boolean columns such as `isOpenSource`. That meaning may be derivable from text like `Commercial / Free Edition` or `Open Source (GPLv2) / Commercial`, but the source does not guarantee normalized values. Therefore the schema preserves the source text and allows optional normalized modeling.

## 8. Constraints and limited OWL semantics

The ontology uses a few lightweight semantics:

- `sw:AttributeProperty` disjoint with `sw:RelationshipProperty`
- inverse links where highly practical:
  - `sw:hasMaintainer` / `sw:maintains`
  - `sw:hasFeature` / `sw:isFeatureOf`
  - `sw:hasLayer` / `sw:isLayerOfArchitecture`

These improve query ergonomics without making the ontology overly complex.

## 9. Example query needs supported

### 9.1 Educational/conceptual queries

- List all Semantic Web architecture layers in dependency order.
- Find the technologies associated with the ontology layer.
- Retrieve the core components of an ontology.
- List the logical profiles of OWL 2 and their intended use focus.
- Find principles such as Open World Assumption and the technologies that follow them.
- Find foundational ontologies or vocabularies described in the project.

### 9.2 Triplestore catalog queries

- List all triplestores and their maintainers.
- Find triplestores supporting SPARQL.
- Find triplestores exposing GraphQL, JDBC, REST, or native APIs.
- List triplestores with reasoning-related features.
- Compare triplestores by license text.
- Find graph databases that are managed services.

### 9.3 Cross-domain queries

- Find triplestores that support query languages used in the Semantic Web architecture.
- Find software systems that implement or support standards introduced in the documentation.
- Find technologies associated with RDF, RDFS, OWL, and SPARQL.

## 10. Import guidance

### 10.1 For markdown-derived knowledge

Create individuals later for:

- RDF, RDFS, OWL, SPARQL, SKOS, Turtle, JSON-LD, RDF/XML
- W3C, FOAF, Dublin Core, BFO, Gene Ontology, DBpedia, Wikidata
- OWA and NUNA
- OWL 2 EL, QL, RL
- reasoners such as HermiT, Pellet, Openllet if desired

The schema already provides the classes and relations needed.

### 10.2 For CSV import

Each CSV row should become an instance of `sw:Triplestore`.

Recommended import pattern:

- assign `sw:name`
- preserve exact source strings in:
  - `sw:developerMaintainerName`
  - `sw:licenseTypeText`
  - `sw:primaryAPIInterfacesText`
  - `sw:keyFeaturesText`
- optionally create linked `sw:Organization`, `sw:LicenseModel`, `sw:APIInterface`, and `sw:Feature` resources
- use `sw:hasMaintainer`, `sw:hasLicenseModel`, `sw:supportsInterface`, and `sw:hasFeature` for normalization

## 11. Design tradeoffs

### Chosen

- broader but practical class coverage
- hybrid raw-string plus normalized graph modeling
- explicit architecture-layer classes
- separate classes for ontology, taxonomy, and knowledge graph

### Avoided

- overly strict cardinality constraints not supported by source evidence
- exhaustive OWL restrictions that would complicate simple Fuseki use
- enumerating instance facts in the ontology itself

## 12. Result

The resulting ontology is a comprehensive RDF/RDFS schema tailored to the provided documents and CSV. It can serve both as:

- a conceptual semantic model of Semantic Web and ontology knowledge
- a practical schema for importing and querying a triplestore catalog

