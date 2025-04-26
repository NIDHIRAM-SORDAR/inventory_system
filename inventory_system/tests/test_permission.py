# inventory_system/tests/test_permission.py
from datetime import datetime, timezone

import pytest
import reflex as rx
from sqlmodel import Session, create_engine, select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import (
    Permission,
    Role,
    RolePermission,
    UserInfo,
)


def get_utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


@pytest.fixture
def session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    print("Creating tables...")
    rx.Model.metadata.create_all(engine)
    print("Tables created:", rx.Model.metadata.tables.keys())
    with Session(engine) as session:
        # Clear permissions before each test
        session.exec(Permission.__table__.delete())
        session.commit()
        yield session


def test_create_permission(session: Session):
    """Test creating a permission with timestamps."""
    permission = Permission(name="manage_users", description="Manage user accounts")
    session.add(permission)
    session.commit()

    retrieved = session.exec(
        select(Permission).where(Permission.name == "manage_users")
    ).first()
    assert retrieved is not None
    assert retrieved.name == "manage_users"
    assert retrieved.description == "Manage user accounts"
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)
    assert retrieved.created_at <= retrieved.updated_at


def test_unique_permission_name(session: Session):
    """Test that permission names are unique."""
    permission1 = Permission(name="manage_users", description="First permission")
    session.add(permission1)
    session.commit()

    permission2 = Permission(name="manage_users", description="Duplicate permission")
    session.add(permission2)
    with pytest.raises(Exception):  # Expect SQL integrity error
        session.commit()


def test_update_timestamp(session: Session):
    """Test updating the updated_at timestamp."""
    permission = Permission(name="view_inventory", description="View inventory")
    session.add(permission)
    session.commit()

    original_updated_at = permission.updated_at
    permission.description = "Updated description"
    permission.update_timestamp()
    session.add(permission)
    session.commit()

    retrieved = session.exec(
        select(Permission).where(Permission.name == "view_inventory")
    ).first()
    assert retrieved.updated_at > original_updated_at


def test_permission_deletion_cascade(session: Session):
    """Test that deleting a permission cascades to RolePermission entries."""
    permission = Permission(name="manage_suppliers", description="Manage suppliers")
    role = Role(name="admin", description="Administrator role")
    session.add_all([permission, role])
    session.commit()

    role.set_permissions(["manage_suppliers"], session)
    session.commit()

    assert (
        session.exec(
            select(RolePermission).where(RolePermission.permission_id == permission.id)
        ).first()
        is not None
    )

    session.delete(permission)
    session.commit()

    assert (
        session.exec(
            select(RolePermission).where(RolePermission.permission_id == permission.id)
        ).first()
        is None
    )


def test_role_permissions_relationship(session: Session):
    """Test the Role-Permission many-to-many relationship."""
    permission1 = Permission(name="manage_users", description="Manage users")
    permission2 = Permission(name="view_inventory", description="View inventory")
    role = Role(name="admin", description="Administrator role")
    session.add_all([permission1, permission2, role])
    session.commit()

    role.set_permissions(["manage_users", "view_inventory"], session)
    session.commit()

    retrieved_role = session.exec(select(Role).where(Role.name == "admin")).first()
    assert len(retrieved_role.permissions) == 2
    assert set(retrieved_role.get_permissions()) == {"manage_users", "view_inventory"}

    retrieved_perm = session.exec(
        select(Permission).where(Permission.name == "manage_users")
    ).first()
    assert len(retrieved_perm.roles) == 1
    assert retrieved_perm.roles[0].name == "admin"


def test_role_users_relationship(session: Session):
    """Test the Role-UserInfo many-to-many relationship."""
    user = UserInfo(email="test@example.com", user_id=1)
    role = Role(name="employee", description="Employee role")
    session.add_all([user, role])
    session.commit()

    user.set_roles(["employee"], session)
    session.commit()

    retrieved_role = session.exec(select(Role).where(Role.name == "employee")).first()
    assert len(retrieved_role.users) == 1
    assert retrieved_role.users[0].email == "test@example.com"

    retrieved_user = session.exec(select(UserInfo).where(UserInfo.user_id == 1)).first()
    assert len(retrieved_user.roles) == 1
    assert retrieved_user.get_roles() == ["employee"]


def test_seed_permissions(session: Session):
    """Test seeding permissions."""
    from inventory_system.scripts.seed_permissions import seed_permissions

    permissions_before = session.exec(select(Permission)).all()
    print(f"Permissions before seeding: {len(permissions_before)}")

    seed_permissions(session=session)
    permissions = session.exec(select(Permission)).all()
    print(f"Seeded permissions: {len(permissions)}")
    print(f"Permissions: {[p.name for p in permissions]}")
    assert len(permissions) >= 9
    perm_names = {p.name for p in permissions}
    assert "manage_users" in perm_names
    assert "create_inventory" in perm_names
    assert "update_inventory" in perm_names
    assert "delete_inventory" in perm_names
    assert any(p.description for p in permissions if p.name == "manage_users")
    assert all(isinstance(p.created_at, datetime) for p in permissions)
    assert all(isinstance(p.updated_at, datetime) for p in permissions)


def test_permission_audit_logging(session: Session):
    """Test that audit logging captures permission changes."""
    log_capture = []
    original_info = audit_logger.info

    def capture_log(event, **kwargs):
        log_capture.append((event, kwargs))

    audit_logger.info = capture_log

    try:
        permission = Permission(name="audit_test", description="Audit test permission")
        session.add(permission)
        session.commit()

        assert len(log_capture) >= 1
        event, kwargs = log_capture[0]
        assert event == "create_permission"
        assert kwargs["entity_type"] == "permission"
        assert kwargs["entity_id"] == permission.id
        assert "details" in kwargs
        assert "new" in kwargs["details"]
        assert kwargs["details"]["new"]["name"] == "audit_test"
        assert "created_at" in kwargs["details"]["new"]
        assert "updated_at" in kwargs["details"]["new"]

        permission.description = "Updated description"
        permission.update_timestamp()
        session.add(permission)
        session.commit()

        assert len(log_capture) >= 2
        event, kwargs = log_capture[1]
        assert event == "update_permission"
        assert kwargs["entity_type"] == "permission"
        assert kwargs["entity_id"] == permission.id
        assert "details" in kwargs
        assert "changes" in kwargs["details"]
        assert "description" in kwargs["details"]["changes"]
        assert "updated_at" in kwargs["details"]["changes"]

        session.delete(permission)
        session.commit()

        assert len(log_capture) >= 3
        event, kwargs = log_capture[2]
        assert event == "delete_permission"
        assert kwargs["entity_type"] == "permission"
        assert kwargs["entity_id"] == permission.id
        assert "details" in kwargs
        assert "deleted" in kwargs["details"]
        assert kwargs["details"]["deleted"]["name"] == "audit_test"
        assert "created_at" in kwargs["details"]["deleted"]
        assert "updated_at" in kwargs["details"]["deleted"]
    finally:
        audit_logger.info = original_info


def test_userinfo_roles(session: Session):
    """Test setting and getting roles for UserInfo."""
    role1 = Role(name="admin", description="Administrator role")
    role2 = Role(name="employee", description="Employee role")
    session.add_all([role1, role2])
    session.commit()

    user = UserInfo(email="test@example.com", user_id=1)
    session.add(user)
    session.commit()

    user.set_roles(["admin", "employee"], session)
    session.commit()

    roles = user.get_roles()
    assert set(roles) == {"admin", "employee"}

    with pytest.raises(ValueError, match="Role 'invalid' does not exist"):
        user.set_roles(["admin", "invalid"], session)


def test_role_permissions(session: Session):
    """Test setting and getting permissions for Role."""
    perm1 = Permission(name="manage_users", description="Manage user accounts")
    perm2 = Permission(name="view_inventory", description="View inventory")
    session.add_all([perm1, perm2])
    session.commit()

    role = Role(name="admin", description="Administrator role")
    session.add(role)
    session.commit()

    role.set_permissions(["manage_users", "view_inventory"], session)
    session.commit()

    permissions = role.get_permissions()
    assert set(permissions) == {"manage_users", "view_inventory"}

    with pytest.raises(ValueError, match="Permission 'invalid' does not exist"):
        role.set_permissions(["manage_users", "invalid"], session)


def test_userinfo_permissions(session: Session):
    # Setup: Create permissions, roles, and a user
    perm1 = Permission(name="manage_users")
    perm2 = Permission(name="view_inventory")
    role1 = Role(name="admin")
    role2 = Role(name="employee")
    user = UserInfo(email="test@example.com", user_id=1)
    session.add_all([perm1, perm2, role1, role2, user])
    session.commit()

    # Assign permissions to roles and roles to user
    role1.set_permissions(["manage_users"], session)
    role2.set_permissions(["view_inventory"], session)
    user.set_roles(["admin", "employee"], session)
    session.commit()

    # Assertions
    assert set(user.get_permissions()) == {"manage_users", "view_inventory"}
    assert user.has_permission("manage_users") is True
    assert user.has_permission("view_inventory") is True
    assert user.has_permission("delete_inventory") is False


def test_audit_logging_roles(session: Session):
    """Test audit logging for UserRole changes."""
    log_capture = []
    original_info = audit_logger.info

    def capture_log(event, **kwargs):
        log_capture.append((event, kwargs))

    audit_logger.info = capture_log

    try:
        role = Role(name="admin", description="Administrator role")
        user = UserInfo(email="test@example.com", user_id=1)
        session.add_all([role, user])
        session.commit()

        user.set_roles(["admin"], session)
        session.commit()

        assert len(log_capture) >= 1
        event, kwargs = log_capture[-1]
        assert event == "create_userrole"
        assert kwargs["entity_type"] == "userrole"
        assert kwargs["entity_id"] == f"{user.id}-{role.id}"
        assert "details" in kwargs
        assert "new" in kwargs["details"]
        assert kwargs["details"]["new"]["user_id"] == user.id
        assert kwargs["details"]["new"]["role_id"] == role.id
    finally:
        audit_logger.info = original_info


def test_audit_logging_permissions(session: Session):
    """Test audit logging for RolePermission changes."""
    log_capture = []
    original_info = audit_logger.info

    def capture_log(event, **kwargs):
        log_capture.append((event, kwargs))

    audit_logger.info = capture_log

    try:
        perm = Permission(name="manage_users", description="Manage user accounts")
        role = Role(name="admin", description="Administrator role")
        session.add_all([perm, role])
        session.commit()

        role.set_permissions(["manage_users"], session)
        session.commit()

        assert len(log_capture) >= 1
        event, kwargs = log_capture[-1]
        assert event == "create_rolepermission"
        assert kwargs["entity_type"] == "rolepermission"
        assert kwargs["entity_id"] == f"{role.id}-{perm.id}"
        assert "details" in kwargs
        assert "new" in kwargs["details"]
        assert kwargs["details"]["new"]["role_id"] == role.id
        assert kwargs["details"]["new"]["permission_id"] == perm.id
    finally:
        audit_logger.info = original_info
