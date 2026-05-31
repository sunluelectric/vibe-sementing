from __future__ import annotations

import threading
import webbrowser

import uvicorn

from src.common.config import get_settings
from src.viewer.app import create_app


def main() -> None:
    settings = get_settings()
    url = f"http://{settings.app_host}:{settings.app_port}"
    print(f"Semantic web mode: {settings.semantic_web_mode}")
    print(f"Viewer model: {settings.llm_model}")
    print(f"Viewer Fuseki dataset: {settings.fuseki_dataset}")
    print(f"Viewer URL: {url}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(
        create_app(),
        host=settings.app_host,
        port=settings.app_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
