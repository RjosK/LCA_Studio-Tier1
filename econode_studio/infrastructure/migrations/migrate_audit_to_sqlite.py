"""
econode_studio/infrastructure/migrate_audit_to_sqlite.py
Migra comentarios y estados de checklist NOM-070 desde archivos JSON planos a SQLite (econode_audit.db).
"""

import os
import sys
import json
import sqlite3

# Asegurar path de importación
STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from infrastructure.audit_adapter import (
    init_audit_db,
    get_audit_db_connection,
    AUDIT_DB_PATH
)

BASE_DIR = os.path.dirname(STUDIO_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
COMMENTS_JSON = os.path.join(DATA_DIR, "econode_comments.json")
CHECKLIST_JSON = os.path.join(DATA_DIR, "econode_checklist_state.json")


def migrate():
    print(f"=== MIGRACIÓN DE AUDITORÍA A SQLITE ===")
    print(f"Target DB: {AUDIT_DB_PATH}")
    init_audit_db()

    with get_audit_db_connection() as conn:
        # 1. Migrar comentarios
        comment_count = 0
        if os.path.exists(COMMENTS_JSON):
            with open(COMMENTS_JSON, "r", encoding="utf-8") as f:
                comments = json.load(f)

            for c in comments:
                cid = c.get("id")
                # Verificar si ya existe
                existing = conn.execute("SELECT id FROM audit_comments WHERE id = ?;", (cid,)).fetchone()
                if not existing:
                    conn.execute("""
                        INSERT INTO audit_comments (
                            id, system_id, author_name, author_role, content, node_id, x, y,
                            status, resolved_by, resolved_at, reply, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cid,
                        c.get("system_id", 21),
                        c.get("author_name", "Usuario"),
                        c.get("author_role", "auditor"),
                        c.get("content", ""),
                        c.get("node_id"),
                        c.get("x"),
                        c.get("y"),
                        c.get("status", "open"),
                        c.get("resolved_by"),
                        c.get("resolved_at"),
                        c.get("reply"),
                        c.get("created_at", "2026-10-07T00:00:00Z")
                    ))
                    comment_count += 1
            print(f"-> {comment_count} comentarios migrados desde {COMMENTS_JSON}.")
        else:
            print(f"-> {COMMENTS_JSON} no encontrado, usando registros existentes o por defecto.")

        # 2. Migrar estados de checklist y sellos
        clause_count = 0
        seal_count = 0
        if os.path.exists(CHECKLIST_JSON):
            with open(CHECKLIST_JSON, "r", encoding="utf-8") as f:
                chk_data = json.load(f)

            for sys_id_str, vals in chk_data.items():
                try:
                    sys_id = int(sys_id_str)
                except ValueError:
                    continue

                for k, v in vals.items():
                    if k == "seal":
                        conn.execute("""
                            INSERT INTO audit_seals (system_id, digital_seal, signed_by, compliance_rate, signed_at)
                            VALUES (?, ?, 'Auditor Líder', 100.0, '2026-10-07T00:00:00Z')
                            ON CONFLICT(system_id) DO UPDATE SET
                                digital_seal = excluded.digital_seal;
                        """, (sys_id, str(v)))
                        seal_count += 1
                    else:
                        is_comp = 1 if bool(v) else 0
                        conn.execute("""
                            INSERT INTO checklist_states (system_id, clause_id, is_compliant, updated_at)
                            VALUES (?, ?, ?, '2026-10-07T00:00:00Z')
                            ON CONFLICT(system_id, clause_id) DO UPDATE SET
                                is_compliant = excluded.is_compliant;
                        """, (sys_id, k, is_comp))
                        clause_count += 1

            print(f"-> {clause_count} estados de cláusulas y {seal_count} sellos migrados desde {CHECKLIST_JSON}.")
        else:
            print(f"-> {CHECKLIST_JSON} no encontrado.")

        # Resumen en base de datos
        total_comments = conn.execute("SELECT COUNT(*) FROM audit_comments;").fetchone()[0]
        total_clauses = conn.execute("SELECT COUNT(*) FROM checklist_states;").fetchone()[0]
        total_seals = conn.execute("SELECT COUNT(*) FROM audit_seals;").fetchone()[0]
        print(f"\n[OK] Estado final en {AUDIT_DB_PATH}:")
        print(f"     Total Comentarios: {total_comments}")
        print(f"     Total Cláusulas Registradas: {total_clauses}")
        print(f"     Total Sellos Digitales: {total_seals}")


if __name__ == "__main__":
    migrate()

