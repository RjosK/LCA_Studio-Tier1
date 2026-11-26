import unittest
import os
import json
import sys

# Ensure root path is in sys.path
sys.path.insert(0, os.getcwd())

from waste_engine import get_waste_engine, WasteEngine

class TestWasteEngineSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_waste_engine()

    def test_database_loaded(self):
        self.assertGreaterEqual(len(self.engine.materials), 200)
        self.assertIn('mswi', self.engine.technologies)
        self.assertIn('landfill', self.engine.technologies)
        self.assertIn('wastewater', self.engine.technologies)
        self.assertIn('open_burning', self.engine.technologies)
        self.assertIn('construction_landfill', self.engine.technologies)

    def test_categories(self):
        cats = self.engine.get_categories()
        self.assertIn('Plastics & Polymers', cats)
        self.assertIn('Biomass & Organic', cats)
        self.assertIn('Paper & Cardboard', cats)

    def test_incineration_calculation(self):
        mats = self.engine.get_materials(search='PET')
        self.assertTrue(len(mats) > 0)
        pet = mats[0]
        res = self.engine.calculate(material_id=pet['id'], mass_kg=100.0, technology='mswi')
        
        epd = res['epd_modules_gwp']
        self.assertGreater(epd['C4_final_disposal'], 100.0) # Fossil CO2 emissions from burning PET
        self.assertGreater(epd['C4_fossil_gwp'], 100.0)
        self.assertLess(epd['Module_D_avoided_burdens'], 0.0) # Avoided burdens are negative credits
        self.assertIn('Electricity recovered (kWh)', res['avoided_energy'])
        self.assertGreater(res['avoided_energy']['Electricity recovered (kWh)'], 50.0)

    def test_landfill_calculation(self):
        mats = self.engine.get_materials(search='wood')
        self.assertTrue(len(mats) > 0)
        res = self.engine.calculate(material_id=mats[0]['id'], mass_kg=100.0, technology='landfill')
        
        epd = res['epd_modules_gwp']
        self.assertGreater(epd['C4_final_disposal'], 0.0)
        self.assertIn('Carbon dioxide, biogenic (CO2)', res['lci_air_emissions'])

    def test_custom_stoichiometry(self):
        res = self.engine.calculate(
            custom_properties={
                'Hu': 22.0,
                'C': 0.60,
                'biogenic_c_share': 0.50,
                'H2O': 0.15,
                'N': 0.015,
                'S': 0.003,
                'degradability_100a': 0.30
            },
            mass_kg=50.0,
            technology='mswi'
        )
        epd = res['epd_modules_gwp']
        self.assertGreater(epd['C4_fossil_gwp'], 0.0)
        self.assertGreater(epd['C4_biogenic_gwp'], 0.0)
        self.assertLess(epd['Module_D_avoided_burdens'], 0.0)
        self.assertAlmostEqual(
            epd['Net_Total_GWP'],
            epd['C2_transport'] + epd['C3_waste_processing'] + epd['C4_final_disposal'] + epd['Module_D_avoided_burdens'],
            places=3
        )

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.engine.calculate(material_id='invalid_id_xyz', mass_kg=10.0)
        with self.assertRaises(ValueError):
            self.engine.calculate(mass_kg=-5.0)

    def test_i18n_waste_keys(self):
        i18n_path = 'public/js/i18n.js' if os.path.exists('public/js/i18n.js') else 'static/i18n.js'
        with open(i18n_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('"waste.modal_title"', content)
        self.assertIn('"waste.btn_calculate"', content)
        self.assertIn('"waste.gwp_net"', content)
        self.assertIn('"waste.tech_mswi"', content)
        self.assertIn('"waste.custom_hu"', content)

if __name__ == '__main__':
    unittest.main()
