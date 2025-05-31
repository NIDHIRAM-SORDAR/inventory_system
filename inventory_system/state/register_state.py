import json
import os
import re

import reflex as rx
import reflex_local_auth
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role, UserInfo
from inventory_system.state.auth import AuthState
from inventory_system.state.user_mgmt_state import UserManagementState

from ..constants import DEFAULT_PROFILE_PICTURE

# Load user data from JSON files
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
USER_DATA_FILE = os.path.join(PROJECT_ROOT, "user_data.json")


def load_user_data():
    """Load user data from JSON file."""
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


class CustomRegisterState(reflex_local_auth.RegistrationState):
    registration_error: str = ""
    is_submitting: bool = False

    def reset_form_state(self):
        """Reset form state on page load."""
        self.registration_error = ""
        self.is_submitting = False

    def validate_user(self, form_data):
        """Validate user ID and email against user_data.json."""
        user_data = load_user_data()
        user_id = form_data.get("id")
        email = form_data.get("email")
        for user in user_data:
            if (
                str(user["ID"]) == str(user_id)
                and user["Email"].lower() == email.lower()
            ):
                return True
        return False

    def _validate_fields(
        self, username: str, password: str, confirm_password: str, email: str
    ) -> bool:
        """Validate username, password, and confirm password."""
        self.registration_error = ""

        # Username validation
        if not username:
            self.registration_error = "Username cannot be empty"
            return False
        if len(username) < 4 or len(username) > 20:
            self.registration_error = "Username must be 4-20 characters long"
            return False
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            self.registration_error = (
                "Username can only contain letters, numbers, and underscores"
            )
            return False
        with rx.session() as session:
            if session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.username == username
                )
            ).one_or_none():
                self.registration_error = f"Username {username} is already taken"
                return False

        # Password validation
        if not password:
            self.registration_error = "Password cannot be empty"
            return False
        if len(password) < 8:
            self.registration_error = "Password must be at least 8 characters long"
            return False
        if not re.search(r"[A-Z]", password):
            self.registration_error = "Password must contain an uppercase letter"
            return False
        if not re.search(r"[a-z]", password):
            self.registration_error = "Password must contain a lowercase letter"
            return False
        if not re.search(r"[0-9]", password):
            self.registration_error = "Password must contain a number"
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            self.registration_error = "Password must contain a special character"
            return False

        # Confirm password
        if password != confirm_password:
            self.registration_error = "Passwords do not match"
            return False

        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            self.registration_error = "Please enter a valid email address."
            return False

        return True

    async def _create_user_with_info(
        self,
        username: str,
        password: str,
        email: str,
        roles: list[str] = None,
        require_validation: bool = True,
        form_data: dict = None,
    ) -> tuple[bool, str, int]:
        """
        Core method to create LocalUser and UserInfo atomically.

        Returns: (success: bool, error_message: str, user_id: int)
        """
        roles = roles or ["employee"]

        ip_address = getattr(self.router.session, "client_ip", "unknown")
        user_id = -1

        try:
            # Pre-validation (if required)
            if require_validation and form_data:
                if not self.validate_user(form_data):
                    return False, "Invalid ID or email. Please check your details.", -1

            # Single atomic transaction for both LocalUser and UserInfo
            with rx.session() as session:
                # Create LocalUser directly
                new_user = reflex_local_auth.LocalUser()
                new_user.username = username
                new_user.password_hash = reflex_local_auth.LocalUser.hash_password(
                    password
                )
                new_user.enabled = True
                session.add(new_user)
                session.flush()  # Assign ID without committing

                if not new_user.id:
                    audit_logger.error(
                        "registration_failed_localuser",
                        username=username,
                        ip_address=ip_address,
                    )
                    return (
                        False,
                        "Registration failed: Could not create user account.",
                        -1,
                    )

                user_id = new_user.id
                audit_logger.info(
                    "registration_localuser_created",
                    username=username,
                    user_id=user_id,
                    ip_address=ip_address,
                )

                # Check for existing UserInfo (safety check)
                existing_info = session.exec(
                    select(UserInfo).where(UserInfo.user_id == user_id)
                ).one_or_none()
                if existing_info:
                    audit_logger.error(
                        "registration_failed_userinfo_exists",
                        username=username,
                        user_id=user_id,
                        existing_user_info_id=existing_info.id,
                        ip_address=ip_address,
                    )
                    return (
                        False,
                        "Registration failed: User profile already exists.",
                        -1,
                    )

                # Create UserInfo
                user_info = UserInfo(
                    email=email,
                    user_id=user_id,
                    profile_picture=DEFAULT_PROFILE_PICTURE,
                )
                session.add(user_info)
                session.flush()

                # Validate and assign roles
                if roles:
                    # Check all roles exist
                    valid_roles = session.exec(
                        select(Role).where(Role.name.in_(roles), Role.is_active)
                    ).all()

                    if len(valid_roles) != len(roles):
                        missing_roles = set(roles) - {role.name for role in valid_roles}
                        audit_logger.error(
                            "registration_failed_role_missing",
                            username=username,
                            user_id=user_id,
                            missing_roles=list(missing_roles),
                            ip_address=ip_address,
                        )
                        return (
                            False,
                            f"Registration failed: Roles not found: {', '.join(missing_roles)}",
                            -1,
                        )

                    # Assign roles
                    user_info.set_roles(roles, session)

                # Commit everything together - all or nothing
                session.commit()
                session.refresh(user_info)

                # Refresh user management state if needed

                user_mgmt_state = await self.get_state(UserManagementState)
                user_mgmt_state.check_auth_and_load()

                # Log success
                audit_logger.info(
                    "success_registration",
                    username=username,
                    email=email,
                    user_id=user_id,
                    user_info_id=user_info.id,
                    roles=user_info.get_roles(),
                    ip_address=ip_address,
                )

                return True, "Success", user_id

        except ValueError as role_error:
            error_msg = (
                f"Registration failed: Could not assign roles: {str(role_error)}"
            )
            audit_logger.error(
                "registration_failed_role_assignment",
                username=username,
                user_id=user_id,
                roles=roles,
                error=str(role_error),
                ip_address=ip_address,
            )
            return False, error_msg, -1

        except Exception as e:
            error_msg = "Registration failed: Could not save user details."
            audit_logger.error(
                "registration_failed_unexpected",
                username=username,
                user_id=user_id,
                error=str(e),
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            return False, error_msg, -1

    @rx.event
    async def handle_registration_with_email(self, form_data: dict):
        """Handle user self-registration with email validation."""
        self.registration_error = ""
        self.is_submitting = True
        yield

        username = form_data.get("username", "N/A")
        password = form_data.get("password", "N/A")
        confirm_password = form_data.get("confirm_password", "N/A")
        email = form_data.get("email", "N/A")
        submitted_id = form_data.get("id", "N/A")
        ip_address = getattr(self.router.session, "client_ip", "unknown")

        audit_logger.info(
            "attempt_registration",
            username=username,
            email=email,
            submitted_id=submitted_id,
            ip_address=ip_address,
        )

        try:
            # Validate fields
            if not self._validate_fields(username, password, confirm_password, email):
                audit_logger.warning(
                    "registration_validation_failed",
                    reason=self.registration_error,
                    username=username,
                    ip_address=ip_address,
                )
                yield rx.toast.error(self.registration_error)
                return

            # Create user with employee role and validation
            success, error_msg, user_id = await self._create_user_with_info(
                username=username,
                password=password,
                email=email,
                roles=["employee"],
                require_validation=True,
                form_data=form_data,
            )

            if not success:
                self.registration_error = error_msg
                yield rx.toast.error(error_msg)
                return

            self.new_user_id = user_id
            yield rx.toast.success(
                "Registration successful! Redirecting...",
                position="top-center",
                duration=1000,
            )
            yield rx.redirect(routes.LOGIN_ROUTE)

        except Exception as e:
            self.registration_error = "An unexpected error occurred. Please try again."
            audit_logger.critical(
                "registration_failed_critical",
                reason=str(e),
                username=username,
                email=email,
                submitted_id=submitted_id,
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            yield rx.toast.error(self.registration_error)

        finally:
            self.is_submitting = False

    @rx.event
    async def create_new_user(self, form_data: dict):
        """Admin method to create a new user directly."""
        permissions = await self.get_var_value(AuthState.permissions)
        acting_username = await self.get_var_value(AuthState.username)
        if "create_user" not in permissions:
            yield rx.toast.error("Permission denied: Cannot create users")
            return

        self.is_submitting = True
        yield

        try:
            # Validate required fields
            required_fields = ["username", "email", "password", "confirm_password"]
            for field in required_fields:
                if not form_data.get(field):
                    yield rx.toast.error(f"Missing required field: {field}")
                    return

            # Validate fields using existing method
            if not self._validate_fields(
                form_data["username"],
                form_data["password"],
                form_data["confirm_password"],
                form_data["email"],
            ):
                audit_logger.warning(
                    "admin_user_creation_validation_failed",
                    reason=self.registration_error,
                    username=form_data["username"],
                    acting_user=acting_username,
                )
                yield rx.toast.error(self.registration_error)
                return

            # Extract roles from form data
            selected_roles = []
            for key, value in form_data.items():
                if key.startswith("role_") and value:
                    role_name = key.replace("role_", "")
                    selected_roles.append(role_name)

            # Default to employee if no roles selected
            if not selected_roles:
                selected_roles = ["employee"]

            # Create user without validation (admin bypass)
            success, error_msg, user_id = await self._create_user_with_info(
                username=form_data["username"],
                password=form_data["password"],
                email=form_data["email"],
                roles=selected_roles,
                require_validation=False,  # Admin bypass
                form_data=None,
            )

            if not success:
                yield rx.toast.error(error_msg)
                return

            audit_logger.info(
                "user_created_by_admin",
                new_user_id=user_id,
                username=form_data["username"],
                email=form_data["email"],
                assigned_roles=selected_roles,
                acting_user=acting_username,
            )

            yield rx.toast.success(
                f"User '{form_data['username']}' created successfully"
            )

            # Refresh user management state if needed

            user_mgmt_state = await self.get_state(UserManagementState)
            user_mgmt_state.check_auth_and_load()

        except Exception as e:
            audit_logger.error(
                "admin_user_creation_failed",
                error=str(e),
                form_data={k: v for k, v in form_data.items() if k != "password"},
                acting_user=acting_username,
            )
            yield rx.toast.error(f"Failed to create user: {str(e)}")

        finally:
            self.is_submitting = False
