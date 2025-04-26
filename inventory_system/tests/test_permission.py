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
    UserRole,
)


def get_utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


@pytest.fixture
def session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    # Import models to ensure metadata is populated
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
    permission = Permission(name="test_permission", description="Test permission")
    session.add(permission)
    session.commit()

    retrieved = session.exec(
        select(Permission).where(Permission.name == "test_permission")
    ).first()
    assert retrieved is not None
    assert retrieved.name == "test_permission"
    assert retrieved.description == "Test permission"
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)
    assert retrieved.created_at <= retrieved.updated_at


def test_unique_permission_name(session: Session):
    """Test that permission names are unique."""
    permission1 = Permission(name="unique_perm", description="First permission")
    session.add(permission1)
    session.commit()

    permission2 = Permission(name="unique_perm", description="Duplicate permission")
    session.add(permission2)
    with pytest.raises(Exception):  # Expect SQL integrity error
        session.commit()


def test_update_timestamp(session: Session):
    """Test updating the updated_at timestamp."""
    permission = Permission(name="update_test", description="Update test permission")
    session.add(permission)
    session.commit()

    original_updated_at = permission.updated_at
    permission.description = "Updated description"
    permission.update_timestamp()
    session.add(permission)
    session.commit()

    retrieved = session.exec(
        select(Permission).where(Permission.name == "update_test")
    ).first()
    assert retrieved.updated_at > original_updated_at


def test_permission_deletion_cascade(session: Session):
    """Test that deleting a permission cascades to RolePermission entries."""
    permission = Permission(name="cascade_test", description="Cascade test permission")
    role = Role(name="TestRole", description="Test role")
    session.add_all([permission, role])
    session.commit()

    role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
    session.add(role_permission)
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
    permission1 = Permission(name="perm1", description="Permission 1")
    permission2 = Permission(name="perm2", description="Permission 2")
    role = Role(name="TestRole", description="Test role")
    session.add_all([permission1, permission2, role])
    session.commit()

    role_permission1 = RolePermission(role_id=role.id, permission_id=permission1.id)
    role_permission2 = RolePermission(role_id=role.id, permission_id=permission2.id)
    session.add_all([role_permission1, role_permission2])
    session.commit()

    retrieved_role = session.exec(select(Role).where(Role.name == "TestRole")).first()
    assert len(retrieved_role.permissions) == 2
    assert {p.name for p in retrieved_role.permissions} == {"perm1", "perm2"}

    retrieved_perm = session.exec(
        select(Permission).where(Permission.name == "perm1")
    ).first()
    assert len(retrieved_perm.roles) == 1
    assert retrieved_perm.roles[0].name == "TestRole"


def test_role_users_relationship(session: Session):
    """Test the Role-UserInfo many-to-many relationship."""
    user = UserInfo(
        email="test@example.com",
        user_id=1,
        role="employee",
        created_at=get_utc_now(),
        updated_at=get_utc_now(),
    )
    role = Role(name="TestRole", description="Test role")
    session.add_all([user, role])
    session.commit()

    user_role = UserRole(user_id=user.user_id, role_id=role.id)
    session.add(user_role)
    session.commit()

    retrieved_role = session.exec(select(Role).where(Role.name == "TestRole")).first()
    assert len(retrieved_role.users) == 1
    assert retrieved_role.users[0].email == "test@example.com"

    retrieved_user = session.exec(select(UserInfo).where(UserInfo.user_id == 1)).first()
    assert len(retrieved_user.roles) == 1
    assert retrieved_user.roles[0].name == "TestRole"


def test_seed_permissions(session: Session):
    """Test seeding permissions."""
    from inventory_system.scripts.seed_permissions import seed_permissions

    # Ensure the database is empty
    permissions_before = session.exec(select(Permission)).all()
    print(f"Permissions before seeding: {len(permissions_before)}")

    # Pass the test session to seed_permissions
    seed_permissions(session=session)
    permissions = session.exec(select(Permission)).all()
    print(f"Seeded permissions: {len(permissions)}")  # Debug
    print(f"Permissions: {[p.name for p in permissions]}")  # Debug
    assert len(permissions) >= 9  # Expect at least the defined permissions
    perm_names = {p.name for p in permissions}
    assert "manage_users" in perm_names
    assert "create_inventory" in perm_names
    assert "update_inventory" in perm_names
    assert "delete_inventory" in perm_names
    assert any(p.description for p in permissions if p.name == "manage_users")
    assert all(isinstance(p.created_at, datetime) for p in permissions)
    assert all(isinstance(p.updated_at, datetime) for p in permissions)


def test_permission_audit_logging(session: Session, tmp_path):
    """Test that audit logging captures created_at and updated_at."""
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
