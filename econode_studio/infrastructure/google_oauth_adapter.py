"""
econode_studio/infrastructure/google_oauth_adapter.py - Adaptador Oficial de Autenticación Google Identity Services
Valida credenciales ID Token JWT contra Google sin dependencias externas.
"""

import urllib.request
import urllib.parse
import json
import os
from typing import Dict, Any, Optional

try:
    from config import settings
except (ImportError, ValueError):
    from econode_studio.config import settings

def get_admin_emails() -> list[str]:
    raw = getattr(settings, "ADMIN_EMAILS", "josuearenteriaz09@gmail.com")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]

def get_configured_client_id() -> str:
    return getattr(settings, "GOOGLE_CLIENT_ID", "").strip()

def verify_google_id_token(credential: str) -> Dict[str, Any]:
    """
    Valida un ID Token emitido por Google Identity Services.
    Utiliza urllib.request estándar para máxima portabilidad y seguridad.
    """
    if not credential:
        raise ValueError("Credencial JWT vacía")

    verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(credential)}"
    req = urllib.request.Request(
        verify_url,
        headers={"User-Agent": "ECONODE-Studio-OAuth/2.5"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} al validar credencial con Google")
        token_info = json.loads(resp.read().decode("utf-8"))

    iss = token_info.get("iss", "")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError(f"Emisor de token de Google inválido: {iss}")

    return token_info

def resolve_role_for_email(email: str) -> str:
    """Asigna rol de auditor a administradores registrados; rol de cliente a cualquier otro usuario."""
    clean_email = (email or "").strip().lower()
    if clean_email in get_admin_emails():
        return "auditor"
    return "user"

