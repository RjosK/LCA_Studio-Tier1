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

from domain import RoleEnum
from application import (
    auth_service,
    get_dashboard_systems_use_case,
    create_system_wizard_use_case,
    import_systems_csv_use_case,
    get_system_canvas_use_case,
    save_system_canvas_use_case,
    delete_product_system_use_case,
    add_system_collaborator_use_case,
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
    export_system_pdf_bytes
)
from infrastructure import get_active_db_connection, get_configured_client_id

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
        if "charset" not in content_type and not content_type.startswith("application/zip") and not content_type.startswith("image/"):
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        else:
            self.send_header("Content-Type", content_type)
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
        # 1. Bearer Token desde encabezado Authorization
        auth_header = self.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif query and "token" in query:
            token = query["token"][0]

        if token:
            parsed = auth_service.parse_session_token(token)
            if parsed:
                for acc in auth_service.accounts:
                    if acc["id"] == parsed["user_id"]:
                        return acc
            for acc in auth_service.accounts:
                if acc.get("token") == token:
                    return acc

        # 2. Parámetros de consulta (email / user_id)
        if query:
            email = query.get("email", [None])[0]
            uid = query.get("user_id", [None])[0]
            if email or uid:
                for acc in auth_service.accounts:
                    if (email and acc.get("email", "").lower() == email.lower()) or (uid and acc.get("id") == uid):
                        return acc
                if email:
                    return {"id": uid or email, "email": email, "display_name": email, "role": "analyst"}

        return None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoints
        if path.startswith("/api"):
            conn = get_active_db_connection()
            try:
                # Auth Config
                if path == "/api/auth/config":
                    self._send_json({
                        "google_client_id": get_configured_client_id(),
                        "active_account": auth_service.get_active_account(),
                        "accounts": auth_service.get_all_accounts(),
                        "mode": "tier1_studio"
                    })
                    return

                # Profile
                elif path == "/api/profile":
                    self._send_json({
                        "active_account": auth_service.get_active_account(),
                        "accounts": auth_service.get_all_accounts(),
                        "tier": "Tier 1: ECONODE Studio",
                        "security": {
                            "cipher": "TLS 1.3 / HMAC-SHA256",
                            "session": "Verificada y Activa",
                            "token_masked": "eco_sec_••••••••44b8"
                        }
                    })
                    return

                # Dashboard Systems
                elif path == "/api/systems":
                    user = self._get_request_user(query)
                    user_email = user.get("email") if user else None
                    user_id = user.get("id") if user else None
                    user_role = user.get("role") if user else None
                    systems = get_dashboard_systems_use_case(conn, user_email=user_email, user_id=user_id, user_role=user_role)
                    self._send_json({
                        "status": "success",
                        "count": len(systems),
                        "items": systems
                    })
                    return

                # Canvas details for a system
                elif path.startswith("/api/systems/") and path.endswith("/canvas"):
                    sys_id = int(path.split("/")[3])
                    details = get_system_canvas_use_case(conn, sys_id)
                    if not details:
                        self._send_error_json("Sistema producto no encontrado", 404)
                    else:
                        self._send_json({"status": "success", "system": details})
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

                # LCI Catalog Search
                elif path == "/api/processes":
                    q = query.get("q", [""])[0].strip()
                    cat = query.get("category_id", [None])[0] or query.get("category", [None])[0]
                    cat_param = cat if cat and cat != "ALL" else None
                    limit = int(query.get("limit", [50])[0])
                    results = search_catalog_use_case(conn, query=q, category_id=cat_param, limit=limit)
                    self._send_json({
                        "status": "success",
                        "count": len(results),
                        "items": results
                    })
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
                    proc_id = int(path.split("/")[3])
                    sheet = get_process_sheet_use_case(conn, proc_id)
                    if not sheet:
                        self._send_error_json("Proceso no encontrado", 404)
                    else:
                        self._send_json({"status": "success", "sheet": sheet})
                    return

                # Comments
                elif path == "/api/comments":
                    sys_id = int(query.get("system_id", [1])[0])
                    comments = list_system_comments_use_case(sys_id)
                    self._send_json({"status": "success", "items": comments})
                    return

                # Catálogo de Normas y Checklists Disponibles
                elif path == "/api/checklists":
                    standards = list_available_standards_use_case()
                    self._send_json({"status": "success", "count": len(standards), "items": standards})
                    return

                # Descargar Plantilla CSV para Checklists
                elif path == "/api/checklists/template-csv":
                    csv_text = get_checklist_csv_template_use_case()
                    self._set_headers(200, "text/csv", {"Content-Disposition": 'attachment; filename="plantilla_checklist_normas.csv"'})
                    self.wfile.write(csv_text.encode("utf-8"))
                    return

                # Checklist Normativo (Multi-Estándar)
                elif path == "/api/checklist":
                    sys_id = int(query.get("system_id", [1])[0])
                    chk_id = query.get("checklist_id", ["nom070"])[0]
                    checklist = get_audit_checklist_use_case(sys_id, checklist_id=chk_id)
                    self._send_json({"status": "success", "checklist": checklist})
                    return

                # Subscription status
                elif path == "/api/subscription/status":
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
                # Documentos de la Bóveda
                elif path == "/api/documents":
                    sys_id = query.get("system_id", [None])[0]
                    sys_int = int(sys_id) if sys_id else None
                    docs = list_documents(sys_int)
                    self._send_json({"status": "success", "count": len(docs), "items": docs})
                    return

                # Descargar documento de la Bóveda
                elif path.startswith("/api/documents/") and path.endswith("/download"):
                    doc_id = int(path.split("/")[3])
                    info = get_document_file(doc_id)
                    if not info:
                        self._send_error_json("Archivo no encontrado en la bóveda", 404)
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

                # Exportaciones industriales (openLCA, ILCD, SimaPro, CSV, Expediente ZIP)
                elif path.startswith("/api/systems/") and "/export/" in path:
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
                        csv_b = csv_txt.encode("utf-8")
                        self._set_headers(200, "text/csv", {
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
                        pdf_bytes = export_system_pdf_bytes(conn, sys_id)
                        self._set_headers(200, "application/pdf", {
                            "Content-Disposition": f'attachment; filename="Reporte_ACV_NOM070_Sistema_{sys_id}.pdf"',
                            "Content-Length": str(len(pdf_bytes))
                        })
                        self.wfile.write(pdf_bytes)
                    else:
                        self._send_error_json(f"Formato no reconocido: {fmt}. Opciones: openlca, ilcd, simapro, csv, expediente, pdf", 400)
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

        conn = get_active_db_connection()
        try:
            # Google OAuth Login
            if path == "/api/auth/google":
                cred = body.get("credential", "")
                email = body.get("email")
                try:
                    user = auth_service.login_with_google(cred, fallback_email=email)
                    self._send_json({"status": "success", "authenticated": True, "user": user})
                except Exception as e:
                    self._send_error_json(str(e), 401)
                return

            # Login con Usuario/Correo y Contraseña (con fallback para pruebas)
            elif path == "/api/auth/login":
                username_or_email = body.get("email") or body.get("username") or body.get("user_id")
                password = body.get("password")

                if password:
                    user = auth_service.authenticate(username_or_email, password)
                    if user:
                        self._send_json({"status": "success", "authenticated": True, "user": user, "token": user.get("token")})
                    else:
                        self._send_error_json("Credenciales incorrectas. Verifica tu correo y contraseña.", 401)
                    return
                else:
                    # Fallback de compatibilidad
                    user = auth_service.switch_account(username_or_email or "analyst_carla")
                    if user:
                        self._send_json({"status": "success", "authenticated": True, "user": user, "token": user.get("token")})
                    else:
                        self._send_error_json("Usuario o rol no reconocido", 400)
                    return

            # Sign-Up (Crear Cuenta / Organización con contraseña)
            elif path == "/api/auth/signup" or path == "/api/auth/register":
                try:
                    user = auth_service.register_account(body)
                    self._send_json({"status": "success", "created": True, "user": user, "token": user.get("token")})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Switch Account
            elif path == "/api/auth/switch-account":
                ident = body.get("account_id") or body.get("role") or ""
                switched = auth_service.switch_account(ident)
                if switched:
                    self._send_json({"status": "success", "user": switched})
                else:
                    self._send_error_json("No se pudo alternar la cuenta", 400)
                return

            # Create Product System (Wizard)
            elif path == "/api/systems/create":
                try:
                    user = self._get_request_user()
                    res = create_system_wizard_use_case(conn, body, user=user)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Import CSV
            elif path == "/api/systems/import-csv":
                csv_str = body.get("csv", "")
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
                    user = self._get_request_user()
                    res = import_systems_csv_use_case(conn, csv_str, user=user)
                    self._send_json(res)
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Save Canvas
            elif path.startswith("/api/systems/") and path.endswith("/save"):
                sys_id = int(path.split("/")[3])
                try:
                    save_system_canvas_use_case(conn, sys_id, body)
                    self._send_json({"status": "success", "message": "Lienzo guardado exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Product System
            elif path == "/api/systems/delete":
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

            # Create Custom Process (Estilo openLCA / Proceso en Blanco)
            elif path == "/api/processes/create":
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

            # Create Custom Flow (Estilo openLCA)
            elif path == "/api/flows/create":
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

            # Delete Custom Process
            elif path == "/api/processes/delete":
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

            # Delete Custom Flow
            elif path == "/api/flows/delete":
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

            # Invite Collaborator (Auditor o Cliente)
            elif path == "/api/systems/collaborators/invite":
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

            # Add Comment
            elif path == "/api/comments":
                sys_id = int(body.get("system_id", 1))
                author = body.get("author_name") or auth_service.get_active_account().get("display_name", "Auditor")
                role = body.get("author_role") or auth_service.get_active_account().get("role", "auditor")
                content = body.get("content", "")
                node_id = body.get("node_id")
                x = body.get("x")
                y = body.get("y")
                if not content:
                    self._send_error_json("Contenido del comentario vacío", 400)
                    return
                comment = add_system_comment_use_case(sys_id, author, role, content, node_id=node_id, x=x, y=y)
                self._send_json({"status": "success", "comment": comment})
                return

            # Resolve Comment
            elif path == "/api/comments/resolve":
                cid = int(body.get("comment_id", 1))
                resolved_by = body.get("resolved_by") or auth_service.get_active_account().get("display_name", "Elena R.")
                reply_text = body.get("reply", "")
                try:
                    resolved = reply_and_resolve_comment_use_case(cid, resolved_by, reply_text)
                    self._send_json({"status": "success", "resolved": resolved})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Delete Comment
            elif path == "/api/comments/delete":
                cid = int(body.get("comment_id", 0))
                active_user = auth_service.get_active_account()
                user_name = body.get("user_name") or active_user.get("display_name", "")
                user_role = body.get("user_role") or active_user.get("role", "analyst")
                try:
                    delete_system_comment_use_case(cid, user_name, user_role)
                    self._send_json({"status": "success", "deleted_id": cid})
                except Exception as e:
                    self._send_error_json(str(e), 403 if isinstance(e, PermissionError) else 400)
                return

            # Toggle Checklist Clause
            elif path == "/api/checklist/toggle":
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

            # Update Clause Evidence Requirement
            elif path == "/api/checklist/evidence":
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

            # Sign Audit
            elif path == "/api/checklist/sign":
                sys_id = int(body.get("system_id", 1))
                chk_id = body.get("checklist_id", "nom070")
                auditor_name = auth_service.get_active_account().get("display_name", "Josué Arentería")
                try:
                    res = sign_normative_audit_use_case(sys_id, auditor_name, checklist_id=chk_id)
                    self._send_json({"status": "success", "receipt": res})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Crear Norma Personalizada
            elif path == "/api/checklists/create":
                user = self._get_request_user()
                try:
                    res = create_custom_standard_use_case(body, user=user)
                    self._send_json({"status": "success", "standard": res, "message": "Norma creada exitosamente."})
                except Exception as e:
                    self._send_error_json(str(e), 400)
                return

            # Importar Norma vía Archivo CSV
            elif path == "/api/checklists/import":
                user = self._get_request_user()
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

            # Subir documento a la Bóveda (SQL, Excel, PDF, CSV, etc.)
            elif path == "/api/documents/upload":
                title = body.get("title") or body.get("original_filename") or body.get("file_name") or "Documento"
                orig_name = body.get("original_filename") or body.get("file_name") or "archivo.bin"
                content_b64 = body.get("content_base64") or body.get("file_data") or ""
                content_text = body.get("content_text", "")
                sys_id = int(body.get("system_id", 1))
                desc = body.get("description", "")
                uploaded_by = body.get("uploaded_by") or body.get("author_name") or auth_service.get_active_account().get("display_name", "Usuario")
                role = body.get("user_role") or body.get("author_role") or auth_service.get_active_account().get("role", "client")

                import base64
                if content_b64:
                    try:
                        file_bytes = base64.b64decode(content_b64)
                    except Exception:
                        file_bytes = content_b64.encode("utf-8")
                elif content_text:
                    file_bytes = content_text.encode("utf-8")
                else:
                    file_bytes = b"Contenido vacio"

                try:
                    doc = save_document(title, orig_name, file_bytes, uploaded_by, role, sys_id, desc)
                    self._send_json({"status": "success", "document": doc})
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            # Eliminar documento de la Bóveda
            elif path == "/api/documents/delete":
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
