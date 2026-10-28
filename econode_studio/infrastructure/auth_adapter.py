"""
econode_studio/infrastructure/auth_adapter.py - Adaptador de Persistencia de Autenticación, RBAC e Invitaciones
Compatible dual: Supabase PostgreSQL (Cloud / Vercel Serverless) y SQLite Local (Offline).
"""

import os
import json
from typing import Optional, List, Dict, Any

try:
    from config import settings
    AUTH_DB_PATH = settings.AUTH_DB_PATH
except (ImportError, ValueError):
    try:
        from econode_studio.config import settings
        AUTH_DB_PATH = settings.AUTH_DB_PATH
    except Exception:
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        AUTH_DB_PATH = os.path.join(DATA_DIR, "econode_auth.db")

from .db_connection import get_db_connection

def get_auth_db_connection() -> Any:
    """Retorna una conexión activa optimizada con soporte dual para Supabase PostgreSQL y SQLite."""
    return get_db_connection(AUTH_DB_PATH)


def ensure_auth_tables() -> None:
    """Garantiza la creación independiente y resiliente de tablas e índices para SQLite y Supabase PostgreSQL."""
    # 1. Tabla de invitaciones (aislada para que nunca sea abortada por errores en otras tablas)
    try:
        with get_auth_db_connection() as conn:
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
                conn.execute("CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(lower(email));")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);")
            except Exception:
                pass
    except Exception as e:
        print("[auth_adapter] Warning creating invitations table:", e)

    # 2. Tabla users (en SQLite crea la tabla; en Supabase se ignora si users ya es una vista)
    try:
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
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username));")
            except Exception:
                pass
    except Exception:
        pass

    # 3. Purga de cuentas de prueba tanto en auth_users (Supabase PostgreSQL) como en users (SQLite)
    try:
        with get_auth_db_connection() as conn:
            conn.execute("DELETE FROM auth_users WHERE id IN ('analyst_carla', 'auditor_lead', 'client_elena');")
    except Exception:
        pass
    try:
        with get_auth_db_connection() as conn:
            conn.execute("DELETE FROM users WHERE id IN ('analyst_carla', 'auditor_lead', 'client_elena');")
    except Exception:
        pass
    try:
        with get_auth_db_connection() as conn:
            conn.execute("DELETE FROM product_systems WHERE id = 21 OR code = 'SYS-PET-CIRCULAR-01';")
    except Exception:
        pass


def init_auth_db(default_accounts: Optional[List[Dict[str, Any]]] = None) -> None:
    """Inicializa esquemas y purga accesos de prueba obsoletos."""
    ensure_auth_tables()


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
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            rows = conn.execute("SELECT * FROM auth_users ORDER BY created_at ASC;").fetchall()
            return [_row_to_user_dict(r) for r in rows]
    except Exception:
        with get_auth_db_connection() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC;").fetchall()
            return [_row_to_user_dict(r) for r in rows]


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por su identificador único."""
    if not user_id:
        return None
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("SELECT * FROM auth_users WHERE id = ?;", (user_id,)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass
    with get_auth_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        return _row_to_user_dict(row) if row else None


def get_user_by_identifier(clean: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por ID, username o email."""
    if not clean:
        return None
    c = clean.strip().lower()
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM auth_users
                WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ?;
            """, (c, c, c)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass

    with get_auth_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM users
            WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ?;
        """, (c, c, c)).fetchone()
        return _row_to_user_dict(row) if row else None


def get_user_by_role_or_identifier(clean: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por rol, ID, username o email."""
    if not clean:
        return None
    c = clean.strip().lower()
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM auth_users
                WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ? OR lower(role) = ?
                LIMIT 1;
            """, (c, c, c, c)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass

    with get_auth_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM users
            WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ? OR lower(role) = ?
            LIMIT 1;
        """, (c, c, c, c)).fetchone()
        return _row_to_user_dict(row) if row else None


def insert_user(user_data: Dict[str, Any]) -> None:
    """Inserta un nuevo usuario de forma transaccional, con soporte dual para users y auth_users."""
    perms_json = json.dumps(user_data.get("permissions", []))
    params = (
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
    )
    # Intentar primero en auth_users (si estamos en Supabase PostgreSQL)
    try:
        with get_auth_db_connection() as conn:
            conn.execute("""
                INSERT INTO auth_users (
                    id, username, email, password_hash, display_name,
                    organization, role, role_title, bio, avatar, token, permissions_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, params)
            return
    except Exception:
        pass

    # Fallback o modo local SQLite en users
    with get_auth_db_connection() as conn:
        conn.execute("""
            INSERT INTO users (
                id, username, email, password_hash, display_name,
                organization, role, role_title, bio, avatar, token, permissions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, params)


def update_user_role(user_id: str, new_role: str, new_org: str = "") -> None:
    """Actualiza el rol y organización de un usuario tras aceptar una invitación."""
    if new_role == "auditor":
        perms = ["nom070_certify", "collaborative_comments", "audit_sign", "canvas_view", "upload_documents"]
        role_title = "Auditor Líder ACV (Verificador Oficial NOM-070)"
    elif new_role == "client":
        perms = ["upload_evidence", "reply_comments", "download_reports", "view_final_system", "upload_documents"]
        role_title = "Cliente / Productor Industrial (Empresa Auditada)"
    else:
        perms = ["canvas_edit", "system_create", "connect_flows", "lci_search", "import_csv", "upload_documents", "invite_users"]
        role_title = "Analista de Ciclo de Vida (Creador)"

    perms_json = json.dumps(perms)
    try:
        with get_auth_db_connection() as conn:
            conn.execute(
                "UPDATE auth_users SET role = ?, role_title = ?, organization = coalesce(nullif(?, ''), organization), permissions_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (new_role, role_title, new_org, perms_json, user_id)
            )
            return
    except Exception:
        pass
    try:
        with get_auth_db_connection() as conn:
            conn.execute(
                "UPDATE users SET role = ?, role_title = ?, organization = coalesce(nullif(?, ''), organization), permissions_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (new_role, role_title, new_org, perms_json, user_id)
            )
    except Exception:
        pass


def update_user_token(user_id: str, new_token: str) -> None:
    """Actualiza el token de sesión de un usuario."""
    try:
        with get_auth_db_connection() as conn:
            conn.execute("UPDATE auth_users SET token = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_token, user_id))
            return
    except Exception:
        pass
    with get_auth_db_connection() as conn:
        conn.execute("UPDATE users SET token = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_token, user_id))


# =========================================================================
# GESTIÓN DE INVITACIONES (RBAC: Solo Analistas pueden invitar)
# =========================================================================

def insert_invitation(invitation: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un registro de invitación para Auditor o Cliente."""
    ensure_auth_tables()
    with get_auth_db_connection() as conn:
        clean_email = invitation["email"].strip().lower()
        try:
            conn.execute("""
                UPDATE invitations
                SET status = 'superseded'
                WHERE lower(email) = ? AND status = 'pending';
            """, (clean_email,))
        except Exception:
            pass

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
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("SELECT * FROM invitations WHERE token = ? LIMIT 1;", (clean,)).fetchone()
            return _row_to_invitation_dict(row) if row else None
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()
            try:
                with get_auth_db_connection() as conn:
                    row = conn.execute("SELECT * FROM invitations WHERE token = ? LIMIT 1;", (clean,)).fetchone()
                    return _row_to_invitation_dict(row) if row else None
            except Exception:
                return None
        return None


def get_pending_invitation_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Busca la invitación pendiente más reciente asociada a un correo."""
    clean = (email or "").strip().lower()
    if not clean:
        return None
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM invitations 
                WHERE lower(email) = ? AND status = 'pending'
                ORDER BY created_at DESC LIMIT 1;
            """, (clean,)).fetchone()
            return _row_to_invitation_dict(row) if row else None
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()
            try:
                with get_auth_db_connection() as conn:
                    row = conn.execute("""
                        SELECT * FROM invitations 
                        WHERE lower(email) = ? AND status = 'pending'
                        ORDER BY created_at DESC LIMIT 1;
                    """, (clean,)).fetchone()
                    return _row_to_invitation_dict(row) if row else None
            except Exception:
                return None
        return None


def list_invitations_by_analyst(analyst_id: str) -> List[Dict[str, Any]]:
    """Retorna todas las invitaciones generadas por un analista determinado."""
    try:
        with get_auth_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM invitations 
                WHERE invited_by_id = ?
                ORDER BY created_at DESC;
            """, (analyst_id,)).fetchall()
            return [_row_to_invitation_dict(r) for r in rows]
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()
            try:
                with get_auth_db_connection() as conn:
                    rows = conn.execute("""
                        SELECT * FROM invitations 
                        WHERE invited_by_id = ?
                        ORDER BY created_at DESC;
                    """, (analyst_id,)).fetchall()
                    return [_row_to_invitation_dict(r) for r in rows]
            except Exception:
                return []
        return []


def get_all_invitations() -> List[Dict[str, Any]]:
    """Retorna todas las invitaciones registradas en el sistema."""
    try:
        with get_auth_db_connection() as conn:
            rows = conn.execute("SELECT * FROM invitations ORDER BY created_at DESC;").fetchall()
            return [_row_to_invitation_dict(r) for r in rows]
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()
            try:
                with get_auth_db_connection() as conn:
                    rows = conn.execute("SELECT * FROM invitations ORDER BY created_at DESC;").fetchall()
                    return [_row_to_invitation_dict(r) for r in rows]
            except Exception:
                return []
        return []


def mark_invitation_accepted(token_or_id: str) -> None:
    """Marca una invitación como aceptada tras el registro o inicio de sesión con Google."""
    try:
        with get_auth_db_connection() as conn:
            conn.execute("""
                UPDATE invitations
                SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP
                WHERE token = ? OR id = ?;
            """, (token_or_id, token_or_id))
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()


def cancel_invitation(invitation_id: str, analyst_id: str) -> bool:
    """Cancela o revoca una invitación pendiente generada por un analista."""
    try:
        with get_auth_db_connection() as conn:
            cur = conn.execute("""
                UPDATE invitations
                SET status = 'cancelled'
                WHERE id = ? AND invited_by_id = ? AND status = 'pending';
            """, (invitation_id, analyst_id))
            return bool(cur.rowcount and cur.rowcount > 0)
    except Exception as e:
        if "invitations" in str(e).lower():
            ensure_auth_tables()
        return False
