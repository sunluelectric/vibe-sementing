from __future__ import annotations

import subprocess
import time
import os
from dataclasses import dataclass
from pathlib import Path

from src.common.fuseki import FusekiClient


@dataclass
class FusekiStartResult:
    status: str
    message: str
    pid: int | None = None


class FusekiManager:
    def __init__(
        self,
        fuseki_home: Path,
        fuseki_run_dir: Path,
        fuseki_log_path: Path,
        dataset: str,
        client: FusekiClient,
        start_timeout_seconds: int = 20,
    ):
        self.fuseki_home = fuseki_home
        self.fuseki_run_dir = fuseki_run_dir
        self.fuseki_log_path = fuseki_log_path
        self.dataset = dataset
        self.client = client
        self.start_timeout_seconds = start_timeout_seconds

    def status(self) -> dict[str, str | bool]:
        available = self.client.is_available()
        return {
            "available": available,
            "query_url": self.client.query_url,
            "message": "Fuseki is reachable." if available else "Fuseki is not reachable.",
        }

    def start(self) -> FusekiStartResult:
        if self.client.is_available():
            return FusekiStartResult(status="already_running", message="Fuseki is already reachable.")

        executable = self.fuseki_home / "fuseki-server"
        if not executable.exists():
            return FusekiStartResult(
                status="not_found",
                message=f"Fuseki executable was not found at {executable}.",
            )

        self.fuseki_run_dir.mkdir(parents=True, exist_ok=True)
        self.fuseki_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.fuseki_log_path.open("ab") as log_file:
            env = os.environ.copy()
            env["FUSEKI_BASE"] = str(self.fuseki_run_dir)
            process = subprocess.Popen(
                self.command(),
                cwd=str(self.fuseki_home),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )

        deadline = time.time() + self.start_timeout_seconds
        while time.time() < deadline:
            if self.client.is_available():
                return FusekiStartResult(
                    status="started",
                    message="Fuseki started and is reachable.",
                    pid=process.pid,
                )
            if process.poll() is not None:
                return FusekiStartResult(
                    status="exited",
                    message=(
                        f"Fuseki process exited with code {process.returncode}. "
                        f"See {self.fuseki_log_path}."
                    ),
                    pid=process.pid,
                )
            time.sleep(0.5)

        return FusekiStartResult(
            status="timeout",
            message="Fuseki start command was launched but did not become reachable in time.",
            pid=process.pid,
        )

    def command(self) -> list[str]:
        executable = self.fuseki_home / "fuseki-server"
        return [
            str(executable),
            "--mem",
            "--update",
            "--localhost",
            f"/{self.dataset}",
        ]
