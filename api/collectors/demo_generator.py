"""Synthetic data generator for development."""

from __future__ import annotations

import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from typing import List
from urllib import request as urlrequest

from loguru import logger

from ..utils.config import load_config


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoGenerator:
    def __init__(self, api_base: str, services: List[str]) -> None:
        self.api_base = api_base.rstrip("/")
        self.services = services or ["demo"]
        self.session = None

    def run(self) -> None:
        logger.info("Starting demo generator", services=self.services)
        threads = [
            threading.Thread(target=self._log_worker, daemon=True),
            threading.Thread(target=self._metric_worker, daemon=True),
        ]
        for t in threads:
            t.start()

        while True:
            time.sleep(1)

    def _log_worker(self) -> None:
        while True:
            batch = []
            for service in self.services:
                level = random.choices(
                    population=["INFO", "WARN", "ERROR"],
                    weights=[0.8, 0.15, 0.05],
                    k=1,
                )[0]
                latency = random.randint(50, 1500)
                status_code = random.choice([200, 200, 200, 500, 502])
                batch.append(
                    {
                        "service": service,
                        "ts": _iso_now(),
                        "level": level,
                        "message": f"{service} processed request latency={latency}ms status={status_code}",
                        "latency_ms": latency,
                        "status_code": status_code,
                    }
                )
            self._post("/api/ingest/logs", batch)
            time.sleep(5)

    def _metric_worker(self) -> None:
        while True:
            batch = []
            for service in self.services:
                tps = random.uniform(10, 50)
                error_rate = max(0.0, random.gauss(0.02, 0.01))
                latency = random.randint(200, 800)
                batch.append(
                    {
                        "service": service,
                        "ts": _iso_now(),
                        "tps": round(tps, 3),
                        "error_rate": round(error_rate, 4),
                        "p95_latency_ms": latency,
                    }
                )
            self._post("/api/ingest/metrics", batch)
            time.sleep(10)

    def _post(self, path: str, payload: List[dict]) -> None:
        endpoint = f"{self.api_base}{path}"
        req = urlrequest.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlrequest.urlopen(req, timeout=5) as resp:
                if resp.status >= 300:
                    logger.warning("Demo generator received non-OK response", status=resp.status)
        except Exception as exc:  # pragma: no cover - dev helper
            logger.debug("Demo generator request failed", error=str(exc))


def main() -> None:
    config = load_config()
    if not config.get("DEV_GENERATOR", False):
        logger.info("DEV_GENERATOR disabled; exiting demo generator")
        return

    api_base = os.getenv("FLOWGUARD_API_BASE", "http://localhost:8000")
    generator = DemoGenerator(api_base, config.get("SERVICE_ALLOWLIST") or ["demo"])
    generator.run()


if __name__ == "__main__":
    main()

