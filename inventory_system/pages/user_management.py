import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.user_mgmt_state import UserManagementState
from inventory_system.templates.template import template


def _header_cell(text: str, icon: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )


def _edit_dialog(user: rx.Var) -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.icon_button(
                rx.icon("square-pen"),
                on_click=lambda: UserManagementState.open_edit_dialog(
                    user["id"], user["role"]
                ),
                color_scheme="blue",
                size="2",
                variant="solid",
                disabled=(user["role"] == "supplier"),
            )
        ),
        rx.alert_dialog.content(
            rx.vstack(
                rx.alert_dialog.title("Change User Role"),
                rx.alert_dialog.description(
                    f"Select a new role for {user['username']}.",
                    size="2",
                ),
                rx.inset(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Username"),
                                rx.table.column_header_cell("Email"),
                                rx.table.column_header_cell("Role"),
                            ),
                        ),
                        rx.table.body(
                            rx.table.row(
                                rx.table.row_header_cell(user["username"]),
                                rx.table.cell(user["email"]),
                                rx.table.cell(rx.text(user["role"])),
                            ),
                        ),
                        width="100%",
                    ),
                    side="x",
                    margin_y="16px",
                ),
                rx.radio(
                    ["admin", "employee"],
                    value=UserManagementState.selected_role,
                    on_change=UserManagementState.set_selected_role,
                    direction="column",
                    spacing="2",
                    width="100%",
                ),
                rx.flex(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                            on_click=UserManagementState.cancel_edit_dialog,
                        )
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Confirm",
                            color_scheme="blue",
                            size="2",
                            on_click=lambda: UserManagementState.change_user_role(
                                user["id"], UserManagementState.selected_role
                            ),
                        )
                    ),
                    direction="column",
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
                spacing="4",
                width="100%",
                padding="16px",
            ),
            style={"max_width": "90vw", "width": "400px"},
        ),
    )


def _show_user(user: rx.Var, index: int) -> rx.Component:
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(rx.text(user["role"])),
        rx.table.cell(
            rx.hstack(
                _edit_dialog(user),
                rx.icon_button(
                    rx.icon("trash-2"),
                    on_click=lambda: UserManagementState.confirm_delete_user(
                        user["id"]
                    ),
                    color_scheme="red",
                    size="2",
                    variant="solid",
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.content(
                rx.vstack(
                    rx.alert_dialog.title("Delete User"),
                    rx.alert_dialog.description(
                        f"Are you sure you want to delete user {user['username']}? "
                        "This action cannot be undone.",
                        size="2",
                    ),
                    rx.inset(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Username"),
                                    rx.table.column_header_cell("Email"),
                                    rx.table.column_header_cell("Role"),
                                ),
                            ),
                            rx.table.body(
                                rx.table.row(
                                    rx.table.row_header_cell(user["username"]),
                                    rx.table.cell(user["email"]),
                                    rx.table.cell(rx.text(user["role"])),
                                ),
                            ),
                            width="100%",
                        ),
                        side="x",
                        margin_y="16px",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                                size="2",
                                on_click=UserManagementState.cancel_delete,
                            )
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Delete",
                                color_scheme="red",
                                size="2",
                                on_click=UserManagementState.delete_user,
                            )
                        ),
                        direction="column",
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    spacing="4",
                    width="100%",
                    padding="16px",
                ),
                style={"max_width": "90vw", "width": "400px"},
            ),
            open=UserManagementState.show_delete_dialog
            & (UserManagementState.user_to_delete == user["id"]),
        ),
        style={"_hover": {"bg": hover_color}, "bg": bg_color},
        align="center",
    )


def _pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text(
            "Page ",
            rx.code(UserManagementState.page_number),
            f" of {UserManagementState.total_pages}",
            justify="end",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevrons-left", size=18),
                on_click=UserManagementState.first_page,
                opacity=rx.cond(UserManagementState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    UserManagementState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=18),
                on_click=UserManagementState.prev_page,
                opacity=rx.cond(UserManagementState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    UserManagementState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=18),
                on_click=UserManagementState.next_page,
                opacity=rx.cond(
                    UserManagementState.page_number == UserManagementState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    UserManagementState.page_number == UserManagementState.total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevrons-right", size=18),
                on_click=UserManagementState.last_page,
                opacity=rx.cond(
                    UserManagementState.page_number == UserManagementState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    UserManagementState.page_number == UserManagementState.total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            align="center",
            spacing="2",
            justify="end",
        ),
        spacing="5",
        margin_top="1em",
        align="center",
        width="100%",
        justify="end",
    )


@template(
    route=routes.USER_MANAGEMENT_ROUTE,
    title="User Management",
    on_load=UserManagementState.check_auth_and_load,
)
@reflex_local_auth.require_login
def user_management() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.heading("User Management", size="3"),
                rx.spacer(),
                rx.button(
                    "Back to Admin",
                    rx.icon("arrow-left"),
                    color_scheme="blue",
                    variant="soft",
                    size="2",
                    on_click=lambda: rx.redirect(routes.ADMIN_ROUTE),
                ),
                width="100%",
                align="center",
            ),
            rx.flex(
                rx.cond(
                    UserManagementState.sort_reverse,
                    rx.icon(
                        "arrow-down-z-a",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=UserManagementState.toggle_sort,
                    ),
                    rx.icon(
                        "arrow-down-a-z",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=UserManagementState.toggle_sort,
                    ),
                ),
                rx.select(
                    ["username", "email", "role"],
                    placeholder="Sort By: Username",
                    size="3",
                    on_change=UserManagementState.set_sort_value,
                ),
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    rx.input.slot(
                        rx.icon("x"),
                        justify="end",
                        cursor="pointer",
                        on_click=UserManagementState.setvar("search_value", ""),
                        display=rx.cond(
                            UserManagementState.search_value, "flex", "none"
                        ),
                    ),
                    value=UserManagementState.search_value,
                    placeholder="Search here...",
                    size="3",
                    max_width=["150px", "150px", "200px", "250px"],
                    width="100%",
                    variant="surface",
                    color_scheme="gray",
                    on_change=UserManagementState.set_search_value,
                ),
                flex_direction=["column", "column", "row"],
                align="center",
                justify="end",
                spacing="3",
                width="100%",
            ),
            direction="column",
            spacing="3",
            justify="between",
            wrap="wrap",
            width="100%",
            padding_bottom="1em",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _header_cell("Username", "user"),
                    _header_cell("Email", "mail"),
                    _header_cell("Role", "shield"),
                    _header_cell("Actions", "settings"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    UserManagementState.current_page,
                    lambda user, index: _show_user(user, index),
                )
            ),
            variant="surface",
            size="3",
            width="100%",
        ),
        _pagination_view(),
        width="100%",
        padding="16px",
    )
