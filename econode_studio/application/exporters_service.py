"""
econode_studio/application/exporters_service.py - Casos de Uso para Exportaciones Industriales
Capa de Aplicación:
Orquesta la generación y validación de expedientes técnicos en estándares abiertos e industriales:
- openLCA Schema v2 (ZIP con JSON-LD)
- ILCD XML (International Reference Life Cycle Data System)
- SimaPro CSV (formato de intercambio industrial)
- Matriz de Balance de Masas y Flujos CSV
- Dossier Digital Completo (ZIP consolidado con hashes criptográficos)
"""

import sqlite3
from typing import Dict, Any, Optional

try:
    from infrastructure import exporters_adapter as _exp_adapter
    from infrastructure.database_adapter import get_active_db_connection
except (ImportError, ValueError):
    from econode_studio.infrastructure import exporters_adapter as _exp_adapter
    from econode_studio.infrastructure.database_adapter import get_active_db_connection


def export_openlca_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> bytes:
    """Genera el paquete ZIP estructurado conforme al esquema oficial openLCA v2."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_openlca_jsonld_zip(c, system_id)
    return _exp_adapter.export_openlca_jsonld_zip(conn, system_id)


def export_ilcd_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> bytes:
    """Genera el archivo ZIP con datasets XML normalizados bajo el estándar ILCD de la Comisión Europea."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_ilcd_xml_zip(c, system_id)
    return _exp_adapter.export_ilcd_xml_zip(conn, system_id)


def export_simapro_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> str:
    """Exporta el modelo en formato CSV de intercambio compatible con SimaPro."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_simapro_csv(c, system_id)
    return _exp_adapter.export_simapro_csv(conn, system_id)


def export_csv_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> str:
    """Genera la sábana tabular CSV de balance de materia, emisiones y consumos."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_lci_consolidated_csv(c, system_id)
    return _exp_adapter.export_lci_consolidated_csv(conn, system_id)


def export_complete_expediente_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> bytes:
    """Genera el expediente completo consolidado (ZIP con todos los estándares, evidencias y sellos)."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_expediente_nom070_zip(c, system_id)
    return _exp_adapter.export_expediente_nom070_zip(conn, system_id)


def export_pdf_use_case(conn: Optional[sqlite3.Connection] = None, system_id: int = 1) -> bytes:
    """Genera el documento PDF oficial formal del Sistema Producto (conforme a ISO 14044 / NOM-070-SE-2024)."""
    if conn is None:
        with get_active_db_connection() as c:
            return _exp_adapter.export_system_pdf_bytes(c, system_id)
    return _exp_adapter.export_system_pdf_bytes(conn, system_id)


# Alias de conveniencia y compatibilidad
export_openlca_jsonld_zip = export_openlca_use_case
export_ilcd_xml_zip = export_ilcd_use_case
export_simapro_csv = export_simapro_use_case
export_lci_consolidated_csv = export_csv_use_case
export_expediente_nom070_zip = export_complete_expediente_use_case
export_nom070_dossier_use_case = export_complete_expediente_use_case
export_system_pdf_bytes = export_pdf_use_case

