"""
econode_studio/domain/vault_document.py - Entidad de Dominio para Archivos de la Bóveda y Evidencias
Modela la metadata y reglas de integridad criptográfica (SHA-256) de los documentos subidos.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class VaultDocument:
    id: int
    system_id: Optional[int]
    title: str
    original_filename: str
    disk_filename: str
    file_type: str
    mime_type: str
    file_size: int
    uploaded_by: str
    user_role: str
    uploaded_at: str
    sha256_hash: str
    description: str = ""

    def formatted_size(self) -> str:
        """Retorna el tamaño en formato legible para humanos (KB, MB)."""
        bytes_val = float(self.file_size)
        if bytes_val < 1024:
            return f"{int(bytes_val)} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024.0:.1f} KB"
        else:
            return f"{bytes_val / (1024.0 * 1024.0):.1f} MB"

    def is_sql_script(self) -> bool:
        return "sql" in self.file_type.lower() or self.original_filename.lower().endswith(".sql")

    def is_spreadsheet(self) -> bool:
        return any(self.original_filename.lower().endswith(ext) for ext in (".xlsx", ".xls", ".csv"))

    def is_pdf(self) -> bool:
        return self.original_filename.lower().endswith(".pdf")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "system_id": self.system_id,
            "title": self.title,
            "original_filename": self.original_filename,
            "disk_filename": self.disk_filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "file_size_formatted": self.formatted_size(),
            "uploaded_by": self.uploaded_by,
            "user_role": self.user_role,
            "uploaded_at": self.uploaded_at,
            "sha256_hash": self.sha256_hash,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VaultDocument":
        return cls(
            id=int(data.get("id") or 0),
            system_id=int(data["system_id"]) if data.get("system_id") is not None else None,
            title=str(data.get("title") or "Documento"),
            original_filename=str(data.get("original_filename") or "archivo.bin"),
            disk_filename=str(data.get("disk_filename") or ""),
            file_type=str(data.get("file_type") or "Documento"),
            mime_type=str(data.get("mime_type") or "application/octet-stream"),
            file_size=int(data.get("file_size") or 0),
            uploaded_by=str(data.get("uploaded_by") or "Usuario"),
            user_role=str(data.get("user_role") or "client"),
            uploaded_at=str(data.get("uploaded_at") or ""),
            sha256_hash=str(data.get("sha256_hash") or ""),
            description=str(data.get("description") or "")
        )

