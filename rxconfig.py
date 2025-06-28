import os

import reflex as rx

config = rx.Config(
    app_name="inventory_system",
    db_url=os.getenv(
        "DATABASE_URL",
    ),  # Adjust for PostgreSQL, MySQL, etc.
    plugins=[
        rx.plugins.TailwindV3Plugin(),  # Add this to explicitly enable Tailwind
    ],
    env_file=".env",
)
