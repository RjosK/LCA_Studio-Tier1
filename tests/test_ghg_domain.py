"""
ECONODE Tests - Pruebas Unitarias del Dominio y Servicios GHG Protocol
Valida las reglas contables, doble reporte Scope 2, conversion spend-based y vinculacion LCA.
"""

import unittest
import sys
from pathlib import Path

# Agregar raiz al sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from econode_studio.domain.ghg_inventory import GHGInventory, GHGEntry, SCOPE_CATEGORIES
from econode_studio.infrastructure.seed_emission_factors import seed_emission_factors
from econode_studio.infrastructure.emission_factors_db import search_emission_factors, get_currency_rate
from econode_studio.application.ghg_service import (
    create_inventory_use_case, get_inventory_by_id_use_case, add_entry_to_inventory_use_case,
    delete_entry_from_inventory_use_case, delete_inventory_use_case
)

class TestGHGDomainAndService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Asegurar factores base sembrados
        seed_emission_factors(force_reload=False)

    def test_scope_taxonomy(self):
        """Verifica que las 15 categorias de Scope 3 y los alcances 1 y 2 esten definidos."""
        self.assertIn("stationary_combustion", SCOPE_CATEGORIES)
        self.assertIn("electricity_location", SCOPE_CATEGORIES)
        self.assertIn("electricity_market", SCOPE_CATEGORIES)

        # Contar categorias de Scope 3
        s3_cats = [k for k, v in SCOPE_CATEGORIES.items() if v.get("scope") == "SCOPE_3"]
        self.assertEqual(len(s3_cats), 15)

    def test_currency_conversion(self):
        """Verifica la tasa de conversion para metodos spend-based."""
        rate_mxn_to_usd = get_currency_rate("MXN", "USD", 2024)
        self.assertGreater(rate_mxn_to_usd, 0.0)
        self.assertLess(rate_mxn_to_usd, 0.10) # ~0.0495 USD por MXN

    def test_search_emission_factors(self):
        """Verifica la busqueda de factores en la base desacoplada."""
        factors, total = search_emission_factors(query="Diesel", scope="SCOPE_1")
        self.assertGreater(total, 0)
        diesel = factors[0]
        self.assertIn("Diesel", diesel["factor_name"])
        self.assertGreater(diesel["gwp_factor_value"], 2.0)

    def test_complete_ghg_inventory_flow(self):
        """Prueba end-to-end de un inventario corporativo con Scope 1, 2 dual y 3."""
        # 1. Crear inventario
        inv_data = {
            "organization_name": "EcoManufactura del Norte S.A. de C.V.",
            "reporting_year": 2024,
            "consolidation_approach": "operational_control",
            "country_code": "MX",
            "description": "Inventario Corporativo Anual 2024"
        }
        inv = create_inventory_use_case(inv_data)
        inv_id = inv["id"]
        self.assertIsNotNone(inv_id)

        try:
            # 2. Agregar Scope 1: Gas Natural (10,000 m3) con DEFRA (2.0214 kg CO2e / m3)
            # Emisiones: 10,000 * 2.0214 = 20,214 kg = 20.214 tCO2e
            entry_s1 = {
                "scope_category": "stationary_combustion",
                "activity_name": "Calderas de Vapor Planta Central",
                "calculation_type": "activity_based",
                "activity_amount": 10000.0,
                "activity_unit": "m3",
                "emission_factor_value": 2.0214,
                "emission_factor_unit": "kg CO2e / m3",
                "emission_factor_source": "DEFRA 2024"
            }
            inv = add_entry_to_inventory_use_case(inv_id, entry_s1)

            # 3. Agregar Scope 2 (Location-Based): Red SEN (100,000 kWh) con CRE Mexico (0.438 kg CO2e / kWh)
            # Emisiones: 100,000 * 0.438 = 43,800 kg = 43.800 tCO2e
            entry_s2_loc = {
                "scope_category": "electricity_location",
                "activity_name": "Suministro CFE Red SEN",
                "calculation_type": "activity_based",
                "activity_amount": 100000.0,
                "activity_unit": "kWh",
                "emission_factor_value": 0.438,
                "emission_factor_unit": "kg CO2e / kWh",
                "emission_factor_source": "CRE 2024"
            }
            inv = add_entry_to_inventory_use_case(inv_id, entry_s2_loc)

            # 4. Agregar Scope 2 (Market-Based): PPA Solar con I-RECs (100,000 kWh a 0.0 kg CO2e / kWh)
            entry_s2_mkt = {
                "scope_category": "electricity_market",
                "activity_name": "PPA Parque Solar Sonora (Certificados I-REC)",
                "calculation_type": "activity_based",
                "activity_amount": 100000.0,
                "activity_unit": "kWh",
                "emission_factor_value": 0.0,
                "emission_factor_unit": "kg CO2e / kWh",
                "emission_factor_source": "I-REC Standard",
                "contractual_instrument": "i_rec"
            }
            inv = add_entry_to_inventory_use_case(inv_id, entry_s2_mkt)

            # 5. Agregar Scope 3 Cat 6 (Viajes de Negocios): Vuelos (20,000 passenger.km) a 0.1535 kg CO2e/km
            # Emisiones: 20,000 * 0.1535 = 3,070 kg = 3.070 tCO2e
            entry_s3_travel = {
                "scope_category": "cat_6_business_travel",
                "activity_name": "Vuelos Ejecutivos Comerciales",
                "calculation_type": "activity_based",
                "activity_amount": 20000.0,
                "activity_unit": "passenger.km",
                "emission_factor_value": 0.1535,
                "emission_factor_unit": "kg CO2e / p.km",
                "emission_factor_source": "DEFRA 2024"
            }
            inv = add_entry_to_inventory_use_case(inv_id, entry_s3_travel)

            # 6. Agregar Scope 3 Cat 1 Spend-Based: Gasto en Software Cloud ($200,000 MXN)
            # USEEIO factor = 0.1420 kg CO2e / USD
            # 200,000 MXN * 0.0495 = 9,900 USD * 0.1420 = 1,405.8 kg = 1.4058 tCO2e
            entry_s3_spend = {
                "scope_category": "cat_1_purchased_goods",
                "activity_name": "Suscripciones AWS y Software Contable",
                "calculation_type": "spend_based",
                "activity_amount": 200000.0,
                "activity_unit": "MXN",
                "currency": "MXN",
                "emission_factor_value": 0.1420,
                "emission_factor_unit": "kg CO2e / USD",
                "emission_factor_source": "USEEIO 2024"
            }
            inv = add_entry_to_inventory_use_case(inv_id, entry_s3_spend)

            # 7. Validaciones del Resumen Ejecutivo
            summary = inv["summary"]
            self.assertEqual(summary["entries_count"], 5)

            # Scope 1 esperado: 20.214 tCO2e
            self.assertAlmostEqual(summary["scope_1"]["total_tco2e"], 20.214, places=2)

            # Scope 2 Location esperado: 43.800 tCO2e
            self.assertAlmostEqual(summary["scope_2"]["location_based_tco2e"], 43.800, places=2)

            # Scope 2 Market esperado: 0.0 tCO2e (debido al PPA 100% renovable con I-RECs)
            self.assertAlmostEqual(summary["scope_2"]["market_based_tco2e"], 0.0, places=2)
            self.assertTrue(summary["scope_2"]["has_market_instruments"])

            # Scope 3 esperado: 3.070 (vuelos) + 1.406 (software) ~ 4.476 tCO2e
            self.assertGreater(summary["scope_3"]["total_tco2e"], 4.0)
            self.assertLess(summary["scope_3"]["total_tco2e"], 5.0)

            # Totales
            totals = summary["totals"]
            # Location-based: 20.214 + 43.800 + 4.476 ~ 68.49 tCO2e
            self.assertAlmostEqual(totals["total_location_based_tco2e"], 20.214 + 43.800 + summary["scope_3"]["total_tco2e"], places=2)

            # Market-based: 20.214 + 0.0 + 4.476 ~ 24.69 tCO2e
            self.assertAlmostEqual(totals["total_market_based_tco2e"], 20.214 + summary["scope_3"]["total_tco2e"], places=2)

            # Reduccion lograda por I-RECs / Mercado: 43.8 tCO2e
            self.assertAlmostEqual(totals["net_reduction_via_market_tco2e"], 43.800, places=2)

        finally:
            delete_inventory_use_case(inv_id)

if __name__ == "__main__":
    unittest.main()
