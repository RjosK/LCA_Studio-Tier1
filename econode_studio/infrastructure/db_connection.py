"""
econode_studio/infrastructure/db_connection.py - Gestor Dual-Mode de Conexiones (PostgreSQL + SQLite)
Permite interoperabilidad transparente entre Supabase PostgreSQL (Cloud / Vercel Serverless)
y bases de datos locales SQLite (Desarrollo offline / Desktop) sin alterar la capa de lógica de negocio.
"""

import os
import re
import sqlite3
from typing import Optional, Any, List, Dict, Tuple

try:
    from config import settings
except (ImportError, ValueError):
    from econode_studio.config import settings

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class PostgresCursorProxy:
    """Proxy para cursores de psycopg2 que traduce placeholders y comportamientos SQLite."""
    def __init__(self, pg_cursor):
        self._cur = pg_cursor
        self.lastrowid = None

    def execute(self, query: str, params: Optional[Any] = None):
        cleaned_query = query.strip()
        
        # Ignorar PRAGMAs de SQLite en PostgreSQL
        if cleaned_query.upper().startswith("PRAGMA"):
            return self

        # 1. Convertir '?' a '%s' y escapar '%' literales
        if "?" in cleaned_query:
            cleaned_query = cleaned_query.replace("%", "%%").replace("?", "%s")
        elif "%" in cleaned_query and params:
            cleaned_query = cleaned_query.replace("%", "%%")

        # 2. Convertir INSERT OR IGNORE a INSERT ... ON CONFLICT DO NOTHING
        if "INSERT OR IGNORE INTO" in cleaned_query.upper():
            cleaned_query = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", cleaned_query, flags=re.IGNORECASE)
            if "ON CONFLICT" not in cleaned_query.upper():
                cleaned_query += " ON CONFLICT DO NOTHING"

        # 3. Convertir INSERT OR REPLACE a INSERT ...
        if "INSERT OR REPLACE INTO" in cleaned_query.upper():
            cleaned_query = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", cleaned_query, flags=re.IGNORECASE)

        # 4. Manejo de lastrowid para INSERTs sin RETURNING id
        is_insert = cleaned_query.upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in cleaned_query.upper()
        if is_insert and not has_returning:
            # Tablas con ID autoincremental en PostgreSQL
            target_tables = ("product_systems", "custom_processes", "custom_flows", "custom_exchanges", "audit_comments", "documents")
            if any(tbl in cleaned_query for tbl in target_tables):
                cleaned_query += " RETURNING id"

        try:
            if params is not None:
                if isinstance(params, (list, tuple)):
                    self._cur.execute(cleaned_query, tuple(params))
                else:
                    self._cur.execute(cleaned_query, (params,))
            else:
                self._cur.execute(cleaned_query)

            if is_insert and "RETURNING id" in cleaned_query:
                try:
                    res = self._cur.fetchone()
                    if res:
                        self.lastrowid = res[0]
                except Exception:
                    pass
        except Exception as e:
            raise e

        return self

    def executemany(self, query: str, params_list: List[Any]):
        if "?" in query:
            query = query.replace("?", "%s")
        return self._cur.executemany(query, params_list)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size: Optional[int] = None):
        return self._cur.fetchmany(size) if size else self._cur.fetchmany()

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def close(self):
        self._cur.close()

    def __iter__(self):
        return iter(self._cur)


class PostgresConnectionProxy:
    """Proxy para conexiones de psycopg2 con compatibilidad con sqlite3.Connection."""
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorProxy(cur)

    def execute(self, query: str, params: Optional[Any] = None):
        cur = self.cursor()
        return cur.execute(query, params)

    def executemany(self, query: str, params_list: List[Any]):
        cur = self.cursor()
        return cur.executemany(query, params_list)

    def executescript(self, script: str):
        with self._conn.cursor() as cur:
            cur.execute(script)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()


def get_db_connection(db_path: Optional[str] = None) -> Any:
    """
    Retorna una conexión activa:
    - Si DATABASE_URL está configurado: Conexión Supabase PostgreSQL (PostgresConnectionProxy)
    - En caso contrario: Conexión SQLite optimizada (sqlite3.Connection en modo WAL)
    """
    if settings.IS_POSTGRES and HAS_PSYCOPG2:
        try:
            # Conexión directa a Supabase PostgreSQL
            conn = psycopg2.connect(settings.DATABASE_URL)
            conn.autocommit = False
            return PostgresConnectionProxy(conn)
        except Exception as e:
            # Si falla la conexión a Postgres y existe una ruta local, fallback seguro
            if not db_path:
                raise e

    # Fallback / Modo Local SQLite
    target_path = db_path or settings.ECOINVENT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        pass
    return conn

