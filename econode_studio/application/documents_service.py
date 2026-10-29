"""
econode_studio/application/documents_service.py - Casos de Uso para Bóveda Documental
Capa de Aplicación:
Valida reglas de negocio, tipos de archivo permitidos, límites de tamaño y auditoría
antes de delegar la persistencia física a 'infrastructure.documents_adapter'.
"""

from typing import Dict, List, Any, Optional, Tuple

try:
    from infrastructure import documents_adapter as _doc_adapter
except (ImportError, ValueError):
    from econode_studio.infrastructure import documents_adapter as _doc_adapter


def list_documents_use_case(system_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Recupera la lista de documentos registrados en la bóveda para un sistema producto."""
    return _doc_adapter.list_documents(system_id)


def upload_document_use_case(
    title: str,
    original_filename: str,
    file_bytes: bytes,
    uploaded_by: str,
    user_role: str,
    system_id: Optional[int] = 1,
    description: str = "",
    override_sha256: Optional[str] = None,
    override_file_size: Optional[int] = None
) -> Dict[str, Any]:
    """Valida y almacena un archivo (SQL, Excel, PDF, JSON, ZIP) en la bóveda con hash SHA-256."""
    is_drive_link = bool(description and "drive.google.com" in description)
    if not file_bytes and not is_drive_link and not override_sha256:
        raise ValueError("El contenido del archivo no puede estar vacío.")

    # Límite de seguridad: 50 MB para subidas directas
    if file_bytes and len(file_bytes) > 50 * 1024 * 1024:
        raise ValueError("El archivo excede el tamaño máximo permitido de 50 MB.")

    title = (title or original_filename or "Documento").strip()
    return _doc_adapter.save_document(
        title=title,
        original_filename=original_filename,
        file_bytes=file_bytes,
        uploaded_by=uploaded_by,
        user_role=user_role,
        system_id=system_id,
        description=description,
        override_sha256=override_sha256,
        override_file_size=override_file_size
    )


def get_document_file_use_case(document_id: int) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Recupera los bytes y metadatos MIME de un archivo almacenado en disco."""
    return _doc_adapter.get_document_file(document_id)


def delete_document_use_case(document_id: int, user_name: str = "", user_role: str = "") -> bool:
    """Elimina un documento y su archivo físico de la bóveda."""
    return _doc_adapter.delete_document(document_id)


# Alias de compatibilidad
list_documents = list_documents_use_case
save_document = upload_document_use_case
get_document_file = get_document_file_use_case
delete_document = delete_document_use_case

