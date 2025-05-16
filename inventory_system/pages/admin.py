# inventory_system/views/admin.py
import reflex as rx
import reflex_local_auth

from inventory_system import routes, styles
from inventory_system.components.card import card
from inventory_system.components.notification import notification
from inventory_system.state.admin_state import AdminState
from inventory_system.state.auth import AuthState
from inventory_system.templates import template


@template(
    route=routes.ADMIN_ROUTE,
    title="Admin Dashboard",
    on_load=AdminState.check_auth_and_load,
)
@reflex_local_auth.require_login
def admin() -> rx.Component:
    """The admin page for managing users and suppliers.

    Returns:
        The UI for the admin page.
    """
    return rx.vstack(
        # Heading
        rx.cond(
            AuthState.is_authenticated,
            rx.heading(
                rx.cond(
                    AuthState.username,
                    f"Welcome, {AuthState.authenticated_user.username}",
                    "Welcome, Admin",
                ),
                size="5",
                color=rx.color_mode_cond(
                    light=rx.color("gray", 12),
                    dark="#E6F0FA",
                ),
                text_shadow=rx.color_mode_cond(
                    light="1px 1px 2px rgba(0, 0, 0, 0.3)",
                    dark="1px 1px 3px rgba(163, 207, 250, 0.5)",
                ),
                transition="all 0.3s ease-in-out",
                _hover={
                    "color": rx.color_mode_cond(
                        light=rx.color("gray", 11), dark="#FFFFFF"
                    )
                },
            ),
            rx.heading("Please log in", size="5"),
        ),
        # Search bar and notifications
        rx.flex(
            rx.input(
                rx.input.slot(rx.icon("search"), padding_left="0"),
                placeholder="Search here...",
                size="3",
                width="100%",
                max_width="450px",
                radius="large",
                style=styles.ghost_input_style,
            ),
            rx.flex(
                notification("bell", "cyan", 12),
                notification("message-square-text", "plum", 6),
                spacing="4",
                width="100%",
                wrap="nowrap",
                justify="end",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        # Cards grid
        rx.cond(
            AdminState.is_loading,
            rx.center(
                rx.spinner(size="3"),
                width="100%",
                min_height="20vh",
            ),
            rx.grid(
                admin_management_card(),
                supplier_approval_card(),
                gap="1rem",
                grid_template_columns=[
                    "1fr",
                    "1fr",
                    "repeat(2, 1fr)",
                    "repeat(2, 1fr)",
                    "repeat(2, 1fr)",
                ],
                width="100%",
            ),
        ),
        spacing="8",
        width="100%",
        padding=["1em", "1.5em", "2em"],
        align_items="center",
    )


def admin_management_card() -> rx.Component:
    """Card for Admin Management panel."""
    return rx.link(
        card(
            rx.hstack(
                rx.icon("users", size=24, color=rx.color("blue", 8)),
                rx.text("Admin Management", font_size="1.2em", font_weight="600"),
                spacing="3",
                align="center",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("Total Users:", font_weight="500"),
                    rx.text(AdminState.user_stats["total"], color=rx.color("blue", 8)),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Admins:", font_weight="500"),
                    rx.text(
                        AdminState.user_stats["admin"], color=rx.color("purple", 8)
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Suppliers:", font_weight="500"),
                    rx.text(
                        AdminState.user_stats["supplier"], color=rx.color("green", 8)
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Employees:", font_weight="500"),
                    rx.text(
                        AdminState.user_stats["employee"], color=rx.color("gray", 8)
                    ),
                    spacing="2",
                ),
                spacing="2",
            ),
            transition="all 0.3s ease-in-out",
            _hover={
                "box_shadow": "0 8px 24px rgba(0, 0, 0, 0.2)",
                "transform": "translateY(-4px)",
            },
        ),
        href=routes.USER_MANAGEMENT_ROUTE,  # Updated from ADMIN_USERS_ROUTE
        width="100%",
    )


def supplier_approval_card() -> rx.Component:
    """Card for Supplier Approval panel."""
    return rx.link(
        card(
            rx.hstack(
                rx.icon("briefcase", size=24, color=rx.color("green", 8)),
                rx.text("Supplier Approval", font_size="1.2em", font_weight="600"),
                spacing="3",
                align="center",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("Total Suppliers:", font_weight="500"),
                    rx.text(
                        AdminState.supplier_stats["total"], color=rx.color("green", 8)
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Pending:", font_weight="500"),
                    rx.text(
                        AdminState.supplier_stats["pending"],
                        color=rx.color("orange", 8),
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Approved:", font_weight="500"),
                    rx.text(
                        AdminState.supplier_stats["approved"], color=rx.color("blue", 8)
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Rejected:", font_weight="500"),
                    rx.text(
                        AdminState.supplier_stats["rejected"], color=rx.color("red", 8)
                    ),
                    spacing="2",
                ),
                spacing="2",
            ),
            transition="all 0.3s ease-in-out",
            _hover={
                "box_shadow": "0 8px 24px rgba(0, 0, 0, 0.2)",
                "transform": "translateY(-4px)",
            },
        ),
        href=routes.SUPPLIER_APPROVAL_ROUTE,  # Updated from ADMIN_SUPPLIERS_ROUTE
        width="100%",
    )
