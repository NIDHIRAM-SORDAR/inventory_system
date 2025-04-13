# app/models.py
from typing import Optional

import reflex as rx
import reflex_local_auth
import sqlmodel

from inventory_system.models.user import UserInfo


class AuthState(reflex_local_auth.LocalAuthState):
    is_computing: bool = False

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
        """Check if the authenticated user is an admin."""
        user_info = self.authenticated_user_info
        return user_info.is_admin if user_info else False
