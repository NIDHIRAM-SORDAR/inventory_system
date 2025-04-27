# inventory_system/scripts/seed_permissions.py
from typing import Optional

import reflex as rx
from sqlmodel import Session, select

from inventory_system.models.user import Permission


def seed_permissions(session: Optional[Session] = None):
    """Seed the Permission table with initial permissions."""
    print("Starting seeding...")
    permissions = [
        {"name": "view_supplier", "description": "View supplier records"},
        {"name": "create_supplier", "description": "Create supplier records"},
        {"name": "edit_supplier", "description": "Edit supplier records"},
        {"name": "delete_supplier", "description": "Delete supplier records"},
        {"name": "view_user", "description": "View user accounts"},
        {"name": "create_user", "description": "Create user accounts"},
        {"name": "edit_user", "description": "Edit user accounts"},
        {"name": "delete_user", "description": "Delete user accounts"},
        {"name": "view_inventory", "description": "View inventory data"},
        {"name": "create_inventory", "description": "Create new inventory items"},
        {
            "name": "update_inventory",
            "description": "Update existing inventory item details",
        },
        {"name": "delete_inventory", "description": "Delete inventory items"},
        {"name": "view_profile", "description": "View own user profile"},
        {
            "name": "edit_profile",
            "description": "Edit own user profile (email, password, etc.)",
        },
        {"name": "manage_roles", "description": "Create, read, update, delete roles"},
        {"name": "manage_users", "description": "Manage all user-related actions"},
        {
            "name": "manage_suppliers",
            "description": "Manage all supplier-related actions",
        },
        {
            "name": "manage_supplier_approval",
            "description": "Approve or reject supplier registrations",
        },
    ]

    try:
        # Use provided session or create a new one
        if session is None:
            print("Using rx.session()")
            session_context = rx.session()
        else:
            print("Using provided session")
            session_context = session

        # Handle session context
        if session is None:
            with session_context as sess:
                for perm in permissions:
                    existing = sess.exec(
                        select(Permission).where(Permission.name == perm["name"])
                    ).first()
                    if not existing:
                        permission = Permission(
                            name=perm["name"], description=perm["description"]
                        )
                        sess.add(permission)
                        print(f"Added permission: {perm['name']}")
                    else:
                        print(f"Permission already exists: {perm['name']}")
                sess.commit()
                print("Seeding completed")
        else:
            for perm in permissions:
                existing = session.exec(
                    select(Permission).where(Permission.name == perm["name"])
                ).first()
                if not existing:
                    permission = Permission(
                        name=perm["name"], description=perm["description"]
                    )
                    session.add(permission)
                    print(f"Added permission: {perm['name']}")
                else:
                    print(f"Permission already exists: {perm['name']}")
            session.commit()
            print("Seeding completed")
    except Exception as e:
        print(f"Seeding error: {e}")
        raise


if __name__ == "__main__":
    seed_permissions()
