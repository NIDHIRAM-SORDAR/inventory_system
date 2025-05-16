# Database Operation Guidelines for Inventory System

This document outlines best practices for performing database operations in the inventory system project, built with Reflex and SQLModel. The goal is to ensure atomicity, prevent partial updates, maintain RBAC compliance, and support responsive UI with dark/light theme compatibility. These guidelines apply to all database interactions, including user registration, role management, supplier approvals, and inventory operations.

## 1. Use Explicit Session Scoping
- **Purpose**: Ensure all database operations are atomic by wrapping them in a single transaction scope, preventing partial commits.
- **Rules**:
  - Always use `with rx.session() as session` for database operations to manage transactions automatically.
  - Avoid reusing sessions across unrelated operations to prevent unintended side effects.
  - Commit the session only after all operations succeed; rollback on errors.
- **Example**:
  ```python
  @rx.background
  async def update_user_email(self, user_id: int, new_email: str):
      try:
          with rx.session() as session:
              user_info = session.exec(
                  select(UserInfo).filter_by(user_id=user_id).with_for_update()
              ).one()
              user_info.email = new_email
              session.add(user_info)
              session.commit()
              return rx.toast.success("Email updated successfully")
      except Exception as e:
          session.rollback()
          return rx.toast.error(f"Failed to update email: {str(e)}")
  ```
- **Why**: The `with` block ensures commits or rollbacks are handled consistently, maintaining database integrity.
- **RBAC Context**: Use `SELECT FOR UPDATE` for operations like `set_roles` or `change_user_role` to prevent concurrent RBAC updates.

## 2. Add and Flush Dependent Records Before Operations
- **Purpose**: Ensure records are persisted to the database before performing operations that query them, avoiding errors like `No row was found`.
- **Rules**:
  - Add records to the session with `session.add(obj)` before operations that depend on their existence (e.g., `set_roles`, `set_permissions`).
  - Flush the session with `session.flush()` to write records to the database without committing the transaction.
  - Minimize flushes to only when necessary (e.g., to obtain an ID or ensure queryability).
- **Example** (Registration):
  ```python
  @rx.background
  async def register(self, form_data: Dict[str, str]):
      try:
          with rx.session() as session:
              local_user = LocalUser(username=form_data["username"], email=form_data["email"], password=form_data["password"])
              session.add(local_user)
              session.flush()  # Ensure local_user.id is set
              
              user_info = UserInfo(user_id=local_user.id, email=form_data["email"])
              session.add(user_info)
              session.flush()  # Ensure UserInfo is queryable
              
              user_info.set_roles(["employee"], session)
              session.commit()
              return rx.toast.success("Registration successful!")
      except Exception as e:
          session.rollback()
          return rx.toast.error(f"Registration failed: {str(e)}")
  ```
- **Why**: Flushing ensures records are available for queries (e.g., `SELECT FOR UPDATE` in `set_roles`), preventing errors like those seen in the audit log (`Failed to set roles: No row was found`).
- **RBAC Context**: Always flush `UserInfo` before calling `set_roles` or `UserRole` operations to ensure RBAC assignments are queryable.

## 3. Validate Object State and Dependencies
- **Purpose**: Prevent operations on unpersisted or invalid objects, ensuring all dependencies (e.g., roles, users) exist before proceeding.
- **Rules**:
  - Check that objects have valid IDs (e.g., `obj.id is not None`) before operations that require persistence.
  - Validate dependent records (e.g., roles, permissions) exist using a single query where possible.
  - Raise specific errors for missing dependencies to aid debugging.
- **Example** (In `UserInfo.set_roles`):
  ```python
  def set_roles(self, role_names: List[str], session: Session) -> None:
      if self.id is None:
          raise ValueError("UserInfo must be persisted to the session")
      
      user_info = session.exec(
          select(UserInfo).where(UserInfo.id == self.id).with_for_update()
      ).one_or_none()
      if not user_info:
          raise ValueError(f"UserInfo with id={self.id} not found")
      
      roles = session.exec(select(Role).where(Role.name.in_(role_names))).all()
      if len(roles) != len(role_names):
          missing = set(role_names) - {r.name for r in roles}
          raise ValueError(f"Roles not found: {missing}")
      
      session.exec(UserRole.__table__.delete().where(UserRole.user_id=self.id))
      for role in roles:
          session.add(UserRole(user_id=self.id, role_id=role.id))
  ```
- **Why**: Validation catches issues early, preventing cryptic database errors and ensuring RBAC operations (e.g., role assignments) are valid.
- **RBAC Context**: Validate roles and permissions exist before assigning them to users or roles, as seen in `manage_users` or `manage_roles`.

## 4. Perform Operations Atomically
- **Purpose**: Minimize the risk of partial updates by grouping related database changes in a single transaction and reducing intermediate states.
- **Rules**:
  - Use bulk operations (e.g., `in_` queries, batch inserts) to reduce database round-trips and intermediate states.
  - Avoid deleting and re-adding records unless necessary; consider updating existing records where possible.
  - Use `SELECT FOR UPDATE` for concurrency-sensitive operations to prevent race conditions.
- **Example** (Batch Role Assignment):
  ```python
  def set_permissions(self, permission_names: List[str], session: Session) -> None:
      permissions = session.exec(
          select(Permission).where(Permission.name.in_(permission_names))
      ).all()
      if len(permissions) != len(permission_names):
          missing = set(permission_names) - {p.name for p in permissions}
          raise ValueError(f"Permissions not found: {missing}")
      
      session.exec(RolePermission.__table__.delete().where(RolePermission.role_id == self.id))
      for perm in permissions:
          session.add(RolePermission(role_id=self.id, permission_id=perm.id))
  ```
- **Why**: Atomic operations reduce the window for partial updates, ensuring RBAC assignments are consistent.
- **RBAC Context**: Use bulk deletes and inserts for `UserRole` and `RolePermission` tables to maintain atomicity in `set_roles` and `set_permissions`.

## 5. Implement Comprehensive Error Handling and Logging
- **Purpose**: Catch and handle errors gracefully, providing detailed audit logs to diagnose issues like partial updates or missing records.
- **Rules**:
  - Wrap all database operations in `try-except` blocks, rolling back the session on errors.
  - Log success and failure events with detailed context (e.g., user ID, parameters, error messages).
  - Use `rx.toast` for user-facing error messages, ensuring responsiveness.
  - Integrate with the project’s audit logging system (e.g., `audit.py`).
- **Example** (Registration with Logging):
  ```python
  @rx.background
  async def register(self, form_data: Dict[str, str]):
      try:
          with rx.session() as session:
              local_user = LocalUser(username=form_data["username"], email=form_data["email"])
              session.add(local_user)
              session.flush()
              
              user_info = UserInfo(user_id=local_user.id, email=form_data["email"])
              session.add(user_info)
              session.flush()
              
              user_info.set_roles(["employee"], session)
              session.commit()
              
              log.info("registration_success", username=form_data["username"], user_id=local_user.id)
              return rx.toast.success("Registration successful!")
      except Exception as e:
          log.error("registration_failed", username=form_data["username"], error=str(e))
          session.rollback()
          return rx.toast.error(f"Registration failed: {str(e)}")
  ```
- **Why**: Detailed logs (e.g., `audit_2025-04-28.log`) help diagnose issues like the `No row was found` error, and user feedback maintains a responsive UI.
- **RBAC Context**: Log all RBAC operations (e.g., `set_roles`, `change_user_role`) to track permission changes, as required by the audit system.

## 6. Use Optimistic Updates with UI Feedback
- **Purpose**: Improve perceived performance by updating the UI optimistically while ensuring errors are handled gracefully.
- **Rules**:
  - Set a loading state (e.g., `is_submitting`) before database operations.
  - Update state optimistically where safe, reverting on errors.
  - Use `yield` for sequential UI updates in async handlers.
  - Reset loading states in `finally` blocks to ensure UI consistency.
- **Example** (User Role Update):
  ```python
  class UserMgmtState(rx.State):
      is_submitting: bool = False

      @rx.background
      async def change_user_role(self, user_id: int, role_name: str):
          self.set_is_submitting(True)
          try:
              with rx.session() as session:
                  user_info = session.exec(
                      select(UserInfo).filter_by(user_id=user_id).with_for_update()
                  ).one()
                  user_info.set_roles([role_name], session)
                  session.commit()
                  yield rx.toast.success("Role updated successfully")
          except Exception as e:
              yield rx.toast.error(f"Failed to update role: {str(e)}")
          finally:
              self.set_is_submitting(False)
  ```
- **Why**: Optimistic updates enhance UX, and error handling ensures the UI reflects the true state, supporting mobile and desktop responsiveness.
- **RBAC Context**: Use optimistic updates for RBAC operations like `manage_users` or `approve_supplier`, ensuring immediate feedback.

## 7. Write Comprehensive Unit Tests
- **Purpose**: Validate database operations and catch issues like partial updates, missing records, or concurrency problems.
- **Rules**:
  - Write tests for success and failure cases, including edge cases (e.g., missing roles, unpersisted objects).
  - Use `pytest.raises` to verify expected exceptions.
  - Simulate concurrent operations to test `SELECT FOR UPDATE` behavior.
  - Include tests in `test_permission.py` for RBAC operations.
- **Example** (Test Registration):
  ```python
  def test_user_registration(session):
      role = Role(name="employee", description="Test role")
      session.add(role)
      session.flush()
      
      local_user = LocalUser(username="testuser", email="test@example.com")
      session.add(local_user)
      session.flush()
      
      user_info = UserInfo(user_id=local_user.id, email="test@example.com")
      session.add(user_info)
      session.flush()
      
      user_info.set_roles(["employee"], session)
      session.commit()
      
      assert "employee" in user_info.get_roles()

  def test_set_roles_unpersisted(session):
      user_info = UserInfo(user_id=1, email="test@example.com")
      with pytest.raises(ValueError, match="UserInfo must be persisted"):
          user_info.set_roles(["employee"], session)
  ```
- **Why**: Tests ensure operations are atomic and handle errors correctly, preventing issues like those in the audit log.
- **RBAC Context**: Test all RBAC operations (e.g., `set_roles`, `set_permissions`, `change_user_role`) to validate permission assignments.

## 8. Monitor and Audit Concurrent Operations
- **Purpose**: Detect and resolve issues with concurrent database operations, especially for RBAC-sensitive actions.
- **Rules**:
  - Log all database operations with timestamps, user IDs, and parameters in `audit.log`.
  - Use `SELECT FOR UPDATE` for concurrency-sensitive operations to prevent race conditions.
  - Simulate concurrent operations in staging using tools like Locust.
  - Review audit logs regularly for patterns of failures (e.g., `No row was found`).
- **Example** (Concurrent Role Change):
  ```python
  @rx.background
  async def change_user_role(self, user_id: int, role_name: str):
      try:
          with rx.session() as session:
              user_info = session.exec(
                  select(UserInfo).filter_by(user_id=user_id).with_for_update()
              ).one()
              user_info.set_roles([role_name], session)
              session.commit()
              log.info("role_change_success", user_id=user_id, role_name=role_name)
              return rx.toast.success("Role updated")
      except Exception as e:
          log.error("role_change_failed", user_id=user_id, role_name=role_name, error=str(e))
          return rx.toast.error(f"Failed to update role: {str(e)}")
  ```
- **Why**: Monitoring ensures RBAC operations are safe under concurrent loads, as required by the project’s audit system.
- **RBAC Context**: Audit logs must capture all RBAC changes (e.g., `create_userrole`, `delete_rolepermission`) for compliance.

## 9. Optimize for Performance
- **Purpose**: Ensure database operations are efficient to maintain responsive UI, especially for mobile and desktop users.
- **Rules**:
  - Use bulk queries (e.g., `in_` clauses) to reduce database round-trips.
  - Avoid unnecessary flushes or commits within loops.
  - Index frequently queried columns (e.g., `UserInfo.user_id`, `Role.name`) in the database schema.
  - Cache static data (e.g., role/permission lists) in state where appropriate.
- **Example** (Bulk Role Validation):
  ```python
  def set_roles(self, role_names: List[str], session: Session) -> None:
      roles = session.exec(select(Role).where(Role.name.in_(role_names))).all()
      if len(roles) != len(role_names):
          missing = set(role_names) - {r.name for r in roles}
          raise ValueError(f"Roles not found: {missing}")
      session.exec(UserRole.__table__.delete().where(UserRole.user_id=self.id))
      for role in roles:
          session.add(UserRole(user_id=self.id, role_id=role.id))
  ```
- **Why**: Efficient queries reduce latency, supporting Reflex’s responsive UI requirements and dark/light theme transitions.
- **RBAC Context**: Optimize RBAC queries (e.g., `permissions`) to ensure fast permission checks for UI rendering.

## 10. Document and Enforce Guidelines
- **Purpose**: Ensure all developers follow consistent database operation patterns to maintain code quality and prevent errors.
- **Rules**:
  - Document all database operation patterns in this file (`DATABASE_OPERATIONS.md`).
  - Include examples for common operations (e.g., registration, role assignment, supplier approval).
  - Enforce guidelines through code reviews and CI checks.
  - Provide onboarding materials referencing this document.
- **Example** (Documentation Snippet):
  ```markdown
  ### User Registration
  - Add and flush `LocalUser` and `UserInfo` before `set_roles`.
  - Example:
    ```python
    session.add(local_user)
    session.flush()
    user_info = UserInfo(user_id=local_user.id)
    session.add(user_info)
    session.flush()
    user_info.set_roles(["employee"], session)
    session.commit()
    ```
  ```
- **Why**: Consistent patterns reduce errors like those in the audit log and ensure RBAC compliance.
- **RBAC Context**: Document RBAC-specific patterns (e.g., `set_roles`, `set_permissions`) to ensure secure permission management.

## Additional Notes
- **Responsive Design**: Ensure database operations are wrapped in `@rx.background` but remeber to pros and cons of https://reflex.dev/docs/events/background-events/ and also to keep the UI responsive, supporting mobile and desktop breakpoints (see [Reflex Breakpoints](https://reflex.dev/docs/styling/responsive/)).
--**Read How Reflex works**:https://reflex.dev/docs/advanced-onboarding/how-reflex-works/#event-processing
- **Dark/Light Theme**: Use `rx.color_mode_cond` for UI components affected by database operations to maintain theme consistency.
- **Audit Compliance**: All RBAC operations must log to `audit.log` with sufficient detail (e.g., user ID, role names, timestamps) to meet audit requirements.
- **Testing**: Use `pytest` with `sqlmodel` fixtures to test all database operations, ensuring coverage for RBAC scenarios (e.g., `test_permission.py`).

By adhering to these guidelines, the inventory system will maintain a robust, secure, and responsive database layer, preventing issues like partial updates and ensuring seamless RBAC integration.