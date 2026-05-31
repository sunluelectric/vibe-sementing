from __future__ import annotations

from pathlib import Path

from src.common.csv_profile import profile_csv, render_csv_profile


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_pdf_text(path: Path) -> str:
    import fitz

    document = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in document)
    finally:
        document.close()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_project_data(data_dir: Path, include_csv: bool = True) -> str:
    parts: list[str] = []
    for path in sorted(data_dir.glob("*")):
        if path.is_dir():
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            parts.append(f"# Source file: {path.name}\n\n{read_text(path)}")
        elif path.suffix.lower() == ".pdf":
            parts.append(f"# Source file: {path.name}\n\n{read_pdf_text(path)}")
        elif include_csv and path.suffix.lower() == ".csv":
            parts.append(render_csv_profile(profile_csv(path)))
    return "\n\n".join(parts).strip()
