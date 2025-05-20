import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from inventory_system.state.permission_state import PermissionsManagementState

# List of available colors from Radix themes
COLOR = [color for color in LiteralAccentColor.__args__ if color != "gray"]


async def get_category_color(category_name: str) -> str:
    """Get a consistent color based on the category.

    Args:
        category_name: The category name

    Returns:
        A color from the COLOR list or gray for 'Uncategorized'
    """
    # Special case for Uncategorized
    if category_name == "Uncategorized":
        return "gray"

    # Get all categories from the state
    categories = await PermissionsManagementState.get_var_value("perm_categories", [])

    # If "All" is in categories (as it usually is), remove it
    if "All" in categories:
        categories = [c for c in categories if c != "All"]

    # Remove "Uncategorized" if present since it has a special color
    categories = [c for c in categories if c != "Uncategorized"]
    print(categories)

    # Find the index of the category in the sorted list
    try:
        index = sorted(categories).index(category_name)
        # Map the index to a color from the COLOR list
        color_index = index % len(COLOR)
        return COLOR[color_index]
    except (ValueError, IndexError):
        # Default color if category not found
        return "blue"


def category_badge(category: rx.Var[str]) -> rx.Component:
    """Create a badge for category with consistent coloring.

    Args:
        category: The category name (string, not rx.Var)

    Returns:
        A badge component with color based on the category
    """
    # Get color for the category
    color_scheme = get_category_color(category)

    # Choose appropriate icon
    icon = "folder"

    return rx.badge(
        rx.icon(icon, size=16),
        category,
        color_scheme=color_scheme,
        radius="large",
        variant="surface",
        size="2",
    )
