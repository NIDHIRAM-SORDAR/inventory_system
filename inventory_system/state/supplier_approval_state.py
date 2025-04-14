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

        # **** Get current user information ****
        acting_user_id = self.authenticated_user.id if self.authenticated_user else None
        acting_username = (
            self.authenticated_user.username if self.authenticated_user else "Unknown"
        )
        ip_address = self.router.session.client_ip
        action = "approve" if make_supplier else "revoke"

        # **** Log the intent BEFORE the operation ****
        audit_logger.info(
            f"attempt_{action}_supplier",
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
                self.is_loading = False
                # **** Log failure ****
                audit_logger.error(
                    f"fail_{action}_supplier",
                    acting_user_id=acting_user_id,
                    acting_username=acting_username,
                    target_supplier_id=supplier_id,
                    reason="Supplier not found",
                    ip_address=ip_address,
                )
                # Reset dialog state on failure
                self.show_approve_dialog = False
                self.show_revoke_dialog = False
                self.target_supplier_id = None
                return

            target_supplier_company_name = supplier.company_name  # For logging

            if make_supplier:  # Approve action
                if not supplier.user_info_id:
                    default_password = (
                        "Supplier123!"  # Consider generating a secure random password
                    )
                    try:
                        # **** Log intent to register new user ****
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
                        # Fetch the UserInfo.id associated with the new LocalUser.id
                        new_user_info = session.exec(
                            select(UserInfo).where(UserInfo.user_id == new_user_id)
                        ).one()
                        supplier.user_info_id = new_user_info.id
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()

                        # **** Log success ****
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
                        self.supplier_success_message = f"Supplier {target_supplier_company_name} approved and user account created."

                    except Exception as e:
                        self.supplier_error_message = (
                            f"Failed to register supplier user: {str(e)}"
                        )
                        # **** Log failure ****
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
                    # Supplier already has a user_info_id, just update status
                    try:
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()
                        # **** Log success ****
                        audit_logger.info(
                            "success_approve_supplier_existing_user",
                            acting_user_id=acting_user_id,
                            acting_username=acting_username,
                            target_supplier_id=supplier_id,
                            target_supplier_company_name=target_supplier_company_name,
                            associated_user_info_id=supplier.user_info_id,
                            ip_address=ip_address,
                        )
                        self.supplier_success_message = f"Supplier {target_supplier_company_name} status set to approved."
                    except Exception as e:
                        session.rollback()
                        self.supplier_error_message = (
                            f"Failed to update supplier status: {e}"
                        )
                        # **** Log failure ****
                        audit_logger.error(
                            "fail_approve_supplier_existing_user",
                            acting_user_id=acting_user_id,
                            acting_username=acting_username,
                            target_supplier_id=supplier_id,
                            target_supplier_company_name=target_supplier_company_name,
                            reason=f"Database error: {e}",
                            ip_address=ip_address,
                        )

            else:  # Revoke/Reject action
                associated_user_id = None
                associated_local_user_id = None
                try:
                    if supplier.user_info_id:
                        # **** Log intent to delete associated user ****
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
                            associated_user_id = user_info.id  # Keep for logging
                            associated_local_user_id = (
                                user_info.user_id
                            )  # Keep for logging
                            local_user = session.exec(
                                select(reflex_local_auth.LocalUser).where(
                                    reflex_local_auth.LocalUser.id == user_info.user_id
                                )
                            ).one_or_none()
                            if local_user:
                                session.delete(local_user)  # Delete LocalUser first
                                session.flush()  # Ensure LocalUser is deleted before UserInfo due to FK
                            session.delete(user_info)  # Then delete UserInfo
                        # Set supplier user_info_id to None *before* deleting the supplier record if needed
                        supplier.user_info_id = None
                        supplier.status = "rejected"  # Or 'revoked' if you prefer
                        session.add(supplier)  # Update supplier status

                    else:
                        # No associated user, just mark as rejected/revoked or delete
                        supplier.status = "rejected"  # Or 'revoked'
                        session.add(
                            supplier
                        )  # Or session.delete(supplier) if rejection means deletion

                    session.commit()
                    # **** Log success ****
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
                    self.supplier_success_message = f"Supplier {target_supplier_company_name} status updated to {supplier.status}."
                    if associated_user_id:
                        self.supplier_success_message += (
                            " Associated user account deleted."
                        )

                except Exception as e:
                    self.supplier_error_message = (
                        f"Error rejecting/revoking supplier: {str(e)}"
                    )
                    # **** Log failure ****
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

            # Refresh data regardless of success/failure within the block
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
