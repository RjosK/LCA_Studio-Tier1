"""
supabase/export_catalog_to_csv.py
Extrae los 26,537 procesos, 14,210 flujos y categorías industriales de ecoinvent_312.db
a archivos CSV optimizados y listos para importar en Supabase PostgreSQL.
"""

import sqlite3
import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECOINVENT_DB = os.path.join(BASE_DIR, "ecoinvent", "ecoinvent_312.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "supabase", "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_all():
    print(f"Abriendo base de datos: {ECOINVENT_DB}...")
    if not os.path.exists(ECOINVENT_DB):
        print(f"Error: {ECOINVENT_DB} no existe.")
        return

    conn = sqlite3.connect(ECOINVENT_DB)
    conn.row_factory = sqlite3.Row

    # 1. Categorías
    print("\n1. Exportando Categorías...")
    cat_file = os.path.join(OUTPUT_DIR, "lci_categories.csv")
    cats = conn.execute("SELECT id, name, category_type, coalesce(description, '') as description FROM categories").fetchall()
    with open(cat_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category_type", "description"])
        for c in cats:
            writer.writerow([c["id"], c["name"], c["category_type"], c["description"]])
    print(f"   -> {len(cats):,} categorías exportadas a {cat_file} ({os.path.getsize(cat_file)/1024:.1f} KB)")

    # 2. Flujos (14,210 flujos)
    print("\n2. Exportando Flujos (Materiales, Insumos, Emisiones)...")
    flow_file = os.path.join(OUTPUT_DIR, "lci_flows.csv")
    flows = conn.execute("SELECT id, coalesce(code, '') as code, name, flow_type, category_name, unit_symbol, coalesce(description, '') as description FROM flows").fetchall()
    with open(flow_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "code", "name", "flow_type", "category_name", "unit_symbol", "description"])
        for fl in flows:
            writer.writerow([fl["id"], fl["code"], fl["name"], fl["flow_type"], fl["category_name"], fl["unit_symbol"], fl["description"]])
    print(f"   -> {len(flows):,} flujos exportados a {flow_file} ({os.path.getsize(flow_file)/(1024*1024):.2f} MB)")

    # 3. Procesos (26,537 procesos)
    print("\n3. Exportando Procesos LCI (26,537 procesos ecoinvent 3.12)...")
    proc_file = os.path.join(OUTPUT_DIR, "lci_processes.csv")
    procs = conn.execute("""
        SELECT p.id, p.code, p.name, p.category_id,
               c.name as category_name,
               coalesce(p.location, 'GLO') as location,
               coalesce(p.reference_flow_id, '') as reference_flow_id,
               coalesce(f.name, '') as reference_flow_name,
               coalesce(p.reference_amount, 1.0) as reference_amount,
               coalesce(f.unit_symbol, 'kg') as reference_unit,
               coalesce(p.description, '') as description
        FROM processes p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN flows f ON p.reference_flow_id = f.id
    """).fetchall()

    with open(proc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "code", "name", "category_id", "category_name", "location",
            "reference_flow_id", "reference_flow_name", "reference_amount", "reference_unit",
            "description", "is_custom"
        ])
        for p in procs:
            is_cust = 1 if (p["id"] >= 1000000 or str(p["code"]).startswith("PR_CUSTOM")) else 0
            writer.writerow([
                p["id"], p["code"], p["name"], p["category_id"] or "", p["category_name"] or "General",
                p["location"], p["reference_flow_id"], p["reference_flow_name"], p["reference_amount"],
                p["reference_unit"], p["description"], is_cust
            ])
    print(f"   -> {len(procs):,} procesos exportados a {proc_file} ({os.path.getsize(proc_file)/(1024*1024):.2f} MB)")

    # 4. Intercambios Unitarios Clave (Production + Technosphere de los procesos)
    print("\n4. Exportando Intercambios Unitarios Industriales (Producción y Tecnósfera)...")
    ex_file = os.path.join(OUTPUT_DIR, "lci_exchanges.csv")
    exchanges = conn.execute("""
        SELECT e.process_id, e.flow_id, e.is_input, e.exchange_type, e.amount, e.unit_symbol,
               coalesce(e.default_provider_id, '') as default_provider_id,
               coalesce(e.description, '') as description
        FROM exchanges e
        WHERE e.exchange_type IN ('production', 'technosphere', 'waste')
    """).fetchall()

    with open(ex_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["process_id", "flow_id", "is_input", "exchange_type", "amount", "unit_symbol", "default_provider_id", "description"])
        for ex in exchanges:
            writer.writerow([
                ex["process_id"], ex["flow_id"], ex["is_input"], ex["exchange_type"],
                ex["amount"], ex["unit_symbol"], ex["default_provider_id"], ex["description"]
            ])
    print(f"   -> {len(exchanges):,} intercambios exportados a {ex_file} ({os.path.getsize(ex_file)/(1024*1024):.2f} MB)")

    conn.close()
    print("\n=======================================================")
    print("¡EXTRACCIÓN EXITOSA! Archivos generados en:")
    print(f"  {OUTPUT_DIR}")
    print("=======================================================")

if __name__ == "__main__":
    export_all()

