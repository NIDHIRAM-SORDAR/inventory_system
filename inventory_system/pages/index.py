import reflex as rx
from inventory_system.templates import template
from inventory_system import routes  # Import the routes module

@template(route=routes.INDEX_ROUTE, title="Telecom Inventory System")
def index() -> rx.Component:
    return rx.vstack(
        # Header Section
        rx.heading(
            "Telecom Inventory System",
            size="3",
            color="white",
            margin_bottom="10px",
        ),
        rx.text(
            "Efficiently manage your telecom inventory, orders, and stores.",
            color="gray",
            font_size="1.2em",
            margin_bottom="20px",
        ),

        # Call to Action
        rx.button(
            "Get Started",
            size="3",
            background_color="#6B46C1",
            color="white",
            _hover={"background_color": "#553C9A"},
            on_click=rx.redirect(routes.LOGIN_ROUTE),  # Use the route constant
        ),

        # Optional: Key Features (minimal)
        rx.text(
            "Track products, manage orders, and oversee stores with ease.",
            color="gray",
            font_size="0.9em",
            margin_top="30px",
        ),

        # Styling for the entire stack
        align_items="center",
        justify_content="center",
        min_height="100vh",
        background_color="#1A202C",
        padding="20px",
    )