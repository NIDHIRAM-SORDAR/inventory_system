from functools import wraps
from typing import List, Optional

import reflex as rx
import reflex_local_auth
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system.models.user import UserInfo


def has_permission(permission_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if permission_name in self.user_permissions:
                return func(self, *args, **kwargs)
            return rx.toast.error("Permission denied")

        return wrapper

    return decorator


class AuthState(reflex_local_auth.LocalAuthState):
    user_email: str = ""
    is_computing: bool = False
    cached_permissions: List[str] = []
    cached_roles: List[str] = []

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
        """Fetch basic UserInfo without relationships."""
        self.is_computing = True
        try:
            if self.authenticated_user.id < 0:
                return None
            with rx.session() as session:
                result = session.exec(
                    select(UserInfo).where(
                        UserInfo.user_id == self.authenticated_user.id
                    )
                ).one_or_none()
                return result
        finally:
            self.is_computing = False

    @rx.var(cache=True)
    def user_permissions(self) -> List[str]:
        """Return cached permissions for the authenticated user."""
        return self.cached_permissions

    @rx.var(cache=True)
    def user_roles(self) -> List[str]:
        """Return cached roles for the authenticated user."""
        return self.cached_roles

    def refresh_user_data(self):
        """Refresh cached permissions and roles from the database."""
        if not self.authenticated_user_info:
            self.cached_permissions = []
            self.cached_roles = []
            return
        with rx.session() as session:
            user_info = session.merge(self.authenticated_user_info)
            self.cached_permissions = user_info.get_permissions()
            self.cached_roles = user_info.get_roles()
