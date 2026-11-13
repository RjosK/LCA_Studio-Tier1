"""
econode_studio/infrastructure/database_adapter.py - Adaptador SQLite de Alta Disponibilidad
Conecta a las bases ecoinvent 3.12 y lcia_engine.db para operaciones de Tier 1 sin cálculos matriciales pesados.
"""

import sqlite3
import os
import json
import re
import uuid
from typing import Dict, List, Any, Optional

try:
    from config import settings
    ECOINVENT_DB_PATH = settings.ECOINVENT_DB_PATH
except (ImportError, ValueError):
    try:
        from econode_studio.config import settings
        ECOINVENT_DB_PATH = settings.ECOINVENT_DB_PATH
    except Exception:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ECOINVENT_DB_PATH = os.path.join(BASE_DIR, "ecoinvent", "ecoinvent_312.db")

from .db_connection import get_db_connection

_PRODUCT_SYSTEMS_COLUMNS_CHECKED = False
_CUSTOM_TABLES_ENSURED = False

def get_active_db_connection() -> Any:
    """Retorna una conexión activa optimizada con soporte dual para Supabase PostgreSQL y SQLite."""
    return get_db_connection(ECOINVENT_DB_PATH)

# -----------------------------------------------------------------------------
def ensure_custom_tables_and_views(conn: Any):
    """Garantiza la infraestructura de procesos y flujos propios creados por el usuario."""
    global _CUSTOM_TABLES_ENSURED
    if _CUSTOM_TABLES_ENSURED:
        return
    if getattr(settings, "IS_POSTGRES", False):
        _CUSTOM_TABLES_ENSURED = True
        return
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS custom_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            flow_type TEXT NOT NULL DEFAULT 'PRODUCT_FLOW',
            category_name TEXT DEFAULT 'Custom processes & flows',
            unit_symbol TEXT DEFAULT 'kg',
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS custom_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category_id INTEGER DEFAULT 999999,
            location TEXT DEFAULT 'GLO',
            reference_flow_id TEXT,
            reference_amount REAL DEFAULT 1.0,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS custom_exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_id INTEGER NOT NULL,
            flow_id TEXT NOT NULL,
            is_input INTEGER NOT NULL CHECK(is_input IN (0, 1)),
            exchange_type TEXT NOT NULL,
            amount REAL NOT NULL,
            unit_symbol TEXT,
            default_provider_id INTEGER,
            description TEXT
        );

        INSERT OR IGNORE INTO TBL_CATEGORIES (ID, REF_ID, NAME, MODEL_TYPE, DESCRIPTION)
        VALUES (999999, 'cat-user-propios', 'Custom processes & flows', 'PROCESS', 'Processes and flows created by the user in ECONODE Studio');

        DROP VIEW IF EXISTS flows;
        CREATE VIEW flows AS
        SELECT 
            cast(f.ID as text) as id,
            f.REF_ID as code,
            f.NAME as name,
            f.FLOW_TYPE as flow_type,
            coalesce(cat.NAME, 'General') as category_name,
            coalesce(u.NAME, 'kg') as unit_symbol,
            f.DESCRIPTION as description
        FROM TBL_FLOWS f
        LEFT JOIN TBL_CATEGORIES cat ON f.F_CATEGORY = cat.ID
        LEFT JOIN TBL_FLOW_PROPERTIES fp ON f.F_REFERENCE_FLOW_PROPERTY = fp.ID
        LEFT JOIN TBL_UNIT_GROUPS ug ON fp.F_UNIT_GROUP = ug.ID
        LEFT JOIN TBL_UNITS u ON ug.F_REFERENCE_UNIT = u.ID
        UNION ALL
        SELECT
            cf.code as id,
            cf.code,
            cf.name,
            cf.flow_type,
            coalesce(cf.category_name, 'Custom processes & flows') as category_name,
            coalesce(cf.unit_symbol, 'kg') as unit_symbol,
            cf.description
        FROM custom_flows cf;
        """)
        _CUSTOM_TABLES_ENSURED = True
    except Exception as e:
        pass


def create_user_custom_flow(
    conn: sqlite3.Connection,
    name: str,
    flow_type: str = "PRODUCT_FLOW",
    unit_symbol: str = "kg",
    description: str = "",
    code: Optional[str] = None
) -> Dict[str, Any]:
    """Crea un nuevo flujo propio en la base de datos LCI (categoría Custom processes & flows)."""
    ensure_custom_tables_and_views(conn)
    if not code:
        import uuid
        code = f"FL_CUSTOM_{uuid.uuid4().hex[:8].upper()}"
    with conn:
        cur = conn.execute("""
            INSERT INTO custom_flows (code, name, flow_type, category_name, unit_symbol, description)
            VALUES (?, ?, ?, 'Custom processes & flows', ?, ?);
        """, (code, name, flow_type, unit_symbol or "kg", description))
        row_id = cur.lastrowid
    return {
        "id": code,
        "code": code,
        "name": name,
        "flow_type": flow_type,
        "category_name": "Custom processes & flows",
        "unit_symbol": unit_symbol or "kg",
        "description": description
    }


def create_user_custom_process(
    conn: sqlite3.Connection,
    name: str,
    code: Optional[str] = None,
    category_id: int = 999999,
    location: str = "GLO",
    reference_flow_name: str = "",
    reference_amount: float = 1.0,
    reference_unit: str = "kg",
    description: str = "",
    inputs: Optional[List[Dict[str, Any]]] = None,
    outputs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Crea un proceso unitario en blanco propio del usuario con sus intercambios,
    registrándolo en custom_processes y custom_exchanges para aparecer en 'Custom processes & flows'.
    """
    ensure_custom_tables_and_views(conn)
    import uuid
    if not code:
        code = f"PR_CUSTOM_{uuid.uuid4().hex[:8].upper()}"

    ref_flow_id = f"FL_REF_{uuid.uuid4().hex[:8].upper()}"
    ref_name = reference_flow_name or f"Output of {name}"
    create_user_custom_flow(
        conn,
        name=ref_name,
        flow_type="PRODUCT_FLOW",
        unit_symbol=reference_unit or "kg",
        description=f"Reference flow for {name}",
        code=ref_flow_id
    )

    with conn:
        cur = conn.execute("""
            INSERT INTO custom_processes (code, name, category_id, location, reference_flow_id, reference_amount, description)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (code, name, category_id, location or "GLO", ref_flow_id, reference_amount or 1.0, description))
        custom_pk = cur.lastrowid
        unified_id = custom_pk + 1000000

        # Intercambio de producción (salida cuantitativa de referencia)
        conn.execute("""
            INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description)
            VALUES (?, ?, 0, 'production', ?, ?, NULL, ?);
        """, (unified_id, ref_flow_id, reference_amount or 1.0, reference_unit or "kg", f"Reference flow: {ref_name}"))

        # Registrar insumos / inputs si se proporcionan
        for inp in (inputs or []):
            f_id = inp.get("flow_id")
            f_name = inp.get("name") or "Input"
            f_unit = inp.get("unit") or inp.get("unit_symbol") or "kg"
            f_amt = float(inp.get("amount") or 1.0)
            if not f_id:
                f_id = f"FL_INP_{uuid.uuid4().hex[:8].upper()}"
                create_user_custom_flow(conn, name=f_name, flow_type="PRODUCT_FLOW", unit_symbol=f_unit, code=f_id)
            conn.execute("""
                INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description)
                VALUES (?, ?, 1, 'technosphere', ?, ?, NULL, ?);
            """, (unified_id, str(f_id), f_amt, f_unit, inp.get("provider") or ""))

        # Registrar salidas / outputs adicionales (residuos y emisiones)
        for out in (outputs or []):
            if out.get("is_reference"):
                continue  # Ya registrado como production exchange
            f_id = out.get("flow_id")
            f_name = out.get("name") or "Output"
            f_unit = out.get("unit") or out.get("unit_symbol") or "kg"
            f_amt = float(out.get("amount") or 1.0)
            f_type = "waste" if out.get("is_waste") else ("biosphere" if out.get("is_elementary") else "technosphere")
            flow_cls = "WASTE_FLOW" if out.get("is_waste") else ("ELEMENTARY_FLOW" if out.get("is_elementary") else "PRODUCT_FLOW")
            if not f_id:
                f_id = f"FL_OUT_{uuid.uuid4().hex[:8].upper()}"
                create_user_custom_flow(conn, name=f_name, flow_type=flow_cls, unit_symbol=f_unit, code=f_id)
            conn.execute("""
                INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description)
                VALUES (?, ?, 0, ?, ?, ?, NULL, ?);
            """, (unified_id, str(f_id), f_type, f_amt, f_unit, out.get("provider") or out.get("description") or ""))

    sheet = get_process_technical_sheet(conn, unified_id)
    return sheet or {
        "id": unified_id,
        "code": code,
        "name": name,
        "location": location,
        "category_id": category_id,
        "category_name": "Custom processes & flows",
        "reference_amount": reference_amount,
        "unit": reference_unit,
        "inputs": inputs or [],
        "outputs": outputs or []
    }


def delete_user_custom_process(conn: sqlite3.Connection, process_id: Any) -> bool:
    """Elimina permanentemente un proceso propio creado por el usuario y sus intercambios asociados."""
    ensure_custom_tables_and_views(conn)
    with conn:
        conn.execute("DELETE FROM custom_exchanges WHERE process_id = ? OR process_id = ?;", (process_id, str(process_id)))
        cur = conn.execute("DELETE FROM custom_processes WHERE id = ? OR code = ?;", (process_id, str(process_id)))
        return cur.rowcount > 0


def delete_user_custom_flow(conn: sqlite3.Connection, flow_id: Any) -> bool:
    """Elimina permanentemente un flujo propio creado por el usuario."""
    ensure_custom_tables_and_views(conn)
    with conn:
        cur = conn.execute("DELETE FROM custom_flows WHERE id = ? OR code = ?;", (flow_id, str(flow_id)))
        return cur.rowcount > 0


def ensure_product_systems_columns(conn: Any):
    """Garantiza la existencia de columnas de propietario, metadatos y proyectos en product_systems (SQLite y PostgreSQL)."""
    global _PRODUCT_SYSTEMS_COLUMNS_CHECKED
    if _PRODUCT_SYSTEMS_COLUMNS_CHECKED:
        return
    if getattr(settings, "IS_POSTGRES", False):
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id BIGSERIAL PRIMARY KEY,
                        code VARCHAR(64) NOT NULL UNIQUE,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        category VARCHAR(128) DEFAULT 'General',
                        owner_id TEXT DEFAULT 'analyst_carla',
                        owner_email VARCHAR(255) DEFAULT 'carla.mendez@econode.io',
                        owner_name VARCHAR(255) DEFAULT 'Carla Méndez',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                pg_cols = [
                    ("project_id", "BIGINT DEFAULT NULL"),
                    ("owner_id", "TEXT DEFAULT 'analyst_carla'"),
                    ("owner_email", "VARCHAR(255) DEFAULT 'carla.mendez@econode.io'"),
                    ("owner_name", "VARCHAR(255) DEFAULT 'Carla Méndez'"),
                    ("owner_role", "VARCHAR(32) DEFAULT 'analyst'"),
                    ("owner_org", "VARCHAR(255) DEFAULT 'BioPack Industrial S.A. de C.V.'"),
                    ("category", "VARCHAR(128) DEFAULT 'Polímeros'"),
                    ("geography", "VARCHAR(64) DEFAULT '[MX]'"),
                    ("status", "VARCHAR(64) DEFAULT 'in_audit'"),
                    ("compliance_rate", "VARCHAR(32) DEFAULT '100.0%'"),
                    ("collaborators_json", "TEXT DEFAULT '[]'"),
                    ("parameters_json", "TEXT DEFAULT '{}'")
                ]
                for col_name, col_def in pg_cols:
                    try:
                        conn.execute(f"ALTER TABLE product_systems ADD COLUMN IF NOT EXISTS {col_name} {col_def};")
                    except Exception:
                        pass
            _PRODUCT_SYSTEMS_COLUMNS_CHECKED = True
        except Exception as e:
            pass
        return

    ensure_custom_tables_and_views(conn)
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'General',
            owner_id TEXT DEFAULT 'analyst_carla',
            owner_email TEXT DEFAULT 'carla.mendez@econode.io',
            owner_name TEXT DEFAULT 'Carla Méndez',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cur = conn.execute("PRAGMA table_info(product_systems);")
        cols = {c[1] for c in cur.fetchall()}
        new_cols = [
            ("owner_id", "TEXT DEFAULT 'analyst_carla'"),
            ("owner_email", "TEXT DEFAULT 'carla.mendez@econode.io'"),
            ("owner_name", "TEXT DEFAULT 'Carla Méndez'"),
            ("owner_role", "TEXT DEFAULT 'analyst'"),
            ("owner_org", "TEXT DEFAULT 'BioPack Industrial S.A. de C.V.'"),
            ("category", "TEXT DEFAULT 'Polímeros'"),
            ("geography", "TEXT DEFAULT '[MX]'"),
            ("status", "TEXT DEFAULT 'in_audit'"),
            ("compliance_rate", "TEXT DEFAULT '100.0%'"),
            ("collaborators_json", "TEXT DEFAULT '[]'"),
            ("parameters_json", "TEXT DEFAULT '{}'"),
            ("project_id", "INTEGER DEFAULT NULL")
        ]
        with conn:
            for col_name, col_def in new_cols:
                if col_name not in cols:
                    conn.execute(f"ALTER TABLE product_systems ADD COLUMN {col_name} {col_def};")
        _PRODUCT_SYSTEMS_COLUMNS_CHECKED = True
    except Exception as e:
        pass

# -----------------------------------------------------------------------------
# 1. SISTEMAS PRODUCTO & DASHBOARD
# -----------------------------------------------------------------------------
def list_product_systems(
    conn: sqlite3.Connection,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de sistemas producto registrados con aislamiento multi-usuario y resiliencia dual.
    """
    ensure_product_systems_columns(conn)

    clean_email = (user_email or "").strip().lower()
    clean_uid = (user_id or "").strip().lower()

    admin_emails = [e.strip().lower() for e in getattr(settings, "ADMIN_EMAILS", "").split(",") if e.strip()]
    admin_emails.extend(["josuearenteriaz09@gmail.com", "carla.mendez@econode.io"])

    is_local_sqlite = not getattr(settings, "IS_POSTGRES", False)
    is_admin = clean_email in admin_emails or user_role == "admin"

    # Consulta principal con JOIN a proyectos
    query_full = """
        SELECT s.id, s.name, s.code, s.reference_process_id, s.target_amount,
               coalesce(s.description, '') as description,
               s.owner_id, s.owner_email, s.owner_name, s.owner_role, s.owner_org,
               coalesce(s.category, 'General') as category,
               coalesce(s.geography, '[MX]') as geography,
               coalesce(s.status, 'draft') as status,
               coalesce(s.compliance_rate, '0.0%') as compliance_rate,
               coalesce(s.collaborators_json, '[]') as collaborators_json,
               s.project_id,
               pr.name as project_name,
               pr.code as project_code,
               p.name as reference_process_name,
               f.unit_symbol as reference_unit
        FROM product_systems s
        LEFT JOIN projects pr ON s.project_id = pr.id
        LEFT JOIN processes p ON s.reference_process_id = p.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id
    """

    # Consulta fallback sin JOIN a proyectos por si la tabla no está creada aún en Supabase
    query_fallback = """
        SELECT s.id, s.name, s.code, s.reference_process_id, s.target_amount,
               coalesce(s.description, '') as description,
               s.owner_id, s.owner_email, s.owner_name, s.owner_role, s.owner_org,
               coalesce(s.category, 'General') as category,
               coalesce(s.geography, '[MX]') as geography,
               coalesce(s.status, 'draft') as status,
               coalesce(s.compliance_rate, '0.0%') as compliance_rate,
               coalesce(s.collaborators_json, '[]') as collaborators_json,
               NULL as project_id,
               NULL as project_name,
               NULL as project_code,
               p.name as reference_process_name,
               f.unit_symbol as reference_unit
        FROM product_systems s
        LEFT JOIN processes p ON s.reference_process_id = p.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id
    """

    rows = []
    # 1. Intentar consulta completa
    try:
        if (not clean_email and not clean_uid) or is_local_sqlite or is_admin:
            rows = conn.execute(query_full + " ORDER BY s.id DESC;").fetchall()
        else:
            email_like = f"%{clean_email}%" if clean_email else "%nomatch%"
            q = query_full + """
                WHERE lower(coalesce(s.owner_email, '')) = ? 
                   OR lower(coalesce(s.owner_id, '')) = ? 
                   OR lower(coalesce(s.owner_name, '')) = ?
                   OR lower(coalesce(s.owner_name, '')) LIKE ?
                   OR s.collaborators_json LIKE ?
                ORDER BY s.id DESC;
            """
            rows = conn.execute(q, (clean_email, clean_uid, clean_email, email_like, email_like)).fetchall()
    except Exception as e:
        # Fallback a consulta segura
        try:
            if (not clean_email and not clean_uid) or is_local_sqlite or is_admin:
                rows = conn.execute(query_fallback + " ORDER BY s.id DESC;").fetchall()
            else:
                email_like = f"%{clean_email}%" if clean_email else "%nomatch%"
                q = query_fallback + """
                    WHERE lower(coalesce(s.owner_email, '')) = ? 
                       OR lower(coalesce(s.owner_id, '')) = ? 
                       OR lower(coalesce(s.owner_name, '')) = ?
                       OR lower(coalesce(s.owner_name, '')) LIKE ?
                       OR s.collaborators_json LIKE ?
                    ORDER BY s.id DESC;
                """
                rows = conn.execute(q, (clean_email, clean_uid, clean_email, email_like, email_like)).fetchall()
        except Exception as e2:
            rows = []

    results = []
    for r in rows:
        sys_id = r["id"]
        try:
            nodes_count = conn.execute("SELECT count(*) FROM product_system_nodes WHERE system_id = ?", (sys_id,)).fetchone()[0]
        except Exception:
            nodes_count = 0

        collabs = []
        raw_c = r["collaborators_json"] if "collaborators_json" in r.keys() and r["collaborators_json"] else "[]"
        try:
            collabs = json.loads(raw_c) if isinstance(raw_c, str) else (raw_c or [])
        except Exception:
            collabs = []

        results.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"] or f"SYS_{r['id']:04d}",
            "reference_process_id": r["reference_process_id"],
            "reference_process_name": r["reference_process_name"] or "Proceso Principal",
            "target_amount": float(r["target_amount"] or 1.0),
            "unit": r["reference_unit"] or "u",
            "description": r["description"],
            "nodes_count": nodes_count,
            "status": r["status"] if "status" in r.keys() and r["status"] else "draft",
            "compliance_rate": r["compliance_rate"] if "compliance_rate" in r.keys() and r["compliance_rate"] else "0.0%",
            "owner_id": r["owner_id"] if "owner_id" in r.keys() and r["owner_id"] else "analyst_carla",
            "owner_email": r["owner_email"] if "owner_email" in r.keys() and r["owner_email"] else "",
            "owner_name": r["owner_name"] if "owner_name" in r.keys() and r["owner_name"] else "Carla Méndez",
            "owner_role": r["owner_role"] if "owner_role" in r.keys() and r["owner_role"] else "Analista de ACV",
            "owner_org": r["owner_org"] if "owner_org" in r.keys() and r["owner_org"] else "BioPack Industrial S.A. de C.V.",
            "category": r["category"] if "category" in r.keys() and r["category"] else "Polímeros",
            "geography": r["geography"] if "geography" in r.keys() and r["geography"] else "[MX]",
            "collaborators": collabs,
            "project_id": r["project_id"] if "project_id" in r.keys() else None,
            "project_name": r["project_name"] if "project_name" in r.keys() else None,
            "project_code": r["project_code"] if "project_code" in r.keys() else None
        })
    return results

def delete_product_system(conn: sqlite3.Connection, system_id: int) -> bool:
    """Elimina permanentemente un sistema producto y sus datos asociados de forma resiliente."""
    # 1. Eliminar nodos asociados
    try:
        conn.execute("DELETE FROM product_system_nodes WHERE system_id = ?", (system_id,))
        try:
            conn.commit()
        except Exception:
            pass
    except Exception:
        pass

    # 2. Eliminar el sistema producto principal
    try:
        conn.execute("DELETE FROM product_systems WHERE id = ?", (system_id,))
        try:
            conn.commit()
        except Exception:
            pass
    except Exception:
        pass

    # 3. Eliminar comentarios, cláusulas y documentos de forma aislada
    for tbl in ("audit_comments", "comments", "checklist_clause_states", "documents"):
        try:
            conn.execute(f"DELETE FROM {tbl} WHERE system_id = ?", (system_id,))
            try:
                conn.commit()
            except Exception:
                pass
        except Exception:
            pass
    return True

def add_system_collaborator(conn: sqlite3.Connection, system_id: int, collaborator: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Agrega un colaborador (Auditor o Cliente) a un sistema producto."""
    ensure_product_systems_columns(conn)
    row = conn.execute("SELECT collaborators_json FROM product_systems WHERE id = ?", (system_id,)).fetchone()
    if not row:
        raise ValueError(f"Sistema producto con ID {system_id} no encontrado.")

    collabs = []
    raw = row["collaborators_json"] if "collaborators_json" in row.keys() else None
    if raw:
        try:
            collabs = json.loads(raw) if isinstance(raw, str) else list(raw)
        except Exception:
            collabs = []

    name = collaborator.get("display_name") or collaborator.get("name") or "Colaborador"
    email = (collaborator.get("email") or "").strip().lower()
    role = collaborator.get("role") or "auditor"

    # Evitar duplicados por email
    exists = any(c.get("email", "").lower() == email for c in collabs if email)
    if not exists:
        from datetime import datetime
        collabs.append({
            "name": name,
            "display_name": name,
            "email": email,
            "role": role,
            "invited_at": datetime.now().isoformat()
        })
        with conn:
            conn.execute("UPDATE product_systems SET collaborators_json = ? WHERE id = ?", (json.dumps(collabs), system_id))

    return collabs

def create_product_system(
    conn: sqlite3.Connection,
    name: str,
    code: str,
    target_amount: float = 1.0,
    description: str = "",
    owner_id: str = "analyst_carla",
    owner_email: str = "carla.mendez@econode.io",
    owner_name: str = "Carla Méndez",
    owner_role: str = "analyst",
    owner_org: str = "BioPack Industrial S.A. de C.V.",
    category: str = "Polímeros",
    geography: str = "[MX]",
    project_id: Optional[int] = None
) -> int:
    """Crea un nuevo sistema producto desde el Wizard asociándolo al usuario activo y opcionalmente a un proyecto."""
    ensure_product_systems_columns(conn)
    # Evitar duplicaciones accidentales por doble clic rápido
    try:
        existing_check = conn.execute("""
            SELECT id FROM product_systems 
            WHERE lower(name) = lower(?) AND code = ? AND lower(owner_email) = lower(?)
            ORDER BY id DESC LIMIT 1;
        """, (name, code, owner_email)).fetchone()
        if existing_check:
            return existing_check[0]
    except Exception:
        pass

    with conn:
        try:
            cur = conn.execute("""
                INSERT INTO product_systems (
                    name, code, target_amount, description, parameters_json,
                    owner_id, owner_email, owner_name, owner_role, owner_org,
                    category, geography, status, compliance_rate, project_id
                )
                VALUES (?, ?, ?, ?, '{}', ?, ?, ?, ?, ?, ?, ?, 'draft', '0.0%', ?)
            """, (name, code, target_amount, description, owner_id, owner_email, owner_name, owner_role, owner_org, category, geography, project_id))
            return cur.lastrowid
        except Exception as err:
            err_str = str(err).lower()
            if "unique" in err_str or "duplicate" in err_str or "integrity" in err_str:
                unique_code = f"{code}_{os.urandom(2).hex()}"
                cur = conn.execute("""
                    INSERT INTO product_systems (
                        name, code, target_amount, description, parameters_json,
                        owner_id, owner_email, owner_name, owner_role, owner_org,
                        category, geography, status, compliance_rate, project_id
                    )
                    VALUES (?, ?, ?, ?, '{}', ?, ?, ?, ?, ?, ?, ?, 'draft', '0.0%', ?)
                """, (name, unique_code, target_amount, description, owner_id, owner_email, owner_name, owner_role, owner_org, category, geography, project_id))
                return cur.lastrowid
            raise err

# -----------------------------------------------------------------------------
# 1.1 GESTIÓN DE PROYECTOS CONTENEDORES DE SISTEMAS PRODUCTO
# -----------------------------------------------------------------------------
def create_project(
    conn: sqlite3.Connection,
    name: str,
    code: Optional[str] = None,
    description: str = "",
    category: str = "General",
    owner_id: str = "analyst_carla",
    owner_email: str = "carla.mendez@econode.io",
    owner_name: str = "Carla Méndez"
) -> int:
    """Crea un proyecto contenedor para agrupar sistemas producto y realizar comparativas."""
    ensure_product_systems_columns(conn)
    if not code:
        code = f"PRJ-{os.urandom(3).hex().upper()}"
    with conn:
        cur = conn.execute("""
            INSERT INTO projects (code, name, description, category, owner_id, owner_email, owner_name)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (code.strip(), name.strip(), description.strip(), category.strip(), owner_id, owner_email, owner_name))
        return cur.lastrowid

def list_projects(
    conn: sqlite3.Connection,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtiene la lista de proyectos registrados con el conteo de sistemas asignados."""
    ensure_product_systems_columns(conn)
    clean_email = (user_email or "").strip().lower()
    clean_uid = (user_id or "").strip().lower()

    admin_emails = [e.strip().lower() for e in getattr(settings, "ADMIN_EMAILS", "").split(",") if e.strip()]
    admin_emails.extend(["josuearenteriaz09@gmail.com", "carla.mendez@econode.io"])

    is_local_sqlite = not getattr(settings, "IS_POSTGRES", False)
    is_admin = clean_email in admin_emails or user_role == "admin"

    try:
        if (not clean_email and not clean_uid) or is_local_sqlite or is_admin:
            query = """
                SELECT pr.id, pr.code, pr.name, coalesce(pr.description, '') as description,
                       coalesce(pr.category, 'General') as category,
                       pr.owner_id, pr.owner_email, pr.owner_name, pr.created_at, pr.updated_at,
                       (SELECT count(*) FROM product_systems WHERE project_id = pr.id) as systems_count
                FROM projects pr
                ORDER BY pr.id DESC;
            """
            rows = conn.execute(query).fetchall()
        else:
            query = """
                SELECT pr.id, pr.code, pr.name, coalesce(pr.description, '') as description,
                       coalesce(pr.category, 'General') as category,
                       pr.owner_id, pr.owner_email, pr.owner_name, pr.created_at, pr.updated_at,
                       (SELECT count(*) FROM product_systems WHERE project_id = pr.id) as systems_count
                FROM projects pr
                WHERE lower(coalesce(pr.owner_email, '')) = ? 
                   OR lower(coalesce(pr.owner_id, '')) = ?
                   OR lower(coalesce(pr.owner_name, '')) = ?
                ORDER BY pr.id DESC;
            """
            rows = conn.execute(query, (clean_email, clean_uid, clean_email)).fetchall()

        return [dict(r) for r in rows]
    except Exception:
        return []

def get_project_by_id(conn: sqlite3.Connection, project_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto por su ID."""
    ensure_product_systems_columns(conn)
    try:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None
    except Exception:
        return None

def delete_project(conn: sqlite3.Connection, project_id: int) -> bool:
    """Elimina un proyecto y desasocia sus sistemas (quedando como independientes 'solitos')."""
    ensure_product_systems_columns(conn)
    try:
        with conn:
            try:
                conn.execute("UPDATE product_systems SET project_id = NULL WHERE project_id = ?;", (project_id,))
            except Exception:
                pass
            cur = conn.execute("DELETE FROM projects WHERE id = ?;", (project_id,))
            return cur.rowcount > 0
    except Exception:
        return False

def assign_system_to_project(conn: sqlite3.Connection, system_id: int, project_id: Optional[int]) -> bool:
    """Asigna o desasocia un sistema producto a un proyecto contenedor."""
    ensure_product_systems_columns(conn)
    try:
        with conn:
            cur = conn.execute("UPDATE product_systems SET project_id = ? WHERE id = ?;", (project_id, system_id))
            return cur.rowcount > 0
    except Exception:
        return False

def get_product_system_details(conn: sqlite3.Connection, system_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un sistema producto con sus nodos y enlaces (modo ultra-rápido optimizado)."""
    ensure_product_systems_columns(conn)
    sys_row = conn.execute("SELECT * FROM product_systems WHERE id = ?", (system_id,)).fetchone()
    if not sys_row:
        return None

    # Parsear colaboradores
    raw_c = sys_row["collaborators_json"] if "collaborators_json" in sys_row.keys() and sys_row["collaborators_json"] else "[]"
    try:
        collabs = json.loads(raw_c) if isinstance(raw_c, str) else (raw_c or [])
    except Exception:
        collabs = []

    # 1. RUTA RÁPIDA: Si el usuario ya guardó nodos y aristas en parameters_json, retornar de inmediato (evita consultas costosas a exchanges)
    raw_p = sys_row["parameters_json"] if "parameters_json" in sys_row.keys() and sys_row["parameters_json"] else "{}"
    try:
        parsed_p = json.loads(raw_p) if isinstance(raw_p, str) else (raw_p or {})
        if isinstance(parsed_p, dict) and "canvas_nodes" in parsed_p and parsed_p["canvas_nodes"] is not None:
            saved_nodes = parsed_p["canvas_nodes"]
            saved_edges = parsed_p.get("canvas_edges", [])
            saved_palette = parsed_p.get("palette_processes", [])
            for n in saved_nodes:
                nx = float(n.get("x") if n.get("x") is not None else n.get("pos_x", 60))
                ny = float(n.get("y") if n.get("y") is not None else n.get("pos_y", 140))
                n["x"] = nx
                n["y"] = ny
                n["pos_x"] = nx
                n["pos_y"] = ny
                if "id" not in n:
                    n["id"] = f"node_{n.get('process_id', 100001)}"
            if isinstance(parsed_p, dict) and "parameters" in parsed_p and isinstance(parsed_p["parameters"], list):
                if len(parsed_p["parameters"]) > 0 or system_id != 21:
                    sys_params = parsed_p["parameters"]
                else:
                    sys_params = get_system_parameters(conn, system_id)
            else:
                sys_params = get_system_parameters(conn, system_id)

            return {
                "id": sys_row["id"],
                "name": sys_row["name"],
                "code": sys_row["code"],
                "target_amount": float(sys_row["target_amount"] or 1.0),
                "description": sys_row["description"] or "",
                "reference_process_id": sys_row["reference_process_id"],
                "owner_id": sys_row["owner_id"] if "owner_id" in sys_row.keys() and sys_row["owner_id"] else "analyst_carla",
                "owner_name": sys_row["owner_name"] if "owner_name" in sys_row.keys() and sys_row["owner_name"] else "Carla Méndez",
                "owner_role": sys_row["owner_role"] if "owner_role" in sys_row.keys() and sys_row["owner_role"] else "analyst",
                "owner_org": sys_row["owner_org"] if "owner_org" in sys_row.keys() and sys_row["owner_org"] else "BioPack Industrial S.A. de C.V.",
                "collaborators": collabs,
                "nodes": saved_nodes,
                "edges": saved_edges,
                "palette": saved_palette,
                "parameters": sys_params
            }
    except Exception:
        pass

    # 2. Si no hay canvas_nodes guardado y es el sistema oficial de referencia PET 500ml, proveer la semilla oficial
    if sys_row["code"] == "SYS-PET-CIRCULAR-01" or sys_row["id"] == 21:
        try:
            from .seed_example_system import OFFICIAL_SYSTEM_SPEC
            return {
                "id": sys_row["id"],
                "name": sys_row["name"],
                "code": sys_row["code"],
                "target_amount": float(sys_row["target_amount"] or 1.0),
                "description": sys_row["description"] or "",
                "reference_process_id": sys_row["reference_process_id"],
                "owner_id": sys_row["owner_id"] if "owner_id" in sys_row.keys() and sys_row["owner_id"] else "analyst_carla",
                "owner_name": sys_row["owner_name"] if "owner_name" in sys_row.keys() and sys_row["owner_name"] else "Carla Méndez",
                "owner_role": sys_row["owner_role"] if "owner_role" in sys_row.keys() and sys_row["owner_role"] else "analyst",
                "owner_org": sys_row["owner_org"] if "owner_org" in sys_row.keys() and sys_row["owner_org"] else "BioPack Industrial S.A. de C.V.",
                "collaborators": collabs,
                "nodes": OFFICIAL_SYSTEM_SPEC["processes"],
                "edges": OFFICIAL_SYSTEM_SPEC["edges"],
                "parameters": get_system_parameters(conn, system_id)
            }
        except Exception:
            pass

    # 3. Fallback relacional únicamente si no existe parameters_json
    nodes_rows = conn.execute("""
        SELECT n.process_id, n.pos_x, n.pos_y,
               p.code as process_code, p.name as process_name, p.location,
               coalesce(p.reference_amount, 1.0) as ref_amount,
               f.name as ref_flow_name, f.unit_symbol as ref_unit,
               c.name as category_name
        FROM product_system_nodes n
        JOIN processes p ON n.process_id = p.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE n.system_id = ?;
    """, (system_id,)).fetchall()

    nodes = []
    for nr in nodes_rows:
        pid = nr["process_id"]
        # Intercambios
        exchanges = conn.execute("""
            SELECT e.id, e.flow_id, e.is_input, e.exchange_type, e.amount, e.unit_symbol,
                   fl.name as flow_name
            FROM exchanges e
            LEFT JOIN flows fl ON e.flow_id = fl.id
            WHERE e.process_id = ?;
        """, (pid,)).fetchall()

        inputs = [dict(x) for x in exchanges if x["is_input"] == 1]
        outputs = [dict(x) for x in exchanges if x["is_input"] == 0]

        nodes.append({
            "id": f"node_{pid}",
            "process_id": pid,
            "code": nr["process_code"],
            "name": nr["process_name"],
            "location": nr["location"] or "GLO",
            "category_name": nr["category_name"] or "General",
            "pos_x": float(nr["pos_x"] or 100),
            "pos_y": float(nr["pos_y"] or 100),
            "x": float(nr["pos_x"] or 100),
            "y": float(nr["pos_y"] or 100),
            "reference_amount": float(nr["ref_amount"]),
            "reference_flow_name": nr["ref_flow_name"] or "Salida Principal",
            "unit": nr["ref_unit"] or "kg",
            "inputs": inputs,
            "outputs": outputs
        })

    # Enlaces
    edges_rows = conn.execute("""
        SELECT e.source_process_id, e.target_process_id, e.flow_id, e.amount,
               fl.name as flow_name, fl.unit_symbol
        FROM product_system_edges e
        LEFT JOIN flows fl ON e.flow_id = fl.id
        WHERE e.system_id = ?;
    """, (system_id,)).fetchall()

    return {
        "id": sys_row["id"],
        "name": sys_row["name"],
        "code": sys_row["code"],
        "target_amount": float(sys_row["target_amount"] or 1.0),
        "description": sys_row["description"] or "",
        "reference_process_id": sys_row["reference_process_id"],
        "owner_id": sys_row["owner_id"] if "owner_id" in sys_row.keys() and sys_row["owner_id"] else None,
        "owner_name": sys_row["owner_name"] if "owner_name" in sys_row.keys() and sys_row["owner_name"] else None,
        "owner_role": sys_row["owner_role"] if "owner_role" in sys_row.keys() and sys_row["owner_role"] else None,
        "owner_org": sys_row["owner_org"] if "owner_org" in sys_row.keys() and sys_row["owner_org"] else None,
        "collaborators": collabs,
        "nodes": nodes,
        "edges": [dict(er) for er in edges_rows],
        "parameters": get_system_parameters(conn, system_id)
    }

def save_system_canvas(conn: sqlite3.Connection, system_id: int, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], palette: Optional[List[Dict[str, Any]]] = None):
    """Guarda las posiciones de los nodos, enlaces y catalogo en el lienzo."""
    ensure_product_systems_columns(conn)
    with conn:
        # 1. Normalizar nodos con coordenadas exactas x, y, pos_x, pos_y
        normalized_nodes = []
        for n in (nodes or []):
            node_copy = dict(n)
            px = float(node_copy.get("x") if node_copy.get("x") is not None else node_copy.get("pos_x", 100))
            py = float(node_copy.get("y") if node_copy.get("y") is not None else node_copy.get("pos_y", 140))
            node_copy["x"] = px
            node_copy["y"] = py
            node_copy["pos_x"] = px
            node_copy["pos_y"] = py
            if "id" not in node_copy:
                node_copy["id"] = f"node_{node_copy.get('process_id', 100001)}"
            normalized_nodes.append(node_copy)

        # 2. Guardar en parameters_json del sistema producto para preservacion total
        cur = conn.execute("SELECT parameters_json FROM product_systems WHERE id = ?;", (system_id,))
        row = cur.fetchone()
        params = {}
        if row and row[0]:
            try:
                params = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
            except Exception:
                params = {}
        params["canvas_nodes"] = normalized_nodes
        params["canvas_edges"] = edges or []
        if palette is not None:
            params["palette_processes"] = palette
        conn.execute("UPDATE product_systems SET parameters_json = ? WHERE id = ?;", (json.dumps(params, ensure_ascii=False), system_id))

        # 3. Mantener consistencia relacional en product_system_nodes
        conn.execute("DELETE FROM product_system_nodes WHERE system_id = ?", (system_id,))
        for node in normalized_nodes:
            pid = node.get("process_id")
            if pid is not None:
                try:
                    num_pid = int(pid)
                    conn.execute("""
                        INSERT OR REPLACE INTO product_system_nodes (system_id, process_id, pos_x, pos_y)
                        VALUES (?, ?, ?, ?);
                    """, (system_id, num_pid, node["x"], node["y"]))
                except (ValueError, TypeError):
                    pass

        # 4. Mantener consistencia relacional en product_system_edges
        conn.execute("DELETE FROM product_system_edges WHERE system_id = ?", (system_id,))
        for edge in (edges or []):
            src_raw = edge.get("source_process_id") or edge.get("from")
            tgt_raw = edge.get("target_process_id") or edge.get("to")
            fl_id = edge.get("flow_id") or edge.get("flow") or ""
            amt = float(edge.get("amount", 1.0))
            desc = edge.get("description", "")
            try:
                src_num = int(str(src_raw).replace("node_", "")) if src_raw else None
                tgt_num = int(str(tgt_raw).replace("node_", "")) if tgt_raw else None
                conn.execute("""
                    INSERT OR REPLACE INTO product_system_edges (system_id, source_process_id, target_process_id, flow_id, amount, description)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (system_id, src_num, tgt_num, str(fl_id), amt, desc))
            except Exception:
                pass

# -----------------------------------------------------------------------------
# 2. CATÁLOGO LCI (ECOINVENT 3.12) & BILINGUAL SEARCH
# -----------------------------------------------------------------------------
SPANISH_TO_ECOINVENT_MAPPINGS = [
    ("inyecc", ["injection moulding", "injection molding", "injection"]),
    ("soplado", ["blow moulding", "stretch blow moulding", "blow"]),
    ("moldeo", ["moulding", "molding"]),
    ("termoformado", ["thermoforming"]),
    ("extrusion", ["extrusion"]),
    ("extrusión", ["extrusion"]),
    ("secado", ["drying"]),
    ("tratamiento termico", ["heat", "treatment", "steam"]),
    ("tratamiento térmico", ["heat", "treatment", "steam"]),
    ("transporte", ["transport", "freight"]),
    ("flete", ["freight", "transport"]),
    ("logistica", ["transport", "logistics"]),
    ("logística", ["transport", "logistics"]),
    ("distribucion", ["transport", "distribution"]),
    ("distribución", ["transport", "distribution"]),
    ("camion", ["lorry", "truck"]),
    ("camión", ["lorry", "truck"]),
    ("electricidad", ["electricity"]),
    ("electrico", ["electricity"]),
    ("eléctrico", ["electricity"]),
    ("energia", ["electricity", "energy"]),
    ("energía", ["electricity", "energy"]),
    ("gas natural", ["natural gas"]),
    ("gasolina", ["petrol"]),
    ("combustible", ["diesel", "fuel", "petrol"]),
    ("agua", ["water"]),
    ("enfriamiento", ["cooling water", "cooling"]),
    ("vapor", ["steam"]),
    ("calor", ["heat"]),
    ("acero", ["steel"]),
    ("aluminio", ["aluminium", "aluminum"]),
    ("cobre", ["copper"]),
    ("vidrio", ["glass"]),
    ("papel", ["paper"]),
    ("carton", ["cardboard", "corrugated board"]),
    ("cartón", ["cardboard", "corrugated board"]),
    ("plastico", ["plastic", "polymer"]),
    ("plástico", ["plastic", "polymer"]),
    ("polimero", ["polymer"]),
    ("polímero", ["polymer"]),
    ("resina", ["resin", "granulate"]),
    ("granulado", ["granulate"]),
    ("preforma", ["preform", "injection moulding"]),
    ("botella", ["bottle", "blow moulding"]),
    ("empaque", ["packaging"]),
    ("envase", ["packaging", "bottle"]),
    ("reciclaje", ["recycling"]),
    ("reciclado", ["recycling"]),
    ("residuo", ["waste"]),
    ("desecho", ["waste"]),
    ("chatarra", ["scrap"]),
    ("cogeneracion", ["heat and power co-generation", "cogeneration"]),
    ("cogeneración", ["heat and power co-generation", "cogeneration"]),
]

def _expand_search_terms(query: str) -> List[str]:
    q_clean = query.strip()
    if not q_clean:
        return []
    terms = [q_clean]
    q_lower = q_clean.lower()
    for es_term, en_synonyms in SPANISH_TO_ECOINVENT_MAPPINGS:
        if es_term in q_lower:
            for syn in en_synonyms:
                if syn not in terms:
                    terms.append(syn)
    return terms

def search_lci_processes(
    conn: sqlite3.Connection,
    query: str = "",
    category_id: Optional[Any] = None,
    limit: int = 50,
    source: Optional[str] = "all"
) -> List[Dict[str, Any]]:
    """Búsqueda en catálogo de procesos con metadatos técnicos, sinónimos bilingües y soporte multifuente (ecoinvent, GLAD, OEKOBAUDAT, ADEME, Custom)."""
    source_val = (source or "all").strip().lower()
    items: List[Dict[str, Any]] = []

    source_info_map = {
        "all": ("Todas las BDs", "all"),
        "ecoinvent_312": ("ecoinvent 3.12", "ecoinvent"),
        "glad_network": ("GLAD (UNEP)", "glad"),
        "oekobaudat": ("OEKOBAUDAT", "oekobaudat"),
        "oekobaudat_de": ("OEKOBAUDAT", "oekobaudat"),
        "ademe_base_carbone": ("Base Carbone", "ademe"),
        "user_custom": ("Mis Procesos", "custom")
    }

    # 1. Catálogo Externo (GLAD, OEKOBAUDAT, ADEME)
    if source_val in ("glad_network", "oekobaudat", "oekobaudat_de", "ademe_base_carbone") or source_val == "all":
        target_src = "oekobaudat_de" if source_val in ("oekobaudat", "oekobaudat_de") else source_val
        cat_sql = """
            SELECT MIN(cp.id) as id, cp.source_code, cp.original_uuid as code, cp.name, cp.location,
                   1.0 as reference_amount, cp.activity_type as category_name,
                   cp.reference_product as reference_flow_name, cp.unit as reference_unit
            FROM catalog_processes cp
            WHERE 1=1
        """
        cat_params = []
        if target_src != "all":
            cat_sql += " AND cp.source_code = ?"
            cat_params.append(target_src)

        if category_id is not None and str(category_id).strip().upper() != "ALL":
            cat_sql += " AND cp.activity_type LIKE ?"
            cat_params.append(f"%{category_id}%")

        if query:
            cat_sql += " AND (cp.name LIKE ? OR cp.reference_product LIKE ? OR cp.original_uuid LIKE ?)"
            q_param = f"%{query}%"
            cat_params.extend([q_param, q_param, q_param])

        cat_sql += " GROUP BY cp.source_code, cp.original_uuid, cp.name, cp.location, cp.activity_type, cp.reference_product, cp.unit ORDER BY cp.name LIMIT ?;"
        cat_params.append(limit if source_val != "all" else min(25, limit))

        cat_rows = conn.execute(cat_sql, cat_params).fetchall()
        for r in cat_rows:
            sc = r["source_code"]
            slabel, sbadge = source_info_map.get(sc, ("Catálogo LCI", "all"))
            item = dict(r)
            item["id"] = f"cat_{r['id']}"
            item["source_code"] = sc
            item["source_label"] = slabel
            item["source_badge"] = sbadge
            items.append(item)

        if source_val in ("glad_network", "oekobaudat", "oekobaudat_de", "ademe_base_carbone"):
            return items

    # 2. Procesos Propios / Custom
    if source_val == "user_custom":
        custom_sql = """
            SELECT p.id, p.code, p.name, p.location, p.reference_amount,
                   c.name as category_name,
                   f.name as reference_flow_name, f.unit_symbol as reference_unit,
                   'user_custom' as source_code, 'Mis Procesos' as source_label, 'custom' as source_badge
            FROM processes p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN flows f ON p.reference_flow_id = f.id
            WHERE p.category_id = 999999 OR p.code LIKE 'CUSTOM_%' OR p.code LIKE 'PROC_CUSTOM_%'
        """
        custom_params = []
        if query:
            custom_sql += " AND (p.name LIKE ? OR p.code LIKE ?)"
            custom_params.extend([f"%{query}%", f"%{query}%"])
        custom_sql += " ORDER BY p.name LIMIT ?;"
        custom_params.append(limit)
        return [dict(r) for r in conn.execute(custom_sql, custom_params).fetchall()]

    # 3. ecoinvent 3.12 (procesos base)
    is_pg = getattr(settings, "IS_POSTGRES", False)
    if is_pg:
        sql = """
            SELECT p.id, p.code, p.name, p.location, p.reference_amount,
                   coalesce(p.category_name, 'General') as category_name,
                   coalesce(p.reference_flow_name, p.name) as reference_flow_name,
                   coalesce(p.reference_unit, 'kg') as reference_unit,
                   'ecoinvent_312' as source_code, 'ecoinvent 3.12' as source_label, 'ecoinvent' as source_badge
            FROM lci_processes p
            WHERE 1=1
        """
    else:
        sql = """
            SELECT p.id, p.code, p.name, p.location, p.reference_amount,
                   c.name as category_name,
                   f.name as reference_flow_name, f.unit_symbol as reference_unit,
                   'ecoinvent_312' as source_code, 'ecoinvent 3.12' as source_label, 'ecoinvent' as source_badge
            FROM processes p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN flows f ON p.reference_flow_id = f.id
            WHERE 1=1
        """
    params = []
    if category_id is not None and str(category_id).strip().upper() != "ALL":
        cat_str = str(category_id).strip()
        if cat_str.isdigit():
            sql += " AND p.category_id = ?"
            params.append(int(cat_str))
        else:
            cat_lower = cat_str.lower()
            if any(k in cat_lower for k in ("polim", "polí", "polym", "plast", "pet", "resin")):
                sql += " AND (c.name LIKE '%plastics%' OR c.name LIKE '%rubber%' OR p.name LIKE '%polymer%' OR p.name LIKE '%polyethylene%' OR p.name LIKE '%polypropylene%' OR p.name LIKE '%PET%' OR p.name LIKE '%granulate%')"
            elif any(k in cat_lower for k in ("energ", "red", "power", "electr", "gas", "electric")):
                sql += " AND (c.name LIKE '%electric%' OR c.name LIKE '%power%' OR c.name LIKE '%energy%' OR c.name LIKE '%gas%' OR c.name LIKE '%steam%' OR p.name LIKE '%electricity%')"
            elif any(k in cat_lower for k in ("transp", "logist", "flete", "freight", "road", "rail")):
                sql += " AND (c.name LIKE '%transport%' OR c.name LIKE '%freight%' OR p.name LIKE '%transport%')"
            else:
                col = "p.category_name" if is_pg else "c.name"
                sql += f" AND {col} LIKE ?"
                params.append(f"%{cat_str}%")

    if query:
        terms = _expand_search_terms(query)
        clauses = []
        for t in terms:
            clauses.append("(p.name LIKE ? OR p.code LIKE ?)")
            params.extend([f"%{t}%", f"%{t}%"])
        if clauses:
            sql += f" AND ({' OR '.join(clauses)})"

    remaining_limit = max(1, limit - len(items)) if source_val == "all" else limit
    sql += " ORDER BY p.name LIMIT ?;"
    params.append(remaining_limit)

    rows = conn.execute(sql, params).fetchall()
    ecoinvent_items = [dict(r) for r in rows]

    if source_val == "all":
        return items + ecoinvent_items
    return ecoinvent_items

def get_process_technical_sheet(conn: sqlite3.Connection, process_id: Any) -> Optional[Dict[str, Any]]:
    """Obtiene la ficha técnica con todos sus intercambios tecnosféricos y elementales (soporta ecoinvent y catálogo externo)."""
    str_pid = str(process_id).strip()

    if str_pid.startswith("cat_") or "_" in str_pid:
        raw_id_str = str_pid.split("_")[-1]
        if raw_id_str.isdigit():
            cp = conn.execute("SELECT * FROM catalog_processes WHERE id = ?", (int(raw_id_str),)).fetchone()
            if cp:
                ref_name = cp["reference_product"] or cp["name"]
                ref_unit = cp["unit"] or "kg"
                sc_str = str(cp["source_code"] or "").lower()
                source_label = "GLAD (UNEP)" if "glad" in sc_str else ("OEKOBAUDAT" if "oeko" in sc_str else ("Base Carbone" if "ademe" in sc_str else "Catálogo LCI"))
                sheet = {
                    "id": str_pid,
                    "code": cp["original_uuid"] or f"CAT-{cp['id']}",
                    "name": cp["name"],
                    "location": cp["location"] or "GLO",
                    "category_name": cp["activity_type"] or "General",
                    "ref_flow_name": ref_name,
                    "ref_unit": ref_unit,
                    "reference_amount": 1.0,
                    "source_code": cp["source_code"],
                    "provider": cp["provider_name"] or source_label,
                    "technosphere_inputs": [],
                    "biosphere_emissions": [],
                    "waste_outputs": [],
                    "inputs": [],
                    "outputs": [{
                        "id": f"out_{cp['id']}",
                        "flow_id": None,
                        "is_input": 0,
                        "exchange_type": "production",
                        "amount": 1.0,
                        "unit_symbol": ref_unit,
                        "flow_name": ref_name,
                        "flow_type": "PRODUCT_FLOW"
                    }],
                    "dqi_score": "5/5 (Verificado)",
                    "pedigree": { "reliability": 1, "completeness": 1, "temporal": 1, "geographic": 1, "technological": 1 }
                }
                sheet["process"] = dict(sheet)
                return sheet

    int_id = int(str_pid) if str_pid.isdigit() else 0
    proc = conn.execute("""
        SELECT p.*, c.name as category_name, 
               COALESCE(f.name, (SELECT description FROM exchanges WHERE process_id = p.id AND is_input = 0 AND exchange_type = 'production' LIMIT 1), p.name) as ref_flow_name, 
               COALESCE(f.unit_symbol, 'kg') as ref_unit
        FROM processes p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id
        WHERE p.id = ?;
    """, (int_id,)).fetchone()
    if not proc:
        cp = conn.execute("SELECT * FROM catalog_processes WHERE id = ?", (int_id,)).fetchone()
        if cp:
            return get_process_technical_sheet(conn, f"cat_{int_id}")
        return None

    exchanges = conn.execute("""
        SELECT e.id, e.flow_id, e.is_input, e.exchange_type, e.amount, e.unit_symbol,
               COALESCE(fl.name, e.description, 'Insumo') as flow_name, 
               COALESCE(fl.flow_type, 'PRODUCT_FLOW') as flow_type
        FROM exchanges e
        LEFT JOIN flows fl ON e.flow_id = fl.id
        WHERE e.process_id = ?
        ORDER BY e.is_input DESC, e.exchange_type, flow_name;
    """, (int_id,)).fetchall()

    inputs = [dict(x) for x in exchanges if x["is_input"] == 1]
    outputs = [dict(x) for x in exchanges if x["is_input"] == 0]

    sheet = dict(proc)
    sheet["process"] = dict(proc)
    sheet["technosphere_inputs"] = [x for x in inputs if x["exchange_type"] != "biosphere"]
    sheet["biosphere_emissions"] = [x for x in outputs if x["exchange_type"] == "biosphere"] + [x for x in inputs if x["exchange_type"] == "biosphere"]
    sheet["waste_outputs"] = [x for x in outputs if "waste" in str(x.get("exchange_type", "")).lower() or "residuo" in str(x.get("flow_name", "")).lower() or "scrap" in str(x.get("flow_name", "")).lower()]
    sheet["inputs"] = inputs
    sheet["outputs"] = outputs
    sheet["dqi_score"] = "5/5 (ecoinvent oficial)"
    sheet["pedigree"] = { "reliability": 1, "completeness": 1, "temporal": 2, "geographic": 1, "technological": 1 }
    return sheet

def get_top_lci_categories(conn: sqlite3.Connection, limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene las categorías oficiales reales de ecoinvent 3.12 y Propios con conteo de procesos."""
    if getattr(settings, "IS_POSTGRES", False):
        sql = """
            SELECT c.id, c.name, count(p.id) as process_count
            FROM lci_categories c
            JOIN lci_processes p ON p.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY process_count DESC
            LIMIT ?;
        """
        rows = conn.execute(sql, (limit,)).fetchall()
        return [{"id": r[0], "name": r[1], "process_count": r[2]} for r in rows]

    sql = """
        SELECT id, name, process_count FROM (
            SELECT c.id, c.name, count(p.id) as process_count
            FROM categories c
            LEFT JOIN processes p ON p.category_id = c.id
            WHERE c.id = 999999 OR c.name LIKE '%propio%'
            GROUP BY c.id, c.name
            UNION ALL
            SELECT c.id, c.name, count(p.id) as process_count
            FROM categories c
            JOIN processes p ON p.category_id = c.id
            WHERE c.id != 999999 AND c.name NOT LIKE '%propio%'
            GROUP BY c.id, c.name
            HAVING count(p.id) > 0
        )
        ORDER BY CASE WHEN id = 999999 OR name LIKE '%propio%' THEN 0 ELSE 1 END,
                 process_count DESC
        LIMIT ?;
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    return [{"id": r[0], "name": r[1], "process_count": r[2]} for r in rows]

def search_flows(conn: sqlite3.Connection, query: str = "", flow_type: Optional[str] = None, category: Optional[Any] = None, limit: int = 40) -> List[Dict[str, Any]]:
    """Busca flujos oficiales existentes en la base de datos ecoinvent 3.12 y propios con soporte bilingüe."""
    sql = "SELECT id, name, flow_type, unit_symbol, category_name FROM flows WHERE 1=1"
    params = []
    if category is not None and str(category).strip() != "" and str(category).strip().upper() != "ALL":
        cat_str = str(category).strip()
        if cat_str == "999999" or "propio" in cat_str.lower() or "custom" in cat_str.lower():
            sql += " AND (category_name IN ('Procesos y flujos propios', 'Custom processes & flows') OR id LIKE 'FL_%')"
        else:
            sql += " AND category_name LIKE ?"
            params.append(f"%{cat_str}%")
    if query:
        terms = _expand_search_terms(query)
        clauses = []
        for t in terms:
            clauses.append("(name LIKE ? OR code LIKE ?)")
            params.extend([f"%{t}%", f"%{t}%"])
        if clauses:
            sql += f" AND ({' OR '.join(clauses)})"
    if flow_type and flow_type != "ALL":
        sql += " AND flow_type = ?"
        params.append(flow_type)
    sql += " ORDER BY CASE WHEN category_name IN ('Procesos y flujos propios', 'Custom processes & flows') THEN 0 ELSE 1 END, name ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, tuple(params)).fetchall()
    return [{"id": r[0], "name": r[1], "flow_type": r[2], "unit_symbol": r[3] or "kg", "category_name": r[4] or "ecoinvent 3.12"} for r in rows]

def search_providers(conn: sqlite3.Connection, flow_name: str = "", limit: int = 15) -> List[Dict[str, Any]]:
    """Busca procesos proveedores potenciales para un flujo determinado en la base de datos."""
    sql = """
        SELECT p.id, p.name, p.location, fl.unit_symbol
        FROM processes p
        LEFT JOIN flows fl ON p.reference_flow_id = fl.id
        WHERE 1=1
    """
    params = []
    if flow_name:
        sql += " AND p.name LIKE ?"
        params.append(f"%{flow_name.strip()}%")
    sql += " ORDER BY p.name ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, tuple(params)).fetchall()
    return [{"id": r[0], "name": r[1], "location": r[2] or "GLO", "unit": r[3] or "kg"} for r in rows]




# -----------------------------------------------------------------------------
# 5. PARAMETRIC MODELING & DYNAMIC PARAMETERS DEFINITION
# -----------------------------------------------------------------------------

DEFAULT_SYSTEM_21_PARAMETERS = [
    {
        "id": "param-sys21-peso-botella",
        "name": "peso_nominal_botella",
        "scope": "global",
        "process_id": None,
        "process_name": "Global / Sistema Completo",
        "group": "Materias Primas",
        "param_type": "independent",
        "value": 0.024,
        "formula": "",
        "unit": "kg",
        "description": "Peso neto nominal del envase PET terminado de 500ml sin tapa ni etiqueta"
    },
    {
        "id": "param-sys21-rpet-pct",
        "name": "contenido_rpet_pct",
        "scope": "global",
        "process_id": None,
        "process_name": "Global / Sistema Completo",
        "group": "Materias Primas",
        "param_type": "independent",
        "value": 25.0,
        "formula": "",
        "unit": "%",
        "description": "Porcentaje de resina reciclada post-consumo (rPET) grado botella en la formulacion"
    },
    {
        "id": "param-sys21-resina-virgen",
        "name": "resina_virgen_requerida",
        "scope": "global",
        "process_id": None,
        "process_name": "Global / Sistema Completo",
        "group": "Materias Primas",
        "param_type": "dependent",
        "value": 0.018,
        "formula": "peso_nominal_botella * (1 - contenido_rpet_pct / 100)",
        "unit": "kg",
        "description": "Cantidad neta de resina PET virgen demandada por envase producido"
    },
    {
        "id": "param-sys21-factor-cfe",
        "name": "factor_emision_red_cfe",
        "scope": "global",
        "process_id": None,
        "process_name": "Global / Sistema Completo",
        "group": "Factores de Emision",
        "param_type": "independent",
        "value": 0.438,
        "formula": "",
        "unit": "kg CO2 eq/kWh",
        "description": "Factor de emision oficial del Sistema Electrico Nacional (SEN) CRE/SEMARNAT"
    },
    {
        "id": "param-sys21-merma-inyeccion",
        "name": "merma_inyeccion_pct",
        "scope": "local",
        "process_id": 100001,
        "process_name": "PET Preform Injection Molding",
        "group": "Eficiencias y Mermas",
        "param_type": "independent",
        "value": 2.5,
        "formula": "",
        "unit": "%",
        "description": "Porcentaje de scrap o purga generado durante la inyeccion de preformas"
    },
    {
        "id": "param-sys21-kwh-inyeccion",
        "name": "consumo_electrico_inyeccion",
        "scope": "local",
        "process_id": 100001,
        "process_name": "PET Preform Injection Molding",
        "group": "Consumo Energetico",
        "param_type": "independent",
        "value": 0.28,
        "formula": "",
        "unit": "kWh/kg",
        "description": "Intensidad energetica especifica de la inyectora hidraulica con servomotor"
    },
    {
        "id": "param-sys21-merma-soplado",
        "name": "merma_soplado_pct",
        "scope": "local",
        "process_id": 100002,
        "process_name": "PET Bottle Stretch Blow Molding",
        "group": "Eficiencias y Mermas",
        "param_type": "independent",
        "value": 0.8,
        "formula": "",
        "unit": "%",
        "description": "Tasa de rechazo y recorte por deformacion termica en soplado rotativo"
    },
    {
        "id": "param-sys21-presion-soplado",
        "name": "presion_aire_soplado_bar",
        "scope": "local",
        "process_id": 100002,
        "process_name": "PET Bottle Stretch Blow Molding",
        "group": "Parametros de Operacion",
        "param_type": "independent",
        "value": 36.0,
        "formula": "",
        "unit": "bar",
        "description": "Presion neumatica de soplado bi-orientado para espesor de pared uniforme"
    },
    {
        "id": "param-sys21-distancia-distribucion",
        "name": "distancia_distribucion_km",
        "scope": "local",
        "process_id": 100003,
        "process_name": "PET Bottle Distribution & Logistics",
        "group": "Logistica y Transporte",
        "param_type": "independent",
        "value": 350.0,
        "formula": "",
        "unit": "km",
        "description": "Distancia promedio ponderada de transporte en camion articulado 16-32t hacia el CEDIS"
    },
    {
        "id": "param-sys21-ton-km",
        "name": "huella_transporte_ton_km",
        "scope": "local",
        "process_id": 100003,
        "process_name": "PET Bottle Distribution & Logistics",
        "group": "Logistica y Transporte",
        "param_type": "dependent",
        "value": 0.0084,
        "formula": "peso_nominal_botella * distancia_distribucion_km / 1000",
        "unit": "t*km",
        "description": "Esfuerzo de transporte ponderado por peso unitario y distancia recorrida"
    }
]

def get_system_parameters(conn: Any, system_id: int) -> List[Dict[str, Any]]:
    """Obtiene los parametros parametricos definidos para un sistema producto."""
    ensure_product_systems_columns(conn)
    cur = conn.execute("SELECT parameters_json FROM product_systems WHERE id = ?;", (system_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        if system_id == 21:
            return [dict(p) for p in DEFAULT_SYSTEM_21_PARAMETERS]
        return []

    raw = row[0]
    try:
        params_dict = json.loads(raw) if isinstance(raw, str) else (raw or {})
        if isinstance(params_dict, dict) and "parameters" in params_dict and isinstance(params_dict["parameters"], list):
            if len(params_dict["parameters"]) > 0 or system_id != 21:
                return params_dict["parameters"]
    except Exception:
        pass

    if system_id == 21:
        return [dict(p) for p in DEFAULT_SYSTEM_21_PARAMETERS]
    return []

def save_system_parameter(conn: Any, system_id: int, param_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea o actualiza un parametro en parameters_json del sistema producto."""
    ensure_product_systems_columns(conn)
    cur = conn.execute("SELECT parameters_json FROM product_systems WHERE id = ?;", (system_id,))
    row = cur.fetchone()
    params_dict = {}
    if row and row[0]:
        try:
            params_dict = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
        except Exception:
            params_dict = {}

    current_params = params_dict.get("parameters")
    if current_params is None:
        if system_id == 21:
            current_params = [dict(p) for p in DEFAULT_SYSTEM_21_PARAMETERS]
        else:
            current_params = []
    elif not isinstance(current_params, list):
        current_params = []

    p_id = str(param_data.get("id") or "").strip()
    if not p_id:
        p_id = f"param_{uuid.uuid4().hex[:8]}"

    raw_name = str(param_data.get("name") or "param_nuevo").strip()
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", raw_name).lower()
    if not clean_name or clean_name[0].isdigit():
        clean_name = f"p_{clean_name}"

    scope = str(param_data.get("scope") or "global").strip().lower()
    if scope not in ("global", "local"):
        scope = "global"

    proc_id = param_data.get("process_id")
    proc_name = str(param_data.get("process_name") or "Global / Sistema Completo").strip()
    if scope == "local" and proc_id is not None and str(proc_id).strip() != "":
        try:
            proc_id = int(str(proc_id).replace("node_", ""))
        except (ValueError, TypeError):
            proc_id = None
    else:
        proc_id = None
        proc_name = "Global / Sistema Completo"

    group = str(param_data.get("group") or "General").strip()
    if not group:
        group = "General"

    param_type = str(param_data.get("param_type") or "independent").strip().lower()
    if param_type not in ("independent", "dependent"):
        param_type = "independent"

    try:
        val = float(param_data.get("value", 0.0))
    except (ValueError, TypeError):
        val = 0.0

    formula = str(param_data.get("formula") or "").strip() if param_type == "dependent" else ""
    unit = str(param_data.get("unit") or "kg").strip()
    description = str(param_data.get("description") or "").strip()

    normalized_param = {
        "id": p_id,
        "name": clean_name,
        "scope": scope,
        "process_id": proc_id,
        "process_name": proc_name,
        "group": group,
        "param_type": param_type,
        "value": val,
        "formula": formula,
        "unit": unit,
        "description": description
    }

    idx = next((i for i, p in enumerate(current_params) if p.get("id") == p_id), -1)
    if idx >= 0:
        current_params[idx] = normalized_param
    else:
        current_params.append(normalized_param)

    params_dict["parameters"] = current_params
    with conn:
        conn.execute("UPDATE product_systems SET parameters_json = ? WHERE id = ?;", (json.dumps(params_dict, ensure_ascii=False), system_id))

    return normalized_param

def delete_system_parameter(conn: Any, system_id: int, param_id: str) -> bool:
    """Elimina un parametro del sistema producto."""
    ensure_product_systems_columns(conn)
    cur = conn.execute("SELECT parameters_json FROM product_systems WHERE id = ?;", (system_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        return False

    try:
        params_dict = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
    except Exception:
        return False

    current_params = params_dict.get("parameters")
    if current_params is None:
        if system_id == 21:
            current_params = [dict(p) for p in DEFAULT_SYSTEM_21_PARAMETERS]
        else:
            return False

    new_params = [p for p in current_params if str(p.get("id")) != str(param_id)]
    params_dict["parameters"] = new_params
    with conn:
        conn.execute("UPDATE product_systems SET parameters_json = ? WHERE id = ?;", (json.dumps(params_dict, ensure_ascii=False), system_id))
    return True
