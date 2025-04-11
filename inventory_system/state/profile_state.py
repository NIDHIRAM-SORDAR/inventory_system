# inventory_system/state/profile_state.py
import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system import routes
from inventory_system.models import UserInfo
from inventory_system.state.auth import AuthState


class ProfileState(AuthState):
    notifications: bool = True

    def handle_submit(self, form_data: dict):
        if not self.is_authenticated:
            return rx.redirect(routes.LOGIN_ROUTE)

        self.set_username(form_data["username"])
        self.set_email(form_data["email"])

        with rx.session() as session:
            user = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.id == self.authenticated_user.id
                )
            ).one()
            user.username = form_data["username"]
            session.add(user)

            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info:
                user_info.email = form_data["email"]
                session.add(user_info)
            else:
                new_user_info = UserInfo(
                    user_id=self.authenticated_user.id,
                    email=form_data["email"],
                    role="employee",
                )
                session.add(new_user_info)

            session.commit()

        return rx.toast.success("Profile updated successfully", position="top-center")

    def toggle_notifications(self):
        self.set_notifications(not self.notifications)
