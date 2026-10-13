"""
econode_studio/domain/audit_comment.py - Entidad de Dominio para Comentarios y Notas Técnicas de Auditoría
Modela las anotaciones técnicas sobre procesos del lienzo y requerimientos de auditoría colaborativa.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class AuditComment:
    id: Optional[int]
    system_id: int
    author_name: str
    author_role: str
    content: str
    node_id: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    status: str = "open"  # 'open', 'resolved'
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    reply: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")

    def is_resolved(self) -> bool:
        """Indica si la observación técnica ha sido resuelta y cerrada."""
        return self.status == "resolved"

    def is_pinned_to_node(self) -> bool:
        """Indica si la nota adhesiva está anclada a una tarjeta de proceso específica en el lienzo."""
        return bool(self.node_id)

    def can_be_deleted_by(self, user_name: str = "", user_role: str = "") -> bool:
        """
        Regla de negocio:
        El Auditor Líder o un Administrador pueden eliminar cualquier observación.
        Un analista o cliente únicamente puede eliminar las observaciones que él mismo redactó.
        """
        if user_role in ("auditor", "admin"):
            return True
        return self.author_name.strip().lower() == (user_name or "").strip().lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "system_id": self.system_id,
            "author_name": self.author_name,
            "author_role": self.author_role,
            "content": self.content,
            "node_id": self.node_id,
            "x": self.x,
            "y": self.y,
            "status": self.status,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at,
            "reply": self.reply,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditComment":
        return cls(
            id=data.get("id"),
            system_id=int(data.get("system_id", 1)),
            author_name=str(data.get("author_name") or "Usuario"),
            author_role=str(data.get("author_role") or "auditor"),
            content=str(data.get("content") or ""),
            node_id=data.get("node_id"),
            x=float(data["x"]) if data.get("x") is not None else None,
            y=float(data["y"]) if data.get("y") is not None else None,
            status=str(data.get("status") or "open"),
            resolved_by=data.get("resolved_by"),
            resolved_at=data.get("resolved_at"),
            reply=data.get("reply"),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat() + "Z")
        )

