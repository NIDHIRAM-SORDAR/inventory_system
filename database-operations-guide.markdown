```markdown
# Database Operations & Audit Guidelines

This document outlines best practices for database operations and audit logging in the Reflex + SQLModel inventory system. Focus is on atomicity, comprehensive audit trails, and preventing partial updates.

## 1. Session Management & Transaction Scoping

**Always use explicit session scoping with proper error handling:**

```python
def update_user_email(self, user_id: int, new_email: str):
    auth_state = self.get_state(AuthState)
    with auth_state.audit_context():  # MODIFIED: Use instance method
        try:
            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo).filter_by(user_id=user_id).with_for_update()
                ).one()
                user_info.email = new_email
                session.add(user_info)
                session.commit()
                log.info("Email updated successfully", user_id=user_id)
                return rx.toast.success("Email updated successfully")
        except Exception as e:
            log.error("Failed to update email", user_id=user_id, error=str(e))
            session.rollback()
            return rx.toast.error(f"Failed to update email: {str(e)}")
```

**Rules:**
- Use `with rx.session() as session` for automatic transaction management
- Always rollback on exceptions
- Use `SELECT FOR UPDATE` for concurrent operations

## 2. Add, Flush, and Validate Pattern

**Ensure records are persisted before dependent operations:**

```python
def register(self, form_data: Dict[str, str]):
    auth_state = self.get_state(AuthState)
    with auth_state.audit_context():  # MODIFIED: Use instance method
        log.info("Starting user registration", username=form_data["username"])
        try:
            with rx.session() as session:
                # Step 1: Create and flush LocalUser
                local_user = LocalUser(
                    username=form_data["username"], 
                    email=form_data["email"], 
                    password=form_data["password"]
                )
                session.add(local_user)
                session.flush()  # Ensure ID is available
                log.debug("LocalUser created", user_id=local_user.id)
                
                # Step 2: Create and flush UserInfo
                user_info = UserInfo(user_id=local_user.id, email=form_data["email"])
                session.add(user_info)
                session.flush()  # Ensure queryable for set_roles
                log.debug("UserInfo created", user_info_id=user_info.id)
                
                # Step 3: Set roles (requires flushed UserInfo)
                user_info.set_roles(["employee"], session)
                session.commit()
                
                log.info("User registration completed successfully", 
                        user_id=local_user.id, username=form_data["username"])
                return rx.toast.success("Registration successful!")
                
        except Exception as e:
            log.error("User registration failed", 
                     username=form_data["username"], error=str(e))
            session.rollback()
            return rx.toast.error(f"Registration failed: {str(e)}")
```

**Rules:**
- Add records with `session.add(obj)`
- Flush with `session.flush()` before dependent operations
- Validate object state before proceeding

## 3. Comprehensive Audit Logging

### Using AuthState.audit_context() for Operation Tracking

**Model-Level Operations:**

```python
class UserInfo(SQLModel, table=True):
    def set_roles(self, role_names: List[str], session: Session, auth_state: 'AuthState') -> None:
        with auth_state.audit_context():  # MODIFIED: Use instance method
            log.info("Setting user roles", user_id=self.id, roles=role_names)
            
            if self.id is None:
                raise ValueError("UserInfo must be persisted to the session")
            
            # Validate roles exist
            roles = session.exec(select(Role).where(Role.name.in_(role_names))).all()
            if len(roles) != len(role_names):
                missing = set(role_names) - {r.name for r in roles}
                log.error("Roles not found", missing_roles=missing)
                raise ValueError(f"Roles not found: {missing}")
            
            # Atomic update
            session.exec(UserRole.__table__.delete().where(UserRole.user_id == self.id))
            for role in roles:
                session.add(UserRole(user_id=self.id, role_id=role.id))
            
            log.info("User roles updated successfully", user_id=self.id, roles=role_names)

class Role(SQLModel, table=True):
    def set_permissions(self, permission_names: List[str], session: Session, auth_state: 'AuthState') -> None:
        with auth_state.audit_context():  # MODIFIED: Use instance method
            log.info("Setting role permissions", role_id=self.id, permissions=permission_names)
            
            permissions = session.exec(
                select(Permission).where(Permission.name.in_(permission_names))
            ).all()
            if len(permissions) != len(permission_names):
                missing = set(permission_names) - {p.name for p in permissions}
                log.error("Permissions not found", missing_permissions=missing)
                raise ValueError(f"Permissions not found: {missing}")
            
            # Atomic update
            session.exec(RolePermission.__table__.delete().where(RolePermission.role_id == self.id))
            for perm in permissions:
                session.add(RolePermission(role_id=self.id, permission_id=perm.id))
            
            log.info("Role permissions updated successfully", role_id=self.id, permissions=permission_names)
```

**State-Level Operations:**

```python
class UserMgmtState(rx.State):
    def change_user_role(self, user_id: int, role_name: str):
        auth_state = self.get_state(AuthState)
        with auth_state.audit_context():  # MODIFIED: Use instance method
            log.info("Changing user role", user_id=user_id, new_role=role_name)
            
            try:
                with rx.session() as session:
                    user_info = session.exec(
                        select(UserInfo).filter_by(user_id=user_id).with_for_update()
                    ).one()
                    
                    old_roles = user_info.get_roles()
                    log.debug("Current user roles", user_id=user_id, current_roles=old_roles)
                    
                    user_info.set_roles([role_name], session, auth_state)
                    session.commit()
                    
                    log.info("User role changed successfully", 
                            user_id=user_id, old_roles=old_roles, new_role=role_name)
                    return rx.toast.success("Role updated successfully")
                    
            except Exception as e:
                log.error("Failed to change user role", 
                         user_id=user_id, role=role_name, error=str(e))
                return rx.toast.error(f"Failed to update role: {str(e)}")

    def approve_supplier(self, supplier_id: int):
        auth_state = self.get_state(AuthState)
        with auth_state.audit_context():  # MODIFIED: Use instance method
            log.info("Approving supplier", supplier_id=supplier_id)
            
            try:
                with rx.session() as session:
                    supplier = session.exec(
                        select(Supplier).filter_by(id=supplier_id).with_for_update()
                    ).one()
                    
                    log.debug("Supplier current status", 
                             supplier_id=supplier_id, current_status=supplier.status)
                    
                    supplier.status = "approved"
                    supplier.approved_at = datetime.utcnow()
                    session.add(supplier)
                    session.commit()
                    
                    log.info("Supplier approved successfully", supplier_id=supplier_id)
                    return rx.toast.success("Supplier approved")
                    
            except Exception as e:
                log.error("Failed to approve supplier", 
                         supplier_id=supplier_id, error=str(e))
                return rx.toast.error(f"Failed to approve supplier: {str(e)}")
```

### When to Use AuthState.audit_context()

**Use auth_state.audit_context() for:**
- **RBAC Operations**: `set_roles`, `set_permissions`, `change_user_role`
- **Critical Business Operations**: `approve_supplier`, `create_inventory_item`
- **User Management**: `register`, `update_profile`, `deactivate_user`
- **Financial Operations**: `process_payment`, `update_pricing`

**AuthState.audit_context() Usage:**
- Access via `auth_state = self.get_state(AuthState)` in State classes
- Use as a context manager with `with auth_state.audit_context():`
- Pass `auth_state` as a parameter to model methods for audit tracking
- # REMOVED: Parameters like `operation` and `**kwargs` are not used, as audit_context is a context manager that sets user context automatically

**Access Pattern:**

```python
# In State classes
auth_state = self.get_state(AuthState)
with auth_state.audit_context():  # MODIFIED: Use instance method
    # Database operations

# In Model methods (pass auth_state as parameter)
def model_method(self, session: Session, auth_state: 'AuthState'):
    with auth_state.audit_context():  # MODIFIED: Use instance method
        # Database operations
```

## 4. Atomic Operations with Bulk Processing

**Use bulk operations to minimize transaction scope:**

```python
def bulk_update_inventory(self, updates: List[Dict]):
    auth_state = self.get_state(AuthState)
    with auth_state.audit_context():  # MODIFIED: Use instance method
        log.info("Starting bulk inventory update", update_count=len(updates))
        
        try:
            with rx.session() as session:
                item_ids = [update["item_id"] for update in updates]
                items = session.exec(
                    select(InventoryItem).where(InventoryItem.id.in_(item_ids)).with_for_update()
                ).all()
                
                log.debug("Retrieved items for update", retrieved_count=len(items))
                
                item_map = {item.id: item for item in items}
                
                for update in updates:
                    item = item_map.get(update["item_id"])
                    if item:
                        item.quantity = update["quantity"]
                        session.add(item)
                
                session.commit()
                log.info("Bulk inventory update completed successfully", 
                        updated_count=len(updates))
                
        except Exception as e:
            log.error("Bulk inventory update failed", 
                     update_count=len(updates), error=str(e))
            session.rollback()
            raise
```

## 5. Error Handling and Recovery

**Comprehensive error handling with detailed logging:**

```python
def complex_operation(self, data: Dict):
    auth_state = self.get_state(AuthState)
    operation_id = generate_operation_id()
    with auth_state.audit_context():  # MODIFIED: Use instance method
        log.info("Starting complex operation", operation_id=operation_id, data_keys=list(data.keys()))
        
        try:
            with rx.session() as session:
                # Step 1
                log.debug("Executing step 1", operation_id=operation_id)
                result1 = perform_step1(data, session)
                session.flush()
                
                # Step 2
                log.debug("Executing step 2", operation_id=operation_id)
                result2 = perform_step2(result1, session)
                session.flush()
                
                # Step 3
                log.debug("Executing step 3", operation_id=operation_id)
                final_result = perform_step3(result2, session)
                
                session.commit()
                log.info("Complex operation completed successfully", 
                        operation_id=operation_id, result=final_result)
                return rx.toast.success("Operation completed")
                
        except ValidationError as e:
            log.warning("Validation error in complex operation", 
                       operation_id=operation_id, validation_error=str(e))
            session.rollback()
            return rx.toast.error(f"Validation failed: {str(e)}")
            
        except DatabaseError as e:
            log.error("Database error in complex operation", 
                     operation_id=operation_id, db_error=str(e))
            session.rollback()
            return rx.toast.error("Database operation failed")
            
        except Exception as e:
            log.error("Unexpected error in complex operation", 
                     operation_id=operation_id, error=str(e), error_type=type(e).__name__)
            session.rollback()
            return rx.toast.error("Operation failed unexpectedly")
```

## 6. Concurrent Operation Safety

**Use SELECT FOR UPDATE for race condition prevention:**

```python
def transfer_inventory(self, from_item_id: int, to_item_id: int, quantity: int):
    auth_state = self.get_state(AuthState)
    with auth_state.audit_context():  # MODIFIED: Use instance method
        log.info("Starting inventory transfer", 
                from_item=from_item_id, to_item=to_item_id, quantity=quantity)
        
        try:
            with rx.session() as session:
                # Lock both items to prevent concurrent modifications
                items = session.exec(
                    select(InventoryItem)
                    .where(InventoryItem.id.in_([from_item_id, to_item_id]))
                    .with_for_update()
                ).all()
                
                if len(items) != 2:
                    log.error("Items not found for transfer", 
                             found_items=len(items), expected=2)
                    raise ValueError("One or both items not found")
                
                from_item = next(item for item in items if item.id == from_item_id)
                to_item = next(item for item in items if item.id == to_item_id)
                
                log.debug("Current quantities", 
                         from_quantity=from_item.quantity, to_quantity=to_item.quantity)
                
                if from_item.quantity < quantity:
                    log.warning("Insufficient quantity for transfer", 
                               available=from_item.quantity, requested=quantity)
                    raise ValueError("Insufficient quantity")
                
                from_item.quantity -= quantity
                to_item.quantity += quantity
                
                session.add_all([from_item, to_item])
                session.commit()
                
                log.info("Inventory transfer completed successfully", 
                        from_item=from_item_id, to_item=to_item_id, quantity=quantity)
                return rx.toast.success("Transfer completed")
                
        except Exception as e:
            log.error("Inventory transfer failed", 
                     from_item=from_item_id, to_item=to_item_id, 
                     quantity=quantity, error=str(e))
            session.rollback()
            return rx.toast.error(f"Transfer failed: {str(e)}")
```

## 7. Testing Database Operations

**Write comprehensive tests with proper audit validation:**

```python
def test_user_registration_with_audit(session):
    with patch('your_module.log') as mock_log:
        # Setup
        role = Role(name="employee", description="Test role")
        session.add(role)
        session.flush()
        
        # Execute
        result = register_user({
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }, session)
        
        # Verify database state
        user = session.exec(select(LocalUser).where(LocalUser.username == "testuser")).one()
        user_info = session.exec(select(UserInfo).where(UserInfo.user_id == user.id)).one()
        
        assert "employee" in user_info.get_roles()
        
        # Verify audit logs
        mock_log.info.assert_any_call("Starting user registration", username="testuser")
        mock_log.info.assert_any_call("User registration completed successfully", 
                                     user_id=user.id, username="testuser")

def test_concurrent_role_change(session):
    """Test race condition handling in role changes"""
    user_info = create_test_user_info(session)
    
    def change_role_worker(role_name):
        with rx.session() as worker_session:
            user = worker_session.exec(
                select(UserInfo).filter_by(id=user_info.id).with_for_update()
            ).one()
            user.set_roles([role_name], worker_session)
            worker_session.commit()
    
    # Simulate concurrent access
    import threading
    threads = [
        threading.Thread(target=change_role_worker, args=("admin",)),
        threading.Thread(target=change_role_worker, args=("manager",))
    ]
    
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Verify final state is consistent
    final_roles = user_info.get_roles()
    assert len(final_roles) == 1  # Should have exactly one role
```

## Key Principles Summary

1. **Session Scoping**: Always use `with rx.session() as session`
2. **Add-Flush-Validate**: Add records, flush before dependent operations, validate state
3. **Comprehensive Logging**: Log before/after operations with audit_context()
4. **Atomic Operations**: Group related changes in single transactions
5. **Error Handling**: Catch specific exceptions, rollback on errors
6. **Concurrency Safety**: Use `SELECT FOR UPDATE` for race-sensitive operations
7. **Audit Compliance**: Use auth_state.audit_context() for all RBAC and critical operations

**AuthState.audit_context() Usage:**
- Wrap all RBAC operations (`set_roles`, `set_permissions`)
- Wrap critical business operations (`approve_supplier`, `process_payment`)
- Wrap complex multi-step operations
- # NEW: Use as an instance method via `with auth_state.audit_context():`, which sets user context automatically based on the authenticated user
- Access via `auth_state = self.get_state(AuthState)` in State classes
- Pass auth_state as parameter to model methods for audit tracking
```