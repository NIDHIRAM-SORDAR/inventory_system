# inventory_system/utils/register_supplier.py

from reflex_local_auth import LocalUser
from sqlmodel import Session, select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo


def register_supplier(
    username: str, email: str, default_password: str, session: Session
) -> int:
    """
    Register a new supplier user and assign the supplier role.

    Args:
        username: Supplier's username (e.g., company name).
        email: Supplier's contact email.
        default_password: Default password for the new user.
        session: SQLAlchemy session for database operations.

    Returns:
        int: ID of the newly created or existing user.

    Raises:
        ValueError: If user creation, role assignment, or username conflict fails.
    """
    try:
        # Check for existing user
        existing_user = session.exec(
            select(LocalUser).where(LocalUser.username == username)
        ).one_or_none()
        if existing_user:
            # Check if user is linked to a supplier UserInfo
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == existing_user.id)
            ).one_or_none()
            if user_info and user_info.is_supplier:
                audit_logger.info(
                    "reuse_existing_supplier_user",
                    user_id=existing_user.id,
                    username=username,
                    email=email,
                )
                return existing_user.id
            else:
                audit_logger.error(
                    "fail_register_supplier_duplicate_username",
                    username=username,
                    email=email,
                    existing_user_id=existing_user.id,
                )
                raise ValueError(
                    f"Username '{username}' is already taken by a non-supplier user."
                )

        # Create LocalUser
        new_user = LocalUser(
            username=username,
            password_hash=LocalUser.hash_password(default_password),
            enabled=True,
        )
        session.add(new_user)
        session.flush()  # Get new_user.id without committing

        audit_logger.info(
            "create_supplier_user", user_id=new_user.id, username=username, email=email
        )

        # Create UserInfo and assign supplier role
        user_info = UserInfo(
            email=email,
            user_id=new_user.id,
            is_supplier=True,
            profile_picture="/default_supplier_avatar.png",
        )
        session.add(user_info)
        session.flush()  # Ensure user_info is persisted

        try:
            user_info.set_roles(["supplier"], session)
        except ValueError as e:
            session.rollback()
            audit_logger.error(
                "fail_set_supplier_role",
                user_id=new_user.id,
                username=username,
                error=str(e),
            )
            raise ValueError(f"Failed to assign supplier role: {str(e)}")

        session.commit()
        audit_logger.info(
            "success_register_supplier",
            user_id=new_user.id,
            username=username,
            email=email,
            roles=["supplier"],
        )
        return new_user.id

    except ValueError as ve:
        session.rollback()
        raise ve
    except Exception as e:
        session.rollback()
        audit_logger.error(
            "fail_register_supplier", username=username, email=email, error=str(e)
        )
        raise ValueError(f"Failed to register supplier: {str(e)}")
