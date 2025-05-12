from pathlib import Path

import pytest
import reflex as rx
from reflex.testing import AppHarness
from sqlmodel import Session, create_engine, select

from inventory_system.models.user import Permission, Role, RolePermission, UserInfo


@pytest.fixture
def session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    rx.Model.metadata.create_all(engine)
    with Session(engine) as session:
        # Clear permissions before each test
        session.exec(Permission.__table__.delete())
        session.commit()
        yield session


@pytest.fixture
def app_harness():
    """Start a Reflex app instance for backend testing."""
    # Assuming the app root is two levels up from the test file
    app_root = Path(__file__).parent.parent.parent
    with AppHarness.create(root=app_root) as harness:
        yield harness


# Permission Model Tests
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


# Role Model Tests
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

    with pytest.raises(ValueError, match="Permissions not found: {'invalid'}"):
        role.set_permissions(["manage_users", "invalid"], session)


# UserInfo Model Tests
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

    with pytest.raises(ValueError, match="Roles not found: {'invalid'}"):
        user.set_roles(["admin", "invalid"], session)


def test_userinfo_permissions(session: Session):
    """Test UserInfo permission retrieval through roles."""
    perm1 = Permission(name="manage_users")
    perm2 = Permission(name="view_inventory")
    role1 = Role(name="admin")
    role2 = Role(name="employee")
    user = UserInfo(email="test@example.com", user_id=1)
    session.add_all([perm1, perm2, role1, role2, user])
    session.commit()

    role1.set_permissions(["manage_users"], session)
    role2.set_permissions(["view_inventory"], session)
    user.set_roles(["admin", "employee"], session)
    session.commit()

    assert set(user.get_permissions()) == {"manage_users", "view_inventory"}
    assert user.has_permission("manage_users") is True
    assert user.has_permission("view_inventory") is True
    assert user.has_permission("delete_inventory") is False
