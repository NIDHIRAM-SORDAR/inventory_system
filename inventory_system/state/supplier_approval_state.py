from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Supplier, UserInfo
from inventory_system.state.auth import AuthState

from ..utils.register_supplier import register_supplier


class SupplierApprovalState(AuthState):
    users_data: List[Dict[str, Any]] = []
    supplier_error_message: str = ""
    supplier_success_message: str = ""
    is_loading: bool = False
    page_number: int = 1
    page_size: int = 10
    sort_value: str = "username"
    sort_reverse: bool = False
    search_value: str = ""
    show_approve_dialog: bool = False
    show_revoke_dialog: bool = False
    show_delete_dialog: bool = False
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

    def show_toast(self, message: str, is_error: bool = False):
        """Helper method to display toast notifications."""
        if is_error:
            rx.toast.error(
                message,
                position="bottom-right",
                # duration=5000,
            )
        else:
            rx.toast.success(
                message,
                position="bottom-right",
                # duration=5000,
            )

    def send_welcome_email(self, email: str, username: str, password: str):
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        try:
            print(
                f"Dummy email to {email} with username: {username}, "
                f"password: {password}"
            )
            self.supplier_success_message = (
                f"Temporary password for {username}: {password} "
                "(Email not sent - dummy)"
            )
            self.show_toast(self.supplier_success_message)
            self.supplier_success_message = ""
        except Exception as e:
            self.supplier_error_message = f"Failed to send email: {str(e)}"
            self.show_toast(self.supplier_error_message, is_error=True)
            self.supplier_error_message = ""

    def delete_supplier(self, supplier_id: int):
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_delete_supplier",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_supplier_id=supplier_id,
            ip_address=ip_address,
        )

        with rx.session() as session:
            supplier = session.exec(
                select(Supplier).where(Supplier.id == supplier_id)
            ).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                self.show_toast(self.supplier_error_message, is_error=True)
                self.is_loading = False
                audit_logger.error(
                    "fail_delete_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    reason="Supplier not found",
                    ip_address=ip_address,
                )
                self.show_delete_dialog = False
                self.target_supplier_id = None
                return

            target_supplier_company_name = supplier.company_name
            associated_user_id = None
            associated_local_user_id = None

            try:
                if supplier.user_info_id:
                    audit_logger.info(
                        "attempt_delete_associated_supplier_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        supplier_id=supplier_id,
                        supplier_company_name=target_supplier_company_name,
                        associated_user_info_id=supplier.user_info_id,
                        ip_address=ip_address,
                    )
                    user_info = session.exec(
                        select(UserInfo).where(UserInfo.id == supplier.user_info_id)
                    ).one_or_none()
                    if user_info:
                        associated_user_id = user_info.id
                        associated_local_user_id = user_info.user_id
                        local_user = session.exec(
                            select(reflex_local_auth.LocalUser).where(
                                reflex_local_auth.LocalUser.id == user_info.user_id
                            )
                        ).one_or_none()
                        if local_user:
                            session.delete(local_user)
                            session.flush()
                        session.delete(user_info)
                session.delete(supplier)
                session.commit()

                audit_logger.info(
                    "success_delete_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    deleted_user_info_id=associated_user_id,
                    deleted_local_user_id=associated_local_user_id,
                    ip_address=ip_address,
                )
                self.supplier_success_message = (
                    f"Supplier {target_supplier_company_name} deleted successfully."
                )
                if associated_user_id:
                    self.supplier_success_message += " Associated user account deleted."
                self.show_toast(self.supplier_success_message)
                self.supplier_success_message = ""

            except Exception as e:
                self.supplier_error_message = f"Error deleting supplier: {str(e)}"
                self.show_toast(self.supplier_error_message, is_error=True)
                audit_logger.error(
                    "fail_delete_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    reason=f"Database error: {e}",
                    ip_address=ip_address,
                )
                session.rollback()

            self.check_auth_and_load()
            self.is_loading = False
            self.show_delete_dialog = False
            self.target_supplier_id = None

    def approve_supplier(self, supplier_id: int):
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_approve_supplier",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_supplier_id=supplier_id,
            ip_address=ip_address,
        )

        with rx.session() as session:
            supplier = session.exec(
                select(Supplier).where(Supplier.id == supplier_id)
            ).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                self.show_toast(self.supplier_error_message, is_error=True)
                self.is_loading = False
                audit_logger.error(
                    "fail_approve_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    reason="Supplier not found",
                    ip_address=ip_address,
                )
                self.show_approve_dialog = False
                self.target_supplier_id = None
                return

            target_supplier_company_name = supplier.company_name

            if not supplier.user_info_id:
                default_password = "Supplier123!"
                try:
                    audit_logger.info(
                        "attempt_register_supplier_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        supplier_id=supplier_id,
                        supplier_company_name=target_supplier_company_name,
                        supplier_email=supplier.contact_email,
                        ip_address=ip_address,
                    )

                    new_user_id = register_supplier(
                        supplier.company_name,
                        supplier.contact_email,
                        default_password,
                        session,
                    )
                    new_user_info = session.exec(
                        select(UserInfo).where(UserInfo.user_id == new_user_id)
                    ).one()
                    supplier.user_info_id = new_user_info.id
                    supplier.status = "approved"
                    session.add(supplier)
                    session.commit()

                    audit_logger.info(
                        "success_approve_supplier_new_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        target_supplier_company_name=target_supplier_company_name,
                        created_user_id=new_user_id,
                        ip_address=ip_address,
                    )
                    self.send_welcome_email(
                        supplier.contact_email,
                        supplier.company_name,
                        default_password,
                    )
                    self.supplier_success_message = (
                        f"Supplier {target_supplier_company_name} approved and "
                        "user account created."
                    )
                    self.show_toast(self.supplier_success_message)
                    self.supplier_success_message = ""

                except Exception as e:
                    self.supplier_error_message = (
                        f"Failed to register supplier user: {str(e)}"
                    )
                    self.show_toast(self.supplier_error_message, is_error=True)
                    audit_logger.error(
                        "fail_register_supplier_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        target_supplier_company_name=target_supplier_company_name,
                        reason=f"Error during registration: {e}",
                        ip_address=ip_address,
                    )
                    session.rollback()
            else:
                try:
                    supplier.status = "approved"
                    session.add(supplier)
                    session.commit()
                    audit_logger.info(
                        "success_approve_supplier_existing_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        target_supplier_company_name=target_supplier_company_name,
                        associated_user_info_id=supplier.user_info_id,
                        ip_address=ip_address,
                    )
                    self.supplier_success_message = (
                        f"Supplier {target_supplier_company_name} status set to "
                        "approved."
                    )
                    self.show_toast(self.supplier_success_message)
                    self.supplier_success_message = ""
                except Exception as e:
                    session.rollback()
                    self.supplier_error_message = (
                        f"Failed to update supplier status: {e}"
                    )
                    self.show_toast(self.supplier_error_message, is_error=True)
                    audit_logger.error(
                        "fail_approve_supplier_existing_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        target_supplier_company_name=target_supplier_company_name,
                        reason=f"Database error: {e}",
                        ip_address=ip_address,
                    )

            self.check_auth_and_load()
            self.is_loading = False
            self.show_approve_dialog = False
            self.target_supplier_id = None

    def revoke_supplier(self, supplier_id: int):
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_revoke_supplier",
            acting_user_id=acting_user_id,
            acting_username=acting_username,
            target_supplier_id=supplier_id,
            ip_address=ip_address,
        )

        with rx.session() as session:
            supplier = session.exec(
                select(Supplier).where(Supplier.id == supplier_id)
            ).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                self.show_toast(self.supplier_error_message, is_error=True)
                self.is_loading = False
                audit_logger.error(
                    "fail_revoke_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    reason="Supplier not found",
                    ip_address=ip_address,
                )
                self.show_revoke_dialog = False
                self.target_supplier_id = None
                return

            target_supplier_company_name = supplier.company_name
            associated_user_id = None
            associated_local_user_id = None

            try:
                if supplier.user_info_id:
                    audit_logger.info(
                        "attempt_delete_associated_supplier_user",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        supplier_id=supplier_id,
                        supplier_company_name=target_supplier_company_name,
                        associated_user_info_id=supplier.user_info_id,
                        ip_address=ip_address,
                    )
                    user_info = session.exec(
                        select(UserInfo).where(UserInfo.id == supplier.user_info_id)
                    ).one_or_none()
                    if user_info:
                        associated_user_id = user_info.id
                        associated_local_user_id = user_info.user_id
                        local_user = session.exec(
                            select(reflex_local_auth.LocalUser).where(
                                reflex_local_auth.LocalUser.id == user_info.user_id
                            )
                        ).one_or_none()
                        if local_user:
                            session.delete(local_user)
                            session.flush()
                        session.delete(user_info)
                    supplier.user_info_id = None
                    supplier.status = "revoked"
                    session.add(supplier)
                else:
                    supplier.status = "revoked"
                    session.add(supplier)

                session.commit()
                audit_logger.info(
                    "success_revoke_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    deleted_user_info_id=associated_user_id,
                    deleted_local_user_id=associated_local_user_id,
                    new_status=supplier.status,
                    ip_address=ip_address,
                )
                self.supplier_success_message = (
                    f"Supplier {target_supplier_company_name} status updated to "
                    f"{supplier.status}."
                )
                if associated_user_id:
                    self.supplier_success_message += " Associated user account deleted."
                self.show_toast(self.supplier_success_message)
                self.supplier_success_message = ""

            except Exception as e:
                self.supplier_error_message = (
                    f"Error rejecting/revoking supplier: {str(e)}"
                )
                self.show_toast(self.supplier_error_message, is_error=True)
                audit_logger.error(
                    "fail_revoke_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    reason=f"Database error: {e}",
                    ip_address=ip_address,
                )
                session.rollback()

            self.check_auth_and_load()
            self.is_loading = False
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

    def cancel_supplier_action(self):
        self.show_approve_dialog = False
        self.show_revoke_dialog = False
        self.show_delete_dialog = False
        self.target_supplier_id = None
