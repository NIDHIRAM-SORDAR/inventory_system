"""The admin page for managing users and suppliers."""

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.models import Supplier, UserInfo
from inventory_system.state.auth import AuthState


class AdminState(AuthState):
    """State for the admin page."""

    is_loading: bool = False
    users_data: list[dict] = []
    suppliers_data: list[dict] = []
    user_stats: dict = {"total": 0, "admin": 0, "supplier": 0, "employee": 0}
    supplier_stats: dict = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}

    def check_auth_and_load(self):
        """Check if the user is authenticated and an admin, then load user and supplier data."""
        if not self.is_authenticated or not self.is_admin:
            return rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)

        self.is_loading = True
        with rx.session() as session:
            # Load user data (excluding the current user)
            current_user_id = (
                self.authenticated_user_info.user_id
                if self.authenticated_user_info
                else None
            )
            stmt_users = (
                select(UserInfo, reflex_local_auth.LocalUser.username)
                .join(
                    reflex_local_auth.LocalUser,
                    UserInfo.user_id == reflex_local_auth.LocalUser.id,
                )
                .where(UserInfo.user_id != current_user_id)
            )
            user_results = session.exec(stmt_users).all()
            self.users_data = [
                {
                    "username": username,
                    "id": user_info.user_id,
                    "email": user_info.email,
                    "role": user_info.role,
                }
                for user_info, username in user_results
            ]

            # Calculate user stats
            self.user_stats = {
                "total": len(self.users_data),
                "admin": sum(1 for user in self.users_data if user["role"] == "admin"),
                "supplier": sum(
                    1 for user in self.users_data if user["role"] == "supplier"
                ),
                "employee": sum(
                    1 for user in self.users_data if user["role"] == "employee"
                ),
            }

            # Load supplier data
            stmt_suppliers = select(Supplier)
            supplier_results = session.exec(stmt_suppliers).all()
            self.suppliers_data = [
                {
                    "id": supplier.id,
                    "company_name": supplier.company_name,
                    "status": supplier.status,
                }
                for supplier in supplier_results
            ]

            # Calculate supplier stats
            self.supplier_stats = {
                "total": len(self.suppliers_data),
                "pending": sum(
                    1
                    for supplier in self.suppliers_data
                    if supplier["status"] == "pending"
                ),
                "approved": sum(
                    1
                    for supplier in self.suppliers_data
                    if supplier["status"] == "approved"
                ),
                "rejected": sum(
                    1
                    for supplier in self.suppliers_data
                    if supplier["status"] == "rejected"
                ),
            }

        self.is_loading = False
