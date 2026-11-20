"""
econode_studio/domain/api_key.py - Entidad de Dominio para Personal Access Tokens
Permite la autenticacion de agentes de IA (MCP) y scripts de automatizacion (Python / cURL).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import secrets


class ApiScopeEnum(str, Enum):
    ALL = "all"
    SYSTEMS_READ = "systems:read"
    SYSTEMS_WRITE = "systems:write"
    GHG_READ = "ghg:read"
    GHG_WRITE = "ghg:write"
    EPD_EXPORT = "epd:export"
    DATABASE_SEARCH = "database:search"


@dataclass(frozen=True)
class ApiKey:
    id: str
    user_id: str
    organization_id: str
    name: str
    key_prefix: str
    hashed_secret: str
    scopes: List[str]
    rate_limit_per_minute: int
    created_at: str
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None

    @classmethod
    def generate(
        cls,
        user_id: str,
        organization_id: str = "",
        name: str = "Default API Key",
        scopes: Optional[List[str]] = None,
        rate_limit_per_minute: int = 120
    ) -> Tuple["ApiKey", str]:
        """
        Genera una nueva clave con prefijo publico eco_live_ y secreto seguro de 32 bytes Base62.
        Retorna la tupla (instancia_entidad, token_en_texto_plano).
        El token en texto plano solo se retorna en este momento y nunca se almacena sin hashear.
        """
        raw_token = secrets.token_urlsafe(32)
        full_token = f"eco_live_{raw_token}"
        key_prefix = full_token[:16]
        hashed_secret = hashlib.sha256(full_token.encode("utf-8")).hexdigest()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        if not now_iso.endswith("Z"):
            now_iso += "Z"
            
        key_id = f"key_{secrets.token_hex(12)}"
        assigned_scopes = scopes if scopes else [ApiScopeEnum.ALL.value]
        
        instance = cls(
            id=key_id,
            user_id=user_id,
            organization_id=organization_id or "",
            name=name.strip() or "API Key",
            key_prefix=key_prefix,
            hashed_secret=hashed_secret,
            scopes=assigned_scopes,
            rate_limit_per_minute=rate_limit_per_minute,
            created_at=now_iso,
            expires_at=None,
            last_used_at=None,
            revoked_at=None
        )
        return instance, full_token

    def is_active(self) -> bool:
        """Verifica si la clave no ha sido revocada."""
        return self.revoked_at is None

    def has_scope(self, scope: str) -> bool:
        """Comprueba si la clave posee un alcance especifico o acceso total (all)."""
        if ApiScopeEnum.ALL.value in self.scopes or "all" in self.scopes:
            return True
        return scope in self.scopes

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Serializa la entidad omitiendo el hash secreto a menos que se especifique explicitamente."""
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "key_prefix": f"{self.key_prefix}...",
            "scopes": list(self.scopes),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used_at": self.last_used_at,
            "is_active": self.is_active()
        }
        if include_sensitive:
            d["hashed_secret"] = self.hashed_secret
        return d
