import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    actor: str = "system"  # Who performed the action
    action: str  # e.g., "create_identity", "assign_role"
    target: str  # e.g., "user:alice@example.com"
    details: Optional[Dict[str, Any]] = None
    status: str = "success"  # success, failure


class AuditLogStore:
    def __init__(self) -> None:
        self._logs: List[AuditEvent] = []

    def log_event(
        self,
        action: str,
        target: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> None:
        event = AuditEvent(
            action=action, target=target, actor=actor, details=details, status=status
        )
        self._logs.append(event)
        # In a real system, this would write to a database or SIEM
        print(f"[AUDIT] {event.timestamp} - {action} on {target} by {actor}: {status}")

    def get_logs(self, limit: int = 100) -> List[AuditEvent]:
        return sorted(self._logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_logs_by_target(self, target: str) -> List[AuditEvent]:
        return [log for log in self._logs if log.target == target]


# Singleton
audit_log_store = AuditLogStore()
