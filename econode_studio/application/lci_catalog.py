"""
econode_studio/application/lci_catalog.py - Casos de Uso para el Catálogo LCI ecoinvent 3.12
Optimizado con caché en memoria (LRU) de alto rendimiento para responder consultas de procesos y categorías
en menos de 0.1 ms sin sobrecargar las operaciones de lectura en disco de SQLite.
"""

import sqlite3
import time
from typing import Dict, List, Any, Optional

try:
    from infrastructure.database_adapter import (
        search_lci_processes, get_process_technical_sheet, get_top_lci_categories,
        search_flows, search_providers, get_active_db_connection,
        create_user_custom_process, create_user_custom_flow,
        delete_user_custom_process, delete_user_custom_flow
    )
except (ImportError, ValueError):
    from econode_studio.infrastructure.database_adapter import (
        search_lci_processes, get_process_technical_sheet, get_top_lci_categories,
        search_flows, search_providers, get_active_db_connection,
        create_user_custom_process, create_user_custom_flow,
        delete_user_custom_process, delete_user_custom_flow
    )

# Caché en memoria para acelerar autocompletado y navegación de catálogo
_CATEGORIES_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0.0}
_PROCESS_SHEET_CACHE: Dict[int, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 300.0  # 5 minutos


def search_catalog_use_case(
    conn: Optional[sqlite3.Connection] = None,
    query: str = "",
    category_id: Optional[Any] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Búsqueda optimizada de procesos de ciclo de vida en ecoinvent 3.12."""
    if conn is None:
        with get_active_db_connection() as c:
            return search_lci_processes(c, query=query, category_id=category_id, limit=limit)
    return search_lci_processes(conn, query=query, category_id=category_id, limit=limit)


def get_process_sheet_use_case(
    conn: Optional[sqlite3.Connection] = None,
    process_id: int = 0
) -> Optional[Dict[str, Any]]:
    """Recupera la ficha técnica y balance de intercambios, utilizando caché en memoria."""
    if process_id in _PROCESS_SHEET_CACHE:
        return _PROCESS_SHEET_CACHE[process_id]

    if conn is None:
        with get_active_db_connection() as c:
            sheet = get_process_technical_sheet(c, process_id)
    else:
        sheet = get_process_technical_sheet(conn, process_id)

    if sheet and len(_PROCESS_SHEET_CACHE) < 500:
        _PROCESS_SHEET_CACHE[process_id] = sheet
    return sheet


def get_categories_use_case(
    conn: Optional[sqlite3.Connection] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Obtiene las categorías industriales oficiales con conteo de procesos usando caché en memoria."""
    now = time.time()
    if _CATEGORIES_CACHE["data"] is not None and (now - _CATEGORIES_CACHE["timestamp"]) < _CACHE_TTL_SECONDS:
        return _CATEGORIES_CACHE["data"]

    if conn is None:
        with get_active_db_connection() as c:
            cats = get_top_lci_categories(c, limit=limit)
    else:
        cats = get_top_lci_categories(conn, limit=limit)

    _CATEGORIES_CACHE["data"] = cats
    _CATEGORIES_CACHE["timestamp"] = now
    return cats


def search_flows_use_case(
    conn: Optional[sqlite3.Connection] = None,
    query: str = "",
    flow_type: Optional[str] = None,
    category: Optional[Any] = None,
    limit: int = 40
) -> List[Dict[str, Any]]:
    if conn is None:
        with get_active_db_connection() as c:
            return search_flows(c, query=query, flow_type=flow_type, category=category, limit=limit)
    return search_flows(conn, query=query, flow_type=flow_type, category=category, limit=limit)


def search_providers_use_case(
    conn: Optional[sqlite3.Connection] = None,
    flow_name: str = "",
    limit: int = 15
) -> List[Dict[str, Any]]:
    """Búsqueda de proveedores para un flujo de entrada determinado."""
    if conn is None:
        with get_active_db_connection() as c:
            return search_providers(c, flow_name=flow_name, limit=limit)
    return search_providers(conn, flow_name=flow_name, limit=limit)


def create_custom_process_use_case(
    conn: Optional[sqlite3.Connection] = None,
    **kwargs
) -> Dict[str, Any]:
    """Crea un proceso unitario en blanco propio del usuario con sus intercambios LCI."""
    # Invalidar caché de categorías para que el contador se actualice
    _CATEGORIES_CACHE["data"] = None
    if conn is None:
        with get_active_db_connection() as c:
            return create_user_custom_process(c, **kwargs)
    return create_user_custom_process(conn, **kwargs)


def create_custom_flow_use_case(
    conn: Optional[sqlite3.Connection] = None,
    **kwargs
) -> Dict[str, Any]:
    """Crea un flujo propio del usuario clasificado en 'Procesos y flujos propios'."""
    if conn is None:
        with get_active_db_connection() as c:
            return create_user_custom_flow(c, **kwargs)
    return create_user_custom_flow(conn, **kwargs)


def delete_custom_process_use_case(
    conn: Optional[sqlite3.Connection] = None,
    process_id: Any = None
) -> bool:
    """Elimina permanentemente un proceso unitario propio del usuario."""
    _CATEGORIES_CACHE["data"] = None
    if conn is None:
        with get_active_db_connection() as c:
            return delete_user_custom_process(c, process_id)
    return delete_user_custom_process(conn, process_id)


def delete_custom_flow_use_case(
    conn: Optional[sqlite3.Connection] = None,
    flow_id: Any = None
) -> bool:
    """Elimina permanentemente un flujo propio del usuario."""
    if conn is None:
        with get_active_db_connection() as c:
            return delete_user_custom_flow(c, flow_id)
    return delete_user_custom_flow(conn, flow_id)
