# inventory_system/auth.py
from typing import Optional

import reflex as rx
import reflex_local_auth
import sqlmodel
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system.models.user import UserInfo


class AuthState(reflex_local_auth.LocalAuthState):
    user_email: str = ""
    is_computing: bool = False

    def load_user_data(self):
        """Initialize user data, including email, from the database."""
        if self.is_authenticated and self.authenticated_user_info:
            self.user_email = self.authenticated_user_info.email

    def set_user_email(self, email: str) -> None:
        """Update email and sync with database."""
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise ValueError(str(e))
        with rx.session() as session:
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info:
                existing_user = session.exec(
                    select(UserInfo).where(
                        UserInfo.email == email,
                        UserInfo.user_id != self.authenticated_user.id,
                    )
                ).one_or_none()
                if existing_user:
                    raise ValueError("This email is already in use by another user")
                user_info.email = email
                session.add(user_info)
                session.commit()
                session.refresh(user_info)
                self.user_email = email

    @rx.var(cache=True)
    def authenticated_user_info(self) -> Optional[UserInfo]:
        self.is_computing = True
        try:
            if self.authenticated_user.id < 0:
                return None
            with rx.session() as session:
                result = session.exec(
                    sqlmodel.select(UserInfo).where(
                        UserInfo.user_id == self.authenticated_user.id
                    )
                ).one_or_none()
                if not result:
                    return None
                return result
        finally:
            self.is_computing = False

    @rx.var(cache=True)
    def is_admin(self) -> bool:
        """Check if the authenticated user has the 'Admin' role."""
        user_info = self.authenticated_user_info
        return "admin" in user_info.get_roles() if user_info else False
