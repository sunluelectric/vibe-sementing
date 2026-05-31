from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=True)


def _mode() -> str:
    value = os.getenv("SEMANTIC_WEB_MODE", "test").strip().lower()
    if value in {"production", "prod"}:
        return "production"
    return "test"


def _mode_default(test_value: str, production_value: str) -> str:
    return production_value if _mode() == "production" else test_value


def _env_int(name: str, test_value: int, production_value: int) -> int:
    return int(os.getenv(name, _mode_default(str(test_value), str(production_value))))


def _llm_model() -> str:
    return os.getenv("LLM_MODEL", _mode_default("gpt-5-mini", "gpt-5.5"))


def _semantic_search_enabled() -> bool:
    return os.getenv("SEMANTIC_SEARCH_ENABLED", "true").lower() not in {"0", "false", "no"}


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    db_dir: Path = ROOT_DIR / "db"
    tests_dir: Path = ROOT_DIR / "tests"
    design_requirements_path: Path = ROOT_DIR / "design-requirements.md"
    design_doc_path: Path = ROOT_DIR / "design.md"
    import_doc_path: Path = ROOT_DIR / "import.md"
    ontology_path: Path = ROOT_DIR / "db" / "ontology.ttl"
    instances_path: Path = ROOT_DIR / "db" / "instances.ttl"
    combined_path: Path = ROOT_DIR / "db" / "semantic_web.ttl"
    export_path: Path = ROOT_DIR / "db" / "export.ttl"
    viewer_chat_dir: Path = ROOT_DIR / "chat" / "viewer"
    semantic_web_mode: str = field(default_factory=_mode)
    llm_model: str = field(default_factory=_llm_model)
    llm_timeout_seconds: int = field(default_factory=lambda: _env_int("LLM_TIMEOUT_SECONDS", 90, 240))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    fuseki_base_url: str = field(default_factory=lambda: os.getenv("FUSEKI_BASE_URL", "http://localhost:3030"))
    fuseki_dataset: str = field(default_factory=lambda: os.getenv("FUSEKI_DATASET", "semantic-web-processor"))
    fuseki_home: Path = field(default_factory=lambda: Path(os.getenv("FUSEKI_HOME", "/opt/apache-jena-fuseki-6.1.0")))
    fuseki_run_dir: Path = ROOT_DIR / "db" / "fuseki-run"
    fuseki_data_dir: Path = field(default_factory=lambda: Path(os.getenv("FUSEKI_DATA_DIR", str(ROOT_DIR / "db" / "fuseki-data"))))
    fuseki_log_path: Path = ROOT_DIR / "db" / "fuseki.log"
    fuseki_start_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("FUSEKI_START_TIMEOUT_SECONDS", "20")))
    ontology_namespace: str = field(default_factory=lambda: os.getenv("ONTOLOGY_NAMESPACE", "http://example.org/semantic-web#"))
    ontology_graph_uri: str = field(default_factory=lambda: os.getenv("ONTOLOGY_GRAPH_URI", "http://example.org/semantic-web/graph/ontology"))
    data_graph_uri: str = field(default_factory=lambda: os.getenv("DATA_GRAPH_URI", "http://example.org/semantic-web/graph/data"))
    app_host: str = field(default_factory=lambda: os.getenv("VIEWER_HOST", "127.0.0.1"))
    app_port: int = field(default_factory=lambda: int(os.getenv("VIEWER_PORT", "8000")))
    designer_iterations: int = field(default_factory=lambda: _env_int("DESIGNER_ITERATIONS", 2, 3))
    importer_iterations: int = field(default_factory=lambda: _env_int("IMPORTER_ITERATIONS", 2, 3))
    semantic_search_enabled: bool = field(default_factory=_semantic_search_enabled)
    semantic_search_provider: str = field(default_factory=lambda: os.getenv("SEMANTIC_SEARCH_PROVIDER", "local"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    semantic_search_top_k: int = field(default_factory=lambda: _env_int("SEMANTIC_SEARCH_TOP_K", 8, 12))
    semantic_context_max_chars: int = field(default_factory=lambda: _env_int("SEMANTIC_CONTEXT_MAX_CHARS", 16000, 40000))
    designer_retrieval_focuses: int = field(default_factory=lambda: _env_int("DESIGNER_RETRIEVAL_FOCUSES", 4, 8))
    designer_slice_context_max_chars: int = field(default_factory=lambda: _env_int("DESIGNER_SLICE_CONTEXT_MAX_CHARS", 5000, 10000))
    designer_ontology_triple_limit: int = field(default_factory=lambda: _env_int("DESIGNER_ONTOLOGY_TRIPLE_LIMIT", 260, 2000))
    importer_retrieval_batches: int = field(default_factory=lambda: _env_int("IMPORTER_RETRIEVAL_BATCHES", 4, 10))
    importer_slice_context_max_chars: int = field(default_factory=lambda: _env_int("IMPORTER_SLICE_CONTEXT_MAX_CHARS", 5000, 10000))

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
    settings.fuseki_data_dir.mkdir(parents=True, exist_ok=True)
    settings.tests_dir.mkdir(parents=True, exist_ok=True)
    settings.viewer_chat_dir.mkdir(parents=True, exist_ok=True)
    return settings
