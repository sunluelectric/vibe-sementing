from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_project_data(data_dir: Path) -> str:
    parts: list[str] = []
    for path in sorted(data_dir.glob("*")):
        if path.is_dir():
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            parts.append(f"# Source file: {path.name}\n\n{read_text(path)}")
        elif path.suffix.lower() == ".csv":
            dataframe = pd.read_csv(path)
            parts.append(
                f"# Source file: {path.name}\n\n"
                f"Columns: {', '.join(dataframe.columns)}\n\n"
                f"{dataframe.to_csv(index=False)}"
            )
    return "\n\n".join(parts).strip()
