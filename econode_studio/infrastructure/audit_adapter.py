"""
econode_studio/infrastructure/audit_adapter.py - Adaptador SQLite para Auditoría Colaborativa y Normativa Multi-Estándar
Implementa persistencia transaccional ACID en SQLite (econode_audit.db) en modo WAL:
1. Tabla 'audit_comments': Hilos de comentarios técnicos, anotaciones y notas del lienzo.
2. Tablas 'checklist_templates' y 'checklist_template_clauses': Catálogo dinámico de normas y checklists.
3. Tabla 'checklist_states': Estados de conformidad por cláusula, sistema producto y norma.
4. Tabla 'audit_seals': Sellos criptográficos y firmas digitales de verificación normativa.
"""

import os
import sqlite3
import datetime
import csv
import io
from typing import Dict, List, Any, Optional

try:
    from config import settings
    AUDIT_DB_PATH = settings.AUDIT_DB_PATH
except (ImportError, ValueError):
    try:
        from econode_studio.config import settings
        AUDIT_DB_PATH = settings.AUDIT_DB_PATH
    except Exception:
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        AUDIT_DB_PATH = os.path.join(DATA_DIR, "econode_audit.db")

try:
    from domain.audit_checklist import OFFICIAL_STANDARDS
except (ImportError, ValueError):
    from econode_studio.domain.audit_checklist import OFFICIAL_STANDARDS


from .db_connection import get_db_connection

def get_audit_db_connection() -> Any:
    """Crea una conexión con soporte dual para Supabase PostgreSQL y SQLite."""
    return get_db_connection(AUDIT_DB_PATH)


def init_audit_db() -> None:
    """Crea las tablas, índices e inicializa los estándares oficiales si no existen."""
    if getattr(settings, "IS_POSTGRES", False):
        return
    with get_audit_db_connection() as conn:
        # 1. Comentarios
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                author_role TEXT NOT NULL DEFAULT 'auditor',
                content TEXT NOT NULL,
                node_id TEXT,
                x REAL,
                y REAL,
                status TEXT NOT NULL DEFAULT 'open',
                resolved_by TEXT,
                resolved_at TEXT,
                reply TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_comments_system ON audit_comments(system_id);")

        # 2. Catálogo de Normas / Plantillas de Checklist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checklist_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                standard_family TEXT NOT NULL,
                description TEXT,
                version TEXT DEFAULT '1.0',
                is_official INTEGER DEFAULT 0,
                created_by TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Cláusulas de cada Plantilla
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checklist_template_clauses (
                checklist_id TEXT NOT NULL,
                clause_id TEXT NOT NULL,
                section TEXT NOT NULL,
                title TEXT NOT NULL,
                criterion TEXT NOT NULL,
                evidence_required TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                PRIMARY KEY (checklist_id, clause_id),
                FOREIGN KEY (checklist_id) REFERENCES checklist_templates(id) ON DELETE CASCADE
            );
        """)

        # 4. Estados de Cláusulas por Sistema Producto
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checklist_states (
                system_id INTEGER NOT NULL,
                clause_id TEXT NOT NULL,
                is_compliant INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                checklist_id TEXT DEFAULT 'nom070',
                PRIMARY KEY (system_id, clause_id)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checklist_states_system ON checklist_states(system_id);")

        # Migración segura: agregar checklist_id si la tabla existía previamente sin ella
        try:
            cur = conn.execute("PRAGMA table_info(checklist_states);")
            cols = {c["name"] for c in cur.fetchall()}
            if "checklist_id" not in cols:
                conn.execute("ALTER TABLE checklist_states ADD COLUMN checklist_id TEXT DEFAULT 'nom070';")
        except Exception:
            pass

        # 5. Sellos Digitales
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_seals (
                system_id INTEGER PRIMARY KEY,
                digital_seal TEXT NOT NULL,
                signed_by TEXT,
                compliance_rate REAL,
                signed_at TEXT NOT NULL,
                checklist_id TEXT DEFAULT 'nom070'
            );
        """)

        try:
            cur = conn.execute("PRAGMA table_info(audit_seals);")
            cols = {c["name"] for c in cur.fetchall()}
            if "checklist_id" not in cols:
                conn.execute("ALTER TABLE audit_seals ADD COLUMN checklist_id TEXT DEFAULT 'nom070';")
        except Exception:
            pass

        # Sembrar las normas oficiales del dominio
        for std_id, std in OFFICIAL_STANDARDS.items():
            conn.execute("""
                INSERT INTO checklist_templates (id, name, code, standard_family, description, version, is_official, created_by)
                VALUES (?, ?, ?, ?, ?, ?, 1, 'system')
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    code = excluded.code,
                    standard_family = excluded.standard_family,
                    description = excluded.description;
            """, (std.id, std.name, std.code, std.standard_family, std.description, std.version))

            for idx, cl in enumerate(std.clauses, start=1):
                conn.execute("""
                    INSERT INTO checklist_template_clauses (checklist_id, clause_id, section, title, criterion, evidence_required, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(checklist_id, clause_id) DO UPDATE SET
                        section = excluded.section,
                        title = excluded.title,
                        criterion = excluded.criterion,
                        evidence_required = excluded.evidence_required,
                        display_order = excluded.display_order;
                """, (std.id, cl.clause_id, cl.section, cl.title, cl.criterion, cl.evidence_required, idx))


# =============================================================================
# COMENTARIOS TÉCNICOS Y ANOTACIONES DEL LIENZO
# =============================================================================

def _row_to_comment_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "system_id": row["system_id"],
        "author_name": row["author_name"],
        "author_role": row["author_role"],
        "content": row["content"],
        "node_id": row["node_id"],
        "x": row["x"],
        "y": row["y"],
        "status": row["status"],
        "resolved_by": row["resolved_by"],
        "resolved_at": row["resolved_at"],
        "reply": row["reply"],
        "created_at": row["created_at"]
    }


def get_comments_by_system(system_id: int) -> List[Dict[str, Any]]:
    """Recupera los comentarios asociados a un sistema producto."""
    init_audit_db()
    with get_audit_db_connection() as conn:
        if system_id in (1, 21):
            cur = conn.execute(
                "SELECT * FROM audit_comments WHERE system_id IN (1, 21) ORDER BY id ASC;"
            )
        else:
            cur = conn.execute(
                "SELECT * FROM audit_comments WHERE system_id = ? ORDER BY id ASC;",
                (system_id,)
            )
        return [_row_to_comment_dict(r) for r in cur.fetchall()]


def insert_comment(
    system_id: int,
    author_name: str,
    author_role: str,
    content: str,
    node_id: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None
) -> Dict[str, Any]:
    """Inserta un nuevo comentario atómicamente y retorna el registro creado."""
    init_audit_db()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    author_name = author_name or "Usuario"
    author_role = author_role or "auditor"

    with get_audit_db_connection() as conn:
        cur = conn.execute("""
            INSERT INTO audit_comments (
                system_id, author_name, author_role, content, node_id, x, y,
                status, resolved_by, resolved_at, reply, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', NULL, NULL, NULL, ?)
        """, (system_id, author_name, author_role, content, node_id, x, y, now_iso))
        comment_id = cur.lastrowid

        row = conn.execute("SELECT * FROM audit_comments WHERE id = ?;", (comment_id,)).fetchone()
        return _row_to_comment_dict(row)


def resolve_comment(
    comment_id: int,
    resolved_by: str,
    reply_text: Optional[str] = None
) -> Dict[str, Any]:
    """Marca un comentario como resuelto y opcionalmente añade respuesta."""
    init_audit_db()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    resolved_by = resolved_by or "Elena Ramírez"

    with get_audit_db_connection() as conn:
        row = conn.execute("SELECT * FROM audit_comments WHERE id = ?;", (comment_id,)).fetchone()
        if not row:
            raise ValueError(f"Comentario #{comment_id} no encontrado")

        conn.execute("""
            UPDATE audit_comments
            SET status = 'resolved', resolved_by = ?, resolved_at = ?, reply = coalesce(?, reply)
            WHERE id = ?
        """, (resolved_by, now_iso, reply_text, comment_id))

        updated_row = conn.execute("SELECT * FROM audit_comments WHERE id = ?;", (comment_id,)).fetchone()
        return _row_to_comment_dict(updated_row)


def delete_comment(
    comment_id: int,
    user_name: str = "",
    user_role: str = ""
) -> bool:
    """Elimina un comentario verificando permisos de autoría o rol auditor/admin."""
    init_audit_db()
    with get_audit_db_connection() as conn:
        row = conn.execute("SELECT * FROM audit_comments WHERE id = ?;", (comment_id,)).fetchone()
        if not row:
            return True

        if user_name or user_role:
            author = row["author_name"] or ""
            role = row["author_role"] or ""
            if user_role not in ("auditor", "admin"):
                if author.strip().lower() != user_name.strip().lower() and role != user_role:
                    raise PermissionError("Solo el autor del comentario o el auditor líder pueden eliminar esta nota")

        conn.execute("DELETE FROM audit_comments WHERE id = ?;", (comment_id,))
        return True


# =============================================================================
# GESTIÓN MULTI-ESTÁNDAR (PLANTILLAS Y CLÁUSULAS DE NORMAS)
# =============================================================================

def list_all_checklist_templates(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna la lista de todas las normas oficiales y personalizadas disponibles."""
    init_audit_db()
    with get_audit_db_connection() as conn:
        sql = """
            SELECT t.*, count(c.clause_id) as total_clauses
            FROM checklist_templates t
            LEFT JOIN checklist_template_clauses c ON t.id = c.checklist_id
            GROUP BY t.id
            ORDER BY t.is_official DESC, t.name ASC;
        """
        rows = conn.execute(sql).fetchall()
        return [{
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "standard_family": r["standard_family"],
            "description": r["description"],
            "version": r["version"],
            "is_official": bool(r["is_official"]),
            "created_by": r["created_by"],
            "total_clauses": r["total_clauses"]
        } for r in rows]


def get_checklist_template(checklist_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una norma con todas sus cláusulas ordenadas."""
    init_audit_db()
    clean_id = (checklist_id or "nom070").strip().lower()
    with get_audit_db_connection() as conn:
        t_row = conn.execute("SELECT * FROM checklist_templates WHERE id = ?;", (clean_id,)).fetchone()
        if not t_row:
            # Fallback a nom070
            t_row = conn.execute("SELECT * FROM checklist_templates WHERE id = 'nom070';").fetchone()
            if not t_row:
                return None
            clean_id = "nom070"

        c_rows = conn.execute("""
            SELECT * FROM checklist_template_clauses
            WHERE checklist_id = ?
            ORDER BY display_order ASC, clause_id ASC;
        """, (clean_id,)).fetchall()

        clauses = [{
            "clause_id": c["clause_id"],
            "section": c["section"],
            "title": c["title"],
            "criterion": c["criterion"],
            "evidence_required": c["evidence_required"],
            "is_compliant": True
        } for c in c_rows]

        return {
            "id": t_row["id"],
            "name": t_row["name"],
            "code": t_row["code"],
            "standard_family": t_row["standard_family"],
            "description": t_row["description"],
            "version": t_row["version"],
            "is_official": bool(t_row["is_official"]),
            "created_by": t_row["created_by"],
            "total_clauses": len(clauses),
            "clauses": clauses
        }


def save_custom_checklist_template(template_data: Dict[str, Any], user_id: str = "auditor") -> Dict[str, Any]:
    """Crea o actualiza una norma personalizada con sus cláusulas."""
    init_audit_db()
    t_id = (template_data.get("id") or "").strip().lower()
    name = (template_data.get("name") or "").strip()
    code = (template_data.get("code") or "").strip().upper()
    family = (template_data.get("standard_family") or "Personalizado").strip()
    description = (template_data.get("description") or "").strip()
    version = (template_data.get("version") or "1.0").strip()
    clauses = template_data.get("clauses") or []

    if not name:
        raise ValueError("El nombre de la norma o checklist es obligatorio.")
    if not code:
        code = f"STD-{os.urandom(3).hex().upper()}"
    if not t_id:
        t_id = f"custom_{code.lower().replace(' ', '_').replace('-', '_')}"

    with get_audit_db_connection() as conn:
        conn.execute("""
            INSERT INTO checklist_templates (id, name, code, standard_family, description, version, is_official, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                code = excluded.code,
                standard_family = excluded.standard_family,
                description = excluded.description,
                version = excluded.version;
        """, (t_id, name, code, family, description, version, user_id))

        # Reemplazar cláusulas
        conn.execute("DELETE FROM checklist_template_clauses WHERE checklist_id = ?;", (t_id,))
        for idx, cl in enumerate(clauses, start=1):
            cl_id = str(cl.get("clause_id") or f"CL-{idx}").strip()
            sec = str(cl.get("section") or f"Sección {idx}").strip()
            title = str(cl.get("title") or f"Requisito {idx}").strip()
            crit = str(cl.get("criterion") or "Criterio de verificación").strip()
            ev = str(cl.get("evidence_required") or cl.get("evidence") or "Comprobante técnico").strip()

            conn.execute("""
                INSERT INTO checklist_template_clauses (checklist_id, clause_id, section, title, criterion, evidence_required, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (t_id, cl_id, sec, title, crit, ev, idx))

    return get_checklist_template(t_id)


def import_checklist_from_csv(
    csv_content: str,
    name: str = "",
    code: str = "",
    family: str = "Personalizado",
    user_id: str = "auditor"
) -> Dict[str, Any]:
    """Parsea un archivo CSV e inserta una nueva norma en la base de datos."""
    if not csv_content.strip():
        raise ValueError("El archivo CSV está vacío.")

    reader = csv.DictReader(io.StringIO(csv_content))
    clauses = []
    for idx, row in enumerate(reader, start=1):
        # Mapeo flexible de columnas en español e inglés
        sec = row.get("seccion") or row.get("sección") or row.get("section") or f"Sección {idx}"
        cl_id = row.get("clausula_id") or row.get("cláusula_id") or row.get("clause_id") or row.get("id") or f"CL-{idx}"
        title = row.get("titulo") or row.get("título") or row.get("title") or f"Requisito {idx}"
        crit = row.get("criterio") or row.get("criterion") or "Criterio de auditoría"
        ev = row.get("evidencia_requerida") or row.get("evidencia") or row.get("evidence") or "Evidencia técnica"

        clauses.append({
            "clause_id": cl_id.strip(),
            "section": sec.strip(),
            "title": title.strip(),
            "criterion": crit.strip(),
            "evidence_required": ev.strip()
        })

    if not clauses:
        raise ValueError("No se encontraron cláusulas válidas en el archivo CSV.")

    if not name:
        name = f"Checklist Importado ({len(clauses)} Cláusulas)"
    if not code:
        code = f"IMP-{os.urandom(2).hex().upper()}"

    template_data = {
        "name": name,
        "code": code,
        "standard_family": family,
        "description": f"Norma importada mediante archivo CSV con {len(clauses)} cláusulas técnicas.",
        "version": "1.0",
        "clauses": clauses
    }
    return save_custom_checklist_template(template_data, user_id=user_id)


def delete_custom_checklist_template(checklist_id: str, user_role: str = "") -> bool:
    """Elimina una norma personalizada si no es oficial del sistema."""
    init_audit_db()
    with get_audit_db_connection() as conn:
        row = conn.execute("SELECT is_official FROM checklist_templates WHERE id = ?;", (checklist_id,)).fetchone()
        if not row:
            return True
        if row["is_official"] == 1:
            raise PermissionError("No se pueden eliminar normas oficiales preconfiguradas del sistema.")

        conn.execute("DELETE FROM checklist_template_clauses WHERE checklist_id = ?;", (checklist_id,))
        conn.execute("DELETE FROM checklist_templates WHERE id = ?;", (checklist_id,))
        return True


def update_clause_evidence(checklist_id: str, clause_id: str, new_evidence: str) -> bool:
    """Actualiza la evidencia requerida para una cláusula en una plantilla o norma."""
    init_audit_db()
    clean_id = (checklist_id or "nom070").strip().lower()
    with get_audit_db_connection() as conn:
        cur = conn.execute("""
            UPDATE checklist_template_clauses
            SET evidence_required = ?
            WHERE checklist_id = ? AND clause_id = ?;
        """, (new_evidence, clean_id, clause_id))
        return cur.rowcount > 0


# =============================================================================
# EVALUACIÓN DE ESTADO Y SELLOS DIGITALES POR NORMA
# =============================================================================

def get_checklist_clause_states(system_id: int, checklist_id: str = "nom070") -> Dict[str, bool]:
    """Obtiene el diccionario {clause_id: is_compliant} para un sistema producto y norma específica."""
    init_audit_db()
    clean_id = (checklist_id or "nom070").strip().lower()
    with get_audit_db_connection() as conn:
        cur = conn.execute("""
            SELECT clause_id, is_compliant FROM checklist_states
            WHERE system_id = ? AND (checklist_id = ? OR (checklist_id IS NULL AND ? = 'nom070'));
        """, (system_id, clean_id, clean_id))
        return {r["clause_id"]: bool(r["is_compliant"]) for r in cur.fetchall()}


def set_checklist_clause_state(
    system_id: int,
    clause_id: str,
    is_compliant: bool,
    checklist_id: str = "nom070"
) -> None:
    """Registra o actualiza el estado de una cláusula para un sistema y norma."""
    init_audit_db()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    clean_id = (checklist_id or "nom070").strip().lower()

    with get_audit_db_connection() as conn:
        conn.execute("""
            INSERT INTO checklist_states (system_id, clause_id, is_compliant, updated_at, checklist_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(system_id, clause_id) DO UPDATE SET
                is_compliant = excluded.is_compliant,
                updated_at = excluded.updated_at,
                checklist_id = excluded.checklist_id;
        """, (system_id, clause_id, 1 if is_compliant else 0, now_iso, clean_id))


def get_audit_seal(system_id: int, checklist_id: str = "nom070") -> Optional[Dict[str, Any]]:
    """Obtiene el sello digital de un sistema si ha sido firmado."""
    init_audit_db()
    clean_id = (checklist_id or "nom070").strip().lower()
    with get_audit_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM audit_seals
            WHERE system_id = ? AND (checklist_id = ? OR checklist_id IS NULL OR ? = 'nom070');
        """, (system_id, clean_id, clean_id)).fetchone()
        if not row:
            # Fallback simple
            row = conn.execute("SELECT * FROM audit_seals WHERE system_id = ?;", (system_id,)).fetchone()
        if not row:
            return None
        return {
            "system_id": row["system_id"],
            "digital_seal": row["digital_seal"],
            "signed_by": row["signed_by"],
            "compliance_rate": row["compliance_rate"],
            "signed_at": row["signed_at"],
            "checklist_id": clean_id
        }


def save_audit_seal(
    system_id: int,
    digital_seal: str,
    signed_by: str,
    compliance_rate: float,
    checklist_id: str = "nom070"
) -> Dict[str, Any]:
    """Registra o actualiza el sello digital de auditoría para un sistema."""
    init_audit_db()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    clean_id = (checklist_id or "nom070").strip().lower()
    with get_audit_db_connection() as conn:
        conn.execute("""
            INSERT INTO audit_seals (system_id, digital_seal, signed_by, compliance_rate, signed_at, checklist_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(system_id) DO UPDATE SET
                digital_seal = excluded.digital_seal,
                signed_by = excluded.signed_by,
                compliance_rate = excluded.compliance_rate,
                signed_at = excluded.signed_at,
                checklist_id = excluded.checklist_id;
        """, (system_id, digital_seal, signed_by, compliance_rate, now_iso, clean_id))
        return {
            "system_id": system_id,
            "digital_seal": digital_seal,
            "signed_by": signed_by,
            "compliance_rate": compliance_rate,
            "signed_at": now_iso,
            "checklist_id": clean_id
        }
