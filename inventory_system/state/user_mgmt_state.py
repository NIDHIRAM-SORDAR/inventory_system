from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.constants import available_colors
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role, UserInfo, UserRole
from inventory_system.state.auth import AuthState
from inventory_system.state.user_data_service import UserDataService


class UserManagementState(AuthState):
    users_data: List[Dict[str, Any]] = []
    admin_error_message: str = ""
    admin_success_message: str = ""
    is_loading: bool = False
    show_delete_dialog: bool = False
    user_to_delete: Optional[int] = None
    page_number: int = 1
    page_size: int = 10
    sort_value: str = "username"
    sort_reverse: bool = False
    search_value: str = ""
    show_edit_dialog: bool = False
    target_user_id: Optional[int] = None
    # Changed from single role to multiple roles support
    selected_roles: List[str] = []
    current_user_roles: List[str] = []
    active_tab: str = "profiles"

    # New state variables for mobile layout
    mobile_displayed_count: int = 10  # Initial number of users to display on mobile

    def check_auth_and_load(self):
        if not self.is_authenticated or not (
            self.is_authenticated_and_ready and "manage_users" in self.permissions
        ):
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.is_loading = True
        current_user_id = self.user_id if self.is_authenticated_and_ready else None
        self.users_data = UserDataService.load_users_data(
            exclude_user_id=current_user_id
        )
        self.is_loading = False

    @rx.var
    def available_roles(self) -> List[str]:
        """Get all available roles from the database dynamically"""
        with rx.session() as session:
            try:
                # Get all roles from the database
                roles = session.exec(select(Role)).all()
                role_names = [role.name for role in roles]
                all_roles = set(role_names)

                return sorted(list(all_roles))
            except Exception as e:
                # Fallback to common roles if database query fails
                audit_logger.error(
                    "loading_roles_failed",
                    reason=f"Database error: {str(e)}",
                )
                return sorted(["admin", "employee", "manager", "viewer"])

    @rx.var
    def role_color_map(self) -> Dict[str, str]:
        """Create a mapping of roles to colors"""

        color_map = {}
        for role in self.available_roles:
            role_hash = hash(role.lower()) % len(available_colors)
            color_map[role] = available_colors[role_hash]
        return color_map

    @rx.event
    async def change_user_roles(self, user_id: int, selected_roles: List[str]):
        """Updated to handle multiple roles assignment"""
        if "edit_user" not in self.permissions:
            yield rx.toast.error(
                "Permission denied: Cannot change user roles", position="bottom-right"
            )
            return

        if not selected_roles:
            yield rx.toast.error(
                "Please select at least one role", position="bottom-right"
            )
            return

        self.is_loading = True
        self.setvar("admin_error_message", "")
        self.setvar("admin_success_message", "")
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_change_roles",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_user_id=user_id,
            target_roles=selected_roles,
            ip_address=ip_address,
        )
        with rx.session() as session:
            try:
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == user_id)
                    .with_for_update()
                ).one_or_none()
                if not user_info:
                    self.setvar("admin_error_message", "User info not found.")
                    audit_logger.error(
                        "fail_change_roles",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_user_id=user_id,
                        reason="User info not found",
                        ip_address=ip_address,
                    )
                    self.setvar("is_loading", False)
                    yield rx.toast.error(
                        self.admin_error_message, position="bottom-right", duration=5000
                    )
                    return

                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == user_id
                    )
                ).one_or_none()
                if not local_user:
                    self.setvar("admin_error_message", "User not found.")
                    audit_logger.error(
                        "fail_change_roles",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_user_id=user_id,
                        reason="Local user not found",
                        ip_address=ip_address,
                    )
                    self.setvar("is_loading", False)
                    yield rx.toast.error(
                        self.admin_error_message, position="bottom-right", duration=5000
                    )
                    return

                target_username = local_user.username
                original_roles = user_info.get_roles()

                # Check if roles are actually changing
                if set(selected_roles) == set(original_roles):
                    self.setvar("is_loading", False)
                    yield rx.toast.info(
                        f"No change: User {target_username} already has these roles.",
                        position="bottom-right",
                        duration=5000,
                    )
                    return

                session.add(user_info)
                session.refresh(user_info)
                user_info.set_roles(selected_roles, session)
                session.commit()

                audit_logger.info(
                    "success_change_roles",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_user_id=user_id,
                    original_roles=original_roles,
                    new_roles=selected_roles,
                    ip_address=ip_address,
                )
                roles_str = ", ".join(selected_roles)
                self.setvar(
                    "admin_success_message",
                    f"User {target_username} roles updated to: {roles_str}.",
                )
                self.check_auth_and_load()
                self.setvar("is_loading", False)
                self.setvar("show_edit_dialog", False)
                self.setvar("target_user_id", None)
                yield rx.toast.success(
                    self.admin_success_message, position="bottom-right", duration=5000
                )

            except Exception as e:
                session.rollback()
                self.setvar("admin_error_message", f"Failed to change roles: {str(e)}")
                audit_logger.error(
                    "fail_change_roles",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_user_id=user_id,
                    reason=f"Database error: {str(e)}",
                    ip_address=ip_address,
                )
                self.setvar("is_loading", False)
                yield rx.toast.error(
                    self.admin_error_message, position="bottom-right", duration=5000
                )

    @rx.event
    async def delete_user(self):
        if "delete_user" not in self.permissions:
            yield rx.toast.error(
                "Permission denied: Cannot delete user", position="bottom-right"
            )
            return
        if self.user_to_delete is None:
            return
        self.is_loading = True
        self.setvar("admin_error_message", "")
        self.setvar("admin_success_message", "")
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        target_user_id = self.user_to_delete
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_delete_user",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_user_id=target_user_id,
            ip_address=ip_address,
        )
        with rx.session() as session:
            try:
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.user_to_delete)
                    .with_for_update()
                ).one_or_none()
                if not user_info:
                    self.setvar("admin_error_message", "User not found.")
                    audit_logger.error(
                        "fail_delete_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_user_id=target_user_id,
                        reason="User not found",
                        ip_address=ip_address,
                    )
                    self.setvar("is_loading", False)
                    yield rx.toast.error(
                        self.admin_error_message, position="bottom-right", duration=5000
                    )
                    return

                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == user_info.user_id
                    )
                ).one_or_none()
                if not local_user:
                    self.setvar("admin_error_message", "Local user not found.")
                    audit_logger.error(
                        "fail_delete_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_user_id=target_user_id,
                        reason="Local user not found",
                        ip_address=ip_address,
                    )
                    self.setvar("is_loading", False)
                    yield rx.toast.error(
                        self.admin_error_message, position="bottom-right", duration=5000
                    )
                    return

                target_username = local_user.username

                # CRITICAL: Delete UserRole records first to prevent orphaned records
                # This handles the case where UserRole.user_id references userinfo.user_id
                session.exec(
                    UserRole.__table__.delete().where(
                        UserRole.user_id == user_info.user_id
                    )
                )

                # Then delete UserInfo and LocalUser
                if local_user:
                    session.delete(local_user)
                session.delete(user_info)
                session.commit()

                audit_logger.info(
                    "success_delete_user",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_user_id=target_user_id,
                    ip_address=ip_address,
                )
                self.setvar(
                    "admin_success_message",
                    f"User {target_username} deleted successfully.",
                )
                self.check_auth_and_load()
                self.setvar("is_loading", False)
                self.setvar("show_delete_dialog", False)
                self.setvar("user_to_delete", None)
                yield rx.toast.success(
                    self.admin_success_message, position="bottom-right", duration=5000
                )

            except Exception as e:
                session.rollback()
                self.setvar("admin_error_message", f"Failed to delete user: {str(e)}")
                audit_logger.error(
                    "fail_delete_user",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_user_id=target_user_id,
                    reason=f"Database error: {str(e)}",
                    ip_address=ip_address,
                )
                self.setvar("is_loading", False)
                yield rx.toast.error(
                    self.admin_error_message, position="bottom-right", duration=5000
                )

    @rx.var
    def total_pages(self) -> int:
        return max(1, (len(self.filtered_users) + self.page_size - 1) // self.page_size)

    @rx.var
    def filtered_users(self) -> List[Dict[str, Any]]:
        return UserDataService.filter_users(
            users_data=self.users_data,
            search_value=self.search_value,
            sort_value=self.sort_value,
            sort_reverse=self.sort_reverse,
        )

    @rx.var
    def current_page(self) -> List[Dict[str, Any]]:
        start = (self.page_number - 1) * self.page_size
        end = start + self.page_size
        return self.filtered_users[start:end]

    @rx.var
    def mobile_displayed_users(self) -> List[Dict[str, Any]]:
        """Computes the list of users to display on mobile based on mobile_displayed_count."""
        return self.filtered_users[: self.mobile_displayed_count]

    @rx.var
    def has_more_users(self) -> bool:
        """Determines if there are more users to load on mobile."""
        return len(self.filtered_users) > self.mobile_displayed_count

    def load_more(self):
        """Increments the number of displayed users on mobile by page_size."""
        self.mobile_displayed_count += self.page_size

    def open_edit_dialog(self, user_id: int, current_roles: List[str]):
        """Updated to handle multiple roles"""
        self.target_user_id = user_id
        self.current_user_roles = current_roles
        self.selected_roles = (
            current_roles.copy()
        )  # Copy the list to avoid reference issues
        self.show_edit_dialog = True

    def cancel_edit_dialog(self):
        self.show_edit_dialog = False
        self.target_user_id = None
        self.selected_roles = []
        self.current_user_roles = []

    def confirm_delete_user(self, user_id: int):
        self.user_to_delete = user_id
        self.show_delete_dialog = True

    def cancel_delete(self):
        self.show_delete_dialog = False
        self.user_to_delete = None

    def set_sort_value(self, value: str):
        self.sort_value = value
        self.mobile_displayed_count = 10  # Reset for mobile

    def toggle_sort(self):
        self.sort_reverse = not self.sort_reverse
        self.mobile_displayed_count = 10  # Reset for mobile

    def set_search_value(self, value: str):
        self.search_value = value
        self.page_number = 1  # For desktop pagination
        self.mobile_displayed_count = 10  # Reset for mobile

    # New methods for handling multiple role selection
    def toggle_role_selection(self, role: str):
        """Toggle a role in the selected roles list"""
        if role in self.selected_roles:
            self.selected_roles = [r for r in self.selected_roles if r != role]
        else:
            self.selected_roles = self.selected_roles + [role]

    def first_page(self):
        self.page_number = 1

    def prev_page(self):
        if self.page_number > 1:
            self.page_number -= 1

    def next_page(self):
        if self.page_number < self.total_pages:
            self.page_number += 1

    def last_page(self):
        self.page_number = self.total_pages

    def set_active_tab(self, tab: str):
        self.active_tab = tab
