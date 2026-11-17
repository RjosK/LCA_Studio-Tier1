"""
ECONODE Tests - Pruebas de Integracion de Endpoints REST GHG Protocol
Verifica las rutas HTTP de inventarios corporativos, catalogo de factores y calculos en server.py.
"""

import subprocess
import time
import requests
import sys
import unittest
from pathlib import Path

STUDIO_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio"
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from application.auth_service import generate_session_token
from infrastructure.auth_adapter import get_all_users
from infrastructure.seed_emission_factors import seed_emission_factors

class TestGHGAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_emission_factors(force_reload=False)
        analyst_user = next(u for u in get_all_users() if u.get("role") == "analyst")
        cls.token = generate_session_token(analyst_user["id"], "analyst")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.port = 8898
        cls.base_url = f"http://localhost:{cls.port}"

        # Iniciar servidor en subproceso
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

    def test_01_get_taxonomy(self):
        """GET /api/ghg/taxonomy retorna la taxonomia de los 3 alcances y 15 categorias de Scope 3."""
        r = requests.get(f"{self.base_url}/api/ghg/taxonomy", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")
        tax = data["taxonomy"]
        self.assertIn("stationary_combustion", tax)
        self.assertIn("cat_1_purchased_goods", tax)
        self.assertIn("cat_15_investments", tax)

    def test_02_get_sources(self):
        """GET /api/ghg/sources retorna las bases de datos sembradas."""
        r = requests.get(f"{self.base_url}/api/ghg/sources", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        sources = r.json().get("sources", [])
        self.assertIn("DEFRA_2024", sources)
        self.assertIn("CRE_MEXICO_2024", sources)

    def test_03_search_emission_factors(self):
        """GET /api/ghg/emission-factors permite busqueda paginada y filtrado."""
        r = requests.get(f"{self.base_url}/api/ghg/emission-factors?q=Natural&scope=SCOPE_1", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertGreater(data["total"], 0)
        item = data["items"][0]
        self.assertIn("Natural", item["factor_name"])

    def test_04_crud_inventory_lifecycle(self):
        """Ciclo completo de creacion, agregado de entradas, resumen contable y eliminacion."""
        # 1. Crear Inventario
        create_payload = {
            "organization_name": "Corporativo Sustentable Alfa",
            "reporting_year": 2024,
            "consolidation_approach": "operational_control",
            "country_code": "MX",
            "description": "Inventario de prueba automatizada"
        }
        r_create = requests.post(f"{self.base_url}/api/ghg/inventories", headers=self.headers, json=create_payload)
        self.assertEqual(r_create.status_code, 200)
        inv = r_create.json().get("inventory")
        inv_id = inv["id"]
        self.assertIsNotNone(inv_id)

        try:
            # 2. Agregar Entrada Scope 1
            entry_s1 = {
                "scope_category": "stationary_combustion",
                "activity_name": "Consumo Gas Natural Planta 1",
                "calculation_type": "activity_based",
                "activity_amount": 5000.0,
                "activity_unit": "m3",
                "emission_factor_value": 2.0214,
                "emission_factor_unit": "kg CO2e / m3",
                "emission_factor_source": "DEFRA 2024"
            }
            r_add = requests.post(f"{self.base_url}/api/ghg/inventories/{inv_id}/entries", headers=self.headers, json=entry_s1)
            self.assertEqual(r_add.status_code, 200)
            inv_updated = r_add.json().get("inventory")
            self.assertEqual(len(inv_updated["entries"]), 1)
            self.assertAlmostEqual(inv_updated["summary"]["scope_1"]["total_tco2e"], 10.107, places=2)

            # 3. Consultar Detalle
            r_get = requests.get(f"{self.base_url}/api/ghg/inventories/{inv_id}", headers=self.headers)
            self.assertEqual(r_get.status_code, 200)
            self.assertEqual(r_get.json()["inventory"]["organization_name"], "Corporativo Sustentable Alfa")

            # 4. Eliminar Entrada
            entry_id = inv_updated["entries"][0]["id"]
            r_del_entry = requests.post(f"{self.base_url}/api/ghg/inventories/{inv_id}/entries/{entry_id}/delete", headers=self.headers, json={})
            self.assertEqual(r_del_entry.status_code, 200)
            inv_empty = r_del_entry.json().get("inventory")
            self.assertEqual(len(inv_empty["entries"]), 0)

        finally:
            # 5. Eliminar Inventario
            r_del = requests.post(f"{self.base_url}/api/ghg/inventories/{inv_id}/delete", headers=self.headers, json={})
            self.assertEqual(r_del.status_code, 200)

if __name__ == "__main__":
    unittest.main()
