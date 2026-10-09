"""CloudWatch custom metrics via Embedded Metric Format (EMF).

Printing one JSON line in this shape to stdout is enough: CloudWatch Logs turns
it into metrics in the "Neeru" namespace. No API calls, no extra permissions,
no added latency. The dashboard in template.yaml charts these.
"""

import json
import time

NAMESPACE = "Neeru"


def emit(metrics: dict[str, float], unit: str = "Count", **dimensions: str) -> None:
    """emit({"VerifiedReports": 1}, Source="telegram")"""
    record = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": NAMESPACE,
                "Dimensions": [list(dimensions)] if dimensions else [[]],
                "Metrics": [{"Name": name, "Unit": unit} for name in metrics],
            }],
        },
        **dimensions,
        **metrics,
    }
    print(json.dumps(record))


class timer:
    """with timer("AgentLatency", Agent="verifier"): ...  -> emits milliseconds."""

    def __init__(self, name: str, **dimensions: str):
        self.name = name
        self.dimensions = dimensions

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_exc):
        elapsed_ms = (time.perf_counter() - self.start) * 1000
        emit({self.name: round(elapsed_ms, 1)}, unit="Milliseconds", **self.dimensions)
        return False
