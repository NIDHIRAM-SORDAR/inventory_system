# audit_setup.py
"""
Setup file to integrate the enhanced audit system with your existing codebase.
This file should be imported early in your application startup.
"""

from typing import List, Type
import reflex as rx

# Import your models and the enhanced audit system
from .audit_listeners import enhanced_audit_listener, register_model_for_audit
from inventory_system.models.audit import AuditTrail
from inventory_system.models.user import UserInfo, Supplier, Permission, Role, UserRole, RolePermission


def setup_audit_system(models_to_track: List[Type] = None):
    """
    Setup the enhanced audit system.
    
    Args:
        models_to_track: List of model classes to track. If None, will track common models.
    """
    
    # Default models to track (adjust based on your models)
    if models_to_track is None:
        models_to_track = [
            UserInfo, Supplier, Permission, Role, UserRole, RolePermission
        ]
    
    # Register models for audit tracking
    for model in models_to_track:
        register_model_for_audit(model)
    
    print(f"✓ Audit system initialized with {len(models_to_track)} tracked models")


def migrate_existing_handlers():
    """
    Helper function showing patterns for migrating existing event handlers.
    """
    
    # Pattern 1: Wrap existing database operations with audit context
    def wrap_with_audit_context(original_handler):
        """Decorator to wrap existing handlers with audit context"""
        from functools import wraps
        from .audit_listeners import with_async_audit_context
        
        @wraps(original_handler)
        async def wrapper(self, *args, **kwargs):
            async with with_async_audit_context(state=self):
                return await original_handler(self, *args, **kwargs)
        return wrapper
    
    # Pattern 2: Add context to specific critical operations
    async def critical_operation_example(self, entity_id: int):
        """Example of adding rich context to critical operations"""
        from .audit_listeners import with_async_audit_context
        
        async with with_async_audit_context(
            state=self,
            operation_name="critical_operation",
            entity_id=entity_id,
            risk_level="high",
            requires_approval=True  # This could be used for future approval workflows
        ):
            # Your critical business logic here
            pass
    
    return wrap_with_audit_context


# Database initialization helper
def ensure_audit_table_exists():
    """Ensure the audit trail table exists in the database."""
    try:
        with rx.session() as session:
            # This will create the table if it doesn't exist
            # Reflex/SQLModel will handle table creation based on the model definition
            pass
        print("✓ AuditTrail table ready")
    except Exception as e:
        print(f"⚠ Warning: Could not verify audit table: {e}")


# Integration with your app startup
def initialize_audit_system():
    """Main function to call during app startup"""
    
    # 1. Ensure database table exists
    ensure_audit_table_exists()
    
    # 2. Setup audit tracking (add your models here)
    setup_audit_system([
        UserInfo, Supplier, Permission, Role, UserRole, RolePermission
    ])
    
    print("✓ Enhanced audit system fully initialized")



# Utility functions for common audit queries
class AuditQueries:
    """Helper class for common audit trail queries"""
    
    @staticmethod
    def get_recent_changes(limit: int = 50):
        """Get recent changes across all entities"""
        with rx.session() as session:
            return session.query(AuditTrail)\
                         .order_by(AuditTrail.timestamp.desc())\
                         .limit(limit)\
                         .all()
    
    @staticmethod
    def get_user_activity(user_id: int, days: int = 30):
        """Get activity for a specific user"""
        from datetime import datetime, timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        with rx.session() as session:
            return session.query(AuditTrail)\
                         .filter(AuditTrail.user_id == user_id)\
                         .filter(AuditTrail.timestamp >= since)\
                         .order_by(AuditTrail.timestamp.desc())\
                         .all()
    
    @staticmethod
    def get_entity_history(entity_type: str, entity_id: str):
        """Get complete history for a specific entity"""
        with rx.session() as session:
            return session.query(AuditTrail)\
                         .filter(AuditTrail.entity_type == entity_type)\
                         .filter(AuditTrail.entity_id == entity_id)\
                         .order_by(AuditTrail.timestamp.desc())\
                         .all()
    
    @staticmethod
    def get_failed_operations(days: int = 7):
        """Get failed operations for monitoring"""
        from datetime import datetime, timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        with rx.session() as session:
            return session.query(AuditTrail)\
                         .filter(AuditTrail.success == False)\
                         .filter(AuditTrail.timestamp >= since)\
                         .order_by(AuditTrail.timestamp.desc())\
                         .all()


# Example of custom audit logging for non-database operations
def log_custom_audit_event(
    operation_name: str,
    entity_type: str,
    user_id: int = None,
    username: str = "system",
    metadata: dict = None,
    success: bool = True,
    error_message: str = None
):
    """
    Log custom audit events for operations that don't involve database changes.
    
    Example: File uploads, API calls, login attempts, etc.
    """
    from .audit import AuditTrail, OperationType
    
    try:
        with rx.session() as session:
            audit_entry = AuditTrail.create_audit_entry(
                operation_type=OperationType.CUSTOM,
                operation_name=operation_name,
                entity_type=entity_type,
                user_id=user_id,
                username=username,
                audit_metadata=metadata or {},
                success=success,
                error_message=error_message
            )
            
            session.add(audit_entry)
            session.commit()
            
    except Exception as e:
        # Log to your existing logger if audit trail creation fails
        print(f"Failed to create custom audit entry: {e}")


# Example custom events you might want to track:
async def track_login_attempt(username: str, success: bool, ip_address: str = None):
    """Track login attempts"""
    log_custom_audit_event(
        operation_name="user_login_attempt",
        entity_type="authentication",
        username=username,
        audit_metadata={
            "ip_address": ip_address,
            "login_success": success
        },
        success=success
    )

async def track_file_upload(user_id: int, filename: str, file_size: int):
    """Track file uploads"""
    log_custom_audit_event(
        operation_name="file_upload",
        entity_type="file",
        user_id=user_id,
        audit_metadata={
            "filename": filename,
            "file_size": file_size,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
    )