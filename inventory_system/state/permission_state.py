from typing import Any, Dict, List, Optional

import reflex as rx
from sqlmodel import select

from inventory_system.models.user import Permission


class PermissionsManagementState(rx.State):
    """State for managing permissions with database integration."""

    # Permission data
    permissions: List[Dict[str, Any]] = []
    perm_search_query: str = ""
    perm_selected_category: str = "All"
    perm_current_page: int = 1
    perm_items_per_page: int = 12
    perm_is_loading: bool = False

    # Modal states
    perm_show_add_modal: bool = False
    perm_show_edit_modal: bool = False
    perm_show_delete_modal: bool = False

    # Form states
    perm_form_name: str = ""
    perm_form_category: str = ""
    perm_form_description: str = ""
    perm_editing_id: Optional[int] = None
    perm_deleting_id: Optional[int] = None

    # Categories derived from loaded permissions
    @rx.var
    def perm_categories(self) -> List[str]:
        """Dynamically generate categories from loaded permissions."""
        unique_categories = set(
            p["category"] for p in self.permissions if p["category"]
        )
        return ["All"] + sorted(list(unique_categories))

    # Computed variables
    @rx.var
    def filtered_permissions(self) -> List[Dict[str, Any]]:
        filtered = self.permissions
        selected_category = self.perm_selected_category
        if selected_category != "All":
            filtered = [
                p
                for p in filtered
                if (p["category"] if p["category"] is not None else "Uncategorized")
                == selected_category
            ]
        if self.perm_search_query:
            query = self.perm_search_query.lower()
            filtered = [
                p
                for p in filtered
                if query in p["name"].lower()
                or query in p["description"].lower()
                or query
                in (
                    p["category"] if p["category"] is not None else "Uncategorized"
                ).lower()
            ]
        return filtered

    @rx.var
    def paginated_permissions(self) -> List[Dict[str, Any]]:
        start = (self.perm_current_page - 1) * self.perm_items_per_page
        end = start + self.perm_items_per_page
        return self.filtered_permissions[start:end]

    @rx.var
    def perm_total_pages(self) -> int:
        return max(
            1,
            (len(self.filtered_permissions) + self.perm_items_per_page - 1)
            // self.perm_items_per_page,
        )

    @rx.var
    def filtered_permissions_by_category(self) -> dict:
        """Group filtered permissions by category, sorted by category name."""
        grouped = {}
        for p in self.filtered_permissions:
            cat = p["category"] if p["category"] else "Uncategorized"
            grouped.setdefault(cat, []).append(p)
        # Sort categories alphabetically
        return dict(sorted(grouped.items()))

    # Initial data load
    def load_permissions(self) -> None:
        """Load permissions from the database."""
        with rx.session() as session:
            perms = session.exec(select(Permission)).all()
            self.permissions = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category
                    if p.category is not None
                    else "Uncategorized",
                }
                for p in perms
            ]
            for perm in self.permissions:
                perm["permission_code"] = self.get_permission_code(perm["name"])

    def get_permission_code(self, name: str) -> str:
        """Generate a 6-character code from the permission name."""
        return name.upper().replace("_", "").zfill(6)[-6:]

    # Event handlers
    @rx.event
    def set_perm_search_query(self, query: str) -> None:
        """Update search query and reset to first page."""
        self.perm_search_query = query
        self.perm_current_page = 1

    @rx.event
    def set_perm_category_filter(self, category: str) -> None:
        """Update category filter and reset to first page."""
        self.perm_selected_category = category
        self.perm_current_page = 1

    @rx.event
    def set_perm_page(self, page: int) -> None:
        """Set current page."""
        self.perm_current_page = max(1, min(page, self.perm_total_pages))

    @rx.event
    def next_perm_page(self) -> None:
        """Go to next page."""
        if self.perm_current_page < self.perm_total_pages:
            self.perm_current_page += 1

    @rx.event
    def prev_perm_page(self) -> None:
        """Go to previous page."""
        if self.perm_current_page > 1:
            self.perm_current_page -= 1

    # Modal handlers
    @rx.event
    def open_perm_add_modal(self) -> None:
        """Open add permission modal."""
        self.perm_form_name = ""
        self.perm_form_category = "Suppliers"
        self.perm_form_description = ""
        self.perm_show_add_modal = True

    @rx.event
    def open_perm_edit_modal(self, perm_id: int) -> None:
        """Open edit permission modal."""
        with rx.session() as session:
            perm = session.exec(
                select(Permission).where(Permission.id == perm_id)
            ).one_or_none()
            if perm:
                self.perm_form_name = perm.name
                self.perm_form_category = perm.category or ""
                self.perm_form_description = perm.description or ""
                self.perm_editing_id = perm_id
                self.perm_show_edit_modal = True

    @rx.event
    def open_perm_delete_modal(self, perm_id: int) -> None:
        """Open delete confirmation modal."""
        self.perm_deleting_id = perm_id
        self.perm_show_delete_modal = True

    @rx.event
    def close_perm_modals(self) -> None:
        """Close all modals."""
        self.perm_show_add_modal = False
        self.perm_show_edit_modal = False
        self.perm_show_delete_modal = False
        self.perm_editing_id = None
        self.perm_deleting_id = None

    # CRUD operations
    @rx.event
    async def add_permission(self):
        """Add a new permission."""
        if not self.perm_form_name or not self.perm_form_description:
            yield rx.toast.error("Name and description are required")
            return
        self.perm_is_loading = True
        try:
            with rx.session() as session:
                Permission.create_permission(
                    name=self.perm_form_name,
                    description=self.perm_form_description,
                    category=self.perm_form_category,
                    session=session,
                )
                session.commit()
                self.load_permissions()
                self.close_perm_modals()
                yield rx.toast.success(
                    f"Permission '{self.perm_form_name}' added successfully"
                )
        except Exception as e:
            yield rx.toast.error(f"Failed to add permission: {str(e)}")
        finally:
            self.perm_is_loading = False

    @rx.event
    async def update_permission(self):
        """Update an existing permission."""
        if not self.perm_form_name or not self.perm_form_description:
            yield rx.toast.error("Name and description are required")
            return
        self.perm_is_loading = True
        try:
            with rx.session() as session:
                perm = session.exec(
                    select(Permission).where(Permission.id == self.perm_editing_id)
                ).one_or_none()
                if perm:
                    perm.update_permission(
                        session=session,
                        name=self.perm_form_name,
                        description=self.perm_form_description,
                        category=self.perm_form_category,
                    )
                    session.commit()
                    self.load_permissions()
                    self.close_perm_modals()
                    yield rx.toast.success(
                        f"Permission '{self.perm_form_name}' updated successfully"
                    )
        except Exception as e:
            yield rx.toast.error(f"Failed to update permission: {str(e)}")
        finally:
            self.perm_is_loading = False

    @rx.event
    async def delete_permission(self):
        """Delete a permission."""
        self.perm_is_loading = True
        try:
            with rx.session() as session:
                perm = session.exec(
                    select(Permission).where(Permission.id == self.perm_deleting_id)
                ).one_or_none()
                if perm:
                    Permission.delete_permission(name=perm.name, session=session)
                    session.commit()
                    self.load_permissions()
                    if (
                        len(self.paginated_permissions) == 0
                        and self.perm_current_page > 1
                    ):
                        self.perm_current_page -= 1
                    self.close_perm_modals()
                    yield rx.toast.success("Permission deleted successfully")
        except Exception as e:
            yield rx.toast.error(f"Failed to delete permission: {str(e)}")
        finally:
            self.perm_is_loading = False
