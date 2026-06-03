from __future__ import annotations

import sys
from pathlib import Path

from src.common.config import Settings


PLOT_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools" / "semantic-web-plot"


def _load_plotter_class():
    if str(PLOT_TOOL_DIR) not in sys.path:
        sys.path.insert(0, str(PLOT_TOOL_DIR))
    from semantic_web_plot import SemanticWebPlotter

    return SemanticWebPlotter


class ViewerPlotService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._plotter_class = _load_plotter_class()

    def render_turtle(self, turtle: str) -> str:
        result = self._plotter_class().render_turtle_text(
            turtle,
            self.settings.plot_html_path,
            input_label="Fuseki semantic web export",
        )
        return result.html
