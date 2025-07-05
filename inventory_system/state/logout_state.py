# inventory_system/state/logout_state.py
import reflex as rx

from inventory_system import routes
from inventory_system.logging.audit_listeners import with_async_audit_context

# **** Import the logger ****
from inventory_system.logging.logging import audit_logger
from inventory_system.models.audit import OperationType
from inventory_system.state.auth import AuthState


class LogoutState(AuthState):
    dialog_open: bool = False  # State to control dialog visibility

    def toggle_dialog(self):
        """Toggle the logout confirmation dialog."""
        self.dialog_open = not self.dialog_open

    @rx.event
    def cancel_logout(self):
        """Cancel logout and close the dialog."""
        self.dialog_open = False

    @rx.event
    async def confirm_logout(self):
        """Perform logout with audit context."""
        # Get user info BEFORE logging out
        user_id = self.authenticated_user.id if self.is_authenticated else None
        username = (
            self.authenticated_user.username if self.is_authenticated else "Unknown"
        )

        # Use audit context manager for the logout process
        async with with_async_audit_context(
            state=self,
            operation_type=OperationType.LOGOUT,
            operation_name="user_logout",
            username=username,
            user_id=user_id,
            logout_method="confirm_dialog",
        ):
            ip_address = self.router.session.client_ip

            # Log the logout event (this will now be captured in audit context)
            if self.is_authenticated:
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
            yield rx.redirect(routes.INDEX_ROUTE)
