"""
econode_studio/application/ghg_service.py - Casos de Uso para Inventarios GHG Protocol y Factores de Emision
Gestiona el ciclo de vida de inventarios corporativos, calculos de doble contabilidad y vinculacion con Sistemas Producto (LCA).
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Importaciones de infraestructura y dominio
try:
    from infrastructure.emission_factors_db import (
        get_ef_db_session, search_emission_factors, get_emission_factor_by_id,
        list_distinct_sources, list_distinct_categories, get_currency_rate
    )
    from infrastructure.database_adapter import get_active_db_connection, get_product_system_details
    from domain.ghg_inventory import GHGInventory, GHGEntry, SCOPE_CATEGORIES
    from application.product_systems import calculate_system_lcia_scores
except (ImportError, ValueError):
    from econode_studio.infrastructure.emission_factors_db import (
        get_ef_db_session, search_emission_factors, get_emission_factor_by_id,
        list_distinct_sources, list_distinct_categories, get_currency_rate
    )
    from econode_studio.infrastructure.database_adapter import get_active_db_connection, get_product_system_details
    from econode_studio.domain.ghg_inventory import GHGInventory, GHGEntry, SCOPE_CATEGORIES
    from econode_studio.application.product_systems import calculate_system_lcia_scores

# --- Casos de Uso de Inventarios ---

def list_inventories_use_case() -> List[Dict[str, Any]]:
    """Retorna la lista de todos los inventarios GHG corporativos registrados con sus totales."""
    with get_ef_db_session() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT id, organization_name, reporting_year, consolidation_approach,
                   country_code, base_year, description, status, created_at, updated_at
            FROM tbl_ghg_inventories
            ORDER BY reporting_year DESC, id DESC;
        """).fetchall()

        inventories = []
        for r in rows:
            inv = get_inventory_by_id_use_case(r["id"])
            if inv:
                summary = inv.get("summary", {})
                inventories.append({
                    "id": r["id"],
                    "organization_name": r["organization_name"],
                    "reporting_year": r["reporting_year"],
                    "consolidation_approach": r["consolidation_approach"],
                    "country_code": r["country_code"],
                    "base_year": r["base_year"],
                    "description": r["description"],
                    "status": r["status"],
                    "entries_count": inv.get("summary", {}).get("entries_count", 0),
                    "scope_1_tco2e": summary.get("scope_1", {}).get("total_tco2e", 0.0),
                    "scope_2_location_tco2e": summary.get("scope_2", {}).get("location_based_tco2e", 0.0),
                    "scope_2_market_tco2e": summary.get("scope_2", {}).get("market_based_tco2e", 0.0),
                    "scope_3_tco2e": summary.get("scope_3", {}).get("total_tco2e", 0.0),
                    "total_location_based_tco2e": summary.get("totals", {}).get("total_location_based_tco2e", 0.0),
                    "total_market_based_tco2e": summary.get("totals", {}).get("total_market_based_tco2e", 0.0),
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"]
                })
        return inventories

def get_inventory_by_id_use_case(inventory_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene el inventario completo, sus entradas y el resumen contable."""
    with get_ef_db_session() as conn:
        inv_row = conn.execute("SELECT * FROM tbl_ghg_inventories WHERE id = ?;", (inventory_id,)).fetchone()
        if not inv_row:
            return None

        entry_rows = conn.execute("""
            SELECT * FROM tbl_ghg_entries
            WHERE inventory_id = ?
            ORDER BY scope ASC, scope_category ASC, id ASC;
        """, (inventory_id,)).fetchall()

        entries = []
        for er in entry_rows:
            entry = GHGEntry(
                id=er["id"],
                inventory_id=er["inventory_id"],
                scope=er["scope"],
                scope_category=er["scope_category"],
                activity_name=er["activity_name"],
                calculation_type=er["calculation_type"],
                activity_amount=float(er["activity_amount"]),
                activity_unit=er["activity_unit"],
                currency=er["currency"],
                emission_factor_id=er["emission_factor_id"],
                emission_factor_value=float(er["emission_factor_value"]),
                emission_factor_unit=er["emission_factor_unit"],
                emission_factor_source=er["emission_factor_source"],
                product_system_id=er["product_system_id"],
                contractual_instrument=er["contractual_instrument"],
                emissions_kgco2e=float(er["emissions_kgco2e"]),
                emissions_tco2e=float(er["emissions_tco2e"]),
                data_quality_tier=er["data_quality_tier"],
                notes=er["notes"] or "",
                created_at=er["created_at"]
            )
            entries.append(entry)

        domain_inv = GHGInventory(
            id=inv_row["id"],
            organization_name=inv_row["organization_name"],
            reporting_year=inv_row["reporting_year"],
            consolidation_approach=inv_row["consolidation_approach"],
            country_code=inv_row["country_code"],
            base_year=inv_row["base_year"],
            description=inv_row["description"] or "",
            status=inv_row["status"] or "draft",
            entries=entries,
            created_at=inv_row["created_at"],
            updated_at=inv_row["updated_at"]
        )
        return domain_inv.to_dict()

def create_inventory_use_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuevo inventario corporativo bajo GHG Protocol."""
    org_name = (data.get("organization_name") or "Empresa / Corporativo").strip()
    reporting_year = int(data.get("reporting_year") or 2024)
    consolidation = data.get("consolidation_approach") or "operational_control"
    country_code = (data.get("country_code") or "MX").upper()
    base_year = int(data.get("base_year")) if data.get("base_year") else reporting_year
    description = (data.get("description") or "").strip()

    with get_ef_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tbl_ghg_inventories (
                organization_name, reporting_year, consolidation_approach,
                country_code, base_year, description, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'draft');
        """, (org_name, reporting_year, consolidation, country_code, base_year, description))
        conn.commit()
        new_id = cursor.lastrowid
        return get_inventory_by_id_use_case(new_id)

def delete_inventory_use_case(inventory_id: int) -> bool:
    """Elimina un inventario corporativo y todas sus entradas en cascada."""
    with get_ef_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tbl_ghg_entries WHERE inventory_id = ?;", (inventory_id,))
        cursor.execute("DELETE FROM tbl_ghg_inventories WHERE id = ?;", (inventory_id,))
        conn.commit()
        return cursor.rowcount > 0

# --- Casos de Uso de Entradas de Emision ---

def add_entry_to_inventory_use_case(inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega una fuente de emision calculada a un inventario.
    Soporta:
    1. Datos de actividad estandar x Factor de Emision.
    2. Spend-Based en divisas (MXN/EUR/USD) convertido a USD con factores USEEIO.
    3. Vinculacion con Sistemas Producto del Lienzo LCA (Scope 3 Cat 1 / EPD).
    """
    inv = get_inventory_by_id_use_case(inventory_id)
    if not inv:
        raise ValueError(f"Inventario con ID {inventory_id} no encontrado.")

    reporting_year = inv["reporting_year"]
    scope_category = data.get("scope_category") or "stationary_combustion"
    cat_meta = SCOPE_CATEGORIES.get(scope_category, {})
    scope = cat_meta.get("scope") or data.get("scope") or "SCOPE_1"

    activity_name = (data.get("activity_name") or cat_meta.get("name_es") or "Actividad").strip()
    calc_type = data.get("calculation_type") or "activity_based"
    activity_amount = float(data.get("activity_amount") or 0.0)
    activity_unit = (data.get("activity_unit") or "kg").strip()
    currency = (data.get("currency") or "USD").upper()
    ef_id = data.get("emission_factor_id")
    ef_val = float(data.get("emission_factor_value") or 0.0)
    ef_unit = data.get("emission_factor_unit") or f"kg CO2e / {activity_unit}"
    ef_source = data.get("emission_factor_source") or "Manual / Usuario"
    ps_id = data.get("product_system_id")
    contractual_inst = data.get("contractual_instrument")
    tier = data.get("data_quality_tier") or "Tier 2"
    notes = data.get("notes") or ""

    # Caso A: Si el usuario selecciono un factor del catalogo universal
    if ef_id and ef_val == 0.0:
        ef_info = get_emission_factor_by_id(int(ef_id))
        if ef_info:
            ef_val = float(ef_info["gwp_factor_value"])
            ef_unit = f"kg CO2e / {ef_info['activity_unit']}"
            ef_source = ef_info["source_database"]

    # Caso B: Si esta vinculado a un Sistema Producto del Lienzo LCA (Scope 3 Cat 1 / Cradle-to-Gate)
    if ps_id:
        try:
            with get_active_db_connection() as c_tier1:
                ps_details = get_product_system_details(c_tier1, int(ps_id))
                if ps_details:
                    target_amt = float(ps_details.get("target_amount") or 1.0)
                    scores = calculate_system_lcia_scores(
                        conn=c_tier1,
                        sys_id=int(ps_id),
                        target_amt=target_amt,
                        param_dict={},
                        raw_parameters_json="{}"
                    )
                    # GWP unitario por unidad funcional del sistema producto
                    gwp_total = scores.get("global_warming", 0.0)
                    ef_val = gwp_total / max(target_amt, 0.001)
                    ef_unit = f"kg CO2e / {ps_details.get('unit') or 'u'}"
                    ef_source = f"ECONODE LCA Studio (Sistema Producto: {ps_details.get('name')})"
                    calc_type = "product_system_lca"
                    tier = "Tier 1"
        except Exception:
            pass

    # Calculo de emisiones
    if calc_type == "spend_based":
        # Obtener tasa de cambio para convertir a USD si el factor esta en USD
        rate_to_usd = get_currency_rate(base_currency=currency, target_currency="USD", year=reporting_year)
        amount_usd = activity_amount * rate_to_usd
        emissions_kg = amount_usd * ef_val
        notes = f"{notes} [Conversion: {activity_amount} {currency} = {amount_usd:.2f} USD (Tasa: {rate_to_usd:.4f})]".strip()
    else:
        emissions_kg = activity_amount * ef_val

    emissions_t = emissions_kg / 1000.0

    with get_ef_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tbl_ghg_entries (
                inventory_id, scope, scope_category, activity_name, calculation_type,
                activity_amount, activity_unit, currency, emission_factor_id,
                emission_factor_value, emission_factor_unit, emission_factor_source,
                product_system_id, contractual_instrument, emissions_kgco2e, emissions_tco2e,
                data_quality_tier, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            inventory_id, scope, scope_category, activity_name, calc_type,
            activity_amount, activity_unit, currency, ef_id,
            ef_val, ef_unit, ef_source, ps_id, contractual_inst,
            emissions_kg, emissions_t, tier, notes
        ))
        conn.commit()
        new_entry_id = cursor.lastrowid

    return get_inventory_by_id_use_case(inventory_id)

def delete_entry_from_inventory_use_case(inventory_id: int, entry_id: int) -> Dict[str, Any]:
    """Elimina una entrada de emision del inventario."""
    with get_ef_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tbl_ghg_entries WHERE id = ? AND inventory_id = ?;", (entry_id, inventory_id))
        conn.commit()
    return get_inventory_by_id_use_case(inventory_id)

def get_scope_taxonomy_use_case() -> Dict[str, Any]:
    """Retorna la taxonomia completa de categorias y alcances de GHG Protocol para la UI."""
    return SCOPE_CATEGORIES
