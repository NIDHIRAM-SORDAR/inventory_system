# inventory_system/pages/profile.py
import reflex as rx
from ..components.profile_input import profile_input
from ..templates import template
from ..state import ProfileState, ProfilePictureState
from inventory_system import routes


def profile_upload_section() -> rx.Component:
    """Render the profile picture upload section."""
    return rx.vstack(
        rx.hstack(
            rx.icon("image"),
            rx.heading("Profile Picture", size="5"),
            align="center",
        ),
        rx.text("Upload a new profile picture.", size="3"),
        rx.cond(
            ProfilePictureState.upload_error,
            rx.callout(
                ProfilePictureState.upload_error,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        rx.upload(
            rx.text("Drag and drop an image or click to select"),
            rx.badge(f"{rx.selected_files("profile_upload")} has been selected"),
            id="profile_upload",
            accept={"image/*": [".png", ".jpg", ".jpeg", ".gif"]},
            max_files=1,
            disabled=ProfilePictureState.is_uploading,
            border="2px dashed #A0AEC0",
            padding="2em",
            width="100%",
        ),
        rx.hstack(
            rx.button(
                "Upload",
                on_click=rx.cond(
                    ~rx.selected_files("profile_upload"),
                    rx.toast.error(
                        "Please select the profile picture first",
                        position="bottom-right",
                    ),
                    ProfilePictureState.handle_profile_picture_upload(
                        rx.upload_files(upload_id="profile_upload")
                    ),
                ),
                disabled=ProfilePictureState.is_uploading,
            ),
            rx.button(
                "Clear",
                on_click=ProfilePictureState.clear_upload,
                disabled=ProfilePictureState.is_uploading,
                color_scheme="gray",
            ),
            spacing="2",
        ),
        rx.cond(
            ProfilePictureState.is_uploading,
            rx.vstack(
                rx.text("Uploading..."),
                rx.progress(value=ProfilePictureState.upload_progress, max=100),
                width="100%",
            ),
        ),
        rx.cond(
            ProfilePictureState.preview_img != "",
            rx.image(
                src=ProfilePictureState.preview_img,
                alt="Profile Picture Preview",
                width="100px",
                height="100px",
                border_radius="50%",
            ),
            rx.image(
                src=ProfilePictureState.profile_picture,
                alt="Profile Picture Preview",
                width="100px",
                height="100px",
                border_radius="50%",
            ),
        ),
        width="100%",
        spacing="4",
    )


@template(route=routes.PROFILE_ROUTE, title="Profile")
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
                profile_upload_section(),
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
                            "Role: N/A",
                        ),
                        size="3",
                    ),
                    width="100%",
                ),
                spacing="6",
                width="100%",
                max_width="800px",
            ),
            rx.vstack(
                rx.heading("Please log in to view your profile", size="5"),
                rx.link("Go to Login", href=routes.LOGIN_ROUTE),
                spacing="4",
                align="center",
            ),
        ),
        width="100%",
    )
