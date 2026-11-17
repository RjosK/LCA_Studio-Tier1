"""
econode_studio/infrastructure/emission_factors_db.py - Base de Datos Desacoplada de Factores de Emision y GHG Protocol
Gestiona la persistencia en SQLite de factores de emision (DEFRA, EPA, CRE, ADEME, USEEIO)
e inventarios de Gases de Efecto Invernadero bajo el estandar GHG Protocol.
"""

import sqlite3
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

# Ruta por defecto de la base de datos de factores de emision
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EF_DB_PATH = DATA_DIR / "econode_emission_factors.db"

def get_resolved_db_path() -> Path:
    """Resuelve la ruta de la base de datos adaptandose a Vercel Serverless (/tmp con permisos de escritura)."""
    if os.environ.get("VERCEL") or not os.access(DATA_DIR, os.W_OK):
        tmp_path = Path("/tmp") / "econode_emission_factors.db"
        if not tmp_path.exists() and EF_DB_PATH.exists():
            import shutil
            try:
                shutil.copy2(EF_DB_PATH, tmp_path)
            except Exception:
                pass
        return tmp_path
    return EF_DB_PATH

def get_ef_db_connection() -> sqlite3.Connection:
    """Crea y retorna una conexion con timeout y soporte para diccionarios (sqlite3.Row)."""
    target = get_resolved_db_path()
    conn = sqlite3.connect(str(target), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        pass
    return conn

@contextmanager
def get_ef_db_session():
    """Context manager que asegura el cierre de la conexion y commit de transacciones."""
    conn = get_ef_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_emission_factors_db() -> None:
    """Crea las tablas e indices requeridos para factores de emision e inventarios GHG."""
    with get_ef_db_session() as conn:
        cursor = conn.cursor()

        # 1. Tabla de Factores de Emision Universales (GWP)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_emission_factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_database TEXT NOT NULL,       -- 'DEFRA_2024', 'EPA_2024', 'CRE_2024', 'ADEME_2024', 'USEEIO_2'
                scope_applicability TEXT NOT NULL,   -- 'SCOPE_1', 'SCOPE_2', 'SCOPE_3_CAT_1', 'SCOPE_3_CAT_4', 'ALL', etc.
                activity_category TEXT NOT NULL,     -- 'Stationary Combustion', 'Electricity Grid', 'Freight Transport'
                factor_name TEXT NOT NULL,           -- 'Diesel (100% mineral)', 'Grid Electricity - Mexico SEN'
                activity_unit TEXT NOT NULL,         -- 'litres', 'kWh', 'ton.km', 'USD', 'kg'
                gwp_factor_value REAL NOT NULL,      -- kg CO2e por unidad
                co2_factor REAL,                     -- kg CO2 por unidad
                ch4_factor REAL,                     -- kg CH4 por unidad (en kg CO2e)
                n2o_factor REAL,                     -- kg N2O por unidad (en kg CO2e)
                geographic_scope TEXT NOT NULL,      -- 'GLO', 'MX', 'US', 'GB', 'EU'
                valid_year INTEGER NOT NULL,         -- 2024
                gwp_standard TEXT DEFAULT 'AR5',     -- 'AR4', 'AR5', 'AR6' (GWP100)
                uncertainty_pct REAL DEFAULT 5.0,    -- % incertidumbre
                metadata_json TEXT                   -- Detalles adicionales, formulas, URLs
            );
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ef_lookup ON tbl_emission_factors (source_database, scope_applicability);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ef_cat ON tbl_emission_factors (activity_category, geographic_scope);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ef_name ON tbl_emission_factors (factor_name);")

        # 2. Tabla de Tipos de Cambio para Calculos Spend-Based
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_currency_rates (
                base_currency TEXT NOT NULL,         -- 'USD'
                target_currency TEXT NOT NULL,       -- 'MXN', 'EUR', 'GBP'
                rate REAL NOT NULL,                  -- 1 USD = X target_currency
                reporting_year INTEGER NOT NULL,     -- 2024
                PRIMARY KEY (base_currency, target_currency, reporting_year)
            );
        """)

        # 3. Tabla de Inventarios Corporativos GHG Protocol
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_ghg_inventories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_name TEXT NOT NULL,
                reporting_year INTEGER NOT NULL,
                consolidation_approach TEXT NOT NULL, -- 'operational_control', 'financial_control', 'equity_share'
                country_code TEXT DEFAULT 'MX',
                base_year INTEGER,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',          -- 'draft', 'in_review', 'audited', 'reported'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Tabla de Registros de Emision por Alcance (Scope 1, 2, 3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_ghg_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER NOT NULL,
                scope TEXT NOT NULL,                 -- 'SCOPE_1', 'SCOPE_2', 'SCOPE_3'
                scope_category TEXT NOT NULL,        -- 'stationary_combustion', 'mobile_combustion', 'electricity_location', 'cat_1_purchased_goods', etc.
                activity_name TEXT NOT NULL,         -- 'Caldera Principal 1', 'Flotilla de Distribucion'
                calculation_type TEXT NOT NULL,      -- 'activity_based', 'spend_based', 'supplier_specific', 'product_system_lca'
                activity_amount REAL NOT NULL,
                activity_unit TEXT NOT NULL,
                currency TEXT,                       -- 'USD', 'MXN', 'EUR' para spend-based
                emission_factor_id INTEGER,          -- FK a tbl_emission_factors si aplica
                emission_factor_value REAL NOT NULL, -- kg CO2e / unidad
                emission_factor_unit TEXT NOT NULL,
                emission_factor_source TEXT NOT NULL,
                product_system_id INTEGER,           -- Referencia al canvas Tier 1 si aplica
                contractual_instrument TEXT,         -- Para Scope 2 market-based: 'i_rec', 'cel', 'ppa'
                emissions_kgco2e REAL NOT NULL,
                emissions_tco2e REAL NOT NULL,
                data_quality_tier TEXT DEFAULT 'Tier 2', -- 'Tier 1', 'Tier 2', 'Tier 3'
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_id) REFERENCES tbl_ghg_inventories (id) ON DELETE CASCADE
            );
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ghg_entry_inv ON tbl_ghg_entries (inventory_id, scope);")
        conn.commit()

# --- Funciones de Consulta de Factores de Emision ---

def search_emission_factors(
    query: Optional[str] = None,
    scope: Optional[str] = None,
    source: Optional[str] = None,
    geo: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Busca factores de emision con filtros por alcance, fuente, geografia y termino de busqueda."""
    with get_ef_db_session() as conn:
        conditions = []
        params = []

        if query:
            conditions.append("(factor_name LIKE ? OR activity_category LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if scope and scope.upper() != "ALL":
            conditions.append("(scope_applicability = ? OR scope_applicability = 'ALL')")
            params.append(scope.upper())

        if source and source.upper() != "ALL":
            conditions.append("source_database = ?")
            params.append(source)

        if geo and geo.upper() != "ALL":
            conditions.append("(geographic_scope = ? OR geographic_scope = 'GLO')")
            params.append(geo)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Contar total
        count_query = f"SELECT COUNT(*) FROM tbl_emission_factors {where_clause};"
        total_count = conn.execute(count_query, params).fetchone()[0]

        # Obtener pagina
        data_query = f"""
            SELECT * FROM tbl_emission_factors
            {where_clause}
            ORDER BY activity_category ASC, factor_name ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(data_query, params + [limit, offset]).fetchall()
        return [dict(r) for r in rows], total_count

def get_emission_factor_by_id(factor_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un factor de emision por su ID primario."""
    with get_ef_db_session() as conn:
        row = conn.execute("SELECT * FROM tbl_emission_factors WHERE id = ?;", (factor_id,)).fetchone()
        return dict(row) if row else None

def list_distinct_sources() -> List[str]:
    """Retorna la lista de fuentes o bases de datos disponibles."""
    with get_ef_db_session() as conn:
        rows = conn.execute("SELECT DISTINCT source_database FROM tbl_emission_factors ORDER BY source_database ASC;").fetchall()
        return [r[0] for r in rows]

def list_distinct_categories(scope: Optional[str] = None) -> List[str]:
    """Retorna las categorias de actividad registradas."""
    with get_ef_db_session() as conn:
        if scope and scope.upper() != "ALL":
            rows = conn.execute(
                "SELECT DISTINCT activity_category FROM tbl_emission_factors WHERE scope_applicability = ? OR scope_applicability = 'ALL' ORDER BY activity_category ASC;",
                (scope.upper(),)
            ).fetchall()
        else:
            rows = conn.execute("SELECT DISTINCT activity_category FROM tbl_emission_factors ORDER BY activity_category ASC;").fetchall()
        return [r[0] for r in rows]

# --- Conversion de Divisas para Spend-Based ---

def get_currency_rate(base_currency: str, target_currency: str, year: int = 2024) -> float:
    """Retorna la tasa de conversion entre divisas para el anio de reporte dado."""
    if base_currency == target_currency:
        return 1.0
    with get_ef_db_session() as conn:
        row = conn.execute(
            "SELECT rate FROM tbl_currency_rates WHERE base_currency = ? AND target_currency = ? AND reporting_year = ?;",
            (base_currency.upper(), target_currency.upper(), year)
        ).fetchone()
        if row:
            return float(row["rate"])
        # Intentar tasa inversa
        rev_row = conn.execute(
            "SELECT rate FROM tbl_currency_rates WHERE base_currency = ? AND target_currency = ? AND reporting_year = ?;",
            (target_currency.upper(), base_currency.upper(), year)
        ).fetchone()
        if rev_row and rev_row["rate"] > 0:
            return 1.0 / float(rev_row["rate"])
    # Tasas de respaldo 2024
    fallback_rates = {
        ("USD", "MXN"): 20.20,
        ("MXN", "USD"): 0.0495,
        ("USD", "EUR"): 0.95,
        ("EUR", "USD"): 1.052,
        ("EUR", "MXN"): 21.26,
        ("MXN", "EUR"): 0.047
    }
    return fallback_rates.get((base_currency.upper(), target_currency.upper()), 1.0)
