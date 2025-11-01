"""Log parsing helpers for FlowGuard."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

LOG_LINE_PATTERN = re.compile(
    r"^(?P<service>[\\w-]+)\\s+\\|\\s+(?P<level>[A-Z]+)\\s+\\|\\s+(?P<message>.*)$"
)
LATENCY_PATTERN = re.compile(r"latency(?:=|:)(?P<latency>\\d+)ms", re.IGNORECASE)
STATUS_PATTERN = re.compile(r"status(?:=|:)(?P<status>\\d{3})", re.IGNORECASE)


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a structured log line into its components."""
    match = LOG_LINE_PATTERN.match(line.strip())
    if not match:
        return None

    payload = match.groupdict()
    payload["latency_ms"] = _extract_int(LATENCY_PATTERN, payload["message"])
    payload["status_code"] = _extract_int(STATUS_PATTERN, payload["message"])
    return payload


def _extract_int(pattern: re.Pattern[str], text: str) -> Optional[int]:
    match = pattern.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None

