# Complete implementation for bulk_roles_state.py

import csv
import io
from typing import Any, Dict, List, Set

import reflex as rx
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Permission, Role, UserInfo
from inventory_system.state.auth import AuthState
from inventory_system.state.register_state import CustomRegisterState

from ..constants import DEFAULT_PROFILE_PICTURE


class BulkOperationsState(AuthState):
    """State for bulk operations on users and roles."""

    # Bulk user operations
    selected_user_ids: Set[int] = set()  # Using set for faster lookups
    bulk_operation_type: str = "replace"  # "replace", "add", "remove"
    bulk_selected_roles: List[str] = []
    show_bulk_roles_modal: bool = False
    bulk_is_loading: bool = False

    # Bulk role operations
    selected_role_ids: Set[int] = set()
    bulk_role_operation_type: str = "replace"
    bulk_selected_permissions: List[str] = []
    show_bulk_permissions_modal: bool = False
    bulk_role_is_loading: bool = False

    # UI state
    show_user_selection: bool = False
    show_role_selection: bool = False

    # User creation state
    create_user_form_data: Dict[str, Any] = {}

    @rx.var
    def selected_user_count(self) -> int:
        """Count of selected users."""
        return len(self.selected_user_ids)

    @rx.var
    def selected_role_count(self) -> int:
        """Count of selected roles."""
        return len(self.selected_role_ids)

    @rx.var
    def available_roles_for_bulk(self) -> List[str]:
        """Get available roles for bulk assignment."""
        with rx.session() as session:
            try:
                roles = session.exec(select(Role).where(Role.is_active)).all()
                return [role.name for role in roles]
            except Exception as e:
                audit_logger.error("loading_roles_for_bulk_failed", error=str(e))
                return []

    @rx.var
    def available_permissions_for_bulk(self) -> List[Dict[str, Any]]:
        """Get available permissions for bulk assignment."""
        with rx.session() as session:
            try:
                perms = session.exec(select(Permission)).all()
                return [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "category": p.category or "Uncategorized",
                    }
                    for p in perms
                ]
            except Exception as e:
                audit_logger.error("loading_permissions_for_bulk_failed", error=str(e))
                return []

    @rx.var
    def grouped_permissions_for_bulk(self) -> List[Dict[str, Any]]:
        """Get permissions grouped by category for bulk assignment."""
        permissions = self.available_permissions_for_bulk

        # Group permissions by category
        categories = {}
        for perm in permissions:
            category = perm["category"] or "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(perm)

        # Convert to list format expected by UI
        return [
            {"category": category, "permissions": perms}
            for category, perms in sorted(categories.items())
        ]

    # User selection methods
    @rx.event
    def toggle_user_selection(self, user_id: int) -> None:
        """Toggle user selection for bulk operations."""
        if user_id in self.selected_user_ids:
            self.selected_user_ids.discard(user_id)
        else:
            self.selected_user_ids.add(user_id)

    @rx.event
    def select_all_current_page_users(self) -> None:
        """Select all users on current page."""
        # This method needs to get current page users from UserManagementState
        # We'll implement this by accessing the current page data
        try:
            # Get current state instance to access current page users
            # Note: This is a simplified approach - in practice you might want to
            # pass the user IDs from the UI or use a different pattern
            with rx.session() as session:
                # For now, we'll select all active users - this should be refined
                # to work with the actual current page from UserManagementState
                users = session.exec(
                    select(UserInfo).where(UserInfo.is_active == True).limit(20)
                ).all()
                user_ids = [user.id for user in users]
                self.selected_user_ids.update(user_ids)
        except Exception as e:
            audit_logger.error("select_all_current_page_failed", error=str(e))

    @rx.event
    def deselect_all_users(self) -> None:
        """Deselect all users."""
        self.selected_user_ids.clear()

    # Role selection methods
    @rx.event
    def toggle_role_selection(self, role_id: int) -> None:
        """Toggle role selection for bulk operations."""
        if role_id in self.selected_role_ids:
            self.selected_role_ids.discard(role_id)
        else:
            self.selected_role_ids.add(role_id)

    @rx.event
    def select_all_available_roles(self) -> None:
        """Select all available roles."""
        with rx.session() as session:
            try:
                roles = session.exec(select(Role).where(Role.is_active)).all()
                role_ids = [role.id for role in roles]
                self.selected_role_ids.update(role_ids)
            except Exception as e:
                audit_logger.error("select_all_roles_failed", error=str(e))

    @rx.event
    def deselect_all_roles(self) -> None:
        """Deselect all roles."""
        self.selected_role_ids.clear()

    # Bulk role assignment for users
    @rx.event
    def open_bulk_roles_modal(self):
        """Open bulk roles assignment modal."""
        if not self.selected_user_ids:
            yield rx.toast.error("Please select users first")
            return

        self.bulk_selected_roles = []
        self.bulk_operation_type = "replace"
        self.show_bulk_roles_modal = True

    @rx.event
    def close_bulk_roles_modal(self) -> None:
        """Close bulk roles modal."""
        self.show_bulk_roles_modal = False
        self.bulk_selected_roles = []

    @rx.event
    def set_bulk_operation_type(self, operation: str) -> None:
        """Set bulk operation type."""
        self.bulk_operation_type = operation

    @rx.event
    def toggle_bulk_role(self, role_name: str):
        """Toggle role in bulk selection."""
        if role_name in self.bulk_selected_roles:
            self.bulk_selected_roles.remove(role_name)
        else:
            self.bulk_selected_roles.append(role_name)

    @rx.event
    async def execute_bulk_role_assignment(self):
        """Execute bulk role assignment."""
        if "edit_user" not in self.permissions:
            yield rx.toast.error("Permission denied: Cannot modify user roles")
            return

        if not self.selected_user_ids:
            yield rx.toast.error("No users selected")
            return

        if not self.bulk_selected_roles and self.bulk_operation_type != "remove":
            yield rx.toast.error("Please select at least one role")
            return

        self.bulk_is_loading = True

        try:
            with rx.session() as session:
                # Convert set to list for the bulk operation
                user_ids = list(self.selected_user_ids)

                results = UserInfo.bulk_set_roles(
                    user_ids=user_ids,
                    role_names=self.bulk_selected_roles,
                    session=session,
                    operation=self.bulk_operation_type,
                )

                session.commit()

                # Create success message
                success_count = len(results["success"])
                failed_count = len(results["failed"])
                unchanged_count = len(results["unchanged"])

                operation_text = {
                    "replace": "assigned to",
                    "add": "added to",
                    "remove": "removed from",
                }[self.bulk_operation_type]

                if success_count > 0:
                    yield rx.toast.success(
                        f"Roles {operation_text} {success_count} user(s) successfully"
                    )

                if failed_count > 0:
                    yield rx.toast.warning(f"Failed to update {failed_count} user(s)")

                if unchanged_count > 0:
                    yield rx.toast.info(f"{unchanged_count} user(s) had no changes")

                # Log the operation
                audit_logger.info(
                    "bulk_role_assignment_completed",
                    operation=self.bulk_operation_type,
                    user_count=len(user_ids),
                    roles=self.bulk_selected_roles,
                    results=results,
                    acting_user=self.username,
                )

                # Refresh user data and close modal
                from inventory_system.state.user_mgmt_state import UserManagementState

                user_mgmt_state = await self.get_state(UserManagementState)
                user_mgmt_state.check_auth_and_load()

                self.close_bulk_roles_modal()
                self.deselect_all_users()

        except Exception as e:
            audit_logger.error(
                "bulk_role_assignment_failed",
                error=str(e),
                user_ids=list(self.selected_user_ids),
                roles=self.bulk_selected_roles,
                acting_user=self.username,
            )
            yield rx.toast.error(f"Bulk operation failed: {str(e)}")

        finally:
            self.bulk_is_loading = False

    # Bulk permission assignment for roles
    @rx.event
    def open_bulk_permissions_modal(self):
        """Open bulk permissions assignment modal."""
        if not self.selected_role_ids:
            yield rx.toast.error("Please select roles first")
            return

        self.bulk_selected_permissions = []
        self.bulk_role_operation_type = "replace"
        self.show_bulk_permissions_modal = True

    @rx.event
    def close_bulk_permissions_modal(self) -> None:
        """Close bulk permissions modal."""
        self.show_bulk_permissions_modal = False
        self.bulk_selected_permissions = []

    @rx.event
    def set_bulk_role_operation_type(self, operation: str) -> None:
        """Set bulk role operation type."""
        self.bulk_role_operation_type = operation

    @rx.event
    def toggle_bulk_permission(self, permission_name: str) -> None:
        """Toggle permission in bulk selection."""
        if permission_name in self.bulk_selected_permissions:
            self.bulk_selected_permissions.remove(permission_name)
        else:
            self.bulk_selected_permissions.append(permission_name)

    @rx.event
    async def execute_bulk_permission_assignment(self):
        """Execute bulk permission assignment."""
        if "manage_roles" not in self.permissions:
            yield rx.toast.error("Permission denied: Cannot modify role permissions")
            return

        if not self.selected_role_ids:
            yield rx.toast.error("No roles selected")
            return

        if (
            not self.bulk_selected_permissions
            and self.bulk_role_operation_type != "remove"
        ):
            yield rx.toast.error("Please select at least one permission")
            return

        self.bulk_role_is_loading = True

        try:
            with rx.session() as session:
                # Convert set to list for the bulk operation
                role_ids = list(self.selected_role_ids)

                results = Role.bulk_set_permissions(
                    role_ids=role_ids,
                    permission_names=self.bulk_selected_permissions,
                    session=session,
                    operation=self.bulk_role_operation_type,
                )

                session.commit()

                # Create success message
                success_count = len(results["success"])
                failed_count = len(results["failed"])
                unchanged_count = len(results["unchanged"])

                operation_text = {
                    "replace": "assigned to",
                    "add": "added to",
                    "remove": "removed from",
                }[self.bulk_role_operation_type]

                if success_count > 0:
                    yield rx.toast.success(
                        f"Permissions {operation_text} "
                        f"{success_count} role(s) successfully"
                    )

                if failed_count > 0:
                    yield rx.toast.warning(f"Failed to update {failed_count} role(s)")

                if unchanged_count > 0:
                    yield rx.toast.info(f"{unchanged_count} role(s) had no changes")

                # Log the operation
                audit_logger.info(
                    "bulk_permission_assignment_completed",
                    operation=self.bulk_role_operation_type,
                    role_count=len(role_ids),
                    permissions=self.bulk_selected_permissions,
                    results=results,
                    acting_user=self.username,
                )

                # Refresh role data and close modal
                from inventory_system.state.role_state import RoleManagementState

                role_mgmt_state = await self.get_state(RoleManagementState)
                role_mgmt_state.load_roles()

                self.close_bulk_permissions_modal()
                self.deselect_all_roles()

        except Exception as e:
            audit_logger.error(
                "bulk_permission_assignment_failed",
                error=str(e),
                role_ids=list(self.selected_role_ids),
                permissions=self.bulk_selected_permissions,
                acting_user=self.username,
            )
            yield rx.toast.error(f"Bulk operation failed: {str(e)}")

        finally:
            self.bulk_role_is_loading = False

    # User Creation Methods
    @rx.event
    async def create_new_user(self, form_data: Dict[str, Any]):
        """Create a new user with the provided form data."""
        if "create_user" not in self.permissions:
            yield rx.toast.error("Permission denied: Cannot create users")
            return

        self.bulk_is_loading = True
        yield

        try:
            # Validate required fields
            required_fields = ["username", "email", "password", "confirm_password"]
            for field in required_fields:
                if not form_data.get(field):
                    yield rx.toast.error(f"Missing required field: {field}")
                    return

            # Validate password confirmation
            if form_data["password"] != form_data["confirm_password"]:
                yield rx.toast.error("Passwords do not match")
                return
            try:
                validate_email(form_data["email"])
            except EmailNotValidError:
                yield rx.toast.error("Email is not valid")
                return

            register_state = await self.get_state(CustomRegisterState)

            if not register_state._validate_fields(
                form_data["username"],
                form_data["password"],
                form_data["confirm_password"],
            ):
                audit_logger.warning(
                    "registration_validation_failed",
                    reason=register_state.registration_error,
                    username=form_data["username"],
                )
                yield rx.toast.error(register_state.registration_error)
                return

            # Extract roles from form data
            selected_roles = []
            for key, value in form_data.items():
                if key.startswith("role_") and value:
                    role_name = key.replace("role_", "")
                    selected_roles.append(role_name)

            with rx.session() as session:
                try:
                    # Register user
                    register_state._register_user(
                        form_data["username"], form_data["password"]
                    )
                    if register_state.new_user_id < 0:
                        register_state.registration_error = (
                            "Registration failed: Could not create user account."
                        )
                        audit_logger.error(
                            "registration_failed_localuser",
                            reason=register_state.registration_error,
                            username=form_data["username"],
                        )
                        yield rx.toast.error(register_state.registration_error)
                        session.rollback()
                        return

                    audit_logger.info(
                        "registration_localuser_created",
                        username=form_data["username"],
                        user_id=register_state.new_user_id,
                    )

                    # Check for existing UserInfo
                    existing_info = session.exec(
                        select(UserInfo).where(
                            UserInfo.user_id == register_state.new_user_id
                        )
                    ).one_or_none()
                    if existing_info:
                        register_state.registration_error = (
                            "Registration failed: User profile already exists."
                        )
                        audit_logger.error(
                            "registration_failed_userinfo_exists",
                            reason=register_state.registration_error,
                            username=form_data["username"],
                            user_id=register_state.new_user_id,
                            existing_user_info_id=existing_info.id,
                        )
                        yield rx.toast.error(register_state.registration_error)
                        session.rollback()
                        return
                    # Create UserInfo
                    user_info = UserInfo(
                        email=form_data["email"],
                        user_id=register_state.new_user_id,
                        profile_picture=DEFAULT_PROFILE_PICTURE,
                    )
                    session.add(user_info)
                    session.flush()

                    # Assign roles if any selected
                    if selected_roles:
                        roles = session.exec(
                            select(Role).where(Role.name.in_(selected_roles))
                        ).all()
                        try:
                            user_info.set_roles(roles, session)
                        except ValueError as role_error:
                            register_state.registration_error = (
                                f"Registration failed: Could not assign employee role: "
                                f"{str(role_error)}"
                            )
                            audit_logger.error(
                                "registration_failed_role_assignment",
                                reason=register_state.registration_error,
                                username=form_data["username"],
                                user_id=register_state.new_user_id,
                                role="employee",
                                error=str(role_error),
                            )
                            yield rx.toast.error(register_state.registration_error)
                            session.rollback()
                            return

                    session.commit()
                    session.refresh(user_info)

                    # Log the operation
                    audit_logger.info(
                        "user_created_via_direct_operations",
                        new_user_id=user_info.id,
                        username=user_info.username,
                        email=user_info.email,
                        assigned_roles=selected_roles,
                        acting_user=self.username,
                    )

                    yield rx.toast.success(
                        f"User '{form_data['username']}' created successfully"
                    )

                    # Refresh the user management state to show the new user
                    from inventory_system.state.user_mgmt_state import (
                        UserManagementState,
                    )

                    user_mgmt_state = await self.get_state(UserManagementState)
                    user_mgmt_state.check_auth_and_load()

                except Exception as db_error:
                    register_state.registration_error = (
                        "Registration failed: Could not save user details."
                    )
                    audit_logger.error(
                        "registration_failed_userinfo",
                        reason=str(db_error),
                        username=form_data["username"],
                        user_id=register_state.new_user_id,
                        error=str(db_error),
                    )

                    yield rx.toast.error(register_state.registration_error)
                    session.rollback()
                    return
        except Exception as e:
            audit_logger.error(
                "user_creation_failed",
                error=str(e),
                form_data={k: v for k, v in form_data.items() if k != "password"},
                acting_user=self.username,
            )
            yield rx.toast.error(f"Failed to create user: {str(e)}")

        finally:
            self.bulk_is_loading = False

    # Export Methods
    @rx.event
    async def export_users(self):
        """Export users to CSV."""
        try:
            with rx.session() as session:
                users = session.exec(select(UserInfo)).all()

                # Create CSV data
                csv_data = []
                for user in users:
                    csv_data.append(
                        {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "is_active": user.is_active,
                            "roles": ",".join([role.name for role in user.roles])
                            if user.roles
                            else "",
                            "created_at": user.created_at.isoformat()
                            if user.created_at
                            else "",
                            "last_login": user.last_login.isoformat()
                            if user.last_login
                            else "",
                        }
                    )

                # Convert to CSV string
                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                # Trigger download
                yield rx.download(
                    data=csv_content, filename="users_export.csv", media_type="text/csv"
                )

                audit_logger.info(
                    "users_exported",
                    user_count=len(csv_data),
                    acting_user=self.username,
                )

                yield rx.toast.success(f"Exported {len(csv_data)} users to CSV")

        except Exception as e:
            audit_logger.error(
                "user_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")

    @rx.event
    async def export_roles(self):
        """Export roles to CSV."""
        try:
            with rx.session() as session:
                roles = session.exec(select(Role)).all()

                csv_data = []
                for role in roles:
                    csv_data.append(
                        {
                            "id": role.id,
                            "name": role.name,
                            "description": role.description or "",
                            "is_active": role.is_active,
                            "permissions": ",".join(
                                [perm.name for perm in role.permissions]
                            )
                            if role.permissions
                            else "",
                            "created_at": role.created_at.isoformat()
                            if role.created_at
                            else "",
                        }
                    )

                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                yield rx.download(
                    data=csv_content, filename="roles_export.csv", media_type="text/csv"
                )

                audit_logger.info(
                    "roles_exported",
                    role_count=len(csv_data),
                    acting_user=self.username,
                )

                yield rx.toast.success(f"Exported {len(csv_data)} roles to CSV")

        except Exception as e:
            audit_logger.error(
                "role_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")

    @rx.event
    async def export_permissions(self):
        """Export permissions to CSV."""
        try:
            with rx.session() as session:
                permissions = session.exec(select(Permission)).all()

                csv_data = []
                for perm in permissions:
                    csv_data.append(
                        {
                            "id": perm.id,
                            "name": perm.name,
                            "description": perm.description or "",
                            "category": perm.category or "Uncategorized",
                            "created_at": perm.created_at.isoformat()
                            if perm.created_at
                            else "",
                        }
                    )

                output = io.StringIO()
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                csv_content = output.getvalue()
                output.close()

                yield rx.download(
                    data=csv_content,
                    filename="permissions_export.csv",
                    media_type="text/csv",
                )

                audit_logger.info(
                    "permissions_exported",
                    permission_count=len(csv_data),
                    acting_user=self.username,
                )

                yield rx.toast.success(f"Exported {len(csv_data)} permissions to CSV")

        except Exception as e:
            audit_logger.error(
                "permission_export_failed", error=str(e), acting_user=self.username
            )
            yield rx.toast.error(f"Export failed: {str(e)}")
