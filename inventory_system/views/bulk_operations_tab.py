import reflex as rx

from inventory_system.pages.register import register_error
from inventory_system.state.auth import AuthState
from inventory_system.state.bulk_roles_state import BulkOperationsState
from inventory_system.state.register_state import CustomRegisterState
from inventory_system.state.role_state import RoleManagementState
from inventory_system.state.user_mgmt_state import UserManagementState


def _permission_count_badge(count: str, role: str) -> rx.Component:
    """Create a styled badge for individual roles with dynamic colors"""
    color_map_dict = UserManagementState.role_color_map

    return rx.badge(
        rx.text(count, size="2"),
        color_scheme=color_map_dict[role],
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


def _export_section() -> rx.Component:
    """Import/Export functionality section"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("download", size=20),
                rx.text("Import/Export", weight="bold"),
                align="center",
                spacing="2",
            ),
            rx.divider(),
            # Export section
            rx.vstack(
                rx.text("Export Data", weight="medium", size="2"),
                rx.hstack(
                    rx.button(
                        "Export Users",
                        source=rx.icon("users", size=16),
                        color_scheme="blue",
                        variant="outline",
                        size="2",
                        on_click=BulkOperationsState.export_users,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    rx.button(
                        rx.icon("shield", size=16),
                        "Export Roles",
                        color_scheme="blue",
                        variant="outline",
                        size="2",
                        on_click=BulkOperationsState.export_roles,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    rx.button(
                        rx.icon("key", size=16),
                        "Export Permissions",
                        color_scheme="blue",
                        variant="outline",
                        size="2",
                        on_click=BulkOperationsState.export_permissions,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    flex_direction=rx.breakpoints(initial="column", sm="row"),
                    spacing="2",
                    width="100%",
                    wrap="wrap",
                ),
                spacing="2",
                width="100%",
                align="start",
            ),
        ),
        padding="4",
        width="100%",
    )


def bulk_operations_tab() -> rx.Component:
    """Complete bulk operations tab with all functionality"""

    return rx.vstack(
        # Header with action buttons
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
        # Bulk User Operations
        rx.card(
            rx.vstack(
                rx.flex(
                    rx.icon("users", size=20),
                    rx.text("Bulk User Role Assignment", weight="bold", size="3"),
                    align="center",
                    spacing="2",
                ),
                rx.divider(),
                # User selection controls
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
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        rx.button(
                            "Deselect All",
                            variant="outline",
                            size="2",
                            on_click=BulkOperationsState.deselect_all_users,
                            width=rx.breakpoints(initial="100%", sm="auto"),
                        ),
                        rx.button(
                            "Assign Roles",
                            color_scheme="blue",
                            size="2",
                            on_click=BulkOperationsState.open_bulk_roles_modal,
                            disabled=BulkOperationsState.selected_user_count == 0,
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
                # Users table with selection
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
                            UserManagementState.current_page,
                            lambda user, index: rx.table.row(
                                rx.table.cell(
                                    _user_selection_checkbox(user, BulkOperationsState)
                                ),
                                rx.table.cell(user["username"]),
                                rx.table.cell(user["email"]),
                                rx.table.cell(_roles_display(user["roles"].to(list))),
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
                    variant="surface",
                    size="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            padding="4",
            width="100%",
        ),
        # Bulk Role Operations
        rx.cond(
            AuthState.permissions.contains("manage_roles"),
            rx.card(
                rx.vstack(
                    rx.flex(
                        rx.icon("shield", size=20),
                        rx.text(
                            "Bulk Role Permission Assignment", weight="bold", size="3"
                        ),
                        align="center",
                        spacing="2",
                    ),
                    rx.divider(),
                    # Role selection controls
                    rx.flex(
                        rx.text(
                            f"Selected: {BulkOperationsState.selected_role_count} roles",
                            size="2",
                        ),
                        rx.flex(
                            rx.button(
                                "Select All Roles",
                                variant="outline",
                                size="2",
                                on_click=BulkOperationsState.select_all_available_roles,
                                width=rx.breakpoints(initial="100%", sm="auto"),
                            ),
                            rx.button(
                                "Deselect All",
                                variant="outline",
                                size="2",
                                on_click=BulkOperationsState.deselect_all_roles,
                                width=rx.breakpoints(initial="100%", sm="auto"),
                            ),
                            rx.button(
                                "Assign Permissions",
                                color_scheme="orange",
                                size="2",
                                on_click=BulkOperationsState.open_bulk_permissions_modal,
                                disabled=BulkOperationsState.selected_role_count == 0,
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
                    # Roles table with selection
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Select"),
                                rx.table.column_header_cell("Role Name"),
                                rx.table.column_header_cell("Description"),
                                rx.table.column_header_cell("Permission Count"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                RoleManagementState.roles,
                                lambda role, index: rx.table.row(
                                    rx.table.cell(
                                        _role_selection_checkbox(
                                            role, BulkOperationsState
                                        )
                                    ),
                                    rx.table.cell(_role_badge(role["name"].to(str))),
                                    rx.table.cell(
                                        role["description"].to(str) | "No description"
                                    ),
                                    rx.table.cell(
                                        _permission_count_badge(
                                            f"{role['permissions'].to(list).length()}",
                                            role["name"].to(str),
                                        )
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
                        variant="surface",
                        size="3",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                padding="4",
                width="100%",
            ),
            None,
        ),
        # Import/Export section
        # _export_section(),
        # # Modals
        _bulk_role_assignment_modal(),
        _bulk_permission_assignment_modal(),
        spacing="4",
        width="100%",
        align="start",
        padding="16px",
    )
