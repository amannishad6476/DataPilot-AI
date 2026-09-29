import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|password|bearer|token)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'),
    re.compile(r'(?i)(Authorization:\s*Bearer\s+)(\S+)'),
]


def redact_sensitive(text: str) -> str:
    """Masks secret tokens and passwords in log messages."""
    if not isinstance(text, str):
        return text
    for pat in SENSITIVE_PATTERNS:
        text = pat.sub(r'\1: [REDACTED]', text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON for production observability ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
        }

        # Include contextual execution identifiers if provided
        for attr in ["request_id", "workflow_id", "run_id", "node_id", "connector_id", "duration_ms"]:
            val = getattr(record, attr, None)
            if val is not None:
                log_obj[attr] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str = "datapilot") -> logging.Logger:
    return logging.getLogger(name)
