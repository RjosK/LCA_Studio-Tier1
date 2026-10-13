import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "econode_auth.db")
JSON_PATH = os.path.join(DATA_DIR, "econode_accounts.json")

os.makedirs(DATA_DIR, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Crear tabla e índices
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        organization TEXT DEFAULT '',
        role TEXT NOT NULL DEFAULT 'analyst',
        role_title TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        token TEXT DEFAULT '',
        permissions_json TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));")
conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username));")

# Migrar desde JSON si existe
migrated_count = 0
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        for acc in data.get("accounts", []):
            perms = json.dumps(acc.get("permissions", []))
            conn.execute("""
                INSERT INTO users (id, username, email, password_hash, display_name, organization, role, role_title, bio, avatar, token, permissions_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    password_hash = excluded.password_hash,
                    token = excluded.token,
                    display_name = excluded.display_name,
                    organization = excluded.organization,
                    role = excluded.role;
            """, (
                acc["id"], acc["username"], acc["email"].lower(), acc.get("password_hash", ""),
                acc["display_name"], acc.get("organization", ""), acc.get("role", "analyst"),
                acc.get("role_title", ""), acc.get("bio", ""), acc.get("avatar", ""),
                acc.get("token", ""), perms
            ))
            migrated_count += 1
conn.commit()

rows = conn.execute("SELECT id, display_name, email, role FROM users;").fetchall()
print(f"Migration successful! {len(rows)} users in SQLite database:")
for r in rows:
    print(dict(r))
conn.close()

