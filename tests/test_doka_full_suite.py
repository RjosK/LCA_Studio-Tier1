"""
test_doka_full_suite.py
=======================
Suite de pruebas unitarias para la replicacion integral de WasteTools 2026 (Gabor Doka):
- Carga de catalogo y modelos
- Motor de mezclas compuestas (WasteMixtureEngine)
- Los 7 modelos tecnologicos (MSWI, Vertedero MSW, RCD, Excavacion, Quema abierta, Relaves mineros, PTAR)
- Exportadores SimaPro CSV y EcoSpold 2 XML
- Integridad de traducciones i18n
"""

import os
import unittest
from waste_suite_full import (
    get_doka_suite,
    WasteMixtureEngine,
    DokaIncinerationEngine,
    DokaLandfillEngine,
    DokaInertLandfillEngine,
    DokaTailingsEngine,
    DokaOpenBurningEngine,
    DokaWastewaterEngine,
    DokaExportEngine
)

class TestDokaFullSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.suite = get_doka_suite()

    def test_01_catalog_loaded(self):
        materials = self.suite.get_materials()
        self.assertGreaterEqual(len(materials), 200, "Debe haber al menos 200 materiales oficiales")
        categories = self.suite.get_categories()
        self.assertGreaterEqual(len(categories), 7, "Debe haber al menos 7 categorias de residuos")

    def test_02_waste_mixture_engine(self):
        fractions = [
            {"material_id": "dokamat_11", "share": 0.6}, # PE
            {"material_id": "dokamat_15", "share": 0.4}  # PET
        ]
        mix = self.suite.mix_fractions(fractions)
        self.assertIn("Mezcla Compuesta", mix["name"])
        self.assertGreater(mix["Hu"], 20.0, "PCI de mezcla de plasticos debe ser > 20 MJ/kg")
        self.assertGreater(mix["C"], 0.60, "Contenido de C debe ser > 60%")
        self.assertIn("ash", mix)

    def test_03_mswi_denox_and_metal_recovery(self):
        mat = self.suite.get_material_by_id("dokamat_11")
        # Calculo con SCR bajo polvo
        res_scr = self.suite.calculate_advanced("mswi", mat, mass_kg=100.0, denox="scr_low_dust", recovery_scrap=True)
        epd = res_scr["epd_modules_gwp"]
        self.assertIn("Net_Total_GWP", epd)
        self.assertGreater(epd["C4_final_disposal"], 0)
        self.assertLess(epd["Module_D_avoided_burdens"], 0, "Modulo D debe ser negativo (credito)")
        self.assertIn("avoided_materials", res_scr)
        self.assertIn("Scrap iron recovered (kg)", res_scr["avoided_materials"])

    def test_04_landfill_climate_and_gas(self):
        mat = self.suite.get_material_by_id("dokamat_11")
        res_ch = self.suite.calculate_advanced("landfill_msw", mat, mass_kg=100.0, climate_site="site_1_ch_temperate", gas_capture_rate=0.60)
        res_jo = self.suite.calculate_advanced("landfill_msw", mat, mass_kg=100.0, climate_site="site_2_jordan_arid", gas_capture_rate=0.20)
        self.assertIn("C4_methane_gwp", res_ch["epd_modules_gwp"])
        self.assertIn("lci_leachate_short_term_100a", res_ch)

    def test_05_inert_and_excavation_landfills(self):
        mat = self.suite.get_material_by_id("dokamat_10")
        res_cd = self.suite.calculate_advanced("landfill_cd", mat, mass_kg=200.0)
        res_ex = self.suite.calculate_advanced("landfill_excavation", mat, mass_kg=200.0)
        self.assertEqual(res_cd["epd_modules_gwp"]["C4_final_disposal"], 0.0)
        self.assertGreater(res_cd["epd_modules_gwp"]["C2_transport"], 0.0)

    def test_06_tailings_impoundment_ard(self):
        mat = self.suite.get_material_by_id("dokamat_10")
        res_ard = self.suite.calculate_advanced("tailings_impoundment", mat, mass_kg=500.0, ard_potential=True)
        res_neutral = self.suite.calculate_advanced("tailings_impoundment", mat, mass_kg=500.0, ard_potential=False)
        self.assertIn("lci_water_leachate_ard", res_ard)
        self.assertEqual(res_ard["technology"], "tailings_impoundment")

    def test_07_open_burning(self):
        mat = self.suite.get_material_by_id("dokamat_11")
        res_ob = self.suite.calculate_advanced("open_burning", mat, mass_kg=50.0)
        air = res_ob["lci_air_emissions"]
        self.assertIn("Black Carbon (BC) [g]", air)
        self.assertIn("Carbon monoxide (CO)", air)
        self.assertEqual(res_ob["epd_modules_gwp"]["Module_D_avoided_burdens"], 0.0)

    def test_08_wastewater_stages_and_sludge(self):
        mat = self.suite.get_material_by_id("dokamat_10")
        res_ww = self.suite.calculate_advanced("wastewater", mat, mass_kg=1000.0, treatment_stage="3_stage_chemical_p", sludge_fate="sludge_to_incineration")
        perf = res_ww["treatment_performance"]
        self.assertGreaterEqual(perf["P_removal_efficiency"], 0.90)
        self.assertGreater(perf["sludge_produced_dry_kg"], 0.0)

    def test_09_export_engines(self):
        mat = self.suite.get_material_by_id("dokamat_11")
        res = self.suite.calculate_advanced("mswi", mat, mass_kg=100.0)
        csv_simapro = DokaExportEngine.to_simapro_csv(res)
        self.assertIn("{SimaPro 9.5.0.0}", csv_simapro)
        self.assertIn("Avoided products", csv_simapro)

        xml_ecospold = DokaExportEngine.to_ecospold2_xml(res)
        self.assertIn("<ecoSpold", xml_ecospold)
        self.assertIn("<activityDataset>", xml_ecospold)

    def test_10_i18n_keys(self):
        i18n_file = r"public/js/i18n.js" if os.path.exists(r"public/js/i18n.js") else r"static/i18n.js"
        with open(i18n_file, "r", encoding="utf-8") as f:
            c = f.read()
        self.assertIn("waste.tab_mixture", c)
        self.assertIn("waste.tech_tailings", c)
        self.assertIn("waste.denox_label", c)
        self.assertIn("waste.climate_site_label", c)
        self.assertIn("waste.btn_export_simapro", c)

if __name__ == "__main__":
    unittest.main()
