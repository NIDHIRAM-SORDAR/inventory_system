import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system import routes
from inventory_system.state.auth import AuthState  # Import LoginState for transition

from ..models import UserInfo


class CustomLoginState(AuthState):
    """Custom login state to redirect based on user role."""

    error_message: str = ""
    is_submitting: bool = False

    def reset_form_state(self):
        """Reset form state on page load."""
        self.error_message = ""
        self.is_submitting = False

    async def on_submit(self, form_data: dict):
        """Handle login form submission and redirect based on role."""
        self.error_message = ""
        self.is_submitting = True

        try:
            with rx.session() as session:
                user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.username == form_data["username"]
                    )
                ).one_or_none()

                if not user or not user.verify(form_data["password"]):
                    self.error_message = "Invalid username or password"
                    self.is_submitting = False
                    return

                # Explicitly call our custom _login method
                self._login(user.id)

                # Check user role and redirect
                user_info = session.exec(
                    select(UserInfo).where(
                        UserInfo.user_id == self.authenticated_user.id
                    )
                ).one_or_none()
                if user_info and user_info.is_admin:
                    return rx.redirect(routes.ADMIN_ROUTE)
                return rx.redirect(routes.OVERVIEW_ROUTE)

        finally:
            self.is_submitting = (
                False  # Ensure is_submitting is reset even if an error occurs
            )
