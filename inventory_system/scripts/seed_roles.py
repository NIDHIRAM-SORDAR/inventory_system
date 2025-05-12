from typing import Optional

import reflex as rx
from sqlmodel import Session, select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Permission, Role


def seed_roles(session: Optional[Session] = None):
    """Seed the Role table with initial roles and assign permissions,
    considering is_active flag."""
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
        session_context = session if session else rx.session()
        session_is_external = session is not None

        # Handle session context
        if not session_is_external:
            with session_context as sess:
                for role_data in roles:
                    _seed_single_role(sess, role_data)
                audit_logger.info("seed_roles_completed", role_count=len(roles))
        else:
            for role_data in roles:
                _seed_single_role(session_context, role_data)
            audit_logger.info("seed_roles_completed", role_count=len(roles))

    except Exception as e:
        audit_logger.error("seed_roles_failed", error=str(e))
        raise


def _seed_single_role(session: Session, role_data: dict):
    """Seed a single role with permissions, handling is_active flag."""
    role_name = role_data["name"]
    try:
        # Check for existing active role
        existing = session.exec(
            select(Role).where(Role.name == role_name, Role.is_active == True)
        ).first()

        if existing:
            audit_logger.info(
                "seed_role_skipped",
                role_name=role_name,
                reason="Active role already exists",
            )
            return

        # Check for inactive role
        inactive_role = session.exec(
            select(Role).where(Role.name == role_name, Role.is_active == False)
        ).first()

        if inactive_role:
            # Reactivate and update
            inactive_role.is_active = True
            inactive_role.description = role_data["description"]
            session.add(inactive_role)
            audit_logger.info(
                "seed_role_reactivated",
                role_name=role_name,
                role_id=inactive_role.id,
            )
            role = inactive_role
        else:
            # Create new role
            role = Role(
                name=role_name,
                description=role_data["description"],
                is_active=True,
            )
            session.add(role)
            audit_logger.info(
                "seed_role_created",
                role_name=role_name,
            )

        session.flush()  # Ensure role.id is available

        # Validate permissions
        permissions = []
        for perm_name in role_data["permissions"]:
            perm = session.exec(
                select(Permission).where(Permission.name == perm_name)
            ).first()
            if not perm:
                audit_logger.warning(
                    "seed_role_permission_missing",
                    role_name=role_name,
                    permission_name=perm_name,
                )
                continue
            permissions.append(perm_name)

        # Assign permissions
        try:
            role.set_permissions(permissions, session)
        except ValueError as perm_error:
            audit_logger.error(
                "seed_role_permission_assignment_failed",
                role_name=role_name,
                error=str(perm_error),
            )
            session.rollback()
            raise

        session.commit()
        audit_logger.info(
            "seed_role_permissions_assigned",
            role_name=role_name,
            permission_count=len(permissions),
        )

    except Exception as e:
        session.rollback()
        audit_logger.error(
            "seed_role_failed",
            role_name=role_name,
            error=str(e),
        )
        raise
