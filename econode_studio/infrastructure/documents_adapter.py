"""
econode_studio/infrastructure/documents_adapter.py - Bóveda de Almacenamiento de Documentos y Archivos
Permite almacenar archivos SQL, Excel (.xlsx, .csv), PDF, JSON y ZIP creados por cualquiera de los 3 perfiles
(Analista, Auditor Líder, Cliente/Productor) con registro de metadatos, tamaño y hash SHA-256 en SQLite local.
"""

import os
import sqlite3
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    from config import settings
except (ImportError, ValueError):
    from econode_studio.config import settings

from .db_connection import get_db_connection

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DOCS_DB_PATH = getattr(settings, "DOCUMENTS_DB_PATH", os.path.join(DATA_DIR, "econode_documents.db"))

def get_uploads_dir() -> str:
    """Retorna un directorio de almacenamiento con permisos de escritura (resiliente en Vercel /tmp)."""
    custom = getattr(settings, "STORAGE_LOCAL_DIR", None)
    if custom:
        try:
            os.makedirs(custom, exist_ok=True)
            return custom
        except OSError:
            pass

    default_dir = os.path.join(DATA_DIR, "documents")
    try:
        os.makedirs(default_dir, exist_ok=True)
        # Verificar capacidad de escritura real
        test_file = os.path.join(default_dir, ".write_test")
        with open(test_file, "w") as tf:
            tf.write("ok")
        os.remove(test_file)
        return default_dir
    except (OSError, PermissionError):
        # Fallback estándar para Vercel Serverless (AWS Lambda: solo /tmp tiene permisos de escritura)
        tmp_dir = os.path.join("/tmp", "econode_documents")
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

UPLOADS_DIR = get_uploads_dir()

def init_documents_db():
    """Inicializa el directorio y la base de datos de documentos si no existen."""
    get_uploads_dir()
    if getattr(settings, "IS_POSTGRES", False):
        return
    with get_db_connection(DOCS_DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER,
                title TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                disk_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_by TEXT NOT NULL,
                user_role TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                description TEXT
            );
        """)

def save_document(
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
    """Guarda un archivo en disco y registra sus metadatos en la base de datos."""
    init_documents_db()

    ext = os.path.splitext(original_filename)[1].lower()
    type_map = {
        ".pdf": "PDF",
        ".xlsx": "Excel",
        ".xls": "Excel",
        ".csv": "CSV / Datos",
        ".sql": "SQL Script / Dump",
        ".json": "JSON / Modelo",
        ".zip": "ZIP / Expediente",
        ".png": "Imagen / Evidencia",
        ".jpg": "Imagen / Evidencia",
        ".jpeg": "Imagen / Evidencia"
    }
    file_type = type_map.get(ext, "Archivo Binario")

    mime_map = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".sql": "application/sql",
        ".json": "application/json",
        ".zip": "application/zip",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }
    mime_type = mime_map.get(ext, "application/octet-stream")

    sha256 = override_sha256 or (hashlib.sha256(file_bytes).hexdigest() if file_bytes else "N/A")
    file_size = override_file_size if override_file_size is not None else len(file_bytes)

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in original_filename if c.isalnum() or c in "._- ") or "archivo.bin"
    disk_filename = f"{timestamp_str}_{safe_name}"

    if file_bytes:
        target_dir = get_uploads_dir()
        file_path = os.path.join(target_dir, disk_filename)
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except OSError:
            target_dir = os.path.join("/tmp", "econode_documents")
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, disk_filename)
            with open(file_path, "wb") as f:
                f.write(file_bytes)
    else:
        disk_filename = f"drive_{safe_name}"

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(DOCS_DB_PATH) as conn:
        cur = conn.execute("""
            INSERT INTO documents (
                system_id, title, original_filename, disk_filename,
                file_type, mime_type, file_size, uploaded_by, user_role,
                uploaded_at, sha256_hash, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            system_id, title, original_filename, disk_filename,
            file_type, mime_type, file_size, uploaded_by, user_role,
            now_iso, sha256, description
        ))
        new_id = cur.lastrowid

    return {
        "id": new_id,
        "system_id": system_id,
        "title": title,
        "original_filename": original_filename,
        "file_type": file_type,
        "mime_type": mime_type,
        "file_size": file_size,
        "uploaded_by": uploaded_by,
        "user_role": user_role,
        "uploaded_at": now_iso,
        "sha256_hash": sha256,
        "description": description
    }

def list_documents(system_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Lista todos los documentos almacenados, con filtro opcional por sistema producto."""
    init_documents_db()
    with get_db_connection(DOCS_DB_PATH) as conn:
        if system_id is not None:
            rows = conn.execute("SELECT * FROM documents WHERE system_id = ? ORDER BY id DESC;", (system_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY id DESC;").fetchall()
        return [dict(r) for r in rows]

def get_document_file(document_id: int) -> Optional[Tuple[str, str, str]]:
    """Obtiene la ruta en disco, nombre original y mime-type para descargar un archivo."""
    init_documents_db()
    with get_db_connection(DOCS_DB_PATH) as conn:
        row = conn.execute("SELECT disk_filename, original_filename, mime_type, description FROM documents WHERE id = ?;", (document_id,)).fetchone()
        if not row:
            return None
        disk_filename = row["disk_filename"]
        target_dir = get_uploads_dir()
        disk_path = os.path.join(target_dir, disk_filename)
        if not os.path.exists(disk_path):
            alt_path = os.path.join("/tmp", "econode_documents", disk_filename)
            if os.path.exists(alt_path):
                disk_path = alt_path
            else:
                desc = row["description"] if ("description" in row.keys() if hasattr(row, "keys") else True) else ""
                if desc and "drive.google.com" in desc:
                    return "DRIVE_REDIRECT", row["original_filename"], desc
                return None
        return disk_path, row["original_filename"], row["mime_type"]

def delete_document(document_id: int) -> bool:
    """Elimina un documento y su archivo físico en disco."""
    init_documents_db()
    with get_db_connection(DOCS_DB_PATH) as conn:
        row = conn.execute("SELECT disk_filename FROM documents WHERE id = ?;", (document_id,)).fetchone()
        if not row:
            return False
        disk_path = os.path.join(UPLOADS_DIR, row["disk_filename"])
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
            except Exception:
                pass
        conn.execute("DELETE FROM documents WHERE id = ?;", (document_id,))
        return True

