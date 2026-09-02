"""Distributed Micro-Span Latency Profiler & Observability Service.
Instruments multi-hop agent execution chains, records high-resolution per-hop latencies,
and generates standard W3C TraceContext compliant telemetry for frontend visualization.
"""

import time
import uuid
import logging
from typing import Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TraceSpan:
    """Represents a single execution span in the agent processing chain."""

    def __init__(self, name: str, category: str = "agent", parent_span_id: str | None = None):
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_span_id = parent_span_id
        self.name = name
        self.category = category
        self.start_time = time.perf_counter()
        self.end_time: float | None = None
        self.duration_ms: float = 0.0
        self.metadata: dict[str, Any] = {}

    def finish(self, metadata: dict[str, Any] | None = None) -> float:
        self.end_time = time.perf_counter()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        if metadata:
            self.metadata.update(metadata)
        return self.duration_ms


class TraceContext:
    """Tracks latency across all hops in an agent conversation turn."""

    def __init__(self, trace_id: str | None = None):
        import uuid
        self.trace_id = trace_id or f"tr_{uuid.uuid4().hex[:12]}"
        self.start_time = time.perf_counter()
        self.spans: list[TraceSpan] = []

    def start_span(self, name: str, category: str = "agent") -> TraceSpan:
        span = TraceSpan(name, category)
        self.spans.append(span)
        return span

    @asynccontextmanager
    async def span(self, name: str, category: str = "agent"):
        span = self.start_span(name, category)
        try:
            yield span
        finally:
            span.finish()

    def get_total_latency_ms(self) -> float:
        return round((time.perf_counter() - self.start_time) * 1000.0, 2)

    def to_dict(self) -> dict[str, Any]:
        root_span_id = self.spans[0].span_id if self.spans else uuid.uuid4().hex[:16]
        return {
            "trace_id": self.trace_id,
            "w3c_traceparent": f"00-{self.trace_id.replace('tr_', '').ljust(32, '0')[:32]}-{root_span_id}-01",
            "total_latency_ms": self.get_total_latency_ms(),
            "spans": [
                {
                    "span_id": s.span_id,
                    "name": s.name,
                    "category": s.category,
                    "duration_ms": s.duration_ms,
                    "metadata": s.metadata,
                }
                for s in self.spans
            ],
        }

    def to_telemetry_pills(self) -> list[dict[str, Any]]:
        """Return clean telemetry pill data for UI decisions drawer."""
        category_icons = {
            "router": "⚡",
            "guardrail": "🛡️",
            "entity": "🎯",
            "llm": "🧠",
            "database": "🔒",
            "payment": "💳",
        }
        return [
            {
                "name": s.name,
                "icon": category_icons.get(s.category, "⚙️"),
                "duration_ms": s.duration_ms,
                "category": s.category,
            }
            for s in self.spans
        ]
