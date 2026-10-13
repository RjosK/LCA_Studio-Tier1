"""
econode_studio/domain/user_account.py - Reglas de Negocio de Cuentas y Control de Acceso (RBAC)
Define los tres perfiles oficiales requeridos para ECONODE Studio más soporte administrativo:
1. ANALYST: Creador del sistema producto (modelado, insumos, balances de masa y parámetros).
2. AUDITOR: Auditor Líder ACV (revisión de conformidad, observaciones normativas y firma digital de dictamen).
3. CLIENT: Cliente / Productor (carga de evidencias/facturas, respuesta a objeciones y consulta de reporte final).
4. ADMIN: Administrador de plataforma con privilegios globales.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class RoleEnum(str, Enum):
    ANALYST = "analyst"  # Creador / Modelador del sistema producto
    AUDITOR = "auditor"  # Auditor Líder ACV / Verificador NOM-070
    CLIENT = "client"    # Cliente / Productor Industrial
    ADMIN = "admin"      # Administrador global


@dataclass(frozen=True)
class UserAccount:
    id: str
    username: str
    display_name: str
    email: str
    organization: str
    role: RoleEnum
    role_title: str
    bio: str
    avatar: str
    token: str
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    last_login: Optional[str] = None

    def can_edit_model(self) -> bool:
        """Determina si el usuario tiene permisos de edición sobre el lienzo y flujos."""
        return self.role in (RoleEnum.ANALYST, RoleEnum.AUDITOR, RoleEnum.ADMIN) or "canvas_edit" in self.permissions

    def can_sign_audit(self) -> bool:
        """Determina si el usuario está acreditado para emitir firma digital de dictamen."""
        return self.role in (RoleEnum.AUDITOR, RoleEnum.ADMIN) or "nom070_certify" in self.permissions

    def can_upload_evidence(self) -> bool:
        """Permite cargar archivos y comprobantes a la bóveda de documentos."""
        return True

    def can_delete_comment(self, comment_author_name: str) -> bool:
        """El auditor líder o admin pueden eliminar cualquier nota; otros roles solo las propias."""
        if self.role in (RoleEnum.AUDITOR, RoleEnum.ADMIN):
            return True
        return self.display_name.strip().lower() == (comment_author_name or "").strip().lower()

    def has_permission(self, permission: str) -> bool:
        """Comprueba si el usuario cuenta con un permiso específico en su colección."""
        return permission in self.permissions or self.role == RoleEnum.ADMIN

    def is_analyst(self) -> bool:
        return self.role == RoleEnum.ANALYST

    def is_auditor(self) -> bool:
        return self.role == RoleEnum.AUDITOR

    def is_client(self) -> bool:
        return self.role == RoleEnum.CLIENT

    def is_admin(self) -> bool:
        return self.role == RoleEnum.ADMIN

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la entidad a un diccionario seguro para capas superiores y API."""
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "organization": self.organization,
            "role": self.role.value if isinstance(self.role, RoleEnum) else str(self.role),
            "role_title": self.role_title,
            "bio": self.bio,
            "avatar": self.avatar,
            "token": self.token,
            "permissions": list(self.permissions),
            "created_at": self.created_at,
            "last_login": self.last_login
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAccount":
        """Instancia la entidad a partir de un diccionario."""
        role_raw = data.get("role", "analyst")
        try:
            role = RoleEnum(role_raw)
        except ValueError:
            role = RoleEnum.ANALYST

        return cls(
            id=str(data.get("id", "")),
            username=str(data.get("username", "")),
            display_name=str(data.get("display_name", "")),
            email=str(data.get("email", "")),
            organization=str(data.get("organization", "")),
            role=role,
            role_title=str(data.get("role_title", "")),
            bio=str(data.get("bio", "")),
            avatar=str(data.get("avatar", "")),
            token=str(data.get("token", "")),
            permissions=list(data.get("permissions", [])),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat() + "Z"),
            last_login=data.get("last_login")
        )
