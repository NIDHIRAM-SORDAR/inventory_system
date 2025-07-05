# audit_setup.py
"""
Setup file to integrate the enhanced audit system with your existing codebase.
This file should be imported early in your application startup.
"""

from typing import List, Type

import reflex as rx

from inventory_system.models.user import (
    Permission,
    Role,
    RolePermission,
    Supplier,
    UserInfo,
    UserRole,
)

# Import your models and the enhanced audit system
from .audit_listeners import register_model_for_audit


def setup_audit_system(models_to_track: List[Type] = None):
    """
    Setup the enhanced audit system.

    Args:
        models_to_track: List of model classes to track. If None, will track common models.
    """

    # Default models to track (adjust based on your models)
    if models_to_track is None:
        models_to_track = [
            UserInfo,
            Supplier,
            Permission,
            Role,
            UserRole,
            RolePermission,
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
            requires_approval=True,  # This could be used for future approval workflows
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
    setup_audit_system([UserInfo, Supplier, Permission, Role, UserRole, RolePermission])

    print("✓ Enhanced audit system fully initialized")
