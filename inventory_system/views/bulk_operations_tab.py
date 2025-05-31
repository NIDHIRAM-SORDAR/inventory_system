import reflex as rx

from inventory_system import styles
from inventory_system.pages.register import register_error
from inventory_system.state.auth import AuthState
from inventory_system.state.bulk_roles_state import BulkOperationsState
from inventory_system.state.register_state import CustomRegisterState
from inventory_system.state.user_mgmt_state import UserManagementState


def _user_card(user: rx.Var) -> rx.Component:
    """Card representation for users on mobile"""
    return rx.card(
        rx.hstack(
            _user_selection_checkbox(user, BulkOperationsState),
            rx.vstack(
                rx.text(user["username"], weight="bold", size="3"),
                rx.text(user["email"], size="2"),
                _roles_display(user["roles"].to(list)),
                spacing="2",
            ),
            spacing="3",
            align="center",
        ),
        width="100%",
        padding="12px",
        variant="surface",
        style=styles.card_transition_style,
    )


# Added _role_card function for mobile layout
def _role_card(role: rx.Var) -> rx.Component:
    """Compact card with status in header"""
    return rx.card(
        rx.vstack(
            # Header with name and status
            rx.hstack(
                _role_selection_checkbox(role, BulkOperationsState),
                rx.hstack(
                    _role_badge(role["name"].to(str)),
                    _role_status_badge(role["is_active"]),
                    spacing="2",
                    align="center",
                    flex="1",
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # Content
            rx.vstack(
                rx.text(
                    role["description"] | "No description",
                    size="2",
                    color=rx.cond(role["is_active"], "inherit", rx.color("gray", 10)),
                ),
                # Improved permission count display with context
                rx.hstack(
                    rx.icon("key", size=14),
                    rx.text(
                        f"{role['permissions'].to(list).length()} permissions", size="2"
                    ),
                    _permission_count_badge(
                        f"{role['permissions'].to(list).length()}", role["name"].to(str)
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                align_items="start",
                width="100%",
                padding_left="32px",  # Align with content below checkbox
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        padding="12px",
        variant="surface",
        style={
            **styles.card_transition_style,  # Added transition styles
            "opacity": rx.cond(role["is_active"], "1", "0.7"),
        },
    )


# Added pagination view for users
def _user_pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text(
            "Page ",
            rx.code(BulkOperationsState.user_page_number),
            f" of {BulkOperationsState.users_total_pages}",
            justify="end",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevrons-left", size=18),
                on_click=BulkOperationsState.user_first_page,
                opacity=rx.cond(BulkOperationsState.user_page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    BulkOperationsState.user_page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=18),
                on_click=BulkOperationsState.user_prev_page,
                opacity=rx.cond(BulkOperationsState.user_page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    BulkOperationsState.user_page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=18),
                on_click=BulkOperationsState.user_next_page,
                opacity=rx.cond(
                    BulkOperationsState.user_page_number
                    == BulkOperationsState.users_total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    BulkOperationsState.user_page_number
                    == BulkOperationsState.users_total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevrons-right", size=18),
                on_click=BulkOperationsState.user_last_page,
                opacity=rx.cond(
                    BulkOperationsState.user_page_number
                    == BulkOperationsState.users_total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    BulkOperationsState.user_page_number
                    == BulkOperationsState.users_total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            align="center",
            spacing="2",
        ),
        spacing="5",
        margin_top="1em",
        align="center",
        width="100%",
        justify="end",
    )


# Added pagination view for roles
def _role_pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text(
            "Page ",
            rx.code(BulkOperationsState.role_page_number),
            f" of {BulkOperationsState.roles_total_pages}",
            justify="end",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevrons-left", size=18),
                on_click=BulkOperationsState.role_first_page,
                opacity=rx.cond(BulkOperationsState.role_page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    BulkOperationsState.role_page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=18),
                on_click=BulkOperationsState.role_prev_page,
                opacity=rx.cond(BulkOperationsState.role_page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    BulkOperationsState.role_page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=18),
                on_click=BulkOperationsState.role_next_page,
                opacity=rx.cond(
                    BulkOperationsState.role_page_number
                    == BulkOperationsState.roles_total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    BulkOperationsState.role_page_number
                    == BulkOperationsState.roles_total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevrons-right", size=18),
                on_click=BulkOperationsState.role_last_page,
                opacity=rx.cond(
                    BulkOperationsState.role_page_number
                    == BulkOperationsState.roles_total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    BulkOperationsState.role_page_number
                    == BulkOperationsState.roles_total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            align="center",
            spacing="2",
        ),
        spacing="5",
        margin_top="1em",
        align="center",
        width="100%",
        justify="end",
    )


def _permission_count_badge(count: str, role: str) -> rx.Component:
    """Create a styled badge for individual roles with dynamic colors"""
    color_map_dict = UserManagementState.role_color_map

    return rx.badge(
        rx.text(count, size="2"),
        color_scheme=color_map_dict[role],
        variant="soft",
        size="1",
    )


def _role_status_badge(is_active: rx.Var) -> rx.Component:
    """Status badge showing active/inactive state"""
    return rx.badge(
        rx.cond(
            is_active,
            rx.hstack(
                rx.icon("circle-check", size=12),
                "Active",
                spacing="1",
                align="center",
            ),
            rx.hstack(
                rx.icon("ban", size=12),
                "Inactive",
                spacing="1",
                align="center",
            ),
        ),
        color_scheme=rx.cond(is_active, "green", "red"),
        variant="soft",
        size="1",
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


def _user_selection_checkbox(
    user: rx.Var, bulk_state: BulkOperationsState
) -> rx.Component:
    """Checkbox for selecting users in bulk operations"""
    return rx.checkbox(
        checked=bulk_state.selected_user_ids.contains(user["id"]),
        on_change=lambda _: bulk_state.toggle_user_selection(user["id"]),
        size="2",
    )


def _role_selection_checkbox(
    role: rx.Var, bulk_state: BulkOperationsState
) -> rx.Component:
    """Checkbox for selecting roles in bulk operations"""
    return rx.checkbox(
        checked=bulk_state.selected_role_ids.contains(role["id"]),
        on_change=lambda _: bulk_state.toggle_role_selection(role["id"]),
        size="2",
    )


# Fix 2: Update the _collapsible_section function
def _collapsible_section(
    title: str,
    icon: str,
    content: rx.Component,
    is_open_var: rx.Var,
    toggle_func: callable,
    color_scheme: str = "blue",
) -> rx.Component:
    """Reusable collapsible section component with full width support"""
    return rx.card(  # Changed from rx.card to rx.box
        rx.inset(
            rx.vstack(
                # Header with toggle functionality
                rx.hstack(
                    rx.icon(icon, size=20),
                    rx.text(title, weight="bold", size="3"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.cond(
                            is_open_var,
                            rx.icon("chevron-up", size=18),
                            rx.icon("chevron-down", size=18),
                        ),
                        variant="ghost",
                        size="2",
                        on_click=toggle_func,
                    ),
                    align="center",
                    width="100%",
                    cursor="pointer",
                ),
                # Collapsible content
                rx.cond(
                    is_open_var,
                    rx.vstack(
                        rx.divider(),
                        rx.box(
                            content,
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                        align="start",
                    ),
                    None,
                ),
                spacing="3",  # Increased spacing
                width="100%",
                align="start",
            ),
            side="x",
            width="100%",
        ),
        width="100%",
        border="1px solid",
        border_color=rx.color("gray", 6),
        border_radius="8px",
        padding="16px",
        background_color=rx.color("gray", 1),
        style=styles.card_transition_style,
    )


# 5. Updated mobile user controls with better alignment
def _mobile_user_controls() -> rx.Component:
    """Mobile-optimized user controls with proper alignment"""
    return rx.vstack(
        # Selection info and main actions
        rx.hstack(
            rx.text(
                f"Selected: {BulkOperationsState.selected_user_count} users",
                size="2",
                weight="medium",
            ),
            rx.spacer(),
            justify="start",
            align="center",
            width="100%",
        ),
        # Action buttons - properly spaced
        rx.vstack(
            rx.button(
                "Select All Visible",
                variant="outline",
                size="2",
                on_click=BulkOperationsState.select_all_visible_users,
                width="100%",
            ),
            rx.button(
                "Deselect All",
                variant="outline",
                size="2",
                on_click=BulkOperationsState.deselect_all_users,
                width="100%",
            ),
            rx.button(
                "Assign Roles",
                color_scheme="blue",
                size="2",
                on_click=BulkOperationsState.open_bulk_roles_modal,
                disabled=BulkOperationsState.selected_user_count == 0,
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        # Search input with proper placeholder handling
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            rx.input.slot(
                rx.icon("x", size=16),
                justify="end",
                cursor="pointer",
                on_click=BulkOperationsState.setvar("user_search_value", ""),
                display=rx.cond(
                    BulkOperationsState.user_search_value,
                    "flex",
                    "none",
                ),
            ),
            value=BulkOperationsState.user_search_value,
            placeholder="Search users...",  # Shortened placeholder for mobile
            size="2",
            width="100%",
            variant="surface",
            color_scheme="gray",
            on_change=BulkOperationsState.set_user_search_value,
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


# 6. Updated mobile role controls with better alignment
def _mobile_role_controls() -> rx.Component:
    """Mobile-optimized role controls with proper alignment"""
    return rx.vstack(
        # Selection info and main actions
        rx.hstack(
            rx.text(
                f"Selected: {BulkOperationsState.selected_role_count} roles",
                size="2",
                weight="medium",
            ),
            rx.spacer(),
            justify="start",
            align="center",
            width="100%",
        ),
        # Action buttons - properly spaced
        rx.vstack(
            rx.button(
                "Select All Visible",
                variant="outline",
                size="2",
                on_click=BulkOperationsState.select_all_visible_roles,
                width="100%",
            ),
            rx.button(
                "Deselect All",
                variant="outline",
                size="2",
                on_click=BulkOperationsState.deselect_all_roles,
                width="100%",
            ),
            rx.button(
                "Assign Permissions",
                color_scheme="orange",
                size="2",
                on_click=BulkOperationsState.open_bulk_permissions_modal,
                disabled=BulkOperationsState.selected_role_count == 0,
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        # Search input with proper placeholder handling
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            rx.input.slot(
                rx.icon("x", size=16),
                justify="end",
                cursor="pointer",
                on_click=BulkOperationsState.setvar("role_search_value", ""),
                display=rx.cond(
                    BulkOperationsState.role_search_value,
                    "flex",
                    "none",
                ),
            ),
            value=BulkOperationsState.role_search_value,
            placeholder="Search roles...",  # Shortened placeholder for mobile
            size="2",
            width="100%",
            variant="surface",
            color_scheme="gray",
            on_change=BulkOperationsState.set_role_search_value,
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


def _bulk_role_assignment_modal() -> rx.Component:
    """Modal for bulk role assignment to users"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Assign Roles to Selected Users"),
                rx.dialog.description(
                    f"You are about to modify roles for {BulkOperationsState.selected_user_count} user(s)",
                    size="2",
                ),
                # Operation type selection
                rx.card(
                    rx.vstack(
                        rx.text("Operation Type:", weight="bold", size="2"),
                        rx.radio.root(
                            rx.flex(
                                rx.radio.item(value="replace"),
                                rx.vstack(
                                    rx.text("Replace", weight="bold"),
                                    rx.text(
                                        "Replace all existing roles",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            rx.flex(
                                rx.radio.item(value="add"),
                                rx.vstack(
                                    rx.text("Add", weight="bold"),
                                    rx.text(
                                        "Add to existing roles",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            rx.flex(
                                rx.radio.item(value="remove"),
                                rx.vstack(
                                    rx.text("Remove", weight="bold"),
                                    rx.text(
                                        "Remove selected roles",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            value=BulkOperationsState.bulk_operation_type,
                            on_change=BulkOperationsState.set_bulk_operation_type,
                            direction=rx.breakpoints(initial="column", sm="row"),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    padding="3",
                ),
                # Role selection
                rx.card(
                    rx.vstack(
                        rx.text("Select Roles:", weight="bold", size="2"),
                        rx.grid(
                            rx.foreach(
                                BulkOperationsState.available_roles_for_bulk,
                                lambda role: rx.checkbox(
                                    role.capitalize(),
                                    checked=BulkOperationsState.bulk_selected_roles.contains(
                                        role
                                    ),
                                    on_change=lambda _: BulkOperationsState.toggle_bulk_role(
                                        role
                                    ),
                                    size="2",
                                ),
                            ),
                            columns=rx.breakpoints(initial="1", sm="2", md="3"),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    padding="3",
                ),
                # Action buttons
                rx.flex(
                    rx.button(
                        "Apply Changes",
                        color_scheme="blue",
                        size="3",
                        on_click=BulkOperationsState.execute_bulk_role_assignment,
                        loading=BulkOperationsState.bulk_is_loading,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                            on_click=BulkOperationsState.close_bulk_roles_modal,
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
                "max_width": rx.breakpoints(initial="95vw", md="600px"),
                "width": "100%",
                "max_height": "90vh",
                "overflow_y": "auto",
            },
        ),
        open=BulkOperationsState.show_bulk_roles_modal,
    )


def _bulk_permission_assignment_modal() -> rx.Component:
    """Modal for bulk permission assignment to roles"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Assign Permissions to Selected Roles"),
                rx.dialog.description(
                    f"You are about to modify permissions for {BulkOperationsState.selected_role_count} role(s)",
                    size="2",
                ),
                # Operation type selection
                rx.card(
                    rx.vstack(
                        rx.text("Operation Type:", weight="bold", size="2"),
                        rx.radio.root(
                            rx.flex(
                                rx.radio.item(value="replace"),
                                rx.vstack(
                                    rx.text("Replace", weight="bold"),
                                    rx.text(
                                        "Replace all existing permissions",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            rx.flex(
                                rx.radio.item(value="add"),
                                rx.vstack(
                                    rx.text("Add", weight="bold"),
                                    rx.text(
                                        "Add to existing permissions",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            rx.flex(
                                rx.radio.item(value="remove"),
                                rx.vstack(
                                    rx.text("Remove", weight="bold"),
                                    rx.text(
                                        "Remove selected permissions",
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                direction="row",
                                align="center",
                                spacing="2",
                                width="100%",
                            ),
                            value=BulkOperationsState.bulk_role_operation_type,
                            on_change=BulkOperationsState.set_bulk_role_operation_type,
                            direction=rx.breakpoints(initial="column", sm="row"),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    padding="3",
                ),
                # Permission selection by category
                rx.card(
                    rx.vstack(
                        rx.text("Select Permissions:", weight="bold", size="2"),
                        rx.foreach(
                            BulkOperationsState.grouped_permissions_for_bulk,
                            lambda category_perms: rx.vstack(
                                rx.text(
                                    category_perms.category,
                                    weight="bold",
                                    size="2",
                                    color="blue",
                                ),
                                rx.grid(
                                    rx.foreach(
                                        category_perms.permissions,
                                        lambda perm: rx.tooltip(
                                            rx.checkbox(
                                                perm.name.replace("_", " ").title(),
                                                checked=BulkOperationsState.bulk_selected_permissions.contains(
                                                    perm.name
                                                ),
                                                on_change=lambda _: BulkOperationsState.toggle_bulk_permission(
                                                    perm.name
                                                ),
                                                size="2",
                                            ),
                                            content=perm.description,
                                        ),
                                    ),
                                    columns=rx.breakpoints(initial="1", sm="2"),
                                    spacing="2",
                                    width="100%",
                                ),
                                spacing="2",
                                width="100%",
                                align="start",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                        max_height="400px",
                        overflow_y="auto",
                    ),
                    padding="3",
                ),
                # Action buttons
                rx.flex(
                    rx.button(
                        "Apply Changes",
                        color_scheme="blue",
                        size="3",
                        on_click=BulkOperationsState.execute_bulk_permission_assignment,
                        loading=BulkOperationsState.bulk_role_is_loading,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                            on_click=BulkOperationsState.close_bulk_permissions_modal,
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
                "max_width": rx.breakpoints(initial="95vw", md="700px"),
                "width": "100%",
                "max_height": "90vh",
                "overflow_y": "auto",
            },
        ),
        open=BulkOperationsState.show_bulk_permissions_modal,
    )


def _user_creation_modal() -> rx.Component:
    """Modal for creating new users"""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("user-plus", size=18),
                "Create User",
                color_scheme="green",
                size="3",
                width=rx.breakpoints(initial="100%", sm="auto"),
            )
        ),
        rx.dialog.content(
            rx.form(
                rx.vstack(
                    rx.dialog.title("Create New User"),
                    rx.dialog.description(
                        "Fill in the user details",
                        size="2",
                    ),
                    register_error(),
                    rx.card(
                        rx.vstack(
                            rx.flex(
                                rx.vstack(
                                    rx.text("Username", weight="medium"),
                                    rx.input(
                                        placeholder="Enter username",
                                        name="username",
                                        required=True,
                                        size="2",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                rx.vstack(
                                    rx.text("Email", weight="medium"),
                                    rx.input(
                                        placeholder="Enter email address",
                                        name="email",
                                        type="email",
                                        required=True,
                                        size="2",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                direction=rx.breakpoints(initial="column", sm="row"),
                                spacing="3",
                                width="100%",
                            ),
                            rx.flex(
                                rx.vstack(
                                    rx.text("Password", weight="medium", size="2"),
                                    rx.input(
                                        placeholder="Enter password",
                                        name="password",
                                        type="password",
                                        required=True,
                                        size="2",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Confirm Password", weight="bold", size="2"
                                    ),
                                    rx.input(
                                        placeholder="Confirm password",
                                        name="confirm_password",
                                        type="password",
                                        required=True,
                                        size="2",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                direction=rx.breakpoints(initial="column", sm="row"),
                                spacing="3",
                                width="100%",
                            ),
                            spacing="3",
                        ),
                        padding="3",
                        width="100%",
                    ),
                    # Role assignment
                    rx.card(
                        rx.vstack(
                            rx.text("Assign Roles:", weight="bold", size="2"),
                            rx.grid(
                                rx.foreach(
                                    BulkOperationsState.available_roles_for_bulk,
                                    lambda role: rx.checkbox(
                                        role.capitalize(),
                                        name=f"role_{role}",
                                        size="2",
                                    ),
                                ),
                                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                                spacing="3",
                                width="100%",
                            ),
                            spacing="3",
                            width_auto="100%",
                        ),
                        padding="3",
                    ),
                    # Action buttons
                    rx.flex(
                        rx.button(
                            "Create User",
                            type="submit",
                            color_scheme="green",
                            size="3",
                            loading=CustomRegisterState.is_submitting,
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                                size="3",
                                width=rx.breakpoints(initial="100%", sm="auto"),
                            ),
                        ),
                        direction=rx.breakpoints(initial="column", sm="row"),
                        spacing="3",
                        width="100%",
                        justify=rx.breakpoints(initial="center", sm="end"),
                    ),
                    spacingEmily="4",
                    width="100%",
                    padding="16px",
                ),
                on_submit=CustomRegisterState.create_new_user,
            ),
            style={
                "max_width": rx.breakpoints(initial="95vw", md="600px"),
                "width": "100%",
                "max_height": "90vh",
                "overflow_y": "auto",
            },
        ),
    )


def bulk_operations_tab() -> rx.Component:
    """Complete bulk operations tab with enhanced functionality and collapsible sections"""
    return rx.container(
        rx.vstack(
            # Header section unchanged
            rx.flex(
                rx.flex(
                    rx.icon("layers", size=20),
                    rx.text("Bulk Operations", weight="bold", size="4"),
                    align="center",
                    spacing="2",
                ),
                rx.flex(
                    _user_creation_modal(),
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        "Refresh",
                        color_scheme="gray",
                        variant="outline",
                        size="2",
                        on_click=UserManagementState.check_auth_and_load,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    spacing="2",
                    width=rx.breakpoints(initial="100%", sm="auto"),
                ),
                justify="between",
                align=rx.breakpoints(initial="start", sm="center"),
                direction=rx.breakpoints(initial="column", sm="row"),
                spacing="3",
                width="100%",
                wrap="wrap",
            ),
            # Collapsible Bulk User Operations Section
            _collapsible_section(
                title="Bulk User Role Assignment",
                icon="users",
                content=rx.fragment(
                    # Desktop layout with full-width table
                    rx.desktop_only(
                        rx.vstack(
                            rx.flex(
                                rx.text(
                                    f"Selected: {BulkOperationsState.selected_user_count} users",
                                    size="2",
                                ),
                                rx.flex(
                                    rx.button(
                                        "Select All Page",
                                        variant="outline",
                                        size="2",
                                        on_click=BulkOperationsState.select_all_current_page_users,
                                    ),
                                    rx.button(
                                        "Deselect All",
                                        variant="outline",
                                        size="2",
                                        on_click=BulkOperationsState.deselect_all_users,
                                    ),
                                    rx.button(
                                        "Assign Roles",
                                        color_scheme="blue",
                                        size="2",
                                        on_click=BulkOperationsState.open_bulk_roles_modal,
                                        disabled=BulkOperationsState.selected_user_count
                                        == 0,
                                    ),
                                    spacing="2",
                                ),
                                justify="between",
                                width="100%",
                            ),
                            # Search and sort controls for desktop
                            rx.flex(
                                rx.cond(
                                    BulkOperationsState.user_sort_reverse,
                                    rx.icon(
                                        "arrow-down-z-a",
                                        size=28,
                                        stroke_width=1.5,
                                        cursor="pointer",
                                        on_click=BulkOperationsState.toggle_user_sort,
                                    ),
                                    rx.icon(
                                        "arrow-down-a-z",
                                        size=28,
                                        stroke_width=1.5,
                                        cursor="pointer",
                                        on_click=BulkOperationsState.toggle_user_sort,
                                    ),
                                ),
                                rx.select(
                                    ["username", "email"],
                                    placeholder="Sort By: Username",
                                    size="3",
                                    on_change=BulkOperationsState.set_user_sort_value,
                                ),
                                rx.input(
                                    rx.input.slot(rx.icon("search")),
                                    rx.input.slot(
                                        rx.icon("x"),
                                        justify="end",
                                        cursor="pointer",
                                        on_click=BulkOperationsState.setvar(
                                            "user_search_value", ""
                                        ),
                                        display=rx.cond(
                                            BulkOperationsState.user_search_value,
                                            "flex",
                                            "none",
                                        ),
                                    ),
                                    value=BulkOperationsState.user_search_value,
                                    placeholder="Search users, emails, or roles...",
                                    size="3",
                                    max_width=["200px", "200px", "250px", "300px"],
                                    width="100%",
                                    variant="surface",
                                    color_scheme="gray",
                                    on_change=BulkOperationsState.set_user_search_value,
                                ),
                                flex_direction=["column", "column", "row"],
                                align="center",
                                justify="end",
                                spacing="3",
                                width="100%",
                            ),
                            # Full-width table container
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Select"),
                                        rx.table.column_header_cell("Username"),
                                        rx.table.column_header_cell("Email"),
                                        rx.table.column_header_cell("Current Roles"),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        BulkOperationsState.current_users_page,
                                        lambda user, index: rx.table.row(
                                            rx.table.cell(
                                                _user_selection_checkbox(
                                                    user, BulkOperationsState
                                                )
                                            ),
                                            rx.table.cell(user["username"]),
                                            rx.table.cell(user["email"]),
                                            rx.table.cell(
                                                _roles_display(user["roles"].to(list))
                                            ),
                                            style={
                                                "_hover": {"bg": rx.color("accent", 2)},
                                                "bg": rx.cond(
                                                    index % 2 == 0,
                                                    rx.color("gray", 1),
                                                    "transparent",
                                                ),
                                            },
                                        ),
                                    )
                                ),
                                width="100%",  # Ensure full width
                            ),
                            _user_pagination_view(),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    # Mobile layout with improved controls
                    rx.mobile_and_tablet(
                        rx.container(
                            rx.vstack(
                                _mobile_user_controls(),  # Use new mobile controls
                                rx.foreach(
                                    BulkOperationsState.mobile_displayed_users,
                                    lambda user: _user_card(user),
                                ),
                                rx.cond(
                                    BulkOperationsState.has_more_users,
                                    rx.button(
                                        "Load More",
                                        on_click=BulkOperationsState.load_more_users,
                                        size="3",
                                        width="100%",
                                        color_scheme="blue",
                                    ),
                                ),
                                spacing="4",
                                width="100%",
                                align="center",
                            ),
                            max_width="600px",
                            width="100%",
                            padding_x="16px",
                            padding_y="16px",
                            margin="0 auto",
                        ),
                    ),
                ),
                is_open_var=BulkOperationsState.user_section_open,
                toggle_func=BulkOperationsState.toggle_user_section,
                color_scheme="blue",
            ),
            # Collapsible Bulk Role Operations Section (only if user has manage_roles permission)
            rx.cond(
                AuthState.permissions.contains("manage_roles"),
                _collapsible_section(
                    title="Bulk Role Permission Assignment",
                    icon="shield",
                    content=rx.fragment(
                        # Desktop layout with full-width table
                        rx.desktop_only(
                            rx.vstack(
                                rx.flex(
                                    rx.text(
                                        f"Selected: {BulkOperationsState.selected_role_count} roles",
                                        size="2",
                                    ),
                                    rx.flex(
                                        rx.button(
                                            "Select All Page",
                                            variant="outline",
                                            size="2",
                                            on_click=BulkOperationsState.select_all_available_roles,
                                        ),
                                        rx.button(
                                            "Deselect All",
                                            variant="outline",
                                            size="2",
                                            on_click=BulkOperationsState.deselect_all_roles,
                                        ),
                                        rx.button(
                                            "Assign Permissions",
                                            color_scheme="orange",
                                            size="2",
                                            on_click=BulkOperationsState.open_bulk_permissions_modal,
                                            disabled=BulkOperationsState.selected_role_count
                                            == 0,
                                        ),
                                        spacing="2",
                                    ),
                                    justify="between",
                                    width="100%",
                                ),
                                # Search and sort controls for desktop
                                rx.flex(
                                    rx.cond(
                                        BulkOperationsState.role_sort_reverse,
                                        rx.icon(
                                            "arrow-down-z-a",
                                            size=28,
                                            stroke_width=1.5,
                                            cursor="pointer",
                                            on_click=BulkOperationsState.toggle_role_sort,
                                        ),
                                        rx.icon(
                                            "arrow-down-a-z",
                                            size=28,
                                            stroke_width=1.5,
                                            cursor="pointer",
                                            on_click=BulkOperationsState.toggle_role_sort,
                                        ),
                                    ),
                                    rx.select(
                                        ["name", "description"],
                                        placeholder="Sort By: Name",
                                        size="3",
                                        on_change=BulkOperationsState.set_role_sort_value,
                                    ),
                                    rx.input(
                                        rx.input.slot(rx.icon("search")),
                                        rx.input.slot(
                                            rx.icon("x"),
                                            justify="end",
                                            cursor="pointer",
                                            on_click=BulkOperationsState.setvar(
                                                "role_search_value", ""
                                            ),
                                            display=rx.cond(
                                                BulkOperationsState.role_search_value,
                                                "flex",
                                                "none",
                                            ),
                                        ),
                                        value=BulkOperationsState.role_search_value,
                                        placeholder="Search roles...",
                                        size="3",
                                        max_width=["200px", "200px", "250px", "300px"],
                                        width="100%",
                                        variant="surface",
                                        color_scheme="gray",
                                        on_change=BulkOperationsState.set_role_search_value,
                                    ),
                                    flex_direction=["column", "column", "row"],
                                    align="center",
                                    justify="end",
                                    spacing="3",
                                    width="100%",
                                ),
                                # Full-width table container
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("Select"),
                                            rx.table.column_header_cell("Role Name"),
                                            rx.table.column_header_cell("Status"),
                                            rx.table.column_header_cell("Description"),
                                            rx.table.column_header_cell("Permissions"),
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            BulkOperationsState.current_roles_page,
                                            lambda role, index: rx.table.row(
                                                rx.table.cell(
                                                    _role_selection_checkbox(
                                                        role, BulkOperationsState
                                                    )
                                                ),
                                                rx.table.cell(
                                                    _role_badge(role["name"].to(str))
                                                ),
                                                rx.table.cell(
                                                    _role_status_badge(
                                                        role["is_active"]
                                                    )
                                                ),
                                                rx.table.cell(
                                                    role["description"].to(str)
                                                    | "No description"
                                                ),
                                                rx.table.cell(
                                                    rx.hstack(
                                                        rx.icon("key", size=14),
                                                        rx.text(
                                                            f"{role['permissions'].to(list).length()}",
                                                            size="2",
                                                        ),
                                                        _permission_count_badge(
                                                            f"{role['permissions'].to(list).length()}",
                                                            role["name"].to(str),
                                                        ),
                                                        spacing="2",
                                                        align="center",
                                                    )
                                                ),
                                                style={
                                                    "_hover": {
                                                        "bg": rx.color("accent", 2)
                                                    },
                                                    "bg": rx.cond(
                                                        index % 2 == 0,
                                                        rx.color("gray", 1),
                                                        "transparent",
                                                    ),
                                                    "opacity": rx.cond(
                                                        role["is_active"], "1", "0.7"
                                                    ),
                                                },
                                            ),
                                        )
                                    ),
                                    variant="surface",
                                    size="3",
                                    width="100%",  # Ensure full width
                                ),
                                _role_pagination_view(),
                                spacing="3",
                                width="100%",
                            ),
                        ),
                        # Mobile layout with improved controls
                        rx.mobile_and_tablet(
                            rx.container(
                                rx.vstack(
                                    _mobile_role_controls(),  # Use new mobile controls
                                    rx.foreach(
                                        BulkOperationsState.mobile_displayed_roles,
                                        lambda role: _role_card(role),
                                    ),
                                    rx.cond(
                                        BulkOperationsState.has_more_roles,
                                        rx.button(
                                            "Load More",
                                            on_click=BulkOperationsState.load_more_roles,
                                            size="3",
                                            width="100%",
                                            color_scheme="orange",
                                        ),
                                    ),
                                    spacing="4",
                                    width="100%",
                                    align="center",
                                ),
                                max_width="600px",
                                width="100%",
                                padding_x="16px",
                                padding_y="16px",
                                margin="0 auto",
                            ),
                        ),
                    ),
                    is_open_var=BulkOperationsState.role_section_open,
                    toggle_func=BulkOperationsState.toggle_role_section,
                    color_scheme="orange",
                ),
                None,
            ),
            # Collapsible Import/Export Section
            _collapsible_section(
                title="Import/Export",
                icon="download",
                content=rx.fragment(
                    rx.text("Export Data", weight="medium", size="2"),
                    rx.hstack(
                        rx.button(
                            rx.icon("users", size=16),
                            "Export Users",
                            color_scheme="blue",
                            variant="outline",
                            size="2",
                            on_click=lambda: BulkOperationsState.export_users,
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        rx.button(
                            rx.icon("shield", size=16),
                            "Export Roles",
                            color_scheme="blue",
                            variant="outline",
                            size="2",
                            on_click=lambda: BulkOperationsState.export_roles,
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        rx.button(
                            rx.icon("key", size=16),
                            "Export Permissions",
                            color_scheme="blue",
                            variant="outline",
                            size="2",
                            on_click=lambda: BulkOperationsState.export_permissions,
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        flex_direction=rx.breakpoints(initial="column", sm="row"),
                        spacing="2",
                        width="100%",
                        wrap="wrap",
                    ),
                ),
                is_open_var=BulkOperationsState.export_section_open,
                toggle_func=BulkOperationsState.toggle_export_section,
                color_scheme="green",
            ),
            # Modals remain unchanged
            _bulk_role_assignment_modal(),
            _bulk_permission_assignment_modal(),
            spacing="4",
            width="100%",
            align="start",
        ),
        size="4",  # Use largest container size
        width="100%",  # Explicit full width
        max_width="100%",  # Ensure no max-width constraints
        padding_x="0",  # Remove side padding that might constrain width
        on_mount=BulkOperationsState.on_mount,
    )
