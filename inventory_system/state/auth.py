# app/models.py
from typing import Optional

import reflex as rx
import reflex_local_auth
import sqlmodel

from ..models import UserInfo


class AuthState(reflex_local_auth.LocalAuthState):
    @rx.var(cache=True)
    def authenticated_user_info(self) -> Optional[UserInfo]:
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

    @rx.var(cache=True)
    def is_admin(self) -> bool:
        """Check if the authenticated user is an admin."""
        user_info = self.authenticated_user_info
        return user_info.is_admin if user_info else False
