# inventory_system/state/logout_state.py
import reflex as rx

from inventory_system import routes

# **** Import the logger ****
from inventory_system.logging.logging import audit_logger
from inventory_system.state.auth import AuthState


class LogoutState(AuthState):
    dialog_open: bool = False  # State to control dialog visibility

    def toggle_dialog(self):
        """Toggle the logout confirmation dialog."""
        self.dialog_open = not self.dialog_open

    async def confirm_logout(self):
        """Perform logout, log the event, and redirect to home page."""
        # **** Get user info BEFORE logging out ****
        user_id = self.authenticated_user.id if self.is_authenticated else None
        username = (
            self.authenticated_user.username if self.is_authenticated else "Unknown"
        )
        ip_address = self.router.session.client_ip

        # **** Log the logout event ****
        if self.is_authenticated:  # Only log if user was actually logged in
            audit_logger.info(
                "user_logout",
                user_id=user_id,
                username=username,
                ip_address=ip_address,
            )
        else:
            audit_logger.warning(
                "logout_attempt_unauthenticated",
                ip_address=ip_address,
            )

        # Perform actual logout actions
        self.do_logout()  # Clear the auth session from the base class
        self.auth_token = ""  # Explicitly clear the token if needed
        self.reset()  # Reset inherited state variables

        # Close dialog and redirect
        self.dialog_open = False
        yield rx.redirect(routes.INDEX_ROUTE)  # Redirect to home page

    def cancel_logout(self):
        """Cancel logout and close the dialog."""
        self.dialog_open = False
