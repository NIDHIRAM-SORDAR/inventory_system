from typing import Any, Dict, List, Optional

import reflex as rx
from sqlmodel import select

from inventory_system.logging.audit_listeners import with_async_audit_context
from inventory_system.models.user import Permission, Role, RolePermission, UserRole
from inventory_system.state.auth import AuthState
from inventory_system.state.bulk_roles_state import BulkOperationsState


class RoleManagementState(rx.State):
    """State for managing roles with database integration."""

    # Role data
    roles: List[Dict[str, Any]] = []
    role_search_query: str = ""
    role_is_loading: bool = False

    # Available permissions for role assignment
    available_permissions: List[Dict[str, Any]] = []

    # Modal states
    role_show_add_modal: bool = False
    role_show_edit_modal: bool = False
    role_show_delete_modal: bool = False
    role_show_permissions_modal: bool = False

    # Form states
    role_form_name: str = ""
    role_form_description: str = ""
    role_editing_id: Optional[int] = None
    role_deleting_id: Optional[int] = None
    role_permissions_id: Optional[int] = None

    # Permission assignment states
    selected_permissions: List[str] = []
    permissions_loading: bool = False

    # Computed variables
    @rx.var
    def filtered_roles(self) -> List[Dict[str, Any]]:
        filtered = [role for role in self.roles if role["is_active"]]
        if self.role_search_query:
            query = self.role_search_query.lower()
            filtered = [
                role
                for role in filtered
                if query in role["name"].lower()
                or query in (role["description"] or "").lower()
            ]
        return filtered

    @rx.var
    def role_assigned_users(self) -> List[str]:
        """Get users assigned to the role being deleted."""
        if self.role_deleting_id is None:
            return []
        with rx.session() as session:
            user_roles = session.exec(
                select(UserRole).where(UserRole.role_id == self.role_deleting_id)
            ).all()
            if not user_roles:
                return []
            from inventory_system.models.user import UserInfo

            user_ids = [ur.user_id for ur in user_roles]
            users = session.exec(
                select(UserInfo).where(UserInfo.id.in_(user_ids))
            ).all()
            return [user.email for user in users]

    @rx.var
    def current_role_permissions(self) -> List[str]:
        """Get permissions for the role being edited."""
        if self.role_permissions_id is None:
            return []
        role = next(
            (r for r in self.roles if r["id"] == self.role_permissions_id), None
        )
        return role["permissions"] if role else []

    # Initial data load
    def load_roles(self) -> None:
        """Load roles from the database."""
        with rx.session() as session:
            roles = session.exec(select(Role)).all()
            self.roles = []
            for role in roles:
                # Get permissions for this role
                role_permissions = session.exec(
                    select(RolePermission).where(RolePermission.role_id == role.id)
                ).all()
                perm_ids = [rp.permission_id for rp in role_permissions]
                permissions = []
                if perm_ids:
                    perms = session.exec(
                        select(Permission).where(Permission.id.in_(perm_ids))
                    ).all()
                    permissions = [perm.name for perm in perms]

                # Count assigned users
                user_count = len(
                    session.exec(
                        select(UserRole).where(UserRole.role_id == role.id)
                    ).all()
                )

                self.roles.append(
                    {
                        "id": role.id,
                        "name": role.name,
                        "description": role.description,
                        "is_active": role.is_active,
                        "permissions": permissions,
                        "user_count": user_count,
                        "created_at": role.created_at.strftime("%Y-%m-%d %H:%M"),
                        "updated_at": role.updated_at.strftime("%Y-%m-%d %H:%M"),
                    }
                )

    def load_permissions(self) -> None:
        """Load available permissions."""
        with rx.session() as session:
            perms = session.exec(select(Permission)).all()
            self.available_permissions = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category or "General",
                }
                for p in perms
            ]

    # Event handlers
    @rx.event
    def set_role_search_query(self, query: str) -> None:
        """Update search query."""
        self.role_search_query = query

    @rx.event
    def set_role_form_name(self, name: str) -> None:
        """Set role form name."""
        self.role_form_name = name

    @rx.event
    def set_role_form_description(self, description: str) -> None:
        """Set role form description."""
        self.role_form_description = description

    # Modal handlers
    @rx.event
    def open_role_add_modal(self) -> None:
        """Open add role modal."""
        self.role_form_name = ""
        self.role_form_description = ""
        self.role_show_add_modal = True

    @rx.event
    def open_role_edit_modal(self, role_id: int) -> None:
        """Open edit role modal."""
        role = next((r for r in self.roles if r["id"] == role_id), None)
        if role:
            self.role_form_name = role["name"]
            self.role_form_description = role["description"] or ""
            self.role_editing_id = role_id
            self.role_show_edit_modal = True

    @rx.event
    def open_role_delete_modal(self, role_id: int) -> None:
        """Open delete confirmation modal."""
        self.role_deleting_id = role_id
        self.role_show_delete_modal = True

    @rx.event
    def open_role_permissions_modal(self, role_id: int) -> None:
        """Open permissions management modal."""
        self.role_permissions_id = role_id
        role = next((r for r in self.roles if r["id"] == role_id), None)
        if role:
            self.selected_permissions = role["permissions"].copy()
        self.load_permissions()
        self.role_show_permissions_modal = True

    @rx.event
    def close_role_modals(self) -> None:
        """Close all modals."""
        self.role_show_add_modal = False
        self.role_show_edit_modal = False
        self.role_show_delete_modal = False
        self.role_show_permissions_modal = False
        self.role_editing_id = None
        self.role_deleting_id = None
        self.role_permissions_id = None
        self.selected_permissions = []

    @rx.event
    def toggle_permission(self, permission_name: str) -> None:
        """Toggle permission selection."""
        if permission_name in self.selected_permissions:
            self.selected_permissions.remove(permission_name)
        else:
            self.selected_permissions.append(permission_name)

    @rx.event
    def select_all_permissions(self):
        """Select all available permissions."""
        self.selected_permissions = [
            perm["name"] for perm in self.available_permissions
        ]

    @rx.event
    def deselect_all_permissions(self):
        """Deselect all permissions."""
        self.selected_permissions = []

    # CRUD operations
    @rx.event
    async def add_role(self):
        """Add a new role."""
        if not self.role_form_name:
            yield rx.toast.error("Name is required")
            return

        self.role_is_loading = True
        try:
            async with with_async_audit_context(
                state=self,
                operation_name="create_role",
                submitted_role_name=self.role_form_name,
                submitted_role_description=self.role_form_description,
            ):
                with rx.session() as session:
                    Role.create_role(
                        name=self.role_form_name,
                        description=self.role_form_description,
                        session=session,
                    )
                    session.commit()
                    self.load_roles()
                    yield AuthState.load_user_data()
                    bulk_state = await self.get_state(BulkOperationsState)
                    async for event in bulk_state.refresh_roles_with_toast():
                        yield event
                    self.close_role_modals()
                    yield rx.toast.success(
                        f"Role '{self.role_form_name}' created successfully"
                    )
        except Exception as e:
            session.rollback()
            yield rx.toast.error(f"Failed to create role: {str(e)}")
        finally:
            self.role_is_loading = False

    @rx.event
    async def update_role(self):
        """Update an existing role."""
        if not self.role_form_name:
            yield rx.toast.error("Name is required")
            return

        self.role_is_loading = True
        try:
            async with with_async_audit_context(
                state=self,
                operation_name="update_role",
                submitted_role_name=self.role_form_name,
                submitted_role_description=self.role_form_description,
            ):
                with rx.session() as session:
                    role = session.exec(
                        select(Role).where(Role.id == self.role_editing_id)
                    ).one_or_none()
                    if role:
                        role.update_role(
                            session=session,
                            name=self.role_form_name,
                            description=self.role_form_description,
                        )
                        session.commit()
                        self.load_roles()
                        yield AuthState.load_user_data()

                        bulk_state = await self.get_state(BulkOperationsState)
                        async for event in bulk_state.refresh_roles_with_toast():
                            yield event
                        self.close_role_modals()
                        yield rx.toast.success(
                            f"Role '{self.role_form_name}' updated successfully"
                        )
        except Exception as e:
            session.rollback()
            yield rx.toast.error(f"Failed to update role: {str(e)}")
        finally:
            self.role_is_loading = False

    @rx.event
    async def delete_role(self):
        """Delete a role."""
        self.role_is_loading = True
        try:
            async with with_async_audit_context(
                state=self,
                operation_name="delete_role",
                selected_role_id_for_deletion=self.role_deleting_id,
            ):
                with rx.session() as session:
                    role = session.exec(
                        select(Role).where(Role.id == self.role_deleting_id)
                    ).one_or_none()
                    if role:
                        # Check if role is assigned to users
                        assigned_users = self.role_assigned_users
                        if assigned_users:
                            yield rx.toast.error(
                                f"Cannot delete role '{role.name}' as it is assigned to users: "
                                f"{', '.join(assigned_users[:3])}"
                                f"{'...' if len(assigned_users) > 3 else ''}. "
                                f"Remove users first."
                            )
                            return
                        Role.delete_role(name=role.name, session=session)
                        session.commit()
                        self.load_roles()
                        yield AuthState.load_user_data()
                        bulk_state = await self.get_state(BulkOperationsState)
                        async for event in bulk_state.refresh_roles_with_toast():
                            yield event
                        self.close_role_modals()
                        yield rx.toast.success(
                            f"Role '{role.name}' deleted successfully"
                        )
        except Exception as e:
            session.rollback()
            yield rx.toast.error(f"Failed to delete role: {str(e)}")
        finally:
            self.role_is_loading = False

    @rx.event
    async def update_role_permissions(self):
        """Update permissions for a role."""
        self.permissions_loading = True
        try:
            async with with_async_audit_context(
                state=self,
                operation_name="update_permission_for_role",
                selected_role_id=self.role_permissions_id,
                selected_permissions=self.selected_permissions,
            ):
                with rx.session() as session:
                    role = session.exec(
                        select(Role).where(Role.id == self.role_permissions_id)
                    ).one_or_none()
                    if role:
                        role.set_permissions(self.selected_permissions, session)
                        session.commit()
                        self.load_roles()
                        yield AuthState.load_user_data()
                        bulk_state = await self.get_state(BulkOperationsState)
                        async for event in bulk_state.refresh_roles_with_toast():
                            yield event
                        self.close_role_modals()
                        yield rx.toast.success(
                            f"Permissions updated for role '{role.name}'"
                        )
        except Exception as e:
            session.rollback()
            yield rx.toast.error(f"Failed to update permissions: {str(e)}")
        finally:
            self.permissions_loading = False
