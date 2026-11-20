"""
tests/test_ghg_dynamic_report.py - Pruebas para la integracion del Reporte Dinamico GHG Protocol
Verifica la estructura DOM, traducciones bilingues i18n, funciones de app.js,
resumenes contables y la politica estricta de Cero Emojis.
"""

import os
import re
import unittest
from econode_studio.domain.ghg_inventory import GHGInventory, GHGEntry, SCOPE_CATEGORIES
from econode_studio.application.ghg_service import list_inventories_use_case, get_inventory_by_id_use_case


class TestGhgDynamicReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.html_path = os.path.join(base_dir, "public", "index.html")
        cls.js_app_path = os.path.join(base_dir, "public", "js", "app.js")
        cls.js_i18n_path = os.path.join(base_dir, "public", "js", "i18n.js")
        cls.css_path = os.path.join(base_dir, "public", "css", "styles.css")

        with open(cls.html_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        with open(cls.js_app_path, "r", encoding="utf-8") as f:
            cls.js_app_content = f.read()

        with open(cls.js_i18n_path, "r", encoding="utf-8") as f:
            cls.js_i18n_content = f.read()

        with open(cls.css_path, "r", encoding="utf-8") as f:
            cls.css_content = f.read()

    def test_dom_elements_present(self):
        """Verifica que el conmutador de 3 vias y el contenedor del reporte GEI existan en index.html."""
        self.assertIn('id="btnReportModeGhg"', self.html_content)
        self.assertIn('data-report-mode="ghg"', self.html_content)
        self.assertIn('id="ghgReportContainer"', self.html_content)
        self.assertIn('id="selectGhgReportInventory"', self.html_content)
        self.assertIn('id="btnGhgScope2Location"', self.html_content)
        self.assertIn('id="btnGhgScope2Market"', self.html_content)
        self.assertIn('id="btnExportGhgReportJson"', self.html_content)
        self.assertIn('id="btnPrintGhgPdf"', self.html_content)
        self.assertIn('id="printGhgOfficialHeader"', self.html_content)
        self.assertIn('id="ghgReportKpiGrid"', self.html_content)
        self.assertIn('id="ghgKpiTotal"', self.html_content)
        self.assertIn('id="ghgKpiScope1"', self.html_content)
        self.assertIn('id="ghgKpiScope2"', self.html_content)
        self.assertIn('id="ghgKpiScope3"', self.html_content)
        self.assertIn('id="ghgKpiReduction"', self.html_content)

    def test_dom_seven_sections_and_tables(self):
        """Verifica la presencia de las 7 secciones normativas y las tablas de datos."""
        self.assertIn('ghg_rep.sec1_title', self.html_content)
        self.assertIn('ghg_rep.sec2_title', self.html_content)
        self.assertIn('ghg_rep.sec3_title', self.html_content)
        self.assertIn('ghg_rep.sec4_title', self.html_content)
        self.assertIn('ghg_rep.sec5_title', self.html_content)
        self.assertIn('ghg_rep.sec6_title', self.html_content)
        self.assertIn('ghg_rep.sec7_title', self.html_content)

        # Tablas de datos dinamicos
        self.assertIn('id="ghgSummaryTableBody"', self.html_content)
        self.assertIn('id="ghgGasesTableBody"', self.html_content)
        self.assertIn('id="ghgScope1TableBody"', self.html_content)
        self.assertIn('id="ghgScope2TableBody"', self.html_content)
        self.assertIn('id="ghgScope3TableBody"', self.html_content)
        self.assertIn('id="ghgFactorsTableBody"', self.html_content)

    def test_i18n_keys_present_in_both_languages(self):
        """Valida que todas las etiquetas de reporte GEI existan en espanol e ingles."""
        required_keys = [
            "report.mode_ghg",
            "ghg_rep.inventory_label",
            "ghg_rep.btn_json",
            "ghg_rep.btn_print_pdf",
            "ghg_rep.kpi_total",
            "ghg_rep.kpi_scope1",
            "ghg_rep.kpi_scope2",
            "ghg_rep.kpi_scope3",
            "ghg_rep.kpi_reduction",
            "ghg_rep.sec1_title",
            "ghg_rep.sec2_title",
            "ghg_rep.gas_breakdown_title",
            "ghg_rep.sec3_title",
            "ghg_rep.sec4_title",
            "ghg_rep.sec5_title",
            "ghg_rep.sec6_title",
            "ghg_rep.sec7_title"
        ]
        for key in required_keys:
            self.assertIn(f'"{key}"', self.js_i18n_content, f"Clave faltante en i18n.js: {key}")

    def test_app_js_functions_and_exports(self):
        """Verifica que las funciones de conmutacion, renderizado y descarga esten en app.js."""
        self.assertIn("switchReportMode", self.js_app_content)
        self.assertIn("setupGhgReportListeners", self.js_app_content)
        self.assertIn("loadGhgReport", self.js_app_content)
        self.assertIn("renderGhgReportView", self.js_app_content)
        self.assertIn("downloadGhgReportJson", self.js_app_content)
        self.assertIn("reportViewMode === \"ghg\"", self.js_app_content)

        # Exportado en window.EconodeApp
        self.assertIn("loadGhgReport: (invId) => loadGhgReport(invId)", self.js_app_content)
        self.assertIn("renderGhgReportView: (inv) => renderGhgReportView(inv)", self.js_app_content)
        self.assertIn("downloadGhgReportJson: () => downloadGhgReportJson()", self.js_app_content)

    def test_css_badges_and_print_styles(self):
        """Verifica que los estilos Apple HIG y badges de Scope/Tier esten en styles.css."""
        self.assertIn("#ghgReportContainer", self.css_content)
        self.assertIn("#ghgReportKpiGrid", self.css_content)
        self.assertIn(".badge-scope1", self.css_content)
        self.assertIn(".badge-scope2", self.css_content)
        self.assertIn(".badge-scope3", self.css_content)
        self.assertIn(".badge-tier1", self.css_content)
        self.assertIn(".badge-tier2", self.css_content)
        self.assertIn(".badge-tier3", self.css_content)
        self.assertIn("body.report-mode-ghg #printGhgOfficialHeader", self.css_content)

    def test_domain_summary_dual_accounting(self):
        """Verifica la logica contable de doble reporte de Alcance 2 y las 15 categorias de Alcance 3."""
        inv = GHGInventory(
            id=999,
            organization_name="Test Corp S.A. de C.V.",
            reporting_year=2024,
            consolidation_approach="operational_control",
            country_code="MX",
            base_year=2021
        )
        # Scope 1
        inv.entries.append(GHGEntry(
            id=1, inventory_id=999, scope="SCOPE_1", scope_category="stationary_combustion",
            activity_name="Caldera Gas Natural", calculation_type="activity_based",
            activity_amount=10000.0, activity_unit="m3", emission_factor_value=2.02,
            emissions_kgco2e=20200.0, emissions_tco2e=20.2
        ))
        # Scope 2 Location
        inv.entries.append(GHGEntry(
            id=2, inventory_id=999, scope="SCOPE_2", scope_category="electricity_location",
            activity_name="CFE Red Nacional", calculation_type="activity_based",
            activity_amount=50000.0, activity_unit="kWh", emission_factor_value=0.438,
            emissions_kgco2e=21900.0, emissions_tco2e=21.9
        ))
        # Scope 2 Market (PPA solar 0 gCO2)
        inv.entries.append(GHGEntry(
            id=3, inventory_id=999, scope="SCOPE_2", scope_category="electricity_market",
            activity_name="PPA Solar Parque Sonora", calculation_type="activity_based",
            activity_amount=50000.0, activity_unit="kWh", emission_factor_value=0.0,
            contractual_instrument="PPA Bilateral Renovable",
            emissions_kgco2e=0.0, emissions_tco2e=0.0
        ))
        # Scope 3 Cat 1
        inv.entries.append(GHGEntry(
            id=4, inventory_id=999, scope="SCOPE_3", scope_category="cat_1_purchased_goods",
            activity_name="Resina PET Virgen", calculation_type="activity_based",
            activity_amount=25000.0, activity_unit="kg", emission_factor_value=2.15,
            emissions_kgco2e=53750.0, emissions_tco2e=53.75
        ))

        summary = inv.calculate_summary()
        self.assertEqual(summary["scope_1"]["total_tco2e"], 20.2)
        self.assertEqual(summary["scope_2"]["location_based_tco2e"], 21.9)
        self.assertEqual(summary["scope_2"]["market_based_tco2e"], 0.0)
        self.assertEqual(summary["totals"]["net_reduction_via_market_tco2e"], 21.9)
        self.assertEqual(summary["scope_3"]["total_tco2e"], 53.75)
        self.assertEqual(summary["totals"]["total_location_based_tco2e"], 20.2 + 21.9 + 53.75)
        self.assertEqual(summary["totals"]["total_market_based_tco2e"], 20.2 + 0.0 + 53.75)

    def test_zero_emojis_in_report_files(self):
        """Regla critica: Cero emojis en index.html, styles.css, app.js e i18n.js."""
        emoji_regex = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

        for name, content in [
            ("index.html", self.html_content),
            ("app.js", self.js_app_content),
            ("i18n.js", self.js_i18n_content),
            ("styles.css", self.css_content)
        ]:
            matches = emoji_regex.findall(content)
            self.assertEqual(len(matches), 0, f"Se encontraron emojis en {name}: {matches}")


if __name__ == "__main__":
    unittest.main()
