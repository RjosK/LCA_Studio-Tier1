"""
econode_studio/infrastructure/seed_emission_factors.py - Sembrador de Factores de Emision Oficiales
Puebla la base de datos de factores de emision con datasets reconocidos de DEFRA 2024,
US EPA 2024, CRE Mexico 2024, ADEME y factores monetarios USEEIO para Scope 3.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Soporte de ejecucion directa o como modulo
infra_dir = Path(__file__).resolve().parent
if str(infra_dir) not in sys.path:
    sys.path.insert(0, str(infra_dir))

try:
    from emission_factors_db import get_ef_db_connection, init_emission_factors_db, seed_sample_inventory_if_needed
except ImportError:
    from .emission_factors_db import get_ef_db_connection, init_emission_factors_db, seed_sample_inventory_if_needed

SEED_EMISSION_FACTORS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 1. MEXICO (CRE / SEMARNAT 2024) - Alcance 1 y 2
    # -------------------------------------------------------------
    {
        "source_database": "CRE_MEXICO_2024",
        "scope_applicability": "SCOPE_2",
        "activity_category": "Electricity Grid",
        "factor_name": "Factor de Emision del Sistema Electrico Nacional (FESEN)",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.438,
        "co2_factor": 0.432,
        "ch4_factor": 0.003,
        "n2o_factor": 0.003,
        "geographic_scope": "MX",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"source": "Comision Reguladora de Energia (CRE)", "document": "Factor de Emision del SEN 2023-2024"})
    },
    {
        "source_database": "CRE_MEXICO_2024",
        "scope_applicability": "SCOPE_2",
        "activity_category": "Electricity Grid",
        "factor_name": "Factor de Emision del Sistema Interconectado Baja California (BCA)",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.395,
        "co2_factor": 0.390,
        "ch4_factor": 0.002,
        "n2o_factor": 0.003,
        "geographic_scope": "MX",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 4.0,
        "metadata_json": json.dumps({"source": "CRE Mexico", "system": "Baja California"})
    },

    # -------------------------------------------------------------
    # 2. DEFRA / DESNZ 2024 - ALCANCE 1 (Combustion Fija, Movil y Fugas)
    # -------------------------------------------------------------
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Stationary Combustion",
        "factor_name": "Gas Natural - Poder Calorifico Neto",
        "activity_unit": "m3",
        "gwp_factor_value": 2.0214,
        "co2_factor": 2.0160,
        "ch4_factor": 0.0027,
        "n2o_factor": 0.0027,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"density": "0.7-0.9 kg/m3", "standard": "DEFRA 2024 Fuels"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Stationary Combustion",
        "factor_name": "Gas Natural - Base Energetica",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.1825,
        "co2_factor": 0.1820,
        "ch4_factor": 0.0003,
        "n2o_factor": 0.0002,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 2.5,
        "metadata_json": json.dumps({"type": "Net CV", "standard": "DEFRA 2024"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Stationary Combustion",
        "factor_name": "Gas Licuado de Petroleo (GLP)",
        "activity_unit": "litres",
        "gwp_factor_value": 1.5571,
        "co2_factor": 1.5510,
        "ch4_factor": 0.0035,
        "n2o_factor": 0.0026,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"standard": "DEFRA 2024 Fuels"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Mobile Combustion",
        "factor_name": "Diesel Comercial (100% mineral)",
        "activity_unit": "litres",
        "gwp_factor_value": 2.6865,
        "co2_factor": 2.6580,
        "ch4_factor": 0.0035,
        "n2o_factor": 0.0250,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"standard": "DEFRA 2024 Road transport fuels"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Mobile Combustion",
        "factor_name": "Gasolina Regular",
        "activity_unit": "litres",
        "gwp_factor_value": 2.3391,
        "co2_factor": 2.3110,
        "ch4_factor": 0.0075,
        "n2o_factor": 0.0206,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"standard": "DEFRA 2024 Road transport fuels"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Fugitive Emissions",
        "factor_name": "Gas Refrigerante HFC-134a",
        "activity_unit": "kg",
        "gwp_factor_value": 1430.0,
        "co2_factor": 0.0,
        "ch4_factor": 0.0,
        "n2o_factor": 0.0,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 2.0,
        "metadata_json": json.dumps({"gas": "1,1,1,2-Tetrafluoroethane", "IPCC_AR5_GWP": 1430})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Fugitive Emissions",
        "factor_name": "Gas Refrigerante R-410A",
        "activity_unit": "kg",
        "gwp_factor_value": 2088.0,
        "co2_factor": 0.0,
        "ch4_factor": 0.0,
        "n2o_factor": 0.0,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 2.0,
        "metadata_json": json.dumps({"blend": "50% HFC-32 / 50% HFC-125", "IPCC_AR5_GWP": 2088})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_1",
        "activity_category": "Fugitive Emissions",
        "factor_name": "Hexafluoruro de Azufre (SF6)",
        "activity_unit": "kg",
        "gwp_factor_value": 23500.0,
        "co2_factor": 0.0,
        "ch4_factor": 0.0,
        "n2o_factor": 0.0,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 1.0,
        "metadata_json": json.dumps({"application": "Equipos de conmutacion electrica / Subestaciones"})
    },

    # -------------------------------------------------------------
    # 3. DEFRA / EPA 2024 - ALCANCE 2 (Electricidad Internacional)
    # -------------------------------------------------------------
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_2",
        "activity_category": "Electricity Grid",
        "factor_name": "Red Electrica Nacional Reino Unido (UK Grid)",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.2071,
        "co2_factor": 0.2050,
        "ch4_factor": 0.0011,
        "n2o_factor": 0.0010,
        "geographic_scope": "GB",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.0,
        "metadata_json": json.dumps({"standard": "DEFRA 2024 Electricity generation"})
    },
    {
        "source_database": "EPA_2024",
        "scope_applicability": "SCOPE_2",
        "activity_category": "Electricity Grid",
        "factor_name": "Red Electrica Promedio Nacional EE.UU. (US eGRID Average)",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.3855,
        "co2_factor": 0.3820,
        "ch4_factor": 0.0018,
        "n2o_factor": 0.0017,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 3.5,
        "metadata_json": json.dumps({"source": "US EPA eGRID 2024 Summary Tables"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_2",
        "activity_category": "Electricity Grid",
        "factor_name": "Electricidad 100% Renovable (PPA / I-REC Certificado)",
        "activity_unit": "kWh",
        "gwp_factor_value": 0.0000,
        "co2_factor": 0.0000,
        "ch4_factor": 0.0000,
        "n2o_factor": 0.0000,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 0.0,
        "metadata_json": json.dumps({"method": "Market-Based", "contractual_instrument": "I-REC / CEL / PPA con garantia de origen"})
    },

    # -------------------------------------------------------------
    # 4. DEFRA / GLEC 2024 - ALCANCE 3 (Transporte, Viajes y Residuos)
    # -------------------------------------------------------------
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_4",
        "activity_category": "Freight Transport",
        "factor_name": "Flete Terrestre - Camion Rigido 7.5t-17t (Promedio Carga)",
        "activity_unit": "ton.km",
        "gwp_factor_value": 0.2741,
        "co2_factor": 0.2715,
        "ch4_factor": 0.0005,
        "n2o_factor": 0.0021,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"standard": "GLEC Framework / DEFRA 2024"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_4",
        "activity_category": "Freight Transport",
        "factor_name": "Flete Terrestre - Trailer Articulado >33t (Promedio Carga)",
        "activity_unit": "ton.km",
        "gwp_factor_value": 0.0894,
        "co2_factor": 0.0885,
        "ch4_factor": 0.0002,
        "n2o_factor": 0.0007,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"standard": "GLEC Framework / DEFRA 2024"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_4",
        "activity_category": "Freight Transport",
        "factor_name": "Flete Aereo de Carga - Vuelo Internacional",
        "activity_unit": "ton.km",
        "gwp_factor_value": 1.1274,
        "co2_factor": 1.1180,
        "ch4_factor": 0.0014,
        "n2o_factor": 0.0080,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 8.0,
        "metadata_json": json.dumps({"type": "Dedicated cargo aircraft"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_4",
        "activity_category": "Freight Transport",
        "factor_name": "Flete Maritimo - Barco Portacontenedores Promedio",
        "activity_unit": "ton.km",
        "gwp_factor_value": 0.0161,
        "co2_factor": 0.0159,
        "ch4_factor": 0.0001,
        "n2o_factor": 0.0001,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 6.0,
        "metadata_json": json.dumps({"vessel": "Average container ship", "standard": "DEFRA / IMO"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_6",
        "activity_category": "Business Travel",
        "factor_name": "Vuelo Comercial - Clase Turista Corto Alcance (<3700 km)",
        "activity_unit": "passenger.km",
        "gwp_factor_value": 0.1535,
        "co2_factor": 0.1518,
        "ch4_factor": 0.0002,
        "n2o_factor": 0.0015,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"with_radiative_forcing": True})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_6",
        "activity_category": "Business Travel",
        "factor_name": "Vuelo Comercial - Clase Turista Largo Alcance (>3700 km)",
        "activity_unit": "passenger.km",
        "gwp_factor_value": 0.1931,
        "co2_factor": 0.1910,
        "ch4_factor": 0.0003,
        "n2o_factor": 0.0018,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"with_radiative_forcing": True})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_6",
        "activity_category": "Business Travel",
        "factor_name": "Estancia en Hotel (Promedio Global por Noche)",
        "activity_unit": "night",
        "gwp_factor_value": 14.20,
        "co2_factor": 14.05,
        "ch4_factor": 0.08,
        "n2o_factor": 0.07,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 10.0,
        "metadata_json": json.dumps({"source": "Cornell Hotel Sustainability Benchmarking"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_7",
        "activity_category": "Employee Commuting",
        "factor_name": "Autobus de Pasajeros Local / Urbano",
        "activity_unit": "passenger.km",
        "gwp_factor_value": 0.0965,
        "co2_factor": 0.0955,
        "ch4_factor": 0.0003,
        "n2o_factor": 0.0007,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 7.0,
        "metadata_json": json.dumps({"standard": "DEFRA 2024 Public transport"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_5",
        "activity_category": "Waste Generated in Operations",
        "factor_name": "Residuos Solidos Urbanos en Relleno Sanitario",
        "activity_unit": "ton",
        "gwp_factor_value": 442.50,
        "co2_factor": 2.10,
        "ch4_factor": 440.40,
        "n2o_factor": 0.0,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 15.0,
        "metadata_json": json.dumps({"disposal_route": "Landfill with methane flaring/recovery"})
    },
    {
        "source_database": "DEFRA_2024",
        "scope_applicability": "SCOPE_3_CAT_5",
        "activity_category": "Waste Generated in Operations",
        "factor_name": "Residuos Enviados a Reciclaje de Materiales",
        "activity_unit": "ton",
        "gwp_factor_value": 21.35,
        "co2_factor": 21.20,
        "ch4_factor": 0.10,
        "n2o_factor": 0.05,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 8.0,
        "metadata_json": json.dumps({"disposal_route": "Closed-loop / Open-loop material sorting"})
    },

    # -------------------------------------------------------------
    # 5. USEEIO v2.0 - ALCANCE 3 CATEGORIA 1 Y 2 (Metodo Spend-Based en USD)
    # -------------------------------------------------------------
    {
        "source_database": "USEEIO_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Spend-Based Purchased Goods",
        "factor_name": "Servicios de Software, TI y Cloud Computing",
        "activity_unit": "USD",
        "gwp_factor_value": 0.1420,  # kg CO2e / USD
        "co2_factor": 0.1390,
        "ch4_factor": 0.0015,
        "n2o_factor": 0.0015,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 12.0,
        "metadata_json": json.dumps({"sector": "NAICS 54151 - Computer systems design and related services"})
    },
    {
        "source_database": "USEEIO_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Spend-Based Purchased Goods",
        "factor_name": "Servicios Profesionales, Legales y Consultoria",
        "activity_unit": "USD",
        "gwp_factor_value": 0.0485,
        "co2_factor": 0.0475,
        "ch4_factor": 0.0005,
        "n2o_factor": 0.0005,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 10.0,
        "metadata_json": json.dumps({"sector": "NAICS 5411/5416 - Legal & Management consulting"})
    },
    {
        "source_database": "USEEIO_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Spend-Based Purchased Goods",
        "factor_name": "Fabricacion de Productos Quimicos y Resinas",
        "activity_unit": "USD",
        "gwp_factor_value": 0.6205,
        "co2_factor": 0.6050,
        "ch4_factor": 0.0100,
        "n2o_factor": 0.0055,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 15.0,
        "metadata_json": json.dumps({"sector": "NAICS 3251 - Basic chemical manufacturing"})
    },
    {
        "source_database": "USEEIO_2024",
        "scope_applicability": "SCOPE_3_CAT_2",
        "activity_category": "Spend-Based Capital Goods",
        "factor_name": "Maquinaria y Equipo Industrial",
        "activity_unit": "USD",
        "gwp_factor_value": 0.2850,
        "co2_factor": 0.2780,
        "ch4_factor": 0.0040,
        "n2o_factor": 0.0030,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 12.0,
        "metadata_json": json.dumps({"sector": "NAICS 3332 - Industrial machinery"})
    },
    {
        "source_database": "USEEIO_2024",
        "scope_applicability": "SCOPE_3_CAT_2",
        "activity_category": "Spend-Based Capital Goods",
        "factor_name": "Edificacion y Construccion de Naves Industriales",
        "activity_unit": "USD",
        "gwp_factor_value": 0.3120,
        "co2_factor": 0.3010,
        "ch4_factor": 0.0060,
        "n2o_factor": 0.0050,
        "geographic_scope": "US",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 14.0,
        "metadata_json": json.dumps({"sector": "NAICS 2362 - Nonresidential building construction"})
    },

    # -------------------------------------------------------------
    # 6. MATERIALES ESENCIALES (Cradle-to-Gate - Scope 3 Cat 1 Actividad)
    # -------------------------------------------------------------
    {
        "source_database": "ADEME_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Raw Materials",
        "factor_name": "Resina PET Virgen (Granulado)",
        "activity_unit": "kg",
        "gwp_factor_value": 2.1500,
        "co2_factor": 2.0800,
        "ch4_factor": 0.0500,
        "n2o_factor": 0.0200,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"source": "ADEME Base Empreinte / PlasticsEurope"})
    },
    {
        "source_database": "ADEME_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Raw Materials",
        "factor_name": "Resina PET Reciclada (rPET Post-Consumo)",
        "activity_unit": "kg",
        "gwp_factor_value": 0.6500,
        "co2_factor": 0.6200,
        "ch4_factor": 0.0200,
        "n2o_factor": 0.0100,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 6.0,
        "metadata_json": json.dumps({"source": "ADEME Base Empreinte / RecyClass"})
    },
    {
        "source_database": "ADEME_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Raw Materials",
        "factor_name": "Aluminio Primario en Lingote",
        "activity_unit": "kg",
        "gwp_factor_value": 8.2400,
        "co2_factor": 8.0100,
        "ch4_factor": 0.1200,
        "n2o_factor": 0.1100,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 7.0,
        "metadata_json": json.dumps({"source": "International Aluminium Institute"})
    },
    {
        "source_database": "ADEME_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Raw Materials",
        "factor_name": "Acero Estructural Comercial",
        "activity_unit": "kg",
        "gwp_factor_value": 1.8900,
        "co2_factor": 1.8500,
        "ch4_factor": 0.0200,
        "n2o_factor": 0.0200,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 6.0,
        "metadata_json": json.dumps({"source": "World Steel Association"})
    },
    {
        "source_database": "ADEME_2024",
        "scope_applicability": "SCOPE_3_CAT_1",
        "activity_category": "Raw Materials",
        "factor_name": "Carton Corrugado para Embalaje",
        "activity_unit": "kg",
        "gwp_factor_value": 0.9200,
        "co2_factor": 0.8900,
        "ch4_factor": 0.0200,
        "n2o_factor": 0.0100,
        "geographic_scope": "GLO",
        "valid_year": 2024,
        "gwp_standard": "AR5",
        "uncertainty_pct": 5.0,
        "metadata_json": json.dumps({"source": "FEFCO European Database"})
    }
]

SEED_CURRENCY_RATES = [
    {"base_currency": "USD", "target_currency": "MXN", "rate": 20.20, "reporting_year": 2024},
    {"base_currency": "USD", "target_currency": "EUR", "rate": 0.95, "reporting_year": 2024},
    {"base_currency": "USD", "target_currency": "GBP", "rate": 0.79, "reporting_year": 2024},
    {"base_currency": "USD", "target_currency": "MXN", "rate": 17.50, "reporting_year": 2023},
    {"base_currency": "USD", "target_currency": "EUR", "rate": 0.92, "reporting_year": 2023},
    {"base_currency": "USD", "target_currency": "GBP", "rate": 0.80, "reporting_year": 2023},
]

def seed_emission_factors(force_reload: bool = False, conn: Optional[Any] = None) -> int:
    """Inserta los factores de emision base y tasas de cambio en la base de datos."""
    if conn is not None:
        return _execute_seed(conn, force_reload)
    with get_ef_db_connection() as c:
        return _execute_seed(c, force_reload)

def _execute_seed(conn: Any, force_reload: bool = False) -> int:
    cursor = conn.cursor()

    # Comprobar si ya existen datos
    count = cursor.execute("SELECT COUNT(*) FROM tbl_emission_factors;").fetchone()[0]
    if count > 0 and not force_reload:
        return count

    if force_reload:
        cursor.execute("DELETE FROM tbl_emission_factors;")
        cursor.execute("DELETE FROM tbl_currency_rates;")
        cursor.execute("DELETE FROM tbl_ghg_entries;")
        cursor.execute("DELETE FROM tbl_ghg_inventories;")

    # Insertar tasas de cambio
    for cr in SEED_CURRENCY_RATES:
        cursor.execute("""
            INSERT OR REPLACE INTO tbl_currency_rates (base_currency, target_currency, rate, reporting_year)
            VALUES (?, ?, ?, ?);
        """, (cr["base_currency"], cr["target_currency"], cr["rate"], cr["reporting_year"]))

    # Insertar factores de emision
    inserted = 0
    for ef in SEED_EMISSION_FACTORS:
        cursor.execute("""
            INSERT INTO tbl_emission_factors (
                source_database, scope_applicability, activity_category, factor_name,
                activity_unit, gwp_factor_value, co2_factor, ch4_factor, n2o_factor,
                geographic_scope, valid_year, gwp_standard, uncertainty_pct, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            ef["source_database"], ef["scope_applicability"], ef["activity_category"], ef["factor_name"],
            ef["activity_unit"], ef["gwp_factor_value"], ef["co2_factor"], ef["ch4_factor"], ef["n2o_factor"],
            ef["geographic_scope"], ef["valid_year"], ef["gwp_standard"], ef["uncertainty_pct"], ef["metadata_json"]
        ))
        inserted += 1

    seed_sample_inventory_if_needed(cursor)
    conn.commit()
    return inserted

if __name__ == "__main__":
    count = seed_emission_factors(force_reload=True)
    print(f"Factores de emision sembrados exitosamente: {count}")
