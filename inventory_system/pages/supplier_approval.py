import reflex as rx
import reflex_local_auth
from inventory_system.templates.template import template
from inventory_system.models import UserInfo, Supplier
from sqlmodel import select
from typing import List, Dict, Any
from ..state import AuthState
from ..utils.register_supplier import register_supplier
from inventory_system import routes


class SupplierApprovalState(AuthState):  # Inherit from CustomRegisterState instead of AuthState
    users_data: List[Dict[str, Any]] = []
    supplier_error_message: str = ""
    supplier_success_message: str = ""
    is_loading: bool = False

    def check_auth_and_load(self):
        if not self.is_authenticated or (self.authenticated_user_info and not self.authenticated_user_info.is_admin):
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.is_loading = True
        with rx.session() as session:
            stmt = (
                select(
                    Supplier.id,
                    Supplier.company_name.label("username"),
                    Supplier.contact_email.label("email"),
                    Supplier.status,
                    UserInfo.role,
                    UserInfo.user_id
                )
                .outerjoin(UserInfo, Supplier.user_info_id == UserInfo.id)
            )
            results = session.exec(stmt).all()
            self.users_data = [{
                "id": row.id,
                "email": row.email,
                "role": row.role if row.role else row.status,  # Prioritize UserInfo.role, fallback to Supplier.status
                "username": row.username,
                "user_id": row.user_id
            } for row in results]
        self.is_loading = False

    def send_welcome_email(self, email: str, username: str, password: str):
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        
        try:
            print(f"Dummy email sent to {email} with username: {username}, password: {password}")
            self.supplier_success_message = f"Temporary password for {username}: {password} (Email not sent - dummy mode)"
        except Exception as e:
            self.supplier_error_message = f"Failed to send email: {str(e)}"

    def change_supplier_status(self, supplier_id: int, make_supplier: bool):
        self.is_loading = True
        self.supplier_error_message = ""
        self.supplier_success_message = ""
        with rx.session() as session:
            supplier = session.exec(select(Supplier).where(Supplier.id == supplier_id)).one_or_none()
            if not supplier:
                self.supplier_error_message = "Supplier not found."
                self.is_loading = False
                return

            if make_supplier:
                if not supplier.user_info_id:  # Only register if no UserInfo exists
                    default_password = "Supplier123!"
                    try:
                        new_user_id = register_supplier(supplier.company_name, supplier.contact_email, default_password, session)
                        supplier.user_info_id = session.exec(select(UserInfo).where(UserInfo.user_id == new_user_id)).one().id
                        supplier.status = "approved"
                        session.add(supplier)
                        session.commit()
                        self.send_welcome_email(supplier.contact_email, supplier.company_name, default_password)
                    except Exception as e:
                        self.supplier_error_message = f"Failed to register supplier: {str(e)}"
                        session.rollback()
                else:
                    supplier.status = "approved"
                    session.add(supplier)
                    session.commit()
            else:
                try:
                    if supplier.user_info_id:
                        user_info = session.exec(select(UserInfo).where(UserInfo.id == supplier.user_info_id)).one_or_none()
                        if user_info:
                            local_user = session.exec(select(reflex_local_auth.LocalUser).where(reflex_local_auth.LocalUser.id == user_info.user_id)).one_or_none()
                            if local_user:
                                session.delete(local_user)
                            session.delete(user_info)  # Cascades to Supplier via ondelete="CASCADE"
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

@template(route=routes.SUPPLIER_APPROV_ROUTE, title="Supplier Approval", on_load=SupplierApprovalState.check_auth_and_load)
@reflex_local_auth.require_login
def supplier_approval() -> rx.Component:
    def action_buttons(user: rx.Var) -> rx.Component:
        return rx.hstack(
            rx.button(
                "Approve Supplier",
                on_click=lambda: SupplierApprovalState.change_supplier_status(user["id"], True),
                color="purple",
                loading=SupplierApprovalState.is_loading,
                disabled=(user["role"] == "supplier") | (user["role"] == "admin"),
            ),
            rx.button(
                "Revoke Supplier",
                on_click=lambda: SupplierApprovalState.change_supplier_status(user["id"], False),
                color="orange",
                loading=SupplierApprovalState.is_loading,
                disabled=user["role"] != "supplier",
            ),
            spacing="2",
            justify="center",
        )

    return rx.vstack(
        rx.hstack(
            rx.heading("Supplier Approval", size="3"),
            rx.spacer(),
            width="100%",
        ),
        rx.cond(
            SupplierApprovalState.supplier_success_message,
            rx.callout(
                SupplierApprovalState.supplier_success_message,
                icon="check",
                color_scheme="green",
                width="100%",
            ),
        ),
        rx.cond(
            SupplierApprovalState.supplier_error_message,
            rx.callout(
                SupplierApprovalState.supplier_error_message,
                icon="triangle_alert",
                color_scheme="red",
                width="100%",
            ),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.cell("Username"),
                    rx.table.cell("Email"),
                    rx.table.cell("Status"),
                    rx.table.cell("Actions", width="200px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SupplierApprovalState.users_data,
                    lambda user: rx.table.row(
                        rx.table.cell(user["username"]),
                        rx.table.cell(user["email"]),
                        rx.table.cell(user["role"]),
                        rx.table.cell(action_buttons(user)),
                    )
                )
            ),
            width="100%",
        ),
        width="100%",
        padding="16px",
    )