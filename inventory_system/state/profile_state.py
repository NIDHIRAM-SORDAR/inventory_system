# inventory_system/state/profile_state.py
import reflex as rx
from ..models import UserInfo
from ..state import AuthState
from sqlmodel import select
import reflex_local_auth
from inventory_system import routes
import os
from pathlib import Path

class ProfileState(AuthState):
    notifications: bool = True  # State-only field for notifications
    upload_error: str = ""  # To display upload errors
    is_uploading: bool = False  # To track upload status
    upload_progress: int = 0  # Progress percentage (0-100)
    img: str = ""  # Store the full URL of the newly uploaded image
    
    @rx.var
    def current_profile_picture(self) -> str:
        """Reactive var for the current profile picture URL."""
        return self.img if self.img else (self.authenticated_user_info.profile_picture if self.authenticated_user_info else "")
    
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

    @rx.event
    async def handle_profile_picture_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of a single profile picture."""
        self.upload_error = ""
        self.is_uploading = True
        self.upload_progress = 0

        if not files:
            self.is_uploading = False
            return rx.toast.error("No file selected. Please select an image to upload.", position="bottom-right")

        file = files[0]
        try:
            file_content = await file.read()
            filename = f"profile-pic-{self.authenticated_user.id}-{file.name}"
            upload_dir = rx.get_upload_dir()
            file_path = Path(os.path.join(upload_dir, filename))

            # Save the file
            with file_path.open("wb") as f:
                f.write(file_content)

            # Use the api_url from Reflex config to construct the full URL
            backend_url = rx.config.get_config().api_url  # e.g., "http://localhost:8000"
            upload_url = f"{backend_url}/_upload/{filename}"  # e.g., "http://localhost:8000/_upload/profile-pic-2-3686930.png"

            # Update the database
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
                user_info.profile_picture = upload_url  # Store the full URL
                session.add(user_info)
                session.commit()
                session.refresh(user_info)

            # Update the img state variable for frontend display
            self.img = upload_url  # Store the full URL as a string
            if self.authenticated_user_info:
                self.authenticated_user_info.profile_picture = upload_url  # Update the cached user info
            self.upload_progress = 100
            return rx.toast.success("Profile picture uploaded!", position="top-center")
        except Exception as e:
            self.upload_error = f"Upload failed: {str(e)}"
            return rx.toast.error(f"Upload failed: {str(e)}", position="bottom-right")
        finally:
            self.is_uploading = False

    def handle_upload_progress(self, progress: dict):
        """Update upload progress."""
        self.upload_progress = round(progress["progress"] * 100)
        if self.upload_progress >= 100:
            self.is_uploading = False

    def clear_upload(self):
        """Clear selected files and reset image preview."""
        self.upload_progress = 0
        self.img = ""
        self.upload_error = ""
        return rx.clear_selected_files("profile_upload")
