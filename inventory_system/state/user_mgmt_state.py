from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.models.user import UserInfo
from inventory_system.state.auth import AuthState


class UserManagementState(AuthState):
    users_data: List[Dict[str, Any]] = []
    admin_error_message: str = ""
    is_loading: bool = False
    show_delete_dialog: bool = False
    user_to_delete: Optional[int] = None
    page_number: int = 1
    page_size: int = 10  # Items per page
    sort_value: str = "username"  # Default sort column
    sort_reverse: bool = False
    search_value: str = ""
    show_admin_dialog: bool = False  # New for Make Admin
    show_employee_dialog: bool = False  # New for Make Employee
    target_user_id: Optional[int] = None  # Reuse for all actions

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

    def check_auth_and_load(self):
        if not self.is_authenticated or (
            self.authenticated_user_info and not self.authenticated_user_info.is_admin
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
                    "role": user_info.role,
                }
                for user_info, username in results
            ]
        self.is_loading = False

    def change_user_role(self, user_id: int, make_admin: bool):
        self.is_loading = True
        self.admin_error_message = ""
        with rx.session() as session:
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == user_id)
            ).one_or_none()
            if not user_info:
                self.admin_error_message = "User info not found."
                self.is_loading = False
                return
            user_info.is_admin = make_admin
            if make_admin:
                user_info.is_supplier = False
            user_info.set_role()
            session.add(user_info)
            session.commit()
            self.check_auth_and_load()
        self.is_loading = False
        self.show_admin_dialog = False  # Close dialogs
        self.show_employee_dialog = False
        self.target_user_id = None

    def confirm_change_role(self, user_id: int, make_admin: bool):
        self.target_user_id = user_id
        if make_admin:
            self.show_admin_dialog = True
        else:
            self.show_employee_dialog = True

    def cancel_role_change(self):
        self.show_admin_dialog = False
        self.show_employee_dialog = False
        self.target_user_id = None

    def confirm_delete_user(self, user_id: int):
        self.user_to_delete = user_id
        self.show_delete_dialog = True

    def cancel_delete(self):
        self.show_delete_dialog = False
        self.user_to_delete = None

    def delete_user(self):
        if self.user_to_delete is None:
            return
        self.is_loading = True
        self.admin_error_message = ""
        with rx.session() as session:
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == self.user_to_delete)
            ).one_or_none()
            if user_info:
                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == user_info.user_id
                    )
                ).one_or_none()
                if local_user:
                    session.delete(local_user)
                session.delete(user_info)
                try:
                    session.commit()
                    self.check_auth_and_load()
                except Exception as e:
                    self.admin_error_message = f"Error deleting user: {str(e)}"
                    session.rollback()
        self.show_delete_dialog = False
        self.user_to_delete = None
        self.is_loading = False

    def set_sort_value(self, value: str):
        self.sort_value = value

    def toggle_sort(self):
        self.sort_reverse = not self.sort_reverse

    def set_search_value(self, value: str):
        self.search_value = value
        self.page_number = 1  # Reset to first page on search

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
