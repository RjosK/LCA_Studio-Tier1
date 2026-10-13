"""
econode_studio/infrastructure/auth_adapter.py - Adaptador SQLite de Autenticación y Cuentas de Usuario
Maneja la conexión a 'econode_auth.db', el esquema DDL de la tabla 'users',
índices únicos en modo WAL y la sincronización con 'credenciales_demo.txt'.
"""

import os
import json
import sqlite3
import time
from typing import Dict, List, Any, Optional

try:
    from config import settings
    AUTH_DB_PATH = settings.AUTH_DB_PATH
    CREDENCIALES_TXT_PATH = settings.CREDENCIALES_TXT_PATH
except (ImportError, ValueError):
    try:
        from econode_studio.config import settings
        AUTH_DB_PATH = settings.AUTH_DB_PATH
        CREDENCIALES_TXT_PATH = settings.CREDENCIALES_TXT_PATH
    except Exception:
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        AUTH_DB_PATH = os.path.join(DATA_DIR, "econode_auth.db")
        CREDENCIALES_TXT_PATH = os.path.join(DATA_DIR, "credenciales_demo.txt")


from .db_connection import get_db_connection

def get_auth_db_connection() -> Any:
    """Retorna una conexión activa optimizada con soporte dual para Supabase PostgreSQL y SQLite."""
    return get_db_connection(AUTH_DB_PATH)


def init_auth_db(default_accounts: Optional[List[Dict[str, Any]]] = None) -> None:
    """Crea la tabla users e índices únicos e inserta las cuentas preconfiguradas si no existen."""
    if getattr(settings, "IS_POSTGRES", False):
        return
    with get_auth_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                organization TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'analyst',
                role_title TEXT DEFAULT '',
                bio TEXT DEFAULT '',
                avatar TEXT DEFAULT '',
                token TEXT DEFAULT '',
                permissions_json TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username));")

        if default_accounts:
            for d in default_accounts:
                perms = json.dumps(d.get("permissions", []))
                conn.execute("""
                    INSERT INTO users (
                        id, username, email, password_hash, display_name,
                        organization, role, role_title, bio, avatar, token, permissions_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        password_hash = CASE WHEN users.password_hash = '' THEN excluded.password_hash ELSE users.password_hash END,
                        display_name = excluded.display_name,
                        role = excluded.role;
                """, (
                    d["id"], d["username"], d["email"].lower(), d["password_hash"],
                    d["display_name"], d["organization"], d["role"],
                    d["role_title"], d["bio"], d["avatar"], d["token"], perms
                ))


def _row_to_user_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convierte una fila de SQLite a un diccionario deserializando permissions_json."""
    d = dict(row)
    try:
        d["permissions"] = json.loads(d.get("permissions_json") or "[]")
    except Exception:
        d["permissions"] = []
    return d


def get_all_users() -> List[Dict[str, Any]]:
    """Recupera la lista completa de usuarios registrados."""
    with get_auth_db_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC;").fetchall()
        return [_row_to_user_dict(r) for r in rows]


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por su clave primaria ID."""
    with get_auth_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        return _row_to_user_dict(row) if row else None


def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por ID, username o correo electrónico (case-insensitive)."""
    clean = (identifier or "").strip().lower()
    if not clean:
        return None
    with get_auth_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM users
            WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ?;
        """, (clean, clean, clean)).fetchone()
        return _row_to_user_dict(row) if row else None


def get_user_by_role_or_identifier(clean: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por rol, ID, username o email (para cambio de cuenta demo)."""
    with get_auth_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM users
            WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ? OR lower(role) = ?
            LIMIT 1;
        """, (clean, clean, clean, clean)).fetchone()
        return _row_to_user_dict(row) if row else None


def insert_user(user_data: Dict[str, Any]) -> None:
    """Inserta un nuevo usuario de forma transaccional."""
    with get_auth_db_connection() as conn:
        perms_json = json.dumps(user_data.get("permissions", []))
        conn.execute("""
            INSERT INTO users (
                id, username, email, password_hash, display_name,
                organization, role, role_title, bio, avatar, token, permissions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            user_data["id"],
            user_data["username"],
            user_data["email"].lower(),
            user_data["password_hash"],
            user_data["display_name"],
            user_data.get("organization", ""),
            user_data.get("role", "analyst"),
            user_data.get("role_title", ""),
            user_data.get("bio", ""),
            user_data.get("avatar", ""),
            user_data.get("token", ""),
            perms_json
        ))


def update_user_token(user_id: str, new_token: str) -> None:
    """Actualiza el token de sesión de un usuario."""
    with get_auth_db_connection() as conn:
        conn.execute("UPDATE users SET token = ? WHERE id = ?;", (new_token, user_id))


def sync_credenciales_txt(name: str, email: str, username: str, role: str, plain_pass: str) -> None:
    """Registra en el archivo de referencia interna las credenciales generadas."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n- [{timestamp}] {name} ({role})\n  Correo: {email}\n  Usuario: {username}\n  Contraseña: {plain_pass}\n"
        with open(CREDENCIALES_TXT_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Aviso al escribir en credenciales_demo.txt: {e}")

