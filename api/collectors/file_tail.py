"""Tail a logfile and push entries into FlowGuard for development."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterator
from urllib import request as urlrequest


def tail(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                time.sleep(0.2)
                continue
            yield line.rstrip()


def post_logs(endpoint: str, line: str) -> None:
    payload = [{"message": line, "service": "file-tail", "level": "INFO", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}]
    req = urlrequest.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlrequest.urlopen(req, timeout=5):
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Tail a file and post logs to FlowGuard.")
    parser.add_argument("path", type=Path, help="Path to the logfile to tail")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/api/ingest/logs",
        help="FlowGuard ingest endpoint",
    )
    args = parser.parse_args()

    for line in tail(args.path):
        try:
            post_logs(args.endpoint, line)
        except Exception:  # pragma: no cover - dev helper
            continue


if __name__ == "__main__":
    main()

