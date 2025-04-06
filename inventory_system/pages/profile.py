# inventory_system/pages/profile.py
import reflex as rx
from ..components.profile_input import profile_input
from ..templates import template
from ..models import UserInfo
from ..state import AuthState
from sqlmodel import select
import reflex_local_auth

class ProfileState(AuthState):  # Inherit from AuthState matching the declaration style
    
    notifications: bool = True  # State-only field for notifications

    def handle_submit(self, form_data: dict):
        """Update the LocalUser and UserInfo models with form data."""
        if not self.is_authenticated:
            return rx.redirect("/login")
        
        # Update AuthState variables using setters
        self.set_username(form_data["username"])
        self.set_email(form_data["email"])
        
        # Update LocalUser (username) and UserInfo (email) in the database
        with rx.session() as session:
            # Update LocalUser
            user = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.id == self.authenticated_user.id
                )
            ).one()
            user.username = form_data["username"]
            session.add(user)
            
            # Update UserInfo
            user_info = session.exec(
                select(UserInfo).where(
                    UserInfo.user_id == self.authenticated_user.id
                )
            ).one_or_none()
            if user_info:
                user_info.email = form_data["email"]
                session.add(user_info)
            else:
                new_user_info = UserInfo(
                    user_id=self.authenticated_user.id,
                    email=form_data["email"],
                    role="employee"
                )
                session.add(new_user_info)
            
            session.commit()
        
        return rx.toast.success("Profile updated successfully", position="top-center")

    def toggle_notifications(self):
        """Toggle the notifications setting."""
        self.set_notifications(not self.notifications)

@template(route="/profile", title="Profile")
def profile() -> rx.Component:
    return rx.vstack(
        rx.cond(
            ProfileState.is_authenticated,
            rx.vstack(
                rx.flex(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("square-user-round"),
                            rx.heading("Personal information", size="5"),
                            align="center",
                        ),
                        rx.text("Update your personal information.", size="3"),
                        width="100%",
                    ),
                    rx.form.root(
                        rx.vstack(
                            profile_input(
                                "Username",
                                "username",
                                "Your username",
                                "text",
                                "user",
                                ProfileState.authenticated_user.username,
                            ),
                            profile_input(
                                "Email",
                                "email",
                                "user@reflex.dev",
                                "email",
                                "mail",
                                ProfileState.authenticated_user_info.email,
                            ),
                            rx.button("Update", type="submit", width="100%"),
                            width="100%",
                            spacing="5",
                        ),
                        on_submit=ProfileState.handle_submit,
                        reset_on_submit=True,
                        width="100%",
                        max_width="325px",
                    ),
                    width="100%",
                    spacing="4",
                    flex_direction=["column", "column", "row"],
                ),
                rx.divider(),
                rx.flex(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("bell"),
                            rx.heading("Notifications", size="5"),
                            align="center",
                        ),
                        rx.text("Manage your notification settings.", size="3"),
                    ),
                    rx.checkbox(
                        "Receive product updates",
                        size="3",
                        checked=ProfileState.notifications,
                        on_change=ProfileState.toggle_notifications,
                    ),
                    width="100%",
                    spacing="4",
                    justify="between",
                    flex_direction=["column", "column", "row"],
                ),
                rx.divider(),
                rx.vstack(
                    rx.hstack(
                        rx.icon("info"),
                        rx.heading("Account Role", size="5"),
                        align="center",
                    ),
                    rx.text(
                        rx.cond(
                            ProfileState.authenticated_user_info,
                            f"Role: {ProfileState.authenticated_user_info.role}",
                            "Role: N/A"
                        ),
                        size="3"
                    ),
                    width="100%",
                ),
                spacing="6",
                width="100%",
                max_width="800px",
            ),
            rx.vstack(
                rx.heading("Please log in to view your profile", size="5"),
                rx.link("Go to Login", href="/login"),
                spacing="4",
                align="center",
            )
        ),
        width="100%",
    )