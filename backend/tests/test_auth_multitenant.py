import pytest
from fastapi import HTTPException
from app.core.security import (
    Role,
    UserContext,
    DEFAULT_LOCAL_USER,
    get_current_user,
    require_role,
    ROLE_HIERARCHY,
)


def test_default_unauthenticated_user():
    # Without headers, defaults to local owner
    user = get_current_user()
    assert user.user_id == DEFAULT_LOCAL_USER.user_id
    assert user.role == Role.OWNER
    assert user.tenant_id == "tenant_default"


def test_api_key_authentication():
    # Admin API key
    admin_user = get_current_user(x_api_key="dp_live_admin_secret_key", x_tenant_id="tenant_alpha")
    assert admin_user.role == Role.ADMIN
    assert admin_user.tenant_id == "tenant_alpha"

    # Viewer Bearer token
    viewer_user = get_current_user(authorization="Bearer dp_live_viewer_secret_key")
    assert viewer_user.role == Role.VIEWER
    assert viewer_user.tenant_id == "tenant_default"


def test_invalid_api_key():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization="Bearer completely_invalid_token")
    assert exc_info.value.status_code == 401


def test_role_hierarchy_permissions():
    owner = UserContext(
        user_id="u1", tenant_id="t1", organization_id="o1", role=Role.OWNER, email="owner@test.com"
    )
    admin = UserContext(
        user_id="u2", tenant_id="t1", organization_id="o1", role=Role.ADMIN, email="admin@test.com"
    )
    member = UserContext(
        user_id="u3", tenant_id="t1", organization_id="o1", role=Role.MEMBER, email="member@test.com"
    )
    viewer = UserContext(
        user_id="u4", tenant_id="t1", organization_id="o1", role=Role.VIEWER, email="viewer@test.com"
    )

    admin_gate = require_role(Role.ADMIN)

    # Owner can pass admin gate
    assert admin_gate(owner).user_id == "u1"
    # Admin can pass admin gate
    assert admin_gate(admin).user_id == "u2"

    # Member fails admin gate
    with pytest.raises(HTTPException) as exc_info:
        admin_gate(member)
    assert exc_info.value.status_code == 403

    # Viewer fails admin gate
    with pytest.raises(HTTPException) as exc_info:
        admin_gate(viewer)
    assert exc_info.value.status_code == 403
