import os

import reflex as rx
import reflex_local_auth
from dotenv import load_dotenv
from sqlmodel import select

from inventory_system.logging.audit import audit_logger
from inventory_system.models.user import Role, UserInfo

# Load environment variables from .env file
load_dotenv()


def create_admin_user():
    """Create an admin user with credentials from
    environment variables, aligned with RBAC."""
    # Read credentials from environment variables
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    email = os.getenv("ADMIN_EMAIL")

    # Check if all required environment variables are set
    if not all([username, password, email]):
        missing = [
            key
            for key, value in {
                "ADMIN_USERNAME": username,
                "ADMIN_PASSWORD": password,
                "ADMIN_EMAIL": email,
            }.items()
            if not value
        ]
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    with rx.session() as session:
        try:
            # Check if the username already exists in LocalUser
            existing_user_by_username = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.username == username
                )
            ).first()
            if existing_user_by_username:
                print(f"Error: User with username '{username}' already exists.")
                return

            # Check if the email already exists in UserInfo
            existing_user_by_email = session.exec(
                select(UserInfo).where(UserInfo.email == email)
            ).first()
            if existing_user_by_email:
                print(f"Error: User with email '{email}' already exists.")
                return

            # Ensure the admin role exists, create if not
            admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
            if not admin_role:
                admin_role = Role(name="admin", description="Administrator role")
                session.add(admin_role)
                session.flush()
                # Set default admin permissions (aligned with seed_roles.py)
                admin_permissions = [
                    "manage_users",
                    "view_user",
                    "create_user",
                    "edit_user",
                    "delete_user",
                    "manage_suppliers",
                    "view_supplier",
                    "create_supplier",
                    "edit_supplier",
                    "delete_supplier",
                    "manage_supplier_approval",
                    "view_inventory",
                    "create_inventory",
                    "update_inventory",
                    "delete_inventory",
                    "manage_roles",
                    "view_profile",
                    "edit_profile",
                ]
                admin_role.set_permissions(admin_permissions, session)
                audit_logger.info(
                    "create_role",
                    entity_type="role",
                    entity_id=admin_role.id,
                    details={"name": "admin", "permissions": admin_permissions},
                )

            # Create a new LocalUser
            user = reflex_local_auth.LocalUser(
                username=username,
                password_hash=reflex_local_auth.LocalUser.hash_password(password),
                enabled=True,
            )
            session.add(user)
            session.flush()  # Assign user.id

            # Create the corresponding UserInfo entry
            user_info = UserInfo(
                email=email, user_id=user.id, profile_picture="/default_avatar.png"
            )
            session.add(user_info)
            session.flush()  # Assign user_info.id

            # Assign the admin role
            user_info.set_roles(["admin"], session)

            # Commit all changes atomically
            session.commit()

            # Log user creation
            audit_logger.info(
                "create_user",
                entity_type="userinfo",
                entity_id=user_info.id,
                details={"email": email, "user_id": user.id, "username": username},
            )

            print(f"Admin user '{username}' created successfully with ID {user.id}")

        except Exception as e:
            session.rollback()
            audit_logger.error(
                "create_admin_failed",
                entity_type="userinfo",
                entity_id="unknown",
                details={"username": username, "email": email, "error": str(e)},
            )
            print(f"Error: Failed to create admin user: {str(e)}")


if __name__ == "__main__":
    try:
        create_admin_user()
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
