import reflex as rx
from inventory_system import routes


class LoginState(rx.State):
    show_login: bool = False

    def trigger_login_transition(self):
        # Set show_login to True to start the fade-in transition
        self.show_login = True
        # Redirect to the login route without delay
        return rx.redirect(routes.LOGIN_ROUTE)

    def reset_transition(self):
        # Reset show_login to False when the page loads
        self.show_login = False

    def start_transition(self):
        # Set show_login to True to trigger the fade-in animation
        self.show_login = True
