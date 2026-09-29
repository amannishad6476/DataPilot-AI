import pytest
import time
from app.services.connectors.circuit_breaker import CircuitBreaker, CircuitState
from app.services.connectors.ssrf_firewall import validate_url_security, assert_url_safe
from app.core.errors import CircuitBreakerOpenError, SsrfBlockedError


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(connector_id="test_conn", failure_threshold=2, recovery_timeout_sec=0.1)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 1st failure
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 2nd failure -> OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    with pytest.raises(CircuitBreakerOpenError):
        cb.ensure_executable()

    # Wait for recovery timeout
    time.sleep(0.12)

    # In HALF_OPEN state
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success resets to CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_ssrf_blocks_private_ips():
    bad_urls = [
        "http://127.0.0.1/admin",
        "http://localhost:8080/secrets",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/",
        "http://172.16.0.5/api",
        "ftp://example.com/file",
        "file:///etc/passwd",
    ]
    for url in bad_urls:
        is_safe, reason = validate_url_security(url)
        assert is_safe is False, f"Expected {url} to be blocked, but passed. Reason: {reason}"
        with pytest.raises(SsrfBlockedError):
            assert_url_safe(url)


def test_ssrf_allows_public_urls():
    safe_urls = [
        "https://example.com",
        "https://api.github.com/repos",
        "http://httpbin.org/get",
    ]
    for url in safe_urls:
        is_safe, reason = validate_url_security(url)
        assert is_safe is True, f"Expected {url} to be safe, but blocked: {reason}"
        # assert_url_safe should not raise
        assert_url_safe(url)


def test_ssrf_domain_allowlist():
    is_safe, _ = validate_url_security("https://allowed.com/data", allowed_domains=["allowed.com"])
    assert is_safe is True

    is_safe, _ = validate_url_security("https://other.com/data", allowed_domains=["allowed.com"])
    assert is_safe is False
