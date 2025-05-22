from typing import Any, Dict, List

import reflex as rx

from inventory_system.state.permission_state import PermissionsManagementState


def permission_card(permission: Dict[str, str]) -> rx.Component:
    """Permission card with dynamic category color and unified layout."""
    return rx.card(
        rx.hstack(
            rx.cond(
                permission["category"] == "Uncategorized",
                rx.badge(
                    rx.icon("book-x", size=16),
                    rx.text(permission["category"]),
                    color_scheme="gray",
                    radius="large",
                    variant="surface",
                    size="2",
                ),
                rx.badge(
                    rx.icon("layers-2", size=16),
                    rx.text(permission["category"]),
                    color_scheme="tomato",
                    radius="large",
                    variant="surface",
                    size="2",
                ),
            ),
            rx.vstack(
                rx.heading(
                    permission["name"].to_string().replace("_", " ").title(),
                    size="4",
                    weight="medium",
                    no_wrap=True,
                ),
                rx.text(
                    permission["description"],
                    color="gray.500",
                    size="2",
                    style={"white_space": "pre-line"},
                ),
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Edit",
                    variant="soft",
                    size="1",
                    on_click=lambda: PermissionsManagementState.open_perm_edit_modal(
                        permission["id"]
                    ),
                ),
                rx.button(
                    rx.icon("trash", size=14),
                    "Delete",
                    variant="soft",
                    size="1",
                    on_click=lambda: PermissionsManagementState.open_perm_delete_modal(
                        permission["id"]
                    ),
                ),
                spacing="2",
            ),
            align="center",
            justify="between",
            width="100%",
        ),
        padding="3",
        width="100%",
        min_width="250px",
        style={
            "transition": "all 0.2s ease",
            "cursor": "pointer",
            "&:hover": {
                "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
                "transform": "translateY(-2px)",
            },
        },
    )


def search_and_filter() -> rx.Component:
    """Enhanced search input and category filter with theme consistency."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("search", size=18, color="var(--gray-9)"),
                    rx.input(
                        placeholder="Search permissions...",
                        value=PermissionsManagementState.perm_search_query,
                        on_change=PermissionsManagementState.set_perm_search_query,
                        variant="soft",
                        width=["100%", "250px", "300px", "350px"],
                        color="var(--gray-11)",
                        style={
                            "border": "none",
                            "box_shadow": "none",
                            "background": "transparent",
                            "_placeholder": {"color": "var(--gray-8)"},
                        },
                    ),
                    align="center",
                    padding="2",
                    border_radius="var(--radius-2)",
                    background="var(--gray-3)",
                    border="1px solid var(--gray-5)",
                    style={
                        "transition": "all 0.2s ease",
                        "&:hover": {"border_color": "var(--gray-7)"},
                        "&:focus-within": {"border_color": "var(--blue-8)"},
                    },
                    width=["100%", "auto"],
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "Add Permission",
                    on_click=PermissionsManagementState.open_perm_add_modal,
                    size="3",
                    color_scheme="blue",
                    variant="solid",
                    border_radius="var(--radius-2)",
                ),
                justify="between",
                align="center",
                width="100%",
                flex_wrap="wrap",
                spacing="3",
            ),
            rx.hstack(
                rx.hstack(
                    rx.text("Filter by category:", size="2", color="var(--gray-10)"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="All categories",
                            variant="soft",
                            size="2",
                            color="var(--gray-11)",
                            style={"background": "var(--gray-2)"},
                        ),
                        rx.select.content(
                            rx.foreach(
                                PermissionsManagementState.perm_categories,
                                lambda category: rx.select.item(
                                    category,
                                    value=category,
                                ),
                            ),
                        ),
                        value=PermissionsManagementState.perm_selected_category,
                        on_change=PermissionsManagementState.set_perm_category_filter,
                        width=["100%", "200px"],
                    ),
                    align="center",
                    spacing="2",
                    width=["100%", "auto"],
                ),
                rx.text(
                    rx.cond(
                        PermissionsManagementState.perm_search_query != "",
                        (
                            f"Showing {PermissionsManagementState.filtered_permissions.length()} "  # noqa: E501
                            f"of {PermissionsManagementState.permissions.length()} "
                            "permissions"
                        ),
                        f"{PermissionsManagementState.permissions.length()} "
                        "total permissions",
                    ),
                    color="var(--gray-9)",
                    size="2",
                ),
                justify="between",
                align="center",
                width="100%",
                flex_wrap="wrap",
                spacing="3",
            ),
            spacing="4",
            width="100%",
        ),
        padding=["3", "4"],
        margin_bottom="6",
        border_radius="var(--radius-3)",
        background="var(--gray-1)",
        border="1px solid var(--gray-4)",
        box_shadow="0 1px 4px rgba(0, 0, 0, 0.03)",
    )


def pagination_controls() -> rx.Component:
    """Enhanced pagination controls."""
    return rx.cond(
        PermissionsManagementState.perm_total_pages > 1,
        rx.hstack(
            rx.text(
                (
                    f"Page {PermissionsManagementState.perm_current_page} "
                    f"of {PermissionsManagementState.perm_total_pages}"
                ),
                color="gray.600",
                size="2",
            ),
            rx.spacer(),
            rx.hstack(
                rx.icon_button(
                    rx.icon("chevrons-left", size=16),
                    variant="soft",
                    size="2",
                    on_click=lambda: PermissionsManagementState.set_perm_page(1),
                    disabled=PermissionsManagementState.perm_current_page == 1,
                ),
                rx.icon_button(
                    rx.icon("chevron-left", size=16),
                    variant="soft",
                    size="2",
                    on_click=PermissionsManagementState.prev_perm_page,
                    disabled=PermissionsManagementState.perm_current_page == 1,
                ),
                rx.text(
                    f"{PermissionsManagementState.perm_current_page}",
                    size="2",
                    weight="medium",
                ),
                rx.icon_button(
                    rx.icon("chevron-right", size=16),
                    variant="soft",
                    size="2",
                    on_click=PermissionsManagementState.next_perm_page,
                    disabled=PermissionsManagementState.perm_current_page
                    == PermissionsManagementState.perm_total_pages,
                ),
                rx.icon_button(
                    rx.icon("chevrons-right", size=16),
                    variant="soft",
                    size="2",
                    on_click=lambda: PermissionsManagementState.set_perm_page(
                        PermissionsManagementState.perm_total_pages
                    ),
                    disabled=PermissionsManagementState.perm_current_page
                    == PermissionsManagementState.perm_total_pages,
                ),
                spacing="1",
            ),
            justify="between",
            align="center",
            width="100%",
            padding_top="6",
            flex_wrap="wrap",
        ),
    )


def permission_form_modal(is_edit: bool = False) -> rx.Component:
    """Responsive Add/Edit permission modal form."""
    title = "Edit Permission" if is_edit else "Add New Permission"
    submit_handler = (
        PermissionsManagementState.update_permission
        if is_edit
        else PermissionsManagementState.add_permission
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.dialog.description(
                "Fill in the permission details below.", margin_bottom="4"
            ),
            rx.vstack(
                rx.input(
                    placeholder="Permission Name",
                    value=PermissionsManagementState.perm_form_name,
                    on_change=PermissionsManagementState.set_perm_form_name,
                    width="100%",
                ),
                rx.select.root(
                    rx.select.trigger(placeholder="Select category", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            PermissionsManagementState.perm_categories,
                            lambda category: rx.select.item(category, value=category),
                        ),
                    ),
                    value=PermissionsManagementState.perm_form_category,
                    on_change=PermissionsManagementState.set_perm_form_category,
                    width="100%",
                ),
                rx.text_area(
                    placeholder="Describe what this permission allows...",
                    value=PermissionsManagementState.perm_form_description,
                    on_change=PermissionsManagementState.set_perm_form_description,
                    width="100%",
                    height="100px",
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray")
                ),
                rx.dialog.close(
                    rx.button(
                        "Update" if is_edit else "Add",
                        on_click=submit_handler,
                        loading=PermissionsManagementState.perm_is_loading,
                    ),
                ),
                spacing="2",
                justify="end",
            ),
            max_width="95vw",
            width=["95vw", "400px"],
            padding=["3", "4"],
        ),
        open=PermissionsManagementState.perm_show_edit_modal
        if is_edit
        else PermissionsManagementState.perm_show_add_modal,
        on_open_change=lambda x: rx.cond(
            ~x, PermissionsManagementState.close_perm_modals(), None
        ),
    )


def delete_confirmation_modal() -> rx.Component:
    """Delete confirmation modal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Delete Permission"),
            rx.dialog.description(
                (
                    f"Are you sure you want to delete the permission "
                    f"'{PermissionsManagementState.perm_deleting_id}'? "
                    "This action cannot be undone."
                ),
                margin_bottom="4",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.dialog.close(
                    rx.button(
                        "Delete",
                        color_scheme="red",
                        on_click=PermissionsManagementState.delete_permission,
                        loading=PermissionsManagementState.perm_is_loading,
                    ),
                ),
                spacing="3",
                margin_top="4",
                justify="end",
                flex_wrap="wrap",
            ),
            max_width=["90vw", "400px"],
            padding=["4", "6"],
        ),
        open=PermissionsManagementState.perm_show_delete_modal,
        on_open_change=lambda x: rx.cond(
            ~x, PermissionsManagementState.close_perm_modals(), None
        ),
    )


def permissions_tab() -> rx.Component:
    """Permissions management tab content with improved layout."""

    # Helper function to render permissions for a category
    def render_category(
        category: str, permissions: List[Dict[str, Any]]
    ) -> rx.Component:
        return rx.vstack(
            rx.heading(category, size="5", margin_bottom="2"),
            rx.box(
                rx.vstack(
                    rx.foreach(permissions, permission_card),
                    spacing="2",
                    width="100%",
                ),
                overflow_y=rx.cond(permissions.length() > 6, "auto", "visible"),
                max_height="400px",
                width="100%",
            ),
            spacing="2",
        )

    # Main layout
    return rx.vstack(
        search_and_filter(),
        rx.cond(
            PermissionsManagementState.filtered_permissions,
            rx.cond(
                PermissionsManagementState.perm_selected_category == "All",
                rx.vstack(
                    rx.foreach(
                        PermissionsManagementState.filtered_permissions_by_category.keys(),
                        lambda category: render_category(
                            category,
                            PermissionsManagementState.filtered_permissions_by_category[
                                category
                            ],
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                render_category(
                    PermissionsManagementState.perm_selected_category,
                    PermissionsManagementState.filtered_permissions,
                ),
            ),
            rx.card(
                rx.vstack(
                    rx.icon("folder-search", size=3, color="gray.300"),
                    rx.heading("No permissions found", size="5", color="gray.600"),
                    rx.text(
                        "Try adjusting your search or filters",
                        color="gray.400",
                        size="3",
                    ),
                    rx.button(
                        "Clear filters",
                        variant="soft",
                        on_click=[
                            PermissionsManagementState.set_perm_search_query(""),
                            PermissionsManagementState.set_perm_category_filter("All"),
                        ],
                        margin_top="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="4",
                width="100%",
                style={
                    "background": "var(--gray-1)",
                    "border": "1px solid var(--gray-4)",
                },
            ),
        ),
        permission_form_modal(is_edit=False),
        permission_form_modal(is_edit=True),
        delete_confirmation_modal(),
        spacing="4",
        width="100%",
        padding=["2", "4"],
        on_mount=PermissionsManagementState.load_permissions,
    )
