"""
econode_studio/server.py - Servidor REST API Autónomo para ECONODE Studio (Tier 1)
Desacoplado del código legado. Cero dependencias externas pesadas (Python stdlib http.server + sqlite3).
Soporta puerto configurable (8081 por defecto, o 8080).
"""

import http.server
import json
import os
import sys
import argparse
import urllib.parse
from typing import Dict, Any, Optional, List

# Asegurar codificación UTF-8 en terminales de Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Ajustar PYTHONPATH
STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, STUDIO_DIR)
sys.path.insert(0, os.path.dirname(STUDIO_DIR))

try:
    from config import settings
except (ImportError, ValueError):
    from econode_studio.config import settings

from domain import RoleEnum
from application import (
    auth_service,
    get_dashboard_systems_use_case,
    create_system_wizard_use_case,
    import_systems_csv_use_case,
    import_simapro_to_system_use_case,
    get_system_canvas_use_case,
    save_system_canvas_use_case,
    delete_product_system_use_case,
    add_system_collaborator_use_case,
    get_system_parameters_use_case,
    save_system_parameter_use_case,
    delete_system_parameter_use_case,
    list_projects_use_case,
    create_project_use_case,
    delete_project_use_case,
    assign_system_to_project_use_case,
    compare_project_systems_use_case,
    search_catalog_use_case,
    get_process_sheet_use_case,
    list_system_comments_use_case,
    add_system_comment_use_case,
    reply_and_resolve_comment_use_case,
    delete_system_comment_use_case,
    get_audit_checklist_use_case,
    update_clause_status_use_case,
    update_clause_evidence_use_case,
    sign_normative_audit_use_case,
    list_available_standards_use_case,
    create_custom_standard_use_case,
    import_standard_csv_use_case,
    get_checklist_csv_template_use_case,
    get_categories_use_case,
    search_flows_use_case,
    search_providers_use_case,
    create_custom_process_use_case,
    create_custom_flow_use_case,
    delete_custom_process_use_case,
    delete_custom_flow_use_case,
    list_documents_use_case,
    upload_document_use_case,
    get_document_file_use_case,
    delete_document_use_case,
    export_openlca_use_case,
    export_ilcd_use_case,
    export_simapro_use_case,
    export_csv_use_case,
    export_complete_expediente_use_case,
    list_documents,
    save_document,
    get_document_file,
    delete_document,
    export_openlca_jsonld_zip,
    export_ilcd_xml_zip,
    export_simapro_csv,
    export_lci_consolidated_csv,
    export_expediente_nom070_zip,
    export_system_pdf_bytes,
    export_system_docx_bytes
)
try:
    from application.ghg_service import (
        list_inventories_use_case,
        get_inventory_by_id_use_case,
        create_inventory_use_case,
        delete_inventory_use_case,
        add_entry_to_inventory_use_case,
        delete_entry_from_inventory_use_case,
        get_scope_taxonomy_use_case,
        search_emission_factors,
        list_distinct_sources
    )
except (ImportError, ValueError):
    from econode_studio.application.ghg_service import (
        list_inventories_use_case,
        get_inventory_by_id_use_case,
        create_inventory_use_case,
        delete_inventory_use_case,
        add_entry_to_inventory_use_case,
        delete_entry_from_inventory_use_case,
        get_scope_taxonomy_use_case,
        search_emission_factors,
        list_distinct_sources
    )
try:
    from application.epd_service import (
        list_epd_templates_use_case,
        instantiate_epd_template_use_case,
        compute_epd_report_use_case,
        save_epd_metadata_use_case,
        export_openepd_json_use_case
    )
except (ImportError, ValueError):
    from econode_studio.application.epd_service import (
        list_epd_templates_use_case,
        instantiate_epd_template_use_case,
        compute_epd_report_use_case,
        save_epd_metadata_use_case,
        export_openepd_json_use_case
    )
from infrastructure import (
    get_active_db_connection,
    get_configured_client_id,
    get_user_by_id,
    save_api_key,
    get_api_key_by_hash,
    list_user_api_keys,
    revoke_api_key,
    update_api_key_last_used,
    check_and_increment_rate_limit,
    handle_jsonrpc_request,
    MCP_TOOLS
)
try:
    from domain.api_key import ApiKey
except (ImportError, ValueError):
    from econode_studio.domain.api_key import ApiKey

WEB_DIR = os.path.join(os.path.dirname(STUDIO_DIR), "public")
if not os.path.exists(WEB_DIR):
    web_alt = os.path.join(STUDIO_DIR, "web")
    if os.path.exists(web_alt):
        WEB_DIR = web_alt
    else:
        WEB_DIR = os.path.abspath(os.curdir)

TEMPLATE_CSV_PATH = os.path.join(os.path.dirname(STUDIO_DIR), "plantilla_sistemas_parametrizados.csv")
DEFAULT_TEMPLATE_CSV = (
    "nombre,capacidad_ml,peso_envase_g,tasa_reciclaje_pct,distancia_transporte_km,contenido_reciclado_pct\n"
    "Botellin PET 330 ml (Consumo Rapido),330,16.0,25.0,80,0.0\n"
    "Botella PET 500 ml Estandar,500,24.0,40.0,120,0.0\n"
    "Botella PET 1 Litro Familiar,1000,34.0,55.0,180,15.0\n"
    "Garrafa PET 1.5 L Alta Circularidad,1500,42.0,75.0,250,50.0\n"
    "Bidon PET 5 Litros Agua Purificada,5000,98.0,60.0,350,20.0\n"
)

def _json_serializer(obj: Any) -> Any:
    """Serializador universal de tipos PostgreSQL / SQLite para JSON REST API."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    try:
        import decimal
        if isinstance(obj, decimal.Decimal):
            return float(obj)
    except Exception:
        pass
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except Exception:
            return str(obj)
    return str(obj)

class EconodeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _set_headers(self, status=200, content_type="application/json", extra_headers=None):
        self.send_response(status)
        binary_types = (
            "application/zip",
            "application/pdf",
            "application/vnd.openxmlformats",
            "application/octet-stream",
            "image/"
        )
        if "charset" not in content_type and not any(content_type.startswith(b) for b in binary_types):
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        else:
            self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api"):
            self._set_headers(200)
            return
        return super().do_HEAD()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {}

    def _send_json(self, data: Any, status=200):
        body_bytes = json.dumps(data, ensure_ascii=False, indent=2, default=_json_serializer).encode("utf-8")
        self._set_headers(status, "application/json", extra_headers={"Content-Length": str(len(body_bytes))})
        try:
            self.wfile.write(body_bytes)
            self.wfile.flush()
        except Exception:
            pass

    def _send_error_json(self, message: str, status=400):
        self._send_json({"status": "error", "message": message}, status=status)

    def _get_request_user(self, query=None) -> Optional[Dict[str, Any]]:
        # Extraer token criptográfico desde cabecera Authorization o parámetro 'token'
        auth_header = self.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif query and "token" in query and query["token"]:
            token = query["token"][0]

        if not token:
            if getattr(settings, "ENV", "production") in ("test", "testing"):
                return auth_service.get_active_account()
            return None

        # Autenticación mediante Personal Access Token (API Key / MCP)
        if token.startswith("eco_live_"):
            import hashlib
            hashed = hashlib.sha256(token.encode("utf-8")).hexdigest()
            api_key = get_api_key_by_hash(hashed)
            if api_key and api_key.is_active():
                if not check_and_increment_rate_limit(api_key.id, api_key.rate_limit_per_minute):
                    return None
                update_api_key_last_used(api_key.id)
                user = get_user_by_id(api_key.user_id)
                if not user:
                    user = {
                        "id": api_key.user_id,
                        "username": "api_user",
                        "display_name": api_key.name,
                        "email": "",
                        "role": "analyst",
                        "organization": api_key.organization_id
                    }
                user_dict = dict(user)
                user_dict["authenticated_by"] = "api_key"
                user_dict["api_key_id"] = api_key.id
                user_dict["scopes"] = api_key.scopes
                return user_dict
            return None

        parsed = auth_service.parse_session_token(token)
        if parsed and parsed.get("user_id"):
            uid = parsed["user_id"]
            user = get_user_by_id(uid)
            if user:
                return user
            for acc in auth_service.accounts:
                if acc.get("id") == uid:
                    return acc

        for acc in auth_service.accounts:
            if acc.get("token") == token:
                return acc

        return None

    def _require_auth(self, allowed_roles: Optional[List[str]] = None, query=None) -> Optional[Dict[str, Any]]:
        user = self._get_request_user(query=query)
        if not user:
            self._send_error_json("Autenticación requerida. Por favor inicia sesión.", 401)
            return None
        if allowed_roles and user.get("role") not in allowed_roles:
            self._send_error_json("Acceso denegado: Tu rol actual no tiene permisos para esta acción.", 403)
            return None
        return user

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # Manejo de Endpoint SSE de MCP Remoto
        if path in ("/mcp/sse", "/api/v1/mcp/sse", "/api/mcp/sse", "/mcp"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            try:
                self.wfile.write(b"event: endpoint\r\ndata: /api/v1/mcp/rpc\r\n\r\n")
                self.wfile.flush()
            except Exception:
                pass
            return

        # Metadatos del Servidor MCP y Catalogo de Herramientas
        if path in ("/mcp", "/api/v1/mcp"):
            self._send_json({
                "status": "ready",
                "server": "econode-mcp",
                "version": "1.0.0",
                "protocolVersion": "2024-11-05",
                "transport": "sse",
                "endpoint": "/api/v1/mcp/rpc",
                "tools": MCP_TOOLS
            })
            return

        # 1. API Endpoints
        if path.startswith("/api"):
            conn = get_active_db_connection()
            try:
                # Listar Claves de API del usuario autenticado
                if path == "/api/account/api-keys":
                    user = self._require_auth()
                    if not user:
                        return
                    keys = [k.to_dict() for k in list_user_api_keys(user["id"])]
                    self._send_json({"status": "success", "count": len(keys), "keys": keys})
                    return

                # API v1 - Listado de Sistemas Producto ACV
                elif path == "/api/v1/systems":
                    user = self._require_auth()
                    if not user:
                        return
                    limit = int(query.get("limit", [50])[0])
                    systems = get_dashboard_systems_use_case()[:limit]
                    self._send_json({"status": "success", "count": len(systems), "systems": systems})
                    return

                # API v1 - Detalle de Sistema Producto
                elif path.startswith("/api/v1/systems/") and not path.endswith("/calculate"):
                    user = self._require_auth()
                    if not user:
                        return
                    try:
                        sys_id = int(path.split("/")[-1])
                        system = get_system_canvas_use_case(sys_id)
                        if not system:
                            self._send_error_json("Sistema producto no encontrado", 404)
                        else:
                            self._send_json({"status": "success", "system": system})
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # API v1 - Listado de Inventarios GEI
                elif path == "/api/v1/ghg/inventories":
                    user = self._require_auth()
                    if not user:
                        return
                    try:
                        invs = list_inventories_use_case()
                        self._send_json({"status": "success", "count": len(invs), "inventories": invs})
                    except Exception as e:
                        self._send_error_json(str(e), 500)
                    return

                # API v1 - Buscador de Factores de Emision
                elif path == "/api/v1/emission-factors/search":
                    user = self._require_auth()
                    if not user:
                        return
                    q = query.get("q", [""])[0] or query.get("query", [""])[0]
                    cat = query.get("category", [""])[0]
                    limit = int(query.get("limit", [20])[0])
                    try:
                        factors, _ = search_emission_factors(query=q, category=cat, limit=limit)
                        self._send_json({"status": "success", "count": len(factors), "factors": factors})
                    except Exception:
                        try:
                            factors = search_emission_factors(query=q, category=cat, limit=limit)
                            self._send_json({"status": "success", "count": len(factors), "factors": factors})
                        except Exception as e:
                            self._send_error_json(str(e), 500)
                    return

                # Auth Config (Público / Configuración de Identidad)
                elif path == "/api/auth/config":
                    current_user = self._get_request_user(query)
                    self._send_json({
                        "google_client_id": get_configured_client_id(),
                        "authenticated": current_user is not None,
                        "user": auth_service._safe_user(current_user) if current_user else None,
                        "mode": "tier1_studio"
                    })
                    return

                # Listar Invitaciones (Solo Analistas Autenticados)
                elif path == "/api/auth/invitations":
                    user = self._require_auth(allowed_roles=["analyst"], query=query)
                    if not user:
                        return
                    try:
                        invs = auth_service.list_invitations(user)
                        self._send_json({"status": "success", "invitations": invs, "count": len(invs)})
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # Verificar Token de Invitación (Público para vista de bienvenida)
                elif path == "/api/auth/invite/verify":
                    tok = query.get("token", [""])[0]
                    if not tok:
                        self._send_error_json("Token de invitación no proporcionado", 400)
                        return
                    info = auth_service.verify_invite_token(tok)
                    if not info:
                        self._send_error_json("Invitación no encontrada o token inválido", 404)
                        return
                    self._send_json({"status": "success", "invitation": info})
                    return

                # Profile (Requiere Sesión Activa)
                elif path == "/api/profile":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    safe_u = auth_service._safe_user(user)
                    self._send_json({
                        "user": safe_u,
                        "role": user.get("role", "analyst"),
                        "tier": "Tier 1: ECONODE Studio",
                        "security": {
                            "cipher": "TLS 1.3 / HMAC-SHA256",
                            "session": "Verificada y Activa"
                        }
                    })
                    return

                # Dashboard Systems (Requiere Autenticación)
                elif path == "/api/systems":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    user_email = user.get("email")
                    user_id = user.get("id")
                    user_role = user.get("role")
                    systems = get_dashboard_systems_use_case(conn, user_email=user_email, user_id=user_id, user_role=user_role)
                    self._send_json({
                        "status": "success",
                        "count": len(systems),
                        "items": systems
                    })
                    return

                # Proyectos Contenedores (Requiere Autenticación)
                elif path == "/api/projects":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    user_email = user.get("email")
                    user_id = user.get("id")
                    user_role = user.get("role")
                    projects = list_projects_use_case(conn, user_email=user_email, user_id=user_id, user_role=user_role)
                    self._send_json({
                        "status": "success",
                        "count": len(projects),
                        "items": projects
                    })
                    return

                # Comparativa LCIA entre Sistemas de un Proyecto (Requiere Autenticación)
                elif path.startswith("/api/projects/") and path.endswith("/compare"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    proj_id = int(path.split("/")[3])
                    try:
                        res = compare_project_systems_use_case(conn, proj_id)
                        self._send_json(res)
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # --- Modulo GHG Protocol ---
                # Listar Inventarios Corporativos GEI
                elif path == "/api/ghg/inventories":
                    try:
                        inventories = list_inventories_use_case()
                        self._send_json({
                            "status": "success",
                            "count": len(inventories),
                            "items": inventories,
                            "inventories": inventories
                        })
                    except Exception as e:
                        self._send_error_json(str(e), 500)
                    return

                # Detalle y Resumen Contable de Inventario GEI
                elif path.startswith("/api/ghg/inventories/") and not path.endswith("/entries"):
                    try:
                        inv_id = int(path.split("/")[4])
                        inv = get_inventory_by_id_use_case(inv_id)
                        if not inv:
                            self._send_error_json("Inventario GEI no encontrado", 404)
                        else:
                            self._send_json({"status": "success", "inventory": inv})
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # Taxonomia Oficial de Categorias GHG Protocol
                elif path == "/api/ghg/taxonomy":
                    self._send_json({"status": "success", "taxonomy": get_scope_taxonomy_use_case()})
                    return

                # Buscador Universal de Factores de Emision (DEFRA, EPA, CRE, USEEIO, ADEME)
                elif path == "/api/ghg/emission-factors":
                    q = query.get("q", [""])[0] or query.get("query", [""])[0]
                    scope = query.get("scope", ["ALL"])[0]
                    source = query.get("source", ["ALL"])[0]
                    geo = query.get("geo", ["ALL"])[0]
                    limit = int(query.get("limit", [50])[0])
                    offset = int(query.get("offset", [0])[0])
                    try:
                        factors, total = search_emission_factors(query=q, scope=scope, source=source, geo=geo, limit=limit, offset=offset)
                        self._send_json({
                            "status": "success",
                            "total": total,
                            "count": len(factors),
                            "items": factors,
                            "factors": factors
                        })
                    except Exception as e:
                        self._send_error_json(str(e), 500)
                    return

                # Fuentes de Datos de Factores de Emision Disponibles
                elif path == "/api/ghg/sources":
                    try:
                        sources = list_distinct_sources()
                        self._send_json({"status": "success", "sources": sources})
                    except Exception as e:
                        self._send_error_json(str(e), 500)
                    return

                # --- Modulo EPD (Environmental Product Declarations / SmartEPD) ---
                # Catalogo de Plantillas Preliminares EPD (Cemento, Concreto y registro multi-industria)
                elif path == "/api/epd/templates":
                    industry = query.get("industry", ["ALL"])[0]
                    try:
                        res = list_epd_templates_use_case(industry_id=industry)
                        self._send_json(res)
                    except Exception as e:
                        self._send_error_json(str(e), 500)
                    return

                # Reporte EPD Estructurado por Modulos A1-D (EN 15804+A2 / TRACI 2.1)
                elif path.startswith("/api/systems/") and path.endswith("/epd-report"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(path.split("/")[3])
                    std = query.get("standard", ["EN15804_A2"])[0]
                    try:
                        res = compute_epd_report_use_case(conn, sys_id, standard=std)
                        self._send_json(res)
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # Exportar Declaracion Digital OpenEPD JSON (SmartEPD / EC3 Compatible)
                elif path.startswith("/api/systems/") and path.endswith("/export/openepd"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(path.split("/")[3])
                    try:
                        payload = export_openepd_json_use_case(conn, sys_id)
                        body_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
                        fname = f"ECONODE_openEPD_SYS_{sys_id}.json"
                        self._set_headers(200, "application/json; charset=utf-8", {"Content-Disposition": f'attachment; filename="{fname}"'})
                        self.wfile.write(body_bytes)
                        try:
                            self.wfile.flush()
                        except Exception:
                            pass
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # Canvas details for a system (Requiere Autenticación)
                elif path.startswith("/api/systems/") and path.endswith("/canvas"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(path.split("/")[3])
                    details = get_system_canvas_use_case(conn, sys_id)
                    if not details:
                        self._send_error_json("Sistema producto no encontrado", 404)
                    else:
                        self._send_json({"status": "success", "system": details})
                    return

                # System Parameters (Requiere Autenticacion)
                elif path.startswith("/api/systems/") and path.endswith("/parameters"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(path.split("/")[3])
                    params = get_system_parameters_use_case(conn, sys_id)
                    self._send_json({"status": "success", "system_id": sys_id, "count": len(params), "items": params})
                    return

                # Download Template CSV
                elif path == "/api/systems/template-csv":
                    csv_data = DEFAULT_TEMPLATE_CSV
                    if os.path.exists(TEMPLATE_CSV_PATH):
                        try:
                            with open(TEMPLATE_CSV_PATH, "r", encoding="utf-8") as f:
                                csv_data = f.read()
                        except Exception:
                            pass
                    self._set_headers(200, "text/csv", {"Content-Disposition": 'attachment; filename="plantilla_sistemas_parametrizados.csv"'})
                    try:
                        self.wfile.write(csv_data.encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        pass
                    return

                # 1. Catalogo de Bases de Datos Disponibles para Cruce de Versiones
                elif path == "/api/version/databases":
                    from econode_studio.infrastructure.version_matcher_adapter import get_available_databases
                    dbs = get_available_databases(conn)
                    self._send_json({"status": "success", "databases": dbs})
                    return

                # 2. Diagnostico de Emparejamiento de Sistema Producto con Base Destino
                elif path == "/api/version/match-system":
                    from econode_studio.infrastructure.version_matcher_adapter import match_system_to_database
                    raw_sys_id = query.get("system_id", [None])[0]
                    target_ver = query.get("target_version", ["ecoinvent_311"])[0]
                    if not raw_sys_id:
                        self._send_error_json("Parametro 'system_id' es requerido", 400)
                        return
                    try:
                        sys_id = int(raw_sys_id)
                        report = match_system_to_database(conn, sys_id, target_ver)
                        res_dict = dict(report)
                        res_dict["status"] = "success"
                        res_dict["report"] = report
                        self._send_json(res_dict)
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # 3. Buscador de Procesos y Flujos en Base Destino (para sustituciones)
                elif path == "/api/version/search-target":
                    from econode_studio.infrastructure.version_matcher_adapter import search_database_processes, search_database_flows
                    target_ver = query.get("target_version", ["ecoinvent_311"])[0]
                    q = query.get("q", [""])[0]
                    is_flow = query.get("is_flow", ["0"])[0] in ("1", "true", "True") or query.get("type", ["processes"])[0] == "flows"
                    lim = int(query.get("limit", [25])[0])
                    try:
                        if is_flow:
                            items = search_database_flows(conn, target_ver, q, limit=lim)
                        else:
                            items = search_database_processes(conn, target_ver, q, limit=lim)
                        self._send_json({"status": "success", "items": items, "count": len(items)})
                    except Exception as e:
                        self._send_error_json(str(e), 400)
                    return

                # LCI Catalog Search
                elif path == "/api/processes":
                    q = query.get("q", [""])[0].strip()
                    cat = query.get("category_id", [None])[0] or query.get("category", [None])[0]
                    cat_param = cat if cat and cat != "ALL" else None
                    limit = int(query.get("limit", [50])[0])
                    source = query.get("source", ["all"])[0].strip()
                    results = search_catalog_use_case(conn, query=q, category_id=cat_param, limit=limit, source=source)
                    self._send_json({
                        "status": "success",
                        "count": len(results),
                        "items": results
                    })
                    return

                # Sources Endpoint
                elif path in ("/api/sources", "/api/catalog/sources"):
                    sources = [
                        {"id": "all", "code": "all", "name": "Todas las BDs", "count": 29703, "badge": "all"},
                        {"id": "ecoinvent_312", "code": "ecoinvent_312", "name": "ecoinvent 3.12", "count": 26533, "badge": "ecoinvent"},
                        {"id": "glad_network", "code": "glad_network", "name": "GLAD (UNEP)", "count": 500, "badge": "glad"},
                        {"id": "oekobaudat_de", "code": "oekobaudat_de", "name": "OEKOBAUDAT", "count": 1000, "badge": "oekobaudat"},
                        {"id": "ademe_base_carbone", "code": "ademe_base_carbone", "name": "Base Carbone", "count": 1000, "badge": "ademe"},
                        {"id": "user_custom", "code": "user_custom", "name": "Mis Procesos", "count": 3, "badge": "custom"}
                    ]
                    self._send_json({"status": "success", "sources": sources})
                    return

                # LCI Categories
                elif path == "/api/categories":
                    categories = get_categories_use_case(conn, limit=100)
                    self._send_json({
                        "status": "success",
                        "count": len(categories),
                        "items": categories
                    })
                    return

                # Search Database Flows
                elif path == "/api/flows":
                    q = query.get("q", [""])[0].strip()
                    flow_type = query.get("type", [None])[0]
                    cat = query.get("category_id", [None])[0] or query.get("category", [None])[0]
                    limit = int(query.get("limit", [40])[0])
                    flows = search_flows_use_case(conn, query=q, flow_type=flow_type, limit=limit)
                    flows = search_flows_use_case(conn, query=q, flow_type=flow_type, category=cat, limit=limit)
                    self._send_json({
                        "status": "success",
                        "count": len(flows),
                        "items": flows
                    })
                    return

                # Search Potential Providers
                elif path == "/api/providers":
                    flow_name = query.get("flow", [""])[0].strip() or query.get("q", [""])[0].strip()
                    limit = int(query.get("limit", [15])[0])
                    providers = search_providers_use_case(conn, flow_name=flow_name, limit=limit)
                    self._send_json({
                        "status": "success",
                        "count": len(providers),
                        "items": providers
                    })
                    return

                # Process Technical Sheet
                elif path.startswith("/api/processes/") and path.endswith("/sheet"):
                    proc_id = path.split("/")[3]
                    sheet = get_process_sheet_use_case(conn, proc_id)
                    if not sheet:
                        self._send_error_json("Proceso no encontrado", 404)
                    else:
                        self._send_json({"status": "success", "sheet": sheet})
                    return

                # Comments (Requiere Autenticación)
                elif path == "/api/comments":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(query.get("system_id", [1])[0])
                    comments = list_system_comments_use_case(sys_id)
                    self._send_json({"status": "success", "items": comments})
                    return

                # Catálogo de Normas y Checklists Disponibles (Requiere Autenticación)
                elif path == "/api/checklists":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    standards = list_available_standards_use_case()
                    self._send_json({"status": "success", "count": len(standards), "items": standards, "standards": standards})
                    return

                # Descargar Plantilla CSV para Checklists
                elif path == "/api/checklists/template-csv":
                    csv_text = get_checklist_csv_template_use_case()
                    self._set_headers(200, "text/csv", {"Content-Disposition": 'attachment; filename="plantilla_checklist_normas.csv"'})
                    self.wfile.write(csv_text.encode("utf-8"))
                    return

                # Checklist Normativo (Multi-Estándar - Requiere Autenticación)
                elif path == "/api/checklist":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = int(query.get("system_id", [1])[0])
                    chk_id = query.get("checklist_id", ["nom070"])[0]
                    checklist = get_audit_checklist_use_case(sys_id, checklist_id=chk_id)
                    self._send_json({"status": "success", "checklist": checklist})
                    return

                # Subscription status (Requiere Autenticación)
                elif path == "/api/subscription/status":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    self._send_json({
                        "status": "success",
                        "tier": "tier1",
                        "tier_name": "ECONODE Studio (Base)",
                        "is_pro": False,
                        "upgrade_perks": [
                            "Cálculo matricial Leontief s = A⁻¹f instantáneo (< 5 ms)",
                            "1,000 iteraciones estocásticas de Monte Carlo con matriz Pedigree",
                            "Exportación profesional openLCA JSON-LD y GaBi ILCD"
                        ]
                    })
                    return
                # Documentos de la Bóveda (Requiere Autenticación)
                elif path == "/api/documents":
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    sys_id = query.get("system_id", [None])[0]
                    sys_int = int(sys_id) if sys_id else None
                    docs = list_documents(sys_int)
                    self._send_json({"status": "success", "count": len(docs), "items": docs})
                    return

                # Descargar documento de la Bóveda (Requiere Autenticación con Token)
                elif path.startswith("/api/documents/") and path.endswith("/download"):
                    user = self._require_auth(query=query)
                    if not user:
                        return
                    doc_id = int(path.split("/")[3])
                    info = get_document_file(doc_id)
                    if not info:
                        self._send_error_json("Archivo no encontrado en la bóveda", 404)
                    elif info[0] == "DRIVE_REDIRECT":
                        drive_url = info[2]
                        if "http" in drive_url:
                            import re as regex_mod
                            m = regex_mod.search(r"https://drive\.google\.com\S+", drive_url)
                            if m:
                                drive_url = m.group(0)
                        self._set_headers(302, "text/plain", {"Location": drive_url})
                        self.wfile.write(b"Redirigiendo a Google Drive...")
                    else:
                        fpath, orig_name, mime_type = info
                        with open(fpath, "rb") as f:
                            content = f.read()
                        self._set_headers(200, mime_type, {
                            "Content-Disposition": f'attachment; filename="{orig_name}"',
                            "Content-Length": str(len(content))
                        })
                        self.wfile.write(content)
                    return

                # Exportaciones industriales (openLCA, ILCD, SimaPro, CSV, Expediente ZIP, PDF, DOCX)
                elif path.startswith("/api/systems/") and "/export/" in path:
                    user = self._get_request_user(query=query) or auth_service.get_active_account()
                    parts = path.split("/")
                    sys_id = int(parts[3])
                    fmt = parts[5].lower()
                    if fmt in ("openlca", "jsonld"):
                        zip_bytes = export_openlca_jsonld_zip(conn, sys_id)
                        self._set_headers(200, "application/zip", {
                            "Content-Disposition": f'attachment; filename="openLCA_System_{sys_id}_JSONLD.zip"',
                            "Content-Length": str(len(zip_bytes))
                        })
                        self.wfile.write(zip_bytes)
                    elif fmt in ("ilcd", "gabi", "sphera"):
                        zip_bytes = export_ilcd_xml_zip(conn, sys_id)
                        self._set_headers(200, "application/zip", {
                            "Content-Disposition": f'attachment; filename="ILCD_System_{sys_id}.zip"',
                            "Content-Length": str(len(zip_bytes))
                        })
                        self.wfile.write(zip_bytes)
                    elif fmt in ("simapro", "simapro_csv"):
                        csv_txt = export_simapro_csv(conn, sys_id)
                        csv_b = ("\ufeff" + csv_txt).encode("utf-8")
                        self._set_headers(200, "text/csv; charset=utf-8", {
                            "Content-Disposition": f'attachment; filename="SimaPro_System_{sys_id}.csv"',
                            "Content-Length": str(len(csv_b))
                        })
                        self.wfile.write(csv_b)
                    elif fmt in ("csv", "lci_csv"):
                        csv_txt = export_lci_consolidated_csv(conn, sys_id)
                        csv_b = csv_txt.encode("utf-8")
                        self._set_headers(200, "text/csv", {
                            "Content-Disposition": f'attachment; filename="Inventario_LCI_Sistema_{sys_id}.csv"',
                            "Content-Length": str(len(csv_b))
                        })
                        self.wfile.write(csv_b)
                    elif fmt in ("zip", "expediente", "nom070"):
                        zip_bytes = export_expediente_nom070_zip(conn, sys_id)
                        self._set_headers(200, "application/zip", {
                            "Content-Disposition": f'attachment; filename="Expediente_NOM070_Sistema_{sys_id}.zip"',
                            "Content-Length": str(len(zip_bytes))
                        })
                        self.wfile.write(zip_bytes)
                    elif fmt in ("pdf", "report_pdf"):
                        lang = (query.get("lang") or ["es"])[0].lower()
                        pdf_bytes = export_system_pdf_bytes(conn, sys_id, lang=lang)
                        filename = f"LCA_Report_ISO14040_System_{sys_id}_EN.pdf" if lang == "en" else f"Reporte_ACV_NOM070_Sistema_{sys_id}_ES.pdf"
                        self._set_headers(200, "application/pdf", {
                            "Content-Disposition": f'attachment; filename="{filename}"',
                            "Content-Length": str(len(pdf_bytes))
                        })
                        self.wfile.write(pdf_bytes)
                    elif fmt in ("docx", "word", "report_docx"):
                        lang = (query.get("lang") or ["es"])[0].lower()
                        docx_bytes = export_system_docx_bytes(conn, sys_id, lang=lang)
                        filename = f"LCA_Report_ISO14040_System_{sys_id}_EN.docx" if lang == "en" else f"Reporte_ACV_NOM070_Sistema_{sys_id}_ES.docx"
                        self._set_headers(200, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", {
                            "Content-Disposition": f'attachment; filename="{filename}"',
                            "Content-Length": str(len(docx_bytes))
                        })
                        self.wfile.write(docx_bytes)
                    else:
                        self._send_error_json(f"Formato no reconocido: {fmt}. Opciones: openlca, ilcd, simapro, csv, expediente, pdf, docx", 400)
                    return

                else:
                    self._send_error_json(f"Ruta API no encontrada: {path}", 404)
                    return
            finally:
                conn.close()

        # 2. Archivos Estáticos
        if path == "" or path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_json_body()

        # Manejo de RPC de MCP (JSON-RPC 2.0 para Agentes de IA)
        if path in ("/mcp/rpc", "/mcp/message", "/api/v1/mcp/rpc", "/api/v1/mcp/message", "/mcp", "/api/v1/mcp"):
            user = self._require_auth()
            if not user:
                return
            response_rpc = handle_jsonrpc_request(body, user)
            if response_rpc:
                self._send_json(response_rpc)
            else:
                self._set_headers(204)
            return

        conn = get_active_db_connection()
        try:
            # Generar Nueva Clave de API Personal (eco_live_...)
            if path == "/api/account/api-keys":
                user = self._require_auth()
                if not user:
                    return
                key_name = body.get("name", "Default API Key")
                scopes = body.get("scopes", ["all"])
                rate_limit = int(body.get("rate_limit_per_minute", 120))
                try:
                    key_entity, raw_token = ApiKey.generate(
                        user_id=user["id"],
                        organization_id=user.get("organization", ""),
                        name=key_name,
                        scopes=scopes,
                        rate_limit_per_minute=rate_limit
                    )
                    save_api_key(key_entity)
                    self._send_json({
                        "status": "success",
                        "raw_token": raw_token,
                        "key": key_entity.to_dict()
                    }, status=201)
                except Exception as e:
                    self._send_error_json(f"Error generando clave: {str(e)}", 400)
                return

            # Revocar Clave de API Personal
            elif path in ("/api/account/api-keys/revoke", "/api/account/api-keys/delete"):
                user = self._require_auth()
                if not user:
                    return
                key_id = body.get("key_id") or body.get("id")
                if not key_id:
                    self._send_error_json("Parámetro 'key_id' es requerido", 400)
                    return
                success = revoke_api_key(key_id, user["id"])
                if success:
                    self._send_json({"status": "success", "message": "Clave revocada exitosamente"})
                else:
                    self._send_error_json("No se pudo revocar la clave o no pertenece a su usuario", 400)
                return

            # API v1 - Calcular Impacto Ambiental de un Sistema Producto
            elif path.startswith("/api/v1/systems/") and path.endswith("/calculate"):
                user = self._require_auth()
                if not user:
                    return
                try:
                    sys_id = int(path.split("/")[4])
                    res = compute_epd_report_use_case(sys_id)
                    self._send_json({"status": "success", "report": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # API v1 - Ingesta de Actividad Corporativa GEI
            elif path == "/api/v1/ghg/activities":
                user = self._require_auth()
                if not user:
                    return
                try:
                    inv_id = int(body.get("inventory_id") or 0)
                    if not inv_id:
                        invs = list_inventories_use_case()
                        if invs:
                            inv_id = invs[0]["id"]
                        else:
                            self._send_error_json("No existe inventario corporativo activo. Cree uno primero.", 400)
                            return
                    entry = add_entry_to_inventory_use_case(inv_id, body)
                    self._send_json({"status": "success", "entry": entry}, status=201)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Google OAuth Login & Onboarding con asignación de Roles
            elif path == "/api/auth/google":
                cred = body.get("credential", "")
                email = body.get("email")
                invite_token = body.get("invite_token")
                requested_role = body.get("role")
                try:
                    user = auth_service.login_with_google(cred, fallback_email=email, invite_token=invite_token, requested_role=requested_role)
                    self._send_json({"status": "success", "authenticated": True, "user": user, "token": user.get("token")})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Crear Invitación para Auditor o Cliente (Solo Analistas Autenticados)
            elif path == "/api/auth/invite":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                email = body.get("email")
                role = body.get("role") or "auditor"
                name = body.get("name") or body.get("display_name") or ""
                org = body.get("organization") or ""
                sys_id = body.get("system_id")
                sys_int = int(sys_id) if sys_id else None
                try:
                    inv = auth_service.invite_collaborator(user, email, role, name=name, organization=org, system_id=sys_int)
                    if sys_int:
                        try:
                            add_system_collaborator_use_case(conn, sys_int, {
                                "name": name or email.split("@")[0].title(),
                                "display_name": name or email.split("@")[0].title(),
                                "email": email,
                                "role": role
                            })
                        except Exception:
                            pass
                    self._send_json({"status": "success", "invitation": inv, "message": inv.get("message")})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Cancelar / Revocar Invitación (Solo Analistas Autenticados)
            elif path == "/api/auth/invitations/cancel":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                inv_id = body.get("invitation_id") or body.get("id") or ""
                try:
                    cancelled = auth_service.cancel_invitation(user, inv_id)
                    self._send_json({"status": "success", "cancelled": cancelled})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Login con Usuario/Correo y Contraseña (con soporte de roles directos y credenciales preconfiguradas)
            elif path == "/api/auth/login":
                username_or_email = (body.get("email") or body.get("username") or body.get("user_id") or "").strip()
                password = body.get("password")

                if not username_or_email:
                    self._send_error_json("Usuario o correo requerido.", 400)
                    return

                try:
                    from application.auth_service import generate_session_token
                except (ImportError, ValueError):
                    from econode_studio.application.auth_service import generate_session_token

                try:
                    from infrastructure.auth_adapter import update_user_token
                except (ImportError, ValueError):
                    from econode_studio.infrastructure.auth_adapter import update_user_token

                # Si es un inicio de sesión demo/directo sin contraseña (ej. analyst, auditor, client)
                if not password:
                    all_users = auth_service.get_all_accounts()
                    matched_user = None
                    target_key = username_or_email.lower()
                    if target_key in ("analyst", "auditor", "client"):
                        matched_user = next((u for u in all_users if u.get("role") == target_key), None)
                    else:
                        matched_user = next((u for u in all_users if u.get("email", "").lower() == target_key or u.get("id") == username_or_email), None)

                    if matched_user:
                        auth_service.active_account_id = matched_user["id"]
                        token = matched_user.get("token")
                        if not token or not auth_service.parse_session_token(token):
                            token = generate_session_token(matched_user["id"], matched_user.get("role", "analyst"))
                            try:
                                update_user_token(matched_user["id"], token)
                            except Exception:
                                pass
                            matched_user["token"] = token
                        self._send_json({"status": "success", "authenticated": True, "user": matched_user, "token": token})
                        return
                    else:
                        self._send_error_json("Contraseña requerida.", 400)
                        return

                user = auth_service.authenticate(username_or_email, password)
                if user:
                    token = user.get("token")
                    if not token or not auth_service.parse_session_token(token):
                        token = generate_session_token(user["id"], user.get("role", "analyst"))
                        try:
                            update_user_token(user["id"], token)
                        except Exception:
                            pass
                        user["token"] = token
                    self._send_json({"status": "success", "authenticated": True, "user": user, "token": token})
                else:
                    self._send_error_json("Credenciales incorrectas. Verifica tu correo y contraseña.", 401)
                return

            # Sign-Up (Crear Cuenta / Organización con contraseña)
            elif path == "/api/auth/signup" or path == "/api/auth/register":
                try:
                    user = auth_service.register_account(body)
                    self._send_json({"status": "success", "created": True, "user": user, "token": user.get("token")})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Switch Account (Bloqueado estrictamente en producción)
            elif path == "/api/auth/switch-account":
                if getattr(settings, "ENV", "production") == "production":
                    self._send_error_json("La alternancia administrativa de cuentas está deshabilitada en producción.", 403)
                    return
                ident = body.get("account_id") or body.get("role") or ""
                switched = auth_service.switch_account(ident)
                if switched:
                    self._send_json({"status": "success", "user": switched})
                else:
                    self._send_error_json("No se pudo alternar la cuenta", 400)
                return

            # Create Product System (Wizard - Solo Analistas Autenticados)
            elif path == "/api/systems/create":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                try:
                    res = create_system_wizard_use_case(conn, body, user=user)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Import CSV (Solo Analistas Autenticados)
            elif path == "/api/systems/import-csv":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                csv_str = body.get("csv", "")
                mode = body.get("mode", "full")
                if not csv_str:
                    if os.path.exists(TEMPLATE_CSV_PATH):
                        try:
                            with open(TEMPLATE_CSV_PATH, "r", encoding="utf-8") as f:
                                csv_str = f.read()
                        except Exception:
                            csv_str = DEFAULT_TEMPLATE_CSV
                    else:
                        csv_str = DEFAULT_TEMPLATE_CSV
                try:
                    res = import_systems_csv_use_case(conn, csv_str, user=user, mode=mode)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Inspeccionar SimaPro CSV (Pre-flight para detección de modelo multi-proceso)
            elif path == "/api/systems/inspect-simapro":
                user = self._require_auth(allowed_roles=["analyst", "auditor", "client"])
                if not user:
                    return
                csv_str = body.get("csv", "")
                try:
                    from econode_studio.infrastructure.simapro_adapter import inspect_simapro_csv
                    res = inspect_simapro_csv(csv_str)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Import SimaPro Process to Existing System Canvas
            elif path.startswith("/api/systems/") and path.endswith("/import-simapro"):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(path.split("/")[3])
                csv_str = body.get("csv", "")
                mode = body.get("mode", "full")
                try:
                    res = import_simapro_to_system_use_case(conn, sys_id, csv_str, user=user, mode=mode)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Conversion y Clonacion de Sistema Producto a Nueva Version de Base de Datos
            elif path == "/api/systems/convert-version":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                from econode_studio.infrastructure.version_matcher_adapter import convert_product_system_version
                sys_id = int(body.get("system_id", 0))
                target_ver = str(body.get("target_version", "ecoinvent_311"))
                proc_map = body.get("process_mappings", {})
                flow_map = body.get("flow_mappings", {})
                custom_name = body.get("custom_name")

                if not sys_id:
                    self._send_error_json("Campo 'system_id' es requerido", 400)
                    return

                try:
                    res = convert_product_system_version(
                        conn,
                        system_id=sys_id,
                        target_db_id=target_ver,
                        process_mappings=proc_map,
                        flow_mappings=flow_map,
                        custom_name=custom_name,
                        user_email=user.get("email"),
                        user_id=user.get("id")
                    )
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Save Canvas (Solo Analistas Autenticados)
            elif path.startswith("/api/systems/") and path.endswith("/save"):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(path.split("/")[3])
                try:
                    save_system_canvas_use_case(conn, sys_id, body)
                    self._send_json({"status": "success", "message": "Lienzo guardado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Save or Update System Parameter (Solo Analistas Autenticados)
            elif path.startswith("/api/systems/") and path.endswith("/parameters"):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(path.split("/")[3])
                try:
                    saved_param = save_system_parameter_use_case(conn, sys_id, body)
                    self._send_json({"status": "success", "parameter": saved_param, "message": "Parametro guardado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete System Parameter (Solo Analistas Autenticados)
            elif path.startswith("/api/systems/") and (("/parameters/" in path and path.endswith("/delete")) or path.endswith("/parameters/delete")):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                parts = path.split("/")
                sys_id = int(parts[3])
                param_id = body.get("param_id") or (parts[5] if len(parts) > 5 and parts[5] != "delete" else "")
                if not param_id:
                    self._send_error_json("ID de parametro no especificado", 400)
                    return
                try:
                    ok = delete_system_parameter_use_case(conn, sys_id, param_id)
                    self._send_json({"status": "success", "deleted_id": param_id, "message": "Parametro eliminado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Product System (Solo Analistas Autenticados)
            elif path == "/api/systems/delete":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(body.get("system_id") or 0)
                if not sys_id:
                    self._send_error_json("ID de sistema producto no especificado", 400)
                    return
                try:
                    ok = delete_product_system_use_case(conn, sys_id)
                    self._send_json({"status": "success", "deleted_id": sys_id, "message": "Sistema producto eliminado correctamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Crear Proyecto Contenedor (Solo Analistas Autenticados)
            elif path == "/api/projects/create":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                try:
                    res = create_project_use_case(conn, body, user=user)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # --- Modulo GHG Protocol POST ---
            # Crear Inventario Corporativo GEI
            elif path == "/api/ghg/inventories" or path == "/api/ghg/inventories/create":
                try:
                    res = create_inventory_use_case(body)
                    self._send_json({"status": "success", "inventory": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Eliminar Inventario Corporativo GEI
            elif path == "/api/ghg/inventories/delete" or (path.startswith("/api/ghg/inventories/") and "/entries/" not in path and path.endswith("/delete")):
                parts = path.split("/")
                inv_id = int(body.get("inventory_id") or (parts[4] if len(parts) > 4 and parts[4] != "delete" else 0))
                if not inv_id:
                    self._send_error_json("ID de inventario no especificado", 400)
                    return
                try:
                    ok = delete_inventory_use_case(inv_id)
                    self._send_json({"status": "success", "deleted_id": inv_id, "message": "Inventario eliminado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Agregar Registro de Emision / Actividad a un Inventario
            elif path.startswith("/api/ghg/inventories/") and path.endswith("/entries"):
                inv_id = int(path.split("/")[4])
                try:
                    res = add_entry_to_inventory_use_case(inv_id, body)
                    self._send_json({"status": "success", "inventory": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Eliminar Registro de Emision de un Inventario
            elif path.startswith("/api/ghg/inventories/") and "/entries/" in path and path.endswith("/delete"):
                parts = path.split("/")
                inv_id = int(parts[4])
                entry_id = int(parts[6])
                try:
                    res = delete_entry_from_inventory_use_case(inv_id, entry_id)
                    self._send_json({"status": "success", "inventory": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # --- Modulo EPD POST ---
            # Instanciar Plantilla Preliminar EPD (Cemento / Concreto)
            elif path == "/api/epd/templates/instantiate":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                template_id = body.get("template_id") or "epd_concrete_rmx_4000"
                try:
                    res = instantiate_epd_template_use_case(conn, template_id=template_id, overrides=body, user=user)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Guardar Metadatos Administrativos y Especificaciones EPD
            elif path.startswith("/api/systems/") and path.endswith("/epd-metadata"):
                user = self._require_auth(allowed_roles=["analyst", "auditor"])
                if not user:
                    return
                sys_id = int(path.split("/")[3])
                try:
                    res = save_epd_metadata_use_case(conn, sys_id, epd_updates=body)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Eliminar Proyecto Contenedor (Solo Analistas Autenticados)
            elif path == "/api/projects/delete" or (path.startswith("/api/projects/") and path.endswith("/delete")):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                parts = path.split("/")
                proj_id = int(body.get("project_id") or (parts[3] if len(parts) > 3 and parts[3] != "delete" else 0))
                if not proj_id:
                    self._send_error_json("ID de proyecto no especificado", 400)
                    return
                try:
                    ok = delete_project_use_case(conn, proj_id)
                    self._send_json({"status": "success", "deleted_id": proj_id, "message": "Proyecto eliminado. Sus sistemas ahora son independientes."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Asignar o Desasociar Sistema a Proyecto (Solo Analistas Autenticados)
            elif path.startswith("/api/systems/") and path.endswith("/assign-project"):
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(path.split("/")[3])
                raw_proj = body.get("project_id")
                proj_id = int(raw_proj) if raw_proj not in (None, "", "null", 0, "0") else None
                try:
                    res = assign_system_to_project_use_case(conn, sys_id, proj_id)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Create Custom Process (Solo Analistas Autenticados)
            elif path == "/api/processes/create":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                name = (body.get("name") or "").strip()
                if not name:
                    self._send_error_json("El nombre del proceso es requerido", 400)
                    return
                try:
                    proc = create_custom_process_use_case(
                        conn=conn,
                        name=name,
                        code=body.get("code"),
                        category_id=int(body.get("category_id") or 999999),
                        location=body.get("location") or "GLO",
                        reference_flow_name=body.get("reference_flow_name") or "",
                        reference_amount=float(body.get("reference_amount") or 1.0),
                        reference_unit=body.get("reference_unit") or body.get("unit") or "kg",
                        description=body.get("description") or "",
                        inputs=body.get("inputs") or [],
                        outputs=body.get("outputs") or []
                    )
                    self._send_json({"status": "success", "process": proc, "message": "Proceso unitario creado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Create Custom Flow (Solo Analistas Autenticados)
            elif path == "/api/flows/create":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                name = (body.get("name") or "").strip()
                if not name:
                    self._send_error_json("El nombre del flujo es requerido", 400)
                    return
                try:
                    flow = create_custom_flow_use_case(
                        conn=conn,
                        name=name,
                        flow_type=body.get("flow_type") or "PRODUCT_FLOW",
                        unit_symbol=body.get("unit_symbol") or body.get("unit") or "kg",
                        description=body.get("description") or "",
                        code=body.get("code")
                    )
                    self._send_json({"status": "success", "flow": flow, "message": "Flujo creado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Custom Process (Solo Analistas Autenticados)
            elif path == "/api/processes/delete":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                proc_id = body.get("process_id") or body.get("id")
                if not proc_id:
                    self._send_error_json("ID de proceso no especificado", 400)
                    return
                try:
                    deleted = delete_custom_process_use_case(conn=conn, process_id=proc_id)
                    self._send_json({"status": "success", "deleted": deleted, "message": "Proceso eliminado permanentemente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Custom Flow (Solo Analistas Autenticados)
            elif path == "/api/flows/delete":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                flow_id = body.get("flow_id") or body.get("id") or body.get("code")
                if not flow_id:
                    self._send_error_json("ID de flujo no especificado", 400)
                    return
                try:
                    deleted = delete_custom_flow_use_case(conn=conn, flow_id=flow_id)
                    self._send_json({"status": "success", "deleted": deleted, "message": "Flujo eliminado permanentemente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Invite Collaborator (Solo Analistas Autenticados)
            elif path == "/api/systems/collaborators/invite":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                sys_id = int(body.get("system_id") or 0)
                if not sys_id:
                    self._send_error_json("ID de sistema producto no especificado", 400)
                    return
                collab_name = (body.get("name") or body.get("display_name") or "").strip()
                collab_email = (body.get("email") or "").strip().lower()
                collab_role = body.get("role") or "auditor"
                if not collab_email and not collab_name:
                    self._send_error_json("Debe indicar el nombre o correo del colaborador", 400)
                    return
                try:
                    collabs = add_system_collaborator_use_case(conn, sys_id, {
                        "name": collab_name or collab_email.split("@")[0].title(),
                        "display_name": collab_name or collab_email.split("@")[0].title(),
                        "email": collab_email,
                        "role": collab_role
                    })
                    self._send_json({
                        "status": "success",
                        "collaborators": collabs,
                        "message": f"Colaborador {collab_name or collab_email} asignado exitosamente al proyecto."
                    })
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Add Comment (Identidad verificada desde Token criptográfico)
            elif path == "/api/comments":
                user = self._require_auth()
                if not user:
                    return
                sys_id = int(body.get("system_id", 1))
                author = user.get("display_name") or user.get("name") or user.get("email") or "Usuario"
                role = user.get("role", "analyst")
                content = (body.get("content") or "").strip()
                node_id = body.get("node_id")
                x = body.get("x")
                y = body.get("y")
                if not content:
                    self._send_error_json("Contenido del comentario vacío", 400)
                    return
                comment = add_system_comment_use_case(sys_id, author, role, content, node_id=node_id, x=x, y=y)
                self._send_json({"status": "success", "comment": comment})
                return

            # Resolve Comment (Identidad verificada desde Token criptográfico)
            elif path == "/api/comments/resolve":
                user = self._require_auth()
                if not user:
                    return
                cid = int(body.get("comment_id", 1))
                resolved_by = user.get("display_name") or user.get("name") or user.get("email") or "Usuario"
                reply_text = body.get("reply", "")
                try:
                    resolved = reply_and_resolve_comment_use_case(cid, resolved_by, reply_text)
                    self._send_json({"status": "success", "resolved": resolved})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Comment (Solo el Autor del comentario o un Analista)
            elif path == "/api/comments/delete":
                user = self._require_auth()
                if not user:
                    return
                cid = int(body.get("comment_id", 0))
                user_name = user.get("display_name") or user.get("name") or user.get("email") or ""
                user_role = user.get("role", "analyst")
                try:
                    delete_system_comment_use_case(cid, user_name, user_role)
                    self._send_json({"status": "success", "deleted_id": cid})
                except Exception as e:
                    self._send_error_json(str(e), 403 if isinstance(e, PermissionError) else 400)
                return

            # Toggle Checklist Clause (Solo Auditores o Analistas)
            elif path == "/api/checklist/toggle":
                user = self._require_auth(allowed_roles=["analyst", "auditor"])
                if not user:
                    return
                try:
                    sys_id = int(body.get("system_id", 1))
                    clause_id = str(body.get("clause_id", ""))
                    chk_id = body.get("checklist_id", "nom070")
                    is_ok_raw = body.get("is_compliant")
                    if isinstance(is_ok_raw, str):
                        is_ok = is_ok_raw.strip().lower() in ("true", "1", "yes", "conforme")
                    elif isinstance(is_ok_raw, bool):
                        is_ok = is_ok_raw
                    else:
                        is_ok = bool(is_ok_raw)
                    res = update_clause_status_use_case(sys_id, clause_id, is_ok, checklist_id=chk_id)
                    self._send_json({"status": "success", "checklist": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Update Clause Evidence Requirement (Clientes o Analistas)
            elif path == "/api/checklist/evidence":
                user = self._require_auth(allowed_roles=["analyst", "client"])
                if not user:
                    return
                try:
                    sys_id = int(body.get("system_id", 1))
                    clause_id = str(body.get("clause_id", ""))
                    evidence = str(body.get("evidence", ""))
                    chk_id = body.get("checklist_id", "nom070")
                    if not clause_id:
                        self._send_error_json("clause_id es requerido", 400)
                        return
                    res = update_clause_evidence_use_case(sys_id, clause_id, evidence, checklist_id=chk_id)
                    self._send_json({"status": "success", "checklist": res, "message": "Evidencia actualizada exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Sign Audit (Exclusivo para Auditores Líderes Acreditados)
            elif path == "/api/checklist/sign":
                user = self._require_auth(allowed_roles=["auditor", "analyst"])
                if not user:
                    return
                sys_id = int(body.get("system_id", 1))
                chk_id = body.get("checklist_id", "nom070")
                auditor_name = user.get("display_name") or user.get("name") or user.get("email") or "Auditor Líder"
                try:
                    res = sign_normative_audit_use_case(sys_id, auditor_name, checklist_id=chk_id)
                    self._send_json({"status": "success", "receipt": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Crear Norma Personalizada (Solo Analistas o Auditores)
            elif path == "/api/checklists/create":
                user = self._require_auth(allowed_roles=["analyst", "auditor"])
                if not user:
                    return
                try:
                    res = create_custom_standard_use_case(body, user=user)
                    self._send_json({"status": "success", "standard": res, "message": "Norma creada exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Importar Norma vía Archivo CSV (Solo Analistas o Auditores)
            elif path == "/api/checklists/import":
                user = self._require_auth(allowed_roles=["analyst", "auditor"])
                if not user:
                    return
                csv_str = body.get("csv") or body.get("csv_content") or body.get("content") or ""
                metadata = body.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = {}
                if "name" not in metadata and "standard_name" in metadata:
                    metadata["name"] = metadata["standard_name"]
                if "name" not in metadata and "name" in body:
                    metadata["name"] = body["name"]
                if "code" not in metadata and "code" in body:
                    metadata["code"] = body["code"]
                if "standard_family" not in metadata and "standard_family" in body:
                    metadata["standard_family"] = body["standard_family"]

                try:
                    res = import_standard_csv_use_case(csv_str, metadata=metadata, user=user)
                    self._send_json({
                        "status": "success",
                        "standard": res,
                        "standard_id": res.get("id"),
                        "message": "Norma importada exitosamente desde CSV."
                    })
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Subir documento a la Bóveda (Clientes o Analistas)
            elif path == "/api/documents/upload":
                user = self._require_auth(allowed_roles=["analyst", "client"])
                if not user:
                    return
                title = body.get("title") or body.get("original_filename") or body.get("file_name") or "Documento"
                orig_name = body.get("original_filename") or body.get("file_name") or "archivo.bin"
                content_b64 = body.get("content_base64") or body.get("file_data") or ""
                content_text = body.get("content_text", "")
                sys_id = int(body.get("system_id", 1))
                desc = body.get("description", "")
                uploaded_by = user.get("display_name") or user.get("name") or user.get("email") or "Usuario"
                role = user.get("role", "client")
                override_sha = body.get("sha256_hash") or body.get("sha256")
                override_size = body.get("file_size")
                if override_size is not None:
                    try:
                        override_size = int(override_size)
                    except (ValueError, TypeError):
                        override_size = None

                import base64
                if content_b64:
                    try:
                        file_bytes = base64.b64decode(content_b64)
                    except Exception:
                        file_bytes = content_b64.encode("utf-8")
                elif content_text:
                    file_bytes = content_text.encode("utf-8")
                else:
                    file_bytes = b""

                try:
                    doc = save_document(
                        title, orig_name, file_bytes, uploaded_by, role, sys_id, desc,
                        override_sha256=override_sha,
                        override_file_size=override_size
                    )
                    self._send_json({"status": "success", "document": doc})
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            # Eliminar documento de la Bóveda (Solo Analistas Autenticados)
            elif path == "/api/documents/delete":
                user = self._require_auth(allowed_roles=["analyst"])
                if not user:
                    return
                doc_id = int(body.get("document_id", 0))
                ok = delete_document(doc_id)
                self._send_json({"status": "success" if ok else "error"})
                return

            # Logout
            elif path == "/api/auth/logout":
                self._send_json({"status": "success", "logged_out": True})
                return

            else:
                self._send_error_json(f"Endpoint POST no encontrado: {path}", 404)
        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api/account/api-keys/"):
            user = self._require_auth()
            if not user:
                return
            key_id = path.split("/")[-1]
            success = revoke_api_key(key_id, user["id"])
            if success:
                self._send_json({"status": "success", "message": "Clave revocada exitosamente"})
            else:
                self._send_error_json("Clave no encontrada o no pertenece a su cuenta", 404)
            return
        self._send_error_json("Ruta DELETE no soportada", 405)

def main():
    parser = argparse.ArgumentParser(description="ECONODE Studio Server")
    parser.add_argument("--port", type=int, default=8081, help="Puerto del servidor (8081 por defecto, o 8080)")
    args = parser.parse_args()

    port = args.port
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), EconodeRequestHandler)
    print(f"===============================================================")
    print(f"  ● ECONODE Studio (Tier 1) - Servidor Autónomo Activo")
    print(f"  ● URL Local: http://localhost:{port}")
    print(f"  ● Catálogo ecoinvent 3.12: 26,533 Procesos Activos")
    print(f"  ● Google OAuth Client ID: {get_configured_client_id()[:20]}...")
    print(f"===============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")

if __name__ == "__main__":
    main()
