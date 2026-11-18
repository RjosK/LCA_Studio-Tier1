"""
econode_studio/infrastructure/version_matcher_adapter.py - Motor Universal de Conciliacion y Cruce Multi-Base de Datos
Permite emparejar y convertir sistemas producto entre cualquier base de datos activa:
- ecoinvent 3.12 (Cutoff Unit)
- ecoinvent 3.11 (Cutoff Unit)
- SimaPro 9.5 (Imported CSV)
- OEKOBAUDAT (Construccion & EPD)
- GLAD Network (UNEP Global)
- Base Carbone (ADEME)
- Mis Procesos (User Custom)

Opera de forma transparente tanto en Supabase PostgreSQL (Cloud / Produccion)
como en SQLite local (Desarrollo / Desktop).
"""

import os
import json
import time
import re
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

try:
    from config import settings
except (ImportError, ValueError):
    from econode_studio.config import settings

from .db_connection import get_db_connection

# Mapeo de equivalencias y alias entre nomenclatura SimaPro y ecoinvent
SIMAPRO_ECOINVENT_ALIASES: Dict[str, str] = {
    "carbon dioxide, biogenic": "carbon dioxide, non-fossil",
    "carbon dioxide, land transformation": "carbon dioxide, from soil or biomass stock",
    "methane, biogenic": "methane, non-fossil",
    "carbon monoxide, biogenic": "carbon monoxide, non-fossil",
    "dinitrogen monoxide": "dinitrogen monoxide",
    "water, unspecified natural origin/m3": "water",
    "water, well, in ground": "water, well",
    "water, lake": "water, lake",
    "water, river": "water, river",
    "particulates, < 2.5 um": "particulate matter, < 2.5 um",
    "particulates, > 2.5 um, and < 10um": "particulate matter, > 2.5 um and < 10um",
    "particulates, > 10 um": "particulate matter, > 10 um",
    "dioxin, 2,3,7,8 tetrachlorodibenzo-p-": "dioxins, measured as 2,3,7,8-tetrachlorodibenzo-p-dioxin",
    "benzene, pentachloro-": "pentachlorobenzene",
    "benzene, hexachloro-": "hexachlorobenzene",
    "phenol, pentachloro-": "pentachlorophenol",
    "iron (ii)": "iron ion",
    "iron ii": "iron ion",
    "iron (iii)": "iron ion",
    "iron iii": "iron ion",
    "iron, ion": "iron ion",
    "iron ion": "iron ion",
    "copper, ion": "copper ion",
    "copper (i)": "copper ion",
    "copper i": "copper ion",
    "copper (ii)": "copper ion",
    "copper ii": "copper ion",
    "lead (ii)": "lead ii",
    "lead ii": "lead ii",
    "zinc (ii)": "zinc ii",
    "zinc ii": "zinc ii",
    "cadmium (ii)": "cadmium ii",
    "cadmium ii": "cadmium ii",
    "barium (ii)": "barium ii",
    "barium ii": "barium ii",
    "manganese (ii)": "manganese ii",
    "manganese ii": "manganese ii",
    "cobalt (ii)": "cobalt ii",
    "cobalt ii": "cobalt ii",
    "nickel (ii)": "nickel ii",
    "nickel ii": "nickel ii",
    "chromium (iii)": "chromium iii",
    "chromium iii": "chromium iii",
    "chromium (vi)": "chromium vi",
    "chromium vi": "chromium vi",
    "bod5 (biological oxygen demand), ch": "bod5, biological oxygen demand",
    "cod (chemical oxygen demand), ch": "cod, chemical oxygen demand",
    "transformation, from grassland/pasture/meadow": "transformation, from grassland, natural (non-use)",
    "transformation, to grassland/pasture/meadow, ch": "transformation, to grassland, natural (non-use)",
}

def parse_simapro_process_name(raw_name: str) -> Tuple[str, str, Optional[str]]:
    """
    Descompone un nombre de proceso de SimaPro en (actividad, producto, localizacion).
    Formatos comunes:
    - 'Product {LOC}| activity name | Cut-off, U'
    - 'Product {LOC}| activity name'
    - 'Product | activity name'
    """
    if not raw_name:
        return "", "", None
    loc = None
    m_loc = re.search(r"\{(.*?)\}", raw_name)
    if m_loc:
        loc = m_loc.group(1).strip()
    parts = raw_name.split("|")
    if len(parts) >= 2:
        activity_name = parts[1].strip()
        product_name = re.sub(r"\{.*?\}", "", parts[0]).strip()
        return activity_name, product_name, loc
    clean = re.sub(r"\{.*?\}", "", raw_name).strip()
    return clean, clean, loc

def normalize_flow_name(raw_name: str) -> str:
    """
    Normaliza nombres de flujos elementales de SimaPro a la nomenclatura canonica de ecoinvent.
    """
    if not raw_name:
        return ""
    n = re.sub(r"\s*\[.*?\]", "", raw_name).strip()

    # 1. Verificar alias directo antes de manipular numeracion romana
    lower_raw = n.lower().strip()
    if lower_raw in SIMAPRO_ECOINVENT_ALIASES:
        return SIMAPRO_ECOINVENT_ALIASES[lower_raw]

    # 2. Normalizar numerales romanos: e.g. Cadmium (II) -> Cadmium II
    n = re.sub(r"\(([I|V|X]+)\)", r"\1", n).strip()
    lower_n = n.lower().strip()
    if lower_n in SIMAPRO_ECOINVENT_ALIASES:
        return SIMAPRO_ECOINVENT_ALIASES[lower_n]

    if lower_n.startswith("particulates,"):
        return lower_n.replace("particulates,", "particulate matter,")
    if lower_n.endswith(", ch"):
        base = lower_n[:-4].strip()
        if base in SIMAPRO_ECOINVENT_ALIASES:
            return SIMAPRO_ECOINVENT_ALIASES[base]
        return base
    return n

# Catalogo Maestro de Bases de Datos Activas
AVAILABLE_DATABASES = [
    {
        "id": "ecoinvent_312",
        "name": "ecoinvent 3.12 (Cutoff Unit)",
        "version": "3.12",
        "short_label": "v3.12",
        "code_suffix": "v312",
        "badge": "ecoinvent",
        "count": "26,537",
        "process_count": 26537,
        "description": "Base canonica internacional ecoinvent 3.12 Cutoff Unit"
    },
    {
        "id": "ecoinvent_311",
        "name": "ecoinvent 3.11 (Cutoff Unit)",
        "version": "3.11",
        "short_label": "v3.11",
        "code_suffix": "v311",
        "badge": "ecoinvent",
        "count": "25,412",
        "process_count": 25412,
        "description": "Base canonica internacional ecoinvent 3.11 Cutoff Unit"
    },
    {
        "id": "simapro",
        "name": "SimaPro 9.5 (Imported CSV / LCI)",
        "version": "9.5",
        "short_label": "SimaPro",
        "code_suffix": "sp95",
        "badge": "simapro",
        "count": "Dinamico",
        "process_count": 500,
        "description": "Modelos y procesos importados via CSV de SimaPro 9.5"
    },
    {
        "id": "oekobaudat_de",
        "name": "OEKOBAUDAT (Construccion & EPD)",
        "version": "2024",
        "short_label": "OEKOBAUDAT",
        "code_suffix": "oeko",
        "badge": "oekobaudat",
        "count": "1,000",
        "process_count": 1000,
        "description": "Base de datos alemana para declaraciones ambientales de producto (EPD)"
    },
    {
        "id": "glad_network",
        "name": "GLAD Network (UNEP Global)",
        "version": "2024",
        "short_label": "GLAD",
        "code_suffix": "glad",
        "badge": "glad",
        "count": "500",
        "process_count": 500,
        "description": "Red global de inventarios de ciclo de vida del PNUMA (UNEP)"
    },
    {
        "id": "ademe_base_carbone",
        "name": "Base Carbone (ADEME)",
        "version": "v22",
        "short_label": "ADEME",
        "code_suffix": "ademe",
        "badge": "ademe",
        "count": "1,000",
        "process_count": 1000,
        "description": "Factores de emision y procesos franceses de la agencia ADEME"
    },
    {
        "id": "user_custom",
        "name": "Mis Procesos Propios",
        "version": "Custom",
        "short_label": "Propios",
        "code_suffix": "custom",
        "badge": "custom",
        "count": "Custom",
        "process_count": 100,
        "description": "Procesos y flujos modelados internamente por el analista"
    }
]

def get_available_databases(conn: Any) -> List[Dict[str, Any]]:
    """Retorna la lista de todas las bases de datos disponibles para el cruce de versiones."""
    return [dict(db) for db in AVAILABLE_DATABASES]

def _get_target_db_meta(target_id: str) -> Dict[str, Any]:
    for db in AVAILABLE_DATABASES:
        if db["id"] == target_id:
            return db
    return {
        "id": target_id,
        "name": f"Base de Datos {target_id}",
        "short_label": target_id,
        "code_suffix": target_id[:4].lower(),
        "badge": "all"
    }

def _get_sqlite_311_connection() -> sqlite3.Connection:
    """Retorna conexion a ecoinvent_311.db en entorno SQLite."""
    base_dir = getattr(settings, "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    p311 = os.path.join(base_dir, "ecoinvent", "ecoinvent_311.db")
    if not os.path.exists(p311):
        alt = os.path.join(os.path.dirname(base_dir), "ECONODE_TIER2", "ecoinvent", "ecoinvent_311.db")
        if os.path.exists(alt):
            p311 = alt
    conn = sqlite3.connect(p311)
    conn.row_factory = sqlite3.Row
    return conn

def search_database_processes(conn: Any, db_id: str, query: str = "", limit: int = 25) -> List[Dict[str, Any]]:
    """Buscador generico de procesos en una base de datos especifica."""
    is_pg = getattr(settings, "IS_POSTGRES", False)
    clean_q = query.strip()
    like_q = f"%{clean_q}%" if clean_q else "%"

    if db_id == "ecoinvent_311":
        if is_pg:
            sql = """
                SELECT id, code, name, location, reference_flow_name, reference_unit, category_name
                FROM lci_processes_311
                WHERE (name ILIKE ? OR code ILIKE ?)
                ORDER BY name LIMIT ?;
            """
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        else:
            conn_311 = _get_sqlite_311_connection()
            try:
                sql = """
                    SELECT p.id, p.code, p.name, coalesce(p.location, 'GLO') as location,
                           coalesce(f.name, p.name) as reference_flow_name,
                           coalesce(f.unit_symbol, 'kg') as reference_unit,
                           coalesce(c.name, 'General') as category_name
                    FROM processes p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN flows f ON p.reference_flow_id = f.id
                    WHERE (p.name LIKE ? OR p.code LIKE ?)
                    ORDER BY p.name LIMIT ?;
                """
                rows = conn_311.execute(sql, (like_q, like_q, limit)).fetchall()
            finally:
                conn_311.close()
        return [{
            "id": f"eco311_{r['id']}",
            "raw_id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "location": r["location"] or "GLO",
            "unit": r["reference_unit"] or "kg",
            "category": r["category_name"] or "General",
            "database": "ecoinvent 3.11"
        } for r in rows]

    elif db_id in ("oekobaudat_de", "glad_network", "ademe_base_carbone"):
        src_code = "oekobaudat_de" if db_id == "oekobaudat_de" else db_id
        sql = """
            SELECT MIN(id) as id, original_uuid as code, name, location,
                   activity_type as category_name, reference_product as reference_flow_name, unit as reference_unit
            FROM catalog_processes
            WHERE source_code = ? AND (name LIKE ? OR original_uuid LIKE ?)
            GROUP BY original_uuid, name, location, activity_type, reference_product, unit
            ORDER BY name LIMIT ?;
        """
        rows = conn.execute(sql, (src_code, like_q, like_q, limit)).fetchall()
        return [{
            "id": f"cat_{r['id']}",
            "raw_id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "location": r["location"] or "GLO",
            "unit": r["reference_unit"] or "kg",
            "category": r["category_name"] or "General",
            "database": _get_target_db_meta(db_id)["name"]
        } for r in rows]

    elif db_id == "user_custom":
        sql = """
            SELECT p.id, p.code, p.name, p.location,
                   coalesce(c.name, 'Custom processes & flows') as category_name,
                   coalesce(f.name, p.name) as reference_flow_name,
                   coalesce(f.unit_symbol, 'kg') as reference_unit
            FROM processes p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN flows f ON p.reference_flow_id = f.id
            WHERE (p.category_id = 999999 OR p.code LIKE 'CUSTOM_%' OR p.code LIKE 'PROC_CUSTOM_%' OR p.code LIKE 'SP-%')
              AND (p.name LIKE ? OR p.code LIKE ?)
            ORDER BY p.name LIMIT ?;
        """
        rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        return [{
            "id": r["id"],
            "raw_id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "location": r["location"] or "GLO",
            "unit": r["reference_unit"] or "kg",
            "category": r["category_name"] or "General",
            "database": _get_target_db_meta(db_id)["name"]
        } for r in rows]

    elif db_id == "simapro":
        sql = """
            SELECT p.id, p.code, p.name, p.location,
                   coalesce(c.name, 'SimaPro Imported') as category_name,
                   coalesce(f.name, p.name) as reference_flow_name,
                   coalesce(f.unit_symbol, 'kg') as reference_unit
            FROM processes p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN flows f ON p.reference_flow_id = f.id
            WHERE (p.code LIKE 'SP-%' OR lower(p.name) LIKE '%simapro%')
              AND (p.name LIKE ? OR p.code LIKE ?)
            ORDER BY p.name LIMIT ?;
        """
        rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        return [{
            "id": r["id"],
            "raw_id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "location": r["location"] or "GLO",
            "unit": r["reference_unit"] or "kg",
            "category": r["category_name"] or "General",
            "database": _get_target_db_meta(db_id)["name"]
        } for r in rows]

    else:
        # Default: ecoinvent 3.12
        if is_pg:
            sql = """
                SELECT id, code, name, location, reference_flow_name, reference_unit, category_name
                FROM lci_processes
                WHERE (name ILIKE ? OR code ILIKE ?)
                ORDER BY name LIMIT ?;
            """
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        else:
            sql = """
                SELECT p.id, p.code, p.name, p.location,
                       coalesce(c.name, 'General') as category_name,
                       coalesce(f.name, p.name) as reference_flow_name,
                       coalesce(f.unit_symbol, 'kg') as reference_unit
                FROM processes p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN flows f ON p.reference_flow_id = f.id
                WHERE (p.name LIKE ? OR p.code LIKE ?)
                ORDER BY p.name LIMIT ?;
            """
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        return [{
            "id": r["id"],
            "raw_id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "location": r["location"] or "GLO",
            "unit": r["reference_unit"] or "kg",
            "category": r["category_name"] or "General",
            "database": _get_target_db_meta(db_id)["name"]
        } for r in rows]

def search_database_flows(conn: Any, db_id: str, query: str = "", limit: int = 25) -> List[Dict[str, Any]]:
    """Buscador generico de flujos en una base de datos especifica."""
    is_pg = getattr(settings, "IS_POSTGRES", False)
    clean_q = query.strip()
    like_q = f"%{clean_q}%" if clean_q else "%"

    if db_id == "ecoinvent_311":
        if is_pg:
            sql = "SELECT id, code, name, flow_type, unit_symbol FROM lci_flows_311 WHERE (name ILIKE ? OR code ILIKE ?) ORDER BY name LIMIT ?;"
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        else:
            conn_311 = _get_sqlite_311_connection()
            try:
                sql = "SELECT id, code, name, flow_type, unit_symbol FROM flows WHERE (name LIKE ? OR code LIKE ?) ORDER BY name LIMIT ?;"
                rows = conn_311.execute(sql, (like_q, like_q, limit)).fetchall()
            finally:
                conn_311.close()
    else:
        # Default ecoinvent 3.12 / flows
        if is_pg:
            sql = "SELECT id, code, name, flow_type, unit_symbol FROM lci_flows WHERE (name ILIKE ? OR code ILIKE ?) ORDER BY name LIMIT ?;"
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()
        else:
            sql = "SELECT id, code, name, flow_type, unit_symbol FROM flows WHERE (name LIKE ? OR code LIKE ?) ORDER BY name LIMIT ?;"
            rows = conn.execute(sql, (like_q, like_q, limit)).fetchall()

    return [{
        "id": r["id"],
        "code": r["code"],
        "name": r["name"],
        "flow_type": r["flow_type"] or "PRODUCT_FLOW",
        "unit": r["unit_symbol"] or "kg"
    } for r in rows]

def _resolve_process_location(conn: Any, process_id: Any, fallback_loc: Optional[str] = None) -> str:
    """Resuelve la localizacion geografica canonica del proceso consultando la base de datos."""
    if not process_id:
        return (fallback_loc or "GLO").strip()

    clean_id = str(process_id).replace("eco311_", "").replace("cat_", "").replace("proc_lci_", "")
    is_pg = getattr(settings, "IS_POSTGRES", False)

    if clean_id.isdigit():
        int_id = int(clean_id)
        # 1. Probar en lci_processes / processes (ecoinvent 3.12)
        tbl_312 = "lci_processes" if is_pg else "processes"
        try:
            row = conn.execute(f"SELECT location FROM {tbl_312} WHERE id = ? LIMIT 1;", (int_id,)).fetchone()
            if row and row[0]:
                return str(row[0]).strip()
        except Exception:
            pass

        # 2. Probar en lci_processes_311 (ecoinvent 3.11)
        if is_pg:
            try:
                row = conn.execute("SELECT location FROM lci_processes_311 WHERE id = ? LIMIT 1;", (int_id,)).fetchone()
                if row and row[0]:
                    return str(row[0]).strip()
            except Exception:
                pass
        else:
            try:
                conn_311 = _get_sqlite_311_connection()
                try:
                    r311 = conn_311.execute("SELECT location FROM processes WHERE id = ? LIMIT 1;", (int_id,)).fetchone()
                    if r311 and r311["location"]:
                        return str(r311["location"]).strip()
                finally:
                    conn_311.close()
            except Exception:
                pass

        # 3. Probar en catalog_processes
        try:
            row = conn.execute("SELECT location FROM catalog_processes WHERE id = ? LIMIT 1;", (int_id,)).fetchone()
            if row and row[0]:
                return str(row[0]).strip()
        except Exception:
            pass

    return (fallback_loc or "GLO").strip()

def match_system_to_database(conn: Any, system_id: int, target_db_id: str) -> Dict[str, Any]:
    """
    Evalua exhaustivamente un sistema producto frente a una base de datos de destino.
    Compara:
    1. Procesos unitarios (Clave canonica Name + Location).
    2. Flujos intercambiados (Verifica si existen en destino o requieren mapeo).
    """
    is_pg = getattr(settings, "IS_POSTGRES", False)
    target_meta = _get_target_db_meta(target_db_id)

    # 1. Obtener datos del sistema producto
    row = conn.execute("SELECT id, name, code, description, parameters_json FROM product_systems WHERE id = ?;", (system_id,)).fetchone()
    if not row:
        raise ValueError(f"Sistema producto #{system_id} no encontrado.")

    sys_name = row["name"]
    sys_code = row["code"] or f"SYS_{system_id:04d}"
    raw_p = row["parameters_json"]
    p_obj = json.loads(raw_p) if isinstance(raw_p, str) else (raw_p or {})

    nodes = p_obj.get("canvas_nodes", [])
    edges = p_obj.get("canvas_edges", [])
    palette = p_obj.get("palette_processes", [])
    palette_locs = {}
    for p in palette:
        pid = str(p.get("process_id") or p.get("id", ""))
        if p.get("location"):
            palette_locs[pid] = p.get("location").strip()

    # Si canvas_nodes esta vacio, obtener nodos relacionales
    if not nodes:
        node_rows = conn.execute("""
            SELECT n.process_id, n.pos_x, n.pos_y, p.name, p.location, p.code
            FROM product_system_nodes n
            LEFT JOIN processes p ON n.process_id = p.id
            WHERE n.system_id = ?;
        """, (system_id,)).fetchall()
        nodes = [{
            "id": f"node_{r['process_id']}",
            "process_id": r["process_id"],
            "name": r["name"] or f"Proceso #{r['process_id']}",
            "location": r["location"] or "GLO",
            "x": r["pos_x"],
            "y": r["pos_y"]
        } for r in node_rows]

    # 2. Diagnostico de Procesos
    processes_match = []
    flows_match = []
    exact_count = 0
    loc_diff_count = 0
    no_match_count = 0
    characterized_flows = 0

    for n in nodes:
        node_id = n.get("id") or f"node_{n.get('process_id')}"
        src_pid = n.get("process_id")
        src_name = (n.get("name") or "").strip()
        raw_node_loc = n.get("location")
        palette_loc = palette_locs.get(str(src_pid)) if src_pid else None
        candidate_loc = raw_node_loc or palette_loc
        src_loc = _resolve_process_location(conn, src_pid, fallback_loc=candidate_loc)

        inputs = n.get("inputs", [])
        outputs = n.get("outputs", [])
        has_embedded_exchanges = bool(inputs or outputs)
        is_custom_id = not src_pid or str(src_pid).startswith("node_") or str(src_pid).startswith("SP-") or str(src_pid).startswith("CUSTOM_")
        is_custom_cat = (n.get("category") or "").lower() in ("material", "unspecified", "custom", "general", "process")

        # Coincidencia canonica en la base destino
        candidates = search_database_processes(conn, target_db_id, query=src_name, limit=10)

        # Si el nodo contiene intercambios internos y no es un proceso de fondo de ecoinvent,
        # se reconoce como proceso de primer plano (FOREGROUND_CUSTOM).
        if has_embedded_exchanges and (is_custom_id or is_custom_cat or not candidates or candidates[0]["name"].strip().lower() != src_name.lower()):
            ref_unit = "kg"
            for out in outputs:
                if out.get("is_reference"):
                    ref_unit = out.get("unit") or "kg"
                    break
            else:
                if outputs:
                    ref_unit = outputs[0].get("unit") or "kg"

            node_flow_issues = 0

            # Pre-optimizacion masiva: resolver flujos y procesos en bloque en 1 sola consulta
            flow_name_keys = set()
            proc_name_keys = set()
            for inp in inputs:
                if inp.get("is_elementary"):
                    flow_name_keys.add(normalize_flow_name(inp.get("name", "")).strip().lower())
                else:
                    act, _, _ = parse_simapro_process_name(inp.get("name", ""))
                    if act:
                        proc_name_keys.add(act.strip().lower())
            for out in outputs:
                if not out.get("is_reference"):
                    oname = out.get("name", "")
                    if "{" in oname and "|" in oname:
                        act, _, _ = parse_simapro_process_name(oname)
                        if act:
                            proc_name_keys.add(act.strip().lower())
                    else:
                        flow_name_keys.add(normalize_flow_name(oname).strip().lower())

            batch_flow_map = {}
            if flow_name_keys:
                try:
                    tbl_f = "lci_flows_311" if target_db_id == "ecoinvent_311" and is_pg else ("flows" if not is_pg else "lci_flows")
                    pl_f = ", ".join(["?"] * len(flow_name_keys))
                    for fr in conn.execute(f"SELECT id, name, unit_symbol FROM {tbl_f} WHERE LOWER(name) IN ({pl_f});", tuple(flow_name_keys)).fetchall():
                        batch_flow_map[fr["name"].strip().lower()] = fr
                except Exception:
                    pass

            batch_proc_map = {}
            if proc_name_keys:
                try:
                    tbl_p = "lci_processes_311" if target_db_id == "ecoinvent_311" and is_pg else ("processes" if not is_pg else "lci_processes")
                    pl_p = ", ".join(["?"] * len(proc_name_keys))
                    for pr in conn.execute(f"SELECT id, name, location FROM {tbl_p} WHERE LOWER(name) IN ({pl_p});", tuple(proc_name_keys)).fetchall():
                        batch_proc_map[pr["name"].strip().lower()] = pr
                except Exception:
                    pass

            memo_proc = {}
            memo_flow = {}

            # Evaluar insumos embebidos (tecnosfera y recursos)
            for inp in inputs:
                iname = inp.get("name", "")
                iunit = inp.get("unit", "kg")
                iamt = float(inp.get("amount", 1.0))
                is_elem = bool(inp.get("is_elementary", False))

                if not is_elem:
                    act, prod, loc = parse_simapro_process_name(iname)
                    act_l = act.strip().lower()
                    if act_l in batch_proc_map:
                        pr = batch_proc_map[act_l]
                        cands = [{"id": pr["id"], "name": pr["name"], "location": pr["location"] or "GLO", "unit": iunit}]
                    elif act_l in memo_proc:
                        cands = memo_proc[act_l]
                    else:
                        cands = search_database_processes(conn, target_db_id, query=act, limit=3)
                        if not cands and "," in act:
                            cands = search_database_processes(conn, target_db_id, query=act.split(",")[0].strip(), limit=3)
                        memo_proc[act_l] = cands

                    if cands:
                        characterized_flows += 1
                        flows_match.append({
                            "flow_id": f"in_{len(flows_match)+1}",
                            "name": iname,
                            "amount": iamt,
                            "unit": iunit,
                            "status": "FLOW_MATCH",
                            "target_flow_id": cands[0]["id"],
                            "target_flow_name": cands[0]["name"],
                            "is_characterized": True,
                            "exchange_type": "technosphere_input",
                            "source_node_id": node_id,
                            "message": f"Insumo identificado en {target_meta['short_label']}."
                        })
                    else:
                        node_flow_issues += 1
                        flows_match.append({
                            "flow_id": f"in_{len(flows_match)+1}",
                            "name": iname,
                            "amount": iamt,
                            "unit": iunit,
                            "status": "FLOW_UNCHARACTERIZED",
                            "target_flow_id": None,
                            "target_flow_name": iname,
                            "is_characterized": False,
                            "suggested_flows": [],
                            "exchange_type": "technosphere_input",
                            "source_node_id": node_id,
                            "message": f"Insumo no encontrado directamente en {target_meta['short_label']}."
                        })
                else:
                    norm = normalize_flow_name(iname)
                    norm_l = norm.strip().lower()
                    if norm_l in batch_flow_map:
                        fr = batch_flow_map[norm_l]
                        fcands = [{"id": fr["id"], "name": fr["name"], "unit": fr["unit_symbol"] or iunit}]
                    elif norm_l in memo_flow:
                        fcands = memo_flow[norm_l]
                    else:
                        fcands = search_database_flows(conn, target_db_id, query=norm, limit=3)
                        if not fcands and "," in norm:
                            fcands = search_database_flows(conn, target_db_id, query=norm.split(",")[0].strip(), limit=3)
                        memo_flow[norm_l] = fcands

                    if fcands:
                        characterized_flows += 1
                        flows_match.append({
                            "flow_id": f"in_{len(flows_match)+1}",
                            "name": iname,
                            "amount": iamt,
                            "unit": iunit,
                            "status": "FLOW_MATCH",
                            "target_flow_id": fcands[0]["id"],
                            "target_flow_name": fcands[0]["name"],
                            "is_characterized": True,
                            "exchange_type": "elementary_resource",
                            "source_node_id": node_id,
                            "message": f"Recurso natural identificado en {target_meta['short_label']}."
                        })
                    else:
                        node_flow_issues += 1
                        flows_match.append({
                            "flow_id": f"in_{len(flows_match)+1}",
                            "name": iname,
                            "amount": iamt,
                            "unit": iunit,
                            "status": "FLOW_UNCHARACTERIZED",
                            "target_flow_id": None,
                            "target_flow_name": iname,
                            "is_characterized": False,
                            "suggested_flows": [],
                            "exchange_type": "elementary_resource",
                            "source_node_id": node_id,
                            "message": f"Recurso elemental no caracterizado directamente en {target_meta['short_label']}."
                        })

            # Evaluar emisiones embebidas y tratamientos de residuos
            for out in outputs:
                if out.get("is_reference"):
                    continue
                oname = out.get("name", "")
                ounit = out.get("unit", "kg")
                oamt = float(out.get("amount", 1.0))

                if "{" in oname and "|" in oname:
                    act, prod, loc = parse_simapro_process_name(oname)
                    act_l = act.strip().lower()
                    if act_l in batch_proc_map:
                        pr = batch_proc_map[act_l]
                        cands = [{"id": pr["id"], "name": pr["name"], "location": pr["location"] or "GLO", "unit": ounit}]
                    elif act_l in memo_proc:
                        cands = memo_proc[act_l]
                    else:
                        cands = search_database_processes(conn, target_db_id, query=act, limit=3)
                        if not cands and "," in act:
                            cands = search_database_processes(conn, target_db_id, query=act.split(",")[0].strip(), limit=3)
                        memo_proc[act_l] = cands

                    if cands:
                        characterized_flows += 1
                        flows_match.append({
                            "flow_id": f"out_{len(flows_match)+1}",
                            "name": oname,
                            "amount": oamt,
                            "unit": ounit,
                            "status": "FLOW_MATCH",
                            "target_flow_id": cands[0]["id"],
                            "target_flow_name": cands[0]["name"],
                            "is_characterized": True,
                            "exchange_type": "waste_treatment",
                            "source_node_id": node_id,
                            "message": f"Tratamiento de residuo identificado en {target_meta['short_label']}."
                        })
                    else:
                        node_flow_issues += 1
                        flows_match.append({
                            "flow_id": f"out_{len(flows_match)+1}",
                            "name": oname,
                            "amount": oamt,
                            "unit": ounit,
                            "status": "FLOW_UNCHARACTERIZED",
                            "target_flow_id": None,
                            "target_flow_name": oname,
                            "is_characterized": False,
                            "suggested_flows": [],
                            "exchange_type": "waste_treatment",
                            "source_node_id": node_id,
                            "message": f"Tratamiento no encontrado directamente en {target_meta['short_label']}."
                        })
                else:
                    norm = normalize_flow_name(oname)
                    norm_l = norm.strip().lower()
                    if norm_l in batch_flow_map:
                        fr = batch_flow_map[norm_l]
                        fcands = [{"id": fr["id"], "name": fr["name"], "unit": fr["unit_symbol"] or ounit}]
                    elif norm_l in memo_flow:
                        fcands = memo_flow[norm_l]
                    else:
                        fcands = search_database_flows(conn, target_db_id, query=norm, limit=3)
                        if not fcands and "," in norm:
                            fcands = search_database_flows(conn, target_db_id, query=norm.split(",")[0].strip(), limit=3)
                        memo_flow[norm_l] = fcands

                    if fcands:
                        characterized_flows += 1
                        flows_match.append({
                            "flow_id": f"out_{len(flows_match)+1}",
                            "name": oname,
                            "amount": oamt,
                            "unit": ounit,
                            "status": "FLOW_MATCH",
                            "target_flow_id": fcands[0]["id"],
                            "target_flow_name": fcands[0]["name"],
                            "is_characterized": True,
                            "exchange_type": "elementary_emission",
                            "source_node_id": node_id,
                            "message": f"Emision elemental identificada en {target_meta['short_label']}."
                        })
                    else:
                        node_flow_issues += 1
                        flows_match.append({
                            "flow_id": f"out_{len(flows_match)+1}",
                            "name": oname,
                            "amount": oamt,
                            "unit": ounit,
                            "status": "FLOW_UNCHARACTERIZED",
                            "target_flow_id": None,
                            "target_flow_name": oname,
                            "is_characterized": False,
                            "suggested_flows": [],
                            "exchange_type": "elementary_emission",
                            "source_node_id": node_id,
                            "message": f"Emision elemental no caracterizada directamente en {target_meta['short_label']}."
                        })

            if node_flow_issues == 0:
                node_status = "FOREGROUND_CUSTOM"
                exact_count += 1
                confidence = 1.0
                target_proc_id = node_id
                target_name = f"{src_name} (Conservado)"
                msg = f"Modelo de primer plano conservado. Se transfieren {len(inputs)} insumos y {len(outputs)} emisiones compatibles a {target_meta['short_label']}."
            else:
                node_status = "EXCHANGES_PENDING"
                no_match_count += 1
                confidence = round(max(0.0, 1.0 - (node_flow_issues / max(1, len(inputs) + len(outputs)))), 2)
                target_proc_id = None
                target_name = f"{src_name} ({node_flow_issues} insumos sin equivalencia)"
                msg = f"Modelo de primer plano con {node_flow_issues} intercambios sin equivalencia directa en {target_meta['short_label']}. Requiere revisión o sustitución."

            processes_match.append({
                "node_id": node_id,
                "source_process_id": src_pid or node_id,
                "source_name": src_name,
                "source_location": src_loc,
                "status": node_status,
                "confidence": confidence,
                "is_foreground": True,
                "target_process_id": target_proc_id,
                "target_name": target_name,
                "target_location": src_loc,
                "target_unit": ref_unit,
                "inputs_count": len(inputs),
                "outputs_count": len(outputs),
                "missing_exchanges_count": node_flow_issues,
                "alternatives": [],
                "message": msg
            })
            continue

        # Buscar match exacto de (nombre, localizacion)
        exact = next((c for c in candidates if c["name"].strip().lower() == src_name.lower() and c["location"].strip().lower() == src_loc.lower()), None)
        if not exact:
            # Buscar match exacto de nombre insensible a mayusculas
            same_name_alts = [c for c in candidates if c["name"].strip().lower() == src_name.lower()]
            if same_name_alts:
                status = "LOCATION_DIFF"
                primary = same_name_alts[0]
                loc_diff_count += 1
                processes_match.append({
                    "node_id": node_id,
                    "source_process_id": src_pid,
                    "source_name": src_name,
                    "source_location": src_loc,
                    "status": status,
                    "confidence": 0.85,
                    "target_process_id": primary["id"],
                    "target_name": primary["name"],
                    "target_location": primary["location"],
                    "target_unit": primary["unit"],
                    "alternatives": same_name_alts,
                    "message": f"El proceso existe en {target_meta['short_label']} con geografia '{primary['location']}' (origen: '{src_loc}')."
                })
            else:
                status = "NO_MATCH"
                no_match_count += 1
                # Sugerencias parciales usando el primer token significativo
                first_token = re.split(r"[,\|]", src_name)[0].strip()
                token_alts = search_database_processes(conn, target_db_id, query=first_token, limit=6) if first_token else []
                processes_match.append({
                    "node_id": node_id,
                    "source_process_id": src_pid,
                    "source_name": src_name,
                    "source_location": src_loc,
                    "status": status,
                    "confidence": 0.0,
                    "target_process_id": token_alts[0]["id"] if token_alts else None,
                    "target_name": token_alts[0]["name"] if token_alts else None,
                    "target_location": token_alts[0]["location"] if token_alts else None,
                    "target_unit": token_alts[0]["unit"] if token_alts else "kg",
                    "alternatives": token_alts,
                    "message": f"Proceso no encontrado directamente en {target_meta['short_label']}. Selecciona un sustituto."
                })
        else:
            status = "EXACT_MATCH"
            exact_count += 1
            processes_match.append({
                "node_id": node_id,
                "source_process_id": src_pid,
                "source_name": src_name,
                "source_location": src_loc,
                "status": status,
                "confidence": 1.0,
                "target_process_id": exact["id"],
                "target_name": exact["name"],
                "target_location": exact["location"],
                "target_unit": exact["unit"],
                "alternatives": [exact],
                "message": f"Coincidencia exacta 1-a-1 en {target_meta['short_label']}."
            })

    # 3. Diagnostico de Flujos entre Nodos
    total_flows = len(edges) + len(flows_match)

    for e in edges:
        fl_id = str(e.get("flow_id") or e.get("flow") or "").strip()
        fl_name = str(e.get("flow_name") or e.get("flow") or "Flujo de Intercambio").strip()
        amt = float(e.get("amount", 1.0))
        unit = str(e.get("unit") or "kg").strip()

        # Comprobar si el flujo existe en la base destino
        fl_cands = search_database_flows(conn, target_db_id, query=fl_name, limit=5)
        fl_exact = next((f for f in fl_cands if f["name"].strip().lower() == fl_name.lower()), None)

        if fl_exact:
            characterized_flows += 1
            flows_match.append({
                "flow_id": fl_id,
                "name": fl_name,
                "amount": amt,
                "unit": unit,
                "status": "FLOW_MATCH",
                "target_flow_id": fl_exact["id"],
                "target_flow_name": fl_exact["name"],
                "is_characterized": True,
                "message": f"Flujo disponible y caracterizado en {target_meta['short_label']}."
            })
        else:
            flows_match.append({
                "flow_id": fl_id,
                "name": fl_name,
                "amount": amt,
                "unit": unit,
                "status": "FLOW_UNCHARACTERIZED",
                "target_flow_id": fl_cands[0]["id"] if fl_cands else fl_id,
                "target_flow_name": fl_cands[0]["name"] if fl_cands else fl_name,
                "is_characterized": False,
                "suggested_flows": fl_cands,
                "message": f"Flujo sin factor de caracterizacion directo en {target_meta['short_label']}. Se mantendra la conexion como flujo elemental informativo a menos que selecciones un sustituto."
            })

    # Estadisticas Globales ponderadas (procesos + flujos/intercambios)
    total_proc = len(nodes)
    total_flows = len(flows_match)
    total_components = total_proc + total_flows
    matched_components = (exact_count * 1.0) + (loc_diff_count * 0.85) + characterized_flows
    comp_pct = round((matched_components / max(1, total_components)) * 100.0, 1) if total_components > 0 else 100.0
    ready = (no_match_count == 0)

    # Nomenclatura Automatica del Sistema Clonado
    auto_name = f"{sys_name} ({target_meta['short_label']})"
    auto_code = f"{sys_code}_{target_meta['code_suffix']}"

    # Enrich each process match with convenient aliases for UI and tests
    for pm in processes_match:
        pm["source_node_name"] = pm.get("source_name", "")
        pm["source_process_code"] = pm.get("source_process_id") or pm.get("source_name", "")
        if pm.get("target_process_id"):
            pm["suggested_match"] = {
                "id": pm["target_process_id"],
                "name": pm["target_name"],
                "location": pm["target_location"],
                "unit": pm.get("target_unit", "kg"),
                "database": target_meta["name"],
                "similarity": pm.get("confidence", 1.0)
            }
        else:
            pm["suggested_match"] = None
        pm["alternative_locations"] = [
            {"id": alt["id"], "location": alt.get("location", "GLO"), "name": alt.get("name", pm.get("target_name", ""))}
            for alt in pm.get("alternatives", [])
        ]

    flow_issues_list = [f for f in flows_match if not f.get("is_characterized")]
    for fi in flow_issues_list:
        fi["flow_code"] = fi.get("flow_id", "")
        fi["flow_name"] = fi.get("name", "")
        fi["issue"] = fi.get("message", "Flujo elemental sin caracterizar en base destino.")

    return {
        "system_id": system_id,
        "target_version": target_db_id,
        "source_system": {
            "id": system_id,
            "name": sys_name,
            "code": sys_code
        },
        "target_database": target_meta,
        "processes_count": total_proc,
        "total_nodes": total_proc,
        "exact_matches": exact_count,
        "location_diffs": loc_diff_count,
        "no_matches": no_match_count,
        "compatibility_percentage": comp_pct,
        "compatibility_score": comp_pct,
        "is_ready_for_conversion": ready,
        "auto_generated_name": auto_name,
        "auto_generated_code": auto_code,
        "processes_match": processes_match,
        "nodes": processes_match,
        "flows_match": flows_match,
        "flow_issues": flow_issues_list,
        "flow_issues_count": len(flow_issues_list),
        "flows_count": total_flows,
        "characterized_flows_count": characterized_flows
    }

def convert_product_system_version(
    conn: Any,
    system_id: int,
    target_db_id: str,
    process_mappings: Dict[str, Any],
    flow_mappings: Optional[Dict[str, Any]] = None,
    custom_name: Optional[str] = None,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta la conversion y clonacion del sistema producto a la nueva version seleccionada.
    Crea el nuevo sistema producto en el Dashboard y devuelve new_system_id para conmutar el Canvas.
    """
    target_meta = _get_target_db_meta(target_db_id)
    flow_map = flow_mappings or {}

    # 1. Leer sistema producto origen
    row = conn.execute("SELECT * FROM product_systems WHERE id = ?;", (system_id,)).fetchone()
    if not row:
        raise ValueError(f"Sistema producto #{system_id} no encontrado.")

    src_name = row["name"]
    src_code = row["code"] or f"SYS_{system_id:04d}"
    proj_id = row["project_id"] if "project_id" in row.keys() else None

    # Nombres y codigos derivados
    new_name = custom_name.strip() if custom_name and custom_name.strip() else f"{src_name} ({target_meta['short_label']})"
    new_code = f"{src_code}_{target_meta['code_suffix']}"
    
    # Evitar colision de SKU
    existing = conn.execute("SELECT id FROM product_systems WHERE code = ?;", (new_code,)).fetchone()
    if existing:
        new_code = f"{new_code}_{uuid.uuid4().hex[:4]}"

    new_db_profile = target_meta["name"]

    # 2. Parsear y actualizar nodes y edges
    raw_p = row["parameters_json"]
    p_obj = json.loads(raw_p) if isinstance(raw_p, str) else (raw_p or {})

    nodes = p_obj.get("canvas_nodes", [])
    edges = p_obj.get("canvas_edges", [])
    params = p_obj.get("parameters", [])
    epd_cfg = p_obj.get("epd_config")

    updated_nodes = []
    for n in nodes:
        n_copy = dict(n)
        nid = n_copy.get("id") or f"node_{n_copy.get('process_id')}"
        
        # Mapeo de proceso
        mapping = process_mappings.get(nid)
        if mapping:
            if isinstance(mapping, dict):
                n_copy["process_id"] = mapping.get("target_process_id") or n_copy.get("process_id")
                if mapping.get("target_name"):
                    n_copy["name"] = mapping["target_name"]
                if mapping.get("target_location"):
                    n_copy["location"] = mapping["target_location"]
            elif str(mapping) != str(nid) and not str(mapping).startswith("node_"):
                n_copy["process_id"] = mapping

        # Si el nodo tiene inputs embebidos, actualizar sus flujos / procesos
        if n_copy.get("inputs"):
            updated_inputs = []
            for inp in n_copy["inputs"]:
                inp_c = dict(inp)
                iname = inp_c.get("name", "")
                if inp_c.get("is_elementary"):
                    inp_c["normalized_name"] = normalize_flow_name(iname)
                else:
                    act, prod, loc = parse_simapro_process_name(iname)
                    inp_c["activity_name"] = act
                    if loc:
                        inp_c["location"] = loc
                updated_inputs.append(inp_c)
            n_copy["inputs"] = updated_inputs

        # Si el nodo tiene outputs embebidos, actualizar sus flujos
        if n_copy.get("outputs"):
            updated_outputs = []
            for out in n_copy["outputs"]:
                out_c = dict(out)
                oname = out_c.get("name", "")
                if not out_c.get("is_reference"):
                    if "{" in oname and "|" in oname:
                        act, prod, loc = parse_simapro_process_name(oname)
                        out_c["activity_name"] = act
                    else:
                        out_c["normalized_name"] = normalize_flow_name(oname)
                updated_outputs.append(out_c)
            n_copy["outputs"] = updated_outputs

        updated_nodes.append(n_copy)

    # Actualizar edges con flujos mapeados si se sustituyeron
    updated_edges = []
    for e in edges:
        e_copy = dict(e)
        fl_id = str(e_copy.get("flow_id") or e_copy.get("flow") or "")
        if fl_id in flow_map:
            sub = flow_map[fl_id]
            if isinstance(sub, dict):
                e_copy["flow_id"] = sub.get("target_flow_id", fl_id)
                e_copy["flow_name"] = sub.get("target_flow_name", e_copy.get("flow_name"))
            else:
                e_copy["flow_id"] = sub
        updated_edges.append(e_copy)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    new_params_json = {
        "canvas_nodes": updated_nodes,
        "canvas_edges": updated_edges,
        "parameters": params,
        "epd_config": epd_cfg,
        "source_format": "version_switch",
        "created_at": now_str,
        "updated_at": now_str,
        "converted_from_system_id": system_id,
        "converted_from_version": row["db_profile"] if "db_profile" in row.keys() else "ecoinvent 3.12"
    }

    # 3. Insertar el nuevo sistema producto en product_systems
    owner_id = user_id or (row["owner_id"] if "owner_id" in row.keys() else "analyst_carla")
    owner_email = user_email or (row["owner_email"] if "owner_email" in row.keys() else "carla.mendez@econode.io")
    owner_name = row["owner_name"] if "owner_name" in row.keys() else "Carla Mendez"
    owner_role = row["owner_role"] if "owner_role" in row.keys() else "analyst"
    owner_org = row["owner_org"] if "owner_org" in row.keys() else "BioPack Industrial S.A. de C.V."
    category = row["category"] if "category" in row.keys() else "General"
    geography = row["geography"] if "geography" in row.keys() else "[MX]"
    desc = f"Convertido a {target_meta['name']} a partir del modelo '{src_name}' ({src_code})."

    with conn:
        cur = conn.execute("""
            INSERT INTO product_systems (
                name, code, target_amount, description, parameters_json,
                owner_id, owner_email, owner_name, owner_role, owner_org,
                category, geography, status, compliance_rate, project_id,
                created_at, updated_at, db_profile
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', '100.0%', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
        """, (
            new_name, new_code, float(row["target_amount"] or 1.0), desc,
            json.dumps(new_params_json, ensure_ascii=False),
            owner_id, owner_email, owner_name, owner_role, owner_org,
            category, geography, proj_id, target_meta["name"]
        ))
        new_sys_id = cur.lastrowid

        # 4. Guardar nodos relacionales en product_system_nodes
        try:
            conn.execute("DELETE FROM product_system_nodes WHERE system_id = ?;", (new_sys_id,))
            for n in updated_nodes:
                pid = n.get("process_id")
                if pid:
                    clean_pid = int(str(pid).replace("eco311_", "").replace("cat_", "")) if str(pid).isdigit() or str(pid).replace("eco311_", "").isdigit() else 100001
                    conn.execute("""
                        INSERT INTO product_system_nodes (system_id, process_id, pos_x, pos_y)
                        VALUES (?, ?, ?, ?);
                    """, (new_sys_id, clean_pid, float(n.get("x", 100)), float(n.get("y", 140))))
        except Exception:
            pass

        # 5. Guardar enlaces relacionales en product_system_edges
        try:
            conn.execute("DELETE FROM product_system_edges WHERE system_id = ?;", (new_sys_id,))
            for e in updated_edges:
                conn.execute("""
                    INSERT INTO product_system_edges (system_id, source_process_id, target_process_id, flow_id, amount)
                    VALUES (?, ?, ?, ?, ?);
                """, (new_sys_id, e.get("source_process_id") or e.get("from"), e.get("target_process_id") or e.get("to"), str(e.get("flow_id", "")), float(e.get("amount", 1.0))))
        except Exception:
            pass

    return {
        "status": "ok",
        "success": True,
        "new_system_id": new_sys_id,
        "new_system": {
            "id": new_sys_id,
            "name": new_name,
            "code": new_code,
            "source_db": target_db_id,
            "db_profile": new_db_profile,
            "nodes_count": len(updated_nodes),
            "edges_count": len(updated_edges),
            "project_id": proj_id
        },
        "message": f"Sistema producto '{new_name}' creado exitosamente en {target_meta['name']}."
    }
