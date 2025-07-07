from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.logging.audit_listeners import (
    with_async_audit_context,
)
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

    # Add new state variables for mobile layout
    mobile_displayed_count: int = 5  # Initial number of suppliers to display on mobile

    def check_auth_and_load(self):
        if not self.is_authenticated or "manage_suppliers" not in self.permissions:
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.set_is_loading(True)
        try:
            with rx.session() as session:
                stmt = select(
                    Supplier.id,
                    Supplier.company_name.label("username"),
                    Supplier.contact_email.label("email"),
                    Supplier.status,
                    UserInfo.user_id,
                ).outerjoin(UserInfo, Supplier.user_info_id == UserInfo.id)
                results = session.exec(stmt).all()
                self.users_data = [
                    {
                        "id": row.id,
                        "email": row.email,
                        "status": row.status,
                        "role": "none",  # Roles set in approve_supplier
                        "username": row.username,
                        "user_id": row.user_id,
                    }
                    for row in results
                ]
        finally:
            self.set_is_loading(False)

    @rx.event
    async def approve_supplier(self, supplier_id: int):
        if "manage_supplier_approval" not in self.permissions:
            yield rx.toast.error(
                "Permission denied: Cannot approve supplier", position="bottom-right"
            )
            return
        self.set_is_loading(True)
        self.set_supplier_error_message("")
        self.set_supplier_success_message("")

        async with with_async_audit_context(
            state=self,
            operation_name="supplier_approval",
            supplier_id=supplier_id,
        ):
            with rx.session() as session:
                try:
                    supplier = session.exec(
                        select(Supplier)
                        .where(Supplier.id == supplier_id)
                        .with_for_update()
                    ).one_or_none()
                    if not supplier:
                        self.set_supplier_error_message("Supplier not found.")
                        yield rx.toast.error(
                            self.supplier_error_message,
                            position="bottom-right",
                            duration=5000,
                        )
                        self.set_is_loading(False)
                        self.set_show_edit_dialog(False)
                        self.set_edit_supplier_id(None)
                        return

                    target_supplier_company_name = supplier.company_name

                    if not supplier.user_info_id:
                        default_password = "Supplier123!"

                        try:
                            new_user_id = register_supplier(
                                supplier.company_name,
                                supplier.contact_email,
                                default_password,
                                session,
                            )
                        except ValueError as e:
                            self.set_supplier_error_message(str(e))
                            yield rx.toast.error(
                                self.supplier_error_message,
                                position="bottom-right",
                                duration=5000,
                            )
                            self.set_is_loading(False)
                            self.set_show_edit_dialog(False)
                            self.set_edit_supplier_id(None)
                            return

                        new_user_info = session.exec(
                            select(UserInfo)
                            .where(UserInfo.user_id == new_user_id)
                            .with_for_update()
                        ).one_or_none()
                        if not new_user_info:
                            raise ValueError(
                                "Failed to create UserInfo for new supplier user"
                            )
                        supplier.user_info_id = new_user_info.id
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()

                        yield await self.send_welcome_email(
                            supplier.contact_email,
                            supplier.company_name,
                            default_password,
                        )
                        self.set_supplier_success_message(
                            f"Supplier {target_supplier_company_name} "
                            "approved and user account created."
                        )
                        yield rx.toast.success(
                            self.supplier_success_message,
                            position="bottom-right",
                            duration=5000,
                        )
                        self.set_supplier_success_message("")

                    else:
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()
                        self.set_supplier_success_message(
                            f"Supplier {target_supplier_company_name} "
                            "status set to approved."
                        )
                        yield rx.toast.success(
                            self.supplier_success_message,
                            position="bottom-right",
                            duration=5000,
                        )
                        self.set_supplier_success_message("")

                except Exception as e:
                    session.rollback()
                    self.set_supplier_error_message(
                        f"Failed to approve supplier: {str(e)}"
                    )
                    yield rx.toast.error(
                        self.supplier_error_message,
                        position="bottom-right",
                        duration=5000,
                    )
                finally:
                    self.check_auth_and_load()
                    self.set_is_loading(False)
                    self.set_show_edit_dialog(False)
                    self.set_edit_supplier_id(None)

    @rx.event
    async def revoke_supplier(self, supplier_id: int):
        if "manage_supplier_approval" not in self.permissions:
            yield rx.toast.error(
                "Permission denied: Cannot revoke supplier", position="bottom-right"
            )
            return
        self.setvar("is_loading", True)
        self.setvar("supplier_error_message", "")
        self.setvar("supplier_success_message", "")
        async with with_async_audit_context(
            state=self,
            operation_name="supplier_revokation",
            supplier_id=supplier_id,
        ):
            with rx.session() as session:
                try:
                    supplier = session.exec(
                        select(Supplier)
                        .where(Supplier.id == supplier_id)
                        .with_for_update()
                    ).one_or_none()
                    if not supplier:
                        self.setvar("supplier_error_message", "Supplier not found.")
                        yield rx.toast.error(
                            self.supplier_error_message,
                            position="bottom-right",
                            duration=5000,
                        )
                        self.setvar("is_loading", False)
                        self.setvar("show_edit_dialog", False)
                        self.setvar("edit_supplier_id", None)
                        return

                    target_supplier_company_name = supplier.company_name
                    associated_user_id = None

                    if supplier.user_info_id:
                        user_info = session.exec(
                            select(UserInfo)
                            .where(UserInfo.id == supplier.user_info_id)
                            .with_for_update()
                        ).one_or_none()
                        if user_info:
                            associated_user_id = user_info.id
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
                    self.setvar(
                        "supplier_success_message",
                        f"Supplier {target_supplier_company_name} "
                        f"status updated to {supplier.status}.",
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

                self.check_auth_and_load()
                self.setvar("is_loading", False)
                self.setvar("show_edit_dialog", False)
                self.setvar("edit_supplier_id", None)

    @rx.event
    async def delete_supplier(self, supplier_id: int):
        if "delete_supplier" not in self.permissions:
            yield rx.toast.error(
                "Permission denied: Cannot delete supplier", position="bottom-right"
            )
            return
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        async with with_async_audit_context(
            state=self,
            operation_name="supplier_deletion",
            supplier_id=supplier_id,
        ):
            with rx.session() as session:
                supplier = session.exec(
                    select(Supplier).where(Supplier.id == supplier_id).with_for_update()
                ).one_or_none()
                if not supplier:
                    self.supplier_error_message = "Supplier not found."
                    yield rx.toast.error(
                        self.supplier_error_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.is_loading = False
                    self.show_delete_dialog = False
                    self.edit_supplier_id = None
                    return

                target_supplier_company_name = supplier.company_name
                associated_user_id = None

                try:
                    if supplier.user_info_id:
                        user_info = session.exec(
                            select(UserInfo)
                            .where(UserInfo.id == supplier.user_info_id)
                            .with_for_update()
                        ).one_or_none()
                        if user_info:
                            associated_user_id = user_info.id
                            local_user = session.exec(
                                select(reflex_local_auth.LocalUser)
                                .where(
                                    reflex_local_auth.LocalUser.id == user_info.user_id
                                )
                                .with_for_update()
                            ).one_or_none()
                            if local_user:
                                session.delete(local_user)
                                session.flush()
                            session.delete(user_info)
                    session.delete(supplier)
                    session.commit()
                    self.supplier_success_message = (
                        f"Supplier {target_supplier_company_name} deleted successfully."
                    )
                    if associated_user_id:
                        self.supplier_success_message += (
                            " Associated user account deleted."
                        )
                    yield rx.toast.success(
                        self.supplier_success_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    self.supplier_success_message = ""

                except Exception as e:
                    self.supplier_error_message = f"Error deleting supplier: {str(e)}"
                    yield rx.toast.error(
                        self.supplier_error_message,
                        position="bottom-right",
                        duration=5000,
                    )
                    session.rollback()
                finally:
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
        self.mobile_displayed_count = 5

    def toggle_sort(self):
        self.sort_reverse = not self.sort_reverse
        self.mobile_displayed_count = 5  # Reset for mobile

    def set_search_value(self, value: str):
        self.search_value = value
        self.page_number = 1
        self.mobile_displayed_count = 5  # Reset for mobile

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

    # Add new computed vars for mobile display
    @rx.var
    def mobile_displayed_suppliers(self) -> List[Dict[str, Any]]:
        """Computes the list of suppliers to display on mobile based on mobile_displayed_count."""
        return self.filtered_users[: self.mobile_displayed_count]

    @rx.var
    def has_more_suppliers(self) -> bool:
        """Determines if there are more suppliers to load on mobile."""
        return len(self.filtered_users) > self.mobile_displayed_count

    # Add new method for mobile pagination
    def load_more(self):
        """Increments the number of displayed suppliers on mobile by page_size."""
        self.mobile_displayed_count += self.page_size
