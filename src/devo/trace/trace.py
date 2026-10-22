"""Trace emitter recording timestamped run events in structured JSONL format."""
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from devo.trace.redact import redact_secrets


@dataclass
class TraceEvent:
    seq: int
    ts: str
    state: str
    kind: str
    detail: str


class TraceEmitter:
    """Manages sequential logging of run events into a trace.jsonl file."""

    def __init__(self, log_path: Path | str | None = None) -> None:
        self.log_path = Path(log_path) if log_path else None
        self.events: list[TraceEvent] = []
        self._seq = 0
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, state: str, kind: str, detail: str) -> TraceEvent:
        """Emit and persist a new redacted trace event."""
        self._seq += 1
        clean_detail = redact_secrets(detail)
        event = TraceEvent(
            seq=self._seq,
            ts=datetime.now(timezone.utc).isoformat(),
            state=state,
            kind=kind,
            detail=clean_detail,
        )
        self.events.append(event)

        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event)) + "\n")

        return event
