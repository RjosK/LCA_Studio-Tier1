"""
econode_studio/domain/ghg_inventory.py - Entidad de Dominio para Inventarios Corporativos GHG Protocol
Define la estructura, reglas contables y agregacion multidimensional para Alcances 1, 2 (Location/Market) y 3 (15 Categorias).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# Taxonomia Oficial de Categorias GHG Protocol
SCOPE_CATEGORIES = {
    # Alcance 1: Emisiones Directas
    "stationary_combustion": {
        "scope": "SCOPE_1",
        "name_es": "Combustión Estacionaria",
        "name_en": "Stationary Combustion",
        "description": "Calderas, hornos, turbinas y generadores fijos en sitio."
    },
    "mobile_combustion": {
        "scope": "SCOPE_1",
        "name_es": "Combustión Móvil",
        "name_en": "Mobile Combustion",
        "description": "Flotillas vehiculares, montacargas y maquinaria móvil propiedad de la empresa."
    },
    "process_emissions": {
        "scope": "SCOPE_1",
        "name_es": "Emisiones de Proceso Industrial",
        "name_en": "Process Emissions",
        "description": "Reacciones químicas, calcinación de carbonatos, manufactura química."
    },
    "fugitive_emissions": {
        "scope": "SCOPE_1",
        "name_es": "Emisiones Fugitivas",
        "name_en": "Fugitive Emissions",
        "description": "Fugas de refrigerantes HFC en HVAC y conmutadores SF6."
    },

    # Alcance 2: Emisiones Indirectas por Energía Adquirida
    "electricity_location": {
        "scope": "SCOPE_2",
        "name_es": "Electricidad Adquirida (Location-Based)",
        "name_en": "Purchased Electricity (Location-Based)",
        "description": "Consumo de red eléctrica evaluado con el factor de emisión promedio de la red (FESEN/eGRID)."
    },
    "electricity_market": {
        "scope": "SCOPE_2",
        "name_es": "Electricidad Adquirida (Market-Based)",
        "name_en": "Purchased Electricity (Market-Based)",
        "description": "Contratos directos, Certificados I-REC/CEL, PPAs solares/eólicos o factor residual del proveedor."
    },
    "steam_heating_cooling": {
        "scope": "SCOPE_2",
        "name_es": "Vapor, Calefacción y Enfriamiento Adquirido",
        "name_en": "Purchased Steam, Heating & Cooling",
        "description": "Energía térmica o vapor industrial canalizado desde terceros."
    },

    # Alcance 3: Cadena de Valor Aguas Arriba (Upstream, Categorías 1-8)
    "cat_1_purchased_goods": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 1,
        "name_es": "1. Bienes y Servicios Adquiridos",
        "name_en": "1. Purchased Goods and Services",
        "description": "Extracción y producción Cradle-to-Gate de materias primas y servicios contratados."
    },
    "cat_2_capital_goods": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 2,
        "name_es": "2. Bienes de Capital",
        "name_en": "2. Capital Goods",
        "description": "Maquinaria industrial, equipo de transporte, edificios e infraestructura adquirida."
    },
    "cat_3_fuel_energy_activities": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 3,
        "name_es": "3. Actividades Relacionadas con Combustibles y Energía (FERA)",
        "name_en": "3. Fuel- and Energy-Related Activities",
        "description": "Extracción y refinación aguas arriba de combustibles y pérdidas de T&D en la red eléctrica."
    },
    "cat_4_upstream_transport": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 4,
        "name_es": "4. Transporte y Distribución Aguas Arriba",
        "name_en": "4. Upstream Transportation & Distribution",
        "description": "Fletes y logística de insumos desde proveedores hasta las instalaciones de la empresa."
    },
    "cat_5_waste_generated": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 5,
        "name_es": "5. Residuos Generados en Operaciones",
        "name_en": "5. Waste Generated in Operations",
        "description": "Disposición final y tratamiento de residuos sólidos y aguas residuales (relleno, reciclaje, compost)."
    },
    "cat_6_business_travel": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 6,
        "name_es": "6. Viajes de Negocios",
        "name_en": "6. Business Travel",
        "description": "Vuelos comerciales, trenes, taxis y hospedaje en hoteles para fines corporativos."
    },
    "cat_7_employee_commuting": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 7,
        "name_es": "7. Conmutación de Empleados",
        "name_en": "7. Employee Commuting",
        "description": "Traslado diario del personal entre su residencia y el lugar de trabajo."
    },
    "cat_8_upstream_leased_assets": {
        "scope": "SCOPE_3",
        "tier": "upstream",
        "cat_num": 8,
        "name_es": "8. Activos Arrendados Aguas Arriba",
        "name_en": "8. Upstream Leased Assets",
        "description": "Operación de activos arrendados por la empresa y no incluidos en Alcance 1 o 2."
    },

    # Alcance 3: Cadena de Valor Aguas Abajo (Downstream, Categorías 9-15)
    "cat_9_downstream_transport": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 9,
        "name_es": "9. Transporte y Distribución Aguas Abajo",
        "name_en": "9. Downstream Transportation & Distribution",
        "description": "Distribución y fletes de productos vendidos a clientes finales no costeados directamente."
    },
    "cat_10_processing_sold_products": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 10,
        "name_es": "10. Procesamiento de Productos Vendidos",
        "name_en": "10. Processing of Sold Products",
        "description": "Transformación intermedia de productos por clientes industriales."
    },
    "cat_11_use_of_sold_products": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 11,
        "name_es": "11. Uso de Productos Vendidos",
        "name_en": "11. Use of Sold Products",
        "description": "Emisiones directas e indirectas derivadas del consumo de energía o uso del producto vendido."
    },
    "cat_12_end_of_life": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 12,
        "name_es": "12. Fin de Vida de Productos Vendidos",
        "name_en": "12. End-of-Life Treatment of Sold Products",
        "description": "Gestión de residuos y reciclaje al final de la vida útil de los productos comercializados."
    },
    "cat_13_downstream_leased_assets": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 13,
        "name_es": "13. Activos Arrendados Aguas Abajo",
        "name_en": "13. Downstream Leased Assets",
        "description": "Inmuebles y activos propiedad de la empresa arrendados a terceros."
    },
    "cat_14_franchises": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 14,
        "name_es": "14. Franquicias",
        "name_en": "14. Franchises",
        "description": "Emisiones derivadas de la operación de franquiciatarios bajo la marca de la empresa."
    },
    "cat_15_investments": {
        "scope": "SCOPE_3",
        "tier": "downstream",
        "cat_num": 15,
        "name_es": "15. Inversiones (Emisiones Financiadas / PCAF)",
        "name_en": "15. Investments",
        "description": "Emisiones atribuidas a inversiones de capital, préstamos bancarios y gestión de activos."
    }
}

@dataclass
class GHGEntry:
    id: Optional[int]
    inventory_id: int
    scope: str                          # 'SCOPE_1', 'SCOPE_2', 'SCOPE_3'
    scope_category: str                 # Llave de SCOPE_CATEGORIES
    activity_name: str
    calculation_type: str               # 'activity_based', 'spend_based', 'supplier_specific', 'product_system_lca'
    activity_amount: float
    activity_unit: str
    currency: Optional[str] = "USD"
    emission_factor_id: Optional[int] = None
    emission_factor_value: float = 0.0  # kg CO2e / unidad
    emission_factor_unit: str = "kg CO2e"
    emission_factor_source: str = ""
    product_system_id: Optional[int] = None
    contractual_instrument: Optional[str] = None
    emissions_kgco2e: float = 0.0
    emissions_tco2e: float = 0.0
    data_quality_tier: str = "Tier 2"   # 'Tier 1' (primario), 'Tier 2' (especifico regional), 'Tier 3' (proxy)
    notes: str = ""
    created_at: Optional[str] = None

    def calculate_emissions(self, currency_rate_to_usd: float = 1.0) -> None:
        """Calcula las emisiones en kg CO2e y toneladas de CO2e."""
        if self.calculation_type == "spend_based":
            # Convertir gasto a USD si el factor esta indexado en USD
            amount_usd = self.activity_amount * currency_rate_to_usd
            self.emissions_kgco2e = amount_usd * self.emission_factor_value
        else:
            self.emissions_kgco2e = self.activity_amount * self.emission_factor_value

        self.emissions_tco2e = self.emissions_kgco2e / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        cat_info = SCOPE_CATEGORIES.get(self.scope_category, {})
        return {
            "id": self.id,
            "inventory_id": self.inventory_id,
            "scope": self.scope,
            "scope_category": self.scope_category,
            "category_name_es": cat_info.get("name_es", self.scope_category),
            "category_name_en": cat_info.get("name_en", self.scope_category),
            "tier": cat_info.get("tier", "operational"),
            "cat_num": cat_info.get("cat_num"),
            "activity_name": self.activity_name,
            "calculation_type": self.calculation_type,
            "activity_amount": self.activity_amount,
            "activity_unit": self.activity_unit,
            "currency": self.currency,
            "emission_factor_id": self.emission_factor_id,
            "emission_factor_value": self.emission_factor_value,
            "emission_factor_unit": self.emission_factor_unit,
            "emission_factor_source": self.emission_factor_source,
            "product_system_id": self.product_system_id,
            "contractual_instrument": self.contractual_instrument,
            "emissions_kgco2e": round(self.emissions_kgco2e, 4),
            "emissions_tco2e": round(self.emissions_tco2e, 6),
            "data_quality_tier": self.data_quality_tier,
            "notes": self.notes,
            "created_at": self.created_at
        }

@dataclass
class GHGInventory:
    id: Optional[int]
    organization_name: str
    reporting_year: int
    consolidation_approach: str = "operational_control" # 'operational_control', 'financial_control', 'equity_share'
    country_code: str = "MX"
    base_year: Optional[int] = None
    description: str = ""
    status: str = "draft"
    entries: List[GHGEntry] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def calculate_summary(self) -> Dict[str, Any]:
        """Calcula el resumen ejecutivo bajo directrices de doble contabilidad del GHG Protocol."""
        scope_1_total = 0.0
        scope_2_location_total = 0.0
        scope_2_market_total = 0.0
        scope_3_upstream_total = 0.0
        scope_3_downstream_total = 0.0

        scope_1_by_category: Dict[str, float] = {}
        scope_2_by_category: Dict[str, float] = {}
        scope_3_by_category: Dict[str, float] = {}

        # Inicializar categorias de Scope 3
        for k, v in SCOPE_CATEGORIES.items():
            if v["scope"] == "SCOPE_3":
                scope_3_by_category[k] = 0.0

        has_market_entries = False

        for entry in self.entries:
            t = entry.emissions_tco2e
            cat = entry.scope_category
            cat_meta = SCOPE_CATEGORIES.get(cat, {})

            if entry.scope == "SCOPE_1":
                scope_1_total += t
                scope_1_by_category[cat] = scope_1_by_category.get(cat, 0.0) + t

            elif entry.scope == "SCOPE_2":
                if cat == "electricity_market":
                    has_market_entries = True
                    scope_2_market_total += t
                else:
                    scope_2_location_total += t
                scope_2_by_category[cat] = scope_2_by_category.get(cat, 0.0) + t

            elif entry.scope == "SCOPE_3":
                tier = cat_meta.get("tier", "upstream")
                if tier == "downstream":
                    scope_3_downstream_total += t
                else:
                    scope_3_upstream_total += t
                scope_3_by_category[cat] = scope_3_by_category.get(cat, 0.0) + t

        # Si se registraron instrumentos contractuales de mercado para Scope 2, se usa ese total (incluso si es 0.0 por PPA verde)
        # Si no se registro ningun instrumento de mercado, bajo GHG Protocol Market-based = Location-based
        market_based_effective = scope_2_market_total if has_market_entries else scope_2_location_total
        scope_3_total = scope_3_upstream_total + scope_3_downstream_total

        total_location_based = scope_1_total + scope_2_location_total + scope_3_total
        total_market_based = scope_1_total + market_based_effective + scope_3_total

        # Formatear categorias de Scope 3 estructuradas
        scope_3_details = []
        for cat_key, t_val in scope_3_by_category.items():
            info = SCOPE_CATEGORIES.get(cat_key, {})
            share = (t_val / scope_3_total * 100.0) if scope_3_total > 0 else 0.0
            scope_3_details.append({
                "category_key": cat_key,
                "cat_num": info.get("cat_num", 0),
                "name_es": info.get("name_es", cat_key),
                "name_en": info.get("name_en", cat_key),
                "tier": info.get("tier", "upstream"),
                "emissions_tco2e": round(t_val, 4),
                "percentage_share": round(share, 2)
            })
        scope_3_details.sort(key=lambda x: x["cat_num"])

        return {
            "inventory_id": self.id,
            "organization_name": self.organization_name,
            "reporting_year": self.reporting_year,
            "consolidation_approach": self.consolidation_approach,
            "country_code": self.country_code,
            "status": self.status,
            "entries_count": len(self.entries),
            "scope_1": {
                "total_tco2e": round(scope_1_total, 4),
                "percentage_location": round((scope_1_total / total_location_based * 100.0) if total_location_based > 0 else 0.0, 2),
                "breakdown": {k: round(v, 4) for k, v in scope_1_by_category.items()}
            },
            "scope_2": {
                "location_based_tco2e": round(scope_2_location_total, 4),
                "market_based_tco2e": round(market_based_effective, 4),
                "has_market_instruments": has_market_entries,
                "percentage_location": round((scope_2_location_total / total_location_based * 100.0) if total_location_based > 0 else 0.0, 2)
            },
            "scope_3": {
                "total_tco2e": round(scope_3_total, 4),
                "upstream_tco2e": round(scope_3_upstream_total, 4),
                "downstream_tco2e": round(scope_3_downstream_total, 4),
                "percentage_location": round((scope_3_total / total_location_based * 100.0) if total_location_based > 0 else 0.0, 2),
                "categories": scope_3_details
            },
            "totals": {
                "total_location_based_tco2e": round(total_location_based, 4),
                "total_market_based_tco2e": round(total_market_based, 4),
                "net_reduction_via_market_tco2e": round(max(0.0, scope_2_location_total - market_based_effective), 4)
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_name": self.organization_name,
            "reporting_year": self.reporting_year,
            "consolidation_approach": self.consolidation_approach,
            "country_code": self.country_code,
            "base_year": self.base_year,
            "description": self.description,
            "status": self.status,
            "entries": [e.to_dict() for e in self.entries],
            "summary": self.calculate_summary(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
