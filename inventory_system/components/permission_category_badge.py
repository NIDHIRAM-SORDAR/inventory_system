import reflex as rx
from reflex import Var
from reflex.components.radix.themes.base import LiteralAccentColor

from inventory_system.state.permission_state import PermissionsManagementState

# List of available colors from Radix themes
COLOR = [color for color in LiteralAccentColor.__args__ if color != "gray"]


class CategoryBadgeState(rx.State):
    """State for handling category badge colors."""

    categories: list[str] = []

    async def on_mount(self):
        self.categories = await self.get_state(
            PermissionsManagementState
        ).perm_categories

    def get_category_color(self, category_name: str) -> str:
        if category_name == "Uncategorized":
            return "gray"
        filtered_categories = [
            c for c in self.categories if c != "All" and c != "Uncategorized"
        ]
        try:
            index = sorted(filtered_categories).index(category_name)
            color_index = index % len(COLOR)
            return COLOR[color_index]
        except (ValueError, IndexError):
            return "blue"


def category_badge(category: str | Var[str]) -> rx.Component:
    """Create a badge for category with consistent coloring.

    Args:
        category: The category name as a string or Var[str]

    Returns:
        A badge component with appropriate styling
    """

    return rx.cond(
        category == "Uncategorized",
        rx.badge(
            rx.icon("folder", size=16),
            "Uncategorized",
            color_scheme="gray",
            radius="large",
            variant="surface",
            size="2",
        ),
        rx.badge(
            rx.icon("folder", size=16),
            category,
            color_scheme=CategoryBadgeState.get_category_color(category),
            radius="large",
            variant="surface",
            size="2",
        ),
    )
