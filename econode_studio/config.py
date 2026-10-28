"""
econode_studio/config.py - Configuración centralizada de ECONODE Studio
Maneja variables de entorno, rutas absolutas a bases de datos y flags operacionales.
"""

import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
VAULT_DIR = os.path.join(PROJECT_ROOT, "ECONODE_VAULT")

class Settings:
    # Entorno
    ENV: str = os.getenv("ENV", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    # Servidor HTTP
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8080))

    # Criptografía y Sesiones
    SECRET_KEY: str = os.getenv("SECRET_KEY", "econode_jwt_studio_sec_2026_x7a9k1m4")
    PASSWORD_SALT: str = os.getenv("PASSWORD_SALT", "econode_salt_studio_pbkdf2_2026")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

    # Conexión Supabase PostgreSQL (Producción / Vercel Serverless)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", None)
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY", None)

    @property
    def IS_POSTGRES(self) -> bool:
        """Determina si el backend opera sobre PostgreSQL (Cloud) o SQLite (Local)."""
        return bool(self.DATABASE_URL and ("postgres" in self.DATABASE_URL.lower()))

    # Conexiones SQLite Locales (Fallback y Desarrollo Local)
    ECOINVENT_DB_PATH: str = os.getenv(
        "ECOINVENT_DB_PATH",
        os.path.join(PROJECT_ROOT, "ecoinvent", "ecoinvent_312.db")
    )
    AUDIT_DB_PATH: str = os.getenv(
        "AUDIT_DB_PATH",
        os.path.join(DATA_DIR, "econode_audit.db")
    )

    # Almacenamiento Documental
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "supabase" if bool(os.getenv("SUPABASE_URL")) else "local")
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", os.path.join(DATA_DIR, "documents"))

    # Cuentas, Autenticación e Invitaciones
    AUTH_DB_PATH: str = os.getenv("AUTH_DB_PATH", os.path.join(DATA_DIR, "econode_auth.db"))

    # Google Identity Services (GSI)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "968718859059-81u6bj6l4op1e0dsnblqg73ego8ns59j.apps.googleusercontent.com")
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS", "")

settings = Settings()
