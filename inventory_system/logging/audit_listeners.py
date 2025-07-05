# inventory_system/logging/audit_listeners.py - Enhanced version

import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import reflex as rx
from reflex import State
from sqlalchemy import event
from sqlalchemy.inspection import inspect

from inventory_system.logging.logging import audit_logger
from inventory_system.models.audit import AuditTrail, OperationType
from inventory_system.state.auth import AuthState


class BulkAuditContext:
    """Context for bulk operations that tracks multiple entities."""

    def __init__(self, operation_name: str, transaction_id: str, **context):
        self.operation_name = operation_name
        self.transaction_id = transaction_id
        self.context = context
        self.entities_affected = []
        self.operation_summary = {}
        self.start_time = datetime.utcnow()

    def add_entity(
        self,
        entity_type: str,
        entity_id: str,
        operation_type: str,
        changes: Dict[str, Any],
    ):
        """Add an entity that was affected by the bulk operation."""
        self.entities_affected.append(
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "operation_type": operation_type,
                "changes": changes,
                "timestamp": datetime.utcnow(),
            }
        )

    def set_summary(self, summary: Dict[str, Any]):
        """Set overall operation summary (success/failure counts, etc.)."""
        self.operation_summary = summary

    def get_audit_data(self) -> Dict[str, Any]:
        """Get complete audit data for the bulk operation, serializing datetimes for JSON."""

        def _serialize_for_json(obj):
            if isinstance(obj, dict):
                return {k: _serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_serialize_for_json(v) for v in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj

        data = {
            "operation_name": self.operation_name,
            "transaction_id": self.transaction_id,
            "entities_affected": self.entities_affected,
            "operation_summary": self.operation_summary,
            "start_time": self.start_time,
            "end_time": datetime.utcnow(),
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "entity_count": len(self.entities_affected),
            **self.context,
        }
        return _serialize_for_json(data)


class EnhancedAuditEventListener:
    """Enhanced audit event listener with bulk operation support."""

    def __init__(self):
        self._tracked_models: Set[type] = set()
        self._context_stack = []
        self._bulk_context_stack = []
        self._pending_audits: List[Dict[str, Any]] = []
        self._pending_bulk_audits: List[BulkAuditContext] = []
        self._lock = threading.Lock()

    def register_model(self, model_class: type) -> None:
        if model_class not in self._tracked_models:
            self._tracked_models.add(model_class)
            event.listen(model_class, "after_insert", self._after_insert)
            event.listen(model_class, "after_update", self._after_update)
            event.listen(model_class, "after_delete", self._after_delete)

    def set_audit_context(self, context: Dict[str, Any]) -> None:
        self._context_stack.append(context)

    def clear_audit_context(self) -> None:
        if self._context_stack:
            self._context_stack.pop()

    def get_current_context(self) -> Dict[str, Any]:
        return self._context_stack[-1] if self._context_stack else {}

    def set_bulk_context(self, bulk_context: BulkAuditContext) -> None:
        """Set bulk operation context."""
        self._bulk_context_stack.append(bulk_context)

    def clear_bulk_context(self) -> BulkAuditContext:
        """Clear and return the current bulk context."""
        if self._bulk_context_stack:
            return self._bulk_context_stack.pop()
        return None

    def get_current_bulk_context(self) -> Optional[BulkAuditContext]:
        """Get current bulk context if any."""
        return self._bulk_context_stack[-1] if self._bulk_context_stack else None

    def _get_model_identifier(self, instance) -> tuple[str, Optional[str]]:
        entity_type = instance.__class__.__name__.lower()
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
        changes = {}
        if operation_type == "update":
            state = inspect(instance)
            if state.persistent:
                for attr in state.attrs:
                    if attr.history.has_changes():
                        old_value = (
                            attr.history.deleted[0] if attr.history.deleted else None
                        )
                        new_value = (
                            attr.history.added[0] if attr.history.added else None
                        )
                        changes[attr.key] = {
                            "old": self._serialize_value(old_value),
                            "new": self._serialize_value(new_value),
                        }
        elif operation_type == "insert":
            for column in instance.__table__.columns:
                value = getattr(instance, column.name, None)
                if value is not None:
                    changes[column.name] = {
                        "old": None,
                        "new": self._serialize_value(value),
                    }
        elif operation_type == "delete":
            for column in instance.__table__.columns:
                value = getattr(instance, column.name, None)
                if value is not None:
                    changes[column.name] = {
                        "old": self._serialize_value(value),
                        "new": None,
                    }
        return changes

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return value
        elif hasattr(value, "__dict__"):
            try:
                return value.__dict__
            except Exception:
                return str(value)
        else:
            return str(value)

    def _create_audit_entry(
        self, instance, operation_type: OperationType, changes: Dict[str, Any]
    ) -> None:
        entity_type, entity_id = self._get_model_identifier(instance)
        context = self.get_current_context()
        bulk_context = self.get_current_bulk_context()

        # If we're in a bulk operation, add to bulk context
        # instead of creating individual entries
        if bulk_context:
            bulk_context.add_entity(
                entity_type, entity_id, operation_type.value, changes
            )
            return

        # Regular single-entity audit logic (existing code)
        user_id = context.get("user_id")
        username = context.get("username", "system")
        ip_address = context.get("ip_address")
        session_id = context.get("session_id")
        request_path = context.get("request_path")
        user_agent = context.get("user_agent")
        transaction_id = context.get("transaction_id")

        operation_name = f"{operation_type.value}_{entity_type}"
        audit_metadata = {
            "table_name": instance.__table__.name,
            "model_class": instance.__class__.__name__,
            "session_id": session_id,
            "request_path": request_path,
            "user_agent": user_agent,
            "change_count": len(changes) if changes else 0,
        }

        log_data = {
            "operation": operation_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "changes": changes,
            "metadata": audit_metadata,
        }

        audit_logger.info(
            f"database_{operation_type.value}",
            extra={
                "audit_data": log_data,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "operation": operation_name,
            },
        )

        audit_data = {
            "operation_type": operation_type,
            "operation_name": operation_name,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "transaction_id": transaction_id,
            "session_id": session_id,
            "request_path": request_path,
            "user_agent": user_agent,
            "success": True,
            "changes": changes,
            "audit_metadata": audit_metadata,
        }

        with self._lock:
            self._pending_audits.append(audit_data)

    def _after_insert(self, mapper, connection, target):
        if target.__class__ in self._tracked_models:
            try:
                changes = self._extract_field_changes(target, "insert")
                self._create_audit_entry(target, OperationType.CREATE, changes)
            except Exception as e:
                audit_logger.error(f"Error in after_insert audit: {e}")

    def _after_update(self, mapper, connection, target):
        if target.__class__ in self._tracked_models:
            try:
                changes = self._extract_field_changes(target, "update")
                if changes:
                    self._create_audit_entry(target, OperationType.UPDATE, changes)
            except Exception as e:
                audit_logger.error(f"Error in after_update audit: {e}")

    def _after_delete(self, mapper, connection, target):
        if target.__class__ in self._tracked_models:
            try:
                changes = self._extract_field_changes(target, "delete")
                self._create_audit_entry(target, OperationType.DELETE, changes)
            except Exception as e:
                audit_logger.error(f"Error in after_delete audit: {e}")

    def flush_pending_audits(self) -> None:
        """Flush individual audit entries."""
        with self._lock:
            pending_audits = self._pending_audits.copy()
            self._pending_audits.clear()

        for audit_data in pending_audits:
            try:
                audit_entry = AuditTrail.create_audit_entry(**audit_data)
                audit_entry.changes = audit_data["changes"]
                audit_entry.audit_metadata = audit_data["audit_metadata"]
                with rx.session() as session:
                    session.add(audit_entry)
                    session.commit()
                    audit_logger.debug(
                        f"Audit entry created successfully: {audit_entry.id}"
                    )
            except Exception as e:
                audit_logger.error(
                    "audit_trail_creation_failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "operation": audit_data["operation_name"],
                        "entity_type": audit_data["entity_type"],
                        "entity_id": audit_data["entity_id"],
                    },
                )

    def flush_bulk_audits(self) -> None:
        """Flush bulk operation audit entries."""
        with self._lock:
            pending_bulk_audits = self._pending_bulk_audits.copy()
            self._pending_bulk_audits.clear()

        for bulk_context in pending_bulk_audits:
            try:
                audit_data = bulk_context.get_audit_data()

                # Create a single audit entry for the bulk operation
                audit_entry = AuditTrail.create_audit_entry(
                    operation_type=OperationType.BULK,
                    operation_name=audit_data["operation_name"],
                    entity_type="bulk_operation",
                    entity_id=audit_data["transaction_id"],
                    user_id=audit_data.get("user_id"),
                    username=audit_data.get("username", "system"),
                    ip_address=audit_data.get("ip_address"),
                    transaction_id=audit_data["transaction_id"],
                    session_id=audit_data.get("session_id"),
                    request_path=audit_data.get("request_path"),
                    user_agent=audit_data.get("user_agent"),
                    success=True,
                    changes=audit_data["entities_affected"],
                    audit_metadata={
                        "operation_summary": audit_data["operation_summary"],
                        "duration_seconds": audit_data["duration_seconds"],
                        "entity_count": audit_data["entity_count"],
                        "operation_type": "bulk",
                    },
                )

                with rx.session() as session:
                    session.add(audit_entry)
                    session.commit()
                    audit_logger.debug(
                        f"Bulk audit entry created successfully: {audit_entry.id}"
                    )

                # Also log the bulk operation details
                audit_logger.info(
                    "bulk_operation_completed",
                    extra={
                        "audit_data": audit_data,
                        "operation": audit_data["operation_name"],
                        "entity_count": audit_data["entity_count"],
                        "transaction_id": audit_data["transaction_id"],
                    },
                )

            except Exception as e:
                audit_logger.error(
                    "bulk_audit_trail_creation_failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "operation": bulk_context.operation_name,
                        "transaction_id": bulk_context.transaction_id,
                    },
                )

    def add_pending_bulk_audit(self, bulk_context: BulkAuditContext) -> None:
        """Add a completed bulk context to pending audits."""
        with self._lock:
            self._pending_bulk_audits.append(bulk_context)


enhanced_audit_listener = EnhancedAuditEventListener()


class AsyncAuditContextManager:
    """Async context manager for setting audit context with AuthState integration."""

    def __init__(
        self,
        state: Optional[State] = None,
        operation_name: str = "custom_operation",
        transaction_id: Optional[str] = None,
        **additional_context,
    ):
        self.state = state
        self.context = {
            "operation_name": operation_name,
            "transaction_id": transaction_id or str(uuid.uuid4()),
            **additional_context,
        }

    async def __aenter__(self):
        auth_state = await self.state.get_state(AuthState) if self.state else None
        if auth_state:
            self.context.setdefault(
                "user_id",
                auth_state.user_id if auth_state.is_authenticated_and_ready else None,
            )
            self.context.setdefault(
                "username",
                auth_state.username
                if auth_state.is_authenticated_and_ready
                else "system",
            )
            self.context.setdefault("ip_address", auth_state.router.session.client_ip)
            self.context.setdefault(
                "session_id", getattr(auth_state, "session_id", None)
            )
            self.context.setdefault(
                "request_path", getattr(auth_state.router.page, "path", None)
            )
            self.context.setdefault(
                "user_agent", getattr(auth_state.router.session, "user_agent", None)
            )
        enhanced_audit_listener.set_audit_context(self.context)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Create audit entry for the operation itself
        operation_type = self.context.get("operation_type")
        operation_name = self.context.get("operation_name")
        if (
            operation_type in [OperationType.LOGIN, OperationType.LOGOUT]
            and operation_name
        ):
            success = exc_type is None
            error_message = str(exc_val) if exc_val else None
            audit_entry = AuditTrail.create_audit_entry(
                operation_type=operation_type,
                operation_name=operation_name,
                entity_type="session",
                entity_id=None,
                user_id=self.context.get("user_id"),
                username=self.context.get("username", "system"),
                ip_address=self.context.get("ip_address"),
                success=success,
                error_message=error_message,
            )
            with rx.session() as session:
                session.add(audit_entry)
                session.commit()
                audit_logger.debug(
                    f"Audit entry created successfully: {audit_entry.id}"
                )
        enhanced_audit_listener.clear_audit_context()
        enhanced_audit_listener.flush_pending_audits()


class AsyncBulkAuditContextManager:
    """Async context manager for bulk operations."""

    def __init__(
        self,
        state: Optional[State] = None,
        operation_name: str = "bulk_operation",
        transaction_id: Optional[str] = None,
        **additional_context,
    ):
        self.state = state
        self.operation_name = operation_name
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.additional_context = additional_context
        self.bulk_context = None

    async def __aenter__(self):
        # Get auth context
        auth_state = await self.state.get_state(AuthState) if self.state else None
        context = {
            "user_id": auth_state.user_id
            if auth_state and auth_state.is_authenticated_and_ready
            else None,
            "username": auth_state.username
            if auth_state and auth_state.is_authenticated_and_ready
            else "system",
            "ip_address": auth_state.router.session.client_ip if auth_state else None,
            "session_id": getattr(auth_state, "session_id", None)
            if auth_state
            else None,
            "request_path": getattr(auth_state.router.page, "path", None)
            if auth_state
            else None,
            "user_agent": getattr(auth_state.router.session, "user_agent", None)
            if auth_state
            else None,
            **self.additional_context,
        }

        # Create bulk context
        self.bulk_context = BulkAuditContext(
            operation_name=self.operation_name,
            transaction_id=self.transaction_id,
            **context,
        )

        # Set both regular and bulk context
        enhanced_audit_listener.set_audit_context(context)
        enhanced_audit_listener.set_bulk_context(self.bulk_context)

        return self.bulk_context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clear contexts
        enhanced_audit_listener.clear_audit_context()
        completed_bulk_context = enhanced_audit_listener.clear_bulk_context()

        # Add to pending bulk audits for later processing
        if completed_bulk_context:
            enhanced_audit_listener.add_pending_bulk_audit(completed_bulk_context)

        # Flush any individual audits that might have been created
        enhanced_audit_listener.flush_pending_audits()
        # Flush bulk audits
        enhanced_audit_listener.flush_bulk_audits()


def with_async_audit_context(
    state: Optional[State] = None, **additional_context
) -> AsyncAuditContextManager:
    """Create context manager for individual operations."""
    return AsyncAuditContextManager(state=state, **additional_context)


def with_async_bulk_audit_context(
    state: Optional[State] = None,
    operation_name: str = "bulk_operation",
    **additional_context,
) -> AsyncBulkAuditContextManager:
    """Create context manager for bulk operations."""
    return AsyncBulkAuditContextManager(
        state=state, operation_name=operation_name, **additional_context
    )


def register_model_for_audit(model_class: type) -> None:
    """Register a model class for automatic audit tracking."""
    enhanced_audit_listener.register_model(model_class)
