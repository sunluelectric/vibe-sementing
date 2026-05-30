from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    db_dir: Path = ROOT_DIR / "db"
    tests_dir: Path = ROOT_DIR / "tests"
    design_requirements_path: Path = ROOT_DIR / "design-requirements.md"
    design_doc_path: Path = ROOT_DIR / "design.md"
    ontology_path: Path = ROOT_DIR / "db" / "ontology.ttl"
    instances_path: Path = ROOT_DIR / "db" / "instances.ttl"
    combined_path: Path = ROOT_DIR / "db" / "semantic_web.ttl"
    export_path: Path = ROOT_DIR / "db" / "export.ttl"
    llm_model: str = os.getenv("LLM_MODEL", "gpt-5-mini")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "90"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    fuseki_base_url: str = os.getenv("FUSEKI_BASE_URL", "http://localhost:3030")
    fuseki_dataset: str = os.getenv("FUSEKI_DATASET", "semantic-web-processor")
    fuseki_home: Path = Path(
        os.getenv("FUSEKI_HOME", "/opt/apache-jena-fuseki-6.1.0")
    )
    fuseki_run_dir: Path = ROOT_DIR / "db" / "fuseki-run"
    fuseki_log_path: Path = ROOT_DIR / "db" / "fuseki.log"
    fuseki_start_timeout_seconds: int = int(
        os.getenv("FUSEKI_START_TIMEOUT_SECONDS", "20")
    )
    ontology_namespace: str = os.getenv(
        "ONTOLOGY_NAMESPACE", "http://example.org/semantic-web#"
    )
    ontology_graph_uri: str = os.getenv(
        "ONTOLOGY_GRAPH_URI", "http://example.org/semantic-web/graph/ontology"
    )
    data_graph_uri: str = os.getenv(
        "DATA_GRAPH_URI", "http://example.org/semantic-web/graph/data"
    )
    app_host: str = os.getenv("VIEWER_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("VIEWER_PORT", "8000"))
    designer_iterations: int = int(os.getenv("DESIGNER_ITERATIONS", "2"))
    importer_iterations: int = int(os.getenv("IMPORTER_ITERATIONS", "2"))

    @property
    def sparql_query_url(self) -> str:
        return f"{self.fuseki_base_url.rstrip('/')}/{self.fuseki_dataset}/query"

    @property
    def sparql_update_url(self) -> str:
        return f"{self.fuseki_base_url.rstrip('/')}/{self.fuseki_dataset}/update"

    @property
    def graph_store_url(self) -> str:
        return f"{self.fuseki_base_url.rstrip('/')}/{self.fuseki_dataset}/data"


def get_settings() -> Settings:
    settings = Settings()
    settings.db_dir.mkdir(parents=True, exist_ok=True)
    settings.tests_dir.mkdir(parents=True, exist_ok=True)
    return settings
