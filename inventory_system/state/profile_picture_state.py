# inventory_system/state/profile_picture_state.py
import asyncio
import os
from pathlib import Path

import reflex as rx
from sqlmodel import select

from inventory_system.models.user import UserInfo
from inventory_system.state.auth import AuthState

from ..constants import DEFAULT_PROFILE_PICTURE


class ProfilePictureState(AuthState):
    _profile_picture: str | None = None  # Private backing variable
    is_uploading: bool = False
    upload_progress: int = 0
    upload_error: str = ""
    preview_img: str = ""

    @rx.var
    def profile_picture(self) -> str:
        """Public computed var for the current profile picture."""
        if (
            self.authenticated_user_info
            and self.authenticated_user_info.profile_picture
        ):
            return self.authenticated_user_info.profile_picture
        return (
            self._profile_picture or DEFAULT_PROFILE_PICTURE
        )  # Default profile picture

    def set_profile_picture(self, url: str | None):
        """Set the profile picture manually and update the backend."""
        self._profile_picture = url
        if self.is_authenticated and self.authenticated_user_info:
            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo).where(
                        UserInfo.user_id == self.authenticated_user.id
                    )
                ).one_or_none()
                if user_info:
                    user_info.profile_picture = url
                    session.add(user_info)
                    session.commit()
                    session.refresh(user_info)
                    self.authenticated_user_info.profile_picture = url

    async def handle_profile_picture_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of a single profile picture."""
        self.upload_error = ""
        self.is_uploading = True
        self.upload_progress = 0
        yield

        if not files:
            self.is_uploading = False
            yield rx.toast.error(
                "No file selected. Please select an image to upload.",
                position="bottom-right",
            )
            return

        file = files[0]
        try:
            file_content = await file.read()
            filename = f"profile-pic-{self.authenticated_user.id}-{file.name}"
            upload_dir = rx.get_upload_dir()
            file_path = Path(os.path.join(upload_dir, filename))

            total_size = len(file_content)
            chunk_size = total_size // 10 or 1
            with file_path.open("wb") as f:
                for i in range(0, total_size, chunk_size):
                    chunk = file_content[i : i + chunk_size]
                    f.write(chunk)
                    self.upload_progress = min(
                        round((i + len(chunk)) / total_size * 100), 100
                    )
                    await asyncio.sleep(0.1)
                    yield

            backend_url = rx.config.get_config().api_url
            upload_url = f"{backend_url}/_upload/{filename}"
            self.set_profile_picture(upload_url)
            self.preview_img = upload_url
            yield rx.toast.success("Profile picture uploaded!", position="top-center")
        except Exception as e:
            self.upload_error = f"Upload failed: {str(e)}"
            yield rx.toast.error(f"Upload failed: {str(e)}", position="bottom-right")
        finally:
            self.is_uploading = False
            yield

    def clear_upload(self):
        """Clear the upload state."""
        self.upload_progress = 0
        self.preview_img = ""
        self.upload_error = ""
        return rx.clear_selected_files("profile_upload")
