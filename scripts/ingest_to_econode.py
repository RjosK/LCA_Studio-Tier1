"""
Ingest all harvested LCA datasets from LCA_Data_Harvester into ECONODE ecoinvent_312.db
"""
import sqlite3
import os

source_db_path = r"C:\Users\Josue\Documents\Espacio\LCA_Data_Harvester\data\sqlite\unified_lca_catalogs.db"
target_db_path = r"C:\Users\Josue\Documents\Espacio\ECONODE\ecoinvent\ecoinvent_312.db"

src_conn = sqlite3.connect(source_db_path)
src_conn.row_factory = sqlite3.Row

tgt_conn = sqlite3.connect(target_db_path)
tgt_conn.row_factory = sqlite3.Row

# Ensure catalog_sources has all needed sources
tgt_sources = {r["code"]: r["id"] for r in tgt_conn.execute("SELECT id, code FROM catalog_sources").fetchall()}

src_sources = src_conn.execute("SELECT * FROM catalog_sources").fetchall()
for s in src_sources:
    code = s["code"]
    # Normalize code mapping if needed
    if code not in tgt_sources:
        cur = tgt_conn.execute("""
            INSERT INTO catalog_sources (code, name, version, license_type, provider, base_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, s["name"], s["version"], s["license_type"], s["provider"], s["base_url"]))
        tgt_sources[code] = cur.lastrowid
        print(f"Added source: {code} -> id {tgt_sources[code]}")

tgt_conn.commit()
print("Target sources mapping:", tgt_sources)

# Check target columns
cols = [c[1] for c in tgt_conn.execute("PRAGMA table_info(catalog_processes)").fetchall()]
print("Target catalog_processes columns:", cols)

# Add source_code column to target if not present for faster direct querying
if "source_code" not in cols:
    tgt_conn.execute("ALTER TABLE catalog_processes ADD COLUMN source_code TEXT")
    print("Added source_code column to catalog_processes in ECONODE ecoinvent_312.db")

# Delete previously imported rows from harvested sources to prevent duplicates
tgt_conn.execute("DELETE FROM catalog_processes WHERE source_code IN ('glad_network', 'oekobaudat_de', 'ademe_base_carbone', 'openlca_elcd') OR source_id IN (SELECT id FROM catalog_sources WHERE code IN ('glad_network', 'oekobaudat', 'oekobaudat_de', 'ademe_base_carbone', 'openlca_elcd'))")

# Read rows from source
src_rows = src_conn.execute("""
    SELECT source_code, original_uuid, process_name, reference_product, unit,
           geography, category, activity_type, provider_name, metadata_json
    FROM catalog_processes
""").fetchall()

print(f"Found {len(src_rows)} rows in unified_lca_catalogs.db to ingest...")

insert_sql = """
INSERT INTO catalog_processes (
    source_id, source_code, original_uuid, name, reference_product, unit,
    location, category_id, provider_name, activity_type, metadata_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

to_insert = []
for r in src_rows:
    sc = r["source_code"]
    sid = tgt_sources.get(sc, tgt_sources.get("glad_network", 1))
    to_insert.append((
        sid,
        sc,
        r["original_uuid"],
        r["process_name"],
        r["reference_product"],
        r["unit"],
        r["geography"],
        1,  # default category_id
        r["provider_name"],
        r["category"] or r["activity_type"],  # store human category in activity_type
        r["metadata_json"]
    ))

tgt_conn.executemany(insert_sql, to_insert)
tgt_conn.commit()

# Create performance index on source_code and name
tgt_conn.execute("CREATE INDEX IF NOT EXISTS idx_catproc_src_name ON catalog_processes(source_code, name)")
tgt_conn.commit()

# Print summary
summary = tgt_conn.execute("SELECT source_code, COUNT(*) FROM catalog_processes GROUP BY source_code").fetchall()
print("Ingestion complete! Total by source in ECONODE:")
for row in summary:
    print(f"  {row[0]}: {row[1]}")

src_conn.close()
tgt_conn.close()
