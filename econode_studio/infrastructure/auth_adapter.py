import time
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

try:
    from domain.api_key import ApiKey
except (ImportError, ValueError):
    from econode_studio.domain.api_key import ApiKey

def get_auth_db_connection() -> Any:
    """Retorna una conexión activa optimizada con soporte dual para Supabase PostgreSQL y SQLite."""
    return get_db_connection(AUTH_DB_PATH)


DEFAULT_USERS: List[Dict[str, Any]] = [
    {
        "id": "usr_gsi_8c09ad66",
        "username": "carla.mendez",
        "email": "carla.mendez@econode.io",
        "password_hash": "eeb86cbde7b5c535aabbdc1adb11f124c32742b59940f3fe405f03da4bf14bea",
        "display_name": "Carla Méndez",
        "organization": "BioPack Industrial S.A. de C.V.",
        "role": "analyst",
        "role_title": "Analista Senior de Ciclo de Vida",
        "bio": "Especialista en ACV ISO 14040/14044 y EPD EN 15804.",
        "avatar": "",
        "token": "",
        "permissions": ["systems:read", "systems:write", "epd:write", "audit:read", "export:all"]
    },
    {
        "id": "usr_gsi_56924c8c",
        "username": "auditor.lca",
        "email": "auditor.test.oficial@ecometrics.io",
        "password_hash": "eeb86cbde7b5c535aabbdc1adb11f124c32742b59940f3fe405f03da4bf14bea",
        "display_name": "Dr. Roberto Silva (Auditor NOM-070)",
        "organization": "EcoMetrics Certification Global",
        "role": "auditor",
        "role_title": "Auditor Líder ISO 14040/14044",
        "bio": "Verificación y auditoría de declaraciones ambientales.",
        "avatar": "",
        "token": "",
        "permissions": ["systems:read", "audit:write", "export:report"]
    },
    {
        "id": "usr_gsi_2472af0c",
        "username": "cliente.biopack",
        "email": "cliente.test.oficial@biopack-industrial.mx",
        "password_hash": "eeb86cbde7b5c535aabbdc1adb11f124c32742b59940f3fe405f03da4bf14bea",
        "display_name": "Ing. Sofia Garza (Cliente Productor)",
        "organization": "BioPack Industrial S.A. de C.V.",
        "role": "client",
        "role_title": "Director de Sostenibilidad y Cadena de Valor",
        "bio": "Revisión de huella de carbono y reportes de sostenibilidad corporativa.",
        "avatar": "",
        "token": "",
        "permissions": ["systems:read", "export:report"]
    }
]

def generate_session_token(user_id: str, role: str) -> str:
    """Genera un token firmado con timestamp para sesión segura en base64."""
    try:
        from application.auth_service import generate_session_token as _gen
        return _gen(user_id, role)
    except (ImportError, ValueError):
        from econode_studio.application.auth_service import generate_session_token as _gen
        return _gen(user_id, role)



_auth_tables_ensured = False
_USERS_CACHE = None
_USERS_CACHE_TIME = 0.0
_USERS_CACHE_TTL = 60.0

def invalidate_users_cache():
    global _USERS_CACHE, _USERS_CACHE_TIME
    _USERS_CACHE = None
    _USERS_CACHE_TIME = 0.0

def ensure_auth_tables() -> None:
    """Garantiza la creación independiente y resiliente de tablas e índices para SQLite y Supabase PostgreSQL."""
    global _auth_tables_ensured
    if _auth_tables_ensured or getattr(settings, "IS_POSTGRES", False):
        return
    _auth_tables_ensured = True
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

    # 4. Tabla user_api_keys para Personal Access Tokens (MCP e integraciones externas)
    try:
        with get_auth_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    organization_id TEXT DEFAULT '',
                    name TEXT NOT NULL,
                    key_prefix TEXT NOT NULL,
                    hashed_secret TEXT UNIQUE NOT NULL,
                    scopes_json TEXT DEFAULT '["all"]',
                    rate_limit_per_minute INTEGER DEFAULT 120,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP DEFAULT NULL,
                    last_used_at TIMESTAMP DEFAULT NULL,
                    revoked_at TIMESTAMP DEFAULT NULL
                );
            """)
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON user_api_keys(hashed_secret);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user ON user_api_keys(user_id);")
            except Exception:
                pass
    except Exception as e:
        print("[auth_adapter] Warning creating user_api_keys table:", e)


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
    """Recupera la lista completa de usuarios registrados (con caché de alta velocidad)."""
    global _USERS_CACHE, _USERS_CACHE_TIME
    now = time.time()
    if _USERS_CACHE is not None and (now - _USERS_CACHE_TIME) < _USERS_CACHE_TTL:
        return _USERS_CACHE

    ensure_auth_tables()
    rows = None
    try:
        with get_auth_db_connection() as conn:
            try:
                rows = conn.execute("SELECT * FROM auth_users ORDER BY created_at ASC;").fetchall()
            except Exception:
                rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC;").fetchall()
    except Exception:
        rows = []

    res = [_row_to_user_dict(r) for r in (rows or [])]
    if not res:
        res = [dict(u) for u in DEFAULT_USERS]
    _USERS_CACHE = res
    _USERS_CACHE_TIME = now
    return res

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
    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass
    for u in DEFAULT_USERS:
        if u["id"] == user_id:
            return dict(u)
    return None


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

    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM users
                WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ?;
            """, (c, c, c)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass

    for u in DEFAULT_USERS:
        if c in (u["id"].lower(), u["username"].lower(), u["email"].lower()):
            return dict(u)
    return None


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

    try:
        with get_auth_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM users
                WHERE lower(id) = ? OR lower(username) = ? OR lower(email) = ? OR lower(role) = ?
                LIMIT 1;
            """, (c, c, c, c)).fetchone()
            if row:
                return _row_to_user_dict(row)
    except Exception:
        pass

    for u in DEFAULT_USERS:
        if c in (u["id"].lower(), u["username"].lower(), u["email"].lower(), u["role"].lower()):
            return dict(u)
    return None


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


# -----------------------------------------------------------------------------
# GESTIÓN Y PERSISTENCIA DE PERSONAL ACCESS TOKENS (API KEYS & MCP)
# -----------------------------------------------------------------------------
_RATE_LIMIT_BUCKETS: Dict[str, List[float]] = {}


def _row_to_api_key(row: Any) -> ApiKey:
    """Convierte un registro de user_api_keys a entidad ApiKey."""
    d = dict(row)
    scopes = []
    try:
        scopes = json.loads(d.get("scopes_json") or '["all"]')
    except Exception:
        scopes = ["all"]

    return ApiKey(
        id=str(d.get("id")),
        user_id=str(d.get("user_id")),
        organization_id=str(d.get("organization_id") or ""),
        name=str(d.get("name") or "API Key"),
        key_prefix=str(d.get("key_prefix") or ""),
        hashed_secret=str(d.get("hashed_secret") or ""),
        scopes=scopes,
        rate_limit_per_minute=int(d.get("rate_limit_per_minute") or 120),
        created_at=str(d.get("created_at") or ""),
        expires_at=d.get("expires_at"),
        last_used_at=d.get("last_used_at"),
        revoked_at=d.get("revoked_at")
    )


def save_api_key(api_key: ApiKey) -> bool:
    """Registra una nueva clave de API en la base de datos."""
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            conn.execute("""
                INSERT INTO user_api_keys (
                    id, user_id, organization_id, name, key_prefix, hashed_secret,
                    scopes_json, rate_limit_per_minute, created_at, expires_at,
                    last_used_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                api_key.id,
                api_key.user_id,
                api_key.organization_id,
                api_key.name,
                api_key.key_prefix,
                api_key.hashed_secret,
                json.dumps(api_key.scopes),
                api_key.rate_limit_per_minute,
                api_key.created_at,
                api_key.expires_at,
                api_key.last_used_at,
                api_key.revoked_at
            ))
            return True
    except Exception as e:
        print("[auth_adapter] Error saving api key:", e)
        return False


def get_api_key_by_hash(hashed_secret: str) -> Optional[ApiKey]:
    """Obtiene y valida una clave de API a partir de su hash SHA-256."""
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            cur = conn.execute("""
                SELECT * FROM user_api_keys
                WHERE hashed_secret = ? AND revoked_at IS NULL
                LIMIT 1;
            """, (hashed_secret,))
            row = cur.fetchone()
            if row:
                return _row_to_api_key(row)
            return None
    except Exception as e:
        if "user_api_keys" in str(e).lower():
            ensure_auth_tables()
        return None


def list_user_api_keys(user_id: str) -> List[ApiKey]:
    """Lista todas las claves activas e históricas pertenecientes a un usuario."""
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            cur = conn.execute("""
                SELECT * FROM user_api_keys
                WHERE user_id = ?
                ORDER BY created_at DESC;
            """, (user_id,))
            rows = cur.fetchall()
            return [_row_to_api_key(r) for r in rows]
    except Exception as e:
        if "user_api_keys" in str(e).lower():
            ensure_auth_tables()
        return []


def revoke_api_key(key_id: str, user_id: str) -> bool:
    """Revoca inmediatamente una clave de API marcando revoked_at."""
    ensure_auth_tables()
    try:
        with get_auth_db_connection() as conn:
            cur = conn.execute("""
                UPDATE user_api_keys
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND revoked_at IS NULL;
            """, (key_id, user_id))
            return bool(cur.rowcount and cur.rowcount > 0)
    except Exception as e:
        return False


def update_api_key_last_used(key_id: str) -> None:
    """Actualiza la marca temporal de último uso de la clave."""
    try:
        with get_auth_db_connection() as conn:
            conn.execute("""
                UPDATE user_api_keys
                SET last_used_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (key_id,))
    except Exception:
        pass


def check_and_increment_rate_limit(key_id: str, limit_per_minute: int = 120) -> bool:
    """Control de tasa en memoria por ventana deslizante de 60 segundos."""
    now = time.time()
    window_start = now - 60.0
    timestamps = _RATE_LIMIT_BUCKETS.get(key_id, [])
    # Filtrar timestamps dentro de la ventana
    valid_timestamps = [t for t in timestamps if t > window_start]
    if len(valid_timestamps) >= limit_per_minute:
        _RATE_LIMIT_BUCKETS[key_id] = valid_timestamps
        return False
    valid_timestamps.append(now)
    _RATE_LIMIT_BUCKETS[key_id] = valid_timestamps
    return True
