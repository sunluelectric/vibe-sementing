from __future__ import annotations

from src.common.config import get_settings
from src.importer.workflow import ImporterWorkflow


def main() -> None:
    settings = get_settings()
    print(f"Importer workflow model: {settings.llm_model}")
    print(f"Importer iterations allowed: {settings.importer_iterations}")
    print(f"Fuseki dataset: {settings.fuseki_dataset}")
    result = ImporterWorkflow(settings).run_sync()
    print(f"Importer wrote {result.instances_path} with {result.triple_count} triples")
    print(
        f"Importer wrote {result.combined_path} "
        f"with {result.combined_triple_count} combined triples"
    )
    print(f"Instance load target: {result.load_target}")
    print(f"Fuseki status: {result.fuseki_status}")


if __name__ == "__main__":
    main()
