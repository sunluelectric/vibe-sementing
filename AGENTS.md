# Semantic Web Processor

This project is developed jointly by sunlu.electric@github and Codex using Python.

## Introduction

## Project Overview

This project is a one-stop solution to design, insert and query semantic web based on user input structured and unstructured data.

Important domain boundary:
* The DnD adventure is example input data only. The application is a general-purpose semantic web designer, importer, and viewer.
* Do not hardcode DnD-specific classes, properties, namespaces, validation rules, prompts, graph URIs, SPARQL queries, importer behavior, or viewer behavior in `./src/*`.
* Product code in `./src/*` should derive ontology terms and instance mappings from `./design-requirements.md`, `./data/*`, generated `./design.md`, generated ontology files, and runtime configuration.
* If development needs checks against the currently generated DnD example result, put those checks in scripts or tests under `./tests/*`, not in reusable product modules.
* The default configuration and prompts should stay domain-neutral. Domain-specific examples may appear in documentation or generated artifacts, but should not become assumptions in the application code.

The project includes three independent executable codes. They are:
* Semantic web designer (`./src/designer/*`): an OpenAI Agents SDK workflow that consumes the design requirement and data, checks or starts Apache Jena Fuseki, uses direct OpenAI API calls as controlled design tools, iteratively validates RDF/RDFS output, writes intermediate Turtle for testing and review, and implements the ontology in Fuseki using Jena-compatible graph operations.
* Semantic web importer (`./src/importer/*`): an OpenAI Agents SDK tool that interprets the semantic web design and then consumes the data and fill instances into the semantic web according to the data.
* Semantic web viewer (`./src/viewer/*`): an chatbot AI agent with browser-based UI, that consumes the user questions from the UI, and based on the questions query the semantic web, and based on the returned results answer the questions; there are also options on the UI that allow the user to export and download the semantic web in Turtle (`.ttl`) or other commonly seen formats, in which case the semantic web viewer needs to (use the triplestore's capability to) convert the data into the required format.

## Current Development State

* The semantic web designer milestone is complete, tested, and documented.
* The original designer milestone and later verification updates for progressive `./design.md` logging, compact prompting, generic product-code validation, and the default model have been committed.
* The designer has produced `./design.md` and `./db/ontology.ttl`.
* The designer has loaded the ontology into Fuseki as named graph `http://example.org/dnd-adventure/graph/ontology`.
* The latest verified designer run used model `gpt-5-mini`, produced 188 RDF triples, 15 RDFS classes, and 28 RDF properties, and was verified by querying Fuseki directly.
* The semantic web importer milestone is complete, tested, documented, and committed.
* The importer has produced `./db/instances.ttl` and `./db/semantic_web.ttl`.
* The importer has loaded the instance graph into Fuseki as named graph `http://example.org/semantic-web/graph/data`, unless overridden by `.env`.
* The latest verified importer run used model `gpt-5-mini`, produced 186 instance RDF triples and 374 combined triples, and was verified with local RDF/SPARQL checks.
* The designer and importer are independent executables. The importer can run on another machine from a handoff package containing `./design.md`, `./db/ontology.ttl`, and the source `./data/*`. Do not rely on in-memory Fuseki process state as the portable handoff artifact; use Turtle files or an equivalent export.
* Future importer improvement: support optional ontology inspection by querying Fuseki when available, while retaining `./db/ontology.ttl` as the portable fallback and handoff artifact.
* Long-term graph handoff should be database/query-first rather than whole-Turtle-prompt-first. Turtle files are useful as portable artifacts, tests, exports, and fallbacks, but future agents should query Fuseki or local RDF graphs for relevant schema/data slices instead of sending large Turtle files wholesale to an LLM.
* The viewer has not been started.
* Next work should follow `./PROGRESS.md`, starting at **Milestone 3: Viewer Framework**.

## Setups and Requirements

### Preparations that have been carried out

* `git` is installed on the server; `git init` has been performed to the project folder
* `uv` is installed on the server; `uv init` has been performed to the project folder
* Apache Jena Fuseki is used as the triplesotre and has been installed on the server. Details are given in **Locations of Files**
* OpenAI API key has been prepared and saved in the project folder under `.env`. Details are given in **Locations of Files**
* Both the semantic web designer and the semantic viewer will need to access unstructured data. It may happen that the files size or numbers are large. In those cases, the agentic AI frameworks may need to chunk the documents and perform semantic search. A semantic search tool is provided in `./tools/semantic-search/*`. Read the codes and documents there to understand how to use it as a tool. 
  * Note: modify the semantic search tool if needed. For example, the semantic search tool supports PDF and HTML files as inputs. Consider also add supports for plain texts and markdown files.
  * The semantic search tool comes with a .env file, inside which are configurations for the tool, such as a seperate `OPENAI_API_KEY` of the tool, choice of models and embedding methods, locations of files by default, etc. Modify them if needed. For example, the locaiton of files definately needs to be changed.

### Locations of Files

* OpenAI API key and LLM instances in agentic AI frameworks
  * The project develops and deploys multiple agentic AI frameworks for semantic web design, data insertation and result query. LLM will be used in the agentic AI frameworks
  * OpenAI API Key can be found in `.env` file, as environment variable `OPENAI_API_KEY`
  * The current default model in `src/common/config.py` is `gpt-5-mini`, chosen to reduce latency and cost for the compact designer workflow. Override it with `LLM_MODEL` in `.env` when needed.

* Design requirements
  * Design requirements is given in `./design-requirements.md`

* Data
  * The data to be used for semantic web design and insertation is saved in `./data/*`
  * There are only two types of data: unstructured data in markdown; structured data in CSV

* Semantic web database
  * Semantic web should be stored in `./db/*`

* Triplestore
  * Apache Jena Fuseki is installed on the server
  * The location is `/opt/apache-jena-fuseki-6.1.0`
  * Designer and importer workflows stop Fuseki automatically only when the workflow started Fuseki itself. If Fuseki was already running before the workflow, leave it running.
  * The tree is given by
  ```
  .
    ├── fuseki-backup
    ├── fuseki-plain
    ├── fuseki-server
    ├── fuseki-server.bat
    ├── fuseki-server.jar
    ├── LICENSE
    ├── log4j2.properties
    ├── NOTICE
    ├── README
    ├── run
    │   ├── backups
    │   ├── config.ttl
    │   ├── configuration
    │   ├── databases
    │   ├── logs
    │   ├── shiro.ini
    │   ├── system_files
    │   └── templates
    │       ├── config-mem
    │       ├── config-tdb
    │       ├── config-tdb2
    │       ├── config-tdb2-dir
    │       ├── config-tdb2-mem
    │       ├── config-tdb-dir
    │       └── config-tdb-mem
    └── service
        └── service
            ├── fuseki.initd
            └── fuseki.service
  ```

### Requirements for semantic web designer

* Use OpenAI Agents SDK as the overall workflow framework.
* Do not use CrewAI for the designer.
* The actual ontology design step can use direct OpenAI API calls, but those calls should be controlled by the designer workflow and wrapped as workflow tools or equivalent internal steps.
* The designer workflow should include at least these stages:
  * Check whether Apache Jena Fuseki is available.
  * Start Apache Jena Fuseki when needed and possible.
  * Read `./design-requirements.md` and `./data/*`.
  * Generate a compact semantic web design and ontology.
  * Validate the generated ontology with RDF parsing and project-specific checks.
  * Iterate the design a few times, using validation feedback to improve quality.
  * Write `./design.md` progressively while the design is running, then leave the final design at the top and append a generation log for human review and for the importer.
  * Write Turtle (`.ttl`) only as an intermediate artifact for testing, review, fallback, and Jena loading.
  * Implement the ontology in Apache Jena Fuseki using Jena-compatible graph operations.
* Focus mainly on RDF and RDFS; OWL can be used but it is not required. In other words, implement class and property hierarchy, but not necessarily implementing complicated OWL-defined class and properties
* Keep the first-pass ontology compact. The current designer prompt asks for about 10 to 16 classes, 15 to 28 properties, and fewer than 220 triples.
* Iteratively improve the design
* Implement the design to the semantic web, with the installed triplestore Apache Jena Fuseki
* Document the design in `./design.md`; later the semantic web importer agentic AI framework will read the document, using which to understand the semantic web design, so that it can insert data into it

### Requirements for semantic web importer

* Understand the semantic web design, either by querying the database, or by reading `./design.md`, or both.
* Read files in `./data/*`, understand them, and insert the data into the semantic web.
* Do not change the semantic web structure designed by semantic web designer. Try to fit the instances into it.

### Requirements for semantic web viewer

* Understand the semtic web design, either by querying the database, or by reading `./design.md`, or both.
* When started, a browser-based UI should pop up, inside which is a chatbot. The user can interact with the chatbot and ask questions about the data in the semantic web. The semantic web viewer should query the semantic web and answer the questions accordingly.
* The semantic web can be exported and downloaded from the UI. For example, there can be a button on the UI that says `Export as Turtle`, and let the user download the semantic web as Turtle.

### Other requirements

* Plan then implement. Save the plan in `./PROGRESS.md`. Carry out the steps one by one according to the plan. After finishing each step, checkbox in `./PROGRESS.md`.
* Test after each step before checking the checkbox.
* Update `README.md` with detailed implementation and explanation after milestones.
* Perform `git add` and `git commit` after milestones.
* Do NOT use emoji in any document, including `./design.md`, `./PROGRESS.md`, `README.md`, and any other documents.
* Intermediate files and testing scripts can be saved at `./tests/*`.

## Example: Semantic web for a DnD game

The following is a use case of the project. It helps Codex understand the purpose, input/output and flow of the project execution.
