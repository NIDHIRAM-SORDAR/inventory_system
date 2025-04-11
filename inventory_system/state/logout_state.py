# inventory_system/state/logout_state.py
import reflex as rx

from inventory_system import routes
from inventory_system.state.auth import AuthState


class LogoutState(AuthState):
    dialog_open: bool = False  # State to control dialog visibility

    def toggle_dialog(self):
        """Toggle the logout confirmation dialog."""
        self.dialog_open = not self.dialog_open

    async def confirm_logout(self):
        """Perform logout and redirect to home page."""
        self.do_logout()  # Clear the auth session
        self.auth_token = ""  # Explicitly clear the token
        self.reset()
        self.dialog_open = False  # Close the dialog
        yield rx.redirect(routes.INDEX_ROUTE)  # Redirect to home page

    def cancel_logout(self):
        """Cancel logout and close the dialog."""
        self.dialog_open = False
