import reflex as rx
from ..state import AuthState
from inventory_system import routes

class LogoutState(AuthState):
    async def confirm_logout(self):
        """Perform logout and redirect to home page."""
        self.do_logout()  # Clear the auth session
        self.auth_token = ""  # Explicitly clear the token
        self.reset()
        yield rx.redirect(routes.INDEX_ROUTE)  # Redirect to home page