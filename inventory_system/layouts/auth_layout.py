import reflex as rx

def auth_layout(*children) -> rx.Component:
    """A shared layout for authentication pages (signup and signin)."""
    return rx.center(
        rx.vstack(
            *children,
            spacing="4",
            align_items="center",
            justify_content="center",
            min_height="100vh",
            background="linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
        ),
    )