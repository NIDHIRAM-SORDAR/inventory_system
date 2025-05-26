from typing import Any, Dict, List

import reflex as rx

from inventory_system.state.permission_state import PermissionsManagementState


def permission_card(permission: Dict[str, str]) -> rx.Component:
    """Responsive permission card with improved mobile layout."""
    return rx.card(
        rx.vstack(
            # Header section with category badge
            rx.hstack(
                rx.cond(
                    permission["category"] == "Uncategorized",
                    rx.badge(
                        rx.icon("book-x", size=14),
                        rx.text(permission["category"], size="1"),
                        color_scheme="gray",
                        radius="large",
                        variant="surface",
                        size="1",
                    ),
                    rx.badge(
                        rx.icon("layers-2", size=14),
                        rx.text(permission["category"], size="1"),
                        color_scheme="blue",
                        radius="large",
                        variant="surface",
                        size="1",
                    ),
                ),
                rx.spacer(),
                # Action buttons - always visible on mobile for better UX
                rx.hstack(
                    rx.button(
                        rx.icon("pencil", size=16),
                        rx.text("Edit", display=["none", "none", "block"]),
                        variant="ghost",
                        size="2",
                        color_scheme="blue",
                        on_click=lambda: (
                            PermissionsManagementState.open_perm_edit_modal(
                                permission["id"]
                            )
                        ),
                        style={
                            "min_width": ["40px", "40px", "auto"],
                            "padding": ["8px", "8px", "8px 12px"],
                        },
                    ),
                    rx.button(
                        rx.icon("trash", size=16),
                        rx.text("Delete", display=["none", "none", "block"]),
                        variant="ghost",
                        size="2",
                        color_scheme="red",
                        on_click=lambda: (
                            PermissionsManagementState.open_perm_delete_modal(
                                permission["id"]
                            )
                        ),
                        style={
                            "min_width": ["40px", "40px", "auto"],
                            "padding": ["8px", "8px", "8px 12px"],
                        },
                    ),
                    spacing="2",
                ),
                align="center",
                width="100%",
            ),
            # Content section
            rx.vstack(
                rx.heading(
                    permission["name"].to_string().replace("_", " ").title(),
                    size=rx.breakpoints(
                        initial="4",
                        sm="4",
                        lg="5",
                    ),
                    weight="bold",
                    color=rx.color_mode_cond(light="gray.900", dark="gray.100"),
                    line_height="1.2",
                ),
                rx.text(
                    permission["description"],
                    size=rx.breakpoints(
                        initial="2",
                        sm="3",
                        lg="3",
                    ),
                    color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                    line_height="1.5",
                ),
                align="start",
                spacing="2",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        padding=["4", "5", "6"],
        width="100%",
        max_width="100%",
        style={
            "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            "cursor": "pointer",
            "border": f"1px solid {rx.color_mode_cond(light='var(--gray-4)', dark='var(--gray-6)')}",
            "background": rx.color_mode_cond(light="white", dark="var(--gray-2)"),
            "&:hover": {
                "transform": "translateY(-2px)",
                "box_shadow": rx.color_mode_cond(
                    light="0 8px 25px rgba(0, 0, 0, 0.1)",
                    dark="0 8px 25px rgba(0, 0, 0, 0.3)",
                ),
                "border_color": rx.color_mode_cond(
                    light="var(--blue-6)", dark="var(--blue-5)"
                ),
            },
            "&:active": {
                "transform": "translateY(0px)",
                "transition": "transform 0.1s ease",
            },
        },
    )


def search_and_filter() -> rx.Component:
    """Enhanced responsive search and filter component."""
    return rx.card(
        rx.vstack(
            # Main action row
            rx.vstack(
                # Search input
                rx.hstack(
                    rx.icon(
                        "search",
                        size=18,
                        color=rx.color_mode_cond(light="gray.500", dark="gray.400"),
                    ),
                    rx.input(
                        placeholder="Search permissions...",
                        value=PermissionsManagementState.perm_search_query,
                        on_change=PermissionsManagementState.set_perm_search_query,
                        variant="soft",
                        size="3",
                        width="100%",
                        style={
                            "border": "none",
                            "box_shadow": "none",
                            "background": "transparent",
                            "font_size": ["14px", "15px", "16px"],
                            "_placeholder": {
                                "color": rx.color_mode_cond(
                                    light="gray.500", dark="gray.500"
                                )
                            },
                        },
                    ),
                    align="center",
                    padding="3",
                    border_radius="var(--radius-3)",
                    background=rx.color_mode_cond(light="gray.50", dark="gray.800"),
                    border=f"1px solid {rx.color_mode_cond(light='var(--gray-5)', dark='var(--gray-6)')}",
                    style={
                        "transition": "all 0.2s ease",
                        "&:hover": {
                            "border_color": rx.color_mode_cond(
                                light="var(--gray-7)", dark="var(--gray-5)"
                            )
                        },
                        "&:focus-within": {
                            "border_color": "var(--blue-8)",
                            "box_shadow": "0 0 0 3px var(--blue-3)",
                        },
                    },
                    width="100%",
                ),
                # Add button - full width on mobile
                rx.button(
                    rx.icon("plus", size=18),
                    rx.text("Add New Permission", size="3"),
                    on_click=PermissionsManagementState.open_perm_add_modal,
                    size="3",
                    color_scheme="blue",
                    variant="solid",
                    width=["100%", "100%", "auto"],
                    style={
                        "min_height": "44px",  # Better touch target
                        "font_weight": "600",
                    },
                ),
                spacing="3",
                width="100%",
            ),
            # Filter and stats row
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Category:",
                        size="2",
                        color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                        weight="medium",
                    ),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="All categories",
                            variant="soft",
                            size="2",
                            style={
                                "min_width": ["120px", "150px"],
                                "background": rx.color_mode_cond(
                                    light="gray.50", dark="gray.800"
                                ),
                            },
                        ),
                        rx.select.content(
                            rx.select.item("All", value="All"),
                            rx.cond(
                                PermissionsManagementState.perm_categories,
                                rx.foreach(
                                    PermissionsManagementState.perm_categories,
                                    lambda category: rx.cond(
                                        category != "All",
                                        rx.select.item(category, value=category),
                                        None,
                                    ),
                                ),
                                None,
                            ),
                        ),
                        value=PermissionsManagementState.perm_selected_category,
                        on_change=PermissionsManagementState.set_perm_category_filter,
                    ),
                    align="center",
                    spacing="2",
                    width=["100%", "auto"],
                    justify=rx.breakpoints(
                        initial="start",
                        sm="center",
                        lg="between",
                    ),
                ),
                # Results counter
                rx.text(
                    rx.cond(
                        PermissionsManagementState.perm_search_query != "",
                        (
                            f"Showing {PermissionsManagementState.filtered_permissions.length()} "
                            f"of {PermissionsManagementState.permissions.length()} permissions"
                        ),
                        f"{PermissionsManagementState.permissions.length()} total permissions",
                    ),
                    color=rx.color_mode_cond(light="gray.600", dark="gray.400"),
                    size="2",
                    weight="medium",
                    text_align=["center", "left"],
                ),
                spacing="3",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        padding=["4", "5", "6"],
        margin_bottom="6",
        background=rx.color_mode_cond(light="gray.25", dark="gray.900"),
        border=f"1px solid {rx.color_mode_cond(light='var(--gray-4)', dark='var(--gray-6)')}",
        style={
            "backdrop_filter": "blur(10px)",
            "box_shadow": rx.color_mode_cond(
                light="0 2px 8px rgba(0, 0, 0, 0.04)",
                dark="0 2px 8px rgba(0, 0, 0, 0.2)",
            ),
        },
        width="100%",
    )


def permission_form_modal(is_edit: bool = False) -> rx.Component:
    """Enhanced responsive form modal."""
    title = rx.cond(is_edit, "Edit Permission", "Add New Permission")
    submit_handler = (
        PermissionsManagementState.update_permission
        if is_edit
        else PermissionsManagementState.add_permission
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    title,
                    size="6",
                    weight="bold",
                    margin_bottom="4px",
                ),
                rx.dialog.description(
                    "Fill in the permission details below.",
                    size="3",
                    color=rx.color_mode_cond(light="gray.600", dark="gray.400"),
                    margin_bottom="8px",
                ),
                # Form fields
                rx.vstack(
                    rx.vstack(
                        rx.text(
                            "Permission Name",
                            size="2",
                            weight="medium",
                            color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                        ),
                        rx.input(
                            placeholder="Enter permission name...",
                            value=PermissionsManagementState.perm_form_name,
                            on_change=PermissionsManagementState.set_perm_form_name,
                            size="3",
                            width="100%",
                            style={"min_height": "44px"},
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Category",
                            size="2",
                            weight="medium",
                            color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                        ),
                        rx.cond(
                            is_edit,
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Select or enter category",
                                    size="3",
                                    width="100%",
                                    style={"min_height": "44px"},
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        PermissionsManagementState.perm_categories,
                                        lambda category: rx.cond(
                                            category != "All",
                                            rx.select.item(category, value=category),
                                            None,
                                        ),
                                    ),
                                ),
                                value=PermissionsManagementState.perm_form_category,
                                on_change=PermissionsManagementState.set_perm_form_category,
                                width="100%",
                            ),
                            rx.input(
                                placeholder="Enter category...",
                                value=PermissionsManagementState.perm_form_category,
                                on_change=PermissionsManagementState.set_perm_form_category,
                                size="3",
                                width="100%",
                                style={"min_height": "44px"},
                            ),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Description",
                            size="2",
                            weight="medium",
                            color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                        ),
                        rx.text_area(
                            placeholder="Describe what this permission allows...",
                            value=PermissionsManagementState.perm_form_description,
                            on_change=PermissionsManagementState.set_perm_form_description,
                            width="100%",
                            height="120px",
                            resize="vertical",
                            size="3",
                            style={"min_height": "120px"},
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                # Action buttons
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                            width=["100%", "auto"],
                            style={"min_height": "44px"},
                        )
                    ),
                    rx.button(
                        rx.cond(is_edit, "Update Permission", "Add Permission"),
                        on_click=submit_handler,
                        loading=PermissionsManagementState.perm_is_loading,
                        size="3",
                        color_scheme="blue",
                        width=["100%", "auto"],
                        style={"min_height": "44px", "font_weight": "600"},
                    ),
                    spacing="3",
                    width="100%",
                    justify="end",
                    flex_direction=["column-reverse", "row"],
                ),
                spacing="6",
                width="100%",
            ),
            max_width=["85vw", "500px"],
            width=["80vw", "500px"],
            padding=["4", "6"],
            style={
                "max_height": "90vh",
                "overflow_y": "auto",
            },
        ),
        open=PermissionsManagementState.perm_show_edit_modal
        if is_edit
        else PermissionsManagementState.perm_show_add_modal,
        on_open_change=lambda x: rx.cond(
            ~x, PermissionsManagementState.close_perm_modals(), None
        ),
    )


def delete_confirmation_modal() -> rx.Component:
    """Enhanced delete confirmation modal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("triangle-alert", size=24, color="red"),
                    rx.dialog.title(
                        "Delete Permission",
                        size="5",
                        weight="bold",
                        color="red",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.dialog.description(
                    rx.cond(
                        PermissionsManagementState.permission_assigned_roles,
                        # MODIFIED: Updated to show message directing to role tab
                        rx.vstack(
                            rx.text(
                                "This permission is assigned to the following "
                                "roles and cannot be deleted until detached:",
                                size="3",
                                color=rx.color_mode_cond(
                                    light="gray.700", dark="gray.300"
                                ),
                                line_height="1.5",
                            ),
                            # NEW: Wrap badges in flex container with wrapping
                            rx.flex(
                                rx.foreach(
                                    PermissionsManagementState.permission_assigned_roles,
                                    lambda role: rx.badge(
                                        role,
                                        color_scheme="orange",
                                        variant="soft",
                                        size="2",
                                        margin="2px",  # MODIFIED: Adjusted margin for flex layout
                                    ),
                                ),
                                wrap="wrap",
                                spacing="2",
                                width="100%",
                            ),
                            # NEW: Message to direct user to role tab
                            rx.text(
                                "Please navigate to the Role Management tab to detach this permission from the listed roles.",
                                size="3",
                                color=rx.color_mode_cond(
                                    light="gray.700", dark="gray.300"
                                ),
                                line_height="1.5",
                                font_weight="600",
                            ),
                            # REMOVED: Detach from All Roles button
                            spacing="3",
                            width="100%",
                        ),
                        # MODIFIED: Default description when no roles are assigned
                        rx.text(
                            "Are you sure you want to delete this permission? This action "
                            "cannot be undone and may affect users "
                            "who currently have this permission.",
                            size="3",
                            color=rx.color_mode_cond(light="gray.700", dark="gray.300"),
                            line_height="1.5",
                        ),
                    ),
                    width="100%",
                ),
                # MODIFIED: Show delete button only if no roles are assigned
                rx.cond(
                    ~PermissionsManagementState.permission_assigned_roles,
                    rx.hstack(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                                size="3",
                                width=["100%", "auto"],
                                style={"min_height": "44px"},
                            )
                        ),
                        rx.button(
                            "Delete Permission",
                            color_scheme="red",
                            on_click=PermissionsManagementState.delete_permission,
                            loading=PermissionsManagementState.perm_is_loading,
                            size="3",
                            width=["100%", "auto"],
                            style={"min_height": "44px", "font_weight": "600"},
                        ),
                        spacing="3",
                        width="100%",
                        justify="end",
                        flex_direction=["column-reverse", "row"],
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                            width=["100%", "auto"],
                            style={"min_height": "44px"},
                        )
                    ),
                ),
                spacing="4",
                width="100%",
            ),
            max_width=["85vw", "450px"],
            width=["80vw", "450px"],
            padding=["4", "6"],
        ),
        open=PermissionsManagementState.perm_show_delete_modal,
        on_open_change=lambda x: rx.cond(
            ~x, PermissionsManagementState.close_perm_modals(), None
        ),
    )


def permissions_grid(permissions: List[Dict[str, Any]]) -> rx.Component:
    """Responsive grid layout for permissions."""
    return rx.box(
        rx.vstack(
            rx.foreach(permissions, permission_card),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def category_section(category: str, permissions: List[Dict[str, Any]]) -> rx.Component:
    """Category section with improved styling."""
    return rx.vstack(
        rx.hstack(
            rx.heading(
                category,
                size=rx.breakpoints(
                    initial="3",
                    sm="5",
                    lg="7",
                ),
                weight="bold",
                color=rx.color_mode_cond(light="gray.900", dark="gray.100"),
            ),
            rx.badge(
                f"{permissions.length()} permission{rx.cond(permissions.length() != 1, 's', '')}",
                color_scheme="blue",
                variant="soft",
                size="1",
            ),
            align="center",
            spacing="3",
            margin_bottom="10px",
        ),
        permissions_grid(permissions),
        spacing="0",
        width="100%",
        margin_bottom="16px",
    )


def empty_state() -> rx.Component:
    """Enhanced empty state component."""
    return rx.card(
        rx.vstack(
            rx.icon(
                "search-x",
                size=48,
                color=rx.color_mode_cond(light="gray.400", dark="gray.500"),
            ),
            rx.heading(
                "No permissions found",
                size="5",
                color=rx.color_mode_cond(light="gray.600", dark="gray.400"),
                text_align="center",
            ),
            rx.text(
                "Try adjusting your search terms or category "
                "filter to find what you're looking for.",
                size="3",
                color=rx.color_mode_cond(light="gray.500", dark="gray.500"),
                text_align="center",
                line_height="1.5",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("x", size=16),
                    "Clear Search",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PermissionsManagementState.set_perm_search_query(""),
                    size="2",
                ),
                rx.button(
                    rx.icon("layers", size=16),
                    "Show All Categories",
                    variant="soft",
                    color_scheme="blue",
                    on_click=PermissionsManagementState.set_perm_category_filter("All"),
                    size="2",
                ),
                spacing="2",
                justify="center",
                flex_wrap="wrap",
            ),
            spacing="4",
            align="center",
            padding="8",
            max_width="400px",
        ),
        padding="6",
        width="100%",
        style={
            "background": rx.color_mode_cond(light="gray.25", dark="gray.900"),
            "border": f"2px dashed {rx.color_mode_cond(light='var(--gray-5)', dark='var(--gray-6)')}",
            "border_radius": "var(--radius-4)",
        },
    )


def permissions_tab() -> rx.Component:
    """Main permissions management component with enhanced responsiveness."""
    return rx.vstack(
        search_and_filter(),
        rx.cond(
            PermissionsManagementState.filtered_permissions,
            rx.cond(
                PermissionsManagementState.perm_selected_category == "All",
                # Show all categories grouped
                rx.vstack(
                    rx.foreach(
                        PermissionsManagementState.filtered_permissions_by_category.keys(),
                        lambda category: category_section(
                            category,
                            PermissionsManagementState.filtered_permissions_by_category[
                                category
                            ],
                        ),
                    ),
                    spacing="0",
                    width="100%",
                ),
                # Show single category
                category_section(
                    PermissionsManagementState.perm_selected_category,
                    PermissionsManagementState.filtered_permissions,
                ),
            ),
            empty_state(),
        ),
        # Modals
        permission_form_modal(is_edit=False),
        permission_form_modal(is_edit=True),
        delete_confirmation_modal(),
        spacing="6",
        width="100%",
        max_width="1200px",
        margin="2px auto",
        padding=["4", "6", "8"],
        on_mount=PermissionsManagementState.load_permissions,
    )
