from __future__ import annotations

from pathlib import Path

from rdflib import RDF, RDFS, Namespace

from src.common.files import load_project_data
from src.common.fuseki import FusekiClient
from src.common.fuseki_manager import FusekiManager
from src.common.rdf import combine_turtle_files, parse_turtle, run_select


def test_load_project_data_reads_markdown_and_csv(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("# Note\n\nMarkdown text", encoding="utf-8")
    (tmp_path / "table.csv").write_text("name,value\nA,1\n", encoding="utf-8")

    loaded = load_project_data(tmp_path)

    assert "Source file: note.md" in loaded
    assert "Markdown text" in loaded
    assert "Source file: table.csv" in loaded
    assert "name,value" in loaded


def test_rdf_parse_combine_and_query(tmp_path: Path) -> None:
    sw = Namespace("http://example.org/semantic-web#")
    one = tmp_path / "one.ttl"
    two = tmp_path / "two.ttl"
    combined = tmp_path / "combined.ttl"
    one.write_text(
        "@prefix sw: <http://example.org/semantic-web#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "sw:Record a rdfs:Class .\n",
        encoding="utf-8",
    )
    two.write_text(
        "@prefix sw: <http://example.org/semantic-web#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "sw:Source a rdfs:Class .\n",
        encoding="utf-8",
    )

    graph = combine_turtle_files([one, two], combined)
    rows = run_select(
        graph,
        """
        SELECT ?class WHERE {
          ?class a <http://www.w3.org/2000/01/rdf-schema#Class> .
        }
        ORDER BY ?class
        """,
    )

    assert (sw.Record, RDF.type, RDFS.Class) in graph
    assert combined.exists()
    assert len(rows) == 2


def test_parse_turtle_accepts_valid_turtle() -> None:
    graph = parse_turtle(
        """
        @prefix sw: <http://example.org/semantic-web#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        sw:Record a rdfs:Class .
        """
    )

    assert len(graph) == 1


def test_fuseki_manager_uses_project_writable_base(tmp_path: Path) -> None:
    class Client:
        query_url = "http://localhost:3030/test/query"

        def is_available(self) -> bool:
            return False

    manager = FusekiManager(
        fuseki_home=tmp_path / "fuseki",
        fuseki_run_dir=tmp_path / "run",
        fuseki_log_path=tmp_path / "fuseki.log",
        dataset="test",
        client=Client(),
    )

    command = manager.command()

    assert "--update" in command
    assert "--localhost" in command


def test_fuseki_manager_stop_ignores_unowned_server(tmp_path: Path) -> None:
    class Client:
        query_url = "http://localhost:3030/test/query"

        def is_available(self) -> bool:
            return True

    manager = FusekiManager(
        fuseki_home=tmp_path / "fuseki",
        fuseki_run_dir=tmp_path / "run",
        fuseki_log_path=tmp_path / "fuseki.log",
        dataset="test",
        client=Client(),
    )

    result = manager.stop_if_started()

    assert result.status == "not_started"


def test_fuseki_manager_stops_owned_process(tmp_path: Path, monkeypatch) -> None:
    class Client:
        query_url = "http://localhost:3030/test/query"

        def is_available(self) -> bool:
            return True

    class Process:
        pid = 12345
        returncode = None

        def __init__(self) -> None:
            self.waited = False

        def poll(self):
            return None

        def wait(self, timeout):
            self.waited = True
            self.returncode = 0
            return 0

    signals = []

    def fake_killpg(pid, sig):
        signals.append((pid, sig))

    manager = FusekiManager(
        fuseki_home=tmp_path / "fuseki",
        fuseki_run_dir=tmp_path / "run",
        fuseki_log_path=tmp_path / "fuseki.log",
        dataset="test",
        client=Client(),
    )
    process = Process()
    manager.process = process
    monkeypatch.setattr("src.common.fuseki_manager.os.killpg", fake_killpg)

    result = manager.stop_if_started()

    assert result.status == "stopped"
    assert result.pid == process.pid
    assert process.waited
    assert signals


def test_fuseki_client_availability_uses_sparql_ask(monkeypatch) -> None:
    calls = []

    class Response:
        status_code = 200

    def fake_post(url, data, headers, timeout):
        calls.append((url, data, headers, timeout))
        return Response()

    monkeypatch.setattr("src.common.fuseki.requests.post", fake_post)
    client = FusekiClient(
        graph_store_url="http://example.test/data",
        query_url="http://example.test/query",
        update_url="http://example.test/update",
    )

    assert client.is_available()
    assert calls[0][1]["query"].startswith("ASK")
