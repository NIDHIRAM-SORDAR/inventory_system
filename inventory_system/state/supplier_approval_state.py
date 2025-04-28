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
    show_edit_dialog: bool = False
    show_delete_dialog: bool = False
    edit_supplier_id: Optional[int] = None
    approve_checked: bool = False
    revoke_checked: bool = False
    current_status: str = ""

    def check_auth_and_load(self):
        if not self.is_authenticated or not (
            self.authenticated_user_info and "manage_suppliers" in self.user_permissions
        ):
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.setvar("is_loading", True)
        with rx.session() as session:
            stmt = select(
                Supplier.id,
                Supplier.company_name.label("username"),
                Supplier.contact_email.label("email"),
                Supplier.status,
                UserInfo.get_roles(),
                UserInfo.user_id,
            ).outerjoin(UserInfo, Supplier.user_info_id == UserInfo.id)
            results = session.exec(stmt).all()
            self.users_data = [
                {
                    "id": row.id,
                    "email": row.email,
                    "status": row.status,
                    "role": row.role if row.role else "none",
                    "username": row.username,
                    "user_id": row.user_id,
                }
                for row in results
            ]
        self.setvar("is_loading", False)

    @rx.event
    async def approve_supplier(self, supplier_id: int):
        if "manage_supplier_approval" not in self.user_permissions:
            yield rx.toast.error(
                "Permission denied: Cannot approve supplier", position="bottom-right"
            )
            return
        self.setvar("is_loading", True)
        self.setvar("supplier_error_message", "")
        self.setvar("supplier_success_message", "")
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
            try:
                supplier = session.exec(
                    select(Supplier).where(Supplier.id == supplier_id).with_for_update()
                ).one_or_none()
                if not supplier:
                    self.setvar("supplier_error_message", "Supplier not found.")
                    yield rx.toast.error(
                        self.supplier_error_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.setvar("is_loading", False)
                    audit_logger.error(
                        "fail_approve_supplier",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        reason="Supplier not found",
                        ip_address=ip_address,
                    )
                    self.setvar("show_edit_dialog", False)
                    self.setvar("edit_supplier_id", None)
                    return

                target_supplier_company_name = supplier.company_name

                if not supplier.user_info_id:
                    default_password = "Supplier123!"
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
                        select(UserInfo)
                        .where(UserInfo.user_id == new_user_id)
                        .with_for_update()
                    ).one()
                    session.add(new_user_info)
                    session.refresh(new_user_info)
                    new_user_info.set_roles(["supplier"], session)
                    supplier.user_info_id = new_user_info.id
                    supplier.status = "approved"
                    session.add(supplier)
                    session.refresh(supplier)
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
                    yield await self.send_welcome_email(
                        supplier.contact_email,
                        supplier.company_name,
                        default_password,
                    )
                    self.setvar(
                        "supplier_success_message",
                        f"Supplier {target_supplier_company_name} "
                        "approved and user account created.",
                    )
                    yield rx.toast.success(
                        self.supplier_success_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.setvar("supplier_success_message", "")

                else:
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
                    self.setvar(
                        "supplier_success_message",
                        f"Supplier {target_supplier_company_name} "
                        "status set to approved.",
                    )
                    yield rx.toast.success(
                        self.supplier_success_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.setvar("supplier_success_message", "")

            except Exception as e:
                session.rollback()
                self.setvar(
                    "supplier_error_message",
                    f"Failed to approve supplier: {str(e)}",
                )
                yield rx.toast.error(
                    self.supplier_error_message,
                    position="bottom-right",
                    duration=5000,
                )
                audit_logger.error(
                    "fail_approve_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    reason=f"Database error: {str(e)}",
                    ip_address=ip_address,
                )

            self.check_auth_and_load()
            self.setvar("is_loading", False)
            self.setvar("show_edit_dialog", False)
            self.setvar("edit_supplier_id", None)

    @rx.event
    async def revoke_supplier(self, supplier_id: int):
        if "manage_supplier_approval" not in self.user_permissions:
            yield rx.toast.error(
                "Permission denied: Cannot revoke supplier", position="bottom-right"
            )
            return
        self.setvar("is_loading", True)
        self.setvar("supplier_error_message", "")
        self.setvar("supplier_success_message", "")
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
            try:
                supplier = session.exec(
                    select(Supplier).where(Supplier.id == supplier_id).with_for_update()
                ).one_or_none()
                if not supplier:
                    self.setvar("supplier_error_message", "Supplier not found.")
                    yield rx.toast.error(
                        self.supplier_error_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.setvar("is_loading", False)
                    audit_logger.error(
                        "fail_revoke_supplier",
                        acting_user_id=acting_user_id,
                        acting_username=acting_username,
                        target_supplier_id=supplier_id,
                        reason="Supplier not found",
                        ip_address=ip_address,
                    )
                    self.setvar("show_edit_dialog", False)
                    self.setvar("edit_supplier_id", None)
                    return

                target_supplier_company_name = supplier.company_name
                associated_user_id = None
                associated_local_user_id = None

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
                        select(UserInfo)
                        .where(UserInfo.id == supplier.user_info_id)
                        .with_for_update()
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
                self.setvar(
                    "supplier_success_message",
                    f"Supplier {target_supplier_company_name} "
                    "status updated to {supplier.status}.",
                )
                if associated_user_id:
                    self.setvar(
                        "supplier_success_message",
                        self.supplier_success_message
                        + " Associated user account deleted.",
                    )
                yield rx.toast.success(
                    self.supplier_success_message,
                    position="bottom-right",
                    duration=5000,
                )
                self.setvar("supplier_success_message", "")

            except Exception as e:
                session.rollback()
                self.setvar(
                    "supplier_error_message",
                    f"Error rejecting/revoking supplier: {str(e)}",
                )
                yield rx.toast.error(
                    self.supplier_error_message,
                    position="bottom-right",
                    duration=5000,
                )
                audit_logger.error(
                    "fail_revoke_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    target_supplier_company_name=target_supplier_company_name,
                    reason=f"Database error: {str(e)}",
                    ip_address=ip_address,
                )

            self.check_auth_and_load()
            self.setvar("is_loading", False)
            self.setvar("show_edit_dialog", False)
            self.setvar("edit_supplier_id", None)

    @rx.event
    async def delete_supplier(self, supplier_id: int):
        if "delete_supplier" not in self.user_permissions:
            yield rx.toast.error(
                "Permission denied: Cannot delete supplier", position="bottom-right"
            )
            return
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
                select(Supplier).where(Supplier.id == supplier_id).with_for_update()
            ).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                yield rx.toast.error(
                    self.supplier_error_message, position="bottom-right", duration=5000
                )
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
                self.edit_supplier_id = None
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
                        select(UserInfo)
                        .where(UserInfo.id == supplier.user_info_id)
                        .with_for_update()
                    ).one_or_none()
                    if user_info:
                        associated_user_id = user_info.id
                        associated_local_user_id = user_info.user_id
                        local_user = session.exec(
                            select(reflex_local_auth.LocalUser)
                            .where(reflex_local_auth.LocalUser.id == user_info.user_id)
                            .with_for_update()
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
                yield rx.toast.success(
                    self.supplier_success_message,
                    position="bottom-right",
                    duration=5000,
                )
                self.supplier_success_message = ""

            except Exception as e:
                self.supplier_error_message = f"Error deleting supplier: {str(e)}"
                yield rx.toast.error(
                    self.supplier_error_message, position="bottom-right", duration=5000
                )
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
            self.edit_supplier_id = None

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

    async def send_welcome_email(self, email: str, username: str, password: str):
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
            return rx.toast.success(
                self.supplier_success_message, position="bottom-right", duration=5000
            )
        except Exception as e:
            self.supplier_error_message = f"Failed to send email: {str(e)}"
            return rx.toast.error(
                self.supplier_error_message, position="bottom-right", duration=5000
            )
        finally:
            self.supplier_success_message = ""
            self.supplier_error_message = ""

    @rx.event
    def handle_submit(self, form_data: dict):
        supplier_id = int(form_data.get("supplier_id", 0))
        approve = self.approve_checked
        revoke = self.revoke_checked
        if approve and revoke:
            self.supplier_error_message = "Cannot approve and revoke simultaneously."
            yield rx.toast.error(
                self.supplier_error_message, position="bottom-right", duration=5000
            )
            return
        if approve:
            return SupplierApprovalState.approve_supplier(supplier_id)
        elif revoke:
            return SupplierApprovalState.revoke_supplier(supplier_id)
        else:
            self.show_edit_dialog = False
            self.edit_supplier_id = None
            self.check_auth_and_load()

    def open_edit_dialog(self, supplier_id: int):
        self.show_edit_dialog = True
        self.edit_supplier_id = supplier_id
        supplier = next((u for u in self.users_data if u["id"] == supplier_id), None)
        if supplier:
            self.current_status = supplier["status"]
            self.approve_checked = supplier["status"] == "approved"
            self.revoke_checked = supplier["status"] == "revoked"

    def toggle_approve(self, value: bool):
        self.approve_checked = value
        if value and self.current_status != "pending":
            self.revoke_checked = False

    def toggle_revoke(self, value: bool):
        self.revoke_checked = value
        if value and self.current_status != "pending":
            self.approve_checked = False

    def cancel_dialog(self):
        self.show_edit_dialog = False
        self.show_delete_dialog = False
        self.edit_supplier_id = None

    def open_delete_dialog(self, supplier_id: int):
        self.show_delete_dialog = True
        self.edit_supplier_id = supplier_id

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

    def clear_search_value(self):
        self.setvar("search_value", "")
        self.setvar("page_number", 1)
