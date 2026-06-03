# Semantic Web Ontology Design

## 1. Purpose and scope

This ontology is designed from the supplied project materials:
- two explanatory markdown documents about the Semantic Web and ontologies
- one CSV listing commonly seen triplestores and their features

The ontology therefore covers two connected areas:
1. **conceptual Semantic Web knowledge**: core technologies, layers, ontology components, logical assumptions, reasoning tasks, standards, syntaxes, and adoption patterns
2. **triplestore catalog structure**: triplestore products, maintainers, licensing descriptions, APIs/interfaces, protocols, features, and specialization statements from the CSV

The goal is not only to model theory, but also to support practical data import and querying in Apache Jena Fuseki.

---

## 2. Design principles

### 2.1 RDF/RDFS-first
The schema is primarily expressed in RDF Schema. A small amount of OWL is used only where it clearly improves practical semantics and remains fully compatible with Jena/Fuseki, such as:
- `owl:Class`
- `owl:ObjectProperty`
- `owl:DatatypeProperty`
- `owl:NamedIndividual`
- `owl:sameAs`
- `owl:inverseOf`
- `owl:SymmetricProperty`
- `owl:TransitiveProperty`

### 2.2 Source-driven modeling
Classes and properties were created from the supplied documents and CSV, not from a generic built-in domain template. The ontology reflects terminology explicitly present in the sources, such as:
- Semantic Web
- Web of Data
- Web of Documents
- RDF, RDFS, OWL, SPARQL, Turtle, JSON-LD, RDF/XML
- ontology components: class, individual, attribute, relationship, axiom
- reasoning functions: classification and consistency checking
- assumptions: Open World Assumption, Non-Unique Name Assumption
- implementation patterns: Linked Open Data, Enterprise Knowledge Graph, Schema.org, DBpedia, Wikidata
- triplestore metadata from the CSV

### 2.3 No instance data inserted
The ontology defines schema only. It does not insert actual triplestore records or factual rows from the CSV as individuals. The importer can later create such instances using this ontology.

### 2.4 Practical typing for CSV imports
The CSV columns are all modeled as strings where they represent names, descriptions, mixed-format values, or semi-structured text. This follows the datatype guidance and avoids brittle assumptions.

---

## 3. Main modeling areas

## 3.1 Knowledge domain overview
The ontology contains these major branches:

### A. Conceptual foundations
- `sw:KnowledgeArtifact`
- `sw:Document`
- `sw:Technology`
- `sw:Standard`
- `sw:ModelingConstruct`
- `sw:Principle`
- `sw:ReasoningProcess`
- `sw:ApplicationArea`

### B. Semantic Web architecture
- `sw:SemanticArchitectureLayer`
- specialized layers such as identifier layer, syntax layer, data model layer, ontology layer, query layer, rules layer, proof layer, trust layer
- technologies and formats linked to layers

### C. Ontology structure
- `sw:Ontology`
- `sw:OntologyComponent`
- subclasses for classes, individuals, datatype properties, object properties, axioms, restrictions, taxonomies

### D. Semantic data systems
- `sw:DataStoreTechnology`
- `sw:Triplestore`
- `sw:GraphDatabase`
- `sw:KnowledgeGraphPlatform`
- `sw:Organization`
- `sw:LicenseOffering`
- `sw:InterfaceTechnology`
- `sw:Feature`

### E. Datasets and web resources
- `sw:Dataset`
- `sw:KnowledgeGraph`
- `sw:WebResource`
- `sw:IRI`

---

## 4. Core classes

## 4.1 General descriptive classes

### `sw:Entity`
Top-level domain entity for things described in the ontology.

### `sw:Concept`
Abstract conceptual unit in the domain.

### `sw:KnowledgeArtifact`
A human- or machine-oriented artifact representing knowledge, such as a document, ontology, taxonomy, dataset, or standard.

### `sw:Document`
A textual or digital document.

### `sw:SpecificationDocument`
A document that specifies a standard, language, or formal framework.

### `sw:Dataset`
A structured collection of data.

### `sw:WebResource`
A web-identifiable resource.

### `sw:Identifier`
A value or construct used to identify a resource.

### `sw:IRI`
An internationalized resource identifier.

### `sw:URI`
A URI identifier concept.

### `sw:CharacterEncoding`
Encoding systems such as Unicode.

---

## 4.2 Semantic Web architecture classes

### `sw:SemanticWeb`
The overall Web of Data paradigm.

### `sw:WebOfData`
The machine-understandable data-centric web.

### `sw:WebOfDocuments`
The traditional document-centric web.

### `sw:SemanticArchitectureLayer`
A layer in the Semantic Web stack.

Subclasses:
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofLayer`
- `sw:TrustLayer`

These support queries like:
- all technologies belonging to the query layer
- all layers above the data model layer
- all standards used in the ontology layer

---

## 4.3 Language, syntax, and standards classes

### `sw:Technology`
General technical artifact or system.

### `sw:LanguageTechnology`
A formal language used in the Semantic Web stack.

### `sw:SerializationFormat`
A syntax/format used to serialize RDF graphs.

### `sw:QueryLanguage`
A language used to query data.

### `sw:KnowledgeRepresentationLanguage`
A language for expressing structured semantics.

### `sw:Standard`
A community or formal standard.

Important subclasses and concepts:
- `sw:RDFTechnology`
- `sw:RDFSchemaTechnology`
- `sw:OWLTechnology`
- `sw:SPARQLTechnology`
- `sw:JSONLDFormat`
- `sw:TurtleFormat`
- `sw:RDFXMLFormat`
- `sw:SKOSTechnology`
- `sw:MicrodataTechnology`

---

## 4.4 Ontology structure classes

### `sw:Ontology`
A formal, explicit specification of a shared conceptualization.

### `sw:Taxonomy`
A hierarchical classification structure.

### `sw:KnowledgeGraph`
A graph of entities and relationships.

### `sw:OntologyComponent`
A component used in ontology structure.

Subclasses:
- `sw:OntologyClassComponent`
- `sw:OntologyIndividualComponent`
- `sw:DatatypePropertyComponent`
- `sw:ObjectPropertyComponent`
- `sw:AxiomComponent`
- `sw:RestrictionComponent`

### `sw:ModelingConstruct`
A broader class for conceptual constructs used in semantic modeling.

Subclasses:
- `sw:ClassConcept`
- `sw:IndividualConcept`
- `sw:AttributeConcept`
- `sw:RelationshipConcept`
- `sw:AxiomConcept`

This gives coverage for the ontology.md explanation of the five core primitives.

---

## 4.5 Logic and reasoning classes

### `sw:Principle`
A conceptual principle or assumption.

Subclasses:
- `sw:OpenWorldAssumption`
- `sw:ClosedWorldAssumption`
- `sw:NonUniqueNameAssumption`

### `sw:ReasoningProcess`
A reasoning activity.

Subclasses:
- `sw:ClassificationReasoning`
- `sw:ConsistencyChecking`

### `sw:Reasoner`
A software component that performs inference or checks consistency.

### `sw:LogicProfile`
A formal profile of an ontology language.

Subclasses:
- `sw:OWL2ELProfile`
- `sw:OWL2QLProfile`
- `sw:OWL2RLProfile`

---

## 4.6 Adoption and implementation classes

### `sw:ApplicationArea`
An area of use or deployment.

Subclasses:
- `sw:LinkedOpenData`
- `sw:EnterpriseKnowledgeGraph`
- `sw:SearchEngineKnowledgeGraph`
- `sw:DataIntegrationUseCase`
- `sw:DataVirtualizationUseCase`

### `sw:FoundationalOntology`
An upper-level or reusable ontology framework.

### `sw:Vocabulary`
A semantic vocabulary.

This supports resources such as FOAF, Dublin Core, SKOS, BFO, and Gene Ontology when imported later as instances.

---

## 4.7 Triplestore and platform classes

The CSV requires practical support for triplestore metadata.

### `sw:DataStoreTechnology`
A technology used to persist, query, or manage structured data.

### `sw:GraphDataSystem`
A graph-oriented data management system.

### `sw:Triplestore`
A database management system specialized for RDF triples.

### `sw:GraphDatabase`
A graph database technology.

### `sw:KnowledgeGraphPlatform`
A platform supporting knowledge graph management.

### `sw:Organization`
An organization such as a developer, maintainer, standards body, or vendor.

### `sw:MaintainerOrganization`
An organization responsible for maintenance.

### `sw:DeveloperOrganization`
An organization responsible for development.

### `sw:LicenseOffering`
A textual or categorized license arrangement for a product.

### `sw:InterfaceTechnology`
An API, interface, protocol, or access mechanism.

Subclasses:
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`
- `sw:QueryEndpoint`

### `sw:Feature`
A product capability or specialization.

Subclasses inspired by source descriptions:
- `sw:ReasoningFeature`
- `sw:VirtualizationFeature`
- `sw:ManagedServiceFeature`
- `sw:DistributedAnalyticsFeature`
- `sw:MultiModelFeature`
- `sw:HighPerformanceFeature`

The schema also retains general text fields so importer pipelines can preserve CSV values without over-normalizing.

---

## 5. Property design

## 5.1 General annotation and identification properties

### `sw:name`
General string name.
- Domain: `sw:Entity`
- Range: `xsd:string`

### `sw:title`
Title for knowledge artifacts or documents.
- Domain: `sw:KnowledgeArtifact`
- Range: `xsd:string`

### `sw:description`
General textual description.
- Domain: `sw:Entity`
- Range: `xsd:string`

### `sw:identifierValue`
Literal identifier content.
- Domain: `sw:Identifier`
- Range: `xsd:string`

### `sw:homepage`
Homepage URL string.
- Domain: `sw:Entity`
- Range: `xsd:anyURI`

### `sw:officialName`
Official name of an organization or formal artifact.
- Domain: `sw:Entity`
- Range: `xsd:string`

---

## 5.2 Structure and hierarchy properties

### `sw:hasComponent`
Relates a composite artifact to a component.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Entity`

### `sw:partOf`
Relates an entity to a larger entity.
- Domain: `sw:Entity`
- Range: `sw:Entity`

### `sw:hasLayer`
Relates a semantic architecture to a layer.
- Domain: `sw:SemanticWeb`
- Range: `sw:SemanticArchitectureLayer`

### `sw:supportsLayer`
Relates a technology or standard to the layer it supports.
- Domain: `sw:Technology`
- Range: `sw:SemanticArchitectureLayer`

### `sw:broaderThan`
Broader conceptual relation.
- Domain: `sw:Concept`
- Range: `sw:Concept`

### `sw:narrowerThan`
Narrower conceptual relation.
- Domain: `sw:Concept`
- Range: `sw:Concept`
- Inverse of `sw:broaderThan`

---

## 5.3 Ontology modeling properties

### `sw:definesClass`
An ontology defines a class construct.
- Domain: `sw:Ontology`
- Range: `sw:ClassConcept`

### `sw:definesPropertyConcept`
An ontology defines a property construct.
- Domain: `sw:Ontology`
- Range: `sw:Concept`

### `sw:definesAxiom`
An ontology defines an axiom.
- Domain: `sw:Ontology`
- Range: `sw:AxiomConcept`

### `sw:usesVocabulary`
A knowledge artifact uses a vocabulary.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Vocabulary`

### `sw:extendsTechnology`
A technology extends another technology.
- Domain: `sw:Technology`
- Range: `sw:Technology`

This is useful for modeling OWL extending RDF/RDFS.

---

## 5.4 Logic and reasoning properties

### `sw:assumesPrinciple`
Connects a technology or artifact to a guiding principle.
- Domain: `sw:Entity`
- Range: `sw:Principle`

### `sw:supportsReasoningProcess`
A technology or system supports a reasoning process.
- Domain: `sw:Technology`
- Range: `sw:ReasoningProcess`

### `sw:performedByReasoner`
Relates a reasoning process to a reasoner.
- Domain: `sw:ReasoningProcess`
- Range: `sw:Reasoner`

### `sw:usesProfile`
Associates an ontology or technology with an OWL profile.
- Domain: `sw:Entity`
- Range: `sw:LogicProfile`

---

## 5.5 Standards and ecosystem properties

### `sw:developedBy`
Relates a technology or artifact to its developer.
- Domain: `sw:Entity`
- Range: `sw:Organization`

### `sw:maintainedBy`
Relates a technology or artifact to its maintainer.
- Domain: `sw:Entity`
- Range: `sw:Organization`

### `sw:publishedBy`
Relates a document or standard to a publisher.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Organization`

### `sw:usedInApplicationArea`
Links a technology to practical usage areas.
- Domain: `sw:Technology`
- Range: `sw:ApplicationArea`

### `sw:integratesWith`
Relates two technologies that are used together.
- Domain: `sw:Technology`
- Range: `sw:Technology`

---

## 5.6 Triplestore catalog properties

These are especially important for the CSV import.

### `sw:triplestoreName`
String name from the CSV column.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:developerMaintainerName`
Literal developer/maintainer string exactly as provided by source data.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:licenseTypeText`
Literal license description from CSV.
- Domain: `sw:LicenseOffering`
- Range: `xsd:string`

### `sw:primaryAPIInterfacesText`
Literal API/interface description from CSV.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:keyFeaturesText`
Literal features/specializations description from CSV.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:hasLicenseOffering`
Relates a triplestore to a license offering object.
- Domain: `sw:Triplestore`
- Range: `sw:LicenseOffering`

### `sw:hasInterfaceTechnology`
Relates a triplestore to an interface or API concept.
- Domain: `sw:Triplestore`
- Range: `sw:InterfaceTechnology`

### `sw:hasFeature`
Relates a system to a feature.
- Domain: `sw:Technology`
- Range: `sw:Feature`

### `sw:specializesIn`
Relates a triplestore or platform to specialization areas.
- Domain: `sw:Technology`
- Range: `sw:Feature`

### `sw:isOpenSource`
Boolean if known through curated import logic.
- Domain: `sw:LicenseOffering`
- Range: `xsd:boolean`

### `sw:offersCommercialOption`
Boolean if known through curated import logic.
- Domain: `sw:LicenseOffering`
- Range: `xsd:boolean`

### `sw:isManagedService`
Boolean if known through curated import logic.
- Domain: `sw:Triplestore`
- Range: `xsd:boolean`

The ontology keeps both literal text properties and normalized object properties. This is important because the CSV columns are slash-separated mixed text and should not be over-interpreted during import.

---

## 6. Expected importer strategy

A practical importer can create:
- one `sw:Triplestore` individual per CSV row
- one `sw:Organization` individual for a developer/maintainer when normalization is desired
- one `sw:LicenseOffering` individual per row or per normalized license description
- optional `sw:InterfaceTechnology` individuals for SPARQL, SQL, JDBC, RDF4J, GraphQL, REST, Gremlin, openCypher, etc.
- optional `sw:Feature` individuals for advanced reasoning, managed service, virtualization, distributed analytics, and similar feature labels

For fidelity, the importer should preserve raw CSV values in:
- `sw:triplestoreName`
- `sw:developerMaintainerName`
- `sw:primaryAPIInterfacesText`
- `sw:keyFeaturesText`
- `sw:licenseTypeText`

This ensures no source information is lost even if normalization is partial.

---

## 7. Query needs supported by the schema

The design supports common SPARQL patterns such as:

### 7.1 Semantic Web concept queries
- find all technologies in the query layer
- list all serialization formats
- list all ontology components
- find all reasoning processes and the reasoners that perform them
- retrieve all principles assumed by Semantic Web artifacts

### 7.2 Ecosystem and standards queries
- list foundational ontologies and vocabularies
- find technologies that extend RDF or RDFS
- find technologies used in Linked Open Data or Enterprise Knowledge Graph contexts

### 7.3 Triplestore catalog queries
- list all triplestores and their maintainers
- find all triplestores whose raw API string mentions SPARQL
- find triplestores with managed-service licensing text
- find triplestores supporting reasoning features
- compare commercial/open-source offerings where boolean fields are curated
- list all interfaces used by triplestores once normalized

Example query patterns the schema enables:
- triplestores and their license text
- all technologies supporting the ontology layer
- all features attached to a given triplestore
- all organizations that develop or maintain triplestores

---

## 8. Constraints and modeling choices

### 8.1 Domain and range usage
The ontology provides `rdfs:domain` and `rdfs:range` for practical data quality and discoverability. These are not closed-world constraints, but they make the schema easier to query and understand.

### 8.2 Conservative datatypes
Only clearly safe datatypes are used:
- names and textual columns: `xsd:string`
- URLs: `xsd:anyURI`
- boolean indicators only where import logic may derive them reliably: `xsd:boolean`

### 8.3 Limited OWL use
OWL is used sparingly for:
- inverse properties between `sw:broaderThan` and `sw:narrowerThan`
- transitivity of broader/narrower conceptual hierarchy
- optional symmetry of `sw:integratesWith`

These choices improve semantic usefulness without making the ontology too complex for Fuseki.

---

## 9. Coverage mapping to source material

## 9.1 Covered from `ontology.md`
- ontology definition and machine-readable formalization
- classes, individuals, attributes, relationships, axioms
- taxonomy vs knowledge graph vs ontology
- OWL and profiles EL, QL, RL
- semantic reasoning: classification and consistency checking
- foundational ontologies and vocabularies

## 9.2 Covered from `semantic web.md`
- Web of Documents vs Web of Data
- Semantic Web architecture layers
- IRI/URI and Unicode
- RDF, RDFS, OWL, SPARQL
- Turtle, JSON-LD, RDF/XML
- Rules, proof, trust
- Open World Assumption and Non-Unique Name Assumption
- Schema.org, Linked Open Data, DBpedia, Wikidata, enterprise knowledge graphs

## 9.3 Covered from CSV
- triplestore product identity
- developer/maintainer
- license type
- API/interface descriptions
- key features/specializations

---

## 10. Recommended usage

Use this ontology as:
1. the schema graph loaded into Fuseki
2. the target vocabulary for a CSV-to-RDF importer
3. a base for later extension if more semantic web tools, datasets, standards, or products are added

The ontology intentionally includes both abstract conceptual modeling and practical triplestore catalog structure so the resulting knowledge graph can answer both educational and technical inventory questions.

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5.4`
- Mode: `production`
- Max attempts: 3
- Started: 2026-06-03T00:16:41+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-06-03T00:16:41+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-06-03T00:18:59+00:00
- Response characters: 43070

## JSON Repair

- Status: started
- Reason: LlmError: The model did not return a JSON object.

## JSON Repair Result

- Status: received
- Response characters: 43070

## Attempt 1 Validation

- Status: failed
- Feedback: Attempt 1 failed: LlmError: The model did not return a JSON object.

## Attempt 2

- Status: LLM request started
- Timestamp: 2026-06-03T00:20:51+00:00
- Retry feedback included: yes

## Attempt 2 Response

- Status: LLM response received
- Timestamp: 2026-06-03T00:23:11+00:00
- Response characters: 44416

## JSON Repair

- Status: started
- Reason: LlmError: The model did not return a JSON object.

## JSON Repair Result

- Status: received
- Response characters: 44201

## Attempt 2 Validation

- Status: failed
- Feedback: Attempt 2 failed: ValueError: Property http://example.org/semantic-web#description is missing rdfs:domain.

## Attempt 3

- Status: LLM request started
- Timestamp: 2026-06-03T00:25:04+00:00
- Retry feedback included: yes

## Attempt 3 Response

- Status: LLM response received
- Timestamp: 2026-06-03T00:27:20+00:00
- Response characters: 41599

## JSON Repair

- Status: started
- Reason: LlmError: The model did not return a JSON object.

## JSON Repair Result

- Status: received
- Response characters: 41547

## Attempt 3 Validation

- Status: passed
- Triple count: 554

### Candidate Design

# Semantic Web Ontology Design

## 1. Purpose and scope

This ontology is designed from the supplied project materials:
- two explanatory markdown documents about the Semantic Web and ontologies
- one CSV listing commonly seen triplestores and their features

The ontology therefore covers two connected areas:
1. **conceptual Semantic Web knowledge**: core technologies, layers, ontology components, logical assumptions, reasoning tasks, standards, syntaxes, and adoption patterns
2. **triplestore catalog structure**: triplestore products, maintainers, licensing descriptions, APIs/interfaces, protocols, features, and specialization statements from the CSV

The goal is not only to model theory, but also to support practical data import and querying in Apache Jena Fuseki.

---

## 2. Design principles

### 2.1 RDF/RDFS-first
The schema is primarily expressed in RDF Schema. A small amount of OWL is used only where it clearly improves practical semantics and remains fully compatible with Jena/Fuseki, such as:
- `owl:Class`
- `owl:ObjectProperty`
- `owl:DatatypeProperty`
- `owl:NamedIndividual`
- `owl:sameAs`
- `owl:inverseOf`
- `owl:SymmetricProperty`
- `owl:TransitiveProperty`

### 2.2 Source-driven modeling
Classes and properties were created from the supplied documents and CSV, not from a generic built-in domain template. The ontology reflects terminology explicitly present in the sources, such as:
- Semantic Web
- Web of Data
- Web of Documents
- RDF, RDFS, OWL, SPARQL, Turtle, JSON-LD, RDF/XML
- ontology components: class, individual, attribute, relationship, axiom
- reasoning functions: classification and consistency checking
- assumptions: Open World Assumption, Non-Unique Name Assumption
- implementation patterns: Linked Open Data, Enterprise Knowledge Graph, Schema.org, DBpedia, Wikidata
- triplestore metadata from the CSV

### 2.3 No instance data inserted
The ontology defines schema only. It does not insert actual triplestore records or factual rows from the CSV as individuals. The importer can later create such instances using this ontology.

### 2.4 Practical typing for CSV imports
The CSV columns are all modeled as strings where they represent names, descriptions, mixed-format values, or semi-structured text. This follows the datatype guidance and avoids brittle assumptions.

---

## 3. Main modeling areas

## 3.1 Knowledge domain overview
The ontology contains these major branches:

### A. Conceptual foundations
- `sw:KnowledgeArtifact`
- `sw:Document`
- `sw:Technology`
- `sw:Standard`
- `sw:ModelingConstruct`
- `sw:Principle`
- `sw:ReasoningProcess`
- `sw:ApplicationArea`

### B. Semantic Web architecture
- `sw:SemanticArchitectureLayer`
- specialized layers such as identifier layer, syntax layer, data model layer, ontology layer, query layer, rules layer, proof layer, trust layer
- technologies and formats linked to layers

### C. Ontology structure
- `sw:Ontology`
- `sw:OntologyComponent`
- subclasses for classes, individuals, datatype properties, object properties, axioms, restrictions, taxonomies

### D. Semantic data systems
- `sw:DataStoreTechnology`
- `sw:Triplestore`
- `sw:GraphDatabase`
- `sw:KnowledgeGraphPlatform`
- `sw:Organization`
- `sw:LicenseOffering`
- `sw:InterfaceTechnology`
- `sw:Feature`

### E. Datasets and web resources
- `sw:Dataset`
- `sw:KnowledgeGraph`
- `sw:WebResource`
- `sw:IRI`

---

## 4. Core classes

## 4.1 General descriptive classes

### `sw:Entity`
Top-level domain entity for things described in the ontology.

### `sw:Concept`
Abstract conceptual unit in the domain.

### `sw:KnowledgeArtifact`
A human- or machine-oriented artifact representing knowledge, such as a document, ontology, taxonomy, dataset, or standard.

### `sw:Document`
A textual or digital document.

### `sw:SpecificationDocument`
A document that specifies a standard, language, or formal framework.

### `sw:Dataset`
A structured collection of data.

### `sw:WebResource`
A web-identifiable resource.

### `sw:Identifier`
A value or construct used to identify a resource.

### `sw:IRI`
An internationalized resource identifier.

### `sw:URI`
A URI identifier concept.

### `sw:CharacterEncoding`
Encoding systems such as Unicode.

---

## 4.2 Semantic Web architecture classes

### `sw:SemanticWeb`
The overall Web of Data paradigm.

### `sw:WebOfData`
The machine-understandable data-centric web.

### `sw:WebOfDocuments`
The traditional document-centric web.

### `sw:SemanticArchitectureLayer`
A layer in the Semantic Web stack.

Subclasses:
- `sw:IdentifierLayer`
- `sw:SyntaxLayer`
- `sw:DataModelLayer`
- `sw:OntologyLayer`
- `sw:QueryLayer`
- `sw:RulesLayer`
- `sw:ProofLayer`
- `sw:TrustLayer`

These support queries like:
- all technologies belonging to the query layer
- all layers above the data model layer
- all standards used in the ontology layer

---

## 4.3 Language, syntax, and standards classes

### `sw:Technology`
General technical artifact or system.

### `sw:LanguageTechnology`
A formal language used in the Semantic Web stack.

### `sw:SerializationFormat`
A syntax/format used to serialize RDF graphs.

### `sw:QueryLanguage`
A language used to query data.

### `sw:KnowledgeRepresentationLanguage`
A language for expressing structured semantics.

### `sw:Standard`
A community or formal standard.

Important subclasses and concepts:
- `sw:RDFTechnology`
- `sw:RDFSchemaTechnology`
- `sw:OWLTechnology`
- `sw:SPARQLTechnology`
- `sw:JSONLDFormat`
- `sw:TurtleFormat`
- `sw:RDFXMLFormat`
- `sw:SKOSTechnology`
- `sw:MicrodataTechnology`

---

## 4.4 Ontology structure classes

### `sw:Ontology`
A formal, explicit specification of a shared conceptualization.

### `sw:Taxonomy`
A hierarchical classification structure.

### `sw:KnowledgeGraph`
A graph of entities and relationships.

### `sw:OntologyComponent`
A component used in ontology structure.

Subclasses:
- `sw:OntologyClassComponent`
- `sw:OntologyIndividualComponent`
- `sw:DatatypePropertyComponent`
- `sw:ObjectPropertyComponent`
- `sw:AxiomComponent`
- `sw:RestrictionComponent`

### `sw:ModelingConstruct`
A broader class for conceptual constructs used in semantic modeling.

Subclasses:
- `sw:ClassConcept`
- `sw:IndividualConcept`
- `sw:AttributeConcept`
- `sw:RelationshipConcept`
- `sw:AxiomConcept`

This gives coverage for the ontology.md explanation of the five core primitives.

---

## 4.5 Logic and reasoning classes

### `sw:Principle`
A conceptual principle or assumption.

Subclasses:
- `sw:OpenWorldAssumption`
- `sw:ClosedWorldAssumption`
- `sw:NonUniqueNameAssumption`

### `sw:ReasoningProcess`
A reasoning activity.

Subclasses:
- `sw:ClassificationReasoning`
- `sw:ConsistencyChecking`

### `sw:Reasoner`
A software component that performs inference or checks consistency.

### `sw:LogicProfile`
A formal profile of an ontology language.

Subclasses:
- `sw:OWL2ELProfile`
- `sw:OWL2QLProfile`
- `sw:OWL2RLProfile`

---

## 4.6 Adoption and implementation classes

### `sw:ApplicationArea`
An area of use or deployment.

Subclasses:
- `sw:LinkedOpenData`
- `sw:EnterpriseKnowledgeGraph`
- `sw:SearchEngineKnowledgeGraph`
- `sw:DataIntegrationUseCase`
- `sw:DataVirtualizationUseCase`

### `sw:FoundationalOntology`
An upper-level or reusable ontology framework.

### `sw:Vocabulary`
A semantic vocabulary.

This supports resources such as FOAF, Dublin Core, SKOS, BFO, and Gene Ontology when imported later as instances.

---

## 4.7 Triplestore and platform classes

The CSV requires practical support for triplestore metadata.

### `sw:DataStoreTechnology`
A technology used to persist, query, or manage structured data.

### `sw:GraphDataSystem`
A graph-oriented data management system.

### `sw:Triplestore`
A database management system specialized for RDF triples.

### `sw:GraphDatabase`
A graph database technology.

### `sw:KnowledgeGraphPlatform`
A platform supporting knowledge graph management.

### `sw:Organization`
An organization such as a developer, maintainer, standards body, or vendor.

### `sw:MaintainerOrganization`
An organization responsible for maintenance.

### `sw:DeveloperOrganization`
An organization responsible for development.

### `sw:LicenseOffering`
A textual or categorized license arrangement for a product.

### `sw:InterfaceTechnology`
An API, interface, protocol, or access mechanism.

Subclasses:
- `sw:API`
- `sw:Protocol`
- `sw:Workbench`
- `sw:ProgrammingInterface`
- `sw:QueryEndpoint`

### `sw:Feature`
A product capability or specialization.

Subclasses inspired by source descriptions:
- `sw:ReasoningFeature`
- `sw:VirtualizationFeature`
- `sw:ManagedServiceFeature`
- `sw:DistributedAnalyticsFeature`
- `sw:MultiModelFeature`
- `sw:HighPerformanceFeature`

The schema also retains general text fields so importer pipelines can preserve CSV values without over-normalizing.

---

## 5. Property design

## 5.1 General annotation and identification properties

### `sw:name`
General string name.
- Domain: `sw:Entity`
- Range: `xsd:string`

### `sw:title`
Title for knowledge artifacts or documents.
- Domain: `sw:KnowledgeArtifact`
- Range: `xsd:string`

### `sw:description`
General textual description.
- Domain: `sw:Entity`
- Range: `xsd:string`

### `sw:identifierValue`
Literal identifier content.
- Domain: `sw:Identifier`
- Range: `xsd:string`

### `sw:homepage`
Homepage URL string.
- Domain: `sw:Entity`
- Range: `xsd:anyURI`

### `sw:officialName`
Official name of an organization or formal artifact.
- Domain: `sw:Entity`
- Range: `xsd:string`

---

## 5.2 Structure and hierarchy properties

### `sw:hasComponent`
Relates a composite artifact to a component.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Entity`

### `sw:partOf`
Relates an entity to a larger entity.
- Domain: `sw:Entity`
- Range: `sw:Entity`

### `sw:hasLayer`
Relates a semantic architecture to a layer.
- Domain: `sw:SemanticWeb`
- Range: `sw:SemanticArchitectureLayer`

### `sw:supportsLayer`
Relates a technology or standard to the layer it supports.
- Domain: `sw:Technology`
- Range: `sw:SemanticArchitectureLayer`

### `sw:broaderThan`
Broader conceptual relation.
- Domain: `sw:Concept`
- Range: `sw:Concept`

### `sw:narrowerThan`
Narrower conceptual relation.
- Domain: `sw:Concept`
- Range: `sw:Concept`
- Inverse of `sw:broaderThan`

---

## 5.3 Ontology modeling properties

### `sw:definesClass`
An ontology defines a class construct.
- Domain: `sw:Ontology`
- Range: `sw:ClassConcept`

### `sw:definesPropertyConcept`
An ontology defines a property construct.
- Domain: `sw:Ontology`
- Range: `sw:Concept`

### `sw:definesAxiom`
An ontology defines an axiom.
- Domain: `sw:Ontology`
- Range: `sw:AxiomConcept`

### `sw:usesVocabulary`
A knowledge artifact uses a vocabulary.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Vocabulary`

### `sw:extendsTechnology`
A technology extends another technology.
- Domain: `sw:Technology`
- Range: `sw:Technology`

This is useful for modeling OWL extending RDF/RDFS.

---

## 5.4 Logic and reasoning properties

### `sw:assumesPrinciple`
Connects a technology or artifact to a guiding principle.
- Domain: `sw:Entity`
- Range: `sw:Principle`

### `sw:supportsReasoningProcess`
A technology or system supports a reasoning process.
- Domain: `sw:Technology`
- Range: `sw:ReasoningProcess`

### `sw:performedByReasoner`
Relates a reasoning process to a reasoner.
- Domain: `sw:ReasoningProcess`
- Range: `sw:Reasoner`

### `sw:usesProfile`
Associates an ontology or technology with an OWL profile.
- Domain: `sw:Entity`
- Range: `sw:LogicProfile`

---

## 5.5 Standards and ecosystem properties

### `sw:developedBy`
Relates a technology or artifact to its developer.
- Domain: `sw:Entity`
- Range: `sw:Organization`

### `sw:maintainedBy`
Relates a technology or artifact to its maintainer.
- Domain: `sw:Entity`
- Range: `sw:Organization`

### `sw:publishedBy`
Relates a document or standard to a publisher.
- Domain: `sw:KnowledgeArtifact`
- Range: `sw:Organization`

### `sw:usedInApplicationArea`
Links a technology to practical usage areas.
- Domain: `sw:Technology`
- Range: `sw:ApplicationArea`

### `sw:integratesWith`
Relates two technologies that are used together.
- Domain: `sw:Technology`
- Range: `sw:Technology`

---

## 5.6 Triplestore catalog properties

These are especially important for the CSV import.

### `sw:triplestoreName`
String name from the CSV column.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:developerMaintainerName`
Literal developer/maintainer string exactly as provided by source data.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:licenseTypeText`
Literal license description from CSV.
- Domain: `sw:LicenseOffering`
- Range: `xsd:string`

### `sw:primaryAPIInterfacesText`
Literal API/interface description from CSV.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:keyFeaturesText`
Literal features/specializations description from CSV.
- Domain: `sw:Triplestore`
- Range: `xsd:string`

### `sw:hasLicenseOffering`
Relates a triplestore to a license offering object.
- Domain: `sw:Triplestore`
- Range: `sw:LicenseOffering`

### `sw:hasInterfaceTechnology`
Relates a triplestore to an interface or API concept.
- Domain: `sw:Triplestore`
- Range: `sw:InterfaceTechnology`

### `sw:hasFeature`
Relates a system to a feature.
- Domain: `sw:Technology`
- Range: `sw:Feature`

### `sw:specializesIn`
Relates a triplestore or platform to specialization areas.
- Domain: `sw:Technology`
- Range: `sw:Feature`

### `sw:isOpenSource`
Boolean if known through curated import logic.
- Domain: `sw:LicenseOffering`
- Range: `xsd:boolean`

### `sw:offersCommercialOption`
Boolean if known through curated import logic.
- Domain: `sw:LicenseOffering`
- Range: `xsd:boolean`

### `sw:isManagedService`
Boolean if known through curated import logic.
- Domain: `sw:Triplestore`
- Range: `xsd:boolean`

The ontology keeps both literal text properties and normalized object properties. This is important because the CSV columns are slash-separated mixed text and should not be over-interpreted during import.

---

## 6. Expected importer strategy

A practical importer can create:
- one `sw:Triplestore` individual per CSV row
- one `sw:Organization` individual for a developer/maintainer when normalization is desired
- one `sw:LicenseOffering` individual per row or per normalized license description
- optional `sw:InterfaceTechnology` individuals for SPARQL, SQL, JDBC, RDF4J, GraphQL, REST, Gremlin, openCypher, etc.
- optional `sw:Feature` individuals for advanced reasoning, managed service, virtualization, distributed analytics, and similar feature labels

For fidelity, the importer should preserve raw CSV values in:
- `sw:triplestoreName`
- `sw:developerMaintainerName`
- `sw:primaryAPIInterfacesText`
- `sw:keyFeaturesText`
- `sw:licenseTypeText`

This ensures no source information is lost even if normalization is partial.

---

## 7. Query needs supported by the schema

The design supports common SPARQL patterns such as:

### 7.1 Semantic Web concept queries
- find all technologies in the query layer
- list all serialization formats
- list all ontology components
- find all reasoning processes and the reasoners that perform them
- retrieve all principles assumed by Semantic Web artifacts

### 7.2 Ecosystem and standards queries
- list foundational ontologies and vocabularies
- find technologies that extend RDF or RDFS
- find technologies used in Linked Open Data or Enterprise Knowledge Graph contexts

### 7.3 Triplestore catalog queries
- list all triplestores and their maintainers
- find all triplestores whose raw API string mentions SPARQL
- find triplestores with managed-service licensing text
- find triplestores supporting reasoning features
- compare commercial/open-source offerings where boolean fields are curated
- list all interfaces used by triplestores once normalized

Example query patterns the schema enables:
- triplestores and their license text
- all technologies supporting the ontology layer
- all features attached to a given triplestore
- all organizations that develop or maintain triplestores

---

## 8. Constraints and modeling choices

### 8.1 Domain and range usage
The ontology provides `rdfs:domain` and `rdfs:range` for practical data quality and discoverability. These are not closed-world constraints, but they make the schema easier to query and understand.

### 8.2 Conservative datatypes
Only clearly safe datatypes are used:
- names and textual columns: `xsd:string`
- URLs: `xsd:anyURI`
- boolean indicators only where import logic may derive them reliably: `xsd:boolean`

### 8.3 Limited OWL use
OWL is used sparingly for:
- inverse properties between `sw:broaderThan` and `sw:narrowerThan`
- transitivity of broader/narrower conceptual hierarchy
- optional symmetry of `sw:integratesWith`

These choices improve semantic usefulness without making the ontology too complex for Fuseki.

---

## 9. Coverage mapping to source material

## 9.1 Covered from `ontology.md`
- ontology definition and machine-readable formalization
- classes, individuals, attributes, relationships, axioms
- taxonomy vs knowledge graph vs ontology
- OWL and profiles EL, QL, RL
- semantic reasoning: classification and consistency checking
- foundational ontologies and vocabularies

## 9.2 Covered from `semantic web.md`
- Web of Documents vs Web of Data
- Semantic Web architecture layers
- IRI/URI and Unicode
- RDF, RDFS, OWL, SPARQL
- Turtle, JSON-LD, RDF/XML
- Rules, proof, trust
- Open World Assumption and Non-Unique Name Assumption
- Schema.org, Linked Open Data, DBpedia, Wikidata, enterprise knowledge graphs

## 9.3 Covered from CSV
- triplestore product identity
- developer/maintainer
- license type
- API/interface descriptions
- key features/specializations

---

## 10. Recommended usage

Use this ontology as:
1. the schema graph loaded into Fuseki
2. the target vocabulary for a CSV-to-RDF importer
3. a base for later extension if more semantic web tools, datasets, standards, or products are added

The ontology intentionally includes both abstract conceptual modeling and practical triplestore catalog structure so the resulting knowledge graph can answer both educational and technical inventory questions.

