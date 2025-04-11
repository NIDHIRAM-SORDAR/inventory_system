import reflex as rx

from inventory_system import routes
from inventory_system.state.login_state import LoginState
from inventory_system.templates import template


class IndexState(rx.State):
    show_content: bool = False

    def trigger_content_transition(self):
        self.show_content = True


@template(
    route=routes.INDEX_ROUTE,
    title="Telecom Inventory System",
    show_nav=False,
    on_load=IndexState.trigger_content_transition,
)
def index() -> rx.Component:
    """The index page for Telecom Inventory System.

    Returns:
        The UI for the index page.
    """
    return rx.box(
        rx.vstack(
            # Heading with gradient text and subtle animation
            rx.heading(
                "Telecom Inventory System",
                size=rx.breakpoints(
                    initial="7",
                    sm="8",
                    lg="9",
                ),
                style=rx.color_mode_cond(
                    light={
                        "background": "linear-gradient(45deg, #FF8C61 0%, #A3CFFA 100%)",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                    dark={
                        "background": "linear-gradient(45deg, #4A90E2 0%, #B19CD9 100%)",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                font_weight="bold",
                text_align="center",
                margin_bottom=rx.breakpoints(
                    initial="8px",
                    sm="10px",
                    lg="12px",
                ),
                transition="all 0.3s ease-in-out",
                _hover={"transform": "scale(1.02)"},
            ),
            # Tagline with modern typography
            rx.text(
                "Manage your telecom inventory at the speed of innovation",
                font_size=rx.breakpoints(
                    initial="1rem",
                    sm="1.2em",
                    lg="1.3em",
                ),
                color=rx.color_mode_cond(
                    light=rx.color("gray", 12),  # Darker gray for better contrast
                    dark="#E6F0FA",  # Brighter, almost white for dark mode
                ),
                text_shadow=rx.color_mode_cond(
                    light="1px 1px 2px rgba(0, 0, 0, 0.3)",  # Dark shadow for light mode
                    dark="1px 1px 3px rgba(163, 207, 250, 0.5)",  # Light cyan glow for dark mode
                ),
                _hover={
                    "color": rx.color_mode_cond(
                        light=rx.color("gray", 11),
                        dark="#FFFFFF",
                    ),
                },
                text_align="center",
                max_width=rx.breakpoints(
                    initial="90%",
                    sm="80%",
                    lg="600px",
                ),
                line_height="1.6",
                margin_bottom=rx.breakpoints(
                    initial="20px",
                    sm="25px",
                    lg="30px",
                ),
                transition="all 0.3s ease-in-out",
            ),
            # Buttons with enhanced styling and animations
            rx.stack(
                rx.button(
                    rx.hstack(
                        rx.icon("rocket", size=16, color="white"),
                        rx.text("Get Started", font_weight="bold"),
                        spacing="2",
                    ),
                    size=rx.breakpoints(
                        initial="2",
                        sm="3",
                        lg="3",
                    ),
                    background=f"linear-gradient(90deg, {rx.color('purple', 8)}, {rx.color('purple', 10)})",
                    color="white",
                    border_radius="10px",
                    padding=rx.breakpoints(
                        initial="8px 20px",
                        sm="10px 25px",
                        lg="10px 30px",
                    ),
                    _hover={
                        "background": f"linear-gradient(90deg, {rx.color('purple', 9)}, {rx.color('purple', 11)})",
                        "transform": "scale(1.05)",
                    },
                    transition="all 0.3s ease-in-out",
                    on_click=LoginState.trigger_login_transition,
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("info", size=16, color=rx.color("purple", 8)),
                        rx.text("Learn More", font_weight="bold"),
                        spacing="2",
                    ),
                    size=rx.breakpoints(
                        initial="2",
                        sm="3",
                        lg="3",
                    ),
                    background="transparent",
                    border=f"2px solid {rx.color('purple', 8)}",
                    color=rx.color("purple", 8),
                    border_radius="10px",
                    padding=rx.breakpoints(
                        initial="8px 20px",
                        sm="10px 25px",
                        lg="10px 30px",
                    ),
                    _hover={
                        "background": rx.color("purple", 8),
                        "color": "white",
                        "transform": "scale(1.05)",
                    },
                    transition="all 0.3s ease-in-out",
                    on_click=rx.redirect(routes.ABOUT_ROUTE),
                ),
                direction=rx.breakpoints(
                    initial="column",  # Vertical on small devices
                    sm="row",  # Horizontal on larger devices
                ),
                spacing="3",
                justify="center",
                align="center",
                width="100%",
                max_width=rx.breakpoints(
                    initial="100%",
                    sm="80%",
                    lg="400px",
                ),
            ),
            # Image with responsive sizing and animation
            rx.color_mode_cond(
                light=rx.image(
                    src="/images/light-landing.png",
                    alt="Telecom Dashboard",
                    width=rx.breakpoints(
                        initial="90%",
                        sm="80%",
                        lg="60%",
                    ),
                    max_width="600px",
                    height=rx.breakpoints(
                        initial="200px",
                        sm="250px",
                        lg="300px",
                    ),
                    margin_top=rx.breakpoints(
                        initial="15px",
                        sm="20px",
                        lg="20px",
                    ),
                    border_radius="12px",
                    box_shadow="0 4px 12px rgba(0, 0, 0, 0.3)",
                    transition="all 0.3s ease-in-out",
                    _hover={"transform": "scale(1.03)"},
                ),
                dark=rx.image(
                    src="/images/dark-landing.png",
                    alt="Telecom Dashboard",
                    width=rx.breakpoints(
                        initial="90%",
                        sm="80%",
                        lg="60%",
                    ),
                    max_width="600px",
                    height=rx.breakpoints(
                        initial="200px",
                        sm="250px",
                        lg="300px",
                    ),
                    margin_top=rx.breakpoints(
                        initial="15px",
                        sm="20px",
                        lg="20px",
                    ),
                    border_radius="12px",
                    box_shadow="0 4px 12px rgba(0, 0, 0, 0.3)",
                    transition="all 0.3s ease-in-out",
                    _hover={"transform": "scale(1.03)"},
                ),
            ),
            # Footer text
            rx.text(
                "Powered by Reflex • Built for Scale",
                font_size=rx.breakpoints(
                    initial="0.8em",
                    sm="0.9em",
                    lg="0.9em",
                ),
                color=rx.color_mode_cond(
                    light=rx.color("gray", 8),
                    dark="#B19CD9",
                ),
                margin_top=rx.breakpoints(
                    initial="30px",
                    sm="35px",
                    lg="40px",
                ),
                text_align="center",
            ),
            spacing="3",
            align_items="center",
            width="100%",
            max_width="100%",
            padding=rx.breakpoints(
                initial="1em",
                sm="1.5em",
                lg="2em",
            ),
        ),
        align_items="center",
        justify_content="center",
        min_height="85vh",
        width="100%",
        max_width="100%",
        padding=rx.breakpoints(
            initial="1em",
            sm="1.5em",
            lg="2em",
        ),
        # Updated background with new gradients for light and dark modes
        background=rx.color_mode_cond(
            light="linear-gradient(135deg, #D5E3F0 0%, #F5E8D8 100%)",  # Light mode gradient
            dark="linear-gradient(135deg, #0A0F2A 0%, #1A2A4A 100%)",  # Dark mode gradient
        ),
        background_position="center",
        background_size="cover",
        overflow="hidden",
        box_sizing="border-box",
        opacity=rx.cond(IndexState.show_content, "1.0", "0.0"),
        transition="opacity 0.5s ease-in-out",
    )
