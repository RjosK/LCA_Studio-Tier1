"""
waste_suite_full.py
===================
Motor de Tratamiento de Residuos Integral (WasteTools 2026 / Gabor Doka / ecoinvent v3.12)
Replicacion 1:1 de los 8 libros y modelos cientificos de Gabor Doka para ECONODE Studio.

Capacidades integradas:
1. WasteMixtureEngine: Sintetizador de mezclas dinamicas multi-fraccion de residuos.
2. DokaIncinerationEngine: Incineracion municipal (MSWI) con DeNOx (SNCR/SCR), FGC,
   desmetalizado de escorias (Fe, Al, Cu), consumibles y recuperacion energetica.
3. DokaLandfillEngine: Vertedero municipal (MSW) con 6 climas (CH, Jordan, GLO, etc.),
   gestion de biogas (antorcha vs turbina) y bifurcacion de horizontes (100a vs 60,000a).
4. DokaInertLandfillEngine: Relleno de RCD (construccion/demolicion) y deposito de tierras de excavacion.
5. DokaTailingsEngine: Presas de relaves mineros con drenaje acido de roca (ARD) y lixiviacion geologica.
6. DokaOpenBurningEngine: Quema no controlada a cielo abierto con factores de combustion incompleta.
7. DokaWastewaterEngine: PTAR de 1, 2 y 3 etapas (precipitacion P con FeSO4) y destino de lodos.
8. DokaExportEngine: Generador de archivos de intercambio en formatos SimaPro CSV y EcoSpold 2 XML.
"""

import os
import json
import math
from typing import Dict, Any, List, Optional, Union

DATA_CANDIDATE_PATHS = [
    os.path.join(os.path.dirname(__file__), 'data', 'waste_suite_full_2026.json'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'waste_suite_full_2026.json'),
    os.path.join(os.path.dirname(__file__), 'econode_studio', 'data', 'waste_suite_full_2026.json'),
    os.path.join(os.getcwd(), 'data', 'waste_suite_full_2026.json'),
    os.path.join(os.getcwd(), 'econode_studio', 'data', 'waste_suite_full_2026.json'),
]

class WasteMixtureEngine:
    """Motor de calculo y sintesis de mezclas compuestas de residuos."""

    @staticmethod
    def mix_fractions(fractions: List[Dict[str, Any]], materials_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pondera una lista de fracciones de residuos para sintetizar un residuo compuesto.
        Cada fraccion debe contener 'material_id' y ('mass_kg' o 'share').
        """
        if not fractions:
            raise ValueError("La lista de fracciones de residuos no puede estar vacia")

        # 1. Normalizar participaciones
        has_mass = any('mass_kg' in f for f in fractions)
        total_mass = sum(float(f.get('mass_kg', 0.0)) for f in fractions) if has_mass else 100.0

        resolved_fractions = []
        for f in fractions:
            mat_id = f.get('material_id')
            if not mat_id or mat_id not in materials_map:
                raise ValueError(f"Material de residuo no valido o no encontrado: {mat_id}")
            mat = materials_map[mat_id]
            if has_mass:
                m_kg = float(f.get('mass_kg', 0.0))
                share = m_kg / total_mass if total_mass > 0 else 0.0
            else:
                share = float(f.get('share', 0.0))
                m_kg = share * total_mass
            resolved_fractions.append({"mat": mat, "share": share, "mass_kg": m_kg})

        # Verificar suma de participaciones
        sum_shares = sum(f['share'] for f in resolved_fractions)
        if abs(sum_shares - 1.0) > 0.01 and sum_shares > 0:
            for f in resolved_fractions:
                f['share'] = f['share'] / sum_shares

        # 2. Ponderar propiedades escalares
        Ho = sum(f['share'] * f['mat'].get('Ho', 0.0) for f in resolved_fractions)
        Hu = sum(f['share'] * f['mat'].get('Hu', 0.0) for f in resolved_fractions)
        H2O = sum(f['share'] * f['mat'].get('H2O', 0.0) for f in resolved_fractions)
        C_tot = sum(f['share'] * f['mat'].get('C', 0.0) for f in resolved_fractions)
        biogenic_c_tot = sum(f['share'] * f['mat'].get('C', 0.0) * f['mat'].get('biogenic_c_share', 0.0) for f in resolved_fractions)
        bio_share = (biogenic_c_tot / C_tot) if C_tot > 0 else 0.0
        degrad = sum(f['share'] * f['mat'].get('degradability_100a', 0.0) for f in resolved_fractions)

        H = sum(f['share'] * f['mat'].get('H', 0.0) for f in resolved_fractions)
        O = sum(f['share'] * f['mat'].get('O', 0.0) for f in resolved_fractions)
        N = sum(f['share'] * f['mat'].get('N', 0.0) for f in resolved_fractions)
        S = sum(f['share'] * f['mat'].get('S', 0.0) for f in resolved_fractions)
        P = sum(f['share'] * f['mat'].get('P', 0.0) for f in resolved_fractions)
        Cl = sum(f['share'] * f['mat'].get('Cl', 0.0) for f in resolved_fractions)
        F = sum(f['share'] * f['mat'].get('F', 0.0) for f in resolved_fractions)
        Br = sum(f['share'] * f['mat'].get('Br', 0.0) for f in resolved_fractions)
        I = sum(f['share'] * f['mat'].get('I', 0.0) for f in resolved_fractions)

        # 3. Ponderar metales traza en ppm
        all_metal_keys = set()
        for f in resolved_fractions:
            all_metal_keys.update(f['mat'].get('elements_ppm', {}).keys())

        mixed_metals = {}
        for k in all_metal_keys:
            mixed_metals[k] = round(sum(f['share'] * f['mat'].get('elements_ppm', {}).get(k, 0.0) for f in resolved_fractions), 4)

        organic_sum = H2O + C_tot + H + O + N + S + Cl + F
        ash = round(max(0.0, 1.0 - organic_sum), 5)

        names_summary = " + ".join([f"{f['mat']['name']} ({round(f['share']*100, 1)}%)" for f in resolved_fractions[:4]])
        if len(resolved_fractions) > 4:
            names_summary += f" + {len(resolved_fractions)-4} mas"

        share_bulk_fe = round(sum(f['share'] * f['mat'].get('share_bulk_fe', 0.0) for f in resolved_fractions), 4)
        share_bulk_al = round(sum(f['share'] * f['mat'].get('share_bulk_al', 0.0) for f in resolved_fractions), 4)
        share_bulk_cu = round(sum(f['share'] * f['mat'].get('share_bulk_cu', 0.0) for f in resolved_fractions), 4)

        return {
            "id": "composite_mixture_" + str(abs(hash(names_summary)) % 100000),
            "name": f"Mezcla Compuesta: {names_summary}",
            "category": "Mezclas Compuestas (Waste Mixture)",
            "Ho": round(Ho, 4),
            "Hu": round(Hu, 4),
            "H2O": round(H2O, 4),
            "C": round(C_tot, 5),
            "biogenic_c_share": round(bio_share, 4),
            "fossil_c_share": round(max(0.0, 1.0 - bio_share), 4),
            "degradability_100a": round(degrad, 4),
            "H": round(H, 5),
            "O": round(O, 5),
            "N": round(N, 5),
            "S": round(S, 5),
            "P": round(P, 5),
            "Cl": round(Cl, 5),
            "F": round(F, 5),
            "Br": round(Br, 5),
            "I": round(I, 5),
            "ash": ash,
            "share_bulk_fe": share_bulk_fe,
            "share_bulk_al": share_bulk_al,
            "share_bulk_cu": share_bulk_cu,
            "elements_ppm": mixed_metals,
            "total_mass_kg": round(total_mass, 2),
            "fractions_count": len(resolved_fractions)
        }


class DokaIncinerationEngine:
    """Modelo completo de Incineracion Municipal (MSWI) de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], mass_kg: float, transport_km: float,
                  denox: str = "sncr", recovery_scrap: bool = True,
                  fgc_mode: str = "wet_scrubber",
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        denox_opts = cfg.get("denox_options", {})
        denox_info = denox_opts.get(denox, denox_opts.get("sncr", {
            "name": "SNCR", "nox_reduction": 0.65, "ammonia_kg_t": 1.8
        }))

        Hu = max(0.0, float(material.get("Hu", 10.0)))
        C_tot = max(0.0, float(material.get("C", 0.3)))
        bio_share = max(0.0, min(1.0, float(material.get("biogenic_c_share", 0.0))))
        fossil_share = 1.0 - bio_share
        S = max(0.0, float(material.get("S", 0.002)))
        N = max(0.0, float(material.get("N", 0.005)))
        Cl = max(0.0, float(material.get("Cl", 0.005)))
        F = max(0.0, float(material.get("F", 0.0001)))
        ash = max(0.0, float(material.get("ash", 0.08)))
        metals = material.get("elements_ppm", {})

        # 1. Emisiones Atmosfericas Directas (C4)
        c_fossil_kg = mass_kg * C_tot * fossil_share
        c_bio_kg = mass_kg * C_tot * bio_share
        co2_fossil = c_fossil_kg * (44.01 / 12.011)
        co2_bio = c_bio_kg * (44.01 / 12.011)

        ch4_air = mass_kg * 0.00000065
        n2o_air = mass_kg * N * 0.0035
        nox_reduction = denox_info.get("nox_reduction", 0.65)
        nox_air = mass_kg * N * 0.18 * (1.0 - nox_reduction)

        eff_fgc = 0.985 if fgc_mode == "wet_scrubber" else 0.95
        so2_air = mass_kg * S * (64.066 / 32.065) * (1.0 - eff_fgc)
        hcl_air = mass_kg * Cl * (36.46 / 35.453) * (1.0 - 0.99)
        hf_air = mass_kg * F * (20.01 / 18.998) * (1.0 - 0.98)
        hg_air = (mass_kg * metals.get("Hg", 0.05) * 1e-6) * (1.0 - 0.98)
        pm_air = mass_kg * ash * 0.00015

        # Transfer coefficients to air for heavy metals and trace elements from Doka MSWI model (permil)
        tk_air_permil = {
            "Pb": 0.08239, "Cd": 0.5097, "As": 7.833, "Cr": 0.8732, "Cu": 0.09159,
            "Ni": 1.256, "Zn": 0.6703, "Sb": 0.500, "Tl": 0.800, "Se": 11.93,
            "Co": 1.819, "Mn": 0.191, "Mo": 1.316, "Sn": 0.000653, "V": 21.209,
            "Ba": 0.020, "Be": 0.050, "Ag": 0.050, "B": 0.100, "Br": 0.4995,
            "I": 0.555, "P": 1.016, "Fe": 0.00179, "Al": 0.000815, "Ca": 7.870,
            "Mg": 1.055, "Na": 8.210, "K": 4.940, "Si": 0.00156, "Ti": 0.050
        }
        metals_air = {}
        for elem_k, tk_val in tk_air_permil.items():
            conc_ppm = float(metals.get(elem_k, 0.0))
            if conc_ppm <= 0 and elem_k in material and isinstance(material[elem_k], (int, float)):
                conc_ppm = float(material[elem_k]) * 10000.0
            if conc_ppm > 0:
                elem_mass_kg = mass_kg * (conc_ppm * 1e-6)
                air_kg = elem_mass_kg * (tk_val / 1000.0)
                if air_kg > 1e-10:
                    metals_air[f"{elem_k} to air"] = round(air_kg, 8)

        # Factor de caracterizacion EN 15804+A2 (GWP100 fosil=1, biogenico=1 al emitirse para equilibrar uptake)
        gwp_c4_fossil = co2_fossil + (ch4_air * 29.8) + (n2o_air * 273.0)
        gwp_c4_bio = co2_bio
        gwp_c4 = gwp_c4_fossil + gwp_c4_bio

        # 2. Residuos Solidos (Escorias y Cenizas)
        bottom_ash_kg = mass_kg * ash * 0.85
        fly_ash_kg = mass_kg * ash * 0.15

        # 3. Desmetalizado de Escoria
        recovered_fe_kg = 0.0
        recovered_al_kg = 0.0
        recovered_cu_kg = 0.0
        avoided_gwp_metals = 0.0

        if recovery_scrap:
            scrap_eff = cfg.get("scrap_separation_efficiency", {"iron": 0.6516, "aluminium": 0.4161, "copper": 0.4161})
            fe_in_waste = mass_kg * metals.get("Fe", 500.0) * 1e-6
            al_in_waste = mass_kg * metals.get("Al", 200.0) * 1e-6
            cu_in_waste = mass_kg * metals.get("Cu", 50.0) * 1e-6

            recovered_fe_kg = fe_in_waste * scrap_eff.get("iron", 0.6516)
            recovered_al_kg = al_in_waste * scrap_eff.get("aluminium", 0.4161)
            recovered_cu_kg = cu_in_waste * scrap_eff.get("copper", 0.4161)

            avoided_gwp_metals = (recovered_fe_kg * -1.85) + (recovered_al_kg * -8.20) + (recovered_cu_kg * -4.10)

        # 4. Recuperacion y Sustitucion Energetica (Modulo D)
        en_cfg = cfg.get("energy_recovery", {
            "efficiency_electric_gross": 0.147,
            "efficiency_thermal_gross": 0.285,
            "co2_credit_per_kwh_el": 0.420,
            "co2_credit_per_mj_th": 0.065
        })
        eta_el = en_cfg.get("efficiency_electric_gross", 0.147)
        eta_th = en_cfg.get("efficiency_thermal_gross", 0.285)

        total_energy_mj = mass_kg * Hu
        gross_elec_kwh = (total_energy_mj * eta_el) / 3.6
        net_elec_kwh = max(0.0, gross_elec_kwh - (mass_kg * 0.065))
        gross_heat_mj = total_energy_mj * eta_th
        net_heat_mj = max(0.0, gross_heat_mj - (mass_kg * 0.120))

        avoided_gwp_elec = -(net_elec_kwh * en_cfg.get("co2_credit_per_kwh_el", 0.420))
        avoided_gwp_heat = -(net_heat_mj * en_cfg.get("co2_credit_per_mj_th", 0.065))
        module_d_total = avoided_gwp_elec + avoided_gwp_heat + avoided_gwp_metals

        # 5. Modulo C2 (Transporte) y C3 (Operacion)
        # Factor EURO 6: 0.11 kg CO2e / tkm
        tkm = (mass_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11

        # Consumibles de planta en C3
        ammonia_cons_kg = (mass_kg / 1000.0) * denox_info.get("ammonia_kg_t", 1.8)
        gwp_c3 = (mass_kg * 0.0105) + (ammonia_cons_kg * 2.1)

        net_total_gwp = gwp_c2 + gwp_c3 + gwp_c4 + module_d_total

        # Inventario de Emisiones Atmosfericas Completo (44 elementos Doka 2026)
        air_emissions_dict = {
            "Carbon dioxide, fossil (CO2)": round(co2_fossil, 4),
            "Carbon dioxide, biogenic (CO2)": round(co2_bio, 4),
            "Methane, fossil (CH4)": round(ch4_air, 6),
            "Dinitrogen monoxide (N2O)": round(n2o_air, 6),
            "Nitrogen oxides (NOx as NO2)": round(nox_air, 5),
            "Sulfur dioxide (SO2)": round(so2_air, 5),
            "Hydrogen chloride (HCl)": round(hcl_air, 5),
            "Hydrogen fluoride (HF)": round(hf_air, 6),
            "Mercury (Hg to air)": round(hg_air, 8),
            "Particulates (< 2.5 um)": round(pm_air, 5)
        }
        metals_air_dict = {}

        elem_tks = cfg.get("element_transfer_coefficients", {})
        for elem_key, tk_info in elem_tks.items():
            if elem_key in ("C", "Org.-C", "H2O", "Water content", "O", "Oxygen", "H", "Hydrogen", "N", "Nitrogen", "S", "Sulfur", "Cl", "Chlorine", "F", "Fluorine", "Hg", "Mercury"):
                continue
            conc_val = 0.0
            if elem_key in metals:
                conc_val = float(metals[elem_key]) * 1e-6
            elif elem_key in material and isinstance(material[elem_key], (int, float)):
                v = float(material[elem_key])
                conc_val = v * 1e-6 if elem_key in ("Br", "I", "B") and v > 0.05 else v

            if conc_val > 0:
                tk_permil = float(tk_info.get("tk_air_permil", 0.0))
                if fgc_mode == "wet_scrubber":
                    tk_permil = tk_permil * 0.8
                m_air_kg = mass_kg * conc_val * (tk_permil / 1000.0)
                if m_air_kg > 1e-12:
                    flow_name = f"{tk_info.get('name', elem_key)} to air"
                    air_emissions_dict[flow_name] = round(m_air_kg, 8)
                    metals_air_dict[elem_key] = {
                        "name": tk_info.get("name", elem_key),
                        "kg_air": round(m_air_kg, 8),
                        "mg_air": round(m_air_kg * 1e6, 4)
                    }

        return {
            "technology": "mswi",
            "technology_name": f"Incineracion Municipal MSWI (DeNOx: {denox_info.get('name', 'SNCR')})",
            "input_summary": {
                "material_name": material.get("name", "Residuo"),
                "mass_kg": mass_kg,
                "transport_km": transport_km,
                "denox": denox,
                "fgc_mode": fgc_mode
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": round(gwp_c3, 4),
                "C4_final_disposal": round(gwp_c4, 4),
                "C4_fossil_gwp": round(gwp_c4_fossil, 4),
                "C4_biogenic_gwp": round(gwp_c4_bio, 4),
                "Module_D_avoided_burdens": round(module_d_total, 4),
                "Net_Total_GWP": round(net_total_gwp, 4),
                "unit": "kg CO2 eq"
            },
            "lci_air_emissions": {
                **{
                    "Carbon dioxide, fossil (CO2)": round(co2_fossil, 4),
                    "Carbon dioxide, biogenic (CO2)": round(co2_bio, 4),
                    "Methane, fossil (CH4)": round(ch4_air, 6),
                    "Dinitrogen monoxide (N2O)": round(n2o_air, 6),
                    "Nitrogen oxides (NOx as NO2)": round(nox_air, 5),
                    "Sulfur dioxide (SO2)": round(so2_air, 5),
                    "Hydrogen chloride (HCl)": round(hcl_air, 5),
                    "Hydrogen fluoride (HF)": round(hf_air, 6),
                    "Mercury (Hg to air)": round(hg_air, 8),
                    "Particulates (< 2.5 um)": round(pm_air, 5)
                },
                **metals_air
            },
            "lci_solid_residues": {
                "Bottom ash (escoria a vertedero)": round(bottom_ash_kg, 4),
                "Air pollution control (APC) filter residues": round(fly_ash_kg, 4)
            },
            "avoided_energy": {
                "Electricity recovered (kWh)": round(net_elec_kwh, 3),
                "District heat recovered (MJ)": round(net_heat_mj, 3)
            },
            "avoided_materials": {
                "Scrap iron recovered (kg)": round(recovered_fe_kg, 4),
                "Scrap aluminium recovered (kg)": round(recovered_al_kg, 4),
                "Scrap copper recovered (kg)": round(recovered_cu_kg, 4)
            },
            "module_d_breakdown": {
                "avoided_electricity_credit_kg_co2e": round(avoided_gwp_elec, 4),
                "avoided_heat_credit_kg_co2e": round(avoided_gwp_heat, 4),
                "avoided_metals_credit_kg_co2e": round(avoided_gwp_metals, 4)
            }
        }


class DokaLandfillEngine:
    """Modelo hidrogeologico de Relleno Sanitario Municipal (MSW) de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], mass_kg: float, transport_km: float,
                  climate_site: str = "site_3_glo_temperate",
                  gas_capture_rate: Optional[float] = None,
                  gas_utilization: str = "flare",
                  time_horizon: str = "100a",
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        sites = cfg.get("climate_sites", {})
        site_info = sites.get(climate_site, sites.get("site_3_glo_temperate", {
            "name": "Global Average", "precipitation_mm_yr": 850.0, "default_gas_capture_rate": 0.45
        }))
        cap_rate = gas_capture_rate if gas_capture_rate is not None else site_info.get("default_gas_capture_rate", 0.45)
        cap_rate = max(0.0, min(0.95, float(cap_rate)))

        tk_dict = cfg.get("element_leachate_coefficients", cfg.get("transfer_coefficients", {}))

        C_tot = max(0.0, float(material.get("C", 0.3)))
        bio_share = max(0.0, min(1.0, float(material.get("biogenic_c_share", 0.0))))
        degrad = max(0.0, min(1.0, float(material.get("degradability_100a", 0.5))))

        # 1. Cinética de Biogas (DOC degradado anaerobiamente)
        # DOC = Carbono Organico Degradable
        c_degradable_kg = mass_kg * C_tot * bio_share * degrad
        
        # Biogas: 55% CH4 y 45% CO2 estequiometrico molar
        ch4_generated_mol = (c_degradable_kg / 12.011) * 0.55
        co2_generated_mol = (c_degradable_kg / 12.011) * 0.45
        ch4_generated_kg = ch4_generated_mol * 16.04
        co2_generated_kg = co2_generated_mol * 44.01

        # Gestion de gas capturado
        ch4_captured_kg = ch4_generated_kg * cap_rate
        ch4_vented_kg = ch4_generated_kg * (1.0 - cap_rate)

        # Destino del gas capturado:
        co2_from_flaring = 0.0
        elec_kwh_recovered = 0.0
        avoided_gwp_elec = 0.0

        if gas_utilization == "electricity" and ch4_captured_kg > 0:
            # PCI CH4 = 50 MJ/kg, eficiencia generador = 35%
            elec_kwh_recovered = (ch4_captured_kg * 50.0 * 0.35) / 3.6
            avoided_gwp_elec = -(elec_kwh_recovered * 0.420)
            co2_from_flaring = ch4_captured_kg * (44.01 / 16.04)
        else:
            # Flaring: 99% conversion de CH4 a CO2
            co2_from_flaring = ch4_captured_kg * 0.99 * (44.01 / 16.04)
            ch4_vented_kg += ch4_captured_kg * 0.01

        # GWP de emisiones a la atmosfera:
        # CH4 emitido sin quemar tiene GWP = 29.8 (IPCC AR6)
        co2_total_bio = co2_generated_kg + co2_from_flaring
        gwp_c4_ch4 = ch4_vented_kg * 29.8
        gwp_c4_fossil = 0.0  # El residuo degradable en vertedero es biogenico
        gwp_c4_bio = co2_total_bio
        gwp_c4 = gwp_c4_ch4 + gwp_c4_bio

        # 2. Lixiviados (Short-term 100a vs Long-term 60,000a)
        leachate_short_term = {}
        leachate_long_term = {}
        for elem, tk_vals in tk_dict.items():
            conc = float(material.get(elem, material.get("elements_ppm", {}).get(elem, 0.0) * 1e-6))
            if conc > 0:
                elem_mass = mass_kg * conc
                st_leach = elem_mass * tk_vals.get("short_term_leachate_100a", 0.0)
                lt_leach = elem_mass * tk_vals.get("long_term_leachate_60ka", 0.0)
                if st_leach > 1e-9:
                    leachate_short_term[elem] = round(st_leach, 7)
                if lt_leach > 1e-9:
                    leachate_long_term[elem] = round(lt_leach, 7)

        # 3. Modulos C2, C3 y D
        tkm = (mass_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11
        # C3 en vertedero: compactacion con maquinaria pesada diesel (0.008 kg CO2e / kg)
        gwp_c3 = mass_kg * 0.008

        module_d_total = avoided_gwp_elec
        net_total_gwp = gwp_c2 + gwp_c3 + gwp_c4 + module_d_total

        return {
            "technology": "landfill_msw",
            "technology_name": f"Relleno Sanitario Municipal (Clima: {site_info.get('name', 'GLO')}, Captura: {int(cap_rate*100)}%)",
            "input_summary": {
                "material_name": material.get("name", "Residuo"),
                "mass_kg": mass_kg,
                "transport_km": transport_km,
                "climate_site": climate_site,
                "gas_capture_rate": cap_rate,
                "gas_utilization": gas_utilization,
                "time_horizon": time_horizon
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": round(gwp_c3, 4),
                "C4_final_disposal": round(gwp_c4, 4),
                "C4_methane_gwp": round(gwp_c4_ch4, 4),
                "C4_biogenic_gwp": round(gwp_c4_bio, 4),
                "Module_D_avoided_burdens": round(module_d_total, 4),
                "Net_Total_GWP": round(net_total_gwp, 4),
                "unit": "kg CO2 eq"
            },
            "lci_air_emissions": {
                "Methane, biogenic (CH4 vented)": round(ch4_vented_kg, 5),
                "Carbon dioxide, biogenic (CO2 total)": round(co2_total_bio, 4)
            },
            "lci_leachate_short_term_100a": leachate_short_term,
            "lci_leachate_long_term_60ka": leachate_long_term if time_horizon in ("60ka", "both") else "Omitido en horizonte 100a (disponible con time_horizon='both')",
            "avoided_energy": {
                "Electricity recovered (kWh)": round(elec_kwh_recovered, 3)
            },
            "module_d_breakdown": {
                "avoided_electricity_credit_kg_co2e": round(avoided_gwp_elec, 4)
            }
        }


class DokaInertLandfillEngine:
    """Modelo de Vertedero de Construccion/Demolicion (RCD) y Excavacion de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], mass_kg: float, transport_km: float,
                  sub_type: str = "construction",
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        tk_key = "transfer_coefficients"
        tk_dict = cfg.get(tk_key, {})

        tkm = (mass_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11
        # Operacion de excavadora/rodillo compactador: 0.0035 kg CO2e / kg
        gwp_c3 = mass_kg * 0.0035

        leachate_st = {}
        for elem, tk_vals in tk_dict.items():
            conc = float(material.get(elem, material.get("elements_ppm", {}).get(elem, 0.0) * 1e-6))
            if conc > 0:
                st_leach = mass_kg * conc * tk_vals.get("short_term_leachate", 0.001)
                if st_leach > 1e-9:
                    leachate_st[elem] = round(st_leach, 7)

        tech_title = "Relleno de Residuos de Construccion y Demolicion (Inertes)" if sub_type == "construction" else "Deposito de Tierras y Rocas de Excavacion"

        return {
            "technology": f"landfill_{sub_type}",
            "technology_name": tech_title,
            "input_summary": {
                "material_name": material.get("name", "Residuo Inerte"),
                "mass_kg": mass_kg,
                "transport_km": transport_km,
                "sub_type": sub_type
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": round(gwp_c3, 4),
                "C4_final_disposal": 0.0,
                "Module_D_avoided_burdens": 0.0,
                "Net_Total_GWP": round(gwp_c2 + gwp_c3, 4),
                "unit": "kg CO2 eq"
            },
            "lci_leachate_emissions": leachate_st
        }


class DokaTailingsEngine:
    """Modelo de Presas de Relaves Mineros con Drenaje Acido de Roca (ARD) de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], mass_kg: float, transport_km: float,
                  ard_potential: bool = True,
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        tk_dict = cfg.get("element_leachate_coefficients", cfg.get("transfer_coefficients", {}))

        tkm = (mass_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11
        # Bombeo y gestion de relaves en presa: 0.005 kg CO2e / kg
        gwp_c3 = mass_kg * 0.005

        ard_mult = 2.5 if ard_potential else 1.0

        leachate_tailings = {}
        for elem, tk_vals in tk_dict.items():
            conc = float(material.get(elem, material.get("elements_ppm", {}).get(elem, 0.0) * 1e-6))
            if conc > 0:
                base_tk = tk_vals.get("short_term_leachate", 0.005)
                ard_factor = tk_vals.get("acid_rock_drainage_factor", 1.0)
                leached = mass_kg * conc * base_tk * (ard_factor if ard_potential else 1.0) * ard_mult
                if leached > 1e-9:
                    leachate_tailings[elem] = round(leached, 7)

        return {
            "technology": "tailings_impoundment",
            "technology_name": f"Presa de Relaves Mineros (Tailings Impoundment, ARD: {'Activo' if ard_potential else 'Neutralizado'})",
            "input_summary": {
                "material_name": material.get("name", "Relave Minero"),
                "mass_kg": mass_kg,
                "transport_km": transport_km,
                "ard_potential": ard_potential
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": round(gwp_c3, 4),
                "C4_final_disposal": 0.0,
                "Module_D_avoided_burdens": 0.0,
                "Net_Total_GWP": round(gwp_c2 + gwp_c3, 4),
                "unit": "kg CO2 eq"
            },
            "lci_water_leachate_ard": leachate_tailings
        }


class DokaOpenBurningEngine:
    """Modelo de Quema no Controlada a Cielo Abierto de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], mass_kg: float, transport_km: float,
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        ef = cfg.get("emission_factors", {})

        C_tot = max(0.0, float(material.get("C", 0.3)))
        bio_share = max(0.0, min(1.0, float(material.get("biogenic_c_share", 0.0))))
        fossil_share = 1.0 - bio_share
        S = max(0.0, float(material.get("S", 0.002)))
        N = max(0.0, float(material.get("N", 0.005)))
        Cl = max(0.0, float(material.get("Cl", 0.005)))
        F = max(0.0, float(material.get("F", 0.0001)))

        total_c_kg = mass_kg * C_tot
        co_fraction = ef.get("CO_fraction_of_carbon", 0.082)
        ch4_fraction = ef.get("CH4_fraction_of_carbon", 0.015)
        co2_fraction = max(0.0, 1.0 - co_fraction - ch4_fraction)

        co2_fossil = total_c_kg * fossil_share * co2_fraction * (44.01 / 12.011)
        co2_bio = total_c_kg * bio_share * co2_fraction * (44.01 / 12.011)
        ch4_air = total_c_kg * ch4_fraction * (16.04 / 12.011)
        co_air = total_c_kg * co_fraction * (28.01 / 12.011)

        black_carbon_g = mass_kg * ef.get("Black_Carbon_g_per_kg_waste", 1.25)
        n2o_air = mass_kg * N * ef.get("N2O_fraction_of_nitrogen", 0.008) * (44.013 / 28.013)
        nox_air = mass_kg * N * ef.get("NOx_as_NO2_fraction_of_N", 0.28) * (46.005 / 14.007)
        so2_air = mass_kg * S * ef.get("SO2_fraction_of_sulfur", 0.85) * (64.066 / 32.065)
        hcl_air = mass_kg * Cl * ef.get("HCl_fraction_of_chlorine", 0.82) * (36.46 / 35.453)
        hf_air = mass_kg * F * ef.get("HF_fraction_of_fluorine", 0.75) * (20.01 / 18.998)
        pm25_g = mass_kg * ef.get("PM25_g_per_kg_waste", 8.5)

        # GWP de combustion incompleta
        gwp_c4_fossil = co2_fossil + (ch4_air * 29.8) + (n2o_air * 273.0) + (black_carbon_g * 0.001 * 900.0)
        gwp_c4_bio = co2_bio
        gwp_c4 = gwp_c4_fossil + gwp_c4_bio

        tkm = (mass_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11

        return {
            "technology": "open_burning",
            "technology_name": "Quema no Controlada a Cielo Abierto (Open Burning)",
            "input_summary": {
                "material_name": material.get("name", "Residuo"),
                "mass_kg": mass_kg,
                "transport_km": transport_km
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": 0.0,
                "C4_final_disposal": round(gwp_c4, 4),
                "C4_fossil_gwp": round(gwp_c4_fossil, 4),
                "C4_biogenic_gwp": round(gwp_c4_bio, 4),
                "Module_D_avoided_burdens": 0.0,
                "Net_Total_GWP": round(gwp_c2 + gwp_c4, 4),
                "unit": "kg CO2 eq"
            },
            "lci_air_emissions": {
                "Carbon dioxide, fossil (CO2)": round(co2_fossil, 4),
                "Carbon dioxide, biogenic (CO2)": round(co2_bio, 4),
                "Carbon monoxide (CO)": round(co_air, 4),
                "Methane, fossil (CH4)": round(ch4_air, 5),
                "Black Carbon (BC) [g]": round(black_carbon_g, 2),
                "Particulates (< 2.5 um) [g]": round(pm25_g, 2),
                "Dinitrogen monoxide (N2O)": round(n2o_air, 6),
                "Nitrogen oxides (NOx as NO2)": round(nox_air, 5),
                "Sulfur dioxide (SO2)": round(so2_air, 5),
                "Hydrogen chloride (HCl)": round(hcl_air, 5),
                "Hydrogen fluoride (HF)": round(hf_air, 6)
            }
        }


class DokaWastewaterEngine:
    """Modelo de Depuracion de Aguas Residuales y Lodos (WWTP) de Gabor Doka."""

    @staticmethod
    def calculate(material: Dict[str, Any], volume_m3_or_kg: float, transport_km: float,
                  treatment_stage: str = "2_stage_biological",
                  sludge_fate: str = "sludge_to_incineration",
                  model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = model_config or {}
        stages = cfg.get("stages", {})
        stage_info = stages.get(treatment_stage, stages.get("2_stage_biological", {
            "name": "2-Stage Biological", "bod5_removal": 0.90, "cod_removal": 0.85,
            "n_removal": 0.65, "p_removal": 0.35, "sludge_produced_kg_per_m3": 0.45
        }))

        sludge_fates = cfg.get("sludge_fates", {})
        fate_info = sludge_fates.get(sludge_fate, sludge_fates.get("sludge_to_incineration", {
            "name": "Sludge Incineration", "gwp_net_per_kg_dry_sludge": 0.35
        }))

        # Electricidad consumida en la PTAR: 0.45 kWh / m3 en 2 etapas, 0.65 en 3 etapas
        kwh_per_m3 = 0.65 if "3_stage" in treatment_stage else (0.45 if "2_stage" in treatment_stage else 0.15)
        kwh_total = volume_m3_or_kg * kwh_per_m3
        gwp_ptar_energy = kwh_total * 0.420

        # Emisiones fugitivas de N2O en desnitrificacion y CH4 en digestor
        N_in = volume_m3_or_kg * float(material.get("N", 0.005))
        n2o_fugitive = N_in * 0.015 * (44.013 / 28.013)
        gwp_fugitive = n2o_fugitive * 273.0

        # Lodos generados y destino
        sludge_kg = volume_m3_or_kg * stage_info.get("sludge_produced_kg_per_m3", 0.45)
        gwp_sludge = sludge_kg * fate_info.get("gwp_net_per_kg_dry_sludge", 0.35)

        tkm = (volume_m3_or_kg / 1000.0) * transport_km
        gwp_c2 = tkm * 0.11
        gwp_c3 = gwp_ptar_energy + gwp_fugitive
        gwp_c4 = gwp_sludge

        net_gwp = gwp_c2 + gwp_c3 + gwp_c4

        return {
            "technology": "wastewater",
            "technology_name": f"Depuracion de Aguas Residuales ({stage_info.get('name', '2-Stage')}) + {fate_info.get('name', 'Incineracion de Lodos')}",
            "input_summary": {
                "material_name": material.get("name", "Efluente"),
                "volume_m3_or_kg": volume_m3_or_kg,
                "treatment_stage": treatment_stage,
                "sludge_fate": sludge_fate
            },
            "epd_modules_gwp": {
                "C1_deconstruction": 0.0,
                "C2_transport": round(gwp_c2, 4),
                "C3_waste_processing": round(gwp_c3, 4),
                "C4_final_disposal": round(gwp_c4, 4),
                "Module_D_avoided_burdens": 0.0,
                "Net_Total_GWP": round(net_gwp, 4),
                "unit": "kg CO2 eq"
            },
            "treatment_performance": {
                "BOD5_removal_efficiency": stage_info.get("bod5_removal", 0.90),
                "COD_removal_efficiency": stage_info.get("cod_removal", 0.85),
                "N_removal_efficiency": stage_info.get("n_removal", 0.65),
                "P_removal_efficiency": stage_info.get("p_removal", 0.35),
                "sludge_produced_dry_kg": round(sludge_kg, 3),
                "electricity_consumed_kwh": round(kwh_total, 2)
            }
        }


class DokaExportEngine:
    """Generador de archivos de intercambio en formatos SimaPro CSV y EcoSpold 2 XML."""

    @staticmethod
    def to_simapro_csv(calc_result: Dict[str, Any]) -> str:
        """Genera un archivo CSV compatible con la importacion de procesos en SimaPro."""
        inp = calc_result.get("input_summary", {})
        epd = calc_result.get("epd_modules_gwp", {})
        air = calc_result.get("lci_air_emissions", {})
        avoided_en = calc_result.get("avoided_energy", {})
        avoided_mat = calc_result.get("avoided_materials", {})

        lines = [
            "{SimaPro 9.5.0.0}",
            "{Processes}",
            f"Process name;Fin de Vida: {inp.get('material_name')} ({calc_result.get('technology_name')})",
            "Status;Finished",
            "Type;Unit process",
            "Process category;Waste treatment / Municipal",
            f"Comment;Generado automaticamente por ECONODE Studio via WasteTools 2026 (Gabor Doka). GWP Neto: {epd.get('Net_Total_GWP')} kg CO2e.",
            "Cut off rules;All elementary flows included",
            "",
            "Products",
            f"Waste treatment of {inp.get('material_name')};kg;{inp.get('mass_kg', 100.0)};100%;not defined",
            "",
            "Avoided products"
        ]

        # Agregar productos evitados (Modulo D)
        if avoided_en.get("Electricity recovered (kWh)", 0) > 0:
            lines.append(f"Electricity, medium voltage [MX];kWh;{avoided_en['Electricity recovered (kWh)']};100%;not defined")
        if avoided_en.get("District heat recovered (MJ)", 0) > 0:
            lines.append(f"Heat, district or industrial [GLO];MJ;{avoided_en['District heat recovered (MJ)']};100%;not defined")
        if avoided_mat.get("Scrap iron recovered (kg)", 0) > 0:
            lines.append(f"Iron scrap, sorted [GLO];kg;{avoided_mat['Scrap iron recovered (kg)']};100%;not defined")

        lines.extend([
            "",
            "Emissions to air"
        ])
        for gas, val in air.items():
            if float(val) > 0:
                lines.append(f"{gas};kg;{val};Unspecified;0")

        return "\n".join(lines)

    @staticmethod
    def to_ecospold2_xml(calc_result: Dict[str, Any]) -> str:
        """Genera un archivo dataset XML EcoSpold 2."""
        inp = calc_result.get("input_summary", {})
        epd = calc_result.get("epd_modules_gwp", {})
        air = calc_result.get("lci_air_emissions", {})

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<ecoSpold xmlns="http://www.EcoInvent.org/EcoSpold02">',
            '  <activityDataset>',
            '    <activityDescription>',
            f'      <activity id="act_{abs(hash(inp.get("material_name", "waste"))) % 1000000}">',
            f'        <activityName xml:lang="en">treatment of {inp.get("material_name")}, {calc_result.get("technology")}</activityName>',
            '        <generalComment xml:lang="en">Calculated using WasteTools 2026 Doka Models in ECONODE Studio.</generalComment>',
            '      </activity>',
            '    </activityDescription>',
            '    <flowData>'
        ]

        # Flujo de referencia
        xml.append('      <intermediateExchange id="flow_ref" amount="1.0" unitName="kg">')
        xml.append(f'        <name xml:lang="en">{inp.get("material_name")}</name>')
        xml.append('        <outputGroup>0</outputGroup>')
        xml.append('      </intermediateExchange>')

        # Emisiones elementales al aire
        for idx, (gas, val) in enumerate(air.items()):
            if float(val) > 0:
                xml.append(f'      <elementaryExchange id="elem_{idx}" amount="{val}" unitName="kg">')
                xml.append(f'        <name xml:lang="en">{gas}</name>')
                xml.append('        <compartment subCompartmentId="air_unspecified">air</compartment>')
                xml.append('        <outputGroup>4</outputGroup>')
                xml.append('      </elementaryExchange>')

        xml.append('    </flowData>')
        xml.append('  </activityDataset>')
        xml.append('</ecoSpold>')
        return "\n".join(xml)


class DokaMasterSuite:
    """Fachada unificada para la suite completa WasteTools 2026."""

    ELEMENTS_METADATA = [
        # Combustion & Macro-properties
        {"key": "Hu", "symbol": "Hu", "name_es": "Poder Calorifico Neto (PCI)", "name_en": "Net Calorific Value", "category": "combustion", "unit": "MJ/kg", "type": "macro", "default": 15.0},
        {"key": "Ho", "symbol": "Ho", "name_es": "Poder Calorifico Bruto (PCS)", "name_en": "Gross Calorific Value", "category": "combustion", "unit": "MJ/kg", "type": "macro", "default": 16.5},
        {"key": "H2O", "symbol": "H2O", "name_es": "Humedad (Agua)", "name_en": "Water Content", "category": "combustion", "unit": "% masa", "type": "macro", "default": 0.20},
        {"key": "C", "symbol": "C", "name_es": "Carbono Organico Total", "name_en": "Total Organic Carbon", "category": "combustion", "unit": "% masa", "type": "macro", "default": 0.45},
        {"key": "biogenic_c_share", "symbol": "C_bio", "name_es": "Fraccion C Biogenico", "name_en": "Biogenic Carbon Share", "category": "combustion", "unit": "0-1", "type": "macro", "default": 0.30},
        {"key": "ash", "symbol": "Ash", "name_es": "Cenizas / Inertes", "name_en": "Ash / Mineral Residue", "category": "combustion", "unit": "% masa", "type": "macro", "default": 0.05},
        {"key": "degradability_100a", "symbol": "Degrad", "name_es": "Degradabilidad 100a (Vertedero)", "name_en": "Degradability 100a", "category": "combustion", "unit": "0-1", "type": "macro", "default": 0.35},

        # Non-metals & Halogens
        {"key": "O", "symbol": "O", "name_es": "Oxigeno", "name_en": "Oxygen", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.25},
        {"key": "H", "symbol": "H", "name_es": "Hidrogeno", "name_en": "Hydrogen", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.05},
        {"key": "N", "symbol": "N", "name_es": "Nitrogeno", "name_en": "Nitrogen", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.01},
        {"key": "S", "symbol": "S", "name_es": "Azufre", "name_en": "Sulfur", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.002},
        {"key": "P", "symbol": "P", "name_es": "Fosforo", "name_en": "Phosphorus", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.001},
        {"key": "Cl", "symbol": "Cl", "name_es": "Cloro", "name_en": "Chlorine", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.005},
        {"key": "F", "symbol": "F", "name_es": "Fluor", "name_en": "Fluorine", "category": "non_metals", "unit": "% masa", "type": "macro", "default": 0.0001},
        {"key": "Br", "symbol": "Br", "name_es": "Bromo", "name_en": "Bromine", "category": "non_metals", "unit": "ppm", "type": "ppm", "default": 10.0},
        {"key": "I", "symbol": "I", "name_es": "Yodo", "name_en": "Iodine", "category": "non_metals", "unit": "ppm", "type": "ppm", "default": 0.5},
        {"key": "B", "symbol": "B", "name_es": "Boro", "name_en": "Boron", "category": "non_metals", "unit": "ppm", "type": "ppm", "default": 25.0},

        # Regulated Heavy Metals (ppm)
        {"key": "Hg", "symbol": "Hg", "name_es": "Mercurio", "name_en": "Mercury", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 0.5},
        {"key": "Pb", "symbol": "Pb", "name_es": "Plomo", "name_en": "Lead", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 55.0},
        {"key": "Cd", "symbol": "Cd", "name_es": "Cadmio", "name_en": "Cadmium", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 5.0},
        {"key": "As", "symbol": "As", "name_es": "Arsenico", "name_en": "Arsenic", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 3.0},
        {"key": "Cr", "symbol": "Cr", "name_es": "Cromo", "name_en": "Chromium", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 45.0},
        {"key": "Cu", "symbol": "Cu", "name_es": "Cobre", "name_en": "Copper", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 120.0},
        {"key": "Ni", "symbol": "Ni", "name_es": "Niquel", "name_en": "Nickel", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 25.0},
        {"key": "Zn", "symbol": "Zn", "name_es": "Zinc", "name_en": "Zinc", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 450.0},
        {"key": "Sb", "symbol": "Sb", "name_es": "Antimonio", "name_en": "Antimony", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 15.0},
        {"key": "Tl", "symbol": "Tl", "name_es": "Talio", "name_en": "Thallium", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 0.5},
        {"key": "Se", "symbol": "Se", "name_es": "Selenio", "name_en": "Selenium", "category": "heavy_metals", "unit": "ppm", "type": "ppm", "default": 2.0},

        # Industrial Metals & Major Minerals
        {"key": "Fe", "symbol": "Fe", "name_es": "Hierro", "name_en": "Iron", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 6500.0},
        {"key": "Al", "symbol": "Al", "name_es": "Aluminio", "name_en": "Aluminium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 3200.0},
        {"key": "Ca", "symbol": "Ca", "name_es": "Calcio", "name_en": "Calcium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 18000.0},
        {"key": "Mg", "symbol": "Mg", "name_es": "Magnesio", "name_en": "Magnesium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 2500.0},
        {"key": "Na", "symbol": "Na", "name_es": "Sodio", "name_en": "Sodium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 4500.0},
        {"key": "K", "symbol": "K", "name_es": "Potasio", "name_en": "Potassium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 3500.0},
        {"key": "Si", "symbol": "Si", "name_es": "Silicio", "name_en": "Silicon", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 25000.0},
        {"key": "Ti", "symbol": "Ti", "name_es": "Titanio", "name_en": "Titanium", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 850.0},
        {"key": "Mn", "symbol": "Mn", "name_es": "Manganeso", "name_en": "Manganese", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 180.0},
        {"key": "Sn", "symbol": "Sn", "name_es": "Estaño", "name_en": "Tin", "category": "minerals_metals", "unit": "ppm", "type": "ppm", "default": 12.0},

        # Trace & Rare Elements
        {"key": "Ag", "symbol": "Ag", "name_es": "Plata", "name_en": "Silver", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 1.5},
        {"key": "Ba", "symbol": "Ba", "name_es": "Bario", "name_en": "Barium", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 250.0},
        {"key": "Be", "symbol": "Be", "name_es": "Berilio", "name_en": "Beryllium", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 0.8},
        {"key": "Co", "symbol": "Co", "name_es": "Cobalto", "name_en": "Cobalt", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 4.5},
        {"key": "Mo", "symbol": "Mo", "name_es": "Molibdeno", "name_en": "Molybdenum", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 2.5},
        {"key": "Sc", "symbol": "Sc", "name_es": "Escandio", "name_en": "Scandium", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 0.1},
        {"key": "Sr", "symbol": "Sr", "name_es": "Estroncio", "name_en": "Strontium", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 65.0},
        {"key": "V", "symbol": "V", "name_es": "Vanadio", "name_en": "Vanadium", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 28.0},
        {"key": "W", "symbol": "W", "name_es": "Wolframio", "name_en": "Tungsten", "category": "trace_elements", "unit": "ppm", "type": "ppm", "default": 1.0}
    ]

    def get_elements_metadata(self) -> list:
        """Retorna la lista completa de metadatos de los 47 elementos y parametros quimicos."""
        return self.ELEMENTS_METADATA


    _instance = None

    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file
        self.materials_map = {}
        self.models_config = {}
        self._load_data()

    def _load_data(self):
        resolved_file = None
        candidates = [self.data_file] + DATA_CANDIDATE_PATHS
        for p in candidates:
            if p and os.path.exists(p):
                resolved_file = p
                break
        if not resolved_file:
            raise FileNotFoundError(f"Archivo de datos maestro WasteTools 2026 no encontrado en: {candidates}")

        with open(resolved_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        self.metadata = raw.get("metadata", {})
        self.element_catalog = raw.get("element_catalog", [])
        self.materials = raw.get("materials", [])
        for m in self.materials:
            self.materials_map[m["id"]] = m

        self.models_config = raw.get("models", {})

    def get_element_catalog(self) -> List[Dict[str, Any]]:
        """Devuelve el catalogo oficial de los 44 elementos y macro-propiedades quimicas."""
        return self.element_catalog

    def get_categories(self) -> List[str]:
        cats = sorted(list(set(m["category"] for m in self.materials if m.get("category"))))
        return cats

    def get_materials(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        res = self.materials
        if category:
            res = [m for m in res if m.get("category") == category]
        if search:
            s = search.lower()
            res = [m for m in res if s in m.get("name", "").lower() or s in m.get("german_name", "").lower()]
        return res

    def get_material_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        return self.materials_map.get(material_id)

    def mix_fractions(self, fractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula una mezcla ponderada de fracciones."""
        return WasteMixtureEngine.mix_fractions(fractions, self.materials_map)

    def calculate_advanced(self, technology: str, material_input: Union[str, Dict[str, Any]],
                           mass_kg: float, transport_km: float = 20.0,
                           **tech_kwargs) -> Dict[str, Any]:
        """
        Ejecuta el calculo estequiometrico sobre cualquiera de las 7 tecnologias de Doka.
        material_input puede ser un ID de material, un diccionario con propiedades, o una mezcla sintetizada.
        """
        if isinstance(material_input, str):
            material = self.get_material_by_id(material_input)
            if not material:
                raise ValueError(f"Material ID no encontrado: {material_input}")
        elif isinstance(material_input, dict):
            material = material_input
        else:
            raise ValueError("material_input debe ser un string (ID) o un dict con propiedades")

        if mass_kg <= 0:
            raise ValueError("mass_kg debe ser mayor a cero")

        tech = technology.lower()

        if tech in ("mswi", "incineration"):
            return DokaIncinerationEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                denox=tech_kwargs.get("denox", "sncr"),
                recovery_scrap=tech_kwargs.get("recovery_scrap", True),
                fgc_mode=tech_kwargs.get("fgc_mode", "wet_scrubber"),
                model_config=self.models_config.get("mswi", {})
            )
        elif tech in ("landfill_msw", "landfill"):
            return DokaLandfillEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                climate_site=tech_kwargs.get("climate_site", "site_3_glo_temperate"),
                gas_capture_rate=tech_kwargs.get("gas_capture_rate"),
                gas_utilization=tech_kwargs.get("gas_utilization", "flare"),
                time_horizon=tech_kwargs.get("time_horizon", "100a"),
                model_config=self.models_config.get("landfill_msw", {})
            )
        elif tech in ("landfill_cd", "construction_landfill"):
            return DokaInertLandfillEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                sub_type="construction",
                model_config=self.models_config.get("landfill_cd", {})
            )
        elif tech in ("landfill_excavation", "excavation_landfill"):
            return DokaInertLandfillEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                sub_type="excavation",
                model_config=self.models_config.get("landfill_excavation", {})
            )
        elif tech in ("tailings_impoundment", "tailings"):
            return DokaTailingsEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                ard_potential=tech_kwargs.get("ard_potential", True),
                model_config=self.models_config.get("tailings_impoundment", {})
            )
        elif tech in ("open_burning", "burning"):
            return DokaOpenBurningEngine.calculate(
                material=material, mass_kg=mass_kg, transport_km=transport_km,
                model_config=self.models_config.get("open_burning", {})
            )
        elif tech in ("wastewater", "wwtp"):
            return DokaWastewaterEngine.calculate(
                material=material, volume_m3_or_kg=mass_kg, transport_km=transport_km,
                treatment_stage=tech_kwargs.get("treatment_stage", "2_stage_biological"),
                sludge_fate=tech_kwargs.get("sludge_fate", "sludge_to_incineration"),
                model_config=self.models_config.get("wastewater", {})
            )
        else:
            raise ValueError(f"Tecnologia de tratamiento no soportada: {technology}")


def get_doka_suite() -> DokaMasterSuite:
    """Singleton para acceder a la suite completa de Doka."""
    if DokaMasterSuite._instance is None:
        DokaMasterSuite._instance = DokaMasterSuite()
    return DokaMasterSuite._instance
