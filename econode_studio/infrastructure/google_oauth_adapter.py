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
    Valida criptográficamente un ID Token emitido por Google Identity Services.
    Consulta el endpoint oficial de verificación de Google oauth2.googleapis.com/tokeninfo.
    """
    if not credential or not isinstance(credential, str):
        raise ValueError("Credencial JWT vacía o inválida")

    credential = credential.strip()

    verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(credential)}"
    req = urllib.request.Request(
        verify_url,
        headers={"User-Agent": "ECONODE-Studio-OAuth/2.5"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status} al validar credencial con Google")
            token_info = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Error al validar credencial con Google: {e}")

    iss = token_info.get("iss", "")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError(f"Emisor de token de Google inválido: {iss}")

    expected_client_id = get_configured_client_id()
    if expected_client_id:
        token_aud = token_info.get("aud", "")
        if token_aud != expected_client_id:
            raise ValueError("Audiencia del token de Google no coincide con el Client ID configurado.")

    email_verified = token_info.get("email_verified")
    if email_verified is not None and not (email_verified is True or str(email_verified).lower() == "true"):
        raise ValueError("La dirección de correo de Google no está verificada.")

    email = token_info.get("email")
    if not email:
        raise ValueError("El token de Google no contiene una dirección de correo válida.")

    return token_info

def resolve_role_for_email(email: str) -> str:
    """Asigna rol de auditor a administradores registrados; rol de analista por defecto."""
    clean_email = (email or "").strip().lower()
    if clean_email in get_admin_emails():
        return "auditor"
    return "analyst"
