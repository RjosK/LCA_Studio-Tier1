"""
econode_studio/config.py - Configuración Unificada y Escalable de ECONODE
Sigue los principios de 'The Twelve-Factor App' para permitir configuración transparente
mediante variables de entorno sin modificar el código fuente.
Soporta dual-mode: Supabase PostgreSQL (Cloud / Vercel) y SQLite Local (Offline / Desktop).
"""

import os
from typing import Dict, Any

# Raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(STUDIO_DIR, "data")

class Settings:
    # Entorno y Servidor
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8081"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Seguridad y Criptografía
    SECRET_KEY: str = os.getenv("SECRET_KEY", "econode_jwt_super_secret_key_tier1_2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "72"))
    PASSWORD_SALT: str = os.getenv("PASSWORD_SALT", "econode_secure_pbkdf2_salt_v1")

    # Conexión Supabase PostgreSQL (Cloud / Producción)
    DEFAULT_SUPABASE_URL: str = "postgresql://postgres.nttdfdsntwlbeqwtgnci:47Tw4W-v8Z7rkqe@aws-1-us-west-2.pooler.supabase.com:6543/postgres"
    DATABASE_URL: str = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or (
        DEFAULT_SUPABASE_URL if os.getenv("VERCEL") or not os.path.exists(os.path.join(BASE_DIR, "ecoinvent", "ecoinvent_312.db")) else ""
    )
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://nttdfdsntwlbeqwtgnci.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "econode-vault")

    @property
    def IS_POSTGRES(self) -> bool:
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip().startswith(("postgres://", "postgresql://")))

    # Bases de Datos Locales SQLite (Desarrollo Offline / Fallback)
    ECOINVENT_DB_PATH: str = os.getenv(
        "ECOINVENT_DB_PATH",
        os.path.join(BASE_DIR, "ecoinvent", "ecoinvent_312.db")
    )
    LCIA_ENGINE_DB_PATH: str = os.getenv(
        "LCIA_ENGINE_DB_PATH",
        os.path.join(DATA_DIR, "lcia_engine.db")
    )
    DOCUMENTS_DB_PATH: str = os.getenv(
        "DOCUMENTS_DB_PATH",
        os.path.join(DATA_DIR, "econode_documents.db")
    )
    AUDIT_DB_PATH: str = os.getenv(
        "AUDIT_DB_PATH",
        os.path.join(DATA_DIR, "econode_audit.db")
    )

    # Almacenamiento Documental
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "supabase" if bool(os.getenv("SUPABASE_URL")) else "local")
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", os.path.join(DATA_DIR, "documents"))

    # Cuentas, Autenticación y Credenciales
    AUTH_DB_PATH: str = os.getenv("AUTH_DB_PATH", os.path.join(DATA_DIR, "econode_auth.db"))
    CREDENCIALES_TXT_PATH: str = os.getenv("CREDENCIALES_TXT_PATH", os.path.join(DATA_DIR, "credenciales_demo.txt"))

    # Google Identity Services
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "744175439482-15giv41g1363tkof89s25bpn36akif3o.apps.googleusercontent.com")
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS", "josuearenteriaz09@gmail.com")

settings = Settings()
