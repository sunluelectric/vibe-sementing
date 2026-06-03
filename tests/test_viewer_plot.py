from __future__ import annotations

from dataclasses import replace

from src.common.config import get_settings
from src.viewer.plot import ViewerPlotService


def test_viewer_plot_service_renders_fuseki_turtle_export(tmp_path) -> None:
    settings = replace(get_settings(), plot_html_path=tmp_path / "plot.html")
    service = ViewerPlotService(settings)

    html = service.render_turtle(
        """
        @prefix sw: <http://example.org/semantic-web#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        sw:Record a rdfs:Class .
        sw:Source a rdfs:Class .
        sw:source a rdf:Property ;
          rdfs:domain sw:Record ;
          rdfs:range sw:Source .
        sw:item1 a sw:Record .
        """
    )

    assert settings.plot_html_path.exists()
    assert "http://example.org/semantic-web#Record" in html
    assert "source" in html
