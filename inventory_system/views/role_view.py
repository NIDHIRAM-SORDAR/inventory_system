import reflex as rx

from inventory_system.state.role_state import RoleManagementState


def permission_item(perm) -> rx.Component:
    """Single permission item component."""
    return rx.hstack(
        rx.checkbox(
            checked=RoleManagementState.selected_permissions.contains(perm["name"]),
            on_change=lambda checked,
            p=perm["name"]: RoleManagementState.toggle_permission(p),
            size="2",
        ),
        rx.vstack(
            rx.text(perm["name"], font_weight="500", font_size="14px"),
            rx.text(
                perm["description"],
                font_size="12px",
                color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
            ),
            align_items="start",
            spacing="1",  # CHANGED: Reduced spacing for better compactness
        ),
        align_items="start",
        spacing="3",  # CHANGED: Reduced spacing
        width="100%",
        padding="10px",  # CHANGED: Reduced padding
        border_radius="6px",  # CHANGED: Slightly smaller radius
        _hover={"bg": rx.color("gray", 2)},  # CHANGED: Dark mode compatible
        border="1px solid",
        border_color=rx.color("gray", 6),  # CHANGED: Dark mode compatible
    )


def permissions_modal() -> rx.Component:
    """Modal for managing role permissions."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Manage Permissions", font_weight="600"),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            size="1",
                            on_click=RoleManagementState.close_role_modals,
                        )
                    ),
                    width="100%",
                    align_items="center",
                ),
                margin_bottom="16px",
            ),
            # ADDED: Select/Deselect all controls
            rx.hstack(
                rx.text(
                    f"Selected: {RoleManagementState.selected_permissions.length()} permissions",
                    font_size="14px",
                    color=rx.color("gray", 10),
                ),
                rx.spacer(),
                rx.button(
                    "Select All",
                    variant="soft",
                    size="1",
                    on_click=RoleManagementState.select_all_permissions,
                ),
                rx.button(
                    "Deselect All",
                    variant="soft",
                    size="1",
                    on_click=RoleManagementState.deselect_all_permissions,
                ),
                width="100%",
                align_items="center",
                margin_bottom="12px",
                padding_x="4px",
            ),
            rx.box(
                rx.cond(
                    RoleManagementState.permissions_loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="40px",
                    ),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                RoleManagementState.available_permissions,
                                permission_item,
                            ),
                            spacing="2",  # CHANGED: Reduced spacing
                            padding_right="8px",  # ADDED: Padding to prevent scroll overlap
                        ),
                        height="350px",  # CHANGED: Slightly reduced height
                        scrollbars="vertical",
                    ),
                ),
                margin_bottom="20px",
            ),
            rx.hstack(
                rx.button(
                    "Cancel",
                    variant="outline",
                    on_click=RoleManagementState.close_role_modals,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                rx.button(
                    "Save Changes",
                    on_click=RoleManagementState.update_role_permissions,
                    loading=RoleManagementState.permissions_loading,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                spacing="3",
                width="100%",
            ),
            max_width="550px",  # CHANGED: Slightly wider
            width="90vw",
            max_height="80vh",
        ),
        open=RoleManagementState.role_show_permissions_modal,
    )


def role_form_modal(is_edit: bool = False) -> rx.Component:
    """Modal for creating/editing roles."""
    title = rx.cond(is_edit, "Edit Role", "Create New Role")
    button_text = rx.cond(is_edit, "Update Role", "Create Role")

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    title,
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            size="1",
                            on_click=RoleManagementState.close_role_modals,
                        )
                    ),
                    width="100%",
                    align_items="center",
                ),
                margin_bottom="20px",
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Role Name *", font_weight="500", font_size="14px"),
                    rx.input(
                        placeholder="Enter role name",
                        value=RoleManagementState.role_form_name,
                        on_change=RoleManagementState.set_role_form_name,
                        width="100%",
                    ),
                    spacing="4",
                    align_items="start",
                ),
                rx.vstack(
                    rx.text("Description", font_weight="500", font_size="14px"),
                    rx.text_area(
                        placeholder="Enter role description (optional)",
                        value=RoleManagementState.role_form_description,
                        on_change=RoleManagementState.set_role_form_description,
                        width="100%",
                        resize="vertical",
                        min_height="80px",
                    ),
                    spacing="4",
                    align_items="start",
                ),
                spacing="6",  # CHANGED: Reduced spacing
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    "Cancel",
                    variant="outline",
                    on_click=RoleManagementState.close_role_modals,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                rx.button(
                    button_text,
                    on_click=rx.cond(
                        is_edit,
                        RoleManagementState.update_role,
                        RoleManagementState.add_role,
                    ),
                    loading=RoleManagementState.role_is_loading,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                spacing="3",  # CHANGED: Reduced spacing
                width="100%",
                margin_top="20px",  # CHANGED: Reduced margin
            ),
            max_width="480px",  # CHANGED: Slightly reduced width
            width="90vw",
        ),
        open=rx.cond(
            is_edit,
            RoleManagementState.role_show_edit_modal,
            RoleManagementState.role_show_add_modal,
        ),
    )


def delete_confirmation_modal() -> rx.Component:
    """Modal for confirming role deletion."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text(
                        "Delete Role", font_weight="600", color="red"
                    ),  # CHANGED: Simplified color
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            size="1",
                            on_click=RoleManagementState.close_role_modals,
                        )
                    ),
                    width="100%",
                    align_items="center",
                ),
                margin_bottom="16px",
            ),
            rx.vstack(
                rx.text(
                    "Are you sure you want to delete this role?",
                    font_size="16px",
                ),
                rx.text(
                    "This action cannot be undone.",
                    font_size="14px",
                    color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
                ),
                rx.cond(
                    RoleManagementState.role_assigned_users.length() > 0,
                    rx.box(
                        rx.text(
                            "Warning: This role is assigned to users:",
                            font_weight="500",
                            color="orange",  # CHANGED: Simplified color
                            margin_bottom="8px",
                        ),
                        rx.text(
                            "You must remove all users from this role before deleting it.",
                            font_size="14px",
                            color="orange",  # CHANGED: Simplified color
                        ),
                        padding="12px",
                        bg=rx.color("orange", 2),  # CHANGED: Dark mode compatible
                        border_radius="8px",
                        border="1px solid",
                        border_color=rx.color(
                            "orange", 6
                        ),  # CHANGED: Dark mode compatible
                    ),
                ),
                spacing="6",
                align_items="start",
            ),
            rx.hstack(
                rx.button(
                    "Cancel",
                    variant="outline",
                    on_click=RoleManagementState.close_role_modals,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                rx.button(
                    "Delete Role",
                    color_scheme="red",
                    on_click=RoleManagementState.delete_role,
                    loading=RoleManagementState.role_is_loading,
                    flex="1",  # CHANGED: Use flex instead of width
                ),
                spacing="3",  # CHANGED: Reduced spacing
                width="100%",
                margin_top="16px",  # CHANGED: Reduced margin
            ),
            max_width="420px",  # CHANGED: Slightly reduced width
            width="90vw",
        ),
        open=RoleManagementState.role_show_delete_modal,
    )


def role_card(role) -> rx.Component:
    """Individual role card component."""
    return rx.box(
        rx.vstack(
            # Header with role name and actions
            rx.hstack(
                rx.vstack(
                    rx.text(
                        role["name"],
                        font_weight="600",
                        font_size="16px",
                        color=rx.color("gray", 12),  # CHANGED: Dark mode compatible
                    ),
                    rx.text(
                        role["description"],
                        font_size="14px",
                        color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
                        line_height="1.4",
                    ),
                    align_items="start",
                    spacing="2",  # CHANGED: Reduced spacing
                    flex="1",
                ),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.icon("ellipsis-vertical", size=20, stroke_width=3),
                            variant="ghost",
                            size="1",
                        )
                    ),
                    rx.menu.content(
                        rx.menu.item(
                            rx.icon("pencil", size=14),
                            "Edit Role",
                            on_click=lambda: RoleManagementState.open_role_edit_modal(
                                role["id"]
                            ),
                        ),
                        rx.menu.item(
                            rx.icon("shield", size=14),
                            "Manage Permissions",
                            on_click=lambda: RoleManagementState.open_role_permissions_modal(
                                role["id"]
                            ),
                        ),
                        rx.menu.separator(),
                        rx.menu.item(
                            rx.icon("trash-2", size=14),
                            "Delete Role",
                            color="red",
                            on_click=lambda: RoleManagementState.open_role_delete_modal(
                                role["id"]
                            ),
                        ),
                    ),
                ),
                align_items="start",
                width="100%",
            ),
            # Stats row
            rx.hstack(
                rx.hstack(
                    rx.icon(
                        "users", size=14, color=rx.color("blue", 9)
                    ),  # CHANGED: Dark mode compatible
                    rx.text(
                        f"{role['user_count']} users",
                        font_size="12px",
                        color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
                    ),
                    spacing="2",  # CHANGED: Reduced spacing
                    align_items="center",
                ),
                rx.hstack(
                    rx.icon(
                        "shield-check", size=14, color=rx.color("green", 9)
                    ),  # CHANGED: Dark mode compatible
                    rx.text(
                        f"{role['permissions'].to(list).length()} permissions",
                        font_size="12px",
                        color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
                    ),
                    spacing="2",  # CHANGED: Reduced spacing
                    align_items="center",
                ),
                spacing="6",
                width="100%",
            ),
            # CHANGED: Improved permissions preview with truncation
            rx.cond(
                role["permissions"].to(list).length() > 0,
                rx.box(
                    rx.text(
                        "Permissions:",
                        font_size="12px",
                        font_weight="500",
                        margin_bottom="6px",
                        color=rx.color("gray", 11),  # CHANGED: Dark mode compatible
                    ),
                    rx.cond(
                        role["permissions"].to(list).length() <= 4,
                        # Show all permissions if 4 or fewer
                        rx.flex(
                            rx.foreach(
                                role["permissions"].to(list),
                                lambda perm: rx.badge(
                                    perm,
                                    variant="soft",
                                    size="1",
                                    color_scheme="blue",
                                ),
                            ),
                            gap="2",
                            wrap="wrap",
                        ),
                        # Show first 3 permissions + count for more
                        rx.flex(
                            rx.foreach(
                                role["permissions"].to(list)[:3],
                                lambda perm: rx.badge(
                                    perm,
                                    variant="soft",
                                    size="1",
                                    color_scheme="blue",
                                ),
                            ),
                            rx.badge(
                                f"+{role['permissions'].to(list).length() - 3} more",
                                variant="outline",
                                size="1",
                                color_scheme="gray",
                            ),
                            gap="2",
                            wrap="wrap",
                        ),
                    ),
                    width="100%",
                ),
                rx.text(
                    "No permissions assigned",
                    font_size="12px",
                    color=rx.color("gray", 9),  # CHANGED: Dark mode compatible
                    font_style="italic",
                ),
            ),
            # Footer with dates
            rx.hstack(
                rx.text(
                    f"Created: {role['created_at']}",
                    font_size="11px",
                    color=rx.color("gray", 9),  # CHANGED: Dark mode compatible
                ),
                rx.spacer(),
                rx.text(
                    f"Updated: {role['updated_at']}",
                    font_size="11px",
                    color=rx.color("gray", 9),  # CHANGED: Dark mode compatible
                ),
                width="100%",
            ),
            spacing="6",  # CHANGED: Reduced spacing
            align_items="start",
            width="100%",
        ),
        padding="16px",  # CHANGED: Reduced padding
        border_radius="8px",  # CHANGED: Consistent with design system
        border="1px solid",
        border_color=rx.color("gray", 6),  # CHANGED: Dark mode compatible
        bg=rx.color("gray", 1),  # CHANGED: Dark mode compatible
        _hover={
            "shadow": "md",
            "border_color": rx.color("gray", 7),  # CHANGED: Dark mode compatible
        },
        transition="all 0.2s ease",
        width="100%",
    )


def roles_grid() -> rx.Component:
    """Grid of role cards."""
    return rx.cond(
        RoleManagementState.role_is_loading,
        rx.center(
            rx.vstack(
                rx.spinner(size="3"),
                rx.text(
                    "Loading roles...", color=rx.color("gray", 10)
                ),  # CHANGED: Dark mode compatible
                spacing="4",  # CHANGED: Reduced spacing
            ),
            padding="40px",  # CHANGED: Reduced padding
        ),
        rx.cond(
            RoleManagementState.filtered_roles.length() > 0,
            rx.box(
                rx.foreach(
                    RoleManagementState.filtered_roles,
                    role_card,
                ),
                display="grid",
                grid_template_columns=rx.breakpoints(
                    initial="1fr",
                    sm="repeat(2, 1fr)",
                    lg="repeat(3, 1fr)",
                ),
                gap="16px",  # CHANGED: Reduced gap
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon(
                        "search", size=48, color=rx.color("gray", 8)
                    ),  # CHANGED: Dark mode compatible
                    rx.text(
                        "No roles found",
                        font_size="18px",
                        font_weight="500",
                        color=rx.color("gray", 11),  # CHANGED: Dark mode compatible
                    ),
                    rx.text(
                        "Try adjusting your search or create a new role",
                        font_size="14px",
                        color=rx.color("gray", 9),  # CHANGED: Dark mode compatible
                        text_align="center",
                    ),
                    spacing="4",  # CHANGED: Reduced spacing
                    align_items="center",
                ),
                padding="40px",  # CHANGED: Reduced padding
            ),
        ),
    )


def header_section() -> rx.Component:
    """Header with title and create button."""
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.heading(
                    "Role Management",
                    size="6",
                    color=rx.color("gray", 12),  # CHANGED: Dark mode compatible
                ),
                rx.text(
                    "Manage user roles and permissions",
                    color=rx.color("gray", 10),  # CHANGED: Dark mode compatible
                    font_size="16px",
                ),
                align_items="start",
                spacing="2",  # CHANGED: Reduced spacing
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Create Role",
                on_click=RoleManagementState.open_role_add_modal,
                size="3",
                display=rx.breakpoints(initial="none", sm="flex"),
            ),
            width="100%",
            align_items="start",
        ),
        # Mobile create button
        rx.button(
            rx.icon("plus", size=16),
            "Create New Role",
            on_click=RoleManagementState.open_role_add_modal,
            width="100%",
            size="3",
            display=rx.breakpoints(initial="flex", sm="none"),
        ),
        spacing="6",  # CHANGED: Reduced spacing
        width="100%",
    )


def search_and_filters() -> rx.Component:
    """Search bar and filters."""
    return rx.hstack(
        rx.input(
            placeholder="Search roles...",
            value=RoleManagementState.role_search_query,
            on_change=RoleManagementState.set_role_search_query,
            width="100%",
            size="3",
        ),
        rx.button(
            rx.icon("refresh-cw", size=16),
            variant="outline",
            on_click=RoleManagementState.load_roles,
            size="3",
        ),
        spacing="4",  # CHANGED: Reduced spacing
        width="100%",
    )


def role_management_page() -> rx.Component:
    """Main role management page."""
    return rx.box(
        rx.vstack(
            header_section(),
            search_and_filters(),
            roles_grid(),
            spacing="6",  # CHANGED: Reduced spacing
            width="100%",
            max_width="1200px",
            margin="0 auto",
        ),
        # Modals
        role_form_modal(is_edit=False),
        role_form_modal(is_edit=True),
        delete_confirmation_modal(),
        permissions_modal(),
        padding="16px",  # CHANGED: Reduced padding
        min_height="100vh",
        bg=rx.color("gray", 1),  # CHANGED: Dark mode compatible background
        width="100%",
        on_mount=[
            RoleManagementState.load_roles,
            RoleManagementState.load_permissions,
        ],
    )
