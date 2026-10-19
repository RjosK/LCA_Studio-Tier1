"""
econode_studio/tests/test_server_api.py - Suite Automatizada de Verificación para ECONODE Studio
Ejecuta el servidor en un hilo secundario y verifica todos los endpoints REST y estáticos.
Compatible tanto con `python -m unittest discover` como con ejecución directa `python test_server_api.py`.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
import threading
import unittest

TEST_PORT = 8089

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)
PARENT_DIR = os.path.dirname(STUDIO_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import http.server
from econode_studio.server import EconodeRequestHandler


class ServerTestManager:
    """Administra el ciclo de vida del servidor HTTP en un puerto aislado para pruebas."""
    server_instance = None
    server_thread = None

    @classmethod
    def start(cls):
        if cls.server_instance is None:
            cls.server_instance = http.server.ThreadingHTTPServer(("127.0.0.1", TEST_PORT), EconodeRequestHandler)
            cls.server_thread = threading.Thread(target=cls.server_instance.serve_forever, daemon=True)
            cls.server_thread.start()
            time.sleep(1.0)

    @classmethod
    def stop(cls):
        if cls.server_instance:
            cls.server_instance.shutdown()
            cls.server_instance.server_close()
            cls.server_instance = None
            cls.server_thread = None


def request_json(path, data=None, method="GET"):
    url = f"http://127.0.0.1:{TEST_PORT}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        content = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return resp.status, json.loads(content.decode("utf-8"))
        elif "application/zip" in content_type:
            return resp.status, len(content)
        return resp.status, content.decode("utf-8", errors="replace")


TEST_CASES = [
    # 1. Estáticos
    ("GET /index.html", lambda: request_json("/index.html")),
    ("GET /css/styles.css", lambda: request_json("/css/styles.css")),
    ("GET /js/app.js", lambda: request_json("/js/app.js")),
    ("GET /js/i18n.js", lambda: request_json("/js/i18n.js")),

    # 2. Auth Config & Profile
    ("GET /api/auth/config", lambda: request_json("/api/auth/config")),
    ("GET /api/profile", lambda: request_json("/api/profile")),

    # 3. Sistemas & Plantilla
    ("GET /api/systems", lambda: request_json("/api/systems")),
    ("GET /api/systems/21/canvas", lambda: request_json("/api/systems/21/canvas")),
    ("GET /api/systems/template-csv", lambda: request_json("/api/systems/template-csv")),

    # 4. Catálogo LCI ecoinvent 3.12 & Categorías
    ("GET /api/processes?limit=5", lambda: request_json("/api/processes?limit=5")),
    ("GET /api/processes?category_id=polymers", lambda: request_json("/api/processes?category_id=polymers&limit=5")),
    ("GET /api/processes?category_id=energy", lambda: request_json("/api/processes?category_id=energy&limit=5")),
    ("GET /api/processes/16615/sheet", lambda: request_json("/api/processes/16615/sheet")),

    # 5. Comentarios Colaborativos & Checklist
    ("GET /api/comments?system_id=21", lambda: request_json("/api/comments?system_id=21")),
    ("GET /api/checklist?system_id=21 (18 cláusulas)", lambda: request_json("/api/checklist?system_id=21")),
    ("GET /api/subscription/status", lambda: request_json("/api/subscription/status")),
    ("GET /api/systems/21/canvas (3 procesos oficiales)", lambda: request_json("/api/systems/21/canvas")),
    ("GET /api/documents?system_id=21 (Bóveda acotada)", lambda: request_json("/api/documents?system_id=21")),

    # 6. POST Endpoints - Los 3 Perfiles Oficiales
    ("POST /api/auth/login (Analista Carla)", lambda: request_json("/api/auth/login", {"user_id": "analyst_carla"}, "POST")),
    ("POST /api/auth/login (Auditor Josué)", lambda: request_json("/api/auth/login", {"user_id": "auditor_lead"}, "POST")),
    ("POST /api/auth/login (Cliente Elena)", lambda: request_json("/api/auth/login", {"user_id": "client_elena"}, "POST")),
    ("POST /api/systems/create (Wizard)", lambda: request_json("/api/systems/create", {
        "name": "Botella Biodegradable PLA 250ml",
        "code": "SKU-PLA-250",
        "category": "Biopolímeros",
        "geography": "[MX] México",
        "reference_amount": 1.0,
        "reference_unit": "u"
    }, "POST")),
    ("POST /api/systems/import-csv", lambda: request_json("/api/systems/import-csv", {}, "POST")),
    ("POST /api/comments", lambda: request_json("/api/comments", {
        "system_id": 21,
        "content": "Revisión de consumo eléctrico de inyección validada según CFE.",
        "author_name": "Josué Arentería",
        "author_role": "auditor"
    }, "POST")),
    ("POST /api/comments/resolve", lambda: request_json("/api/comments/resolve", {
        "comment_id": 1,
        "reply": "Se actualizó la ficha técnica con el recibo CFE 2026.",
        "resolved_by": "Elena Ramírez"
    }, "POST")),
    ("POST /api/checklist/toggle", lambda: request_json("/api/checklist/toggle", {
        "system_id": 21,
        "clause_id": "NOM-4.6.1.1",
        "is_compliant": True
    }, "POST")),
    ("POST /api/checklist/sign", lambda: request_json("/api/checklist/sign", {
        "system_id": 21
    }, "POST")),
    ("GET /api/checklists", lambda: request_json("/api/checklists")),
    ("GET /api/checklists/template-csv", lambda: request_json("/api/checklists/template-csv")),
    ("GET /api/checklist (ISO 14067)", lambda: request_json("/api/checklist?system_id=21&checklist_id=iso14067")),
    ("POST /api/checklists/create", lambda: request_json("/api/checklists/create", {
        "name": "Norma Específica Circularidad PET",
        "code": "NORM-PET-TEST",
        "standard_family": "Corporativa",
        "clauses": [
            {"clause_id": "TEST-1", "section": "1.0", "title": "Inspección de Resina", "criterion": "100% rPET", "evidence": "Ficha"}
        ]
    }, "POST")),
    ("POST /api/checklists/import", lambda: request_json("/api/checklists/import", {
        "name": "Norma Importada CSV Test",
        "code": "NORM-CSV-TEST",
        "csv": "seccion,clausula_id,titulo,criterio,evidencia_requerida\n1. General,C-1,Requisito Test,Criterio Test,Evidencia Test\n"
    }, "POST")),

    # 7. Bóveda de Documentos (SQL, Excel, PDF)
    ("GET /api/documents", lambda: request_json("/api/documents")),
    ("POST /api/documents/upload", lambda: request_json("/api/documents/upload", {
        "title": "Archivo de Prueba Temporal",
        "original_filename": "temp_test_2026.sql",
        "content_text": "CREATE TABLE test_temp (id INT);",
        "system_id": 21,
        "description": "Script temporal de prueba"
    }, "POST")),
    ("GET /api/documents/download (Valid)", lambda: request_json(f"/api/documents/{request_json('/api/documents')[1]['items'][0]['id']}/download")),
    ("POST /api/documents/delete", lambda: request_json("/api/documents/delete", {"document_id": request_json('/api/documents')[1]['items'][0]['id']}, "POST")),
    ("POST /api/comments/delete", lambda: request_json("/api/comments/delete", {"comment_id": 2, "user_name": "Josué Arentería", "user_role": "auditor"}, "POST")),

    # 8. Exportaciones Industriales
    ("GET /api/systems/21/export/openlca", lambda: request_json("/api/systems/21/export/openlca")),
    ("GET /api/systems/21/export/ilcd", lambda: request_json("/api/systems/21/export/ilcd")),
    ("GET /api/systems/21/export/simapro", lambda: request_json("/api/systems/21/export/simapro")),
    ("GET /api/systems/21/export/csv", lambda: request_json("/api/systems/21/export/csv")),
    ("GET /api/systems/21/export/nom070", lambda: request_json("/api/systems/21/export/nom070")),
    ("GET /api/systems/21/export/expediente", lambda: request_json("/api/systems/21/export/expediente")),
    ("POST /api/auth/logout", lambda: request_json("/api/auth/logout", {}, "POST")),
]


class TestServerApi(unittest.TestCase):
    """Suite estándar unittest.TestCase para integrarse con runners de CI/CD y CLI."""

    @classmethod
    def setUpClass(cls):
        try:
            from infrastructure.audit_adapter import AUDIT_DB_PATH
        except ImportError:
            from econode_studio.infrastructure.audit_adapter import AUDIT_DB_PATH
        cls.audit_backup = None
        if os.path.exists(AUDIT_DB_PATH):
            try:
                with open(AUDIT_DB_PATH, "rb") as f:
                    cls.audit_backup = f.read()
            except Exception:
                pass
        ServerTestManager.start()

    @classmethod
    def tearDownClass(cls):
        ServerTestManager.stop()
        # Restaurar estado idempotente de la bóveda
        try:
            from infrastructure.documents_adapter import DOCS_DB_PATH, UPLOADS_DIR
            import sqlite3
            with sqlite3.connect(DOCS_DB_PATH) as conn:
                conn.execute("DELETE FROM documents")
            if os.path.exists(UPLOADS_DIR):
                for f in os.listdir(UPLOADS_DIR):
                    fp = os.path.join(UPLOADS_DIR, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
        except Exception:
            pass

        try:
            from infrastructure.audit_adapter import AUDIT_DB_PATH
            import sqlite3
            with sqlite3.connect(AUDIT_DB_PATH) as conn:
                conn.execute("DELETE FROM audit_comments WHERE content LIKE '%Revisión de consumo eléctrico%' OR id > 1")
        except Exception:
            pass


        # Limpiar modelos temporales de prueba en ecoinvent_312.db (preservar sólo oficiales 21 y 390)
        try:
            from config import settings
            import sqlite3
            with sqlite3.connect(settings.ECOINVENT_DB_PATH) as conn:
                conn.execute("DELETE FROM product_systems WHERE id NOT IN (21, 390)")
                conn.execute("DELETE FROM product_system_nodes WHERE system_id NOT IN (21, 390)")
                conn.execute("DELETE FROM product_system_edges WHERE system_id NOT IN (21, 390)")
        except Exception:
            pass

    def test_all_endpoints(self):
        """Ejecuta los 44 endpoints asegurando códigos HTTP 200 o 201."""
        for name, fn in TEST_CASES:
            status, res = fn()
            self.assertIn(status, (200, 201), f"Endpoint {name} retornó status {status}")


def run_all_tests():
    """Ejecutor directo por consola que imprime el reporte amigable paso a paso."""
    print(f"Iniciando servidor de pruebas en puerto {TEST_PORT}...")
    ServerTestManager.start()

    passed = 0
    failed = 0

    for name, fn in TEST_CASES:
        try:
            status, res = fn()
            if status in (200, 201):
                print(f"  [PASS] {name} (Status: {status})")
                passed += 1
            else:
                print(f"  [FAIL] {name} (Status: {status})")
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {name} -> {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passed} PASARON, {failed} FALLARON.")
    print("=" * 60)

    TestServerApi.tearDownClass()
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
