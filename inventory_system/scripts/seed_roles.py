# inventory_system/scripts/seed_roles.py
from typing import Optional

import reflex as rx
from sqlmodel import Session, select

from inventory_system.models.user import Role


def seed_roles(session: Optional[Session] = None):
    """Seed the Role table with initial roles and assign permissions."""
    print("Starting role seeding...")
    roles = [
        {
            "name": "admin",
            "description": "Full system access for administrators",
            "permissions": [
                "manage_users",
                "view_user",
                "create_user",
                "edit_user",
                "delete_user",
                "manage_suppliers",
                "view_supplier",
                "create_supplier",
                "edit_supplier",
                "delete_supplier",
                "manage_supplier_approval",
                "view_inventory",
                "create_inventory",
                "update_inventory",
                "delete_inventory",
                "manage_roles",
                "view_profile",
                "edit_profile",
            ],
        },
        {
            "name": "employee",
            "description": "General staff managing inventory",
            "permissions": [
                "view_inventory",
                "create_inventory",
                "update_inventory",
                "view_supplier",
                "view_profile",
                "edit_profile",
            ],
        },
        {
            "name": "supplier",
            "description": "Suppliers managing their own records and inventory",
            "permissions": [
                "view_supplier",
                "edit_supplier",
                "view_inventory",
                "create_inventory",
                "update_inventory",
                "view_profile",
                "edit_profile",
            ],
        },
        {
            "name": "inventory_manager",
            "description": "Manages all inventory operations",
            "permissions": [
                "view_inventory",
                "create_inventory",
                "update_inventory",
                "delete_inventory",
                "view_supplier",
                "view_profile",
                "edit_profile",
            ],
        },
        {
            "name": "supplier_manager",
            "description": "Manages supplier relationships and approvals",
            "permissions": [
                "view_supplier",
                "create_supplier",
                "edit_supplier",
                "delete_supplier",
                "manage_supplier_approval",
                "view_profile",
                "edit_profile",
            ],
        },
        {
            "name": "auditor",
            "description": "Read-only access for auditing purposes",
            "permissions": [
                "view_user",
                "view_supplier",
                "view_inventory",
                "view_profile",
            ],
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
                for role_data in roles:
                    existing = sess.exec(
                        select(Role).where(Role.name == role_data["name"])
                    ).first()
                    if not existing:
                        role = Role(
                            name=role_data["name"], description=role_data["description"]
                        )
                        sess.add(role)
                        sess.commit()  # Commit to get role.id
                        role.set_permissions(role_data["permissions"], sess)
                        sess.commit()
                        print(
                            f"Added role: {role_data['name']} with "
                            " {len(role_data['permissions'])} permissions"
                        )
                    else:
                        print(f"Role already exists: {role_data['name']}")
                print("Role seeding completed")
        else:
            for role_data in roles:
                existing = session.exec(
                    select(Role).where(Role.name == role_data["name"])
                ).first()
                if not existing:
                    role = Role(
                        name=role_data["name"], description=role_data["description"]
                    )
                    session.add(role)
                    session.commit()  # Commit to get role.id
                    role.set_permissions(role_data["permissions"], session)
                    session.commit()
                    print(
                        f"Added role: {role_data['name']} with "
                        " {len(role_data['permissions'])} permissions"
                    )
                else:
                    print(f"Role already exists: {role_data['name']}")
            print("Role seeding completed")
    except Exception as e:
        print(f"Role seeding error: {e}")
        raise


if __name__ == "__main__":
    seed_roles()
