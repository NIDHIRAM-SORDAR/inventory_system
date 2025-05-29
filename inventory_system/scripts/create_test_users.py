import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.constants import DEFAULT_PROFILE_PICTURE
from inventory_system.logging.audit import audit_logger
from inventory_system.models.user import Role, UserInfo


def create_test_users():
    """Create 20 test users with hardcoded credentials."""
    password = "Test@1234"  # Meets password requirements

    with rx.session() as session:
        try:
            # Ensure the employee role exists
            employee_role = session.exec(
                select(Role).where(Role.name == "employee")
            ).first()
            if not employee_role:
                raise ValueError(
                    "Employee role does not exist. Please initialize it first."
                )

            # Create 20 test users (Test_2 to Test_21)
            for i in range(2, 22):  # Range from 2 to 21 inclusive
                username = f"Test_{i}"
                email = f"test{i}@example.com"

                # Check if the username already exists in LocalUser
                existing_user_by_username = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.username == username
                    )
                ).first()
                if existing_user_by_username:
                    print(
                        f"Warning: User with username '{username}' already exists. Skipping."
                    )
                    continue

                # Check if the email already exists in UserInfo
                existing_user_by_email = session.exec(
                    select(UserInfo).where(UserInfo.email == email)
                ).first()
                if existing_user_by_email:
                    print(
                        f"Warning: User with email '{email}' already exists. Skipping."
                    )
                    continue

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
                    email=email,
                    user_id=user.id,
                    profile_picture=DEFAULT_PROFILE_PICTURE,
                )
                session.add(user_info)
                session.flush()  # Assign user_info.id

                # Assign the employee role
                user_info.set_roles(["employee"], session)

                # Log user creation
                audit_logger.info(
                    "create_user",
                    entity_type="userinfo",
                    entity_id=user_info.id,
                    details={
                        "email": email,
                        "user_id": user.id,
                        "username": username,
                        "role": "employee",
                    },
                )

                print(f"Test user '{username}' created successfully with ID {user.id}")

            # Commit all changes atomically
            session.commit()

        except Exception as e:
            session.rollback()
            audit_logger.error(
                "create_test_users_failed",
                entity_type="userinfo",
                entity_id="unknown",
                details={"error": str(e)},
            )
            print(f"Error: Failed to create test users: {str(e)}")


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
