import csv
import io
from dataclasses import dataclass
from typing import Any, Dict, List, Set

import reflex as rx
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Permission, Role, UserInfo
from inventory_system.state.auth import AuthState
from inventory_system.state.role_data_service import RoleDataService
from inventory_system.state.user_data_service import UserDataService


@dataclass
class PermissionInfo:
    """Dataclass for individual permission details."""

    id: int
    name: str
    description: str
    category: str


@dataclass
class GroupedPermission:
    """Dataclass for permissions grouped by category."""

    category: str
    permissions: List[PermissionInfo]


class BulkOperationsState(AuthState):
    """State for bulk operations on users and roles."""

    # Bulk user operations
    selected_user_ids: Set[int] = set()  # Using set for faster lookups
    bulk_operation_type: str = "replace"  # "replace", "add", "remove"
    bulk_selected_roles: List[str] = []
    show_bulk_roles_modal: bool = False
    bulk_is_loading: bool = False

    # Bulk role operations
    selected_role_ids: Set[int] = set()
    bulk_role_operation_type: str = "replace"
    bulk_selected_permissions: List[str] = []
    show_bulk_permissions_modal: bool = False
    bulk_role_is_loading: bool = False

    # UI state
    show_user_selection: bool = False
    show_role_selection: bool = False

    # User creation state
    create_user_form_data: Dict[str, Any] = {}

    # Added variables for user table search, sort, pagination, and mobile display
    user_search_value: str = ""  # Search term for users
    user_sort_value: str = "username"  # Column to sort by (default: username)
    user_sort_reverse: bool = False  # Sort direction (False: ascending)
    user_page_number: int = 1  # Current page number
    user_page_size: int = 10  # Items per page
    user_mobile_displayed_count: int = 10  # Number of users shown on mobile

    # Added variables for role table search, sort, pagination, and mobile display
    role_search_value: str = ""  # Search term for roles
    role_sort_value: str = "name"  # Column to sort by (default: name)
    role_sort_reverse: bool = False  # Sort direction (False: ascending)
    role_page_number: int = 1  # Current page number
    role_page_size: int = 10  # Items per page
    role_mobile_displayed_count: int = 10  # Number of roles shown on mobile
    _roles_data: List[Dict[str, Any]] = []

    user_section_open: bool = True
    role_section_open: bool = True
    export_section_open: bool = False

    # Existing computed vars remain unchanged
    @rx.var
    def selected_user_count(self) -> int:
        return len(self.selected_user_ids)

    @rx.var
    def selected_role_count(self) -> int:
        return len(self.selected_role_ids)

    # Added computed var for filtered users based on search and sort
    @rx.var
    def filtered_users(self) -> List[Dict[str, Any]]:
        current_user_id = self.user_id if self.is_authenticated_and_ready else None
        users_data = UserDataService.load_users_data(exclude_user_id=current_user_id)

        return UserDataService.filter_users(
            users_data=users_data,
            search_value=self.user_search_value,
            sort_value=self.user_sort_value,
            sort_reverse=self.user_sort_reverse,
        )

    # Added computed var for current page of users (desktop)
    @rx.var
    def current_users_page(self) -> List[Dict[str, Any]]:
        start = (self.user_page_number - 1) * self.user_page_size
        end = start + self.user_page_size
        return self.filtered_users[start:end]

    # Added computed var for total pages of users
    @rx.var
    def users_total_pages(self) -> int:
        return max(
            1,
            (len(self.filtered_users) + self.user_page_size - 1) // self.user_page_size,
        )

    # Added computed var for mobile displayed users
    @rx.var
    def mobile_displayed_users(self) -> List[Dict[str, Any]]:
        return self.filtered_users[: self.user_mobile_displayed_count]

    # Added computed var to check if more users are available on mobile
    @rx.var
    def has_more_users(self) -> bool:
        return len(self.filtered_users) > self.user_mobile_displayed_count

    # Added computed var for filtered roles based on search and sort
    @rx.var
    def filtered_roles(self) -> List[Dict[str, Any]]:
        roles_data = self._roles_data

        return RoleDataService.filter_roles(
            roles_data=roles_data,
            search_value=self.role_search_value,
            sort_value=self.role_sort_value,
            sort_reverse=self.role_sort_reverse,
        )

    # Added computed var for current page of roles (desktop)
    @rx.var
    def current_roles_page(self) -> List[Dict[str, Any]]:
        start = (self.role_page_number - 1) * self.role_page_size
        end = start + self.role_page_size
        return self.filtered_roles[start:end]

    # Added computed var for total pages of roles
    @rx.var
    def roles_total_pages(self) -> int:
        return max(
            1,
            (len(self.filtered_roles) + self.role_page_size - 1) // self.role_page_size,
        )

    # Added computed var for mobile displayed roles
    @rx.var
    def mobile_displayed_roles(self) -> List[Dict[str, Any]]:
        return self.filtered_roles[: self.role_mobile_displayed_count]

    # Added computed var to check if more roles are available on mobile
    @rx.var
    def has_more_roles(self) -> bool:
        return len(self.filtered_roles) > self.role_mobile_displayed_count

    @rx.event
    def on_mount(self):
        self._roles_data = RoleDataService.load_roles_data()

    @rx.event
    def refresh_role_data(self):
        """Force refresh of role data by triggering re-computation."""
        # Reset pagination and search to ensure clean state
        self.role_page_number = 1
        self.role_mobile_displayed_count = 10
        self._roles_data = RoleDataService.load_roles_data()
        # The computed vars will automatically re-evaluate on next access

    @rx.event
    async def refresh_roles_with_toast(self):
        """Refresh roles and show confirmation."""
        self.refresh_role_data()
        yield rx.toast.info("Role data refreshed")

    # Added methods for user search, sort, and pagination
    def set_user_search_value(self, value: str):
        self.user_search_value = value
        self.user_page_number = 1  # Reset to first page
        self.user_mobile_displayed_count = 10  # Reset mobile display count

    def set_user_sort_value(self, value: str):
        self.user_sort_value = value
        self.user_mobile_displayed_count = 10  # Reset mobile display count

    def toggle_user_sort(self):
        self.user_sort_reverse = not self.user_sort_reverse
        self.user_mobile_displayed_count = 10  # Reset mobile display count

    def user_first_page(self):
        self.user_page_number = 1

    def user_prev_page(self):
        if self.user_page_number > 1:
            self.user_page_number -= 1

    def user_next_page(self):
        if self.user_page_number < self.users_total_pages:
            self.user_page_number += 1

    def user_last_page(self):
        self.user_page_number = self.users_total_pages

    def load_more_users(self):
        self.user_mobile_displayed_count += self.user_page_size

    # Added method for selecting all visible users on mobile
    def select_all_visible_users(self):
        visible_users = self.mobile_displayed_users
        user_ids = [user["id"] for user in visible_users]
        self.selected_user_ids.update(user_ids)

    # Added methods for role search, sort, and pagination
    def set_role_search_value(self, value: str):
        self.role_search_value = value
        self.role_page_number = 1  # Reset to first page
        self.role_mobile_displayed_count = 10  # Reset mobile display count

    def set_role_sort_value(self, value: str):
        self.role_sort_value = value
        self.role_mobile_displayed_count = 10  # Reset mobile display count

    def toggle_role_sort(self):
        self.role_sort_reverse = not self.role_sort_reverse
        self.role_mobile_displayed_count = 10  # Reset mobile display count

    def role_first_page(self):
        self.role_page_number = 1

    def role_prev_page(self):
        if self.role_page_number > 1:
            self.role_page_number -= 1

    def role_next_page(self):
        if self.role_page_number < self.roles_total_pages:
            self.role_page_number += 1

    def role_last_page(self):
        self.role_page_number = self.roles_total_pages

    def load_more_roles(self):
        self.role_mobile_displayed_count += self.role_page_size

    # Added method for selecting all visible roles on mobile
    def select_all_visible_roles(self):
        visible_roles = self.mobile_displayed_roles
        role_ids = [role["id"] for role in visible_roles]
        self.selected_role_ids.update(role_ids)

    def toggle_user_section(self):
        """Toggle the user section open/closed state"""
        self.user_section_open = not self.user_section_open

    def toggle_role_section(self):
        """Toggle the role section open/closed state"""
        self.role_section_open = not self.role_section_open

    def toggle_export_section(self):
        """Toggle the export section open/closed state"""
        self.export_section_open = not self.export_section_open

    @rx.var
    def available_roles_for_bulk(self) -> List[str]:
        """Get available roles for bulk assignment."""
        with rx.session() as session:
            try:
                roles = session.exec(select(Role).where(Role.is_active)).all()
                return [role.name for role in roles]
            except Exception as e:
                audit_logger.error("loading_roles_for_bulk_failed", error=str(e))
                return []

    @rx.var
    def available_permissions_for_bulk(self) -> List[PermissionInfo]:
        """Get available permissions for bulk assignment."""
        with rx.session() as session:
            try:
                perms = session.exec(select(Permission)).all()
                return [
                    PermissionInfo(
                        id=p.id,
                        name=p.name,
                        description=p.description,
                        category=p.category or "Uncategorized",
                    )
                    for p in perms
                ]
            except Exception as e:
                audit_logger.error("loading_permissions_for_bulk_failed", error=str(e))
                return []

    @rx.var
    def grouped_permissions_for_bulk(self) -> List[GroupedPermission]:
        """Get permissions grouped by category for bulk assignment."""
        permissions = self.available_permissions_for_bulk

        # Group permissions by category
        categories: Dict[str, List[PermissionInfo]] = {}
        for perm in permissions:
            category = perm.category or "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(perm)

        # Convert to list of GroupedPermission objects
        return [
            GroupedPermission(category=category, permissions=perms)
            for category, perms in sorted(categories.items())
        ]

    # User selection methods
    @rx.event
    def toggle_user_selection(self, user_id: int) -> None:
        """Toggle user selection for bulk operations."""
        if user_id in self.selected_user_ids:
            self.selected_user_ids.discard(user_id)
        else:
            self.selected_user_ids.add(user_id)

    @rx.event
    def select_all_current_page_users(self) -> None:
        """Select all users on current page."""
        try:
            with rx.session() as session:
                users = session.exec(select(UserInfo).limit(20)).all()
                user_ids = [user.id for user in users]
                self.selected_user_ids.update(user_ids)
        except Exception as e:
            audit_logger.error("select_all_current_page_failed", error=str(e))

    @rx.event
    def deselect_all_users(self) -> None:
        """Deselect all users."""
        self.selected_user_ids.clear()

    # Role selection methods
    @rx.event
    def toggle_role_selection(self, role_id: int) -> None:
        """Toggle role selection for bulk operations."""
        if role_id in self.selected_role_ids:
            self.selected_role_ids.discard(role_id)
        else:
            self.selected_role_ids.add(role_id)

    @rx.event
    def select_all_available_roles(self) -> None:
        """Select all available roles."""
        with rx.session() as session:
            try:
                roles = session.exec(select(Role).where(Role.is_active)).all()
                role_ids = [role.id for role in roles]
                self.selected_role_ids.update(role_ids)
            except Exception as e:
                audit_logger.error("select_all_roles_failed", error=str(e))

    @rx.event
    def deselect_all_roles(self) -> None:
        """Deselect all roles."""
        self.selected_role_ids.clear()

    # Bulk role assignment for users
    @rx.event
    def open_bulk_roles_modal(self):
        """Open bulk roles assignment modal."""
        if not self.selected_user_ids:
            yield rx.toast.error("Please select users first")
            return

        self.bulk_selected_roles = []
        self.bulk_operation_type = "replace"
        self.show_bulk_roles_modal = True

    @rx.event
    def close_bulk_roles_modal(self) -> None:
        """Close bulk roles modal."""
        self.show_bulk_roles_modal = False
        self.bulk_selected_roles = []

    @rx.event
    def set_bulk_operation_type(self, operation: str) -> None:
        """Set bulk operation type."""
        self.bulk_operation_type = operation

    @rx.event
    def toggle_bulk_role(self, role_name: str):
        """Toggle role in bulk selection."""
        if role_name in self.bulk_selected_roles:
            self.bulk_selected_roles.remove(role_name)
        else:
            self.bulk_selected_roles.append(role_name)

    @rx.event
    async def execute_bulk_role_assignment(self):
        """Execute bulk role assignment."""
        if "edit_user" not in self.permissions:
            yield rx.toast.error("Permission denied: Cannot modify user roles")
            return

        if not self.selected_user_ids:
            yield rx.toast.error("No users selected")
            return

        if not self.bulk_selected_roles and self.bulk_operation_type != "remove":
            yield rx.toast.error("Please select at least one role")
            return

        self.bulk_is_loading = True

        try:
            with rx.session() as session:
                user_ids = list(self.selected_user_ids)
                results = UserInfo.bulk_set_roles(
                    user_ids=user_ids,
                    role_names=self.bulk_selected_roles,
                    session=session,
                    operation=self.bulk_operation_type,
                )
                session.commit()

                success_count = len(results["success"])
                failed_count = len(results["failed"])
                unchanged_count = len(results["unchanged"])

                operation_text = {
                    "replace": "assigned to",
                    "add": "added to",
                    "remove": "removed from",
                }[self.bulk_operation_type]

                if success_count > 0:
                    yield rx.toast.success(
                        f"Roles {operation_text} {success_count} user(s) successfully"
                    )

                if failed_count > 0:
                    yield rx.toast.warning(f"Failed to update {failed_count} user(s)")

                if unchanged_count > 0:
                    yield rx.toast.info(f"{unchanged_count} user(s) had no changes")

                audit_logger.info(
                    "bulk_role_assignment_completed",
                    operation=self.bulk_operation_type,
                    user_count=len(user_ids),
                    roles=self.bulk_selected_roles,
                    results=results,
                    acting_user=self.username,
                )

                from inventory_system.state.user_mgmt_state import UserManagementState

                user_mgmt_state = await self.get_state(UserManagementState)
                user_mgmt_state.check_auth_and_load()

                self.close_bulk_roles_modal()
                self.deselect_all_users()

        except Exception as e:
            audit_logger.error(
                "bulk_role_assignment_failed",
                error=str(e),
                user_ids=list(self.selected_user_ids),
                roles=self.bulk_selected_roles,
                acting_user=self.username,
            )
            yield rx.toast.error(f"Bulk operation failed: {str(e)}")

        finally:
            self.bulk_is_loading = False

    # Bulk permission assignment for roles
    @rx.event
    def open_bulk_permissions_modal(self):
        """Open bulk permissions assignment modal."""
        if not self.selected_role_ids:
            yield rx.toast.error("Please select roles first")
            return

        self.bulk_selected_permissions = []
        self.bulk_role_operation_type = "replace"
        self.show_bulk_permissions_modal = True

    @rx.event
    def close_bulk_permissions_modal(self) -> None:
        """Close bulk permissions modal."""
        self.show_bulk_permissions_modal = False
        self.bulk_selected_permissions = []

    @rx.event
    def set_bulk_role_operation_type(self, operation: str) -> None:
        """Set bulk role operation type."""
        self.bulk_role_operation_type = operation

    @rx.event
    def toggle_bulk_permission(self, permission_name: str) -> None:
        """Toggle permission in bulk selection."""
        if permission_name in self.bulk_selected_permissions:
            self.bulk_selected_permissions.remove(permission_name)
        else:
            self.bulk_selected_permissions.append(permission_name)

    @rx.event
    async def execute_bulk_permission_assignment(self):
        """Execute bulk permission assignment."""
        if "manage_roles" not in self.permissions:
            yield rx.toast.error("Permission denied: Cannot modify role permissions")
            return

        if not self.selected_role_ids:
            yield rx.toast.error("No roles selected")
            return

        if (
            not self.bulk_selected_permissions
            and self.bulk_role_operation_type != "remove"
        ):
            yield rx.toast.error("Please select at least one permission")
            return

        self.bulk_role_is_loading = True

        try:
            with rx.session() as session:
                role_ids = list(self.selected_role_ids)
                results = Role.bulk_set_permissions(
                    role_ids=role_ids,
                    permission_names=self.bulk_selected_permissions,
                    session=session,
                    operation=self.bulk_role_operation_type,
                )
                session.commit()

                success_count = len(results["success"])
                failed_count = len(results["failed"])
                unchanged_count = len(results["unchanged"])

                operation_text = {
                    "replace": "assigned to",
                    "add": "added to",
                    "remove": "removed from",
                }[self.bulk_role_operation_type]

                if success_count > 0:
                    yield rx.toast.success(
                        f"Permissions {operation_text} "
                        f"{success_count} role(s) successfully"
                    )

                if failed_count > 0:
                    yield rx.toast.warning(f"Failed to update {failed_count} role(s)")

                if unchanged_count > 0:
                    yield rx.toast.info(f"{unchanged_count} role(s) had no changes")

                audit_logger.info(
                    "bulk_permission_assignment_completed",
                    operation=self.bulk_role_operation_type,
                    role_count=len(role_ids),
                    permissions=self.bulk_selected_permissions,
                    results=results,
                    acting_user=self.username,
                )

                from inventory_system.state.role_state import RoleManagementState

                role_mgmt_state = await self.get_state(RoleManagementState)
                role_mgmt_state.load_roles()

                self.close_bulk_permissions_modal()
                self.deselect_all_roles()

        except Exception as e:
            audit_logger.error(
                "bulk_permission_assignment_failed",
                error=str(e),
                role_ids=list(self.selected_role_ids),
                permissions=self.bulk_selected_permissions,
                acting_user=self.username,
            )
            yield rx.toast.error(f"Bulk operation failed: {str(e)}")

        finally:
            self.bulk_role_is_loading = False

    # Export Methods
    @rx.event
    async def export_users(self):
        """Export users to CSV."""
        try:
            with rx.session() as session:
                users = session.exec(select(UserInfo)).all()
                csv_data = []
                for user in users:
                    csv_data.append(
                        {
                            "id": user.id,
                            "email": user.email,
                            "roles": ",".join([role.name for role in user.roles])
                            if user.roles
                            else "",
                            "created_at": user.created_at.isoformat()
                            if user.created_at
                            else "",
                        }
                    )

                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                yield rx.download(data=csv_content, filename="users_export.csv")

                audit_logger.info(
                    "users_exported",
                    user_count=len(csv_data),
                    acting_user=self.username,
                )
                yield rx.toast.success(f"Exported {len(csv_data)} users to CSV")

        except Exception as e:
            audit_logger.error(
                "user_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")

    @rx.event
    async def export_roles(self):
        """Export roles to CSV."""
        try:
            with rx.session() as session:
                roles = session.exec(select(Role)).all()
                csv_data = []
                for role in roles:
                    csv_data.append(
                        {
                            "id": role.id,
                            "name": role.name,
                            "description": role.description or "",
                            "is_active": role.is_active,
                            "permissions": ",".join(
                                [perm.name for perm in role.permissions]
                            )
                            if role.permissions
                            else "",
                            "created_at": role.created_at.isoformat()
                            if role.created_at
                            else "",
                        }
                    )

                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                yield rx.download(
                    data=csv_content,
                    filename="roles_export.csv",
                )

                audit_logger.info(
                    "roles_exported",
                    role_count=len(csv_data),
                    acting_user=self.username,
                )
                yield rx.toast.success(f"Exported {len(csv_data)} roles to CSV")

        except Exception as e:
            audit_logger.error(
                "role_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")

    @rx.event
    async def export_permissions(self):
        """Export permissions to CSV."""
        try:
            with rx.session() as session:
                permissions = session.exec(select(Permission)).all()
                csv_data = []
                for perm in permissions:
                    csv_data.append(
                        {
                            "id": perm.id,
                            "name": perm.name,
                            "description": perm.description or "",
                            "category": perm.category or "Uncategorized",
                            "created_at": perm.created_at.isoformat()
                            if perm.created_at
                            else "",
                        }
                    )

                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                yield rx.download(
                    data=csv_content,
                    filename="permissions_export.csv",
                )

                audit_logger.info(
                    "permissions_exported",
                    permission_count=len(csv_data),
                    acting_user=self.username,
                )
                yield rx.toast.success(f"Exported {len(csv_data)} permissions to CSV")

        except Exception as e:
            audit_logger.error(
                "permission_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")
