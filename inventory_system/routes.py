# inventory_system/routes.py
"""Route constants for the inventory system application."""

from __future__ import annotations

# Base Routes
INDEX_ROUTE = "/"
LOGIN_ROUTE = "/login"
REGISTER_ROUTE = "/register"
OVERVIEW_ROUTE = "/overview"
ABOUT_ROUTE = "/about"
PROFILE_ROUTE = "/profile"
SETTINGS_ROUTE = "/settings"
TABLE_ROUTE = "/table"
SUPPLIER_REGISTER_ROUTE = "/supplier-register"

# Admin Routes
ADMIN_ROUTE = "/admin"
USER_MANAGEMENT_ROUTE = "/admin/users"  # Renamed from ADMIN_USERS_ROUTE
SUPPLIER_APPROVAL_ROUTE = "/admin/suppliers"  # Renamed from ADMIN_SUPPLIERS_ROUTE

# Dictionary to store routes (for easy access and modification)
_routes = {
    "index": INDEX_ROUTE,
    "login": LOGIN_ROUTE,
    "register": REGISTER_ROUTE,
    "overview": OVERVIEW_ROUTE,
    "about": ABOUT_ROUTE,
    "profile": PROFILE_ROUTE,
    "settings": SETTINGS_ROUTE,
    "table": TABLE_ROUTE,
    "supplier_register": SUPPLIER_REGISTER_ROUTE,
    "admin": ADMIN_ROUTE,
    "user_management": USER_MANAGEMENT_ROUTE,  # Renamed from admin_users
    "supplier_approval": SUPPLIER_APPROVAL_ROUTE,  # Renamed from admin_suppliers
}


def get_route(name: str) -> str:
    """Get a route by its name.

    Args:
        name: The name of the route (e.g., 'login', 'register').

    Returns:
        The route path as a string.

    Raises:
        KeyError: If the route name is not found.
    """
    return _routes[name]


def set_route(name: str, route: str) -> None:
    """Set a route by its name.

    Args:
        name: The name of the route (e.g., 'login', 'register').
        route: The route path to set.

    Raises:
        KeyError: If the route name is not found.
    """
    if name not in _routes:
        raise KeyError(f"Route '{name}' not found in available routes.")
    _routes[name] = route
    # Update the corresponding constant
    globals()[f"{name.upper()}_ROUTE"] = route
