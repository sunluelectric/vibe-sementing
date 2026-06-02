# Semantic Web Schema Design

## 1. Purpose and scope

This schema models the knowledge explicitly present in the project sources:

1. the conceptual content of the two markdown documents about the Semantic Web and ontologies, and  
2. the CSV structure describing commonly seen triplestores and their major characteristics.

The goal is to provide an RDF/RDFS-first ontology that:

- captures the main concepts introduced in the documents,
- supports ingest of the triplestore CSV without loss of meaning,
- remains practical for Apache Jena Fuseki storage and SPARQL querying,
- uses OWL only where it clearly helps interoperability or identity handling.

This is a schema only. It does **not** include instance data.

---

## 2. Design principles

### 2.1 Source-driven modeling
The ontology is derived from the supplied materials, not from a generic prebuilt domain model. The source material repeatedly discusses:

- semantic web architecture layers,
- RDF, RDFS, OWL, SPARQL, serialization syntaxes,
- ontology primitives such as classes, individuals, datatype properties, object properties, and axioms,
- reasoning, classification, consistency checking,
- knowledge organization structures such as taxonomy, knowledge graph, and ontology,
- foundational assumptions such as the Open World Assumption and Non-Unique Name Assumption,
- examples of foundational ontologies and standards,
- triplestore products, maintainers, licenses, APIs/interfaces, and feature descriptions.

The schema therefore includes classes for these concepts and explicit properties for their relationships.

### 2.2 RDF/RDFS first
The model uses `rdfs:Class`, `rdf:Property`, `rdfs:subClassOf`, `rdfs:domain`, and `rdfs:range` as the main structural mechanisms. A small amount of OWL is used for:

- declaring the ontology resource,
- optional inverse property support,
- `owl:sameAs` compatibility for identity alignment discussed in the source material.

### 2.3 Import fidelity for CSV
The CSV contains mixed textual values. Its columns are modeled conservatively as strings where appropriate:

- names,
- maintainers,
- license descriptions,
- API/interface text,
- feature/specialization text.

Because several columns contain compound values such as `Commercial / Free Edition` or `SPARQL / SQL / ODBC / JDBC`, the schema supports **both**:

- literal preservation of the full original field, and
- optional structured decomposition into linked entities such as interfaces, licenses, and capabilities.

This preserves source fidelity while enabling richer graph queries.

### 2.4 Practical query support
The schema is designed to support queries such as:

- Which triplestores support SPARQL?
- Which triplestores are open source, commercial, or mixed-license?
- Which products are maintained by a particular organization?
- Which systems expose GraphQL, Gremlin, JDBC, or REST interfaces?
- Which technologies belong to the Semantic Web layer cake?
- Which concepts are part of ontology structure versus reasoning versus publishing?
- Which foundational vocabularies are examples of ontologies or knowledge organization systems?

---

## 3. Namespace

Base namespace:

- `http://example.org/semantic-web#`

Preferred prefix:

- `sw:`

---

## 4. High-level model overview

The ontology has four major modules.

### 4.1 Knowledge and architecture module
Models the concepts introduced in the markdown documents:

- `sw:SemanticWeb`
- `sw:WebArchitecture`
- `sw:ArchitectureLayer`
- `sw:Technology`
- `sw:DataModelTechnology`
- `sw:OntologyLanguage`
- `sw:QueryLanguage`
- `sw:SerializationFormat`
- `sw:IdentifierScheme`
- `sw:CharacterSetStandard`
- `sw:Reasoner`
- `sw:SemanticPrinciple`
- `sw:ReasoningTask`

### 4.2 Knowledge organization and ontology module
Models the conceptual distinctions discussed in the ontology and semantic web introductions:

- `sw:KnowledgeOrganizationArtifact`
- `sw:Taxonomy`
- `sw:KnowledgeGraph`
- `sw:Ontology`
- `sw:OntologyPrimitive`
- `sw:OntologyClass`
- `sw:OntologyIndividual`
- `sw:DatatypePropertyConcept`
- `sw:ObjectPropertyConcept`
- `sw:Axiom`
- `sw:Constraint`

### 4.3 Standards and profiles module
Models standards, profiles, and named ontology families:

- `sw:Standard`
- `sw:OntologyProfile`
- `sw:FoundationalOntology`
- `sw:Vocabulary`

### 4.4 Triplestore catalog module
Models the CSV and practical repository metadata:

- `sw:Triplestore`
- `sw:DatabaseManagementSystem`
- `sw:Organization`
- `sw:LicenseModel`
- `sw:Interface`
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`
- `sw:Feature`
- `sw:Specialization`
- `sw:DeploymentModel`

---

## 5. Core classes

### 5.1 General conceptual classes

#### `sw:Concept`
Top-level domain concept in this ontology. Used as a broad superclass for major modeled ideas.

#### `sw:InformationResource`
A resource that conveys structured knowledge, such as a vocabulary, ontology, standard, or architecture description.

#### `sw:Standard`
A formalized technical standard or specification.

#### `sw:Technology`
A technology, language, framework element, or implementation used within the semantic web ecosystem.

#### `sw:Organization`
An organization that develops, maintains, publishes, or standardizes a technology.

---

### 5.2 Semantic Web architecture classes

#### `sw:SemanticWeb`
Represents the Semantic Web as a web-of-data paradigm.

#### `sw:WebArchitecture`
A technical architecture composed of layers and technologies.

#### `sw:ArchitectureLayer`
A conceptual layer in the semantic web stack.

Subclasses:
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofLayer`
- `sw:TrustLayer`

#### `sw:IdentifierScheme`
Identifier technology such as URI or IRI.

#### `sw:CharacterSetStandard`
Character encoding standard such as Unicode.

#### `sw:SerializationFormat`
RDF serialization syntax such as Turtle, JSON-LD, RDF/XML.

#### `sw:DataModelTechnology`
Data model technology such as RDF or RDFS.

#### `sw:OntologyLanguage`
Ontology or schema language such as OWL or SKOS.

#### `sw:QueryLanguage`
Query language such as SPARQL.

#### `sw:RuleLanguage`
Rule language such as RIF or SWRL.

#### `sw:Reasoner`
A reasoning engine or reasoner type used for inference or consistency checking.

#### `sw:ReasoningTask`
A task performed by reasoning systems.

Subclasses:
- `sw:ClassificationTask`
- `sw:ConsistencyCheckingTask`

#### `sw:SemanticPrinciple`
A principle or assumption in semantic web logic.

Subclasses:
- `sw:OpenWorldAssumption`
- `sw:NonUniqueNameAssumption`

---

### 5.3 Ontology and knowledge organization classes

#### `sw:KnowledgeOrganizationArtifact`
A formal artifact used to organize or structure knowledge.

Subclasses:
- `sw:Taxonomy`
- `sw:KnowledgeGraph`
- `sw:Ontology`
- `sw:Vocabulary`

#### `sw:Ontology`
A formal, explicit specification of a shared conceptualization.

#### `sw:Taxonomy`
A hierarchical classification scheme focused on subclassing or parent-child structure.

#### `sw:KnowledgeGraph`
A graph of entities connected by typed relationships.

#### `sw:Vocabulary`
A named set of terms for describing resources.

#### `sw:FoundationalOntology`
A reusable upper-level or broadly applicable ontology/vocabulary family.

#### `sw:OntologyProfile`
An OWL profile or similar modeling profile.

Examples expected at data level could include EL, QL, RL.

---

### 5.4 Ontology primitives and logical components

#### `sw:OntologyPrimitive`
A building block of an ontology.

Subclasses:
- `sw:OntologyClass`
- `sw:OntologyIndividual`
- `sw:DatatypePropertyConcept`
- `sw:ObjectPropertyConcept`
- `sw:Axiom`

#### `sw:OntologyClass`
The concept of a class within an ontology.

#### `sw:OntologyIndividual`
The concept of an individual/instance.

#### `sw:DatatypePropertyConcept`
The concept of a datatype property as an ontology primitive.

#### `sw:ObjectPropertyConcept`
The concept of an object property as an ontology primitive.

#### `sw:Axiom`
A logical assertion in an ontology.

Subclasses:
- `sw:Constraint`
- `sw:PropertyCharacteristic`
- `sw:ClassRestriction`
- `sw:CardinalityConstraint`
- `sw:DisjointnessAxiom`

#### `sw:PropertyCharacteristic`
A property-level logical feature such as transitive, symmetric, functional, or inverse.

#### `sw:ClassRestriction`
A class-level restriction expressed over properties.

#### `sw:CardinalityConstraint`
A restriction on the number of values for a property.

#### `sw:DisjointnessAxiom`
An axiom stating that classes do not overlap.

---

### 5.5 Triplestore catalog classes

#### `sw:DatabaseManagementSystem`
A database management system.

#### `sw:Triplestore`
An RDF-oriented database or graph repository platform. Modeled as a subclass of `sw:DatabaseManagementSystem` and `sw:Technology`.

#### `sw:Interface`
A general access interface exposed by software.

Subclasses:
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`

This allows mixed CSV values like SPARQL, JDBC, REST, RDF4J, GraphQL, Workbench, native Java API, etc. to be represented either uniformly or more specifically.

#### `sw:LicenseModel`
A textual or structured description of software licensing.

#### `sw:Feature`
A notable capability, property, or advertised feature.

#### `sw:Specialization`
A specialized focus area of a technology or product.

#### `sw:DeploymentModel`
A deployment style such as managed service, native component, distributed analytics platform, or enterprise platform.

---

## 6. Property design

### 6.1 Labeling and descriptive properties

#### `sw:name`
Datatype property for human-readable names.

#### `sw:description`
Datatype property for descriptive text.

#### `sw:identifier`
Datatype property for local identifiers or codes when needed.

These supplement `rdfs:label` and `rdfs:comment` and are useful for importer output.

---

### 6.2 Architecture and conceptual relations

#### `sw:hasLayer`
Links a web architecture to one of its layers.

#### `sw:layerUsesTechnology`
Links an architecture layer to a technology used at that layer.

#### `sw:supportsPrinciple`
Links a semantic web or technology to a semantic principle.

#### `sw:enablesTask`
Links a technology or reasoner to a reasoning or operational task.

#### `sw:extendsTechnology`
Links one technology to another that it extends conceptually.

Useful example at data level: OWL extends RDFS, RDFS extends RDF.

#### `sw:serializedAs`
Links a data model or resource to a serialization format.

#### `sw:queriesWith`
Links a graph or system to a query language.

---

### 6.3 Ontology structure relations

#### `sw:hasPrimitive`
Links an ontology to one of its primitives.

#### `sw:definesConcept`
Links a vocabulary or ontology to a concept it defines.

#### `sw:definesProperty`
Links a vocabulary or ontology to a property it defines.

#### `sw:hasAxiom`
Links an ontology to one of its axioms.

#### `sw:hasProfile`
Links an ontology language to a profile.

#### `sw:usedFor`
Links a technology, ontology, profile, or feature to a purpose or application description.

#### `sw:contrastsWith`
Links related but distinct conceptual artifacts, such as taxonomy vs knowledge graph vs ontology.

---

### 6.4 Organization and publication relations

#### `sw:developedBy`
Links a technology or triplestore to its developer.

#### `sw:maintainedBy`
Links a technology or triplestore to its maintainer.

#### `sw:publishedBy`
Links a standard, ontology, or vocabulary to its publisher or standards body.

---

### 6.5 Triplestore-specific relations

#### `sw:hasLicenseModel`
Links a triplestore to a structured license model resource.

#### `sw:licenseText`
Stores the original CSV license field as a string.

#### `sw:offersInterface`
Links a triplestore to any interface it exposes.

#### `sw:offersAPI`
Specialized subproperty of `sw:offersInterface` for APIs.

#### `sw:offersProtocol`
Specialized subproperty of `sw:offersInterface` for protocols.

#### `sw:offersWorkbench`
Specialized subproperty of `sw:offersInterface` for workbench-style tools.

#### `sw:primaryInterfaceText`
Stores the original CSV interface field as a string.

#### `sw:hasFeature`
Links a triplestore to a feature resource.

#### `sw:hasSpecialization`
Links a triplestore to a specialization resource.

#### `sw:featureText`
Stores the original CSV feature/specialization field as a string.

#### `sw:hasDeploymentModel`
Links a system to a deployment model resource.

#### `sw:isOpenSource`
Boolean convenience property for downstream enrichment when licensing has been normalized. Not required during import if source text is ambiguous.

#### `sw:isCommercial`
Boolean convenience property for downstream enrichment when licensing has been normalized.

These booleans are optional because the CSV often expresses mixed licensing.

---

### 6.6 Identity and interoperability relations

#### `sw:equivalentResource`
An interoperability-friendly subproperty aligned with `owl:sameAs` usage expectations from the source material.

This is included because the documents explicitly discuss multiple URIs identifying the same entity.

---

## 7. Hierarchy summary

### 7.1 Class hierarchy highlights

- `sw:Technology`
  - `sw:IdentifierScheme`
  - `sw:CharacterSetStandard`
  - `sw:SerializationFormat`
  - `sw:DataModelTechnology`
  - `sw:OntologyLanguage`
  - `sw:QueryLanguage`
  - `sw:RuleLanguage`
  - `sw:Reasoner`
  - `sw:DatabaseManagementSystem`
    - `sw:Triplestore`
  - `sw:Interface`
    - `sw:API`
    - `sw:Protocol`
    - `sw:Workbench`
    - `sw:ProgrammingInterface`

- `sw:KnowledgeOrganizationArtifact`
  - `sw:Taxonomy`
  - `sw:KnowledgeGraph`
  - `sw:Ontology`
  - `sw:Vocabulary`
    - `sw:FoundationalOntology`

- `sw:OntologyPrimitive`
  - `sw:OntologyClass`
  - `sw:OntologyIndividual`
  - `sw:DatatypePropertyConcept`
  - `sw:ObjectPropertyConcept`
  - `sw:Axiom`
    - `sw:Constraint`
    - `sw:PropertyCharacteristic`
    - `sw:ClassRestriction`
    - `sw:CardinalityConstraint`
    - `sw:DisjointnessAxiom`

- `sw:ArchitectureLayer`
  - `sw:IdentifierLayer`
  - `sw:SyntaxLayer`
  - `sw:DataModelLayer`
  - `sw:OntologyLayer`
  - `sw:QueryLayer`
  - `sw:RulesLayer`
  - `sw:ProofLayer`
  - `sw:TrustLayer`

- `sw:SemanticPrinciple`
  - `sw:OpenWorldAssumption`
  - `sw:NonUniqueNameAssumption`

- `sw:ReasoningTask`
  - `sw:ClassificationTask`
  - `sw:ConsistencyCheckingTask`

### 7.2 Property hierarchy highlights

- `sw:offersAPI` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:offersProtocol` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:offersWorkbench` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:hasSpecialization` `rdfs:subPropertyOf` `sw:hasFeature`
- `sw:equivalentResource` `rdfs:subPropertyOf` `owl:sameAs`

---

## 8. Datatype choices

The CSV profile strongly supports strings for all supplied columns. The ontology therefore uses:

- `xsd:string` for names, developer/maintainer names, license text, API/interface text, and feature text,
- `xsd:boolean` only for optional normalized convenience properties `sw:isOpenSource` and `sw:isCommercial`.

No numeric or date datatypes are introduced because the source data does not justify them.

---

## 9. Constraints and modeling choices

### 9.1 Domain/range are guidance, not hard validation
RDFS domains and ranges are included for practical inferencing and query clarity, but they should be understood under open-world semantics. They help consumers and importers without imposing rigid closed-world validation.

### 9.2 Literal preservation plus normalization
For CSV import, each compound text field should be preserved exactly in literal form:

- `sw:licenseText`
- `sw:primaryInterfaceText`
- `sw:featureText`

Optionally, importers may additionally create linked resources for:

- organizations,
- licenses,
- interfaces,
- features,
- specializations,
- deployment models.

This dual strategy avoids loss of source fidelity and supports later normalization.

### 9.3 Avoiding overcommitment on licenses
The source has mixed values like `Open Source (GPLv2) / Commercial` and `Commercial / Free Edition`. Therefore the schema does not force a single controlled license taxonomy. Instead it supports:

- raw textual preservation,
- a structured `sw:LicenseModel` node if desired,
- optional booleans when a downstream process confidently derives them.

### 9.4 Avoiding overcommitment on interfaces
The `Primary API/Interfaces` column mixes protocols, APIs, query languages, frameworks, workbenches, and language bindings. The schema therefore uses a broad superclass `sw:Interface` with specialized subclasses.

---

## 10. Expected importer mapping from CSV

For each CSV row, an importer would typically create one `sw:Triplestore` resource and attach:

- `rdfs:label` and/or `sw:name` from **Triplestore Name**,
- `sw:developedBy` or `sw:maintainedBy` to an `sw:Organization` resource derived from **Developer/Maintainer**,
- `sw:licenseText` from **License Type**,
- optionally `sw:hasLicenseModel` to one or more structured `sw:LicenseModel` resources,
- `sw:primaryInterfaceText` from **Primary API/Interfaces**,
- optionally multiple `sw:offersInterface` links to interface resources,
- `sw:featureText` from **Key Features/Specializations**,
- optionally `sw:hasFeature`, `sw:hasSpecialization`, or `sw:hasDeploymentModel` links.

Because the CSV is only 11 rows and values are varied, a semi-structured import strategy is appropriate.

---

## 11. Example query patterns supported

### 11.1 Find triplestores and their maintainers
```sparql
SELECT ?store ?label ?orgLabel WHERE {
  ?store a sw:Triplestore ;
         rdfs:label ?label ;
         sw:maintainedBy ?org .
  ?org rdfs:label ?orgLabel .
}
```

### 11.2 Find triplestores exposing SPARQL or GraphQL
```sparql
SELECT ?storeLabel ?ifaceLabel WHERE {
  ?store a sw:Triplestore ;
         rdfs:label ?storeLabel ;
         sw:offersInterface ?iface .
  ?iface rdfs:label ?ifaceLabel .
  FILTER (?ifaceLabel IN ("SPARQL", "SPARQL 1.1", "GraphQL"))
}
```

### 11.3 List semantic web layers and their technologies
```sparql
SELECT ?layerLabel ?techLabel WHERE {
  ?layer a sw:ArchitectureLayer ;
         rdfs:label ?layerLabel ;
         sw:layerUsesTechnology ?tech .
  ?tech rdfs:label ?techLabel .
}
ORDER BY ?layerLabel ?techLabel
```

### 11.4 Show ontology primitives
```sparql
SELECT ?primitiveClass ?label WHERE {
  ?primitiveClass rdfs:subClassOf sw:OntologyPrimitive ;
                  rdfs:label ?label .
}
```

### 11.5 Find concepts related to reasoning
```sparql
SELECT ?thing ?label WHERE {
  ?thing sw:enablesTask sw:ClassificationTask .
  OPTIONAL { ?thing rdfs:label ?label }
}
```

---

## 12. Why this schema fits the project

This design reflects both source types:

- The markdown files are conceptual and educational, so the ontology includes classes for semantic web architecture, ontology primitives, reasoning, assumptions, standards, and profiles.
- The CSV is product-oriented, so the ontology includes concrete software catalog structures for triplestores, maintainers, licenses, interfaces, and features.

The combined result allows one graph to represent both:

- the **theory** of the Semantic Web and ontologies, and
- the **software ecosystem** used to implement those ideas.

That makes the schema suitable for documentation, linked-data publication, teaching examples, and practical triplestore comparison queries in Fuseki.

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5.4`
- Mode: `production`
- Max attempts: 3
- Started: 2026-06-02T13:17:18+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-06-02T13:17:18+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-06-02T13:19:30+00:00
- Response characters: 40384

## Attempt 1 Validation

- Status: passed
- Triple count: 427

### Candidate Design

# Semantic Web Schema Design

## 1. Purpose and scope

This schema models the knowledge explicitly present in the project sources:

1. the conceptual content of the two markdown documents about the Semantic Web and ontologies, and  
2. the CSV structure describing commonly seen triplestores and their major characteristics.

The goal is to provide an RDF/RDFS-first ontology that:

- captures the main concepts introduced in the documents,
- supports ingest of the triplestore CSV without loss of meaning,
- remains practical for Apache Jena Fuseki storage and SPARQL querying,
- uses OWL only where it clearly helps interoperability or identity handling.

This is a schema only. It does **not** include instance data.

---

## 2. Design principles

### 2.1 Source-driven modeling
The ontology is derived from the supplied materials, not from a generic prebuilt domain model. The source material repeatedly discusses:

- semantic web architecture layers,
- RDF, RDFS, OWL, SPARQL, serialization syntaxes,
- ontology primitives such as classes, individuals, datatype properties, object properties, and axioms,
- reasoning, classification, consistency checking,
- knowledge organization structures such as taxonomy, knowledge graph, and ontology,
- foundational assumptions such as the Open World Assumption and Non-Unique Name Assumption,
- examples of foundational ontologies and standards,
- triplestore products, maintainers, licenses, APIs/interfaces, and feature descriptions.

The schema therefore includes classes for these concepts and explicit properties for their relationships.

### 2.2 RDF/RDFS first
The model uses `rdfs:Class`, `rdf:Property`, `rdfs:subClassOf`, `rdfs:domain`, and `rdfs:range` as the main structural mechanisms. A small amount of OWL is used for:

- declaring the ontology resource,
- optional inverse property support,
- `owl:sameAs` compatibility for identity alignment discussed in the source material.

### 2.3 Import fidelity for CSV
The CSV contains mixed textual values. Its columns are modeled conservatively as strings where appropriate:

- names,
- maintainers,
- license descriptions,
- API/interface text,
- feature/specialization text.

Because several columns contain compound values such as `Commercial / Free Edition` or `SPARQL / SQL / ODBC / JDBC`, the schema supports **both**:

- literal preservation of the full original field, and
- optional structured decomposition into linked entities such as interfaces, licenses, and capabilities.

This preserves source fidelity while enabling richer graph queries.

### 2.4 Practical query support
The schema is designed to support queries such as:

- Which triplestores support SPARQL?
- Which triplestores are open source, commercial, or mixed-license?
- Which products are maintained by a particular organization?
- Which systems expose GraphQL, Gremlin, JDBC, or REST interfaces?
- Which technologies belong to the Semantic Web layer cake?
- Which concepts are part of ontology structure versus reasoning versus publishing?
- Which foundational vocabularies are examples of ontologies or knowledge organization systems?

---

## 3. Namespace

Base namespace:

- `http://example.org/semantic-web#`

Preferred prefix:

- `sw:`

---

## 4. High-level model overview

The ontology has four major modules.

### 4.1 Knowledge and architecture module
Models the concepts introduced in the markdown documents:

- `sw:SemanticWeb`
- `sw:WebArchitecture`
- `sw:ArchitectureLayer`
- `sw:Technology`
- `sw:DataModelTechnology`
- `sw:OntologyLanguage`
- `sw:QueryLanguage`
- `sw:SerializationFormat`
- `sw:IdentifierScheme`
- `sw:CharacterSetStandard`
- `sw:Reasoner`
- `sw:SemanticPrinciple`
- `sw:ReasoningTask`

### 4.2 Knowledge organization and ontology module
Models the conceptual distinctions discussed in the ontology and semantic web introductions:

- `sw:KnowledgeOrganizationArtifact`
- `sw:Taxonomy`
- `sw:KnowledgeGraph`
- `sw:Ontology`
- `sw:OntologyPrimitive`
- `sw:OntologyClass`
- `sw:OntologyIndividual`
- `sw:DatatypePropertyConcept`
- `sw:ObjectPropertyConcept`
- `sw:Axiom`
- `sw:Constraint`

### 4.3 Standards and profiles module
Models standards, profiles, and named ontology families:

- `sw:Standard`
- `sw:OntologyProfile`
- `sw:FoundationalOntology`
- `sw:Vocabulary`

### 4.4 Triplestore catalog module
Models the CSV and practical repository metadata:

- `sw:Triplestore`
- `sw:DatabaseManagementSystem`
- `sw:Organization`
- `sw:LicenseModel`
- `sw:Interface`
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`
- `sw:Feature`
- `sw:Specialization`
- `sw:DeploymentModel`

---

## 5. Core classes

### 5.1 General conceptual classes

#### `sw:Concept`
Top-level domain concept in this ontology. Used as a broad superclass for major modeled ideas.

#### `sw:InformationResource`
A resource that conveys structured knowledge, such as a vocabulary, ontology, standard, or architecture description.

#### `sw:Standard`
A formalized technical standard or specification.

#### `sw:Technology`
A technology, language, framework element, or implementation used within the semantic web ecosystem.

#### `sw:Organization`
An organization that develops, maintains, publishes, or standardizes a technology.

---

### 5.2 Semantic Web architecture classes

#### `sw:SemanticWeb`
Represents the Semantic Web as a web-of-data paradigm.

#### `sw:WebArchitecture`
A technical architecture composed of layers and technologies.

#### `sw:ArchitectureLayer`
A conceptual layer in the semantic web stack.

Subclasses:
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofLayer`
- `sw:TrustLayer`

#### `sw:IdentifierScheme`
Identifier technology such as URI or IRI.

#### `sw:CharacterSetStandard`
Character encoding standard such as Unicode.

#### `sw:SerializationFormat`
RDF serialization syntax such as Turtle, JSON-LD, RDF/XML.

#### `sw:DataModelTechnology`
Data model technology such as RDF or RDFS.

#### `sw:OntologyLanguage`
Ontology or schema language such as OWL or SKOS.

#### `sw:QueryLanguage`
Query language such as SPARQL.

#### `sw:RuleLanguage`
Rule language such as RIF or SWRL.

#### `sw:Reasoner`
A reasoning engine or reasoner type used for inference or consistency checking.

#### `sw:ReasoningTask`
A task performed by reasoning systems.

Subclasses:
- `sw:ClassificationTask`
- `sw:ConsistencyCheckingTask`

#### `sw:SemanticPrinciple`
A principle or assumption in semantic web logic.

Subclasses:
- `sw:OpenWorldAssumption`
- `sw:NonUniqueNameAssumption`

---

### 5.3 Ontology and knowledge organization classes

#### `sw:KnowledgeOrganizationArtifact`
A formal artifact used to organize or structure knowledge.

Subclasses:
- `sw:Taxonomy`
- `sw:KnowledgeGraph`
- `sw:Ontology`
- `sw:Vocabulary`

#### `sw:Ontology`
A formal, explicit specification of a shared conceptualization.

#### `sw:Taxonomy`
A hierarchical classification scheme focused on subclassing or parent-child structure.

#### `sw:KnowledgeGraph`
A graph of entities connected by typed relationships.

#### `sw:Vocabulary`
A named set of terms for describing resources.

#### `sw:FoundationalOntology`
A reusable upper-level or broadly applicable ontology/vocabulary family.

#### `sw:OntologyProfile`
An OWL profile or similar modeling profile.

Examples expected at data level could include EL, QL, RL.

---

### 5.4 Ontology primitives and logical components

#### `sw:OntologyPrimitive`
A building block of an ontology.

Subclasses:
- `sw:OntologyClass`
- `sw:OntologyIndividual`
- `sw:DatatypePropertyConcept`
- `sw:ObjectPropertyConcept`
- `sw:Axiom`

#### `sw:OntologyClass`
The concept of a class within an ontology.

#### `sw:OntologyIndividual`
The concept of an individual/instance.

#### `sw:DatatypePropertyConcept`
The concept of a datatype property as an ontology primitive.

#### `sw:ObjectPropertyConcept`
The concept of an object property as an ontology primitive.

#### `sw:Axiom`
A logical assertion in an ontology.

Subclasses:
- `sw:Constraint`
- `sw:PropertyCharacteristic`
- `sw:ClassRestriction`
- `sw:CardinalityConstraint`
- `sw:DisjointnessAxiom`

#### `sw:PropertyCharacteristic`
A property-level logical feature such as transitive, symmetric, functional, or inverse.

#### `sw:ClassRestriction`
A class-level restriction expressed over properties.

#### `sw:CardinalityConstraint`
A restriction on the number of values for a property.

#### `sw:DisjointnessAxiom`
An axiom stating that classes do not overlap.

---

### 5.5 Triplestore catalog classes

#### `sw:DatabaseManagementSystem`
A database management system.

#### `sw:Triplestore`
An RDF-oriented database or graph repository platform. Modeled as a subclass of `sw:DatabaseManagementSystem` and `sw:Technology`.

#### `sw:Interface`
A general access interface exposed by software.

Subclasses:
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`

This allows mixed CSV values like SPARQL, JDBC, REST, RDF4J, GraphQL, Workbench, native Java API, etc. to be represented either uniformly or more specifically.

#### `sw:LicenseModel`
A textual or structured description of software licensing.

#### `sw:Feature`
A notable capability, property, or advertised feature.

#### `sw:Specialization`
A specialized focus area of a technology or product.

#### `sw:DeploymentModel`
A deployment style such as managed service, native component, distributed analytics platform, or enterprise platform.

---

## 6. Property design

### 6.1 Labeling and descriptive properties

#### `sw:name`
Datatype property for human-readable names.

#### `sw:description`
Datatype property for descriptive text.

#### `sw:identifier`
Datatype property for local identifiers or codes when needed.

These supplement `rdfs:label` and `rdfs:comment` and are useful for importer output.

---

### 6.2 Architecture and conceptual relations

#### `sw:hasLayer`
Links a web architecture to one of its layers.

#### `sw:layerUsesTechnology`
Links an architecture layer to a technology used at that layer.

#### `sw:supportsPrinciple`
Links a semantic web or technology to a semantic principle.

#### `sw:enablesTask`
Links a technology or reasoner to a reasoning or operational task.

#### `sw:extendsTechnology`
Links one technology to another that it extends conceptually.

Useful example at data level: OWL extends RDFS, RDFS extends RDF.

#### `sw:serializedAs`
Links a data model or resource to a serialization format.

#### `sw:queriesWith`
Links a graph or system to a query language.

---

### 6.3 Ontology structure relations

#### `sw:hasPrimitive`
Links an ontology to one of its primitives.

#### `sw:definesConcept`
Links a vocabulary or ontology to a concept it defines.

#### `sw:definesProperty`
Links a vocabulary or ontology to a property it defines.

#### `sw:hasAxiom`
Links an ontology to one of its axioms.

#### `sw:hasProfile`
Links an ontology language to a profile.

#### `sw:usedFor`
Links a technology, ontology, profile, or feature to a purpose or application description.

#### `sw:contrastsWith`
Links related but distinct conceptual artifacts, such as taxonomy vs knowledge graph vs ontology.

---

### 6.4 Organization and publication relations

#### `sw:developedBy`
Links a technology or triplestore to its developer.

#### `sw:maintainedBy`
Links a technology or triplestore to its maintainer.

#### `sw:publishedBy`
Links a standard, ontology, or vocabulary to its publisher or standards body.

---

### 6.5 Triplestore-specific relations

#### `sw:hasLicenseModel`
Links a triplestore to a structured license model resource.

#### `sw:licenseText`
Stores the original CSV license field as a string.

#### `sw:offersInterface`
Links a triplestore to any interface it exposes.

#### `sw:offersAPI`
Specialized subproperty of `sw:offersInterface` for APIs.

#### `sw:offersProtocol`
Specialized subproperty of `sw:offersInterface` for protocols.

#### `sw:offersWorkbench`
Specialized subproperty of `sw:offersInterface` for workbench-style tools.

#### `sw:primaryInterfaceText`
Stores the original CSV interface field as a string.

#### `sw:hasFeature`
Links a triplestore to a feature resource.

#### `sw:hasSpecialization`
Links a triplestore to a specialization resource.

#### `sw:featureText`
Stores the original CSV feature/specialization field as a string.

#### `sw:hasDeploymentModel`
Links a system to a deployment model resource.

#### `sw:isOpenSource`
Boolean convenience property for downstream enrichment when licensing has been normalized. Not required during import if source text is ambiguous.

#### `sw:isCommercial`
Boolean convenience property for downstream enrichment when licensing has been normalized.

These booleans are optional because the CSV often expresses mixed licensing.

---

### 6.6 Identity and interoperability relations

#### `sw:equivalentResource`
An interoperability-friendly subproperty aligned with `owl:sameAs` usage expectations from the source material.

This is included because the documents explicitly discuss multiple URIs identifying the same entity.

---

## 7. Hierarchy summary

### 7.1 Class hierarchy highlights

- `sw:Technology`
  - `sw:IdentifierScheme`
  - `sw:CharacterSetStandard`
  - `sw:SerializationFormat`
  - `sw:DataModelTechnology`
  - `sw:OntologyLanguage`
  - `sw:QueryLanguage`
  - `sw:RuleLanguage`
  - `sw:Reasoner`
  - `sw:DatabaseManagementSystem`
    - `sw:Triplestore`
  - `sw:Interface`
    - `sw:API`
    - `sw:Protocol`
    - `sw:Workbench`
    - `sw:ProgrammingInterface`

- `sw:KnowledgeOrganizationArtifact`
  - `sw:Taxonomy`
  - `sw:KnowledgeGraph`
  - `sw:Ontology`
  - `sw:Vocabulary`
    - `sw:FoundationalOntology`

- `sw:OntologyPrimitive`
  - `sw:OntologyClass`
  - `sw:OntologyIndividual`
  - `sw:DatatypePropertyConcept`
  - `sw:ObjectPropertyConcept`
  - `sw:Axiom`
    - `sw:Constraint`
    - `sw:PropertyCharacteristic`
    - `sw:ClassRestriction`
    - `sw:CardinalityConstraint`
    - `sw:DisjointnessAxiom`

- `sw:ArchitectureLayer`
  - `sw:IdentifierLayer`
  - `sw:SyntaxLayer`
  - `sw:DataModelLayer`
  - `sw:OntologyLayer`
  - `sw:QueryLayer`
  - `sw:RulesLayer`
  - `sw:ProofLayer`
  - `sw:TrustLayer`

- `sw:SemanticPrinciple`
  - `sw:OpenWorldAssumption`
  - `sw:NonUniqueNameAssumption`

- `sw:ReasoningTask`
  - `sw:ClassificationTask`
  - `sw:ConsistencyCheckingTask`

### 7.2 Property hierarchy highlights

- `sw:offersAPI` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:offersProtocol` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:offersWorkbench` `rdfs:subPropertyOf` `sw:offersInterface`
- `sw:hasSpecialization` `rdfs:subPropertyOf` `sw:hasFeature`
- `sw:equivalentResource` `rdfs:subPropertyOf` `owl:sameAs`

---

## 8. Datatype choices

The CSV profile strongly supports strings for all supplied columns. The ontology therefore uses:

- `xsd:string` for names, developer/maintainer names, license text, API/interface text, and feature text,
- `xsd:boolean` only for optional normalized convenience properties `sw:isOpenSource` and `sw:isCommercial`.

No numeric or date datatypes are introduced because the source data does not justify them.

---

## 9. Constraints and modeling choices

### 9.1 Domain/range are guidance, not hard validation
RDFS domains and ranges are included for practical inferencing and query clarity, but they should be understood under open-world semantics. They help consumers and importers without imposing rigid closed-world validation.

### 9.2 Literal preservation plus normalization
For CSV import, each compound text field should be preserved exactly in literal form:

- `sw:licenseText`
- `sw:primaryInterfaceText`
- `sw:featureText`

Optionally, importers may additionally create linked resources for:

- organizations,
- licenses,
- interfaces,
- features,
- specializations,
- deployment models.

This dual strategy avoids loss of source fidelity and supports later normalization.

### 9.3 Avoiding overcommitment on licenses
The source has mixed values like `Open Source (GPLv2) / Commercial` and `Commercial / Free Edition`. Therefore the schema does not force a single controlled license taxonomy. Instead it supports:

- raw textual preservation,
- a structured `sw:LicenseModel` node if desired,
- optional booleans when a downstream process confidently derives them.

### 9.4 Avoiding overcommitment on interfaces
The `Primary API/Interfaces` column mixes protocols, APIs, query languages, frameworks, workbenches, and language bindings. The schema therefore uses a broad superclass `sw:Interface` with specialized subclasses.

---

## 10. Expected importer mapping from CSV

For each CSV row, an importer would typically create one `sw:Triplestore` resource and attach:

- `rdfs:label` and/or `sw:name` from **Triplestore Name**,
- `sw:developedBy` or `sw:maintainedBy` to an `sw:Organization` resource derived from **Developer/Maintainer**,
- `sw:licenseText` from **License Type**,
- optionally `sw:hasLicenseModel` to one or more structured `sw:LicenseModel` resources,
- `sw:primaryInterfaceText` from **Primary API/Interfaces**,
- optionally multiple `sw:offersInterface` links to interface resources,
- `sw:featureText` from **Key Features/Specializations**,
- optionally `sw:hasFeature`, `sw:hasSpecialization`, or `sw:hasDeploymentModel` links.

Because the CSV is only 11 rows and values are varied, a semi-structured import strategy is appropriate.

---

## 11. Example query patterns supported

### 11.1 Find triplestores and their maintainers
```sparql
SELECT ?store ?label ?orgLabel WHERE {
  ?store a sw:Triplestore ;
         rdfs:label ?label ;
         sw:maintainedBy ?org .
  ?org rdfs:label ?orgLabel .
}
```

### 11.2 Find triplestores exposing SPARQL or GraphQL
```sparql
SELECT ?storeLabel ?ifaceLabel WHERE {
  ?store a sw:Triplestore ;
         rdfs:label ?storeLabel ;
         sw:offersInterface ?iface .
  ?iface rdfs:label ?ifaceLabel .
  FILTER (?ifaceLabel IN ("SPARQL", "SPARQL 1.1", "GraphQL"))
}
```

### 11.3 List semantic web layers and their technologies
```sparql
SELECT ?layerLabel ?techLabel WHERE {
  ?layer a sw:ArchitectureLayer ;
         rdfs:label ?layerLabel ;
         sw:layerUsesTechnology ?tech .
  ?tech rdfs:label ?techLabel .
}
ORDER BY ?layerLabel ?techLabel
```

### 11.4 Show ontology primitives
```sparql
SELECT ?primitiveClass ?label WHERE {
  ?primitiveClass rdfs:subClassOf sw:OntologyPrimitive ;
                  rdfs:label ?label .
}
```

### 11.5 Find concepts related to reasoning
```sparql
SELECT ?thing ?label WHERE {
  ?thing sw:enablesTask sw:ClassificationTask .
  OPTIONAL { ?thing rdfs:label ?label }
}
```

---

## 12. Why this schema fits the project

This design reflects both source types:

- The markdown files are conceptual and educational, so the ontology includes classes for semantic web architecture, ontology primitives, reasoning, assumptions, standards, and profiles.
- The CSV is product-oriented, so the ontology includes concrete software catalog structures for triplestores, maintainers, licenses, interfaces, and features.

The combined result allows one graph to represent both:

- the **theory** of the Semantic Web and ontologies, and
- the **software ecosystem** used to implement those ideas.

That makes the schema suitable for documentation, linked-data publication, teaching examples, and practical triplestore comparison queries in Fuseki.

