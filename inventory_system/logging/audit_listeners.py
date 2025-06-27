from typing import Any, Dict, Optional, Set
import json
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
import reflex as rx

from .audit import AuditTrail, OperationType, get_utc_now
from inventory_system.logging.logging import audit_logger


class EnhancedAuditEventListener:
    """Enhanced audit event listener that writes to both logs and AuditTrail table."""
    
    def __init__(self):
        self._tracked_models: Set[type] = set()
        self._context_stack = []
    
    def register_model(self, model_class: type) -> None:
        """Register a model for audit tracking."""
        if model_class not in self._tracked_models:
            self._tracked_models.add(model_class)
            
            # Register SQLAlchemy events for this model
            event.listen(model_class, 'after_insert', self._after_insert)
            event.listen(model_class, 'after_update', self._after_update)
            event.listen(model_class, 'after_delete', self._after_delete)
    
    def set_audit_context(self, context: Dict[str, Any]) -> None:
        """Set audit context for the current operation."""
        self._context_stack.append(context)
    
    def clear_audit_context(self) -> None:
        """Clear the current audit context."""
        if self._context_stack:
            self._context_stack.pop()
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get the current audit context."""
        return self._context_stack[-1] if self._context_stack else {}
    
    def _get_model_identifier(self, instance) -> tuple[str, Optional[str]]:
        """Extract entity type and ID from model instance."""
        entity_type = instance.__class__.__name__.lower()
        
        # Try to get primary key value
        entity_id = None
        try:
            pk_columns = inspect(instance.__class__).primary_key
            if pk_columns:
                pk_value = getattr(instance, pk_columns[0].name, None)
                entity_id = str(pk_value) if pk_value is not None else None
        except Exception:
            pass
        
        return entity_type, entity_id
    
    def _extract_field_changes(self, instance, operation_type: str) -> Dict[str, Any]:
        """Extract field changes from the instance."""
        changes = {}
        
        if operation_type == 'update':
            # Get the instance state to track changes
            state = inspect(instance)
            if state.committed:
                for attr in state.attrs:
                    if attr.history.has_changes():
                        old_value = attr.history.deleted[0] if attr.history.deleted else None
                        new_value = attr.history.added[0] if attr.history.added else None
                        
                        # Convert complex objects to strings for JSON serialization
                        if old_value is not None:
                            old_value = self._serialize_value(old_value)
                        if new_value is not None:
                            new_value = self._serialize_value(new_value)
                        
                        changes[attr.key] = {
                            'old': old_value,
                            'new': new_value
                        }
        
        elif operation_type == 'insert':
            # For inserts, capture all non-None fields
            for column in instance.__table__.columns:
                value = getattr(instance, column.name, None)
                if value is not None:
                    changes[column.name] = {
                        'old': None,
                        'new': self._serialize_value(value)
                    }
        
        elif operation_type == 'delete':
            # For deletes, capture all current values as 'old'
            for column in instance.__table__.columns:
                value = getattr(instance, column.name, None)
                if value is not None:
                    changes[column.name] = {
                        'old': self._serialize_value(value),
                        'new': None
                    }
        
        return changes
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON storage."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            # For complex objects, use string representation
            return str(value)
        else:
            return str(value)
    
    def _create_audit_entry(
        self, 
        instance, 
        operation_type: OperationType, 
        changes: Dict[str, Any]
    ) -> None:
        """Create audit entry in both log and database."""
        entity_type, entity_id = self._get_model_identifier(instance)
        context = self.get_current_context()
        
        # Extract context information
        user_id = context.get('user_id')
        username = context.get('username', 'system')
        ip_address = context.get('ip_address')
        session_id = context.get('session_id')
        request_path = context.get('request_path')
        user_agent = context.get('user_agent')
        transaction_id = context.get('transaction_id')
        
        # Create operation name
        operation_name = f"{operation_type.value}_{entity_type}"
        
        # Create audit metadata
        audit_metadata = {
            'table_name': instance.__table__.name,
            'model_class': instance.__class__.__name__,
            'session_id': session_id,
            'request_path': request_path,
            'user_agent': user_agent,
            'change_count': len(changes) if changes else 0
        }
        
        # Add any additional context metadata
        for key, value in context.items():
            if key not in ['user_id', 'username', 'ip_address', 'session_id', 
                          'request_path', 'user_agent', 'transaction_id']:
                audit_metadata[key] = value
        
        # 1. Log to existing audit logger (maintain backward compatibility)
        log_data = {
            'operation': operation_name,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'changes': changes,
            'metadata': audit_metadata
        }
        
        audit_logger.info(
            f"database_{operation_type.value}",
            extra={
                'audit_data': log_data,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'operation': operation_name
            }
        )
        
        # 2. Create AuditTrail database entry
        try:
            # Get or create a database session
            with rx.session() as session:
                audit_entry = AuditTrail.create_audit_entry(
                    operation_type=operation_type,
                    operation_name=operation_name,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                    username=username,
                    ip_address=ip_address,
                    changes=changes,
                    audit_metadata=audit_metadata,
                    transaction_id=transaction_id,
                    session_id=session_id,
                    request_path=request_path,
                    user_agent=user_agent,
                    success=True  # Database operations that reach here are successful
                )
                
                session.add(audit_entry)
                session.commit()
                
        except Exception as e:
            # Log the error but don't fail the main operation
            audit_logger.error(
                "audit_trail_creation_failed",
                extra={
                    'error': str(e),
                    'operation': operation_name,
                    'entity_type': entity_type,
                    'entity_id': entity_id
                }
            )
    
    def _after_insert(self, mapper, connection, target):
        """Handle after insert events."""
        if target.__class__ in self._tracked_models:
            changes = self._extract_field_changes(target, 'insert')
            self._create_audit_entry(target, OperationType.CREATE, changes)
    
    def _after_update(self, mapper, connection, target):
        """Handle after update events."""
        if target.__class__ in self._tracked_models:
            changes = self._extract_field_changes(target, 'update')
            if changes:  # Only log if there are actual changes
                self._create_audit_entry(target, OperationType.UPDATE, changes)
    
    def _after_delete(self, mapper, connection, target):
        """Handle after delete events."""
        if target.__class__ in self._tracked_models:
            changes = self._extract_field_changes(target, 'delete')
            self._create_audit_entry(target, OperationType.DELETE, changes)


# Global instance
enhanced_audit_listener = EnhancedAuditEventListener()


class AuditContextManager:
    """Context manager for setting audit context during operations."""
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        username: str = 'system',
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        request_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        transaction_id: Optional[str] = None,
        **additional_context
    ):
        self.context = {
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'session_id': session_id,
            'request_path': request_path,
            'user_agent': user_agent,
            'transaction_id': transaction_id,
            **additional_context
        }
    
    def __enter__(self):
        enhanced_audit_listener.set_audit_context(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        enhanced_audit_listener.clear_audit_context()


# Async version of the context manager
class AsyncAuditContextManager:
    """Async context manager for setting audit context during operations."""
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        username: str = 'system',
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        request_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        transaction_id: Optional[str] = None,
        **additional_context
    ):
        self.context = {
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'session_id': session_id,
            'request_path': request_path,
            'user_agent': user_agent,
            'transaction_id': transaction_id,
            **additional_context
        }
    
    async def __aenter__(self):
        enhanced_audit_listener.set_audit_context(self.context)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        enhanced_audit_listener.clear_audit_context()


def register_model_for_audit(model_class: type) -> None:
    """Register a model class for automatic audit tracking."""
    enhanced_audit_listener.register_model(model_class)


def get_request_context(state: Optional[rx.State] = None) -> Dict[str, Any]:
    """Extract request context from Reflex state for audit logging."""
    context = {}
    
    if state:
        # Extract user information
        if hasattr(state, 'user_info') and state.user_info:
            context['user_id'] = getattr(state.user_info, 'id', None)
            context['username'] = getattr(state.user_info, 'username', 'unknown')
        
        # Extract session information if available
        if hasattr(state, 'router') and state.router:
            context['request_path'] = getattr(state.router, 'page', {}).get('path')
        
        # You can add more context extraction based on your Reflex state structure
        if hasattr(state, 'session_id'):
            context['session_id'] = state.session_id
    
    return context


# Convenience function for use in Reflex event handlers
def with_audit_context(
    state: Optional[rx.State] = None,
    **additional_context
) -> AuditContextManager:
    """Create audit context manager with automatic request context extraction."""
    context = get_request_context(state)
    context.update(additional_context)
    
    return AuditContextManager(**context)


def with_async_audit_context(
    state: Optional[rx.State] = None,
    **additional_context
) -> AsyncAuditContextManager:
    """Create async audit context manager with automatic request context extraction."""
    context = get_request_context(state)
    context.update(additional_context)
    
    return AsyncAuditContextManager(**context)