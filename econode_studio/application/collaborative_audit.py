"""
econode_studio/application/collaborative_audit.py - Casos de Uso para Hilos de Comentarios y Auditoría
Persistencia transaccional ACID en SQLite (econode_audit.db) vía audit_adapter.
"""

from typing import Dict, List, Any, Optional

try:
    from infrastructure.audit_adapter import (
        get_comments_by_system,
        insert_comment,
        resolve_comment,
        delete_comment
    )
except (ImportError, ValueError):
    from econode_studio.infrastructure.audit_adapter import (
        get_comments_by_system,
        insert_comment,
        resolve_comment,
        delete_comment
    )


def list_system_comments_use_case(system_id: int) -> List[Dict[str, Any]]:
    """Lista todos los comentarios de auditoría para el sistema especificado."""
    return get_comments_by_system(system_id)


def add_system_comment_use_case(
    system_id: int,
    author_name: str,
    author_role: str,
    content: str,
    node_id: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None
) -> Dict[str, Any]:
    """Crea un nuevo comentario técnico o anotación de lienzo."""
    return insert_comment(
        system_id=system_id,
        author_name=author_name,
        author_role=author_role,
        content=content,
        node_id=node_id,
        x=x,
        y=y
    )


def reply_and_resolve_comment_use_case(
    comment_id: int,
    resolved_by: str,
    reply_text: Optional[str] = None
) -> Dict[str, Any]:
    """Resuelve un hilo de auditoría agregando la justificación técnica."""
    return resolve_comment(
        comment_id=comment_id,
        resolved_by=resolved_by,
        reply_text=reply_text
    )


def delete_system_comment_use_case(
    comment_id: int,
    user_name: str = "",
    user_role: str = ""
) -> bool:
    """Elimina un comentario si pertenece al usuario activo o si es auditor líder/admin."""
    return delete_comment(
        comment_id=comment_id,
        user_name=user_name,
        user_role=user_role
    )
