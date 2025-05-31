# role_data_service.py
from typing import Any, Dict, List

import reflex as rx
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role


class RoleDataService:
    """Shared service for loading role data across different states."""

    @staticmethod
    def load_roles_data(include_inactive: bool = True) -> List[Dict[str, Any]]:
        """Load roles data as dictionaries."""
        with rx.session() as session:
            try:
                stmt = select(Role)
                if not include_inactive:
                    stmt = stmt.where(Role.is_active)

                roles = session.exec(stmt).all()

                return [
                    {
                        "id": role.id,
                        "name": role.name,
                        "description": role.description,
                        "is_active": role.is_active,
                        "created_at": role.created_at,
                        # Add permissions if needed
                        "permissions": [perm.name for perm in role.permissions]
                        if hasattr(role, "permissions")
                        else [],
                    }
                    for role in roles
                ]
            except Exception as e:
                audit_logger.error("loading_roles_data_failed", error=str(e))
                return []

    @staticmethod
    def filter_roles(
        roles_data: List[Dict[str, Any]],
        search_value: str = "",
        sort_value: str = "name",
        sort_reverse: bool = False,
    ) -> List[Dict[str, Any]]:
        """Filter and sort roles data."""
        data = roles_data

        if search_value:
            search_lower = search_value.lower()
            data = [
                r
                for r in data
                if search_lower in r["name"].lower()
                or (r["description"] and search_lower in r["description"].lower())
            ]

        return sorted(data, key=lambda x: x[sort_value], reverse=sort_reverse)
