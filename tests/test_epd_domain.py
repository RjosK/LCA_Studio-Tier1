"""
ECONODE Tests - Pruebas de Dominio y Calculo Modular EPD (SmartEPD / EN 15804+A2 / TRACI 2.1)
Verifica plantillas preliminares de Cemento y Concreto, overrides parametricos,
calculo modular A1-D y exportacion digital OpenEPD JSON.
"""

import sys
import unittest
import sqlite3
from pathlib import Path

STUDIO_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio"
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from domain.epd_models import EPD_PRELIMINARY_TEMPLATES, EPD_MODULES, SMART_EPD_PCR_REGISTRY
from application.epd_service import (
    list_epd_templates_use_case,
    instantiate_epd_template_use_case,
    compute_epd_report_use_case,
    save_epd_metadata_use_case,
    export_openepd_json_use_case
)
from infrastructure.database_adapter import get_active_db_connection, delete_product_system


class TestEPDDomainAndService(unittest.TestCase):
    def test_01_templates_and_pcr_registry(self):
        """Verifica que existan las 4 plantillas de cemento/concreto y el registro multi-industria SmartEPD."""
        res = list_epd_templates_use_case()
        self.assertEqual(res["status"], "success")
        tpl_ids = [t["template_id"] for t in res["templates"]]
        self.assertIn("epd_cement_cpo", tpl_ids)
        self.assertIn("epd_cement_cpc", tpl_ids)
        self.assertIn("epd_concrete_rmx_4000", tpl_ids)
        self.assertIn("epd_concrete_low_carbon_a1_d", tpl_ids)
        self.assertEqual(len(res["modules"]), 17)
        ind_ids = [i["industry_id"] for i in res["industries"]]
        self.assertIn("cement_concrete", ind_ids)
        self.assertIn("steel", ind_ids)
        self.assertIn("asphalt", ind_ids)

    def test_02_cement_cpo_vs_cpc_gwp_benchmarks(self):
        """Instancia CPO 40 y CPC 30R y verifica rangos reales de huella de carbono (kg CO2e/t)."""
        with get_active_db_connection() as conn:
            cpo = instantiate_epd_template_use_case(conn, "epd_cement_cpo", {"name": "Test CPO 40"})
            cpc = instantiate_epd_template_use_case(conn, "epd_cement_cpc", {"name": "Test CPC 30R"})
            try:
                rep_cpo = compute_epd_report_use_case(conn, cpo["system_id"], standard="EN15804_A2")
                rep_cpc = compute_epd_report_use_case(conn, cpc["system_id"], standard="EN15804_A2")

                gwp_cpo = rep_cpo["summary_kpis"]["gwp_a1_a3"]
                gwp_cpc = rep_cpc["summary_kpis"]["gwp_a1_a3"]

                # Rango industrial realista: CPO ~780-920 kg CO2e/t, CPC ~580-720 kg CO2e/t
                self.assertGreater(gwp_cpo, 750.0)
                self.assertLess(gwp_cpo, 950.0)
                self.assertGreater(gwp_cpc, 550.0)
                self.assertLess(gwp_cpc, 750.0)
                self.assertLess(gwp_cpc, gwp_cpo)

                # Verificar 13 indicadores en EN 15804+A2
                self.assertEqual(len(rep_cpo["impact_results"]), 13)
                # Verificar TRACI 2.1 (6 indicadores)
                rep_traci = compute_epd_report_use_case(conn, cpo["system_id"], standard="TRACI_2_1")
                self.assertEqual(len(rep_traci["impact_results"]), 6)
            finally:
                delete_product_system(conn, cpo["system_id"])
                delete_product_system(conn, cpc["system_id"])

    def test_03_concrete_standard_vs_low_carbon_full_lifecycle(self):
        """Verifica concreto 4,000 psi A1-A3 vs concreto bajo carbono A1-D con SCMs y credito Modulo D."""
        with get_active_db_connection() as conn:
            rmx = instantiate_epd_template_use_case(conn, "epd_concrete_rmx_4000", {"name": "Test Concreto 4000"})
            lc = instantiate_epd_template_use_case(conn, "epd_concrete_low_carbon_a1_d", {"name": "Test Concreto Bajo Carbono"})
            try:
                rep_rmx = compute_epd_report_use_case(conn, rmx["system_id"], standard="TRACI_2_1")
                rep_lc = compute_epd_report_use_case(conn, lc["system_id"], standard="EN15804_A2")

                gwp_rmx = rep_rmx["summary_kpis"]["gwp_a1_a3"]
                gwp_lc = rep_lc["summary_kpis"]["gwp_a1_a3"]
                gwp_d = rep_lc["summary_kpis"]["gwp_module_d"]
                sm_lc = rep_lc["summary_kpis"]["secondary_materials_kg"]

                # Concreto 4,000 psi tipico: 280 - 380 kg CO2e/m3
                self.assertGreater(gwp_rmx, 280.0)
                self.assertLess(gwp_rmx, 380.0)
                # Concreto bajo carbono debe reducir al menos 20% en A1-A3
                self.assertLess(gwp_lc, gwp_rmx * 0.80)
                # Modulo D debe reflejar credito negativo por sustitucion de aridos
                self.assertLess(gwp_d, 0.0)
                # Materiales secundarios (GGBFS 85 + Fly ash 45 = 130 kg)
                self.assertAlmostEqual(sm_lc, 130.0, places=1)
                # Modulos declarados en ciclo completo
                self.assertEqual(rep_lc["declared_modules"], ["A1", "A2", "A3", "A4", "A5", "C1", "C2", "C3", "C4", "D"])
            finally:
                delete_product_system(conn, rmx["system_id"])
                delete_product_system(conn, lc["system_id"])

    def test_04_metadata_save_and_openepd_export(self):
        """Verifica guardado de metadatos EPD y estructura valida del JSON openEPD."""
        with get_active_db_connection() as conn:
            inst = instantiate_epd_template_use_case(
                conn,
                "epd_concrete_rmx_4000",
                {"name": "Concreto Planta Monterrey", "cement_dosage_kg_m3": 380.0}
            )
            try:
                save_res = save_epd_metadata_use_case(conn, inst["system_id"], {
                    "program_operator": "Smart EPD",
                    "plant_location": "Planta Apodaca, Nuevo Leon, MX",
                    "declaration_number": "SMART-EPD-MX-2026-009"
                })
                self.assertEqual(save_res["epd_config"]["program_operator"], "Smart EPD")

                openepd = export_openepd_json_use_case(conn, inst["system_id"])
                self.assertEqual(openepd["doctype"], "openEPD")
                self.assertEqual(openepd["id"], "SMART-EPD-MX-2026-009")
                self.assertEqual(openepd["declared_unit"]["unit"], "m3")
                self.assertIn("EN15804_A2", openepd["impacts"])
                self.assertIn("TRACI_2_1", openepd["impacts"])
                # Con 380 kg cemento (> 340 kg default), GWP debe superar 350 kg CO2e/m3
                self.assertGreater(openepd["impacts"]["EN15804_A2"]["gwp_total"]["A1A2A3"]["mean"], 350.0)
            finally:
                delete_product_system(conn, inst["system_id"])


if __name__ == "__main__":
    unittest.main()
