"""
econode_studio/application/product_systems.py - Casos de Uso para Gestión e Importación de Sistemas Producto
"""

import sqlite3
import os
import sys
import csv
import io
import json
from typing import Dict, List, Any, Optional

try:
    from infrastructure.database_adapter import (
        list_product_systems, create_product_system, get_product_system_details, save_system_canvas,
        delete_product_system, add_system_collaborator, get_system_parameters, save_system_parameter, delete_system_parameter,
        create_project, list_projects, get_project_by_id, delete_project, assign_system_to_project,
        get_active_db_connection
    )
    from infrastructure.simapro_adapter import parse_simapro_csv, simapro_process_to_econode_node
except (ImportError, ValueError):
    from econode_studio.infrastructure.database_adapter import (
        list_product_systems, create_product_system, get_product_system_details, save_system_canvas,
        delete_product_system, add_system_collaborator, get_system_parameters, save_system_parameter, delete_system_parameter,
        create_project, list_projects, get_project_by_id, delete_project, assign_system_to_project,
        get_active_db_connection
    )
    from econode_studio.infrastructure.simapro_adapter import parse_simapro_csv, simapro_process_to_econode_node


def get_dashboard_systems_use_case(
    conn: Optional[sqlite3.Connection] = None,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtiene los sistemas producto filtrados por el propietario y rol del usuario."""
    if conn is None:
        with get_active_db_connection() as c:
            return list_product_systems(c, user_email=user_email, user_id=user_id, user_role=user_role)
    return list_product_systems(conn, user_email=user_email, user_id=user_id, user_role=user_role)


def create_system_wizard_use_case(
    conn: Optional[sqlite3.Connection] = None,
    data: Optional[Dict[str, Any]] = None,
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Crea un nuevo sistema producto asociándolo al usuario activo autenticado."""
    data = data or {}
    name = (data.get("name") or "").strip()
    code = (data.get("code") or "").strip()
    target_amount = float(data.get("target_amount") or data.get("reference_amount") or 1.0)
    description = (data.get("description") or "").strip()
    category = data.get("category") or "Polímeros"
    geography = data.get("geography") or "[MX]"
    raw_proj = data.get("project_id")
    project_id = int(raw_proj) if raw_proj not in (None, "", "null", 0, "0") else None

    owner_id = (user.get("id") if user else None) or data.get("owner_id") or "analyst_carla"
    owner_email = (user.get("email") if user else None) or data.get("owner_email") or "carla.mendez@econode.io"
    owner_name = (user.get("display_name") if user else None) or data.get("owner_name") or "Carla Méndez"
    owner_role = (user.get("role") if user else None) or data.get("owner_role") or "analyst"
    owner_org = (user.get("organization") if user else None) or data.get("owner_org") or "Organización Independiente"

    if not name:
        raise ValueError("El nombre del sistema es obligatorio.")
    if not code:
        code = f"SKU-{os.urandom(3).hex().upper()}"

    def _execute(c: sqlite3.Connection):
        return create_product_system(
            c,
            name=name,
            code=code,
            target_amount=target_amount,
            description=description,
            owner_id=owner_id,
            owner_email=owner_email,
            owner_name=owner_name,
            owner_role=owner_role,
            owner_org=owner_org,
            category=category,
            geography=geography,
            project_id=project_id
        )

    if conn is None:
        with get_active_db_connection() as c:
            sys_id = _execute(c)
    else:
        sys_id = _execute(conn)

    return {
        "status": "success",
        "system_id": sys_id,
        "name": name,
        "code": code,
        "target_amount": target_amount,
        "owner_name": owner_name,
        "message": f"Sistema producto '{name}' creado exitosamente."
    }


def import_systems_csv_use_case(
    conn: Optional[sqlite3.Connection] = None,
    csv_content: str = "",
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Importa modelos de sistemas producto desde un CSV (plantilla o SimaPro) asignando la propiedad al usuario activo."""
    if not csv_content.strip():
        raise ValueError("El archivo CSV está vacío.")

    owner_id = (user.get("id") if user else None) or "analyst_carla"
    owner_email = (user.get("email") if user else None) or "carla.mendez@econode.io"
    owner_name = (user.get("display_name") if user else None) or "Carla Méndez"
    owner_role = (user.get("role") if user else None) or "analyst"
    owner_org = (user.get("organization") if user else None) or "Organización Independiente"

    # 1. Detección de formato SimaPro CSV
    is_simapro = (
        "{SimaPro" in csv_content or
        "{processes}" in csv_content or
        "{CSV separator:" in csv_content or
        "Process\n\nCategory type" in csv_content or
        "Process\r\n\r\nCategory type" in csv_content
    )

    if is_simapro:
        header, raw_procs = parse_simapro_csv(csv_content)
        if not raw_procs:
            raise ValueError("No se encontraron procesos válidos en el archivo SimaPro CSV.")

        nodes = []
        total_flows = 0
        for idx, rp in enumerate(raw_procs, start=1):
            n = simapro_process_to_econode_node(rp, idx=idx)
            n["x"] = 80 + (idx - 1) * 360
            n["y"] = 120
            n["pos_x"] = n["x"]
            n["pos_y"] = n["y"]
            total_flows += len(n.get("inputs", [])) + len(n.get("outputs", []))
            nodes.append(n)

        proj_name = header.get("Project") or (nodes[0]["name"] if nodes else "Modelo SimaPro")
        sys_name = f"{proj_name} (SimaPro)" if "(SimaPro)" not in proj_name else proj_name
        sys_code = f"SP-{nodes[0].get('code', os.urandom(3).hex().upper())}"
        cat = nodes[0].get("category", "Material").capitalize()
        geo = nodes[0].get("location", "GLO")
        
        # Buscar flujo de referencia para cantidad funcional
        ref_amt = 1.0
        for out in nodes[0].get("outputs", []):
            if out.get("is_reference"):
                ref_amt = float(out.get("amount", 1.0))
                break

        def _execute_simapro(c: sqlite3.Connection):
            sys_id = create_product_system(
                c,
                name=sys_name,
                code=sys_code,
                target_amount=ref_amt,
                description=f"Importado desde SimaPro CSV ({len(nodes)} proceso(s), {total_flows} flujos LCI)",
                owner_id=owner_id,
                owner_email=owner_email,
                owner_name=owner_name,
                owner_role=owner_role,
                owner_org=owner_org,
                category=cat,
                geography=geo
            )
            # Guardar lienzo con todos los nodos y flujos
            save_system_canvas(c, sys_id, nodes, [])
            return sys_id

        if conn is None:
            with get_active_db_connection() as c:
                created_sys_id = _execute_simapro(c)
        else:
            created_sys_id = _execute_simapro(conn)

        return {
            "status": "success",
            "format": "simapro",
            "imported_count": 1,
            "systems_imported": 1,
            "system_ids": [created_sys_id],
            "systems_created": [created_sys_id],
            "system_id": created_sys_id,
            "processes_count": len(nodes),
            "flows_count": total_flows,
            "message": f"Se importó el modelo SimaPro '{sys_name}' con {len(nodes)} proceso(s) y {total_flows} flujos de inventario LCI."
        }

    # 2. Plantilla CSV estándar
    def _execute_import(c: sqlite3.Connection):
        created_ids = []
        reader = csv.DictReader(io.StringIO(csv_content))
        for idx, row in enumerate(reader, start=1):
            name = row.get("nombre") or row.get("name") or row.get("sistema") or f"Sistema Importado #{idx}"
            capacidad = row.get("capacidad_ml") or "500"
            peso = row.get("peso_envase_g") or "24.0"
            rec = row.get("tasa_reciclaje_pct") or "30.0"
            transp = row.get("distancia_transporte_km") or "100"
            code = f"SKU-IMP-{capacidad}-{idx}"
            desc = f"Parámetros: Capacidad {capacidad}ml, Peso {peso}g, Reciclaje {rec}%, Transporte {transp}km"
            
            sys_id = create_product_system(
                c,
                name=name,
                code=code,
                target_amount=1.0,
                description=desc,
                owner_id=owner_id,
                owner_email=owner_email,
                owner_name=owner_name,
                owner_role=owner_role,
                owner_org=owner_org
            )
            created_ids.append(sys_id)

        if not created_ids:
            sys_id = create_product_system(
                c,
                name="Sistema Importado desde Archivo",
                code=f"SKU-CSV-{os.urandom(3).hex().upper()}",
                target_amount=1.0,
                description="Importado desde texto",
                owner_id=owner_id,
                owner_email=owner_email,
                owner_name=owner_name,
                owner_role=owner_role,
                owner_org=owner_org
            )
            created_ids.append(sys_id)
        return created_ids

    if conn is None:
        with get_active_db_connection() as c:
            created_ids = _execute_import(c)
    else:
        created_ids = _execute_import(conn)

    return {
        "status": "success",
        "format": "template",
        "imported_count": len(created_ids),
        "systems_imported": len(created_ids),
        "system_ids": created_ids,
        "message": f"Se importaron {len(created_ids)} sistemas producto exitosamente desde la plantilla CSV."
    }


def import_simapro_to_system_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1,
    csv_content: str = "",
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Importa uno o varios procesos de SimaPro directamente dentro del lienzo de un sistema existente."""
    if not csv_content.strip():
        raise ValueError("El archivo SimaPro CSV está vacío.")

    header, raw_procs = parse_simapro_csv(csv_content)
    if not raw_procs:
        raise ValueError("No se encontraron procesos válidos en el archivo SimaPro CSV.")

    def _execute(c: sqlite3.Connection):
        details = get_product_system_details(c, system_id)
        existing_nodes = details.get("nodes", []) if details else []
        existing_edges = details.get("edges", []) if details else []

        start_idx = len(existing_nodes) + 1
        new_nodes = []
        total_new_flows = 0

        for i, rp in enumerate(raw_procs, start=start_idx):
            n = simapro_process_to_econode_node(rp, idx=i)
            n["x"] = 120 + ((i - 1) % 4) * 350
            n["y"] = 100 + ((i - 1) // 4) * 260
            n["pos_x"] = n["x"]
            n["pos_y"] = n["y"]
            total_new_flows += len(n.get("inputs", [])) + len(n.get("outputs", []))
            new_nodes.append(n)

        combined_nodes = list(existing_nodes) + new_nodes
        save_system_canvas(c, system_id, combined_nodes, existing_edges)
        return len(new_nodes), total_new_flows

    if conn is None:
        with get_active_db_connection() as c:
            proc_count, flow_count = _execute(c)
    else:
        proc_count, flow_count = _execute(conn)

    return {
        "status": "success",
        "system_id": system_id,
        "added_processes": proc_count,
        "added_flows": flow_count,
        "message": f"Se agregaron {proc_count} proceso(s) de SimaPro con {flow_count} flujos al lienzo actual."
    }


def get_system_canvas_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> Optional[Dict[str, Any]]:
    """Obtiene los nodos y aristas del lienzo para el sistema producto."""
    if conn is None:
        with get_active_db_connection() as c:
            return get_product_system_details(c, system_id)
    return get_product_system_details(conn, system_id)


def save_system_canvas_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1, payload: Optional[Dict[str, Any]] = None):
    """Guarda la posición de los nodos, conexiones y catálogo del lienzo."""
    payload = payload or {}
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    palette = payload.get("palette", None)
    if conn is None:
        with get_active_db_connection() as c:
            save_system_canvas(c, system_id, nodes, edges, palette)
    else:
        save_system_canvas(conn, system_id, nodes, edges, palette)


def delete_product_system_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> bool:
    """Elimina permanentemente un sistema producto y sus dependencias."""
    if conn is None:
        with get_active_db_connection() as c:
            return delete_product_system(c, system_id)
    return delete_product_system(conn, system_id)


def add_system_collaborator_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1,
    collaborator: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Invita o asigna un colaborador al equipo del sistema producto."""
    collaborator = collaborator or {}
    if conn is None:
        with get_active_db_connection() as c:
            return add_system_collaborator(c, system_id, collaborator)
    return add_system_collaborator(conn, system_id, collaborator)



def get_system_parameters_use_case(conn: Optional[Any] = None, system_id: int = 1) -> List[Dict[str, Any]]:
    """Obtiene los parametros definidos para el sistema producto."""
    if conn is None:
        with get_active_db_connection() as c:
            return get_system_parameters(c, system_id)
    return get_system_parameters(conn, system_id)


def save_system_parameter_use_case(
    conn: Optional[Any] = None,
    system_id: int = 1,
    param_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Crea o actualiza un parametro en el sistema producto."""
    param_data = param_data or {}
    if conn is None:
        with get_active_db_connection() as c:
            return save_system_parameter(c, system_id, param_data)
    return save_system_parameter(conn, system_id, param_data)


def delete_system_parameter_use_case(
    conn: Optional[Any] = None,
    system_id: int = 1,
    param_id: str = ""
) -> bool:
    """Elimina un parametro del sistema producto."""
    if conn is None:
        with get_active_db_connection() as c:
            return delete_system_parameter(c, system_id, param_id)
    return delete_system_parameter(conn, system_id, param_id)


# -----------------------------------------------------------------------------
# CASOS DE USO DE PROYECTOS CONTENEDORES Y COMPARATIVA LCIA
# -----------------------------------------------------------------------------

def list_projects_use_case(
    conn: Optional[sqlite3.Connection] = None,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtiene la lista de proyectos registrados para el usuario con conteo de sistemas."""
    if conn is None:
        with get_active_db_connection() as c:
            return list_projects(c, user_email=user_email, user_id=user_id, user_role=user_role)
    return list_projects(conn, user_email=user_email, user_id=user_id, user_role=user_role)


def create_project_use_case(
    conn: Optional[sqlite3.Connection] = None,
    data: Optional[Dict[str, Any]] = None,
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Crea un nuevo proyecto contenedor de sistemas producto."""
    data = data or {}
    name = (data.get("name") or "").strip()
    code = (data.get("code") or "").strip()
    description = (data.get("description") or "").strip()
    category = data.get("category") or "General"

    if not name:
        raise ValueError("El nombre del proyecto es obligatorio.")
    if not code:
        code = f"PRJ-{os.urandom(3).hex().upper()}"

    owner_id = (user.get("id") if user else None) or data.get("owner_id") or "analyst_carla"
    owner_email = (user.get("email") if user else None) or data.get("owner_email") or "carla.mendez@econode.io"
    owner_name = (user.get("display_name") if user else None) or data.get("owner_name") or "Carla Méndez"

    def _execute(c: sqlite3.Connection):
        proj_id = create_project(
            c,
            name=name,
            code=code,
            description=description,
            category=category,
            owner_id=owner_id,
            owner_email=owner_email,
            owner_name=owner_name
        )
        return get_project_by_id(c, proj_id)

    if conn is None:
        with get_active_db_connection() as c:
            proj = _execute(c)
    else:
        proj = _execute(conn)

    return {
        "status": "success",
        "project": proj,
        "message": f"Proyecto '{name}' creado exitosamente."
    }


def delete_project_use_case(
    conn: Optional[sqlite3.Connection] = None,
    project_id: int = 1
) -> bool:
    """Elimina un proyecto y desasocia sus sistemas (quedan como independientes 'solitos')."""
    if conn is None:
        with get_active_db_connection() as c:
            return delete_project(c, project_id)
    return delete_project(conn, project_id)


def assign_system_to_project_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """Asigna o desasocia un sistema producto a un proyecto contenedor."""
    def _execute(c: sqlite3.Connection):
        ok = assign_system_to_project(c, system_id, project_id)
        proj_name = None
        if project_id:
            pr = get_project_by_id(c, project_id)
            if pr:
                proj_name = pr.get("name")
        return ok, proj_name

    if conn is None:
        with get_active_db_connection() as c:
            success, proj_name = _execute(c)
    else:
        success, proj_name = _execute(conn)

    msg = f"Sistema asignado al proyecto '{proj_name}'" if proj_name else "Sistema desasociado (ahora es independiente/solito)"
    return {
        "status": "success" if success else "error",
        "system_id": system_id,
        "project_id": project_id,
        "project_name": proj_name,
        "message": msg
    }


def calculate_system_lcia_scores(
    conn: sqlite3.Connection,
    sys_id: int,
    target_amt: float,
    param_dict: Dict[str, float],
    raw_parameters_json: str
) -> Dict[str, float]:
    """Calcula los puntajes de impacto ambiental ReCiPe 2016 Midpoint (H) específicos de cada sistema."""
    # 1. Verificar si existen resultados completos pre-calculados (ej. SimaPro CSV o archivados en el proyecto)
    details = get_product_system_details(conn, sys_id) or {}
    nodes = details.get("nodes", [])

    base_proj_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidate_dirs = [
        os.path.join(base_proj_dir, "simaproexamples"),
        base_proj_dir
    ]
    for n in nodes:
        node_name = n.get("name") or n.get("label") or ""
        if node_name:
            for c_dir in candidate_dirs:
                csv_path = os.path.join(c_dir, f"{node_name}_RECIPE_2016_RESULTADOS_COMPLETOS.CSV")
                if os.path.exists(csv_path):
                    scores: Dict[str, float] = {}
                    try:
                        with open(csv_path, "r", encoding="utf-8") as f:
                            for line in f:
                                parts = line.strip().split(";")
                                if len(parts) >= 2:
                                    cat_name = parts[0].lower()
                                    try:
                                        val = float(parts[1]) * target_amt
                                        if "climate change" in cat_name or "global warming" in cat_name:
                                            scores["global_warming"] = round(val, 5)
                                        elif "acidification: terrestrial" in cat_name or "acidification" in cat_name:
                                            scores["acidification"] = round(val, 6)
                                        elif "eutrophication: freshwater" in cat_name:
                                            scores["eutrophication"] = round(val, 8)
                                        elif "water use" in cat_name or "water consumption" in cat_name:
                                            scores["water_consumption"] = round(val, 6)
                                        elif "material resources" in cat_name or "energy resources: non-renewable" in cat_name:
                                            scores["resource_scarcity"] = round(val, 6)
                                    except ValueError:
                                        pass
                        if scores and "global_warming" in scores:
                            return scores
                    except Exception:
                        pass

    # 2. Evaluación directa de inventario de ciclo de vida (LCI) de los nodos del lienzo
    gw = 0.0
    ac = 0.0
    eu = 0.0
    wa = 0.0
    rs = 0.0
    has_inventory_flows = False

    for n in nodes:
        # Intercambios de entrada (Tecnosfera y Biosfera)
        for inp in n.get("inputs", []):
            name = (inp.get("name") or "").lower()
            amt = float(inp.get("amount") or 0.0)
            if amt <= 0:
                continue
            has_inventory_flows = True

            # Combustibles y energía fósil
            if "kerosene" in name or "jet fuel" in name:
                gw += amt * 3.05
                ac += amt * 0.0075
                rs += amt * 0.95
            elif "diesel" in name or "gasoil" in name:
                gw += amt * 3.15
                ac += amt * 0.0082
                rs += amt * 0.98
            elif "gasoline" in name or "petrol" in name:
                gw += amt * 3.10
                ac += amt * 0.0078
                rs += amt * 0.96
            elif "natural gas" in name or "gas natural" in name:
                gw += amt * 0.056
                rs += amt * 0.85
            elif "biogas" in name:
                gw += amt * 0.025
                rs += amt * 0.015
            elif "electricity" in name or "electricidad" in name or "cfe" in name:
                factor_cfe = param_dict.get("factor_emision_red_cfe", 0.438)
                gw += amt * factor_cfe
                ac += amt * 0.00085
                eu += amt * 0.00004
                rs += amt * 0.09
            elif "virgin pet" in name or "pet granulate" in name or "resina virgen" in name:
                gw += amt * 2.15
                ac += amt * 0.0045
                rs += amt * 1.15
            elif "recycled pet" in name or "rpet" in name:
                gw += amt * 0.65
                ac += amt * 0.0018
                rs += amt * 0.35
            elif "water" in name or "agua" in name:
                unit_str = str(inp.get("unit", "")).lower()
                wa += amt * (1.0 if "m3" in unit_str else 0.001)
            elif "transport" in name or "freight" in name or "lorry" in name or "truck" in name or "camion" in name:
                gw += amt * 0.095
                ac += amt * 0.00045
                rs += amt * 0.025

        # Intercambios de salida (Emisiones elementales a aire, agua, suelo)
        for out in n.get("outputs", []):
            name = (out.get("name") or "").lower()
            amt = float(out.get("amount") or 0.0)
            if amt <= 0:
                continue
            has_inventory_flows = True

            # Emisiones a aire
            if "fossil co2" in name or ("carbon dioxide" in name and "fossil" in name):
                gw += amt * 1.0
            elif "methane" in name:
                gw += amt * 34.0
            elif "dinitrogen monoxide" in name or "n2o" in name:
                gw += amt * 298.0
            elif "sulfur dioxide" in name or "so2" in name:
                ac += amt * 1.0
            elif "nitrogen oxides" in name or "nox" in name:
                ac += amt * 0.36
            elif "ammonia" in name or "nh3" in name:
                ac += amt * 1.96
            # Emisiones a agua
            elif "phosphate" in name or "phosphorus" in name:
                eu += amt * 0.33

    if has_inventory_flows and gw > 0:
        return {
            "global_warming": round(max(0.00001, gw * target_amt), 5),
            "acidification": round(max(0.000001, ac * target_amt), 6),
            "eutrophication": round(max(0.0000001, eu * target_amt), 7),
            "water_consumption": round(max(0.00001, wa * target_amt), 5),
            "resource_scarcity": round(max(0.00001, rs * target_amt), 5)
        }

    # 3. Fallback paramétrico (para modelos de envases/embalajes con parámetros de proceso)
    peso_g = param_dict.get("peso_envase_g") or (param_dict.get("peso_nominal_botella", 0.0) * 1000.0) or 24.0
    rec_content = (param_dict.get("contenido_reciclado_pct") or param_dict.get("contenido_rpet_pct", 0.0)) / 100.0
    tasa_rec = (param_dict.get("tasa_reciclaje_pct", 0.0)) / 100.0
    dist_km = param_dict.get("distancia_transporte_km") or param_dict.get("distancia_distribucion_km", 100.0)

    peso_kg = (peso_g / 1000.0) * target_amt
    gw_mat = peso_kg * ((1.0 - rec_content) * 2.15 + rec_content * 0.65) * (1.0 - tasa_rec * 0.4)
    gw_trans = peso_kg * (dist_km / 1000.0) * 0.095
    gw_total = max(0.0001, gw_mat + gw_trans)

    return {
        "global_warming": round(gw_total, 5),
        "acidification": round(gw_total * 0.0042, 6),
        "eutrophication": round(gw_total * 0.00085, 6),
        "water_consumption": round(peso_kg * 0.045, 5),
        "resource_scarcity": round(peso_kg * 1.15 * (1.0 - rec_content * 0.7), 5)
    }


def compare_project_systems_use_case(
    conn: Optional[sqlite3.Connection] = None,
    project_id: int = 1
) -> Dict[str, Any]:
    """Realiza la comparación multidimensional de inventario e impacto ambiental (LCIA) entre los sistemas de un proyecto."""
    def _execute(c: sqlite3.Connection):
        proj = get_project_by_id(c, project_id)
        if not proj:
            raise ValueError(f"Proyecto con ID {project_id} no encontrado.")

        rows = c.execute("""
            SELECT s.id, s.name, s.code, s.target_amount, coalesce(s.parameters_json, '{}') as parameters_json,
                   coalesce(s.status, 'draft') as status, coalesce(s.compliance_rate, '0.0%') as compliance_rate,
                   coalesce(s.category, 'Polímeros') as category, coalesce(s.geography, '[MX]') as geography,
                   p.name as reference_process_name, f.unit_symbol as reference_unit,
                   (SELECT count(*) FROM product_system_nodes WHERE system_id = s.id) as nodes_count,
                   (SELECT count(*) FROM product_system_edges WHERE system_id = s.id) as edges_count
            FROM product_systems s
            LEFT JOIN processes p ON s.reference_process_id = p.id
            LEFT JOIN flows f ON p.reference_flow_id = f.id
            WHERE s.project_id = ?
            ORDER BY s.id ASC;
        """, (project_id,)).fetchall()

        systems_data = []
        for r in rows:
            sys_id = r["id"]
            sys_name = r["name"]
            sys_code = r["code"] or f"SYS_{sys_id:04d}"
            target_amt = float(r["target_amount"] or 1.0)
            unit_sym = r["reference_unit"] or "u"
            nodes_cnt = r["nodes_count"]
            edges_cnt = r["edges_count"]

            # Si el recuento relacional es 0, consultar los nodos guardados en parameters_json
            if nodes_cnt == 0:
                try:
                    raw_pj = r["parameters_json"] or "{}"
                    parsed_pj = json.loads(raw_pj) if isinstance(raw_pj, str) else (raw_pj or {})
                    if isinstance(parsed_pj, dict):
                        c_nodes = parsed_pj.get("canvas_nodes") or []
                        if c_nodes:
                            nodes_cnt = len(c_nodes)
                        c_edges = parsed_pj.get("canvas_edges") or []
                        if c_edges:
                            edges_cnt = len(c_edges)
                except Exception:
                    pass

            params = get_system_parameters(c, sys_id)
            param_dict = {p.get("name"): float(p.get("value", 0.0)) for p in params if "name" in p}

            lcia_scores = calculate_system_lcia_scores(
                conn=c,
                sys_id=sys_id,
                target_amt=target_amt,
                param_dict=param_dict,
                raw_parameters_json=r["parameters_json"]
            )

            systems_data.append({
                "id": sys_id,
                "name": sys_name,
                "code": sys_code,
                "status": r["status"],
                "compliance_rate": r["compliance_rate"],
                "target_amount": target_amt,
                "unit": unit_sym,
                "category": r["category"],
                "geography": r["geography"],
                "reference_process_name": r["reference_process_name"] or "Proceso Unitario Principal",
                "nodes_count": nodes_cnt,
                "edges_count": edges_cnt,
                "parameters": params,
                "parameter_values": param_dict,
                "lcia_scores": lcia_scores
            })

        if systems_data:
            gw_vals = [s["lcia_scores"]["global_warming"] for s in systems_data]
            min_gw = min(gw_vals)
            max_gw = max(gw_vals)
            for s in systems_data:
                curr_gw = s["lcia_scores"]["global_warming"]
                s["is_best_carbon"] = (curr_gw == min_gw)
                diff_vs_min_pct = round(((curr_gw - min_gw) / min_gw * 100.0), 1) if min_gw > 0 else 0.0
                s["diff_vs_best_pct"] = diff_vs_min_pct
                if max_gw > min_gw:
                    s["eco_efficiency_score"] = round(max(10.0, 100.0 - ((curr_gw - min_gw) / (max_gw - min_gw) * 50.0)), 1)
                else:
                    s["eco_efficiency_score"] = 100.0

        return {
            "status": "success",
            "project": proj,
            "systems_count": len(systems_data),
            "systems": systems_data,
            "comparison_categories": [
                {"key": "global_warming", "label": "Huella de Carbono (GWP)", "unit": "kg CO2-eq", "description": "Calentamiento Global ReCiPe Midpoint (H)"},
                {"key": "acidification", "label": "Acidificación Terrestre", "unit": "kg SO2-eq", "description": "Impacto de emisiones de SO2 y NOx en suelos"},
                {"key": "eutrophication", "label": "Eutrofización Agua Dulce", "unit": "kg P-eq", "description": "Acumulación de fósforo y nutrientes en cuerpos de agua"},
                {"key": "water_consumption", "label": "Consumo de Agua", "unit": "m3", "description": "Uso neto y agotamiento de recursos hídricos"},
                {"key": "resource_scarcity", "label": "Escasez Fósil", "unit": "kg oil-eq", "description": "Agotamiento de combustibles fósiles y reservas no renovables"}
            ]
        }

    if conn is None:
        with get_active_db_connection() as c:
            return _execute(c)
    return _execute(conn)
