from typing import Any, Dict, List, Optional

import reflex as rx
from sqlmodel import select

from inventory_system.constants import available_colors
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Permission, Role, RolePermission
from inventory_system.state.auth import AuthState


class PermissionsManagementState(rx.State):
    """State for managing permissions with database integration."""

    # Permission data
    permissions: List[Dict[str, Any]] = []
    perm_search_query: str = ""
    perm_selected_category: str = "All"
    perm_is_loading: bool = False

    # Modal states
    perm_show_add_modal: bool = False
    perm_show_edit_modal: bool = False
    perm_show_delete_modal: bool = False

    # Form states
    perm_form_name: str = ""
    perm_form_category: str = ""
    perm_form_description: str = ""
    perm_editing_id: Optional[int] = None
    perm_deleting_id: Optional[int] = None

    # Categories derived from loaded permissions
    @rx.var
    def perm_categories(self) -> List[str]:
        """Dynamically generate categories from loaded permissions."""
        unique_categories = set(
            p["category"] for p in self.permissions if p["category"]
        )
        return ["All"] + sorted(list(unique_categories))

    # Computed variables
    @rx.var
    def filtered_permissions(self) -> List[Dict[str, Any]]:
        filtered = self.permissions
        selected_category = self.perm_selected_category
        if selected_category != "All":
            filtered = [
                p
                for p in filtered
                if (p["category"] if p["category"] is not None else "Uncategorized")
                == selected_category
            ]
        if self.perm_search_query:
            query = self.perm_search_query.lower()
            filtered = [
                p
                for p in filtered
                if query in p["name"].lower()
                or query in p["description"].lower()
                or query
                in (
                    p["category"] if p["category"] is not None else "Uncategorized"
                ).lower()
            ]
        return filtered

    @rx.var
    def filtered_permissions_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group filtered permissions by category, sorted by category name."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for p in self.filtered_permissions:
            cat = p["category"] if p["category"] else "Uncategorized"
            grouped.setdefault(cat, []).append(p)
        # Sort categories alphabetically
        return dict(sorted(grouped.items()))

    @rx.var
    def permission_assigned_roles(self) -> List[str]:
        """Get roles assigned to the permission being deleted."""
        if self.perm_deleting_id is None:
            return []
        with rx.session() as session:
            role_permissions = session.exec(
                select(RolePermission).where(
                    RolePermission.permission_id == self.perm_deleting_id
                )
            ).all()
            role_ids = [rp.role_id for rp in role_permissions]
            if not role_ids:
                return []
            roles = session.exec(select(Role).where(Role.id.in_(role_ids))).all()
            return [role.name for role in roles if role.is_active]

    @rx.var
    def category_color_map(self) -> Dict[str, str]:
        """Create a mapping of roles to colors"""
        color_map_category = {}
        filtered_categories = [
            cat for cat in self.perm_categories if cat.lower() != "all"
        ]
        for category in filtered_categories:
            category_hash = hash(category.lower()) % len(available_colors)
            color_map_category[category] = available_colors[category_hash]
        return color_map_category

    # Initial data load
    def load_permissions(self) -> None:
        """Load permissions from the database."""
        with rx.session() as session:
            perms = session.exec(select(Permission)).all()
            self.permissions = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category
                    if p.category is not None
                    else "Uncategorized",
                }
                for p in perms
            ]

    # Event handlers
    @rx.event
    def set_perm_search_query(self, query: str) -> None:
        """Update search query and reset to first page."""
        self.perm_search_query = query

    @rx.event
    def set_perm_category_filter(self, category: str) -> None:
        """Update category filter and reset to first page."""
        self.perm_selected_category = category

    # Modal handlers
    @rx.event
    def open_perm_add_modal(self) -> None:
        """Open add permission modal."""
        self.perm_form_name = ""
        self.perm_form_category = ""
        self.perm_form_description = ""
        self.perm_show_add_modal = True

    @rx.event
    def open_perm_edit_modal(self, perm_id: int) -> None:
        """Open edit permission modal."""
        with rx.session() as session:
            perm = session.exec(
                select(Permission).where(Permission.id == perm_id)
            ).one_or_none()
            if perm:
                self.perm_form_name = perm.name
                self.perm_form_category = perm.category or ""
                self.perm_form_description = perm.description or ""
                self.perm_editing_id = perm_id
                self.perm_show_edit_modal = True

    @rx.event
    def open_perm_delete_modal(self, perm_id: int) -> None:
        """Open delete confirmation modal."""
        self.perm_deleting_id = perm_id
        self.perm_show_delete_modal = True

    @rx.event
    def close_perm_modals(self) -> None:
        """Close all modals."""
        self.perm_show_add_modal = False
        self.perm_show_edit_modal = False
        self.perm_show_delete_modal = False
        self.perm_editing_id = None
        self.perm_deleting_id = None

    # CRUD operations
    @rx.event
    async def add_permission(self):
        """Add a new permission."""
        if not self.perm_form_name or not self.perm_form_description:
            yield rx.toast.error("Name and description are required")
            return
        self.perm_is_loading = True
        try:
            # Get the AuthState instance from the current state
            auth_state = await self.get_state(AuthState)

            with auth_state.audit_context():
                audit_logger.info(
                    f"{auth_state.username} is attempting to add a new permission",
                    name=self.perm_form_name,
                    description=self.perm_form_description,
                    category=self.perm_form_category,
                )
                with rx.session() as session:
                    Permission.create_permission(
                        name=self.perm_form_name,
                        description=self.perm_form_description,
                        category=self.perm_form_category,
                        session=session,
                    )
                    session.commit()
                    self.load_permissions()
                    self.close_perm_modals()
                    new_perm = session.exec(
                        select(Permission).where(Permission.name == self.perm_form_name)
                    ).one()
                    audit_logger.info(
                        "add_permission_success",
                        permission_id=new_perm.id,
                        name=new_perm.name,
                        description=new_perm.description,
                        category=new_perm.category,
                    )
                    yield AuthState.load_user_data()
                    yield rx.toast.success(
                        f"Permission '{self.perm_form_name}' added successfully"
                    )
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "add_permission_failed",
                name=self.perm_form_name,
                description=self.perm_form_description,
                category=self.perm_form_category,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to add permission: {str(e)}")
        finally:
            self.perm_is_loading = False

    @rx.event
    async def update_permission(self):
        """Update an existing permission."""
        if not self.perm_form_name or not self.perm_form_description:
            yield rx.toast.error("Name and description are required")
            return
        self.perm_is_loading = True
        try:
            auth_state = await self.get_state(AuthState)
            with auth_state.audit_context():
                with rx.session() as session:
                    perm = session.exec(
                        select(Permission).where(Permission.id == self.perm_editing_id)
                    ).one_or_none()
                    if perm:
                        audit_logger.info(
                            f"{auth_state.username} is attempting to update a permission",
                            permission_id=perm.id,
                            name=perm.name,
                            description=perm.description,
                            category=perm.category,
                        )
                        perm.update_permission(
                            session=session,
                            name=self.perm_form_name,
                            description=self.perm_form_description,
                            category=self.perm_form_category,
                        )
                        session.commit()
                        self.load_permissions()
                        yield AuthState.load_user_data()
                        self.close_perm_modals()
                        yield rx.toast.success(
                            f"Permission '{self.perm_form_name}' updated successfully"
                        )
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "update_permission_failed",
                name=self.perm_form_name,
                description=self.perm_form_description,
                category=self.perm_form_category,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to update permission: {str(e)}")
        finally:
            self.perm_is_loading = False

    @rx.event
    async def delete_permission(self):
        """Delete a permission."""
        self.perm_is_loading = True
        try:
            auth_state = await self.get_state(AuthState)
            with auth_state.audit_context():
                with rx.session() as session:
                    perm = session.exec(
                        select(Permission).where(Permission.id == self.perm_deleting_id)
                    ).one_or_none()
                    if perm:
                        role_permissions = session.exec(
                            select(RolePermission).where(
                                RolePermission.permission_id == perm.id
                            )
                        ).all()
                        if role_permissions:
                            role_names = self.permission_assigned_roles
                            yield rx.toast.error(
                                f"Cannot delete permission '{perm.name}' as it is "
                                f"assigned to roles: {', '.join(role_names)}. "
                                "Detach it first."
                            )
                            return

                        # NEW: Log before state
                        audit_logger.info(
                            f"{auth_state.username} is attempting to delete a permission",
                            permission_id=perm.id,
                            name=perm.name,
                            description=perm.description,
                            category=perm.category,
                        )
                        Permission.delete_permission(name=perm.name, session=session)
                        session.commit()
                        self.load_permissions()
                        yield AuthState.load_user_data()
                        self.close_perm_modals()
                        audit_logger.info(
                            "delete_permission_success",
                            permission_id=perm.id,
                            name=perm.name,
                        )
                        yield rx.toast.success("Permission deleted successfully")
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "delete_permission_failed",
                name=perm.name,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to delete permission: {str(e)}")
        finally:
            self.perm_is_loading = False
