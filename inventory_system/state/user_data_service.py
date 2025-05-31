# user_data_service.py
from typing import Any, Dict, List, Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo


class UserDataService:
    """Shared service for loading user data across different states."""

    @staticmethod
    def load_users_data(exclude_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load users data with roles information."""
        with rx.session() as session:
            try:
                stmt = select(UserInfo, reflex_local_auth.LocalUser.username).join(
                    reflex_local_auth.LocalUser,
                    UserInfo.user_id == reflex_local_auth.LocalUser.id,
                )

                if exclude_user_id:
                    stmt = stmt.where(UserInfo.user_id != exclude_user_id)

                results = session.exec(stmt).all()

                return [
                    {
                        "username": username,
                        "id": user_info.user_id,
                        "email": user_info.email,
                        "roles": user_info.get_roles() or ["none"],
                    }
                    for user_info, username in results
                ]
            except Exception as e:
                audit_logger.error("loading_users_data_failed", error=str(e))
                return []

    @staticmethod
    def filter_users(
        users_data: List[Dict[str, Any]],
        search_value: str = "",
        sort_value: str = "username",
        sort_reverse: bool = False,
    ) -> List[Dict[str, Any]]:
        """Filter and sort users data."""
        data = users_data

        if search_value:
            search_lower = search_value.lower()
            data = [
                u
                for u in data
                if search_lower in u["username"].lower()
                or search_lower in u["email"].lower()
                or any(search_lower in role.lower() for role in u["roles"])
            ]

        return sorted(data, key=lambda x: x[sort_value], reverse=sort_reverse)
