"""Anomaly detection utilities."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Deque, Dict, Optional

import numpy as np
from loguru import logger
from sklearn.ensemble import IsolationForest

WINDOW_SIZE = 64
MIN_POINTS = 12


@dataclass
class DetectorState:
    window: Deque[np.ndarray]
    model: Optional[IsolationForest] = None


_detectors: Dict[str, DetectorState] = defaultdict(
    lambda: DetectorState(window=deque(maxlen=WINDOW_SIZE))
)


def _to_vector(snapshot: dict) -> np.ndarray:
    return np.array(
        [
            float(snapshot.get("error_rate", 0.0)),
            float(snapshot.get("p95_latency_ms", 0)),
            float(snapshot.get("tps", 0.0)),
        ],
        dtype=float,
    )


def evaluate(service_name: str, snapshot: dict, config: dict) -> dict:
    """Evaluate anomaly scores for a KPI snapshot."""
    state = _detectors[service_name]
    vector = _to_vector(snapshot)
    state.window.append(vector)

    if len(state.window) < MIN_POINTS:
        return {"is_anomaly": False, "reason": None, "score": 0.0}

    try:
        model = IsolationForest(
            n_estimators=50,
            contamination=0.1,
            random_state=42,
        )
        data = np.stack(tuple(state.window))
        model.fit(data)
        score = float(model.decision_function([vector])[0])
        prediction = int(model.predict([vector])[0])
        state.model = model
        if prediction == -1:
            reason = _build_reason(snapshot)
            return {"is_anomaly": True, "reason": reason, "score": score}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("IsolationForest failed, falling back to z-score", error=str(exc))

    # Fallback to simple z-score detection
    error_rate_z = _z_score([vec[0] for vec in state.window], vector[0])
    latency_z = _z_score([vec[1] for vec in state.window], vector[1])
    tps_z = _z_score([vec[2] for vec in state.window], vector[2])

    max_score = max(abs(error_rate_z), abs(latency_z), abs(tps_z))
    if max_score >= 3:
        reason = _build_reason(snapshot)
        return {"is_anomaly": True, "reason": reason, "score": float(max_score)}

    return {"is_anomaly": False, "reason": None, "score": float(max_score)}


def _z_score(series, value) -> float:
    if len(series) < 2:
        return 0.0
    mu = mean(series)
    sigma = pstdev(series)
    if sigma == 0:
        return 0.0
    return (value - mu) / sigma


def _build_reason(snapshot: dict) -> str:
    components = []
    if snapshot.get("error_rate", 0) > 0.01:
        components.append("error_rate spike")
    if snapshot.get("p95_latency_ms", 0) > 0:
        components.append("latency outlier")
    if not components:
        components.append("traffic anomaly")
    return ", ".join(components)

