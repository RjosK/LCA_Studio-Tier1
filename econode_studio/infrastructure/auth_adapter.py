"""
econode_studio/infrastructure/auth_adapter.py - Adaptador SQLite/PostgreSQL de Autenticación, Usuarios e Invitaciones
Maneja la conexión a 'econode_auth.db', el esquema DDL de las tablas 'users' e 'invitations',
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
    """Crea las tablas users e invitations e índices únicos e inserta las cuentas preconfiguradas si no existen."""
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                name TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'auditor',
                invited_by_id TEXT NOT NULL,
                invited_by_name TEXT NOT NULL,
                organization TEXT DEFAULT '',
                system_id INTEGER DEFAULT NULL,
                token TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP DEFAULT NULL
            );
        """)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username));")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(lower(email));")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);")
        except Exception:
            pass

        if default_accounts:
            for d in default_accounts:
                perms = json.dumps(d.get("permissions", []))
                try:
                    # Inserción segura idempotente
                    existing = conn.execute("SELECT id FROM users WHERE id = ?;", (d["id"],)).fetchone()
                    if not existing:
                        conn.execute("""
                            INSERT INTO users (
                                id, username, email, password_hash, display_name,
                                organization, role, role_title, bio, avatar, token, permissions_json
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            d["id"], d["username"], d["email"].lower(), d["password_hash"],
                            d["display_name"], d["organization"], d["role"],
                            d["role_title"], d["bio"], d["avatar"], d["token"], perms
                        ))
                except Exception:
                    pass


def _row_to_user_dict(row: Any) -> Dict[str, Any]:
    """Convierte una fila de SQLite/Postgres a un diccionario deserializando permissions_json y normalizando fechas."""
    d = dict(row)
    try:
        d["permissions"] = json.loads(d.get("permissions_json") or "[]")
    except Exception:
        d["permissions"] = []
    for k in ("created_at", "updated_at"):
        val = d.get(k)
        if val is not None and hasattr(val, "isoformat"):
            d[k] = val.isoformat()
        elif val is not None:
            d[k] = str(val)
    return d


def _row_to_invitation_dict(row: Any) -> Dict[str, Any]:
    """Convierte una fila de invitación a un diccionario con fechas normalizadas."""
    if not row:
        return {}
    d = dict(row)
    for k in ("created_at", "accepted_at"):
        val = d.get(k)
        if val is not None and hasattr(val, "isoformat"):
            d[k] = val.isoformat()
        elif val is not None:
            d[k] = str(val)
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


# =========================================================================
# GESTIÓN DE INVITACIONES (RBAC: Solo Analistas pueden invitar)
# =========================================================================

def insert_invitation(invitation: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un registro de invitación para Auditor o Cliente."""
    with get_auth_db_connection() as conn:
        # Invalidar cualquier invitación previa pendiente para el mismo correo
        clean_email = invitation["email"].strip().lower()
        conn.execute("""
            UPDATE invitations
            SET status = 'superseded'
            WHERE lower(email) = ? AND status = 'pending';
        """, (clean_email,))

        conn.execute("""
            INSERT INTO invitations (
                id, email, name, role, invited_by_id, invited_by_name,
                organization, system_id, token, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            invitation["id"],
            clean_email,
            invitation.get("name", "").strip(),
            invitation["role"],
            invitation["invited_by_id"],
            invitation.get("invited_by_name", ""),
            invitation.get("organization", ""),
            invitation.get("system_id"),
            invitation["token"],
            invitation.get("status", "pending")
        ))
    return invitation


def get_invitation_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Busca una invitación válida por su token criptográfico."""
    clean = (token or "").strip()
    if not clean:
        return None
    with get_auth_db_connection() as conn:
        row = conn.execute("SELECT * FROM invitations WHERE token = ? LIMIT 1;", (clean,)).fetchone()
        return _row_to_invitation_dict(row) if row else None


def get_pending_invitation_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Busca la invitación pendiente más reciente asociada a un correo."""
    clean = (email or "").strip().lower()
    if not clean:
        return None
    with get_auth_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM invitations 
            WHERE lower(email) = ? AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1;
        """, (clean,)).fetchone()
        return _row_to_invitation_dict(row) if row else None


def list_invitations_by_analyst(analyst_id: str) -> List[Dict[str, Any]]:
    """Retorna todas las invitaciones generadas por un analista determinado."""
    with get_auth_db_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM invitations 
            WHERE invited_by_id = ?
            ORDER BY created_at DESC;
        """, (analyst_id,)).fetchall()
        return [_row_to_invitation_dict(r) for r in rows]


def get_all_invitations() -> List[Dict[str, Any]]:
    """Retorna todas las invitaciones registradas en el sistema."""
    with get_auth_db_connection() as conn:
        rows = conn.execute("SELECT * FROM invitations ORDER BY created_at DESC;").fetchall()
        return [_row_to_invitation_dict(r) for r in rows]


def mark_invitation_accepted(token_or_id: str) -> None:
    """Marca una invitación como aceptada tras el registro o inicio de sesión con Google."""
    with get_auth_db_connection() as conn:
        conn.execute("""
            UPDATE invitations
            SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE token = ? OR id = ?;
        """, (token_or_id, token_or_id))


def cancel_invitation(invitation_id: str, analyst_id: str) -> bool:
    """Cancela o revoca una invitación pendiente generada por un analista."""
    with get_auth_db_connection() as conn:
        cur = conn.execute("""
            UPDATE invitations
            SET status = 'cancelled'
            WHERE id = ? AND invited_by_id = ? AND status = 'pending';
        """, (invitation_id, analyst_id))
        return bool(cur.rowcount and cur.rowcount > 0)
