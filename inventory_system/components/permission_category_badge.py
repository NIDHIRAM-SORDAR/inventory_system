import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from inventory_system.state.permission_state import PermissionsManagementState

# List of available colors from Radix themes
COLOR = [color for color in LiteralAccentColor.__args__ if color != "gray"]


class CategoryBadgeState(rx.State):
    """State for handling category badge colors."""

    async def get_category_color(self, category_name: str) -> str:
        """Get a consistent color based on the category.

        Args:
            category_name: The category name

        Returns:
            A color from the COLOR list or gray for 'Uncategorized'
        """
        # Special case for Uncategorized
        if category_name == "Uncategorized":
            return "gray"

        # Get all categories from the PermissionsManagementState using get_var_value
        categories = await self.get_var_value(
            PermissionsManagementState.perm_categories, []
        )

        # Filter categories
        filtered_categories = [
            c for c in categories if c != "All" and c != "Uncategorized"
        ]

        # Find the index of the category in the sorted list
        try:
            index = sorted(filtered_categories).index(category_name)
            # Map the index to a color from the COLOR list
            color_index = index % len(COLOR)
            return COLOR[color_index]
        except (ValueError, IndexError):
            # Default color if category not found
            return "blue"


def category_badge(category: str) -> rx.Component:
    """Create a badge for category with consistent coloring.

    Args:
        category: The category name as a string

    Returns:
        A badge component with appropriate styling
    """
    # For the "Uncategorized" case, we can directly return a badge with gray color
    if category == "Uncategorized":
        return rx.badge(
            rx.icon("folder", size=16),
            "Uncategorized",
            color_scheme="gray",
            radius="large",
            variant="surface",
            size="2",
        )

    # For other categories, we need a component
    # that can compute its color based on state
    return rx.badge(
        rx.icon("folder", size=16),
        category,
        # Use an async_var to get the color
        color_scheme=CategoryBadgeState.get_category_color(category),
        radius="large",
        variant="surface",
        size="2",
    )
