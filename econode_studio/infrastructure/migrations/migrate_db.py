import sqlite3
import os

DB_PATH = r"C:\Users\Josue\Documents\Espacio\ECONODE\ecoinvent\ecoinvent_312.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.execute("PRAGMA table_info(product_systems);")
cols = {c[1] for c in cur.fetchall()}

new_cols = [
    ("owner_id", "TEXT DEFAULT 'analyst_carla'"),
    ("owner_email", "TEXT DEFAULT 'carla.mendez@econode.io'"),
    ("owner_name", "TEXT DEFAULT 'Carla Méndez'"),
    ("owner_role", "TEXT DEFAULT 'analyst'"),
    ("owner_org", "TEXT DEFAULT 'BioPack Industrial S.A. de C.V.'"),
    ("category", "TEXT DEFAULT 'Polímeros'"),
    ("geography", "TEXT DEFAULT '[MX]'"),
    ("status", "TEXT DEFAULT 'in_audit'"),
    ("compliance_rate", "TEXT DEFAULT '100.0%'")
]

for col_name, col_def in new_cols:
    if col_name not in cols:
        conn.execute(f"ALTER TABLE product_systems ADD COLUMN {col_name} {col_def};")
        print(f"Added column {col_name}")

conn.execute("DELETE FROM product_systems WHERE id > 21;")
conn.execute("UPDATE product_systems SET owner_email = 'carla.mendez@econode.io', owner_name = 'Carla Méndez' WHERE id = 21;")
conn.commit()

rows = conn.execute("SELECT id, name, code, owner_email, owner_name FROM product_systems;").fetchall()
print("Migration completed successfully. Systems:")
for r in rows:
    print(r)
conn.close()

