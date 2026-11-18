"""
econode_studio/application/epd_service.py - Casos de Uso para Plantillas Preliminares EPD y Estructuracion de Reportes
Alineado con ISO 14025, ISO 21930:2017, EN 15804+A2:2019 y OpenEPD (SmartEPD).
"""

import os
import json
import copy
import datetime
import sqlite3
from typing import Dict, List, Any, Optional

try:
    from domain.epd_models import (
        EPD_MODULES, EPD_MODULE_CODES, SMART_EPD_PCR_REGISTRY,
        EPD_INDICATORS_EN15804_A2, EPD_INDICATORS_TRACI_2_1,
        EPD_RESOURCE_INDICATORS, EPD_WASTE_OUTPUT_INDICATORS,
        EPD_PRELIMINARY_TEMPLATES, get_default_epd_config
    )
    from infrastructure.database_adapter import (
        get_active_db_connection, create_product_system,
        get_product_system_details, save_system_canvas, ensure_product_systems_columns
    )
except (ImportError, ValueError):
    from econode_studio.domain.epd_models import (
        EPD_MODULES, EPD_MODULE_CODES, SMART_EPD_PCR_REGISTRY,
        EPD_INDICATORS_EN15804_A2, EPD_INDICATORS_TRACI_2_1,
        EPD_RESOURCE_INDICATORS, EPD_WASTE_OUTPUT_INDICATORS,
        EPD_PRELIMINARY_TEMPLATES, get_default_epd_config
    )
    from econode_studio.infrastructure.database_adapter import (
        get_active_db_connection, create_product_system,
        get_product_system_details, save_system_canvas, ensure_product_systems_columns
    )


def list_epd_templates_use_case(industry_id: Optional[str] = None) -> Dict[str, Any]:
    """Retorna el catalogo de plantillas preliminares EPD, registro de PCRs SmartEPD y taxonomia modular A1-D."""
    templates_out = []
    for tpl_id, tpl in EPD_PRELIMINARY_TEMPLATES.items():
        if industry_id and industry_id != "ALL" and tpl.get("industry_id") != industry_id:
            continue
        templates_out.append({
            "template_id": tpl_id,
            "industry_id": tpl["industry_id"],
            "sub_sector": tpl["sub_sector"],
            "name_es": tpl["name_es"],
            "name_en": tpl["name_en"],
            "short_desc_es": tpl["short_desc_es"],
            "short_desc_en": tpl["short_desc_en"],
            "code_prefix": tpl["code_prefix"],
            "declared_unit_amount": tpl["declared_unit_amount"],
            "declared_unit_symbol": tpl["declared_unit_symbol"],
            "declared_unit_label_es": tpl["declared_unit_label_es"],
            "declared_unit_label_en": tpl["declared_unit_label_en"],
            "system_boundary": tpl["system_boundary"],
            "declared_modules": tpl["declared_modules"],
            "pcr_reference": tpl["pcr_reference"],
            "standards": tpl["standards"],
            "un_cpc": tpl["un_cpc"],
            "nodes_count": len(tpl["nodes"]),
            "edges_count": len(tpl["edges"]),
            "key_override": tpl.get("key_override"),
            "technical_specs": tpl.get("technical_specs", {})
        })

    return {
        "status": "success",
        "templates": templates_out,
        "industries": SMART_EPD_PCR_REGISTRY,
        "modules": EPD_MODULES
    }


def _apply_template_overrides(tpl: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica ajustes parametricos del usuario (ej. % clinker o dosificacion de cemento) sobre una copia de la plantilla."""
    cloned = copy.deepcopy(tpl)
    key_ov = cloned.get("key_override")
    if not key_ov:
        return cloned

    param_name = key_ov["param_name"]
    raw_val = overrides.get(param_name) if overrides.get(param_name) is not None else overrides.get("key_param_value")
    if raw_val in (None, ""):
        return cloned

    try:
        new_val = float(raw_val)
    except (ValueError, TypeError):
        return cloned

    default_val = float(key_ov["default"])
    if default_val <= 0 or abs(new_val - default_val) < 1e-6:
        return cloned

    ratio = new_val / default_val

    # Actualizar lista de parametros
    for p in cloned.get("parameters", []):
        if p.get("name") == param_name:
            p["value"] = round(new_val, 3)

    # Escalar flujos clave segun tipo de plantilla
    if param_name == "clinker_ratio_pct":
        # Ajustar composicion y calcinacion/combustibles en horno A3
        for comp in cloned.get("composition", []):
            if "clinker" in comp.get("material_en", "").lower():
                comp["share_pct"] = round(new_val, 2)
                comp["mass_kg"] = round(new_val * 10.0, 2)
        if "technical_specs" in cloned:
            cloned["technical_specs"]["clinker_ratio_pct"] = round(new_val, 2)
        for node in cloned.get("nodes", []):
            if node.get("epd_module") == "A3":
                for inp in node.get("inputs", []):
                    n_low = (inp.get("name") or "").lower()
                    if any(k in n_low for k in ("petcoke", "petroleum coke", "natural gas", "kiln")):
                        inp["amount"] = round(float(inp["amount"]) * ratio, 2)
                for out in node.get("outputs", []):
                    n_low = (out.get("name") or "").lower()
                    if "calcination" in n_low or "carbon dioxide" in n_low:
                        out["amount"] = round(float(out["amount"]) * ratio, 2)
            elif node.get("epd_module") == "A1":
                for inp in node.get("inputs", []):
                    n_low = (inp.get("name") or "").lower()
                    if "limestone, crushed" in n_low or "clay" in n_low:
                        inp["amount"] = round(float(inp["amount"]) * ratio, 2)

    elif param_name == "cement_dosage_kg_m3":
        for comp in cloned.get("composition", []):
            if "portland cement" in comp.get("material_en", "").lower():
                comp["mass_kg"] = round(new_val, 2)
        total_mass = sum(float(c.get("mass_kg", 0.0)) for c in cloned.get("composition", []))
        if total_mass > 0:
            for comp in cloned.get("composition", []):
                comp["share_pct"] = round((float(comp.get("mass_kg", 0.0)) / total_mass) * 100.0, 2)
        for node in cloned.get("nodes", []):
            if node.get("epd_module") == "A1":
                for inp in node.get("inputs", []):
                    if "portland cement" in (inp.get("name") or "").lower():
                        inp["amount"] = round(new_val, 2)

    return cloned


def instantiate_epd_template_use_case(
    conn: Optional[sqlite3.Connection] = None,
    template_id: str = "epd_concrete_rmx_4000",
    overrides: Optional[Dict[str, Any]] = None,
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Instancia una plantilla preliminar EPD como un nuevo Sistema Producto completo con nodos A1-D y metadatos EPD."""
    overrides = overrides or {}
    if template_id not in EPD_PRELIMINARY_TEMPLATES:
        raise ValueError(f"Plantilla EPD '{template_id}' no encontrada.")

    tpl = _apply_template_overrides(EPD_PRELIMINARY_TEMPLATES[template_id], overrides)

    custom_name = (overrides.get("name") or "").strip() or tpl["name_es"]
    custom_code = (overrides.get("code") or "").strip() or f"{tpl['code_prefix']}-{os.urandom(2).hex().upper()}"
    geography = (overrides.get("geography") or "").strip() or tpl["geography"]
    plant_location = (overrides.get("plant_location") or "").strip()
    program_operator = (overrides.get("program_operator") or "").strip()
    default_standard = (overrides.get("default_standard") or "EN15804_A2").strip()
    raw_proj = overrides.get("project_id")
    project_id = int(raw_proj) if raw_proj not in (None, "", "null", 0, "0") else None

    owner_id = (user.get("id") if user else None) or overrides.get("owner_id") or "analyst_carla"
    owner_email = (user.get("email") if user else None) or overrides.get("owner_email") or "carla.mendez@econode.io"
    owner_name = (user.get("display_name") if user else None) or overrides.get("owner_name") or "Carla Mendez"
    owner_role = (user.get("role") if user else None) or overrides.get("owner_role") or "analyst"
    owner_org = (user.get("organization") if user else None) or overrides.get("owner_org") or "ECONODE Industrial S.A. de C.V."

    epd_config = get_default_epd_config(
        system_name=custom_name,
        declared_unit=tpl["declared_unit_label_es"],
        org_name=owner_org,
        geography=geography,
        template_id=template_id
    )
    epd_config["composition"] = tpl.get("composition", epd_config["composition"])
    epd_config["technical_specs"] = tpl.get("technical_specs", epd_config["technical_specs"])
    epd_config["default_standard"] = default_standard
    if plant_location:
        epd_config["plant_location"] = plant_location
    if program_operator:
        epd_config["program_operator"] = program_operator
    if overrides.get("declaration_holder"):
        epd_config["declaration_holder"] = str(overrides["declaration_holder"]).strip()

    description = f"[EPD {tpl['system_boundary']}] {tpl['short_desc_es']} | PCR: {tpl['pcr_reference']}"

    def _execute(c: sqlite3.Connection):
        sys_id = create_product_system(
            c,
            name=custom_name,
            code=custom_code,
            target_amount=float(tpl["declared_unit_amount"]),
            description=description,
            owner_id=owner_id,
            owner_email=owner_email,
            owner_name=owner_name,
            owner_role=owner_role,
            owner_org=owner_org,
            category=tpl["category"],
            geography=geography,
            project_id=project_id
        )

        # Guardar nodos, enlaces, parametros y configuracion EPD en parameters_json
        save_system_canvas(c, sys_id, tpl["nodes"], tpl["edges"])

        cur = c.execute("SELECT parameters_json FROM product_systems WHERE id = ?;", (sys_id,))
        row = cur.fetchone()
        pj = {}
        if row and row[0]:
            try:
                pj = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
            except Exception:
                pj = {}

        pj["parameters"] = tpl.get("parameters", [])
        pj["epd_config"] = epd_config
        pj["unit_symbol"] = tpl["declared_unit_symbol"]

        with c:
            c.execute(
                "UPDATE product_systems SET parameters_json = ? WHERE id = ?;",
                (json.dumps(pj, ensure_ascii=False), sys_id)
            )
        return sys_id

    if conn is None:
        with get_active_db_connection() as c:
            sys_id = _execute(c)
    else:
        sys_id = _execute(conn)

    return {
        "status": "success",
        "system_id": sys_id,
        "template_id": template_id,
        "name": custom_name,
        "code": custom_code,
        "system_boundary": tpl["system_boundary"],
        "declared_modules": tpl["declared_modules"],
        "epd_config": epd_config,
        "message": f"Modelo preliminar EPD '{custom_name}' creado exitosamente con {len(tpl['nodes'])} modulos conectados."
    }


# =============================================================================
# MOTOR DE CARACTERIZACION MODULAR EPD (EN 15804+A2 / TRACI 2.1 + RECURSOS)
# =============================================================================
def _zero_impact_bucket() -> Dict[str, float]:
    return {
        # EN 15804+A2 Core Impacts
        "gwp_total": 0.0,
        "gwp_fossil": 0.0,
        "gwp_biogenic": 0.0,
        "gwp_luluc": 0.0,
        "odp": 0.0,
        "ap": 0.0,
        "ep_freshwater": 0.0,
        "ep_marine": 0.0,
        "ep_terrestrial": 0.0,
        "pocp": 0.0,
        "adp_minerals": 0.0,
        "adp_fossil": 0.0,
        "wdp": 0.0,
        # TRACI 2.1 Specifics
        "ap_traci": 0.0,
        "ep_traci": 0.0,
        "sfp": 0.0,
        "ffd": 0.0,
        # Resource Use
        "pere": 0.0,
        "perm": 0.0,
        "pert": 0.0,
        "penre": 0.0,
        "penrm": 0.0,
        "penrt": 0.0,
        "sm": 0.0,
        "rsf": 0.0,
        "nrsf": 0.0,
        "fw": 0.0,
        # Waste & Output Flows
        "hwd": 0.0,
        "nhwd": 0.0,
        "rwd": 0.0,
        "cru": 0.0,
        "mfr": 0.0,
        "mer": 0.0,
        "ee": 0.0,
    }


def _accumulate_flow(bucket: Dict[str, float], name_raw: str, amount: float, unit_raw: str, is_output: bool = False, is_waste: bool = False, is_elementary: bool = False, epd_output_flow: str = ""):
    """Caracteriza un intercambio tecnosferico o elemental en las categorias EN 15804+A2, TRACI 2.1, Recursos y Residuos."""
    name = (name_raw or "").lower()
    unit = (unit_raw or "").lower().strip()

    if abs(amount) < 1e-12:
        return

    # 1. Salidas de residuos y flujos de salida (Waste & Output Flows)
    if is_output:
        if epd_output_flow == "mfr" or "for recycling" in name or "(mfr)" in name:
            bucket["mfr"] += max(0.0, amount)
            return
        if epd_output_flow == "cru":
            bucket["cru"] += max(0.0, amount)
            return
        if epd_output_flow == "mer":
            bucket["mer"] += max(0.0, amount)
            return
        if is_waste:
            if "hazardous" in name and "non-hazardous" not in name and "no peligroso" not in name:
                bucket["hwd"] += max(0.0, amount)
            elif "radioactive" in name:
                bucket["rwd"] += max(0.0, amount)
            else:
                bucket["nhwd"] += max(0.0, amount)
            return

        # Emisiones directas a aire / agua (ej. calcinacion en horno cementero)
        if is_elementary or any(k in name for k in ("carbon dioxide", "co2", "nitrogen oxides", "nox", "sulfur dioxide", "so2", "methane")):
            if "biogenic" in name:
                bucket["gwp_biogenic"] += amount * 1.0
                bucket["gwp_total"] += amount * 1.0
            elif "carbon dioxide" in name or "co2" in name:
                bucket["gwp_fossil"] += amount * 1.0
                bucket["gwp_total"] += amount * 1.0
            elif "methane" in name or "ch4" in name:
                bucket["gwp_fossil"] += amount * 29.8
                bucket["gwp_total"] += amount * 29.8
                bucket["pocp"] += amount * 0.0101
                bucket["sfp"] += amount * 0.014
            elif "nitrogen oxides" in name or "nox" in name:
                bucket["ap"] += amount * 0.74
                bucket["ap_traci"] += amount * 0.70
                bucket["ep_marine"] += amount * 0.39
                bucket["ep_terrestrial"] += amount * 4.26
                bucket["ep_traci"] += amount * 0.044
                bucket["pocp"] += amount * 1.0
                bucket["sfp"] += amount * 24.8
            elif "sulfur dioxide" in name or "so2" in name:
                bucket["ap"] += amount * 1.31
                bucket["ap_traci"] += amount * 1.0
                bucket["pocp"] += amount * 0.081
                bucket["sfp"] += amount * 0.0
            return
        return

    # 2. Entradas tecnosfericas (Materiales de construccion, energia, combustibles, transporte)
    def _add(gwp_f=0.0, gwp_b=0.0, luluc=0.0, odp=0.0, ap=0.0, ep_fw=0.0, ep_m=0.0, ep_t=0.0, pocp=0.0, adp_m=0.0, adp_f=0.0, wdp=0.0, pere=0.0, sm=0.0, fw=0.0):
        bucket["gwp_fossil"] += amount * gwp_f
        bucket["gwp_biogenic"] += amount * gwp_b
        bucket["gwp_luluc"] += amount * luluc
        bucket["gwp_total"] += amount * (gwp_f + gwp_b + luluc)
        bucket["odp"] += amount * odp
        bucket["ap"] += amount * ap
        bucket["ap_traci"] += amount * (ap * 0.76)
        bucket["ep_freshwater"] += amount * ep_fw
        bucket["ep_marine"] += amount * ep_m
        bucket["ep_terrestrial"] += amount * ep_t
        bucket["ep_traci"] += amount * (ep_m * 0.65 + ep_fw * 7.29)
        bucket["pocp"] += amount * pocp
        bucket["sfp"] += amount * (pocp * 18.5)
        bucket["adp_minerals"] += amount * adp_m
        bucket["adp_fossil"] += amount * adp_f
        bucket["ffd"] += amount * (adp_f * 0.125)
        bucket["wdp"] += amount * wdp
        bucket["pere"] += amount * pere
        bucket["penre"] += amount * adp_f
        bucket["sm"] += max(0.0, amount * sm)
        bucket["fw"] += amount * fw

    # Cemento Portland (como insumo en A1 de concreto)
    if ("portland cement" in name or "cemento portland" in name or "cem i" in name) and "clinker" not in name:
        _add(gwp_f=0.855, luluc=0.0004, odp=1.8e-8, ap=0.0021, ep_fw=0.00008, ep_m=0.00058, ep_t=0.0064, pocp=0.0016, adp_m=2.1e-6, adp_f=3.85, wdp=0.045, pere=0.35, fw=0.0012)
    elif "clinker" in name:
        _add(gwp_f=0.910, luluc=0.0004, odp=1.9e-8, ap=0.0023, ep_fw=0.000085, ep_m=0.00062, ep_t=0.0068, pocp=0.0017, adp_m=2.2e-6, adp_f=4.10, wdp=0.048, pere=0.32, fw=0.0013)
    # Materiales Cementantes Suplementarios (SCMs - Secundarios)
    elif "ggbfs" in name or "blast furnace slag" in name or "escoria" in name:
        _add(gwp_f=0.075, odp=2.5e-9, ap=0.00025, ep_fw=0.000012, ep_m=0.00008, ep_t=0.00085, pocp=0.00022, adp_m=4.0e-7, adp_f=0.92, wdp=0.012, pere=0.14, sm=1.0, fw=0.0004)
    elif "fly ash" in name or "pozzolan" in name or "ceniza volante" in name or "puzolana" in name:
        _add(gwp_f=0.025, odp=1.1e-9, ap=0.00009, ep_fw=0.000005, ep_m=0.00003, ep_t=0.00032, pocp=0.00008, adp_m=1.5e-7, adp_f=0.34, wdp=0.004, pere=0.06, sm=1.0, fw=0.00015)
    # Minerales y Agregados
    elif "avoided virgin gravel" in name or "credit (module d)" in name:
        _add(gwp_f=0.0052, odp=4.2e-10, ap=0.000026, ep_fw=0.0000012, ep_m=0.000009, ep_t=0.000095, pocp=0.000024, adp_m=1.2e-7, adp_f=0.082, wdp=0.003, pere=0.009, fw=0.00008)
    elif "gravel" in name or "grava" in name or "crushed aggregate" in name:
        _add(gwp_f=0.0052, odp=4.2e-10, ap=0.000026, ep_fw=0.0000012, ep_m=0.000009, ep_t=0.000095, pocp=0.000024, adp_m=1.2e-7, adp_f=0.082, wdp=0.003, pere=0.009, fw=0.00008)
    elif "sand" in name or "arena" in name:
        _add(gwp_f=0.0041, odp=3.4e-10, ap=0.000021, ep_fw=0.0000010, ep_m=0.000007, ep_t=0.000078, pocp=0.000019, adp_m=1.0e-7, adp_f=0.068, wdp=0.0025, pere=0.007, fw=0.00006)
    elif "limestone" in name or "caliza" in name:
        _add(gwp_f=0.0065, odp=5.0e-10, ap=0.000032, ep_fw=0.0000014, ep_m=0.000011, ep_t=0.00012, pocp=0.000028, adp_m=1.5e-7, adp_f=0.095, wdp=0.0035, pere=0.011, fw=0.00009)
    elif "clay" in name or "arcilla" in name:
        _add(gwp_f=0.0080, odp=5.5e-10, ap=0.000038, ep_fw=0.0000016, ep_m=0.000012, ep_t=0.00013, pocp=0.000032, adp_m=1.8e-7, adp_f=0.115, wdp=0.004, pere=0.012, fw=0.00010)
    elif "gypsum" in name or "yeso" in name:
        _add(gwp_f=0.0055, odp=4.0e-10, ap=0.000024, ep_fw=0.0000011, ep_m=0.000008, ep_t=0.000088, pocp=0.000021, adp_m=1.1e-7, adp_f=0.078, wdp=0.0028, pere=0.008, fw=0.00007)
    elif "iron ore" in name or "corrective mineral" in name:
        _add(gwp_f=0.055, odp=2.1e-9, ap=0.00022, ep_fw=0.000012, ep_m=0.000065, ep_t=0.00072, pocp=0.00018, adp_m=2.4e-5, adp_f=0.72, wdp=0.015, pere=0.04, fw=0.00035)
    # Aditivos quimicos
    elif "admixture" in name or "plasticizer" in name or "aditivo" in name:
        _add(gwp_f=1.65, odp=8.2e-8, ap=0.0078, ep_fw=0.00042, ep_m=0.0014, ep_t=0.015, pocp=0.0052, adp_m=1.4e-5, adp_f=32.0, wdp=0.85, pere=1.2, fw=0.022)
    # Combustibles y Energia
    elif "petcoke" in name or "petroleum coke" in name or "coque" in name:
        _add(gwp_f=3.45, odp=1.4e-7, ap=0.022, ep_fw=0.00015, ep_m=0.0012, ep_t=0.013, pocp=0.0048, adp_m=4.5e-6, adp_f=35.0, wdp=0.09, pere=0.15, fw=0.0025)
    elif "natural gas" in name or "gas natural" in name:
        _add(gwp_f=2.02, odp=4.5e-8, ap=0.0028, ep_fw=0.00004, ep_m=0.00035, ep_t=0.0038, pocp=0.0014, adp_m=1.2e-6, adp_f=38.0, wdp=0.04, pere=0.08, fw=0.0011)
    elif "diesel" in name or "gasoil" in name:
        _add(gwp_f=3.15, odp=2.2e-7, ap=0.0115, ep_fw=0.00009, ep_m=0.0028, ep_t=0.031, pocp=0.0085, adp_m=3.1e-6, adp_f=42.5, wdp=0.075, pere=0.22, fw=0.0020)
    elif "electricity" in name or "electricidad" in name or "cfe" in name:
        _add(gwp_f=0.438, odp=1.8e-8, ap=0.0016, ep_fw=0.000045, ep_m=0.00032, ep_t=0.0035, pocp=0.00095, adp_m=1.8e-6, adp_f=7.8, wdp=0.065, pere=1.42, fw=0.0018)
    # Transporte
    elif "transit mixer" in name or "camion olla" in name:
        _add(gwp_f=0.125, odp=1.5e-8, ap=0.00048, ep_fw=0.000008, ep_m=0.00014, ep_t=0.0015, pocp=0.00039, adp_m=4.2e-7, adp_f=1.85, wdp=0.006, pere=0.035, fw=0.00018)
    elif "transport" in name or "freight" in name or "lorry" in name or "truck" in name or "camion" in name:
        _add(gwp_f=0.098, odp=1.2e-8, ap=0.00038, ep_fw=0.000006, ep_m=0.00011, ep_t=0.0012, pocp=0.00031, adp_m=3.4e-7, adp_f=1.45, wdp=0.005, pere=0.028, fw=0.00014)
    # Agua
    elif "water" in name or "agua" in name:
        vol_m3 = 1.0 if "m3" in unit else 0.001
        _add(gwp_f=0.35 * vol_m3, odp=1.2e-8 * vol_m3, ap=0.0011 * vol_m3, ep_fw=0.00006 * vol_m3, adp_f=4.2 * vol_m3, wdp=1.0 * vol_m3, pere=0.45 * vol_m3, fw=1.0 * vol_m3)
    # Disposicion en relleno inerte
    elif "landfill" in name or "relleno" in name:
        _add(gwp_f=0.0085, odp=6.0e-10, ap=0.000042, ep_fw=0.000002, ep_m=0.000015, ep_t=0.00016, pocp=0.000038, adp_m=8.0e-8, adp_f=0.12, wdp=0.004, pere=0.008, fw=0.0001)
    # Polimeros (compatibilidad con modelos existentes de PET / envases en ECONODE)
    elif "virgin pet" in name or "pet granulate" in name:
        _add(gwp_f=2.15, odp=1.1e-7, ap=0.0065, ep_fw=0.00025, ep_m=0.0011, ep_t=0.012, pocp=0.0048, adp_m=8.5e-6, adp_f=72.0, wdp=0.55, pere=1.8, fw=0.018)
    elif "recycled pet" in name or "rpet" in name:
        _add(gwp_f=0.65, odp=3.2e-8, ap=0.0022, ep_fw=0.00009, ep_m=0.00038, ep_t=0.0041, pocp=0.0015, adp_m=2.1e-6, adp_f=18.5, wdp=0.18, pere=0.95, sm=1.0, fw=0.006)


def _infer_node_epd_module(node: Dict[str, Any], idx: int, total_nodes: int) -> str:
    """Obtiene el modulo EPD explicito del nodo o lo infiere de su nombre/codigo si es un modelo libre."""
    explicit = (node.get("epd_module") or "").strip().upper()
    if explicit in EPD_MODULE_CODES:
        return explicit

    text = f"{node.get('code', '')} {node.get('name', '')} {node.get('category', '')}".upper()
    for code in ("A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "C1", "C2", "C3", "C4"):
        if f"{code}:" in text or f" {code} " in text or text.startswith(f"{code} ") or f"-{code}" in text:
            return code

    low = text.lower()
    if any(k in low for k in ("distribu", "transport", "freight", "logistica", "flete", "camion")):
        return "A4" if idx == total_nodes - 1 and total_nodes >= 3 else "A2"
    if any(k in low for k in ("raw", "extracc", "materia prima", "suministro", "quarr", "cemento", "agregado")):
        return "A1"
    if any(k in low for k in ("demolic", "disposal", "landfill", "relleno")):
        return "C4"
    if any(k in low for k in ("recicl", "triturac", "crush")):
        return "C3"
    return "A3"


def _round_indicator(val: float, key: str) -> float:
    if abs(val) < 1e-12:
        return 0.0
    if key in ("odp", "adp_minerals", "ep_freshwater"):
        return float(f"{val:.4e}")
    if abs(val) < 0.01:
        return round(val, 6)
    if abs(val) < 1.0:
        return round(val, 4)
    return round(val, 2)


def compute_epd_report_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1,
    standard: str = "EN15804_A2"
) -> Dict[str, Any]:
    """Calcula y estructura el reporte EPD completo por modulos A1-D (EN 15804+A2 o TRACI 2.1)."""
    std = (standard or "EN15804_A2").upper()
    if std not in ("EN15804_A2", "TRACI_2_1"):
        std = "EN15804_A2"

    def _execute(c: sqlite3.Connection):
        details = get_product_system_details(c, system_id)
        if not details:
            raise ValueError(f"Sistema producto {system_id} no encontrado.")

        # Recuperar epd_config de parameters_json si existe
        cur = c.execute("SELECT parameters_json, category, geography, status FROM product_systems WHERE id = ?;", (system_id,))
        row = cur.fetchone()
        raw_pj = row[0] if row else "{}"
        cat = row[1] if row and len(row) > 1 else "Construccion & Edificacion"
        geo = row[2] if row and len(row) > 2 else "[MX]"
        status = row[3] if row and len(row) > 3 else "draft"

        parsed_pj = {}
        try:
            parsed_pj = json.loads(raw_pj) if isinstance(raw_pj, str) else (raw_pj or {})
        except Exception:
            parsed_pj = {}

        epd_config = parsed_pj.get("epd_config")
        if not isinstance(epd_config, dict):
            unit_sym = parsed_pj.get("unit_symbol") or "u"
            epd_config = get_default_epd_config(
                system_name=details["name"],
                declared_unit=f"{details.get('target_amount', 1.0)} {unit_sym}",
                org_name=details.get("owner_org") or "ECONODE Industrial",
                geography=geo
            )

        nodes = details.get("nodes") or []
        target_amt = float(details.get("target_amount") or 1.0)

        # Agrupar resultados por modulo EPD
        module_buckets: Dict[str, Dict[str, float]] = {}
        module_nodes_map: Dict[str, List[str]] = {}
        active_modules_set = set()

        for idx, n in enumerate(nodes):
            mod = _infer_node_epd_module(n, idx, len(nodes))
            active_modules_set.add(mod)
            if mod not in module_buckets:
                module_buckets[mod] = _zero_impact_bucket()
                module_nodes_map[mod] = []
            module_nodes_map[mod].append(n.get("name") or f"Proceso {idx + 1}")

            for inp in (n.get("inputs") or []):
                if inp.get("is_unit"):
                    continue  # Flujo interno conectado desde nodo previo; evita doble conteo
                amt = float(inp.get("amount") or 0.0) * target_amt
                _accumulate_flow(module_buckets[mod], inp.get("name", ""), amt, inp.get("unit", ""), is_output=False)

            for out in (n.get("outputs") or []):
                if out.get("is_reference"):
                    continue
                amt = float(out.get("amount") or 0.0) * target_amt
                _accumulate_flow(
                    module_buckets[mod],
                    out.get("name", ""),
                    amt,
                    out.get("unit", ""),
                    is_output=True,
                    is_waste=bool(out.get("is_waste")),
                    is_elementary=bool(out.get("is_elementary")),
                    epd_output_flow=str(out.get("epd_output_flow") or "")
                )

        # Calcular PERT y PENRT en cada modulo
        for mod, b in module_buckets.items():
            b["pert"] = b["pere"] + b["perm"]
            b["penrt"] = b["penre"] + b["penrm"]

        # Orden canonico de modulos activos
        declared_modules = [m for m in EPD_MODULE_CODES if m in active_modules_set]
        if not declared_modules:
            declared_modules = list(epd_config.get("declared_modules") or ["A1", "A2", "A3"])

        # Construir matriz de limites A1-D (X = Declarado, MND = No Declarado)
        boundary_matrix = []
        for m_def in EPD_MODULES:
            code = m_def["code"]
            is_decl = code in active_modules_set
            boundary_matrix.append({
                "code": code,
                "stage": m_def["stage"],
                "stage_es": m_def["stage_es"],
                "stage_en": m_def["stage_en"],
                "name_es": m_def["name_es"],
                "name_en": m_def["name_en"],
                "status": "X" if is_decl else "MND",
                "is_declared": is_decl,
                "processes": module_nodes_map.get(code, [])
            })

        # Seleccionar lista de indicadores segun estandar
        impact_defs = EPD_INDICATORS_EN15804_A2 if std == "EN15804_A2" else EPD_INDICATORS_TRACI_2_1

        def _build_table(indicator_defs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
            rows_out = []
            for ind in indicator_defs:
                key = ind["key"]
                per_mod = {}
                a1_a3_sum = 0.0
                total_all = 0.0
                for mod in declared_modules:
                    raw_v = module_buckets.get(mod, {}).get(key, 0.0)
                    per_mod[mod] = _round_indicator(raw_v, key)
                    if mod in ("A1", "A2", "A3"):
                        a1_a3_sum += raw_v
                    if mod != "D":
                        total_all += raw_v
                rows_out.append({
                    "key": key,
                    "code": ind["code"],
                    "name_es": ind["name_es"],
                    "name_en": ind["name_en"],
                    "unit": ind["unit"],
                    "modules": per_mod,
                    "total_a1_a3": _round_indicator(a1_a3_sum, key),
                    "total_declared": _round_indicator(total_all, key)
                })
            return rows_out

        impact_table = _build_table(impact_defs)
        resource_table = _build_table(EPD_RESOURCE_INDICATORS)
        waste_table = _build_table(EPD_WASTE_OUTPUT_INDICATORS)

        # Desglose porcentual de GWP por modulo para grafico de barras horizontales
        gwp_row = next((r for r in impact_table if r["key"] == "gwp_total"), None)
        gwp_breakdown = []
        if gwp_row:
            positive_sum = sum(max(0.0, float(gwp_row["modules"].get(m, 0.0))) for m in declared_modules if m != "D")
            for m in declared_modules:
                v = float(gwp_row["modules"].get(m, 0.0))
                pct = round((v / positive_sum) * 100.0, 1) if positive_sum > 0 else 0.0
                m_info = next((x for x in EPD_MODULES if x["code"] == m), {})
                gwp_breakdown.append({
                    "module": m,
                    "name_es": m_info.get("name_es", m),
                    "name_en": m_info.get("name_en", m),
                    "gwp_kg_co2e": round(v, 2),
                    "share_pct": pct
                })

        return {
            "status": "success",
            "system_id": system_id,
            "system_name": details["name"],
            "system_code": details["code"],
            "system_status": status,
            "category": cat,
            "geography": geo,
            "standard": std,
            "standard_label": "EN 15804:2012+A2:2019 (EF 3.1)" if std == "EN15804_A2" else "TRACI 2.1 / ISO 21930 (SmartEPD North America)",
            "epd_config": epd_config,
            "declared_modules": declared_modules,
            "boundary_matrix": boundary_matrix,
            "impact_results": impact_table,
            "resource_use": resource_table,
            "waste_and_outputs": waste_table,
            "gwp_breakdown": gwp_breakdown,
            "summary_kpis": {
                "gwp_a1_a3": gwp_row["total_a1_a3"] if gwp_row else 0.0,
                "gwp_total_lifecycle": gwp_row["total_declared"] if gwp_row else 0.0,
                "gwp_module_d": gwp_row["modules"].get("D", 0.0) if gwp_row else 0.0,
                "declared_modules_count": len(declared_modules),
                "secondary_materials_kg": next((r["total_declared"] for r in resource_table if r["key"] == "sm"), 0.0),
                "fresh_water_m3": next((r["total_declared"] for r in resource_table if r["key"] == "fw"), 0.0)
            }
        }

    if conn is None:
        with get_active_db_connection() as c:
            return _execute(c)
    return _execute(conn)


def save_epd_metadata_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1,
    epd_updates: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Actualiza y persiste la configuracion administrativa EPD en parameters_json."""
    epd_updates = epd_updates or {}

    def _execute(c: sqlite3.Connection):
        ensure_product_systems_columns(c)
        cur = c.execute("SELECT name, target_amount, owner_org, geography, parameters_json FROM product_systems WHERE id = ?;", (system_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Sistema producto {system_id} no encontrado.")

        raw_pj = row[4] if len(row) > 4 else "{}"
        parsed_pj = {}
        try:
            parsed_pj = json.loads(raw_pj) if isinstance(raw_pj, str) else (raw_pj or {})
        except Exception:
            parsed_pj = {}

        existing = parsed_pj.get("epd_config")
        if not isinstance(existing, dict):
            existing = get_default_epd_config(
                system_name=row[0],
                declared_unit=f"{row[1] or 1.0} u",
                org_name=row[2] or "ECONODE Industrial",
                geography=row[3] or "[MX]"
            )

        for k, v in epd_updates.items():
            if v is not None:
                existing[k] = v

        existing["is_epd_enabled"] = True
        parsed_pj["epd_config"] = existing

        with c:
            c.execute(
                "UPDATE product_systems SET parameters_json = ? WHERE id = ?;",
                (json.dumps(parsed_pj, ensure_ascii=False), system_id)
            )
        return existing

    if conn is None:
        with get_active_db_connection() as c:
            saved = _execute(c)
    else:
        saved = _execute(conn)

    return {
        "status": "success",
        "system_id": system_id,
        "epd_config": saved,
        "message": "Metadatos de la Declaracion Ambiental de Producto (EPD) guardados exitosamente."
    }


def export_openepd_json_use_case(
    conn: Optional[sqlite3.Connection] = None,
    system_id: int = 1
) -> Dict[str, Any]:
    """Exporta la EPD en formato digital estructurado openEPD (compatible con SmartEPD / BuildingTransparency EC3)."""
    rep_en = compute_epd_report_use_case(conn, system_id, standard="EN15804_A2")
    rep_traci = compute_epd_report_use_case(conn, system_id, standard="TRACI_2_1")
    cfg = rep_en["epd_config"]

    def _map_impacts(table: List[Dict[str, Any]]) -> Dict[str, Any]:
        out = {}
        for row in table:
            mod_dict = {}
            for m, val in row["modules"].items():
                mod_dict[m] = {"mean": val, "unit": row["unit"]}
            mod_dict["A1A2A3"] = {"mean": row["total_a1_a3"], "unit": row["unit"]}
            out[row["key"]] = mod_dict
        return out

    return {
        "doctype": "openEPD",
        "openepd_version": "0.1",
        "id": cfg.get("declaration_number", f"ECONODE-EPD-{system_id}"),
        "language": "es",
        "date_of_issue": cfg.get("issue_date", datetime.date.today().isoformat()),
        "valid_until": cfg.get("valid_until", "2031-11-17"),
        "name": cfg.get("product_name", rep_en["system_name"]),
        "product_classes": {
            "UN_CPC": cfg.get("un_cpc", "N/A"),
            "ECONODE_Industry": cfg.get("industry_id", "cement_concrete")
        },
        "declared_unit": {
            "qty": cfg.get("declared_unit_amount", 1.0),
            "unit": cfg.get("declared_unit_symbol", "u"),
            "description": cfg.get("declared_unit", "")
        },
        "program_operator": {
            "name": cfg.get("program_operator", "Smart EPD (Compatible Draft)"),
            "web_domain": "smartepd.com"
        },
        "pcr": {
            "name": cfg.get("pcr_reference", ""),
            "standards": cfg.get("standards", "ISO 14025, ISO 21930, EN 15804+A2")
        },
        "manufacturer": {
            "name": cfg.get("declaration_holder", ""),
            "plant": cfg.get("plant_location", "")
        },
        "third_party_verifier": {
            "verification_type": cfg.get("verification_type", ""),
            "verifier": cfg.get("verifier_name", "")
        },
        "system_boundary": cfg.get("system_boundary", "Cradle-to-Gate (A1-A3)"),
        "declared_modules": rep_en["declared_modules"],
        "specs": cfg.get("technical_specs", {}),
        "composition": cfg.get("composition", []),
        "impacts": {
            "EN15804_A2": _map_impacts(rep_en["impact_results"]),
            "TRACI_2_1": _map_impacts(rep_traci["impact_results"])
        },
        "resource_uses": _map_impacts(rep_en["resource_use"]),
        "output_flows": _map_impacts(rep_en["waste_and_outputs"]),
        "comparability_statement": cfg.get("comparability_statement_en", "")
    }
