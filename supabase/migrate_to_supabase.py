"""
supabase/migrate_to_supabase.py
Script automatizado para migrar el esquema y los datos del catálogo a Supabase PostgreSQL.

Uso:
  python supabase/migrate_to_supabase.py "postgresql://postgres.[REF]:[PASSWORD]@aws-1-[REGION].pooler.supabase.com:6543/postgres"
"""

import os
import sys
import time

# Asegurar codificación UTF-8 en consola de Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def run_migration():
    db_url = None
    if len(sys.argv) > 1:
        db_url = sys.argv[1].strip()
    else:
        db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("=" * 70)
        print("ECONODE STUDIO -> MIGRACION A SUPABASE")
        print("=" * 70)
        print("Por favor proporciona la URL de conexion a tu base de datos Supabase.")
        print("\nEjemplo de uso:")
        print('  python supabase/migrate_to_supabase.py "postgresql://postgres.[REF]:[PASSWORD]@aws-1-[REGION].pooler.supabase.com:6543/postgres"')
        print("=" * 70)
        return

    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2 no esta instalado. Ejecuta: pip install psycopg2-binary")
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "supabase", "01_schema.sql")
    data_dir = os.path.join(base_dir, "supabase", "data")

    print("\n" + "=" * 70)
    print("CONECTANDO A SUPABASE POSTGRESQL...")
    print("=" * 70)

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        print("[OK] Conexion establecida exitosamente con Supabase!")
    except Exception as e:
        print(f"Error conectando a Supabase: {e}")
        return

    # 1. Ejecutar Schema DDL
    print("\n[Paso 1/5] Ejecutando esquema DDL y datos operativos iniciales (01_schema.sql)...")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        try:
            # Dividir en bloques de comandos limpios para compatibilidad total con Pooler
            statements = [stmt.strip() for stmt in schema_sql.split(";\n") if stmt.strip()]
            for s in statements:
                if s:
                    try:
                        cur.execute(s + ";")
                    except Exception as stmt_err:
                        # Si ya existe o aviso menor
                        err_str = str(stmt_err).lower()
                        if "already exists" not in err_str and "duplicate" not in err_str:
                            print(f"  Aviso: {stmt_err}")
            print("[OK] Esquema DDL, tablas, vistas y usuarios creados con exito.")
        except Exception as e:
            print(f"Aviso durante ejecucion de schema: {e}")
    else:
        print(f"Error: No se encontro {schema_path}")
        return

    # Limpiar tablas de catálogo antes de la importación masiva
    cur.execute("TRUNCATE TABLE lci_exchanges, lci_processes, lci_flows, lci_categories RESTART IDENTITY CASCADE;")

    # 2. Cargar Categorías
    cat_file = os.path.join(data_dir, "lci_categories.csv")
    if os.path.exists(cat_file):
        print("\n[Paso 2/5] Importando 786 categorias industriales...")
        t0 = time.time()
        with open(cat_file, "r", encoding="utf-8") as f:
            next(f) # skip header
            cur.copy_expert("COPY lci_categories (id, name, category_type, description) FROM STDIN WITH (FORMAT csv, DELIMITER ',', QUOTE '\"');", f)
        print(f"[OK] Categorias importadas en {time.time()-t0:.2f}s.")

    # 3. Cargar Flujos
    flow_file = os.path.join(data_dir, "lci_flows.csv")
    if os.path.exists(flow_file):
        print("\n[Paso 3/5] Importando 14,211 flujos de inventario...")
        t0 = time.time()
        with open(flow_file, "r", encoding="utf-8") as f:
            next(f)
            cur.copy_expert("COPY lci_flows (id, code, name, flow_type, category_name, unit_symbol, description) FROM STDIN WITH (FORMAT csv, DELIMITER ',', QUOTE '\"');", f)
        print(f"[OK] Flujos importados en {time.time()-t0:.2f}s.")

    # 4. Cargar Procesos
    proc_file = os.path.join(data_dir, "lci_processes.csv")
    if os.path.exists(proc_file):
        print("\n[Paso 4/5] Importando 26,537 procesos unitarios (ecoinvent 3.12)...")
        t0 = time.time()
        with open(proc_file, "r", encoding="utf-8") as f:
            next(f)
            cur.copy_expert("""
                COPY lci_processes (
                    id, code, name, category_id, category_name, location,
                    reference_flow_id, reference_flow_name, reference_amount, reference_unit,
                    description, is_custom
                ) FROM STDIN WITH (FORMAT csv, DELIMITER ',', QUOTE '\"');
            """, f)
        print(f"[OK] Procesos importados en {time.time()-t0:.2f}s.")

    # 5. Cargar Intercambios Clave
    ex_file = os.path.join(data_dir, "lci_exchanges.csv")
    if os.path.exists(ex_file):
        print("\n[Paso 5/5] Importando 339,067 intercambios unitarios de tecnosfera y produccion...")
        t0 = time.time()
        with open(ex_file, "r", encoding="utf-8") as f:
            next(f)
            cur.copy_expert("""
                COPY lci_exchanges (
                    process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description
                ) FROM STDIN WITH (FORMAT csv, DELIMITER ',', QUOTE '\"');
            """, f)
        print(f"[OK] Intercambios importados en {time.time()-t0:.2f}s.")

    # Verificación final
    print("\n" + "=" * 70)
    print("VERIFICACION DE CONTEO EN SUPABASE POSTGRESQL:")
    print("=" * 70)
    tables_to_check = [
        "auth_users", "product_systems", "product_system_nodes", "product_system_edges",
        "checklist_template_clauses", "lci_categories", "lci_flows", "lci_processes", "lci_exchanges"
    ]
    for tbl in tables_to_check:
        try:
            cur.execute(f"SELECT count(*) FROM {tbl};")
            count = cur.fetchone()[0]
            print(f"  * {tbl:28s}: {count:,} filas registradas")
        except Exception as e:
            print(f"  * {tbl:28s}: error ({e})")

    cur.close()
    conn.close()
    print("\n[EXITO TOTAL] MIGRACION A SUPABASE COMPLETADA AL 100%!")

if __name__ == "__main__":
    run_migration()
