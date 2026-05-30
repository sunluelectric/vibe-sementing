from __future__ import annotations

from src.common.config import get_settings
from src.designer.workflow import DesignerWorkflow


def main() -> None:
    settings = get_settings()
    print(f"Designer workflow model: {settings.llm_model}")
    print(f"Designer iterations allowed: {settings.designer_iterations}")
    print(f"Fuseki dataset: {settings.fuseki_dataset}")
    result = DesignerWorkflow(settings).run_sync()
    print(f"Designer wrote {result.design_path}")
    print(f"Designer wrote {result.ontology_path} with {result.triple_count} triples")
    print(f"Ontology load target: {result.load_target}")
    print(f"Fuseki status: {result.fuseki_status}")


if __name__ == "__main__":
    main()
