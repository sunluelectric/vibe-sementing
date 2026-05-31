Design for design.md

Title
------
Compact RDFS schema for a probability / statistics / data-science notebook

Purpose and scope
------------------
This small RDFS schema (RDF + RDFS only) is designed to capture the core
concepts from a notebook on probability, statistics and data science.
The goal is a compact, practical vocabulary that supports importing the
notebook's knowledge into an RDF triplestore (e.g., Apache Jena Fuseki) and
answering basic queries such as:
- which distributions have parameter "µ"?
- give the PDF/PMF formula for Poisson distribution
- which estimators implement MLE or are implemented in R/Python
- which theorems assume iid and finite variance

Design principles and tradeoffs
-------------------------------
- Minimal and practical: only core concepts needed for import and queries
  (distributions, parameters, random variables, statistics, estimators,
  hypothesis tests, theorems, tools, documents, and expressions).
- RDFS-only (no OWL) to keep the schema lightweight and widely compatible.
- Broad reusable properties (hasParameter, hasPDF, implementedIn) rather
  than many one-off properties.
- Named distributions are modeled as subclasses of Distribution so both the
  family-level and parameterized instances can be added later.
- Mathematical formulas are represented by a simple MathematicalExpression
  node that can store LaTeX/MathML/code strings. This avoids forcing a
  particular math serialization now.
- Simple numeric properties use xsd numeric types; numeric constraints
  (e.g., p in [0,1]) are documented, to be enforced later with validation
  (SHACL) if desired.

Overview of classes
--------------------
(All classes use the base namespace http://example.org/semantic-web#)

- MathematicalEntity
  - A lightweight root class for domain items. Useful as a general type for
    things described in the notebook.

- Distribution (subclass of MathematicalEntity)
  - Represents a probability distribution family.

- ContinuousDistribution, DiscreteDistribution (subclasses of Distribution)
  - Shallow subclassing to separate continuous vs discrete families.

- RandomVariable
  - A random variable; linked to a Distribution via sw:hasDistribution.

- Parameter
  - Parameters of distributions/statistical models (µ, σ², λ, p, n, ...).
  - Use sw:parameterSymbol (string) to hold the symbol name and
    sw:parameterValue (xsd:double) for numeric values (when known).

- Statistic
  - Sample statistics or test statistics (sample mean, variance, t-stat).
  - Linked to the random variable via sw:computedFrom.

- Estimator
  - Estimators (MLE, BayesianEstimator, etc.). Use sw:estimates to point
    at the Parameter(s). Use sw:implementedIn to link to software.

- HypothesisTest
  - Represents a hypothesis test; has p-value (sw:hasPValue), significance
    level (sw:hasSignificanceLevel) and a linked test-statistic
    (sw:hasTestStatistic).

- ConfidenceInterval
  - Confidence interval artefact with a confidence level (sw:hasConfidenceLevel).

- Theorem
  - Mathematical/statistical theorems (Central Limit Theorem, Law of Large Numbers).
  - Use sw:hasStatement (text) and sw:assumesCondition to link to Conditions.

- Condition
  - Assumptions or conditions referenced by theorems (e.g., iid, finite variance).

- MathematicalExpression
  - Holds formula text (LaTeX, MathML, code snippet) via sw:hasFormula.

- Tool
  - Software tools / packages (R, Python, numpy, scipy, R packages).

- Document
  - Documents, notebook pages or PDFs from the source; useful for provenance.

- SemanticWebConcept
  - Represents mentions of RDF/RDFS/OWL/semantic-web concepts inside the
    notebook (keeps the ontology aware of the notebook's meta-discussion).

Core properties (selected)
---------------------------
- sw:hasDistribution (RandomVariable -> Distribution)
  - Connects a random variable to its distribution family.

- sw:hasParameter (Distribution -> Parameter)
  - Links a distribution family to its parameters.

- sw:parameterSymbol (Parameter -> xsd:string)
  - Symbol used in the notebook (e.g., "µ", "σ2", "λ", "p").

- sw:parameterValue (Parameter -> xsd:double)
  - Numeric value when available.

- sw:hasMean, sw:hasVariance (Distribution -> xsd:double)
  - Common numeric moments recorded at distribution-level when known.

- sw:hasPDF, sw:hasPMF, sw:hasCDF (Distribution -> MathematicalExpression)
  - Links to formulas for PDF/PMF/CDF; expression literals can hold LaTeX
    or executable code.

- sw:isSpecialCaseOf (Distribution -> Distribution)
  - e.g., Poisson as a limiting case of Binomial (documented relation).

- sw:computedFrom (Statistic -> RandomVariable)
  - Which RV or sample a statistic is computed from.

- sw:estimates (Estimator -> Parameter)
  - What parameter(s) an estimator targets (MLE, Bayesian, ...).

- sw:implementedIn (Estimator -> Tool)
  - Links estimators/methods to software implementations (R/Python packages).

- sw:hasFormula (MathematicalExpression -> xsd:string)
  - The textual/formal representation of formulas (LaTeX, MathML, or code).

- sw:hasStatement (Theorem -> xsd:string)
  - Short human-readable theorem statement.

- sw:assumesCondition (Theorem -> Condition)
  - The theorem's assumptions (iid, finite variance, etc.).

- sw:hasPValue, sw:hasSignificanceLevel (HypothesisTest -> xsd:double)
  - Numeric properties for testing.

- sw:hasTestStatistic (HypothesisTest -> Statistic)
  - The statistic used in the test.

- sw:hasConfidenceLevel (ConfidenceInterval -> xsd:double)
  - Confidence level of an interval (e.g., 0.95).

- sw:documentedIn (MathematicalEntity -> Document)
  - Provenance: where the concept or formula is documented in the notebook.

- sw:mentionsSemanticWebConcept (Document -> SemanticWebConcept)
  - Links documents that discuss RDF/RDFS/OWL etc.

Modeling notes and examples
---------------------------
- Named distributions (NormalDistribution, PoissonDistribution, BinomialDistribution,
  ExponentialDistribution, GammaDistribution, StudentTDistribution) are subclasses
  of Distribution. Parameter objects (with sw:parameterSymbol) connect to their
  distributions via sw:hasParameter. The exact numeric parameter value is optional.

- MathematicalExpression nodes are deliberately generic; formulas can be stored as
  LaTeX strings or as code snippets (R/Python). Any formal math serialization can be
  added later as a new literal datatype or a new property.

- Theorems include a human statement and links to Condition nodes so downstream tools
  can check applicability (e.g., whether CLT conditions hold for a given dataset).

- Numeric constraints (λ>0, σ²≥0, p in [0,1], p-values in [0,1]) are documented in
  comments; enforce them later via validation shapes (SHACL) rather than in RDFS.

SPARQL examples (illustrative)
------------------------------
- Find distributions that have a parameter symbol "µ":
  SELECT ?dist WHERE { ?dist a sw:Distribution ; sw:hasParameter ?p . ?p sw:parameterSymbol "µ" . }

- Get PDF/PMF string for PoissonDistribution:
  SELECT ?formula WHERE { sw:PoissonDistribution sw:hasPMF ?expr . ?expr sw:hasFormula ?formula }

- Find theorems that assume "iid":
  SELECT ?th WHERE { ?th a sw:Theorem ; sw:assumesCondition ?c . ?c rdfs:label "iid" }

Import guidance
----------------
- Load the Turtle schema into Fuseki (as a separate graph) before importing instance
  data representing the notebook's content.
- Instance data can create Parameter instances, Distribution instances (or use the
  named subclass IRIs), link MathematicalExpression nodes with formula strings, and
  attach provenance to Document nodes.
- Use external identifiers for named concepts where appropriate (e.g., link
  sw:NormalDistribution to external resources) via additional predicates later.

Extensibility
--------------
- Later versions may add:
  - SHACL shapes for numeric ranges and structural validation.
  - Additional classes for Sample, LikelihoodFunction, Posterior, MCMCChain.
  - Crosslinks to external vocabularies (PROV, DC, SKOS) and stable IDs (Wikidata).

Maintenance notes
------------------
- Keep the schema intentionally small; extend only when a new class or property is
  re-used across multiple notebook items.
- Prefer adding instances and links in data over adding many specialized schema terms.

License and provenance
-----------------------
- The schema uses the example.org base IRI for design purposes; in production choose
  a persistent base IRI. Document provenance (who authored/modified the schema) in
  repository metadata alongside the schema file.

## Designer Generation Log

## Retrieval Focus Planning

- Status: LLM request started
- Timestamp: 2026-05-31T14:04:39+00:00
- Max focuses: 4

## Retrieval Focus Planning Result

- Status: passed
- Focus count: 4
- Query: List named mathematical concepts and theorems in the notebook: probability, random variable, expectation, variance, distribution (normal, binomial, Poisson, exponential, gamma, t), Central Limit Theorem, Law of Large Numbers, hypothesis testing, Bayesian methods, MLE, confidence interval
- Query: Extract explicit relationships and attributes between concepts: statements of 'is a' / subclass, 'has parameter', 'has PDF/CDF/formula', 'has mean', 'has variance', 'is special case of', 'depends on', and variable/parameter names (µ, σ, λ, p)
- Query: Find references to tools, code and data artifacts: R and Python mentions, package and function names (ggplot2, pandas, numpy, seaborn, TensorFlow, scikit-learn, ggplot, read.csv), code snippets, example data frames/datasets (iris, mortgage_price), figure/table captions and code-to-figure links
- Query: Locate semantic-web examples and provenance: RDF/Turtle snippets, RDFS/OWL class/property hierarchies, namespace declarations, SPARQL query examples, blank node usage, OWL restrictions and property chains, SWRL/RIF rules, linked data/DBpedia URIs

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T14:04:58+00:00
- Query: List named mathematical concepts and theorems in the notebook: probability, random variable, expectation, variance, distribution (normal, binomial, Poisson, exponential, gamma, t), Central Limit Theorem, Law of Large Numbers, hypothesis testing, Bayesian methods, MLE, confidence interval
- Context characters: 3359

## Schema Slice Draft Result

- Status: passed
- Query: List named mathematical concepts and theorems in the notebook: probability, random variable, expectation, variance, distribution (normal, binomial, Poisson, exponential, gamma, t), Central Limit Theorem, Law of Large Numbers, hypothesis testing, Bayesian methods, MLE, confidence interval
- Notes characters: 7367

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T14:05:27+00:00
- Query: Extract explicit relationships and attributes between concepts: statements of 'is a' / subclass, 'has parameter', 'has PDF/CDF/formula', 'has mean', 'has variance', 'is special case of', 'depends on', and variable/parameter names (µ, σ, λ, p)
- Context characters: 2688

## Schema Slice Draft Result

- Status: passed
- Query: Extract explicit relationships and attributes between concepts: statements of 'is a' / subclass, 'has parameter', 'has PDF/CDF/formula', 'has mean', 'has variance', 'is special case of', 'depends on', and variable/parameter names (µ, σ, λ, p)
- Notes characters: 6783

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T14:05:59+00:00
- Query: Find references to tools, code and data artifacts: R and Python mentions, package and function names (ggplot2, pandas, numpy, seaborn, TensorFlow, scikit-learn, ggplot, read.csv), code snippets, example data frames/datasets (iris, mortgage_price), figure/table captions and code-to-figure links
- Context characters: 4842

## Schema Slice Draft Result

- Status: passed
- Query: Find references to tools, code and data artifacts: R and Python mentions, package and function names (ggplot2, pandas, numpy, seaborn, TensorFlow, scikit-learn, ggplot, read.csv), code snippets, example data frames/datasets (iris, mortgage_price), figure/table captions and code-to-figure links
- Notes characters: 8752

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T14:06:35+00:00
- Query: Locate semantic-web examples and provenance: RDF/Turtle snippets, RDFS/OWL class/property hierarchies, namespace declarations, SPARQL query examples, blank node usage, OWL restrictions and property chains, SWRL/RIF rules, linked data/DBpedia URIs
- Context characters: 4858

## Schema Slice Draft Result

- Status: passed
- Query: Locate semantic-web examples and provenance: RDF/Turtle snippets, RDFS/OWL class/property hierarchies, namespace declarations, SPARQL query examples, blank node usage, OWL restrictions and property chains, SWRL/RIF rules, linked data/DBpedia URIs
- Notes characters: 8924

# Semantic Web Designer Progress

- Model: `gpt-5-mini`
- Max attempts: 2
- Started: 2026-05-31T14:07:07+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-05-31T14:07:07+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-05-31T14:08:37+00:00
- Response characters: 19152

## Attempt 1 Validation

- Status: passed
- Triple count: 202

### Candidate Design

Design for design.md

Title
------
Compact RDFS schema for a probability / statistics / data-science notebook

Purpose and scope
------------------
This small RDFS schema (RDF + RDFS only) is designed to capture the core
concepts from a notebook on probability, statistics and data science.
The goal is a compact, practical vocabulary that supports importing the
notebook's knowledge into an RDF triplestore (e.g., Apache Jena Fuseki) and
answering basic queries such as:
- which distributions have parameter "µ"?
- give the PDF/PMF formula for Poisson distribution
- which estimators implement MLE or are implemented in R/Python
- which theorems assume iid and finite variance

Design principles and tradeoffs
-------------------------------
- Minimal and practical: only core concepts needed for import and queries
  (distributions, parameters, random variables, statistics, estimators,
  hypothesis tests, theorems, tools, documents, and expressions).
- RDFS-only (no OWL) to keep the schema lightweight and widely compatible.
- Broad reusable properties (hasParameter, hasPDF, implementedIn) rather
  than many one-off properties.
- Named distributions are modeled as subclasses of Distribution so both the
  family-level and parameterized instances can be added later.
- Mathematical formulas are represented by a simple MathematicalExpression
  node that can store LaTeX/MathML/code strings. This avoids forcing a
  particular math serialization now.
- Simple numeric properties use xsd numeric types; numeric constraints
  (e.g., p in [0,1]) are documented, to be enforced later with validation
  (SHACL) if desired.

Overview of classes
--------------------
(All classes use the base namespace http://example.org/semantic-web#)

- MathematicalEntity
  - A lightweight root class for domain items. Useful as a general type for
    things described in the notebook.

- Distribution (subclass of MathematicalEntity)
  - Represents a probability distribution family.

- ContinuousDistribution, DiscreteDistribution (subclasses of Distribution)
  - Shallow subclassing to separate continuous vs discrete families.

- RandomVariable
  - A random variable; linked to a Distribution via sw:hasDistribution.

- Parameter
  - Parameters of distributions/statistical models (µ, σ², λ, p, n, ...).
  - Use sw:parameterSymbol (string) to hold the symbol name and
    sw:parameterValue (xsd:double) for numeric values (when known).

- Statistic
  - Sample statistics or test statistics (sample mean, variance, t-stat).
  - Linked to the random variable via sw:computedFrom.

- Estimator
  - Estimators (MLE, BayesianEstimator, etc.). Use sw:estimates to point
    at the Parameter(s). Use sw:implementedIn to link to software.

- HypothesisTest
  - Represents a hypothesis test; has p-value (sw:hasPValue), significance
    level (sw:hasSignificanceLevel) and a linked test-statistic
    (sw:hasTestStatistic).

- ConfidenceInterval
  - Confidence interval artefact with a confidence level (sw:hasConfidenceLevel).

- Theorem
  - Mathematical/statistical theorems (Central Limit Theorem, Law of Large Numbers).
  - Use sw:hasStatement (text) and sw:assumesCondition to link to Conditions.

- Condition
  - Assumptions or conditions referenced by theorems (e.g., iid, finite variance).

- MathematicalExpression
  - Holds formula text (LaTeX, MathML, code snippet) via sw:hasFormula.

- Tool
  - Software tools / packages (R, Python, numpy, scipy, R packages).

- Document
  - Documents, notebook pages or PDFs from the source; useful for provenance.

- SemanticWebConcept
  - Represents mentions of RDF/RDFS/OWL/semantic-web concepts inside the
    notebook (keeps the ontology aware of the notebook's meta-discussion).

Core properties (selected)
---------------------------
- sw:hasDistribution (RandomVariable -> Distribution)
  - Connects a random variable to its distribution family.

- sw:hasParameter (Distribution -> Parameter)
  - Links a distribution family to its parameters.

- sw:parameterSymbol (Parameter -> xsd:string)
  - Symbol used in the notebook (e.g., "µ", "σ2", "λ", "p").

- sw:parameterValue (Parameter -> xsd:double)
  - Numeric value when available.

- sw:hasMean, sw:hasVariance (Distribution -> xsd:double)
  - Common numeric moments recorded at distribution-level when known.

- sw:hasPDF, sw:hasPMF, sw:hasCDF (Distribution -> MathematicalExpression)
  - Links to formulas for PDF/PMF/CDF; expression literals can hold LaTeX
    or executable code.

- sw:isSpecialCaseOf (Distribution -> Distribution)
  - e.g., Poisson as a limiting case of Binomial (documented relation).

- sw:computedFrom (Statistic -> RandomVariable)
  - Which RV or sample a statistic is computed from.

- sw:estimates (Estimator -> Parameter)
  - What parameter(s) an estimator targets (MLE, Bayesian, ...).

- sw:implementedIn (Estimator -> Tool)
  - Links estimators/methods to software implementations (R/Python packages).

- sw:hasFormula (MathematicalExpression -> xsd:string)
  - The textual/formal representation of formulas (LaTeX, MathML, or code).

- sw:hasStatement (Theorem -> xsd:string)
  - Short human-readable theorem statement.

- sw:assumesCondition (Theorem -> Condition)
  - The theorem's assumptions (iid, finite variance, etc.).

- sw:hasPValue, sw:hasSignificanceLevel (HypothesisTest -> xsd:double)
  - Numeric properties for testing.

- sw:hasTestStatistic (HypothesisTest -> Statistic)
  - The statistic used in the test.

- sw:hasConfidenceLevel (ConfidenceInterval -> xsd:double)
  - Confidence level of an interval (e.g., 0.95).

- sw:documentedIn (MathematicalEntity -> Document)
  - Provenance: where the concept or formula is documented in the notebook.

- sw:mentionsSemanticWebConcept (Document -> SemanticWebConcept)
  - Links documents that discuss RDF/RDFS/OWL etc.

Modeling notes and examples
---------------------------
- Named distributions (NormalDistribution, PoissonDistribution, BinomialDistribution,
  ExponentialDistribution, GammaDistribution, StudentTDistribution) are subclasses
  of Distribution. Parameter objects (with sw:parameterSymbol) connect to their
  distributions via sw:hasParameter. The exact numeric parameter value is optional.

- MathematicalExpression nodes are deliberately generic; formulas can be stored as
  LaTeX strings or as code snippets (R/Python). Any formal math serialization can be
  added later as a new literal datatype or a new property.

- Theorems include a human statement and links to Condition nodes so downstream tools
  can check applicability (e.g., whether CLT conditions hold for a given dataset).

- Numeric constraints (λ>0, σ²≥0, p in [0,1], p-values in [0,1]) are documented in
  comments; enforce them later via validation shapes (SHACL) rather than in RDFS.

SPARQL examples (illustrative)
------------------------------
- Find distributions that have a parameter symbol "µ":
  SELECT ?dist WHERE { ?dist a sw:Distribution ; sw:hasParameter ?p . ?p sw:parameterSymbol "µ" . }

- Get PDF/PMF string for PoissonDistribution:
  SELECT ?formula WHERE { sw:PoissonDistribution sw:hasPMF ?expr . ?expr sw:hasFormula ?formula }

- Find theorems that assume "iid":
  SELECT ?th WHERE { ?th a sw:Theorem ; sw:assumesCondition ?c . ?c rdfs:label "iid" }

Import guidance
----------------
- Load the Turtle schema into Fuseki (as a separate graph) before importing instance
  data representing the notebook's content.
- Instance data can create Parameter instances, Distribution instances (or use the
  named subclass IRIs), link MathematicalExpression nodes with formula strings, and
  attach provenance to Document nodes.
- Use external identifiers for named concepts where appropriate (e.g., link
  sw:NormalDistribution to external resources) via additional predicates later.

Extensibility
--------------
- Later versions may add:
  - SHACL shapes for numeric ranges and structural validation.
  - Additional classes for Sample, LikelihoodFunction, Posterior, MCMCChain.
  - Crosslinks to external vocabularies (PROV, DC, SKOS) and stable IDs (Wikidata).

Maintenance notes
------------------
- Keep the schema intentionally small; extend only when a new class or property is
  re-used across multiple notebook items.
- Prefer adding instances and links in data over adding many specialized schema terms.

License and provenance
-----------------------
- The schema uses the example.org base IRI for design purposes; in production choose
  a persistent base IRI. Document provenance (who authored/modified the schema) in
  repository metadata alongside the schema file.

