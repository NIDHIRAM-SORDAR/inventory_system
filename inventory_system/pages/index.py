import reflex as rx
from inventory_system.templates import template
from inventory_system import routes
from inventory_system.state.login_state import LoginState


@template(route=routes.INDEX_ROUTE, title="Telecom Inventory System", show_nav=False)
def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Telecom Inventory System",
                size="7",
                color="white",
                font_weight="bold",
                text_align="center",
                margin_bottom="10px",
                transition="all 0.3s ease-in-out",
                _hover={"color": "#A78BFA"},
            ),
            rx.text(
                "Manage your telecom inventory at the speed of innovation",
                color="#A0AEC0",
                font_size="1.3em",
                text_align="center",
                margin_bottom="30px",
                transition="all 0.3s ease-in-out",
                _hover={"color": "#E2E8F0"},
            ),
            rx.hstack(
                rx.button(
                    "Get Started",
                    size="3",
                    background="linear-gradient(90deg, #6B46C1, #9F7AEA)",
                    color="white",
                    border_radius="10px",
                    padding="10px 30px",
                    font_weight="bold",
                    _hover={
                        "background": "linear-gradient(90deg, #553C9A, #7F6AEA)",
                        "transform": "scale(1.05)",
                    },
                    transition="all 0.3s ease-in-out",
                    on_click=LoginState.trigger_login_transition,
                ),
                rx.button(
                    "Learn More",
                    size="3",
                    background="transparent",
                    border="2px solid #6B46C1",
                    color="#6B46C1",
                    border_radius="10px",
                    padding="10px 30px",
                    font_weight="bold",
                    _hover={
                        "background": "#6B46C1",
                        "color": "white",
                        "transform": "scale(1.05)",
                    },
                    transition="all 0.3s ease-in-out",
                    on_click=rx.redirect(routes.ABOUT_ROUTE),
                ),
                spacing="2",
            ),
            rx.image(
                src="/images/landing_1.avif",
                alt="Telecom Dashboard",
                width="80%",
                height="300px",
                margin_top="20px",
                border_radius="12px",
                box_shadow="0 4px 12px rgba(0, 0, 0, 0.3)",
            ),
            rx.text(
                "Powered by Reflex • Built for Scale",
                color="#718096",
                font_size="0.9em",
                margin_top="40px",
                text_align="center",
            ),
            spacing="3",
            align_items="center",
        ),
        align_items="center",
        justify_content="center",
        min_height="70vh",
        padding="20px",
        width="100%",
        background="linear-gradient(135deg, #1A202C, #2D3748)",
        background_position="center",
        background_size="cover",
        position="relative",
        overflow="hidden",
        _before={
            "content": '""',
            "position": "absolute",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "background": "radial-gradient(circle, rgba(107, 70, 193, 0.2) 0%, transparent 70%)",
            "z_index": "-1",
        },
    )
