"""
Waste Calculation Engine (WasteTools 2026 / Doka ecoinvent v3.12 methodology)
Author: ECONODE Studio / Brigthway
Description:
Calculates end-of-life environmental inventories (LCI) and environmental impacts (LCIA)
for 220+ predefined waste materials and custom elemental compositions across:
- Municipal Solid Waste Incineration (MSWI) with energy and metal recovery
- Sanitary Landfill with Landfill Gas (LFG) capture and leachate modeling
- Uncontrolled Open Burning
- Inert Construction Debris Landfill
- Municipal Wastewater Treatment (WWTP)

Outputs categorized according to EN 15804 / ISO 21930 EPD Modules:
- Module C1: Deconstruction / Demolition
- Module C2: Waste Transport to Treatment
- Module C3: Waste Processing
- Module C4: Final Disposal
- Module D: Benefits and loads beyond system boundary (Avoided burdens)
"""

import os
import json
import math
from typing import Dict, Any, List, Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'waste_data_2026.json')

class WasteEngine:
    _instance = None
    _data = None

    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file or DATA_PATH
        self.materials_map = {}
        self.technologies = {}
        self._load_data()

    def _load_data(self):
        candidate_paths = [
            self.data_file,
            os.path.join(os.path.dirname(__file__), 'data', 'waste_data_2026.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'waste_data_2026.json'),
            os.path.join(os.path.dirname(__file__), 'econode_studio', 'data', 'waste_data_2026.json'),
            os.path.join(os.getcwd(), 'data', 'waste_data_2026.json'),
            os.path.join(os.getcwd(), 'econode_studio', 'data', 'waste_data_2026.json'),
        ]
        resolved_file = None
        for p in candidate_paths:
            if p and os.path.exists(p):
                resolved_file = p
                break
        if not resolved_file:
            raise FileNotFoundError(f"Waste database file not found in candidates: {candidate_paths}")
        with open(resolved_file, 'r', encoding='utf-8') as f:
            self._data = json.load(f)
            
        self.materials = self._data.get('materials', [])
        for m in self.materials:
            self.materials_map[m['id']] = m
            self.materials_map[m['name'].lower()] = m
            
        self.technologies = self._data.get('technologies', {})

    def get_categories(self) -> List[str]:
        cats = sorted(list(set(m['category'] for m in self.materials)))
        return cats

    def get_materials(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        q = search.lower().strip() if search else None
        for m in self.materials:
            if category and m['category'] != category:
                continue
            if q and (q not in m['name'].lower() and q not in m.get('german_name', '').lower()):
                continue
            results.append({
                'id': m['id'],
                'name': m['name'],
                'german_name': m.get('german_name', ''),
                'category': m['category'],
                'net_heating_value_mj_kg': m['properties'].get('Hu', 0.0),
                'gross_heating_value_mj_kg': m['properties'].get('Ho', 0.0),
                'water_content': m['properties'].get('H2O', 0.0),
                'carbon_content': m['properties'].get('C', 0.0),
                'biogenic_carbon_share': m['properties'].get('biogenic_c_share', 0.0),
                'degradability_100a': m['properties'].get('degradability_100a', 0.0),
                'properties': m['properties']
            })
        return results

    def get_material_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        return self.materials_map.get(material_id) or self.materials_map.get(material_id.lower())

    def calculate(self, 
                  material_id: Optional[str] = None,
                  custom_properties: Optional[Dict[str, float]] = None,
                  mass_kg: float = 1.0,
                  technology: str = 'mswi',
                  tech_overrides: Optional[Dict[str, float]] = None,
                  transport_km: float = 20.0,
                  grid_ghg_factor: float = 0.420,  # kg CO2e / kWh (default grid electricity)
                  heat_ghg_factor: float = 0.065   # kg CO2e / MJ (default avoided natural gas heat)
                  ) -> Dict[str, Any]:
        """
        Executes end-of-life inventory and LCIA calculation for a given waste flow.
        """
        if mass_kg <= 0:
            raise ValueError("Waste mass must be positive.")

        # 1. Resolve material properties
        props = {}
        mat_name = "Custom Waste Formulation"
        mat_cat = "Custom"
        
        if material_id:
            m = self.get_material_by_id(material_id)
            if not m:
                raise ValueError(f"Waste material '{material_id}' not found.")
            mat_name = m['name']
            mat_cat = m['category']
            props = dict(m['properties'])
            
        if custom_properties:
            props.update(custom_properties)
            
        if not props:
            raise ValueError("No material properties provided.")

        tech_key = technology.lower()
        if tech_key not in ['mswi', 'landfill', 'open_burning', 'construction_landfill', 'wastewater']:
            raise ValueError(f"Unsupported technology: {technology}")

        # Basic elemental properties
        hu = float(props.get('Hu', 0.0))          # Net heating value MJ/kg
        ho = float(props.get('Ho', 0.0))          # Gross heating value MJ/kg
        h2o = float(props.get('H2O', 0.0))        # Water content kg/kg
        c_tot = float(props.get('C', 0.0))        # Total carbon kg/kg
        bio_share = float(props.get('biogenic_c_share', 0.0)) # 0 to 1
        n = float(props.get('N', 0.0))            # Nitrogen kg/kg
        s = float(props.get('S', 0.0))            # Sulfur kg/kg
        p = float(props.get('P', 0.0))            # Phosphorus kg/kg
        cl = float(props.get('Cl', 0.0))          # Chlorine kg/kg
        f_elem = float(props.get('F', 0.0))       # Fluorine kg/kg
        br = float(props.get('Br', 0.0))          # Bromine kg/kg
        fe = float(props.get('Fe', 0.0))          # Iron kg/kg
        al = float(props.get('Al', 0.0))          # Aluminium kg/kg
        cu = float(props.get('Cu', 0.0))          # Copper kg/kg
        hg = float(props.get('Hg', 0.0))          # Mercury kg/kg
        cd = float(props.get('Cd', 0.0))          # Cadmium kg/kg
        pb = float(props.get('Pb', 0.0))          # Lead kg/kg
        cr = float(props.get('Cr', 0.0))          # Chromium kg/kg
        zn = float(props.get('Zn', 0.0))          # Zinc kg/kg
        degrad_100a = float(props.get('degradability_100a', 0.0))

        fe_rec_share = float(props.get('fe_recyclable_share', 0.8))
        al_rec_share = float(props.get('al_recyclable_share', 0.5))
        cu_rec_share = float(props.get('cu_recyclable_share', 0.5))

        overrides = tech_overrides or {}

        # 2. Compute by technology
        air_emissions = {}
        water_emissions = {}
        solid_residues = {}
        avoided_energy = {}
        avoided_materials = {}

        if tech_key == 'mswi':
            # Incineration parameters
            eta_el = float(overrides.get('electric_efficiency', 0.15))
            eta_th = float(overrides.get('thermal_efficiency', 0.28))
            fe_rec_eff = float(overrides.get('fe_scrap_recovery', 0.85))
            al_rec_eff = float(overrides.get('al_scrap_recovery', 0.50))
            cu_rec_eff = float(overrides.get('cu_scrap_recovery', 0.35))

            # Air emissions
            c_fossil = c_tot * (1.0 - bio_share) * mass_kg
            c_biogenic = c_tot * bio_share * mass_kg
            
            # Transfer coefficient to air for C ~ 0.999
            co2_fossil = c_fossil * 0.999 * (44.0 / 12.0)
            co2_biogenic = c_biogenic * 0.999 * (44.0 / 12.0)
            ch4_air = mass_kg * 6.5e-7  # trace
            n2o_air = n * mass_kg * 0.015 * (44.0 / 28.0) # SNCR/SCR DeNOx emission
            nox_air = n * mass_kg * 0.065 * (46.0 / 14.0)
            so2_air = s * mass_kg * 0.010 * (64.0 / 32.0) # 99% scrubbing efficiency
            hcl_air = cl * mass_kg * 0.005 * (36.46 / 35.45)
            hf_air = f_elem * mass_kg * 0.005 * (20.0 / 19.0)
            hg_air = hg * mass_kg * 0.020 # 98% carbon filter retention

            air_emissions = {
                'Carbon dioxide, fossil (CO2)': co2_fossil,
                'Carbon dioxide, biogenic (CO2)': co2_biogenic,
                'Methane, fossil (CH4)': ch4_air,
                'Dinitrogen monoxide (N2O)': n2o_air,
                'Nitrogen oxides (NOx as NO2)': nox_air,
                'Sulfur dioxide (SO2)': so2_air,
                'Hydrogen chloride (HCl)': hcl_air,
                'Hydrogen fluoride (HF)': hf_air,
                'Mercury (Hg to air)': hg_air,
                'Particulates, < 2.5 um': mass_kg * 1.2e-5
            }

            # Solid residues
            slag_mass = mass_kg * (1.0 - h2o - c_tot) * 0.85
            apc_mass = mass_kg * 0.035
            solid_residues = {
                'Bottom ash (slag to landfill)': max(0.0, slag_mass),
                'Air pollution control (APC) filter residues': max(0.0, apc_mass)
            }

            # Energy recovery
            net_heat_total_mj = max(0.0, hu * mass_kg)
            el_kwh = (net_heat_total_mj * eta_el) / 3.6
            th_mj = net_heat_total_mj * eta_th
            avoided_energy = {
                'Electricity recovered (kWh)': el_kwh,
                'District heat recovered (MJ)': th_mj
            }

            # Metal recovery from slag
            fe_rec_kg = fe * mass_kg * fe_rec_share * fe_rec_eff
            al_rec_kg = al * mass_kg * al_rec_share * al_rec_eff
            cu_rec_kg = cu * mass_kg * cu_rec_share * cu_rec_eff
            avoided_materials = {
                'Secondary scrap steel (kg)': fe_rec_kg,
                'Secondary scrap aluminium (kg)': al_rec_kg,
                'Secondary scrap copper (kg)': cu_rec_kg
            }

        elif tech_key == 'landfill':
            # Sanitary Landfill parameters
            gas_cap = float(overrides.get('gas_capture_efficiency', 0.55))
            flare_share = float(overrides.get('gas_flaring_share', 0.20))
            el_eff = float(overrides.get('gas_electricity_efficiency', 0.33))
            soil_ox = float(overrides.get('soil_oxidation', 0.10))

            # Degradation over 100 years
            c_deg = c_tot * mass_kg * degrad_100a
            c_deg_gas = c_deg * 0.97
            
            # LFG composition: 50% CH4, 50% CO2
            ch4_gen = c_deg_gas * 0.50 * (16.0 / 12.0)
            co2_gen = c_deg_gas * 0.50 * (44.0 / 12.0)

            # Captured vs Uncaptured
            ch4_captured = ch4_gen * gas_cap
            ch4_uncaptured = ch4_gen * (1.0 - gas_cap)
            ch4_fugitive = ch4_uncaptured * (1.0 - soil_ox)
            co2_soil_ox = ch4_uncaptured * soil_ox * (44.0 / 16.0)

            ch4_flared = ch4_captured * flare_share
            ch4_energy = ch4_captured * (1.0 - flare_share)

            co2_flared = ch4_flared * (44.0 / 16.0)
            co2_energy = ch4_energy * (44.0 / 16.0)
            co2_fugitive = co2_gen * (1.0 - gas_cap)

            # Partition fossil vs biogenic
            bio_f = bio_share
            co2_fossil = (co2_fugitive + co2_flared + co2_energy + co2_soil_ox) * (1.0 - bio_f)
            co2_biogenic = (co2_fugitive + co2_flared + co2_energy + co2_soil_ox) * bio_f
            ch4_fossil = ch4_fugitive * (1.0 - bio_f)
            ch4_biogenic = ch4_fugitive * bio_f

            air_emissions = {
                'Carbon dioxide, fossil (CO2)': co2_fossil,
                'Carbon dioxide, biogenic (CO2)': co2_biogenic,
                'Methane, biogenic (CH4)': ch4_biogenic,
                'Methane, fossil (CH4)': ch4_fossil,
                'Nitrogen oxides (NOx from flare/engine)': mass_kg * 5.0e-5
            }

            # Leachate to water (short term 100a)
            water_emissions = {
                'Chemical Oxygen Demand (COD)': c_deg * 0.03 * (32.0 / 12.0),
                'Nitrogen total to groundwater': n * mass_kg * degrad_100a * 0.05,
                'Phosphorus total to groundwater': p * mass_kg * degrad_100a * 0.01,
                'Heavy metals in leachate': (hg + cd + pb + cr + zn) * mass_kg * 0.02
            }

            # Electricity from captured LFG (LHV CH4 = 50 MJ/kg)
            lfg_heat_mj = ch4_energy * 50.0
            el_kwh = (lfg_heat_mj * el_eff) / 3.6
            avoided_energy = {
                'Electricity recovered from LFG (kWh)': el_kwh
            }

            solid_residues = {
                'Waste mass stored in landfill body (kg)': mass_kg * (1.0 - degrad_100a * 0.5)
            }

        elif tech_key == 'open_burning':
            # Uncontrolled open combustion
            c_fossil = c_tot * (1.0 - bio_share) * mass_kg
            c_biogenic = c_tot * bio_share * mass_kg

            co2_fossil = c_fossil * 0.90 * (44.0 / 12.0)
            co2_biogenic = c_biogenic * 0.90 * (44.0 / 12.0)
            co_air = (c_fossil + c_biogenic) * 0.06 * (28.0 / 12.0)
            ch4_air = (c_fossil + c_biogenic) * 0.02 * (16.0 / 12.0)
            pm25 = mass_kg * 0.015 # 15 g / kg particulates
            so2_air = s * mass_kg * (64.0 / 32.0)
            nox_air = n * mass_kg * 0.5 * (46.0 / 14.0)

            air_emissions = {
                'Carbon dioxide, fossil (CO2)': co2_fossil,
                'Carbon dioxide, biogenic (CO2)': co2_biogenic,
                'Carbon monoxide (CO)': co_air,
                'Methane (CH4)': ch4_air,
                'Particulates, < 2.5 um (Black Carbon)': pm25,
                'Sulfur dioxide (SO2)': so2_air,
                'Nitrogen oxides (NOx as NO2)': nox_air
            }

            solid_residues = {
                'Unburned open residue on soil (kg)': mass_kg * 0.15
            }

        elif tech_key == 'construction_landfill':
            # Inert debris
            solid_residues = {
                'Inert mineral landfill storage (kg)': mass_kg
            }
            water_emissions = {
                'Suspended solids to groundwater': mass_kg * 0.001,
                'Sulfate (SO4--) to groundwater': s * mass_kg * 0.05
            }

        elif tech_key == 'wastewater':
            # PTAR / WWTP
            sludge_mass = mass_kg * (1.0 - h2o) * 0.65
            ch4_digester = c_tot * mass_kg * 0.25 * (16.0 / 12.0)
            el_kwh = (ch4_digester * 50.0 * 0.33) / 3.6

            air_emissions = {
                'Carbon dioxide, biogenic (CO2)': c_tot * bio_share * mass_kg * 0.5 * (44.0 / 12.0),
                'Methane, biogenic (fugitive CH4)': ch4_digester * 0.05
            }
            water_emissions = {
                'BOD5 in treated effluent': mass_kg * 0.015,
                'COD in treated effluent': mass_kg * 0.045,
                'Nitrate in treated effluent': n * mass_kg * 0.30,
                'Phosphate in treated effluent': p * mass_kg * 0.15
            }
            solid_residues = {
                'Dewatered sewage sludge (kg)': sludge_mass
            }
            avoided_energy = {
                'Electricity recovered from biogas (kWh)': el_kwh
            }

        # 3. Transport (Module C2)
        # Default diesel truck 16-32t: ~0.11 kg CO2e / t*km = 0.00011 kg CO2e / kg*km
        transport_t_km = (mass_kg / 1000.0) * transport_km
        c2_ghg_kg = transport_t_km * 0.110

        # 4. Impact Characterization (EN 15804 / IPCC 2021 GWP100)
        # GWP100 factors: CO2 fossil = 1.0, CO2 biogenic = 1.0 (EN 15804+A2), CH4 fossil = 29.8, CH4 biogenic = 27.2, N2O = 273.0
        c4_ghg_fossil = air_emissions.get('Carbon dioxide, fossil (CO2)', 0.0) * 1.0 + \
                        air_emissions.get('Methane, fossil (CH4)', 0.0) * 29.8 + \
                        air_emissions.get('Methane (CH4)', 0.0) * 29.8
        c4_ghg_biogenic = air_emissions.get('Carbon dioxide, biogenic (CO2)', 0.0) * 1.0 + \
                          air_emissions.get('Methane, biogenic (CH4)', 0.0) * 27.2
        c4_ghg_n2o = air_emissions.get('Dinitrogen monoxide (N2O)', 0.0) * 273.0
        c4_ghg_total = c4_ghg_fossil + c4_ghg_biogenic + c4_ghg_n2o

        # Module C3 (Processing energy consumed)
        # MSWI sorting/pumps ~ 25 kWh/t = 0.025 kWh/kg
        c3_kwh = mass_kg * (0.025 if tech_key == 'mswi' else (0.010 if tech_key == 'landfill' else 0.0))
        c3_ghg_kg = c3_kwh * grid_ghg_factor

        # Module D (Credits)
        avoided_el_kwh = avoided_energy.get('Electricity recovered (kWh)', 0.0) + \
                         avoided_energy.get('Electricity recovered from LFG (kWh)', 0.0) + \
                         avoided_energy.get('Electricity recovered from biogas (kWh)', 0.0)
        avoided_th_mj = avoided_energy.get('District heat recovered (MJ)', 0.0)
        
        ghg_credit_el = avoided_el_kwh * grid_ghg_factor
        ghg_credit_th = avoided_th_mj * heat_ghg_factor
        
        ghg_credit_fe = avoided_materials.get('Secondary scrap steel (kg)', 0.0) * 1.80
        ghg_credit_al = avoided_materials.get('Secondary scrap aluminium (kg)', 0.0) * 8.50
        ghg_credit_cu = avoided_materials.get('Secondary scrap copper (kg)', 0.0) * 3.20
        ghg_credit_metals = ghg_credit_fe + ghg_credit_al + ghg_credit_cu

        module_d_ghg_credit = -(ghg_credit_el + ghg_credit_th + ghg_credit_metals)

        # Net Total Lifecycle GWP
        net_gwp_total = c2_ghg_kg + c3_ghg_kg + c4_ghg_total + module_d_ghg_credit

        return {
            'input_summary': {
                'material_name': mat_name,
                'category': mat_cat,
                'mass_kg': mass_kg,
                'technology': tech_key,
                'technology_name': self.technologies.get(tech_key, {}).get('name', tech_key),
                'transport_km': transport_km
            },
            'epd_modules_gwp': {
                'C1_deconstruction': 0.0,
                'C2_transport': round(c2_ghg_kg, 4),
                'C3_waste_processing': round(c3_ghg_kg, 4),
                'C4_final_disposal': round(c4_ghg_total, 4),
                'C4_fossil_gwp': round(c4_ghg_fossil, 4),
                'C4_biogenic_gwp': round(c4_ghg_biogenic, 4),
                'Module_D_avoided_burdens': round(module_d_ghg_credit, 4),
                'Net_Total_GWP': round(net_gwp_total, 4),
                'unit': 'kg CO2 eq'
            },
            'lci_air_emissions': {k: round(v, 6) for k, v in air_emissions.items() if abs(v) > 1e-9},
            'lci_water_emissions': {k: round(v, 6) for k, v in water_emissions.items() if abs(v) > 1e-9},
            'lci_solid_residues': {k: round(v, 4) for k, v in solid_residues.items() if abs(v) > 1e-6},
            'avoided_energy': {k: round(v, 3) for k, v in avoided_energy.items() if v > 1e-4},
            'avoided_materials': {k: round(v, 4) for k, v in avoided_materials.items() if v > 1e-4},
            'module_d_breakdown': {
                'avoided_electricity_credit_kg_co2e': round(-ghg_credit_el, 4),
                'avoided_heat_credit_kg_co2e': round(-ghg_credit_th, 4),
                'avoided_metals_credit_kg_co2e': round(-ghg_credit_metals, 4)
            }
        }

# Global singleton helper
_engine_singleton = None

def get_waste_engine() -> WasteEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = WasteEngine()
    return _engine_singleton
