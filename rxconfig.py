import reflex as rx

config = rx.Config(
    app_name="inventory_system",
    db_url="sqlite:///reflex.db",  # Adjust for PostgreSQL, MySQL, etc.
)
