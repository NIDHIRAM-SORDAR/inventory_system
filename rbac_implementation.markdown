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

## Step 4: Implement Permission Checks
**Status**: Completed  
**Details**:  
- Added `get_permissions()` and `has_permission()` to `UserInfo`.  
- Added `user_permissions` to `AuthState` with eager loading.  
- Enhanced `seed_permissions.py` with action-specific permissions (e.g., `view_supplier`, `delete_user`) and legacy permissions (`manage_users`, `manage_suppliers`).  
- Created `seed_roles.py` for `admin`, `employee`, `supplier`, `inventory_manager`, `supplier_manager`, `auditor` roles.  
- Updated `test_permission.py` with tests for new permissions and roles.  

## Next Steps

- 
# Step 5: Transition to Permission-Based Authorization - Status and Completion

## Overview
Step 5 focuses on updating the inventory system's authorization logic to replace legacy flag-based checks (e.g., `is_admin`, `is_supplier`) with permission-based checks, aligning with the Role-Based Access Control (RBAC) system. This step enhances security, scalability, and maintainability in a multi-user environment. Below is the status of completion, detailing what has been accomplished and what remains to be done before moving to Step 6.

## Completion Status

### Completed Tasks
The following components have been successfully updated to use permission-based authorization, ensuring alignment with Reflex best practices for state management, event handling, and responsive UI:

1. **Authentication and Registration Modules**  
   - **Status**: Completed  
   - **Files Updated**: `auth.py`, `register_state.py`, `register.py`, `supplier_register_state.py`, `supplier_register.py`  
   - **Details**: 
     - Replaced flag-based checks with permission checks using `set_roles` and `get_permissions()`. 
     - Registration logic assigns roles like `"employee"` or defers to approval for suppliers, supporting RBAC. 
     - UI components use `rx.cond` for conditional rendering, with responsive design (e.g., `width=["100%", "50%"]`) and dark/light theme support. 
     - Optimistic updates (e.g., `is_submitting=True`) enhance UX.  
   - **RBAC Alignment**: Fully transitioned to permission-based checks, ensuring secure user creation and role assignment.

2. **Login and Logout Functionality**  
   - **Status**: Completed  
   - **Files Updated**: `login_state.py`, `logout_state.py`, `login.py`, `logout.py`  
   - **Details**: 
     - Updated redirection logic to use permissions (e.g., `"manage_users"`) instead of flags like `is_admin`. 
     - Logout remains permission-agnostic, as appropriate. 
     - UI components use `rx.cond` for reactive feedback (e.g., spinners, toasts), with responsive design and theme support. 
     - Optimistic updates improve perceived performance.  
   - **RBAC Alignment**: All flag-based checks removed, ensuring secure access control.

3. **Profile Management Interfaces**  
   - **Status**: Completed  
   - **Files Updated**: `profile_input.py`, `profile.py`, `profile_picture_state.py`, `profile_state.py`  
   - **Details**: 
     - Profile management inherently RBAC-compatible, with no flag-based checks. 
     - Uses `user_roles` from `get_roles()`, rendered as badges with `rx.foreach`. 
     - UI is responsive (e.g., `flex_direction=["column", "column", "row"]`) and theme-aware. 
     - Optimistic updates (e.g., loading states) implemented.  
   - **RBAC Alignment**: No changes needed, fully aligned with permission-based system.

4. **Supplier Approval Processes**  
   - **Status**: Completed  
   - **Files Updated**: `supplier_approval.py`, `supplier_approval_state.py`  
   - **Details**: 
     - Introduced granular permissions: `"manage_suppliers"` (view), `"manage_supplier_approval"` (approve/revoke), `"delete_supplier"` (delete). 
     - State methods use `with_for_update()` for race condition handling. 
     - UI conditionally renders action buttons with `rx.cond` based on permissions, maintaining responsive design (e.g., `max_width=["90vw", "500px"]`) and theme support. 
     - Optimistic updates (e.g., `is_loading=True`) ensure smooth UX.  
   - **RBAC Alignment**: All actions permission-gated, flag-based checks eliminated.

5. **User Management Tools**  
   - **Status**: Completed  
   - **Files Updated**: `user_mgmt_state.py`, `user_management.py`  
   - **Details**: 
     - Implemented permissions: `"manage_users"` (view), `"edit_user"` (role changes), `"delete_user"` (delete). 
     - State methods use `with_for_update()` for race condition handling. 
     - UI conditionally renders edit/delete buttons with `rx.cond`, ensuring responsive design and theme support. 
     - Optimistic updates (e.g., `is_loading=True`) enhance performance.  
   - **RBAC Alignment**: Fully transitioned to permission-based checks, ensuring granular access control.

6. **Supporting Infrastructure**  
   - **Status**: Completed  
   - **Files Reviewed**: `seed_permissions.py`, `seed_roles.py`  
   - **Details**: 
     - These files define initial permissions and roles, supporting the RBAC system across the application. 
     - No updates were needed, as they are already aligned with the permission-based approach.  
   - **RBAC Alignment**: Provides the foundation for permission checks implemented in other modules.

### Remaining Tasks
The following tasks must be completed to finalize Step 5 and ensure a robust RBAC implementation before proceeding to Step 6:

1. **Update Navigation Bar and Sidebar**  
   - **Status**: Pending  
   - **Details**: 
     - The navigation bar and sidebar likely contain menu items or links that need conditional rendering based on user permissions (e.g., showing "Admin" only for users with `"manage_users"`). 
     - Updates should use `rx.cond` for permission checks, ensuring responsive design (mobile/desktop) and theme support (dark/light modes). 
     - This is critical for a consistent and secure user experience, preventing unauthorized access to restricted areas.  
   - **Action Required**: Review and update the relevant files (e.g., `navbar.py`, `sidebar.py`) in a separate conversation, as specified by the user.

2. **Final Code Audit**  
   - **Status**: Pending  
   - **Details**: 
     - Although all specified files have been updated, a comprehensive audit is recommended to ensure no residual flag-based checks (e.g., `is_admin`, `is_supplier`) remain in the codebase. 
     - This involves searching the entire codebase for legacy terms and verifying all authorization logic uses permissions.  
   - **Action Required**: Conduct a codebase-wide search and review to confirm complete transition to RBAC.

3. **Testing Verification**  
   - **Status**: Pending  
   - **Details**: 
     - Tests, particularly those in `test_permission.py`, need to be run to validate the permission-based authorization. 
     - This includes testing edge cases like multi-role users, permission denial scenarios, and UI rendering under different permissions. 
     - Ensures the RBAC system functions correctly across all updated modules.  
   - **Action Required**: Execute test suite and verify all permission-related tests pass, addressing any failures.

## Summary Table

| **Component**                  | **Status** | **Details**                                                                 |
|--------------------------------|------------|-----------------------------------------------------------------------------|
| Authentication & Registration  | Completed  | Uses `set_roles`, permission checks, responsive UI with optimistic updates. |
| Login & Logout                 | Completed  | Permission-based redirection, reactive UI, theme support.                   |
| Profile Management             | Completed  | No flag checks, uses `user_roles`, responsive and theme-aware.              |
| Supplier Approval              | Completed  | Granular permissions, race condition handling, permission-gated UI.         |
| User Management                | Completed  | Granular permissions, race condition handling, permission-gated UI.         |
| Supporting Infrastructure       | Completed  | `seed_permissions.py`, `seed_roles.py` support RBAC, no changes needed.     |
| Navigation Bar & Sidebar       | Pending    | Needs permission-based rendering, to be addressed separately.               |
| Final Code Audit               | Pending    | Ensure no residual flag-based checks remain.                                |
| Testing Verification           | Pending    | Run tests, validate permission logic and edge cases.                       |

## Conclusion
Step 5 is nearly complete, with all specified files (except navigation bar and sidebar) updated to use permission-based authorization. The system now leverages granular permissions, race condition handling, and responsive UI, aligning with Reflex best practices. Completing the remaining tasks—updating the navigation bar and sidebar, conducting a final code audit, and verifying tests—will finalize Step 5, ensuring a secure and robust RBAC implementation. Once these are addressed, the project can confidently proceed to Step 6, likely focusing on role management enhancements.

## Next Steps
- **Immediate Action**: Address navigation bar and sidebar updates in a separate conversation, as planned.
- **Follow-Up**: Perform the final code audit and run tests to confirm RBAC integrity.
- **Transition**: Move to Step 6 after completing all pending tasks, ensuring a smooth progression in the RBAC implementation.
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
