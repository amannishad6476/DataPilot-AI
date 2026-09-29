import time
from enum import Enum
from typing import Dict
from app.core.errors import CircuitBreakerOpenError


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation, requests allowed
    OPEN = "OPEN"          # Failing, fast fail requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery with trial request


class CircuitBreaker:
    """
    Per-connector circuit breaker pattern.
    Protects downstream systems and saves execution resources by fast-failing
    requests to persistently broken or unresponsive endpoints.
    """

    def __init__(
        self,
        connector_id: str,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 30.0
    ):
        self.connector_id = connector_id
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow trial probe
            return True

        return True

    def record_success(self):
        self.failure_count = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()

    def ensure_executable(self):
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                connector_id=self.connector_id,
                message=f"Circuit breaker for connector '{self.connector_id}' is OPEN (recent consecutive failures). Retrying in {int(self.recovery_timeout_sec - (time.time() - self.last_failure_time))}s."
            )
