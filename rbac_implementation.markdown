# Role-Based Access Control (RBAC) Implementation

## Overview

This document describes the implementation of Role-Based Access Control (RBAC) in the inventory system, replacing legacy flag-based authorization (e.g., `is_admin`, `is_supplier`) with a flexible role and permission model. The RBAC system supports roles (`admin`, `employee`, `supplier`) and permissions (`manage_users`, `manage_suppliers`, `view_inventory`, etc.), enabling fine-grained access control.

## Models

The RBAC system is built on SQLModel models defined in `inventory_system/models/user.py`:

- **UserInfo**:
  - Stores user metadata (e.g., `email`, `user_id`).
  - Links to roles via the `UserRole` association table.
  - Methods:
    - `get_roles() -> list[str]`: Retrieves the user's roles (e.g., `["admin", "employee"]`).
    - `set_roles(role_names: list[str], session: Session)`: Assigns roles atomically, using `SELECT FOR UPDATE` to prevent race conditions.
- **Role**:
  - Defines roles (e.g., `name="admin"`, `description="Administrator role"`).
  - Links to permissions via the `RolePermission` association table.
  - Methods:
    - `get_permissions() -> list[str]`: Retrieves the role's permissions (e.g., `["manage_users", "view_inventory"]`).
    - `set_permissions(permission_names: list[str], session: Session)`: Assigns permissions atomically with `SELECT FOR UPDATE`.
- **Permission**:
  - Defines permissions (e.g., `name="manage_users"`, `description="Manage user accounts"`).
  - Linked to roles via `RolePermission`.
- **UserRole**:
  - Association table mapping `UserInfo` to `Role` (composite key: `user_id`, `role_id`).
- **RolePermission**:
  - Association table mapping `Role` to `Permission` (composite key: `role_id`, `permission_id`).

## Role and Permission Management

- **Roles**: `admin`, `employee`, `supplier` (lowercase, per convention).
- **Permissions**: Include `manage_users`, `manage_suppliers`, `view_inventory`, `create_inventory`, `update_inventory`, `delete_inventory`, and more (seeded via `seed_permissions.py`).
- **Assignment**:
  - Roles are assigned to users via `UserInfo.set_roles` (e.g., `user.set_roles(["admin"], session)`).
  - Permissions are assigned to roles via `Role.set_permissions` (e.g., `role.set_permissions(["manage_users"], session)`).
- **State Handlers**:
  - `user_mgmt_state.py`: `change_user_role` uses `set_roles` to update user roles.
  - `supplier_approval_state.py`: `approve_supplier` assigns the `supplier` role to new users.
  - `admin_state.py`: Displays user roles and supplier statuses, using `get_roles`.

## Race Condition Protections

To prevent race conditions in concurrent role or permission assignments:

- **Locking**:
  - `UserInfo.set_roles` and `Role.set_permissions` use `SELECT FOR UPDATE` to lock the respective records (`UserInfo` or `Role`) during updates.
  - `user_mgmt_state.py`: `change_user_role` and `delete_user` use `SELECT FOR UPDATE` on `UserInfo`.
  - `supplier_approval_state.py`: `approve_supplier`, `revoke_supplier`, and `delete_supplier` use `SELECT FOR UPDATE` on `Supplier` and `UserInfo` (when applicable).
- **Transactions**:
  - All database operations use `with rx.session() as session` for atomicity, with automatic rollbacks on errors.
- **Testing**:
  - `test_concurrent_role_assignment` in `test_permission.py` verifies atomicity using an in-memory SQLite database.
  - Production testing is planned with PostgreSQL, using tools like Locust to simulate concurrent `change_user_role` or `approve_supplier` calls.
- **Future Considerations**:
  - If deadlocks occur in production, optimistic locking (e.g., a version column) may be added in **Step 6**.

## Audit Logging

Audit logging, implemented in `inventory_system/logging/audit.py`, tracks all role and permission changes:

- **Events**:
  - `create_userrole`, `create_rolepermission`: Log role/permission assignments.
  - `update_userinfo`, `delete_userinfo`: Log user updates/deletions.
  - `attempt_change_role`, `success_change_role`, `fail_change_role`: Log role changes in `user_mgmt_state.py`.
  - `attempt_approve_supplier`, `success_approve_supplier_new_user`, etc.: Log supplier actions in `supplier_approval_state.py`.
- **Handling Association Tables**:
  - `UserRole` and `RolePermission` lack a single `id` field, so composite keys (e.g., `f"{user_id}-{role_id}"`) are used for `entity_id`.
- **Tests**:
  - `test_audit_logging_roles` and `test_audit_logging_permissions` verify logging for `UserRole` and `RolePermission` changes.

## State and Authorization Updates

- **user_mgmt_state.py**:
  - Replaced `is_admin` with `"manage_users" in get_permissions()` for authorization.
  - Uses `set_roles` for role updates, ensuring atomicity.
- **supplier_approval_state.py**:
  - Replaced `is_admin` with `"manage_suppliers" in get_permissions()`.
  - Assigns `supplier` role atomically in `approve_supplier`.
- **admin_state.py**:
  - Replaced `is_admin` with `"manage_users" or "manage_suppliers" in get_permissions()`.
  - Displays single roles (temporary, pending multi-role support in **Step 6**).
- **auth_state.py** (assumed):
  - Removed `is_admin` flag, relying on `get_permissions` for authorization.

## Testing

- **Unit Tests** (`test_permission.py`):
  - `test_create_permission`, `test_unique_permission_name`, `test_update_timestamp`: Verify `Permission` model.
  - `test_permission_deletion_cascade`: Ensures cascading deletes for `RolePermission`.
  - `test_role_permissions_relationship`, `test_role_users_relationship`: Verify many-to-many relationships.
  - `test_userinfo_roles`, `test_role_permissions`: Test `get_roles`, `set_roles`, `get_permissions`, `set_permissions`.
  - `test_concurrent_role_assignment`: Verifies atomic role assignments.
  - `test_audit_logging_roles`, `test_audit_logging_permissions`: Verify audit logging.
- **Production Testing**:
  - Planned for PostgreSQL environment to simulate concurrent role assignments and supplier approvals.

## ## Step 4: Implement Permission Checks

**Status**: Completed  
**Details**:  

- Added `get_permissions()` to `UserInfo` to aggregate permissions from roles.  
- Added `has_permission(permission_name: str) -> bool` to `UserInfo` for permission checks.  
- Added `user_permissions` computed var to `AuthState` for state class access.  
- Optimized with `selectinload` for permission queries.  
- Existing tests in `test_permission.py` passed; concurrency testing deferred to production.  

## Next Steps

- 
- **Step 5: Update Authorization Logic**:
  - Ensure all pages/routes check permissions via `get_permissions`.
  - Update `auth_state.py` (if exists) for permission-based authorization.
- **Step 6: Implement Role Management**:
  - Extend `user_mgmt_state.py` and `user_management.py` (if exists) for multi-role assignments.
  - Add UI for role/permission management (e.g., multi-select dropdowns).
- **Step 7: Extend User Management**:
  - Update UI to display multiple roles and permissions.
  - Add bulk role/permission assignment features.
- **Production Testing**:
  - Deploy to staging and use Locust to test concurrent role assignments and supplier actions.
  - Monitor audit logs for errors or unexpected overwrites.

## Notes

- All role names are lowercase (`admin`, `employee`, `supplier`) per convention.
- Reflex best practices are followed:
  - `@rx.event` for event handlers.
  - `setvar` for state updates.
  - No awaiting event handlers; `yield` for async updates.
  - Error handling with `try-except` and `rx.toast` for user feedback.
- The system is designed to support PostgreSQL in production, with `SELECT FOR UPDATE` ensuring concurrency safety.
