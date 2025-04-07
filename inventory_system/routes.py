from __future__ import annotations

# Route constants
LOGIN_ROUTE = "/login"
LOGOUT_ROUTE = "/logout"
REGISTER_ROUTE = "/register"
INDEX_ROUTE = "/"
OVERVIEW_ROUTE = "/overview"
PROFILE_ROUTE = "/profile"
SETTINGS_ROUTE = "/settings"
ABOUT_ROUTE = "/about"
TABLE_ROUTE = "/table"
SUPPLIER_REGISTER_ROUTE = "/supplier-register"
SUPPLIER_APPROV_ROUTE = "/supplier-management"
ADMIN_MGMT = "/admin-management"

# Dictionary to store routes (for easy access and modification)
_routes = {
    "login": LOGIN_ROUTE,
    "register": REGISTER_ROUTE,
    "index": INDEX_ROUTE,
    "profile": PROFILE_ROUTE,
    "settings": SETTINGS_ROUTE,
    "about": ABOUT_ROUTE,
    "table": TABLE_ROUTE,
    "supplier_register": SUPPLIER_REGISTER_ROUTE,
    "supplier_approval": SUPPLIER_APPROV_ROUTE,
    "admin-mgmt": ADMIN_MGMT,
    "logout": LOGOUT_ROUTE,
    "overview": OVERVIEW_ROUTE,

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