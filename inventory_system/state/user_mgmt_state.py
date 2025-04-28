from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo
from inventory_system.state.auth import AuthState


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
    selected_role: str = ""
    current_user_role: str = ""

    def check_auth_and_load(self):
        if not self.is_authenticated or not (
            self.authenticated_user_info and "manage_users" in self.user_permissions
        ):
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.is_loading = True
        with rx.session() as session:
            current_user_id = (
                self.authenticated_user_info.user_id
                if self.authenticated_user_info
                else None
            )
            stmt = (
                select(UserInfo, reflex_local_auth.LocalUser.username)
                .join(
                    reflex_local_auth.LocalUser,
                    UserInfo.user_id == reflex_local_auth.LocalUser.id,
                )
                .where(UserInfo.user_id != current_user_id)
            )
            results = session.exec(stmt).all()
            self.users_data = [
                {
                    "username": username,
                    "id": user_info.user_id,
                    "email": user_info.email,
                    "role": user_info.get_roles()[0]
                    if user_info.get_roles()
                    else "none",
                }
                for user_info, username in results
            ]
        self.is_loading = False

    @rx.event
    async def change_user_role(self, user_id: int, selected_role: str):
        if "edit_user" not in self.user_permissions:
            yield rx.toast.error(
                "Permission denied: Cannot change user role", position="bottom-right"
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
            "attempt_change_role",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_user_id=user_id,
            target_role=selected_role,
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
                        "fail_change_role",
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

                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == user_id
                    )
                ).one_or_none()
                if not local_user:
                    self.setvar("admin_error_message", "User not found.")
                    audit_logger.error(
                        "fail_change_role",
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

                target_username = local_user.username
                original_roles = user_info.get_roles()
                if selected_role in original_roles:
                    self.setvar("is_loading", False)
                    yield rx.toast.info(
                        f"No change: User {target_username} "
                        "already has role {selected_role}.",
                        position="bottom-right",
                        duration=5000,
                    )

                session.add(user_info)
                session.refresh(user_info)
                user_info.set_roles([selected_role], session)
                session.commit()

                audit_logger.info(
                    "success_change_role",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_user_id=user_id,
                    original_roles=original_roles,
                    new_role=selected_role,
                    ip_address=ip_address,
                )
                self.setvar(
                    "admin_success_message",
                    f"User {target_username} role changed to {selected_role}.",
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
                self.setvar("admin_error_message", f"Failed to change role: {str(e)}")
                audit_logger.error(
                    "fail_change_role",
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
        if "delete_user" not in self.user_permissions:
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

                target_username = local_user.username
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
        data = self.users_data
        if self.search_value:
            data = [
                u
                for u in data
                if self.search_value.lower() in u["username"].lower()
                or self.search_value.lower() in u["email"].lower()
                or self.search_value.lower() in u["role"].lower()
            ]
        return sorted(data, key=lambda x: x[self.sort_value], reverse=self.sort_reverse)

    @rx.var
    def current_page(self) -> List[Dict[str, Any]]:
        start = (self.page_number - 1) * self.page_size
        end = start + self.page_size
        return self.filtered_users[start:end]

    def open_edit_dialog(self, user_id: int, current_role: str):
        self.target_user_id = user_id
        self.current_user_role = current_role
        self.selected_role = current_role
        self.show_edit_dialog = True

    def cancel_edit_dialog(self):
        self.show_edit_dialog = False
        self.target_user_id = None
        self.selected_role = ""
        self.current_user_role = ""

    def confirm_delete_user(self, user_id: int):
        self.user_to_delete = user_id
        self.show_delete_dialog = True

    def cancel_delete(self):
        self.show_delete_dialog = False
        self.user_to_delete = None

    def set_sort_value(self, value: str):
        self.sort_value = value

    def toggle_sort(self):
        self.sort_reverse = not self.sort_reverse

    def set_search_value(self, value: str):
        self.search_value = value
        self.page_number = 1

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
