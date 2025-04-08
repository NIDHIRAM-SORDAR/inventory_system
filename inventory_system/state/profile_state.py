# inventory_system/state/profile_state.py
import reflex as rx
from ..models import UserInfo
from ..state import AuthState
from sqlmodel import select
import reflex_local_auth
from inventory_system import routes
import os

class ProfileState(AuthState):
    notifications: bool = True  # State-only field for notifications
    upload_error: str = ""  # To display upload errors
    is_uploading: bool = False  # To track upload status
    upload_progress: int = 0  # Progress percentage (0-100)
    img: str = ""

    def handle_submit(self, form_data: dict):
        """Update the LocalUser and UserInfo models with form data."""
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
                select(UserInfo).where(
                    UserInfo.user_id == self.authenticated_user.id
                )
            ).one_or_none()
            if user_info:
                user_info.email = form_data["email"]
                session.add(user_info)
            else:
                new_user_info = UserInfo(
                    user_id=self.authenticated_user.id,
                    email=form_data["email"],
                    role="employee"
                )
                session.add(new_user_info)
            
            session.commit()
        
        return rx.toast.success("Profile updated successfully", position="top-center")

    def toggle_notifications(self):
        """Toggle the notifications setting."""
        self.set_notifications(not self.notifications)

    async def handle_profile_picture_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of a single profile picture."""
        self.upload_error = ""
        self.is_uploading = True
        self.upload_progress = 0  # Reset progress

        if not files:
            self.upload_error = "No file selected."
            self.is_uploading = False
            return

        file = files[0]  # Single file upload
        try:
            file_content = await file.read()
            filename = f"profile-pic-{self.authenticated_user.id}-{file.filename}"
            upload_dir = rx.get_upload_dir()
            file_path = os.path.join(upload_dir, filename)

            with open(file_path, "wb") as f:
                f.write(file_content)

            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
                ).one_or_none()
                if not user_info:
                    user_info = UserInfo(
                        user_id=self.authenticated_user.id,
                        email=self.authenticated_user.email,
                        role="employee"
                    )
                user_info.profile_picture = rx.get_upload_url(filename)
                session.add(user_info)
                session.commit()

            self.upload_progress = 100  # Set to 100% on success
            return rx.toast.success("Profile picture uploaded!", position="top-center")
        except Exception as e:
            self.upload_error = f"Upload failed: {str(e)}"
        finally:
            self.is_uploading = False

    def handle_upload_progress(self, progress: dict):
        """Update upload progress."""
        self.upload_progress = round(progress["progress"] * 100)
        if self.upload_progress >= 100:
            self.is_uploading = False

    def clear_upload(self):
        """Clear selected files."""
        self.upload_progress = 0  # Reset progress when clearing
        return rx.clear_selected_files("profile_upload")