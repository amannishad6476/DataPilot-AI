import uuid
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        super().__init__(status_code=status_code, detail=message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detail": self.message,
            "error": {
                "code": self.code,
                "message": self.message,
                "request_id": self.request_id,
                "retryable": self.retryable,
                "details": self.details
            }
        }

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict()
        )


class NotFoundError(AppException):
    def __init__(self, message: str, resource_type: str = "resource", resource_id: str = ""):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message,
            retryable=False,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ConnectorTimeoutError(AppException):
    def __init__(self, message: str, connector_id: str = ""):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="CONNECTOR_TIMEOUT",
            message=message,
            retryable=True,
            details={"connector_id": connector_id}
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", retry_after_sec: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            retryable=True,
            details={"retry_after_sec": retry_after_sec}
        )


class PolicyViolationError(AppException):
    def __init__(self, message: str, violations: Optional[list] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="POLICY_VIOLATION",
            message=message,
            retryable=False,
            details={"violations": violations or []}
        )


class CircuitBreakerOpenError(AppException):
    def __init__(self, connector_id: str, message: str = "Circuit breaker is open; service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="CIRCUIT_BREAKER_OPEN",
            message=message,
            retryable=True,
            details={"connector_id": connector_id}
        )


class SsrfBlockedError(AppException):
    def __init__(self, message: str = "Destination address is forbidden under SSRF safety firewall policy"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="SSRF_FIREWALL_BLOCKED",
            message=message,
            retryable=False
        )
