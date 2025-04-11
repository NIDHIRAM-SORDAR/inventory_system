import reflex as rx
import reflex_local_auth
from inventory_system.models import UserInfo, Supplier
from sqlmodel import select
from typing import List, Dict, Any, Optional
from ..state import AuthState
from ..utils.register_supplier import register_supplier


class SupplierApprovalState(AuthState):
    users_data: List[Dict[str, Any]] = []
    supplier_error_message: str = ""
    supplier_success_message: str = ""
    is_loading: bool = False
    page_number: int = 1
    page_size: int = 10
    sort_value: str = "username"  # Default sort column
    sort_reverse: bool = False
    search_value: str = ""
    show_approve_dialog: bool = False
    show_revoke_dialog: bool = False
    target_supplier_id: Optional[int] = None

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
                or self.search_value.lower() in u["status"].lower()
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
            stmt = select(
                Supplier.id,
                Supplier.company_name.label("username"),
                Supplier.contact_email.label("email"),
                Supplier.status,
                UserInfo.role,
                UserInfo.user_id,
            ).outerjoin(UserInfo, Supplier.user_info_id == UserInfo.id)
            results = session.exec(stmt).all()
            self.users_data = [
                {
                    "id": row.id,
                    "email": row.email,
                    "role": row.role if row.role else row.status,
                    "username": row.username,
                    "user_id": row.user_id,
                }
                for row in results
            ]
        self.is_loading = False

    def send_welcome_email(self, email: str, username: str, password: str):
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        try:
            print(
                f"Dummy email sent to {email} with username: {username}, password: {password}"
            )
            self.supplier_success_message = f"Temporary password for {username}: {password} (Email not sent - dummy mode)"
        except Exception as e:
            self.supplier_error_message = f"Failed to send email: {str(e)}"

    def change_supplier_status(self, supplier_id: int, make_supplier: bool):
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        with rx.session() as session:
            supplier = session.exec(
                select(Supplier).where(Supplier.id == supplier_id)
            ).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                self.is_loading = False
                return
            if make_supplier:
                if not supplier.user_info_id:
                    default_password = "Supplier123!"
                    try:
                        new_user_id = register_supplier(
                            supplier.company_name,
                            supplier.contact_email,
                            default_password,
                            session,
                        )
                        supplier.user_info_id = (
                            session.exec(
                                select(UserInfo).where(UserInfo.user_id == new_user_id)
                            )
                            .one()
                            .id
                        )
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()
                        self.send_welcome_email(
                            supplier.contact_email,
                            supplier.company_name,
                            default_password,
                        )
                    except Exception as e:
                        self.supplier_error_message = (
                            f"Failed to register supplier: {str(e)}"
                        )
                        session.rollback()
                else:
                    supplier.status = "approved"
                    session.add(supplier)
                    session.commit()
            else:
                try:
                    if supplier.user_info_id:
                        user_info = session.exec(
                            select(UserInfo).where(UserInfo.id == supplier.user_info_id)
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
                        else:
                            session.delete(supplier)
                    else:
                        session.delete(supplier)
                    session.commit()
                except Exception as e:
                    self.supplier_error_message = f"Error rejecting supplier: {str(e)}"
                    session.rollback()
            self.check_auth_and_load()
        self.is_loading = False
        # Reset dialog state
        self.show_approve_dialog = False
        self.show_revoke_dialog = False
        self.target_supplier_id = None

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

    def confirm_change_supplier_status(self, supplier_id: str, approve: bool):
        """Show confirmation dialog for changing supplier status."""
        self.target_supplier_id = supplier_id
        if approve:
            self.show_approve_dialog = True
        else:
            self.show_revoke_dialog = True

    def cancel_supplier_action(self):
        self.show_approve_dialog = False
        self.show_revoke_dialog = False
        self.target_supplier_id = None
