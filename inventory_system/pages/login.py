# inventory_system/pages/login.py
import reflex as rx
import reflex_local_auth
from sqlmodel import select
from ..templates import template
from ..models import UserInfo
from ..state import AuthState  # Import your custom AuthState
from inventory_system import routes

class CustomLoginState(AuthState):  # Inherit from your AuthState instead
    """Custom login state to redirect based on user role."""
    error_message: str = ""  # Add error_message as a state var

    def on_submit(self, form_data: dict):
        """Handle login form submission and redirect based on role."""
        self.error_message = ""
        
        # Implement login logic directly instead of relying on super()
        with rx.session() as session:
            user = session.exec(
                select(reflex_local_auth.LocalUser)
                .where(reflex_local_auth.LocalUser.username == form_data["username"])
            ).one_or_none()
            
            if not user or not user.verify(form_data["password"]):
                self.error_message = "Invalid username or password"
                return
            
            # Explicitly call our custom _login method
            self._login(user.id)
            
            # Check user role and redirect
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info and user_info.is_admin:
                return rx.redirect(routes.ADMIN_MGMT)
            return rx.redirect(routes.OVERVIEW_ROUTE)

def login_error() -> rx.Component:
    """Render the login error message."""
    return rx.cond(
        CustomLoginState.error_message != "",
        rx.callout(
            CustomLoginState.error_message,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
        ),
    )

def login_form() -> rx.Component:
    """Render the login form."""
    return rx.form(
        rx.vstack(
            rx.heading("Login", size="7"),
            login_error(),
            rx.text("Username"),
            rx.input(
                name="username",
                type="text",
                placeholder="Enter your username",
                width="100%",
            ),
            rx.text("Password"),
            rx.input(
                name="password",
                type="password",
                placeholder="Enter your password",
                width="100%",
            ),
            rx.button(
                "Login",
                type="submit",
                width="100%",
            ),
            rx.center(
                rx.link(
                    "Register",
                    href=reflex_local_auth.routes.REGISTER_ROUTE,
                ),
                width="100%",
            ),
            min_width="300px",
            spacing="2",
        ),
        on_submit=CustomLoginState.on_submit,
        width="100%",
    )

@template(route=routes.LOGIN_ROUTE, title="Login")
def login_page() -> rx.Component:
    """Render the login page."""
    return rx.center(
        rx.card(
            login_form(),
            width="400px",
        ),
        padding_top="2em",
        width="100%",
        height="100vh",
        align="center",
        justify="center",
    )