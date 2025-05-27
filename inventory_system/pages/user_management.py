import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.auth import AuthState
from inventory_system.state.user_mgmt_state import UserManagementState
from inventory_system.templates.template import template
from inventory_system.views.permission_view import permissions_tab
from inventory_system.views.role_view import role_management_page


def _header_cell(text: str, icon: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )


def _role_badge(role: str) -> rx.Component:
    """Create a styled badge for individual roles with dynamic colors"""
    color_map_dict = UserManagementState.role_color_map

    return rx.badge(
        rx.text(role.capitalize(), size="2"),
        color_scheme=color_map_dict[role],
        variant="soft",
        size="1",
    )


def _roles_display(roles: rx.Var) -> rx.Component:
    """Display multiple roles as badges with proper wrapping"""
    return rx.flex(
        rx.foreach(
            roles,
            lambda role: _role_badge(role.to(str)),
        ),
        wrap="wrap",
        gap="1",
        align="center",
    )


def _role_selection_checkboxes() -> rx.Component:
    """Create checkboxes for role selection with improved layout"""
    return rx.vstack(
        rx.text("Select Roles:", weight="bold", size="2"),
        rx.grid(
            rx.foreach(
                UserManagementState.available_roles.to(list),
                lambda role: rx.flex(
                    rx.checkbox(
                        role.to(str).capitalize(),
                        checked=rx.cond(
                            UserManagementState.selected_roles.contains(role),
                            True,
                            False,
                        ),
                        on_change=lambda _: UserManagementState.toggle_role_selection(
                            role
                        ),
                        size="2",
                    ),
                    align="center",
                    min_width="120px",  # Ensure consistent spacing
                ),
            ),
            columns=rx.breakpoints(initial="1", sm="2", md="3"),
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
        align="start",
    )


def _edit_dialog(user: rx.Var) -> rx.Component:
    """Updated edit dialog with multiple role selection and improved mobile UI"""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.cond(
                AuthState.permissions.contains("edit_user"),
                rx.icon_button(
                    rx.icon("square-pen"),
                    on_click=lambda: UserManagementState.open_edit_dialog(
                        user["id"], user["roles"]
                    ),
                    color_scheme="blue",
                    size="2",
                    variant="solid",
                    # Remove supplier restriction since we now support multiple roles
                ),
                None,
            )
        ),
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Change User Roles"),
                rx.dialog.description(
                    f"Select roles for {user['username']}. Multiple roles can be assigned.",
                    size="2",
                ),
                # User info display - improved for mobile
                rx.desktop_only(
                    rx.inset(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Username"),
                                    rx.table.column_header_cell("Email"),
                                    rx.table.column_header_cell("Current Roles"),
                                ),
                            ),
                            rx.table.body(
                                rx.table.row(
                                    rx.table.row_header_cell(user["username"]),
                                    rx.table.cell(user["email"]),
                                    rx.table.cell(
                                        _roles_display(user["roles"].to(list))
                                    ),
                                ),
                            ),
                            width="100%",
                        ),
                        side="x",
                        margin_y="16px",
                    ),
                ),
                rx.mobile_and_tablet(
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Username:", weight="bold", size="2"),
                                rx.text(user["username"], size="2"),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            rx.hstack(
                                rx.text("Email:", weight="bold", size="2"),
                                rx.text(user["email"], size="2"),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            rx.vstack(
                                rx.text("Current Roles:", weight="bold", size="2"),
                                _roles_display(user["roles"].to(list)),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                            align="start",
                        ),
                        padding="3",
                        width="100%",
                    ),
                ),
                # Role selection section with improved layout
                rx.card(
                    _role_selection_checkboxes(),
                    padding="4",
                    width="100%",
                ),
                # Action buttons with improved mobile layout
                rx.flex(
                    rx.button(
                        "Update Roles",
                        color_scheme="blue",
                        size="3",
                        on_click=lambda: UserManagementState.change_user_roles(
                            user["id"], UserManagementState.selected_roles
                        ),
                        width=rx.breakpoints(initial="100%", sm="auto"),
                        disabled=UserManagementState.is_loading,
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                            width=rx.breakpoints(initial="100%", sm="auto"),
                            on_click=UserManagementState.cancel_edit_dialog,
                        )
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    spacing="3",
                    width="100%",
                    justify=rx.breakpoints(initial="center", sm="end"),
                ),
                spacing="4",
                width="100%",
                padding="16px",
            ),
            style={
                "max_width": rx.breakpoints(initial="95vw", md="600px"),
                "width": "100%",
                "max_height": "90vh",
                "overflow_y": "auto",
            },
        ),
        open=UserManagementState.show_edit_dialog
        & (UserManagementState.target_user_id == user["id"]),
    )


def _show_user(user: rx.Var, index: int) -> rx.Component:
    """Updated user row display with multiple roles support"""
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(
            _roles_display(user["roles"].to(list))
        ),  # Updated to show multiple roles
        rx.table.cell(
            rx.hstack(
                _edit_dialog(user),
                rx.cond(
                    AuthState.permissions.contains("delete_user"),
                    rx.icon_button(
                        rx.icon("trash-2"),
                        on_click=lambda: UserManagementState.confirm_delete_user(
                            user["id"]
                        ),
                        color_scheme="red",
                        size="2",
                        variant="solid",
                    ),
                    None,
                ),
                spacing="2",
                align="center",
            )
        ),
        # Improved delete confirmation dialog with better mobile layout
        rx.alert_dialog.root(
            rx.alert_dialog.content(
                rx.vstack(
                    rx.alert_dialog.title("Delete User"),
                    rx.alert_dialog.description(
                        f"Are you sure you want to delete user {user['username']}? "
                        "This action cannot be undone.",
                        size="2",
                    ),
                    rx.desktop_only(
                        rx.inset(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Username"),
                                        rx.table.column_header_cell("Email"),
                                        rx.table.column_header_cell("Roles"),
                                    ),
                                ),
                                rx.table.body(
                                    rx.table.row(
                                        rx.table.row_header_cell(user["username"]),
                                        rx.table.cell(user["email"]),
                                        rx.table.cell(
                                            _roles_display(user["roles"].to(list))
                                        ),
                                    ),
                                ),
                                width="100%",
                            ),
                            side="x",
                            margin_y="16px",
                        ),
                    ),
                    rx.mobile_and_tablet(
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Username:", weight="bold"),
                                    rx.text(user["username"]),
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                rx.hstack(
                                    rx.text("Email:", weight="bold"),
                                    rx.text(user["email"]),
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                rx.vstack(
                                    rx.text("Roles:", weight="bold"),
                                    _roles_display(user["roles"].to(list)),
                                    spacing="2",
                                    align="start",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                                align="start",
                            ),
                            padding="3",
                        ),
                    ),
                    # Improved button layout for mobile
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                                size="3",
                                on_click=UserManagementState.cancel_delete,
                                width=rx.breakpoints(initial="100%", sm="auto"),
                            )
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Delete",
                                color_scheme="red",
                                size="3",
                                on_click=UserManagementState.delete_user,
                                width=rx.breakpoints(initial="100%", sm="auto"),
                            )
                        ),
                        direction=rx.breakpoints(initial="column", sm="row"),
                        spacing="3",
                        width="100%",
                        justify=rx.breakpoints(initial="center", sm="end"),
                    ),
                    spacing="4",
                    width="100%",
                    padding="16px",
                ),
                style={
                    "max_width": rx.breakpoints(initial="95vw", md="500px"),
                    "width": "100%",
                },
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
            padding_bottom="1em",
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    "Profiles",
                    value="profiles",
                    size="3",
                    width="100px",
                ),
                rx.tabs.trigger(
                    "Roles",
                    value="roles",
                    size="3",
                    width="100px",
                ),
                rx.tabs.trigger(
                    "Permissions",
                    value="permissions",
                    size="3",
                    width="100px",
                ),
                justify="start",
                spacing="2",
                padding_bottom="1em",
            ),
            rx.tabs.content(
                rx.card(
                    # Enhanced search and filter section
                    rx.flex(
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
                                [
                                    "username",
                                    "email",
                                ],  # Removed "role" since we now have multiple roles
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
                                    on_click=UserManagementState.setvar(
                                        "search_value", ""
                                    ),
                                    display=rx.cond(
                                        UserManagementState.search_value, "flex", "none"
                                    ),
                                ),
                                value=UserManagementState.search_value,
                                placeholder="Search users, emails, or roles...",
                                size="3",
                                max_width=[
                                    "200px",
                                    "200px",
                                    "250px",
                                    "300px",
                                ],  # Increased for better mobile experience
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
                    # Enhanced table with better mobile support
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                _header_cell("Username", "user"),
                                _header_cell("Email", "mail"),
                                _header_cell("Roles", "shield"),  # Updated header text
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
                ),
                value="profiles",
            ),
            rx.tabs.content(
                role_management_page(),
                value="roles",
            ),
            rx.tabs.content(
                permissions_tab(),
                value="permissions",
            ),
            value=UserManagementState.active_tab,
            on_change=lambda val: UserManagementState.set_active_tab(val),
            width="100%",
            padding="16px",
        ),
        width="100%",
    )
