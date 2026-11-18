"""
supabase/migrate_ecoinvent_311.py
Migracion automatizada del catalogo ligero de ecoinvent 3.11 Cutoff Unit
(25,412 procesos y 14,051 flujos) a Supabase PostgreSQL.

Uso:
    python supabase/migrate_ecoinvent_311.py
    python supabase/migrate_ecoinvent_311.py "postgresql://..."
"""

import os
import sys
import time
import sqlite3

# Ajustar sys.path para importar config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from econode_studio.config import settings
except ImportError:
    settings = None

import psycopg2
import psycopg2.extras

DEFAULT_URL = "postgresql://postgres.nttdfdsntwlbeqwtgnci:47Tw4W-v8Z7rkqe@aws-1-us-west-2.pooler.supabase.com:6543/postgres"

def run_migration():
    db_url = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        db_url = sys.argv[1].strip()
    elif settings and getattr(settings, "DATABASE_URL", None):
        db_url = settings.DATABASE_URL
    else:
        db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or DEFAULT_URL

    sqlite_path = os.path.join(BASE_DIR, "ecoinvent", "ecoinvent_311.db")
    if not os.path.exists(sqlite_path):
        alt_path = os.path.join(os.path.dirname(BASE_DIR), "ECONODE_TIER2", "ecoinvent", "ecoinvent_311.db")
        if os.path.exists(alt_path):
            sqlite_path = alt_path
        else:
            print(f"[ERROR] No se encontro ecoinvent_311.db en {sqlite_path}")
            sys.exit(1)

    print("=" * 70)
    print("ECONODE STUDIO -> MIGRACION DE ECOINVENT 3.11 A SUPABASE POSTGRESQL")
    print("=" * 70)
    print(f"Ruta SQLite local: {sqlite_path}")

    # 1. Conexion a SQLite Local
    conn_sq = sqlite3.connect(sqlite_path)
    cur_sq = conn_sq.cursor()

    # 2. Conexion a Supabase PostgreSQL
    print("Conectando a Supabase PostgreSQL...")
    conn_pg = psycopg2.connect(db_url)
    conn_pg.autocommit = True
    cur_pg = conn_pg.cursor()
    print("[OK] Conexion con Supabase establecida exitosamente.")

    # 3. Crear esquema DDL para ecoinvent 3.11 con tipos TEXT flexibles
    print("\n[Paso 1/3] Creando tablas e indices de alta velocidad para ecoinvent 3.11...")
    cur_pg.execute("""
        CREATE TABLE IF NOT EXISTS lci_processes_311 (
            id BIGINT PRIMARY KEY,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER,
            category_name TEXT,
            location TEXT DEFAULT 'GLO',
            reference_flow_id TEXT,
            reference_flow_name TEXT,
            reference_amount NUMERIC DEFAULT 1.0,
            reference_unit TEXT DEFAULT 'kg',
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        ALTER TABLE lci_processes_311 ALTER COLUMN location TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN reference_unit TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN code TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN name TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN category_name TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN reference_flow_id TYPE TEXT;
        ALTER TABLE lci_processes_311 ALTER COLUMN reference_flow_name TYPE TEXT;

        CREATE INDEX IF NOT EXISTS idx_lci_proc_311_name_loc ON lci_processes_311 (name, location);
        CREATE INDEX IF NOT EXISTS idx_lci_proc_311_code ON lci_processes_311 (code);
        CREATE INDEX IF NOT EXISTS idx_lci_proc_311_name ON lci_processes_311 (name);
        CREATE INDEX IF NOT EXISTS idx_lci_proc_311_cat ON lci_processes_311 (category_name);

        CREATE TABLE IF NOT EXISTS lci_flows_311 (
            id TEXT PRIMARY KEY,
            code TEXT,
            name TEXT NOT NULL,
            flow_type TEXT DEFAULT 'PRODUCT_FLOW',
            category_name TEXT,
            unit_symbol TEXT DEFAULT 'kg',
            description TEXT
        );

        ALTER TABLE lci_flows_311 ALTER COLUMN id TYPE TEXT;
        ALTER TABLE lci_flows_311 ALTER COLUMN code TYPE TEXT;
        ALTER TABLE lci_flows_311 ALTER COLUMN name TYPE TEXT;
        ALTER TABLE lci_flows_311 ALTER COLUMN flow_type TYPE TEXT;
        ALTER TABLE lci_flows_311 ALTER COLUMN category_name TYPE TEXT;
        ALTER TABLE lci_flows_311 ALTER COLUMN unit_symbol TYPE TEXT;

        CREATE INDEX IF NOT EXISTS idx_lci_flows_311_name ON lci_flows_311 (name);
        CREATE INDEX IF NOT EXISTS idx_lci_flows_311_code ON lci_flows_311 (code);
    """)
    print("[OK] Tablas e indices creados en Supabase.")

    # 4. Truncar tablas para garantizar idempotencia
    cur_pg.execute("TRUNCATE TABLE lci_processes_311, lci_flows_311;")

    # 5. Importar Flujos (14,051 registros)
    print("\n[Paso 2/3] Extrayendo e importando flujos elementales y de producto (flows)...")
    t0 = time.time()
    cur_sq.execute("""
        SELECT 
            id,
            code,
            name,
            flow_type,
            coalesce(category_name, 'General'),
            coalesce(unit_symbol, 'kg'),
            coalesce(description, '')
        FROM flows;
    """)
    flow_rows = cur_sq.fetchall()
    print(f"Extraidos {len(flow_rows):,} flujos desde SQLite.")

    insert_flow_sql = """
        INSERT INTO lci_flows_311 (id, code, name, flow_type, category_name, unit_symbol, description)
        VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """
    batch_size = 2500
    for i in range(0, len(flow_rows), batch_size):
        batch = flow_rows[i:i + batch_size]
        psycopg2.extras.execute_values(cur_pg, insert_flow_sql, batch)
    print(f"[OK] {len(flow_rows):,} flujos importados en {time.time() - t0:.2f}s.")

    # 6. Importar Procesos (25,412 registros)
    print("\n[Paso 3/3] Extrayendo e importando catalogo unitario de procesos (processes)...")
    t0 = time.time()
    cur_sq.execute("""
        SELECT 
            p.id,
            p.code,
            p.name,
            p.category_id,
            coalesce(c.name, 'General') as category_name,
            coalesce(p.location, 'GLO') as location,
            coalesce(p.reference_flow_id, '') as reference_flow_id,
            coalesce(f.name, p.name) as reference_flow_name,
            coalesce(p.reference_amount, 1.0) as reference_amount,
            coalesce(f.unit_symbol, 'kg') as reference_unit,
            coalesce(p.description, '') as description
        FROM processes p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id;
    """)
    proc_rows = cur_sq.fetchall()
    print(f"Extraidos {len(proc_rows):,} procesos desde SQLite.")

    insert_proc_sql = """
        INSERT INTO lci_processes_311 (
            id, code, name, category_id, category_name, location,
            reference_flow_id, reference_flow_name, reference_amount, reference_unit, description
        )
        VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """
    for i in range(0, len(proc_rows), batch_size):
        batch = proc_rows[i:i + batch_size]
        psycopg2.extras.execute_values(cur_pg, insert_proc_sql, batch)
    print(f"[OK] {len(proc_rows):,} procesos importados en {time.time() - t0:.2f}s.")

    # 7. Verificacion de Conteos en Supabase
    print("\n" + "=" * 70)
    print("VERIFICACION DE REGISTROS EN SUPABASE POSTGRESQL:")
    print("=" * 70)
    cur_pg.execute("SELECT count(*) FROM lci_processes_311;")
    pg_proc_count = cur_pg.fetchone()[0]
    cur_pg.execute("SELECT count(*) FROM lci_flows_311;")
    pg_flow_count = cur_pg.fetchone()[0]

    cur_pg.execute("SELECT count(*) FROM lci_processes;")
    pg_proc_312_count = cur_pg.fetchone()[0]

    print(f"  * ecoinvent 3.12 (lci_processes):     {pg_proc_312_count:,} procesos activos")
    print(f"  * ecoinvent 3.11 (lci_processes_311): {pg_proc_count:,} procesos cargados")
    print(f"  * ecoinvent 3.11 (lci_flows_311):     {pg_flow_count:,} flujos cargados")

    assert pg_proc_count == len(proc_rows), f"Discrepancia en conteo de procesos: {pg_proc_count} != {len(proc_rows)}"
    assert pg_flow_count == len(flow_rows), f"Discrepancia en conteo de flujos: {pg_flow_count} != {len(flow_rows)}"

    # Muestra de consulta de prueba
    cur_pg.execute("SELECT id, name, location FROM lci_processes_311 WHERE name ILIKE '%tin production%' LIMIT 1;")
    sample = cur_pg.fetchone()
    print(f"\n[TEST QUERY OK] Proceso muestra: #{sample[0]} | {sample[1]} [{sample[2]}]")

    cur_pg.close()
    conn_pg.close()
    cur_sq.close()
    conn_sq.close()

    print("\n[EXITO TOTAL] MIGRACION DE ECOINVENT 3.11 A SUPABASE COMPLETADA AL 100%!")

if __name__ == "__main__":
    run_migration()
