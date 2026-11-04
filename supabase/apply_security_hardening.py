"""
supabase/apply_security_hardening.py
Aplica de forma automatizada las politicas de seguridad y RLS de Supabase
definidas en 02_security_hardening.sql sobre la base de datos PostgreSQL en produccion.

Uso:
    python supabase/apply_security_hardening.py "<DATABASE_URL>"
o simplemente:
    python supabase/apply_security_hardening.py
(si DATABASE_URL esta configurada en el entorno o en el archivo .env)
"""

import os
import sys

def main():
    db_url = None
    if len(sys.argv) > 1:
        db_url = sys.argv[1].strip()
    
    if not db_url:
        db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("[ERROR] No se proporciono DATABASE_URL. Especifica la URL de conexion:")
        print("  python supabase/apply_security_hardening.py \"postgresql://postgres.[REF]:[PASS]@[HOST]:6543/postgres\"")
        sys.exit(1)

    sql_path = os.path.join(os.path.dirname(__file__), "02_security_hardening.sql")
    if not os.path.exists(sql_path):
        print(f"[ERROR] Archivo no encontrado: {sql_path}")
        sys.exit(1)

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        import psycopg2
    except ImportError:
        print("[ERROR] psycopg2 no esta instalado. Ejecuta: pip install psycopg2-binary")
        sys.exit(1)

    print("[SUPABASE SECURITY] Conectando a Supabase PostgreSQL...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        print("[SUPABASE SECURITY] Ejecutando 02_security_hardening.sql...")
        cur.execute(sql_content)
        cur.close()
        conn.close()
        print("[SUPABASE SECURITY] Hardening completado con exito:")
        print("  - Row Level Security (RLS) habilitado y forzado en todas las tablas")
        print("  - Vistas configuradas con security_invoker = true")
        print("  - Permisos por defecto revocados de anon y public")
        print("  - Politicas granulares aplicadas para catalogo LCI y aislamiento de tenancy")
        print("  - Bucket 'econode-vault' configurado como privado con RLS en storage.objects")
        print("  - Realtime publication saneada sin tablas sensibles")
    except Exception as e:
        print(f"[ERROR] Fallo al aplicar hardening: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

