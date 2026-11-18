"""
ECONODE Tests - Pruebas de Integracion REST para Plantillas y Reportes EPD (SmartEPD / EN 15804+A2 / TRACI 2.1)
"""

import subprocess
import time
import requests
import sys
import unittest

STUDIO_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio"
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from application.auth_service import generate_session_token
from infrastructure.auth_adapter import get_all_users


class TestEPDAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        analyst_user = next(u for u in get_all_users() if u.get("role") == "analyst")
        cls.token = generate_session_token(analyst_user["id"], "analyst")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.port = 8897
        cls.base_url = f"http://localhost:{cls.port}"

        cls.server_proc = subprocess.Popen(
            [sys.executable, r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio\server.py", "--port", str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2.5)

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc:
            cls.server_proc.terminate()
            cls.server_proc.wait()

    def test_01_list_epd_templates(self):
        """GET /api/epd/templates retorna las 4 plantillas de cemento y concreto y la taxonomia SmartEPD."""
        r = requests.get(f"{self.base_url}/api/epd/templates", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["templates"]), 4)
        self.assertEqual(len(data["modules"]), 17)

    def test_02_instantiate_report_metadata_and_openepd(self):
        """Flujo HTTP completo: instanciar concreto bajo carbono A1-D -> reporte EN 15804+A2 & TRACI 2.1 -> editar metadatos -> descargar openEPD."""
        r_inst = requests.post(
            f"{self.base_url}/api/epd/templates/instantiate",
            headers=self.headers,
            json={
                "template_id": "epd_concrete_low_carbon_a1_d",
                "name": "Concreto Bajo Carbono API Test",
                "plant_location": "Planta Queretaro, MX",
                "default_standard": "EN15804_A2"
            }
        )
        self.assertEqual(r_inst.status_code, 200)
        inst = r_inst.json()
        sys_id = inst["system_id"]
        self.assertIsNotNone(sys_id)

        try:
            # 1. Consultar Canvas y confirmar epd_config y nodos con epd_module
            r_canvas = requests.get(f"{self.base_url}/api/systems/{sys_id}/canvas", headers=self.headers)
            self.assertEqual(r_canvas.status_code, 200)
            sys_obj = r_canvas.json()["system"]
            self.assertEqual(len(sys_obj["nodes"]), 10)
            self.assertEqual(sys_obj["nodes"][0]["epd_module"], "A1")
            self.assertIsNotNone(sys_obj.get("epd_config"))

            # 2. Consultar Reporte EPD (EN 15804+A2)
            r_rep_en = requests.get(f"{self.base_url}/api/systems/{sys_id}/epd-report?standard=EN15804_A2", headers=self.headers)
            self.assertEqual(r_rep_en.status_code, 200)
            rep_en = r_rep_en.json()
            self.assertEqual(len(rep_en["impact_results"]), 13)
            self.assertEqual(len(rep_en["boundary_matrix"]), 17)
            self.assertLess(rep_en["summary_kpis"]["gwp_module_d"], 0.0)

            # 3. Consultar Reporte EPD (TRACI 2.1 / ISO 21930)
            r_rep_tr = requests.get(f"{self.base_url}/api/systems/{sys_id}/epd-report?standard=TRACI_2_1", headers=self.headers)
            self.assertEqual(r_rep_tr.status_code, 200)
            rep_tr = r_rep_tr.json()
            self.assertEqual(len(rep_tr["impact_results"]), 6)

            # 4. Actualizar Metadatos EPD
            r_meta = requests.post(
                f"{self.base_url}/api/systems/{sys_id}/epd-metadata",
                headers=self.headers,
                json={
                    "program_operator": "Smart EPD",
                    "declaration_number": "SMARTEPD-TEST-2026-88",
                    "verifier_name": "Verificador Externo ISO 14025"
                }
            )
            self.assertEqual(r_meta.status_code, 200)
            self.assertEqual(r_meta.json()["epd_config"]["declaration_number"], "SMARTEPD-TEST-2026-88")

            # 5. Exportar OpenEPD JSON
            r_open = requests.get(f"{self.base_url}/api/systems/{sys_id}/export/openepd", headers=self.headers)
            self.assertEqual(r_open.status_code, 200)
            open_doc = r_open.json()
            self.assertEqual(open_doc["doctype"], "openEPD")
            self.assertEqual(open_doc["id"], "SMARTEPD-TEST-2026-88")
        finally:
            requests.post(f"{self.base_url}/api/systems/delete", headers=self.headers, json={"system_id": sys_id})


if __name__ == "__main__":
    unittest.main()
