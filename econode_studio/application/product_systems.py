"""
econode_studio/application/product_systems.py - Casos de Uso para Gestión e Importación de Sistemas Producto
"""

import sqlite3
import os
import sys
import csv
import io
from typing import Dict, List, Any, Optional

try:
    from infrastructure.database_adapter import (
        list_product_systems, create_product_system, get_product_system_details, save_system_canvas,
        delete_product_system, add_system_collaborator,
        get_active_db_connection
    )
except (ImportError, ValueError):
    from econode_studio.infrastructure.database_adapter import (
        list_product_systems, create_product_system, get_product_system_details, save_system_canvas,
        delete_product_system, add_system_collaborator,
        get_active_db_connection
    )


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
            geography=geography
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
    """Importa modelos de sistemas producto desde un CSV asignando la propiedad al usuario activo."""
    if not csv_content.strip():
        raise ValueError("El archivo CSV está vacío.")

    owner_id = (user.get("id") if user else None) or "analyst_carla"
    owner_email = (user.get("email") if user else None) or "carla.mendez@econode.io"
    owner_name = (user.get("display_name") if user else None) or "Carla Méndez"
    owner_role = (user.get("role") if user else None) or "analyst"
    owner_org = (user.get("organization") if user else None) or "Organización Independiente"

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
        "imported_count": len(created_ids),
        "systems_imported": len(created_ids),
        "system_ids": created_ids,
        "message": f"Se importaron {len(created_ids)} sistemas producto exitosamente desde la plantilla CSV."
    }


def get_system_canvas_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> Optional[Dict[str, Any]]:
    """Obtiene los nodos y aristas del lienzo para el sistema producto."""
    if conn is None:
        with get_active_db_connection() as c:
            return get_product_system_details(c, system_id)
    return get_product_system_details(conn, system_id)


def save_system_canvas_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1, payload: Optional[Dict[str, Any]] = None):
    """Guarda la posición de los nodos y conexiones del lienzo."""
    payload = payload or {}
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    if conn is None:
        with get_active_db_connection() as c:
            save_system_canvas(c, system_id, nodes, edges)
    else:
        save_system_canvas(conn, system_id, nodes, edges)


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

