import reflex as rx
import reflex_local_auth
from inventory_system.templates.template import template
from inventory_system.models import UserInfo
from sqlmodel import select
from typing import List, Dict, Any, Optional
from ..state import AuthState
from inventory_system import routes

class AdminManagementState(AuthState):
    users_data: List[Dict[str, Any]] = []
    admin_error_message: str = ""
    is_loading: bool = False
    show_delete_dialog: bool = False
    user_to_delete: Optional[int] = None  # Changed to Optional[int]

    def check_auth_and_load(self):
        """Check authentication and load users on page load."""
        if not self.is_authenticated or (self.authenticated_user_info and not self.authenticated_user_info.is_admin):
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)
        self.is_loading = True
        with rx.session() as session:
            stmt = (
                select(UserInfo, reflex_local_auth.LocalUser)
                .join(reflex_local_auth.LocalUser, UserInfo.user_id == reflex_local_auth.LocalUser.id)
            )
            results = session.exec(stmt).all()
            
            # Filter out the current admin user
            current_user_id = self.authenticated_user_info.user_id if self.authenticated_user_info else None
            self.users_data = [{
                "username": local_user.username,
                "id": user_info.user_id,
                "email": user_info.email,
                "role": user_info.role,
            } for user_info, local_user in results if user_info.user_id != current_user_id]
        self.is_loading = False

    def change_user_role(self, user_id: int, make_admin: bool):
        """Change a user's role."""
        self.is_loading = True
        self.admin_error_message = ""
        with rx.session() as session:
            user_info = session.exec(select(UserInfo).where(UserInfo.user_id == user_id)).one_or_none()
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
            session.refresh(user_info)
            self.check_auth_and_load()
        self.is_loading = False

    def confirm_delete_user(self, user_id: int):
        """Show delete confirmation dialog."""
        self.user_to_delete = user_id
        self.show_delete_dialog = True

    def cancel_delete(self):
        """Cancel deletion and close dialog."""
        self.show_delete_dialog = False
        self.user_to_delete = None

    def delete_user(self):
        """Delete the selected user."""
        if self.user_to_delete is None:
            return
        
        self.is_loading = True
        self.admin_error_message = ""
        
        with rx.session() as session:
            user_info = session.exec(select(UserInfo).where(UserInfo.user_id == self.user_to_delete)).one_or_none()
            if user_info:
                session.delete(user_info)
            
            local_user = session.exec(select(reflex_local_auth.LocalUser).where(reflex_local_auth.LocalUser.id == self.user_to_delete)).one_or_none()
            if local_user:
                session.delete(local_user)
            
            try:
                session.commit()
                self.check_auth_and_load()
            except Exception as e:
                self.admin_error_message = f"Error deleting user: {str(e)}"
                session.rollback()
            
        self.show_delete_dialog = False
        self.user_to_delete = None
        self.is_loading = False

@template(route=routes.ADMIN_MGMT, title="Admin Management", on_load=AdminManagementState.check_auth_and_load)
@reflex_local_auth.require_login
def admin_management() -> rx.Component:
    """Admin Management Page with regular Reflex table."""
    def action_buttons(user: rx.Var) -> rx.Component:
        return rx.hstack(
            rx.button(
                "Make Admin",
                on_click=lambda: AdminManagementState.change_user_role(user["id"], True),
                color="blue",
                loading=AdminManagementState.is_loading,
                disabled=(user["role"] == "admin") | (user["role"] == "supplier"),
            ),
            rx.button(
                "Make Employee",
                on_click=lambda: AdminManagementState.change_user_role(user["id"], False),
                color="green",
                loading=AdminManagementState.is_loading,
                disabled=(user["role"] == "employee") | (user["role"] == "supplier"),
            ),
            rx.button(
                "Delete",
                on_click=lambda: AdminManagementState.confirm_delete_user(user["id"]),
                color="red",
                loading=AdminManagementState.is_loading,
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Delete User"),
                    rx.alert_dialog.description(
                        f"Are you sure you want to delete user {user['username']}? This action cannot be undone.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "Cancel",
                                on_click=AdminManagementState.cancel_delete,
                                variant="soft",
                                color_scheme="gray",
                            ),
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Delete",
                                on_click=AdminManagementState.delete_user,
                                color_scheme="red",
                            ),
                        ),
                        spacing="3",
                        justify="end",
                    ),
                ),
                open=AdminManagementState.show_delete_dialog & (AdminManagementState.user_to_delete == user["id"]),
            ),
            spacing="2",
            justify="center",
        )

    return rx.vstack(
        rx.hstack(
            rx.heading("Admin Management", size="3"),
            rx.spacer(),
            rx.button("Logout", on_click=rx.redirect(routes.LOGOUT_ROUTE), color="red"),
            width="100%",
        ),
        rx.cond(
            AdminManagementState.admin_error_message,
            rx.text(AdminManagementState.admin_error_message, color="red"),
            rx.fragment(),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.cell("Username"),
                    rx.table.cell("Email"),
                    rx.table.cell("Current Role"),
                    rx.table.cell("Actions", width="200px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminManagementState.users_data,
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