"""
econode_studio/domain/epd_models.py - Entidades de Dominio, Taxonomia y Plantillas EPD
Alineado con ISO 14025, ISO 21930:2017, EN 15804+A2:2019 y la arquitectura Part A / Part B de SmartEPD.
Enfoque inicial en la industria de Cemento y Concreto con registro extensible multi-industria.
"""

from typing import Dict, List, Any
import copy

# =============================================================================
# 1. TAXONOMIA OFICIAL DE MODULOS DE CICLO DE VIDA (EN 15804+A2 / ISO 21930)
# =============================================================================
EPD_MODULES: List[Dict[str, Any]] = [
    {"code": "A1", "stage": "product", "stage_es": "Etapa de Producto", "stage_en": "Product Stage", "name_es": "Suministro de Materias Primas", "name_en": "Raw Material Supply", "mandatory_ctg": True},
    {"code": "A2", "stage": "product", "stage_es": "Etapa de Producto", "stage_en": "Product Stage", "name_es": "Transporte a Planta", "name_en": "Transport to Manufacturer", "mandatory_ctg": True},
    {"code": "A3", "stage": "product", "stage_es": "Etapa de Producto", "stage_en": "Product Stage", "name_es": "Manufactura en Planta", "name_en": "Manufacturing", "mandatory_ctg": True},
    {"code": "A4", "stage": "construction", "stage_es": "Proceso de Construccion", "stage_en": "Construction Process Stage", "name_es": "Transporte a Obra", "name_en": "Transport to Building Site", "mandatory_ctg": False},
    {"code": "A5", "stage": "construction", "stage_es": "Proceso de Construccion", "stage_en": "Construction Process Stage", "name_es": "Instalacion y Construccion", "name_en": "Installation / Construction", "mandatory_ctg": False},
    {"code": "B1", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Uso / Carbonatacion en Servicio", "name_en": "Use / In-Service Carbonation", "mandatory_ctg": False},
    {"code": "B2", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Mantenimiento", "name_en": "Maintenance", "mandatory_ctg": False},
    {"code": "B3", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Reparacion", "name_en": "Repair", "mandatory_ctg": False},
    {"code": "B4", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Reemplazo", "name_en": "Replacement", "mandatory_ctg": False},
    {"code": "B5", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Rehabilitacion", "name_en": "Refurbishment", "mandatory_ctg": False},
    {"code": "B6", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Uso de Energia Operacional", "name_en": "Operational Energy Use", "mandatory_ctg": False},
    {"code": "B7", "stage": "use", "stage_es": "Etapa de Uso", "stage_en": "Use Stage", "name_es": "Uso de Agua Operacional", "name_en": "Operational Water Use", "mandatory_ctg": False},
    {"code": "C1", "stage": "eol", "stage_es": "Etapa de Fin de Vida", "stage_en": "End-of-Life Stage", "name_es": "Deconstruccion / Demolicion", "name_en": "Deconstruction / Demolition", "mandatory_ctg": False},
    {"code": "C2", "stage": "eol", "stage_es": "Etapa de Fin de Vida", "stage_en": "End-of-Life Stage", "name_es": "Transporte de Residuos", "name_en": "Transport to Waste Processing", "mandatory_ctg": False},
    {"code": "C3", "stage": "eol", "stage_es": "Etapa de Fin de Vida", "stage_en": "End-of-Life Stage", "name_es": "Procesamiento de Residuos", "name_en": "Waste Processing", "mandatory_ctg": False},
    {"code": "C4", "stage": "eol", "stage_es": "Etapa de Fin de Vida", "stage_en": "End-of-Life Stage", "name_es": "Disposicion Final", "name_en": "Disposal", "mandatory_ctg": False},
    {"code": "D", "stage": "beyond", "stage_es": "Mas Alla del Limite", "stage_en": "Beyond System Boundary", "name_es": "Beneficios por Reuso y Reciclaje", "name_en": "Reuse, Recovery, Recycling Potential", "mandatory_ctg": False},
]

EPD_MODULE_CODES = [m["code"] for m in EPD_MODULES]

# =============================================================================
# 2. REGISTRO DE PCRs MULTI-INDUSTRIA (ARQUITECTURA SMARTEPD PART A + PART B)
# =============================================================================
SMART_EPD_PCR_REGISTRY: List[Dict[str, Any]] = [
    {
        "industry_id": "cement_concrete",
        "industry_es": "Cemento y Concreto",
        "industry_en": "Cement & Concrete",
        "status": "active",
        "pcrs": [
            {
                "pcr_code": "Smart EPD Part B 1000-010",
                "title": "Smart EPD Part B PCR for Cements for Construction (ISO 21930 / EN 16908)",
                "declared_unit": "1 metric ton (1,000 kg)",
                "default_boundary": "A1-A3",
                "un_cpc": "37440"
            },
            {
                "pcr_code": "Smart EPD Part B / NSF Concrete PCR",
                "title": "Product Category Rule for Concrete (ISO 21930 / EN 16757)",
                "declared_unit": "1 m3",
                "default_boundary": "A1-A3",
                "un_cpc": "37510"
            }
        ]
    },
    {
        "industry_id": "steel",
        "industry_es": "Acero Estructural y Varilla",
        "industry_en": "Designated Steel Construction Products",
        "status": "roadmap",
        "pcrs": [
            {
                "pcr_code": "Smart EPD Part B Steel v3.0",
                "title": "Smart EPD Part B PCR for Designated Steel Construction Products",
                "declared_unit": "1 metric ton (1,000 kg)",
                "default_boundary": "A1-A3",
                "un_cpc": "412"
            }
        ]
    },
    {
        "industry_id": "asphalt",
        "industry_es": "Asfalto y Ligantes Asfalticos",
        "industry_en": "Asphalt Binders & Mixtures",
        "status": "roadmap",
        "pcrs": [
            {
                "pcr_code": "Smart EPD Part B Asphalt",
                "title": "Smart EPD Part B PCR for Asphalt Binders",
                "declared_unit": "1 metric ton (1,000 kg)",
                "default_boundary": "A1-A3",
                "un_cpc": "15330"
            }
        ]
    },
    {
        "industry_id": "gypsum",
        "industry_es": "Paneles de Yeso",
        "industry_en": "Gypsum Panels",
        "status": "roadmap",
        "pcrs": [
            {
                "pcr_code": "Smart EPD Part B Gypsum v2.0",
                "title": "Smart EPD Part B PCR for Gypsum Panels",
                "declared_unit": "1 m2 (o 1,000 ft2)",
                "default_boundary": "A1-A5, C1-C4",
                "un_cpc": "37530"
            }
        ]
    },
    {
        "industry_id": "lime_masonry",
        "industry_es": "Cal y Mamposteria",
        "industry_en": "Lime & Masonry Products",
        "status": "roadmap",
        "pcrs": [
            {
                "pcr_code": "Smart EPD Part B Lime",
                "title": "Smart EPD Part B PCR for Lime Products",
                "declared_unit": "1 metric ton (1,000 kg)",
                "default_boundary": "A1-A3",
                "un_cpc": "37420"
            }
        ]
    }
]

# =============================================================================
# 3. CATALOGO DE INDICADORES EPD (EN 15804+A2 Y TRACI 2.1 / ISO 21930)
# =============================================================================
EPD_INDICATORS_EN15804_A2: List[Dict[str, str]] = [
    {"key": "gwp_total", "code": "GWP-total", "name_es": "Potencial de Calentamiento Global - Total", "name_en": "Global Warming Potential - Total", "unit": "kg CO2 eq"},
    {"key": "gwp_fossil", "code": "GWP-fossil", "name_es": "Potencial de Calentamiento Global - Fosil", "name_en": "Global Warming Potential - Fossil", "unit": "kg CO2 eq"},
    {"key": "gwp_biogenic", "code": "GWP-biogenic", "name_es": "Potencial de Calentamiento Global - Biogenico", "name_en": "Global Warming Potential - Biogenic", "unit": "kg CO2 eq"},
    {"key": "gwp_luluc", "code": "GWP-luluc", "name_es": "Calentamiento Global - Cambio Uso de Suelo", "name_en": "Global Warming Potential - Land Use & Change", "unit": "kg CO2 eq"},
    {"key": "odp", "code": "ODP", "name_es": "Agotamiento de la Capa de Ozono", "name_en": "Ozone Depletion Potential", "unit": "kg CFC-11 eq"},
    {"key": "ap", "code": "AP", "name_es": "Potencial de Acidificacion", "name_en": "Acidification Potential", "unit": "mol H+ eq"},
    {"key": "ep_freshwater", "code": "EP-freshwater", "name_es": "Eutrofizacion de Agua Dulce", "name_en": "Eutrophication Potential - Freshwater", "unit": "kg P eq"},
    {"key": "ep_marine", "code": "EP-marine", "name_es": "Eutrofizacion Marina", "name_en": "Eutrophication Potential - Marine", "unit": "kg N eq"},
    {"key": "ep_terrestrial", "code": "EP-terrestrial", "name_es": "Eutrofizacion Terrestre", "name_en": "Eutrophication Potential - Terrestrial", "unit": "mol N eq"},
    {"key": "pocp", "code": "POCP", "name_es": "Formacion de Ozono Fotoquimico", "name_en": "Photochemical Ozone Creation Potential", "unit": "kg NMVOC eq"},
    {"key": "adp_minerals", "code": "ADP-minerals", "name_es": "Agotamiento Abiotico - Minerales y Metales", "name_en": "Abiotic Depletion - Minerals & Metals", "unit": "kg Sb eq"},
    {"key": "adp_fossil", "code": "ADP-fossil", "name_es": "Agotamiento Abiotico - Combustibles Fosiles", "name_en": "Abiotic Depletion - Fossil Resources", "unit": "MJ, NCV"},
    {"key": "wdp", "code": "WDP", "name_es": "Potencial de Privacion de Agua", "name_en": "Water Deprivation Potential", "unit": "m3 world eq"},
]

EPD_INDICATORS_TRACI_2_1: List[Dict[str, str]] = [
    {"key": "gwp_total", "code": "GWP100", "name_es": "Potencial de Calentamiento Global (IPCC AR5/AR6)", "name_en": "Global Warming Potential (GWP100)", "unit": "kg CO2 eq"},
    {"key": "odp", "code": "ODP", "name_es": "Agotamiento de la Capa de Ozono", "name_en": "Ozone Depletion Potential", "unit": "kg CFC-11 eq"},
    {"key": "ap_traci", "code": "AP", "name_es": "Potencial de Acidificacion (TRACI)", "name_en": "Acidification Potential", "unit": "kg SO2 eq"},
    {"key": "ep_traci", "code": "EP", "name_es": "Potencial de Eutrofizacion (TRACI)", "name_en": "Eutrophication Potential", "unit": "kg N eq"},
    {"key": "sfp", "code": "SFP", "name_es": "Formacion de Smog Fotoquimico", "name_en": "Smog Formation Potential", "unit": "kg O3 eq"},
    {"key": "ffd", "code": "FFD", "name_es": "Agotamiento de Combustibles Fosiles", "name_en": "Fossil Fuel Depletion", "unit": "MJ surplus"},
]

EPD_RESOURCE_INDICATORS: List[Dict[str, str]] = [
    {"key": "pere", "code": "PERE", "name_es": "Energia primaria renovable como portador energetico", "name_en": "Renewable primary energy as energy carrier", "unit": "MJ"},
    {"key": "perm", "code": "PERM", "name_es": "Energia primaria renovable como materia prima", "name_en": "Renewable primary energy as material", "unit": "MJ"},
    {"key": "pert", "code": "PERT", "name_es": "Uso total de energia primaria renovable", "name_en": "Total renewable primary energy use", "unit": "MJ"},
    {"key": "penre", "code": "PENRE", "name_es": "Energia primaria no renovable como portador energetico", "name_en": "Non-renewable primary energy as energy carrier", "unit": "MJ"},
    {"key": "penrm", "code": "PENRM", "name_es": "Energia primaria no renovable como materia prima", "name_en": "Non-renewable primary energy as material", "unit": "MJ"},
    {"key": "penrt", "code": "PENRT", "name_es": "Uso total de energia primaria no renovable", "name_en": "Total non-renewable primary energy use", "unit": "MJ"},
    {"key": "sm", "code": "SM", "name_es": "Uso de materiales secundarios (SCMs / Reciclados)", "name_en": "Use of secondary materials (SCMs / Recycled)", "unit": "kg"},
    {"key": "rsf", "code": "RSF", "name_es": "Combustibles secundarios renovables", "name_en": "Use of renewable secondary fuels", "unit": "MJ"},
    {"key": "nrsf", "code": "NRSF", "name_es": "Combustibles secundarios no renovables", "name_en": "Use of non-renewable secondary fuels", "unit": "MJ"},
    {"key": "fw", "code": "FW", "name_es": "Uso neto de agua dulce", "name_en": "Net use of fresh water", "unit": "m3"},
]

EPD_WASTE_OUTPUT_INDICATORS: List[Dict[str, str]] = [
    {"key": "hwd", "code": "HWD", "name_es": "Residuos peligrosos dispuestos", "name_en": "Hazardous waste disposed", "unit": "kg"},
    {"key": "nhwd", "code": "NHWD", "name_es": "Residuos no peligrosos dispuestos", "name_en": "Non-hazardous waste disposed", "unit": "kg"},
    {"key": "rwd", "code": "RWD", "name_es": "Residuos radiactivos dispuestos", "name_en": "Radioactive waste disposed", "unit": "kg"},
    {"key": "cru", "code": "CRU", "name_es": "Componentes para reutilizacion", "name_en": "Components for re-use", "unit": "kg"},
    {"key": "mfr", "code": "MFR", "name_es": "Materiales para reciclaje", "name_en": "Materials for recycling", "unit": "kg"},
    {"key": "mer", "code": "MER", "name_es": "Materiales para recuperacion energetica", "name_en": "Materials for energy recovery", "unit": "kg"},
    {"key": "ee", "code": "EE", "name_es": "Energia exportada (electrica y termica)", "name_en": "Exported energy (electrical & thermal)", "unit": "MJ"},
]


# =============================================================================
# 4. PLANTILLAS PRELIMINARES EPD - INDUSTRIA DE CEMENTO Y CONCRETO
# =============================================================================
EPD_PRELIMINARY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "epd_cement_cpo": {
        "template_id": "epd_cement_cpo",
        "industry_id": "cement_concrete",
        "sub_sector": "cement",
        "name_es": "Cemento Portland Ordinario (CPO 40 / Tipo I / CEM I)",
        "name_en": "Ordinary Portland Cement (OPC / Type I / CEM I)",
        "short_desc_es": "Modelo Cradle-to-Gate (A1-A3) para 1 tonelada de cemento Portland ordinario con ~92% de clinker, calcinacion directa en horno rotatorio y molienda con yeso.",
        "short_desc_en": "Cradle-to-Gate (A1-A3) model for 1 metric ton of Ordinary Portland Cement (~92% clinker) covering quarrying, inbound freight, kiln calcination, and finish grinding.",
        "code_prefix": "EPD-CEM-CPO",
        "declared_unit_amount": 1.0,
        "declared_unit_symbol": "t",
        "declared_unit_label_es": "1 tonelada metrica (1,000 kg) de cemento Portland ordinario a granel en puerta de planta",
        "declared_unit_label_en": "1 metric ton (1,000 kg) of bulk Ordinary Portland Cement at plant gate",
        "system_boundary": "Cradle-to-Gate (A1-A3)",
        "declared_modules": ["A1", "A2", "A3"],
        "pcr_reference": "Smart EPD Part B 1000-010: Cements for Construction / EN 16908",
        "standards": "ISO 14025, ISO 21930:2017, EN 15804+A2:2019",
        "un_cpc": "37440",
        "category": "Construccion & Edificacion",
        "geography": "[MX]",
        "key_override": {
            "param_name": "clinker_ratio_pct",
            "label_es": "Relacion Clinker / Cemento (%)",
            "label_en": "Clinker-to-Cement Ratio (%)",
            "default": 92.0,
            "min": 65.0,
            "max": 98.0,
            "unit": "%"
        },
        "composition": [
            {"material_es": "Clinker de cemento Portland", "material_en": "Portland cement clinker", "mass_kg": 920.0, "share_pct": 92.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Yeso natural / Sulfato de calcio", "material_en": "Natural gypsum / Calcium sulfate", "mass_kg": 50.0, "share_pct": 5.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Caliza de adicion (Filler)", "material_en": "Limestone filler", "mass_kg": 30.0, "share_pct": 3.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0}
        ],
        "technical_specs": {
            "standard_norm": "NMX-C-414-ONNCCE / ASTM C150 Type I / EN 197-1 CEM I",
            "strength_class": "40 MPa (28 dias)",
            "clinker_ratio_pct": 92.0,
            "bulk_density_kg_m3": 1440.0
        },
        "parameters": [
            {"name": "clinker_ratio_pct", "value": 92.0, "unit": "%", "group": "Composicion", "description": "Porcentaje masico de clinker en el cemento terminado"},
            {"name": "kiln_thermal_mj_kg", "value": 3.35, "unit": "MJ/kg", "group": "Proceso Horno", "description": "Consumo termico especifico del horno rotatorio por kg de clinker"},
            {"name": "plant_electricity_kwh_t", "value": 105.0, "unit": "kWh/t", "group": "Energia", "description": "Consumo electrico total de molienda de crudo, horno y cemento"},
            {"name": "a2_transport_km", "value": 85.0, "unit": "km", "group": "Logistica A2", "description": "Distancia promedio ponderada de suministro de materias primas y combustibles"}
        ],
        "nodes": [
            {
                "id": "node_epd_cpo_a1",
                "process_id": 910101,
                "code": "EPD-CPO-A1",
                "name": "A1: Extraccion y Preparacion de Materias Primas (Caliza, Arcilla, Yeso)",
                "category": "Extraccion Mineral",
                "location": "[MX]",
                "epd_module": "A1",
                "x": 60,
                "y": 140,
                "reference_flow": {"name": "Harina cruda y adiciones minerales", "amount": 1625.0, "unit": "kg"},
                "inputs": [
                    {"name": "Limestone, crushed, for mill [MX]", "amount": 1350.0, "unit": "kg", "is_unit": False},
                    {"name": "Clay, quarried [MX]", "amount": 215.0, "unit": "kg", "is_unit": False},
                    {"name": "Iron ore / corrective mineral [GLO]", "amount": 30.0, "unit": "kg", "is_unit": False},
                    {"name": "Gypsum, mineral [MX]", "amount": 50.0, "unit": "kg", "is_unit": False},
                    {"name": "Limestone filler, milled [MX]", "amount": 30.0, "unit": "kg", "is_unit": False},
                    {"name": "Diesel fuel, quarry machinery", "amount": 2.4, "unit": "l", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Harina cruda y adiciones minerales", "amount": 1625.0, "unit": "kg", "is_reference": True},
                    {"name": "Quarry overburden / mineral dust (Waste)", "amount": 12.0, "unit": "kg", "is_waste": True}
                ]
            },
            {
                "id": "node_epd_cpo_a2",
                "process_id": 910102,
                "code": "EPD-CPO-A2",
                "name": "A2: Transporte Inbound de Insumos y Combustibles a Planta",
                "category": "Logistica Inbound",
                "location": "[MX]",
                "epd_module": "A2",
                "x": 430,
                "y": 140,
                "reference_flow": {"name": "Insumos entregados en planta cementera", "amount": 1625.0, "unit": "kg"},
                "inputs": [
                    {"name": "Harina cruda y adiciones minerales", "amount": 1625.0, "unit": "kg", "is_unit": True},
                    {"name": "Freight lorry transport >32t EURO5 [MX]", "amount": 142.3, "unit": "t*km", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Insumos entregados en planta cementera", "amount": 1625.0, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_cpo_a3",
                "process_id": 910103,
                "code": "EPD-CPO-A3",
                "name": "A3: Clinkerizacion en Horno Rotatorio y Molienda Final (CPO 40)",
                "category": "Manufactura Cemento",
                "location": "[MX]",
                "epd_module": "A3",
                "x": 800,
                "y": 140,
                "reference_flow": {"name": "Cemento Portland Ordinario CPO 40", "amount": 1.0, "unit": "t"},
                "inputs": [
                    {"name": "Insumos entregados en planta cementera", "amount": 1625.0, "unit": "kg", "is_unit": True},
                    {"name": "Petroleum coke (petcoke), kiln fuel", "amount": 68.0, "unit": "kg", "is_unit": False},
                    {"name": "Natural gas, thermal kiln burner", "amount": 18.0, "unit": "m3", "is_unit": False},
                    {"name": "Electricity, medium voltage grid [MX]", "amount": 105.0, "unit": "kWh", "is_unit": False},
                    {"name": "Industrial cooling water [MX]", "amount": 0.28, "unit": "m3", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Cemento Portland Ordinario CPO 40", "amount": 1.0, "unit": "t", "is_reference": True},
                    {"name": "Carbon dioxide, fossil (Clinker calcination CaCO3->CaO+CO2) [Air]", "amount": 483.0, "unit": "kg", "is_elementary": True},
                    {"name": "Nitrogen oxides (NOx) [Air]", "amount": 1.15, "unit": "kg", "is_elementary": True},
                    {"name": "Sulfur dioxide (SO2) [Air]", "amount": 0.28, "unit": "kg", "is_elementary": True},
                    {"name": "Cement kiln dust / refractory waste (Non-hazardous)", "amount": 4.5, "unit": "kg", "is_waste": True}
                ]
            }
        ],
        "edges": [
            {"from": "node_epd_cpo_a1", "to": "node_epd_cpo_a2", "source_process_id": 910101, "target_process_id": 910102, "flow": "Harina cruda y adiciones minerales", "flow_id": "FL_CPO_A1_A2", "amount": 1625.0, "unit": "kg"},
            {"from": "node_epd_cpo_a2", "to": "node_epd_cpo_a3", "source_process_id": 910102, "target_process_id": 910103, "flow": "Insumos entregados en planta cementera", "flow_id": "FL_CPO_A2_A3", "amount": 1625.0, "unit": "kg"}
        ]
    },

    "epd_cement_cpc": {
        "template_id": "epd_cement_cpc",
        "industry_id": "cement_concrete",
        "sub_sector": "cement",
        "name_es": "Cemento Portland Compuesto / Mezclado (CPC 30R / Tipo IL / CEM II)",
        "name_en": "Blended Portland Cement (CPC 30R / Type IL / CEM II)",
        "short_desc_es": "Modelo Cradle-to-Gate (A1-A3) para 1 tonelada de cemento compuesto con 70% de clinker y 25% de adiciones cementantes (puzolana/ceniza volante y caliza).",
        "short_desc_en": "Cradle-to-Gate (A1-A3) model for 1 metric ton of blended cement (70% clinker) incorporating pozzolan/fly ash SCMs and limestone filler to reduce embodied carbon.",
        "code_prefix": "EPD-CEM-CPC",
        "declared_unit_amount": 1.0,
        "declared_unit_symbol": "t",
        "declared_unit_label_es": "1 tonelada metrica (1,000 kg) de cemento Portland compuesto CPC 30R en puerta de planta",
        "declared_unit_label_en": "1 metric ton (1,000 kg) of blended Portland cement CPC 30R at plant gate",
        "system_boundary": "Cradle-to-Gate (A1-A3)",
        "declared_modules": ["A1", "A2", "A3"],
        "pcr_reference": "Smart EPD Part B 1000-010: Cements for Construction / EN 16908",
        "standards": "ISO 14025, ISO 21930:2017, EN 15804+A2:2019",
        "un_cpc": "37440",
        "category": "Construccion & Edificacion",
        "geography": "[MX]",
        "key_override": {
            "param_name": "clinker_ratio_pct",
            "label_es": "Relacion Clinker / Cemento (%)",
            "label_en": "Clinker-to-Cement Ratio (%)",
            "default": 70.0,
            "min": 45.0,
            "max": 85.0,
            "unit": "%"
        },
        "composition": [
            {"material_es": "Clinker de cemento Portland", "material_en": "Portland cement clinker", "mass_kg": 700.0, "share_pct": 70.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Puzolana natural / Ceniza volante (SCM)", "material_en": "Natural pozzolan / Fly ash (SCM)", "mass_kg": 180.0, "share_pct": 18.0, "post_consumer_pct": 18.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Caliza micronizada (Filler)", "material_en": "Limestone filler", "mass_kg": 70.0, "share_pct": 7.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Yeso natural / Sulfato de calcio", "material_en": "Natural gypsum", "mass_kg": 50.0, "share_pct": 5.0, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0}
        ],
        "technical_specs": {
            "standard_norm": "NMX-C-414-ONNCCE CPC 30R / ASTM C595 Type IL / EN 197-1 CEM II/B",
            "strength_class": "30R MPa (28 dias)",
            "clinker_ratio_pct": 70.0,
            "bulk_density_kg_m3": 1380.0
        },
        "parameters": [
            {"name": "clinker_ratio_pct", "value": 70.0, "unit": "%", "group": "Composicion", "description": "Fraccion masica de clinker en el cemento compuesto"},
            {"name": "scm_pozzolan_pct", "value": 18.0, "unit": "%", "group": "Composicion", "description": "Porcentaje de puzolana o ceniza volante como SCM"},
            {"name": "plant_electricity_kwh_t", "value": 112.0, "unit": "kWh/t", "group": "Energia", "description": "Electricidad total de molienda conjunta (clinker + adiciones)"},
            {"name": "a2_transport_km", "value": 110.0, "unit": "km", "group": "Logistica A2", "description": "Distancia media de suministro de materias primas y SCMs"}
        ],
        "nodes": [
            {
                "id": "node_epd_cpc_a1",
                "process_id": 910201,
                "code": "EPD-CPC-A1",
                "name": "A1: Materias Primas Minerales y Adiciones Cementantes (SCMs)",
                "category": "Extraccion y SCMs",
                "location": "[MX]",
                "epd_module": "A1",
                "x": 60,
                "y": 140,
                "reference_flow": {"name": "Crudo mineral y adiciones SCM", "amount": 1520.0, "unit": "kg"},
                "inputs": [
                    {"name": "Limestone, crushed, for mill [MX]", "amount": 1030.0, "unit": "kg", "is_unit": False},
                    {"name": "Clay, quarried [MX]", "amount": 165.0, "unit": "kg", "is_unit": False},
                    {"name": "Fly ash / natural pozzolan (Secondary SCM)", "amount": 180.0, "unit": "kg", "is_unit": False},
                    {"name": "Limestone filler, milled [MX]", "amount": 70.0, "unit": "kg", "is_unit": False},
                    {"name": "Gypsum, mineral [MX]", "amount": 50.0, "unit": "kg", "is_unit": False},
                    {"name": "Iron ore / corrective mineral [GLO]", "amount": 25.0, "unit": "kg", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Crudo mineral y adiciones SCM", "amount": 1520.0, "unit": "kg", "is_reference": True},
                    {"name": "Quarry mineral tailings (Waste)", "amount": 9.0, "unit": "kg", "is_waste": True}
                ]
            },
            {
                "id": "node_epd_cpc_a2",
                "process_id": 910202,
                "code": "EPD-CPC-A2",
                "name": "A2: Transporte de Materias Primas y SCMs a Planta",
                "category": "Logistica Inbound",
                "location": "[MX]",
                "epd_module": "A2",
                "x": 430,
                "y": 140,
                "reference_flow": {"name": "Insumos minerales en planta", "amount": 1520.0, "unit": "kg"},
                "inputs": [
                    {"name": "Crudo mineral y adiciones SCM", "amount": 1520.0, "unit": "kg", "is_unit": True},
                    {"name": "Freight lorry transport >32t EURO5 [MX]", "amount": 167.2, "unit": "t*km", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Insumos minerales en planta", "amount": 1520.0, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_cpc_a3",
                "process_id": 910203,
                "code": "EPD-CPC-A3",
                "name": "A3: Horno Rotatorio (70% Clinker) y Molienda Compuesta CPC 30R",
                "category": "Manufactura Cemento",
                "location": "[MX]",
                "epd_module": "A3",
                "x": 800,
                "y": 140,
                "reference_flow": {"name": "Cemento Portland Compuesto CPC 30R", "amount": 1.0, "unit": "t"},
                "inputs": [
                    {"name": "Insumos minerales en planta", "amount": 1520.0, "unit": "kg", "is_unit": True},
                    {"name": "Petroleum coke (petcoke), kiln fuel", "amount": 51.0, "unit": "kg", "is_unit": False},
                    {"name": "Natural gas, thermal kiln burner", "amount": 14.0, "unit": "m3", "is_unit": False},
                    {"name": "Electricity, medium voltage grid [MX]", "amount": 112.0, "unit": "kWh", "is_unit": False},
                    {"name": "Industrial cooling water [MX]", "amount": 0.24, "unit": "m3", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Cemento Portland Compuesto CPC 30R", "amount": 1.0, "unit": "t", "is_reference": True},
                    {"name": "Carbon dioxide, fossil (Clinker calcination 70%) [Air]", "amount": 367.5, "unit": "kg", "is_elementary": True},
                    {"name": "Nitrogen oxides (NOx) [Air]", "amount": 0.88, "unit": "kg", "is_elementary": True},
                    {"name": "Sulfur dioxide (SO2) [Air]", "amount": 0.21, "unit": "kg", "is_elementary": True},
                    {"name": "Kiln bypass dust (Non-hazardous waste)", "amount": 3.5, "unit": "kg", "is_waste": True}
                ]
            }
        ],
        "edges": [
            {"from": "node_epd_cpc_a1", "to": "node_epd_cpc_a2", "source_process_id": 910201, "target_process_id": 910202, "flow": "Crudo mineral y adiciones SCM", "flow_id": "FL_CPC_A1_A2", "amount": 1520.0, "unit": "kg"},
            {"from": "node_epd_cpc_a2", "to": "node_epd_cpc_a3", "source_process_id": 910202, "target_process_id": 910203, "flow": "Insumos minerales en planta", "flow_id": "FL_CPC_A2_A3", "amount": 1520.0, "unit": "kg"}
        ]
    },

    "epd_concrete_rmx_4000": {
        "template_id": "epd_concrete_rmx_4000",
        "industry_id": "cement_concrete",
        "sub_sector": "concrete",
        "name_es": "Concreto Premezclado Estructural (f'c 250-300 kg/cm2 / 4,000 psi)",
        "name_en": "Structural Ready-Mix Concrete (4,000 psi / C30/37)",
        "short_desc_es": "Modelo Cradle-to-Gate (A1-A3) para 1 m3 de concreto estructural convencional siguiendo NSF / SmartEPD Concrete PCR y EN 16757.",
        "short_desc_en": "Cradle-to-Gate (A1-A3) model for 1 m3 of standard structural ready-mix concrete aligned with SmartEPD / NSF Concrete PCR and EN 16757.",
        "code_prefix": "EPD-CON-4000",
        "declared_unit_amount": 1.0,
        "declared_unit_symbol": "m3",
        "declared_unit_label_es": "1 metro cubico (1 m3) de concreto premezclado estructural f'c 280 kg/cm2 (4,000 psi) en puerta de planta",
        "declared_unit_label_en": "1 cubic meter (1 m3) of structural ready-mix concrete 4,000 psi (28 MPa) at batch plant gate",
        "system_boundary": "Cradle-to-Gate (A1-A3)",
        "declared_modules": ["A1", "A2", "A3"],
        "pcr_reference": "Smart EPD Part B / NSF Product Category Rule for Concrete (ISO 21930 / EN 16757)",
        "standards": "ISO 14025, ISO 21930:2017, EN 15804+A2:2019",
        "un_cpc": "37510",
        "category": "Construccion & Edificacion",
        "geography": "[MX]",
        "key_override": {
            "param_name": "cement_dosage_kg_m3",
            "label_es": "Dosificacion de Cemento (kg / m3)",
            "label_en": "Cement Dosage (kg / m3)",
            "default": 340.0,
            "min": 220.0,
            "max": 480.0,
            "unit": "kg/m3"
        },
        "composition": [
            {"material_es": "Cemento Portland (CPO / Tipo I)", "material_en": "Portland Cement (OPC / Type I)", "mass_kg": 340.0, "share_pct": 14.5, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agregado grueso (Grava triturada 20mm)", "material_en": "Coarse aggregate (Crushed gravel 20mm)", "mass_kg": 1050.0, "share_pct": 44.7, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agregado fino (Arena silica lavada)", "material_en": "Fine aggregate (Washed silica sand)", "mass_kg": 780.0, "share_pct": 33.2, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agua de mezclado", "material_en": "Batching water", "mass_kg": 175.0, "share_pct": 7.5, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Aditivo quimico reductor de agua", "material_en": "Chemical water-reducing admixture", "mass_kg": 2.5, "share_pct": 0.1, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0}
        ],
        "technical_specs": {
            "standard_norm": "NMX-C-155-ONNCCE / ASTM C94 / ACI 318",
            "compressive_strength_28d": "28 MPa (280 kg/cm2 / 4,000 psi)",
            "slump_cm": "14 +/- 2.5 cm",
            "water_cement_ratio": 0.51,
            "density_kg_m3": 2347.5
        },
        "parameters": [
            {"name": "cement_dosage_kg_m3", "value": 340.0, "unit": "kg/m3", "group": "Diseno de Mezcla", "description": "Contenido de cemento Portland por metro cubico"},
            {"name": "water_cement_ratio", "value": 0.51, "unit": "ratio", "group": "Diseno de Mezcla", "description": "Relacion agua/cemento efectiva"},
            {"name": "a2_cement_km", "value": 140.0, "unit": "km", "group": "Logistica A2", "description": "Distancia de transporte del cemento a planta dosificadora"},
            {"name": "a2_aggregates_km", "value": 45.0, "unit": "km", "group": "Logistica A2", "description": "Distancia de transporte de grava y arena desde banco"}
        ],
        "nodes": [
            {
                "id": "node_epd_con_a1_binder",
                "process_id": 910301,
                "code": "EPD-CON-A1a",
                "name": "A1: Suministro de Cemento Portland y Aditivos Quimicos",
                "category": "Cementantes A1",
                "location": "[MX]",
                "epd_module": "A1",
                "x": 50,
                "y": 70,
                "reference_flow": {"name": "Paquete cementante y aditivos", "amount": 342.5, "unit": "kg"},
                "inputs": [
                    {"name": "Portland cement, CEM I / OPC [MX]", "amount": 340.0, "unit": "kg", "is_unit": False},
                    {"name": "Concrete chemical admixture (plasticizer)", "amount": 2.5, "unit": "kg", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Paquete cementante y aditivos", "amount": 342.5, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_con_a1_agg",
                "process_id": 910302,
                "code": "EPD-CON-A1b",
                "name": "A1: Agregados Petreos (Grava, Arena) y Agua de Mezcla",
                "category": "Agregados A1",
                "location": "[MX]",
                "epd_module": "A1",
                "x": 50,
                "y": 290,
                "reference_flow": {"name": "Agregados y agua para 1 m3", "amount": 2005.0, "unit": "kg"},
                "inputs": [
                    {"name": "Gravel, crushed aggregate [MX]", "amount": 1050.0, "unit": "kg", "is_unit": False},
                    {"name": "Sand, washed silica aggregate [MX]", "amount": 780.0, "unit": "kg", "is_unit": False},
                    {"name": "Batching water, municipal/well [MX]", "amount": 0.175, "unit": "m3", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Agregados y agua para 1 m3", "amount": 2005.0, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_con_a2",
                "process_id": 910303,
                "code": "EPD-CON-A2",
                "name": "A2: Transporte de Cemento y Agregados a Planta Dosificadora",
                "category": "Logistica Inbound",
                "location": "[MX]",
                "epd_module": "A2",
                "x": 450,
                "y": 175,
                "reference_flow": {"name": "Insumos en planta dosificadora", "amount": 2347.5, "unit": "kg"},
                "inputs": [
                    {"name": "Paquete cementante y aditivos", "amount": 342.5, "unit": "kg", "is_unit": True},
                    {"name": "Agregados y agua para 1 m3", "amount": 2005.0, "unit": "kg", "is_unit": True},
                    {"name": "Freight lorry transport >32t EURO5 [MX]", "amount": 130.0, "unit": "t*km", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Insumos en planta dosificadora", "amount": 2347.5, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_con_a3",
                "process_id": 910304,
                "code": "EPD-CON-A3",
                "name": "A3: Dosificacion, Mezclado y Operacion de Planta de Concreto",
                "category": "Planta Concreto",
                "location": "[MX]",
                "epd_module": "A3",
                "x": 830,
                "y": 175,
                "reference_flow": {"name": "Concreto Premezclado Estructural 4,000 psi", "amount": 1.0, "unit": "m3"},
                "inputs": [
                    {"name": "Insumos en planta dosificadora", "amount": 2347.5, "unit": "kg", "is_unit": True},
                    {"name": "Electricity, batching plant grid [MX]", "amount": 4.8, "unit": "kWh", "is_unit": False},
                    {"name": "Diesel fuel, front-end loader", "amount": 1.2, "unit": "l", "is_unit": False},
                    {"name": "Plant washout water [MX]", "amount": 0.035, "unit": "m3", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Concreto Premezclado Estructural 4,000 psi", "amount": 1.0, "unit": "m3", "is_reference": True},
                    {"name": "Hardened concrete plant waste (Non-hazardous)", "amount": 18.0, "unit": "kg", "is_waste": True},
                    {"name": "Admixture drum residue (Hazardous waste)", "amount": 0.04, "unit": "kg", "is_waste": True}
                ]
            }
        ],
        "edges": [
            {"from": "node_epd_con_a1_binder", "to": "node_epd_con_a2", "source_process_id": 910301, "target_process_id": 910303, "flow": "Paquete cementante y aditivos", "flow_id": "FL_CON_A1a_A2", "amount": 342.5, "unit": "kg"},
            {"from": "node_epd_con_a1_agg", "to": "node_epd_con_a2", "source_process_id": 910302, "target_process_id": 910303, "flow": "Agregados y agua para 1 m3", "flow_id": "FL_CON_A1b_A2", "amount": 2005.0, "unit": "kg"},
            {"from": "node_epd_con_a2", "to": "node_epd_con_a3", "source_process_id": 910303, "target_process_id": 910304, "flow": "Insumos en planta dosificadora", "flow_id": "FL_CON_A2_A3", "amount": 2347.5, "unit": "kg"}
        ]
    },

    "epd_concrete_low_carbon_a1_d": {
        "template_id": "epd_concrete_low_carbon_a1_d",
        "industry_id": "cement_concrete",
        "sub_sector": "concrete",
        "name_es": "Concreto Estructural Bajo Carbono con SCMs (Ciclo Completo A1-A5, C1-C4, D)",
        "name_en": "Low-Carbon Concrete with SCMs (Cradle-to-Grave + Module D)",
        "short_desc_es": "Modelo completo Cradle-to-Grave con Modulo D para 1 m3 de concreto bajo carbono (37% sustitucion con escoria GGBFS y ceniza volante), entrega en camion olla, bombeo, demolicion, trituracion y credito de reciclaje.",
        "short_desc_en": "Full Cradle-to-Grave + Module D model for 1 m3 of low-carbon concrete (37% GGBFS/fly ash replacement), transit mixer delivery (A4), placement (A5), demolition/crushing (C1-C4), and recycled aggregate credit (D).",
        "code_prefix": "EPD-CON-LC37",
        "declared_unit_amount": 1.0,
        "declared_unit_symbol": "m3",
        "declared_unit_label_es": "1 metro cubico (1 m3) de concreto estructural bajo carbono f'c 280 kg/cm2 con 37% SCMs",
        "declared_unit_label_en": "1 cubic meter (1 m3) of low-carbon structural concrete (28 MPa) with 37% SCMs",
        "system_boundary": "Cradle-to-Grave with Module D (A1-A5, C1-C4, D)",
        "declared_modules": ["A1", "A2", "A3", "A4", "A5", "C1", "C2", "C3", "C4", "D"],
        "pcr_reference": "Smart EPD Part B / EN 16757 Concrete Full Lifecycle PCR",
        "standards": "ISO 14025, ISO 21930:2017, EN 15804+A2:2019",
        "un_cpc": "37510",
        "category": "Construccion & Edificacion",
        "geography": "[MX]",
        "key_override": {
            "param_name": "cement_dosage_kg_m3",
            "label_es": "Dosificacion Cemento Portland Base (kg / m3)",
            "label_en": "Base Portland Cement Dosage (kg / m3)",
            "default": 220.0,
            "min": 140.0,
            "max": 320.0,
            "unit": "kg/m3"
        },
        "composition": [
            {"material_es": "Cemento Portland (CPO / Tipo I)", "material_en": "Portland Cement (OPC)", "mass_kg": 220.0, "share_pct": 9.4, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Escoria granulada de alto horno (GGBFS)", "material_en": "Ground granulated blast furnace slag (GGBFS)", "mass_kg": 85.0, "share_pct": 3.6, "post_consumer_pct": 3.6, "biogenic_carbon_kg": 0.0},
            {"material_es": "Ceniza volante clase F (Fly Ash)", "material_en": "Class F Fly Ash", "mass_kg": 45.0, "share_pct": 1.9, "post_consumer_pct": 1.9, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agregado grueso (Grava triturada)", "material_en": "Coarse aggregate (Crushed gravel)", "mass_kg": 1030.0, "share_pct": 44.2, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agregado fino (Arena silica)", "material_en": "Fine aggregate (Silica sand)", "mass_kg": 775.0, "share_pct": 33.3, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Agua de mezclado", "material_en": "Batching water", "mass_kg": 170.0, "share_pct": 7.3, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0},
            {"material_es": "Superplastificante policarboxilato", "material_en": "Polycarboxylate superplasticizer", "mass_kg": 3.2, "share_pct": 0.14, "post_consumer_pct": 0.0, "biogenic_carbon_kg": 0.0}
        ],
        "technical_specs": {
            "standard_norm": "NMX-C-155-ONNCCE / ASTM C94 / EN 206",
            "compressive_strength_28d": "28 MPa (280 kg/cm2 / 4,000 psi)",
            "scm_substitution_pct": 37.1,
            "water_cement_ratio": 0.49,
            "eol_recycling_rate_pct": 75.0,
            "density_kg_m3": 2328.2
        },
        "parameters": [
            {"name": "cement_dosage_kg_m3", "value": 220.0, "unit": "kg/m3", "group": "Diseno de Mezcla", "description": "Cemento Portland base por m3"},
            {"name": "ggbfs_slag_kg_m3", "value": 85.0, "unit": "kg/m3", "group": "SCMs", "description": "Escoria granulada de alto horno (material secundario)"},
            {"name": "fly_ash_kg_m3", "value": 45.0, "unit": "kg/m3", "group": "SCMs", "description": "Ceniza volante clase F (material secundario)"},
            {"name": "a4_mixer_km", "value": 25.0, "unit": "km", "group": "Construccion A4-A5", "description": "Distancia en camion olla de planta a obra"},
            {"name": "eol_recycling_rate_pct", "value": 75.0, "unit": "%", "group": "Fin de Vida C-D", "description": "Fraccion de concreto demolido triturado a agregado reciclado"}
        ],
        "nodes": [
            {
                "id": "node_epd_lc_a1",
                "process_id": 910401,
                "code": "EPD-LC-A1",
                "name": "A1: Cemento, SCMs (Escoria GGBFS, Ceniza Volante) y Agregados",
                "category": "Materias Primas A1",
                "location": "[MX]",
                "epd_module": "A1",
                "x": 40,
                "y": 100,
                "reference_flow": {"name": "Insumos para 1 m3 concreto bajo carbono", "amount": 2328.2, "unit": "kg"},
                "inputs": [
                    {"name": "Portland cement, CEM I / OPC [MX]", "amount": 220.0, "unit": "kg", "is_unit": False},
                    {"name": "GGBFS blast furnace slag (Secondary SCM)", "amount": 85.0, "unit": "kg", "is_unit": False},
                    {"name": "Fly ash, class F (Secondary SCM)", "amount": 45.0, "unit": "kg", "is_unit": False},
                    {"name": "Gravel, crushed aggregate [MX]", "amount": 1030.0, "unit": "kg", "is_unit": False},
                    {"name": "Sand, washed silica aggregate [MX]", "amount": 775.0, "unit": "kg", "is_unit": False},
                    {"name": "Batching water, municipal/well [MX]", "amount": 0.170, "unit": "m3", "is_unit": False},
                    {"name": "Concrete chemical admixture (superplasticizer)", "amount": 3.2, "unit": "kg", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Insumos para 1 m3 concreto bajo carbono", "amount": 2328.2, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_lc_a2",
                "process_id": 910402,
                "code": "EPD-LC-A2",
                "name": "A2: Transporte Inbound de Cemento, SCMs y Agregados",
                "category": "Logistica A2",
                "location": "[MX]",
                "epd_module": "A2",
                "x": 380,
                "y": 100,
                "reference_flow": {"name": "Insumos en planta dosificadora", "amount": 2328.2, "unit": "kg"},
                "inputs": [
                    {"name": "Insumos para 1 m3 concreto bajo carbono", "amount": 2328.2, "unit": "kg", "is_unit": True},
                    {"name": "Freight lorry transport >32t EURO5 [MX]", "amount": 145.0, "unit": "t*km", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Insumos en planta dosificadora", "amount": 2328.2, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_lc_a3",
                "process_id": 910403,
                "code": "EPD-LC-A3",
                "name": "A3: Mezclado y Dosificacion en Planta de Concreto",
                "category": "Manufactura A3",
                "location": "[MX]",
                "epd_module": "A3",
                "x": 720,
                "y": 100,
                "reference_flow": {"name": "Concreto bajo carbono en planta", "amount": 1.0, "unit": "m3"},
                "inputs": [
                    {"name": "Insumos en planta dosificadora", "amount": 2328.2, "unit": "kg", "is_unit": True},
                    {"name": "Electricity, batching plant grid [MX]", "amount": 5.0, "unit": "kWh", "is_unit": False},
                    {"name": "Diesel fuel, front-end loader", "amount": 1.1, "unit": "l", "is_unit": False},
                    {"name": "Plant washout water [MX]", "amount": 0.030, "unit": "m3", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Concreto bajo carbono en planta", "amount": 1.0, "unit": "m3", "is_reference": True},
                    {"name": "Hardened concrete plant waste (Non-hazardous)", "amount": 14.0, "unit": "kg", "is_waste": True}
                ]
            },
            {
                "id": "node_epd_lc_a4",
                "process_id": 910404,
                "code": "EPD-LC-A4",
                "name": "A4: Transporte a Obra en Camion Olla (25 km)",
                "category": "Construccion A4",
                "location": "[MX]",
                "epd_module": "A4",
                "x": 1060,
                "y": 100,
                "reference_flow": {"name": "Concreto entregado en obra", "amount": 1.0, "unit": "m3"},
                "inputs": [
                    {"name": "Concreto bajo carbono en planta", "amount": 1.0, "unit": "m3", "is_unit": True},
                    {"name": "Transit mixer truck transport [MX]", "amount": 58.2, "unit": "t*km", "is_unit": False},
                    {"name": "Diesel fuel, mixer drum agitation", "amount": 2.8, "unit": "l", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Concreto entregado en obra", "amount": 1.0, "unit": "m3", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_lc_a5",
                "process_id": 910405,
                "code": "EPD-LC-A5",
                "name": "A5: Bombeo, Colado y Merma en Sitio (2%)",
                "category": "Construccion A5",
                "location": "[MX]",
                "epd_module": "A5",
                "x": 40,
                "y": 360,
                "reference_flow": {"name": "Concreto colocado en estructura", "amount": 1.0, "unit": "m3"},
                "inputs": [
                    {"name": "Concreto entregado en obra", "amount": 1.0, "unit": "m3", "is_unit": True},
                    {"name": "Diesel fuel, concrete pump & vibrators", "amount": 1.8, "unit": "l", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Concreto colocado en estructura", "amount": 1.0, "unit": "m3", "is_reference": True},
                    {"name": "On-site concrete placement waste (Non-hazardous)", "amount": 46.5, "unit": "kg", "is_waste": True}
                ]
            },
            {
                "id": "node_epd_lc_c1",
                "process_id": 910406,
                "code": "EPD-LC-C1",
                "name": "C1: Demolicion de Estructura de Concreto",
                "category": "Fin de Vida C1",
                "location": "[MX]",
                "epd_module": "C1",
                "x": 380,
                "y": 360,
                "reference_flow": {"name": "Escombro de concreto demolido", "amount": 2328.2, "unit": "kg"},
                "inputs": [
                    {"name": "Concreto colocado en estructura", "amount": 1.0, "unit": "m3", "is_unit": True},
                    {"name": "Diesel fuel, hydraulic demolition hammer", "amount": 3.4, "unit": "l", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Escombro de concreto demolido", "amount": 2328.2, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_lc_c2",
                "process_id": 910407,
                "code": "EPD-LC-C2",
                "name": "C2: Transporte de Escombro a Trituracion / Relleno (35 km)",
                "category": "Fin de Vida C2",
                "location": "[MX]",
                "epd_module": "C2",
                "x": 720,
                "y": 360,
                "reference_flow": {"name": "Escombro en planta de gestion", "amount": 2328.2, "unit": "kg"},
                "inputs": [
                    {"name": "Escombro de concreto demolido", "amount": 2328.2, "unit": "kg", "is_unit": True},
                    {"name": "Freight lorry transport >32t EURO5 [MX]", "amount": 81.5, "unit": "t*km", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Escombro en planta de gestion", "amount": 2328.2, "unit": "kg", "is_reference": True}
                ]
            },
            {
                "id": "node_epd_lc_c3",
                "process_id": 910408,
                "code": "EPD-LC-C3",
                "name": "C3: Trituracion y Clasificacion para Agregado Reciclado (75%)",
                "category": "Fin de Vida C3",
                "location": "[MX]",
                "epd_module": "C3",
                "x": 1060,
                "y": 360,
                "reference_flow": {"name": "Agregado reciclado de concreto (RCA)", "amount": 1746.0, "unit": "kg"},
                "inputs": [
                    {"name": "Escombro en planta de gestion", "amount": 1746.0, "unit": "kg", "is_unit": True},
                    {"name": "Diesel fuel, mobile jaw crusher", "amount": 2.1, "unit": "l", "is_unit": False},
                    {"name": "Electricity, sorting screen [MX]", "amount": 2.5, "unit": "kWh", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Agregado reciclado de concreto (RCA)", "amount": 1746.0, "unit": "kg", "is_reference": True},
                    {"name": "Recycled concrete aggregate for recycling (MFR)", "amount": 1746.0, "unit": "kg", "is_waste": False, "epd_output_flow": "mfr"}
                ]
            },
            {
                "id": "node_epd_lc_c4",
                "process_id": 910409,
                "code": "EPD-LC-C4",
                "name": "C4: Disposicion Final en Relleno de Inertes (25%)",
                "category": "Fin de Vida C4",
                "location": "[MX]",
                "epd_module": "C4",
                "x": 720,
                "y": 580,
                "reference_flow": {"name": "Fraccion inerte dispuesta", "amount": 582.2, "unit": "kg"},
                "inputs": [
                    {"name": "Escombro en planta de gestion", "amount": 582.2, "unit": "kg", "is_unit": True},
                    {"name": "Inert landfill disposal operation", "amount": 582.2, "unit": "kg", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Fraccion inerte dispuesta", "amount": 582.2, "unit": "kg", "is_reference": True},
                    {"name": "Inert concrete debris landfilled (Non-hazardous)", "amount": 582.2, "unit": "kg", "is_waste": True}
                ]
            },
            {
                "id": "node_epd_lc_d",
                "process_id": 910410,
                "code": "EPD-LC-D",
                "name": "D: Credito por Sustitucion de Grava Virgen con RCA",
                "category": "Beneficios Modulo D",
                "location": "[MX]",
                "epd_module": "D",
                "x": 1060,
                "y": 580,
                "reference_flow": {"name": "Credito neto por sustitucion de aridos", "amount": 1746.0, "unit": "kg"},
                "inputs": [
                    {"name": "Agregado reciclado de concreto (RCA)", "amount": 1746.0, "unit": "kg", "is_unit": True},
                    {"name": "Avoided virgin gravel extraction credit (Module D)", "amount": -1746.0, "unit": "kg", "is_unit": False}
                ],
                "outputs": [
                    {"name": "Credito neto por sustitucion de aridos", "amount": 1746.0, "unit": "kg", "is_reference": True}
                ]
            }
        ],
        "edges": [
            {"from": "node_epd_lc_a1", "to": "node_epd_lc_a2", "source_process_id": 910401, "target_process_id": 910402, "flow": "Insumos para 1 m3 concreto bajo carbono", "flow_id": "FL_LC_A1_A2", "amount": 2328.2, "unit": "kg"},
            {"from": "node_epd_lc_a2", "to": "node_epd_lc_a3", "source_process_id": 910402, "target_process_id": 910403, "flow": "Insumos en planta dosificadora", "flow_id": "FL_LC_A2_A3", "amount": 2328.2, "unit": "kg"},
            {"from": "node_epd_lc_a3", "to": "node_epd_lc_a4", "source_process_id": 910403, "target_process_id": 910404, "flow": "Concreto bajo carbono en planta", "flow_id": "FL_LC_A3_A4", "amount": 1.0, "unit": "m3"},
            {"from": "node_epd_lc_a4", "to": "node_epd_lc_a5", "source_process_id": 910404, "target_process_id": 910405, "flow": "Concreto entregado en obra", "flow_id": "FL_LC_A4_A5", "amount": 1.0, "unit": "m3"},
            {"from": "node_epd_lc_a5", "to": "node_epd_lc_c1", "source_process_id": 910405, "target_process_id": 910406, "flow": "Concreto colocado en estructura", "flow_id": "FL_LC_A5_C1", "amount": 1.0, "unit": "m3"},
            {"from": "node_epd_lc_c1", "to": "node_epd_lc_c2", "source_process_id": 910406, "target_process_id": 910407, "flow": "Escombro de concreto demolido", "flow_id": "FL_LC_C1_C2", "amount": 2328.2, "unit": "kg"},
            {"from": "node_epd_lc_c2", "to": "node_epd_lc_c3", "source_process_id": 910407, "target_process_id": 910408, "flow": "Escombro en planta de gestion", "flow_id": "FL_LC_C2_C3", "amount": 1746.0, "unit": "kg"},
            {"from": "node_epd_lc_c2", "to": "node_epd_lc_c4", "source_process_id": 910407, "target_process_id": 910409, "flow": "Escombro en planta de gestion", "flow_id": "FL_LC_C2_C4", "amount": 582.2, "unit": "kg"},
            {"from": "node_epd_lc_c3", "to": "node_epd_lc_d", "source_process_id": 910408, "target_process_id": 910410, "flow": "Agregado reciclado de concreto (RCA)", "flow_id": "FL_LC_C3_D", "amount": 1746.0, "unit": "kg"}
        ]
    }
}


def get_default_epd_config(system_name: str, declared_unit: str = "1.0 u", org_name: str = "ECONODE Industrial", geography: str = "[MX]", template_id: str = "") -> Dict[str, Any]:
    """Genera el bloque estandar de metadatos administrativos EPD estilo SmartEPD."""
    tpl = EPD_PRELIMINARY_TEMPLATES.get(template_id)
    if tpl:
        return {
            "is_epd_enabled": True,
            "template_id": template_id,
            "industry_id": tpl["industry_id"],
            "sub_sector": tpl["sub_sector"],
            "program_operator": "Smart EPD (Borrador Compatible / ECONODE Studio)",
            "pcr_reference": tpl["pcr_reference"],
            "standards": tpl["standards"],
            "declaration_number": f"EPD-ECONODE-2026-{tpl['code_prefix'].split('-')[-1]}",
            "declaration_holder": org_name,
            "plant_location": f"Planta Industrial Principal ({geography})",
            "product_name": system_name,
            "declared_unit": tpl["declared_unit_label_es"],
            "declared_unit_en": tpl["declared_unit_label_en"],
            "declared_unit_amount": tpl["declared_unit_amount"],
            "declared_unit_symbol": tpl["declared_unit_symbol"],
            "un_cpc": tpl["un_cpc"],
            "system_boundary": tpl["system_boundary"],
            "declared_modules": list(tpl["declared_modules"]),
            "default_standard": "EN15804_A2",
            "issue_date": "2026-11-17",
            "valid_until": "2031-11-17",
            "verification_type": "Independent Third-Party Verification (Pending / Draft)",
            "verifier_name": "Auditor Lider Acreditado ISO 14025 / NOM-070",
            "reference_service_life": "No declarada (Cradle-to-Gate)" if "A1-A3" in tpl["system_boundary"] else "50 anos (Estructura de edificacion)",
            "composition": copy.deepcopy(tpl["composition"]),
            "technical_specs": copy.deepcopy(tpl["technical_specs"]),
            "scenarios_notes": "Los escenarios de transporte (A2/A4) consideran camion pesado diesel EURO 5. La composicion y consumos energeticos son editables directamente en el lienzo de procesos.",
            "comparability_statement_es": "Las Declaraciones Ambientales de Producto (EPD) dentro de la misma categoria de producto pero de diferentes operadores de programa pueden no ser comparables. Para productos de construccion, las EPD solo son comparables si cumplen con ISO 21930 / EN 15804 y se evaluan en el contexto del edificio completo.",
            "comparability_statement_en": "Environmental Product Declarations (EPDs) within the same product category but from different programs may not be comparable. EPDs of construction products may not be comparable if they do not comply with ISO 21930 / EN 15804 and are not evaluated within the full building context."
        }

    return {
        "is_epd_enabled": True,
        "template_id": "",
        "industry_id": "general",
        "sub_sector": "general",
        "program_operator": "Smart EPD / ECONODE Studio (Borrador)",
        "pcr_reference": "ISO 21930:2017 / EN 15804+A2 Core Rules (Part A)",
        "standards": "ISO 14025, ISO 21930:2017, EN 15804+A2:2019",
        "declaration_number": "EPD-ECONODE-2026-DRAFT",
        "declaration_holder": org_name,
        "plant_location": f"Planta Principal ({geography})",
        "product_name": system_name,
        "declared_unit": declared_unit,
        "declared_unit_en": declared_unit,
        "declared_unit_amount": 1.0,
        "declared_unit_symbol": "u",
        "un_cpc": "N/A",
        "system_boundary": "Cradle-to-Gate (A1-A3)",
        "declared_modules": ["A1", "A2", "A3"],
        "default_standard": "EN15804_A2",
        "issue_date": "2026-11-17",
        "valid_until": "2031-11-17",
        "verification_type": "Internal Draft (Pre-Verification)",
        "verifier_name": "Por asignar",
        "reference_service_life": "No declarada",
        "composition": [],
        "technical_specs": {},
        "scenarios_notes": "Asigne modulos EPD (A1-D) a cada proceso en el Lienzo para desglosar automaticamente los resultados por etapa de ciclo de vida.",
        "comparability_statement_es": "Las Declaraciones Ambientales de Producto (EPD) dentro de la misma categoria de producto pero de diferentes operadores de programa pueden no ser comparables segun ISO 14025, ISO 21930 y EN 15804.",
        "comparability_statement_en": "Environmental Product Declarations (EPDs) within the same product category but from different programs may not be comparable per ISO 14025, ISO 21930, and EN 15804."
    }
