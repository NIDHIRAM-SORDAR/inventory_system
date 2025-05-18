# inventory_system/scripts/seed_permissions.py
from typing import Optional

import reflex as rx
from sqlmodel import Session, select

from inventory_system.models.user import Permission


def seed_permissions(session: Optional[Session] = None):
    """Seed the Permission table with initial permissions."""
    print("Starting seeding...")
    permissions = [
        {
            "name": "view_supplier",
            "description": "View supplier records",
            "category": "Suppliers",
        },
        {
            "name": "create_supplier",
            "description": "Create supplier records",
            "category": "Suppliers",
        },
        {
            "name": "edit_supplier",
            "description": "Edit supplier records",
            "category": "Suppliers",
        },
        {
            "name": "delete_supplier",
            "description": "Delete supplier records",
            "category": "Suppliers",
        },
        {"name": "view_user", "description": "View user accounts", "category": "Users"},
        {
            "name": "create_user",
            "description": "Create user accounts",
            "category": "Users",
        },
        {"name": "edit_user", "description": "Edit user accounts", "category": "Users"},
        {
            "name": "delete_user",
            "description": "Delete user accounts",
            "category": "Users",
        },
        {
            "name": "view_inventory",
            "description": "View inventory data",
            "category": "Inventory",
        },
        {
            "name": "create_inventory",
            "description": "Create new inventory items",
            "category": "Inventory",
        },
        {
            "name": "update_inventory",
            "description": "Update existing inventory item details",
            "category": "Inventory",
        },
        {
            "name": "delete_inventory",
            "description": "Delete inventory items",
            "category": "Inventory",
        },
        {
            "name": "view_profile",
            "description": "View own user profile",
            "category": "Users",
        },
        {
            "name": "edit_profile",
            "description": "Edit own user profile (email, password, etc.)",
            "category": "Users",
        },
        {
            "name": "manage_roles",
            "description": "Create, read, update, delete roles",
            "category": "Administration",
        },
        {
            "name": "manage_users",
            "description": "Manage all user-related actions",
            "category": "Administration",
        },
        {
            "name": "manage_suppliers",
            "description": "Manage all supplier-related actions",
            "category": "Suppliers",
        },
        {
            "name": "manage_supplier_approval",
            "description": "Approve or reject supplier registrations",
            "category": "Suppliers",
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
                            name=perm["name"],
                            description=perm["description"],
                            category=perm["category"],
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
                        name=perm["name"],
                        description=perm["description"],
                        category=perm["category"],
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
