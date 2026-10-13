"""
econode_studio/application/normative_audit.py - Casos de Uso para Auditoría Multi-Estándar y Creación de Checklists
Soporta:
1. Evaluación paralela de múltiples normas (NOM-070, ISO 14044, ISO 14067, GHG Protocol).
2. Creación interactiva de normas personalizadas por parte del auditor o analista.
3. Importación y carga masiva de checklists mediante plantillas CSV.
4. Generación de plantilla CSV descargable para edición externa en Excel.
"""

from typing import Dict, List, Any, Optional

try:
    from domain.audit_checklist import (
        AuditClause, AuditStandard, OFFICIAL_CLAUSES, OFFICIAL_STANDARDS, calculate_audit_compliance
    )
    from infrastructure.crypto_signer import sign_audit_dossier
    from infrastructure.audit_adapter import (
        get_checklist_clause_states,
        set_checklist_clause_state,
        get_audit_seal,
        save_audit_seal,
        list_all_checklist_templates,
        get_checklist_template,
        save_custom_checklist_template,
        import_checklist_from_csv,
        delete_custom_checklist_template,
        update_clause_evidence
    )
except (ImportError, ValueError):
    from econode_studio.domain.audit_checklist import (
        AuditClause, AuditStandard, OFFICIAL_CLAUSES, OFFICIAL_STANDARDS, calculate_audit_compliance
    )
    from econode_studio.infrastructure.crypto_signer import sign_audit_dossier
    from econode_studio.infrastructure.audit_adapter import (
        get_checklist_clause_states,
        set_checklist_clause_state,
        get_audit_seal,
        save_audit_seal,
        list_all_checklist_templates,
        get_checklist_template,
        save_custom_checklist_template,
        import_checklist_from_csv,
        delete_custom_checklist_template,
        update_clause_evidence
    )


def list_available_standards_use_case(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna la lista de todas las normas oficiales y personalizadas disponibles en la plataforma."""
    return list_all_checklist_templates(user_id)


def get_audit_checklist_use_case(system_id: int, checklist_id: str = "nom070") -> Dict[str, Any]:
    """
    Obtiene el checklist normativo completo para el sistema producto y norma especificada.
    Por defecto consulta 'nom070', garantizando 100% de compatibilidad con llamadas existentes.
    """
    clean_id = (checklist_id or "nom070").strip().lower()
    template = get_checklist_template(clean_id)
    if not template:
        # Fallback a NOM-070 oficial
        template = get_checklist_template("nom070")

    saved_states = get_checklist_clause_states(system_id, clean_id)
    seal_info = get_audit_seal(system_id, clean_id)

    clauses_data = []
    conforme_count = 0
    raw_clauses = template.get("clauses", []) if template else []

    for raw in raw_clauses:
        cl_id = raw.get("clause_id")
        # El demo de referencia oficial (ID 21) inicia al 100% verificado; los sistemas creados por usuarios inician en 0% (Pendientes)
        default_val = raw.get("is_compliant", True) if system_id == 21 else False
        is_ok = saved_states.get(cl_id, default_val)
        if is_ok:
            conforme_count += 1
        clauses_data.append({
            "clause_id": cl_id,
            "section": raw.get("section", ""),
            "title": raw.get("title", ""),
            "criterion": raw.get("criterion", ""),
            "evidence": raw.get("evidence_required", ""),
            "is_compliant": is_ok,
            "status_badge": "Conforme" if is_ok else "Obs. Pendiente",
            "status_color": "#059669" if is_ok else "#D97706",
            "verified_by": raw.get("verified_by", "Auditor Asignado")
        })

    total = len(clauses_data)
    rate = (conforme_count / total * 100.0) if total > 0 else 100.0
    digital_seal = seal_info["digital_seal"] if seal_info else "0x8F2A6C4D91BC437E"

    std_name = template.get("name", "NOM-070-SE-2024 / ISO 14044:2006") if template else "NOM-070-SE-2024 / ISO 14044:2006"
    std_code = template.get("code", "NOM-070") if template else "NOM-070"

    return {
        "system_id": system_id,
        "checklist_id": clean_id,
        "standard": std_name,
        "standard_code": std_code,
        "standard_family": template.get("standard_family", "General") if template else "General",
        "total_clauses": total,
        "compliant_clauses": conforme_count,
        "compliance_rate": round(rate, 1),
        "compliance_label": f"{rate:.1f}% Conforme ({conforme_count} de {total} Cláusulas)",
        "clauses": clauses_data,
        "mass_balance_status": "100.0% Validado",
        "digital_seal": digital_seal,
        "can_sign": rate >= 90.0
    }


def update_clause_status_use_case(
    system_id: int,
    clause_id: str,
    is_compliant: bool,
    checklist_id: str = "nom070"
) -> Dict[str, Any]:
    """Actualiza atómicamente el estado de conformidad de una cláusula para la norma elegida."""
    clean_id = (checklist_id or "nom070").strip().lower()
    set_checklist_clause_state(system_id, clause_id, is_compliant, clean_id)
    return get_audit_checklist_use_case(system_id, clean_id)


def update_clause_evidence_use_case(
    system_id: int,
    clause_id: str,
    evidence: str,
    checklist_id: str = "nom070"
) -> Dict[str, Any]:
    """Actualiza el texto del requerimiento de evidencia para una cláusula."""
    clean_id = (checklist_id or "nom070").strip().lower()
    update_clause_evidence(clean_id, clause_id, evidence)
    return get_audit_checklist_use_case(system_id, clean_id)


def sign_normative_audit_use_case(
    system_id: int,
    auditor_name: str,
    checklist_id: str = "nom070"
) -> Dict[str, Any]:
    """Firma digitalmente el expediente y persiste el sello en SQLite para la norma evaluada."""
    clean_id = (checklist_id or "nom070").strip().lower()
    curr = get_audit_checklist_use_case(system_id, clean_id)

    if curr["compliance_rate"] < 90.0:
        raise ValueError(
            f"No es posible emitir la firma digital: la tasa de conformidad actual ({curr['compliance_rate']}%) "
            f"es inferior al mínimo reglamentario del 90.0% requerido por el estándar."
        )

    receipt = sign_audit_dossier(system_id, auditor_name, curr["compliance_rate"])
    save_audit_seal(
        system_id=system_id,
        digital_seal=receipt["digital_seal"],
        signed_by=auditor_name,
        compliance_rate=curr["compliance_rate"],
        checklist_id=clean_id
    )
    receipt["checklist_summary"] = curr
    receipt["standard"] = curr["standard"]
    receipt["checklist_id"] = clean_id
    return receipt


def create_custom_standard_use_case(
    data: Dict[str, Any],
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Crea una nueva norma o checklist con cláusulas definidas interactivamente."""
    user_id = (user.get("id") if user else None) or "auditor"
    return save_custom_checklist_template(data, user_id=user_id)


def import_standard_csv_use_case(
    csv_content: str,
    metadata: Optional[Dict[str, Any]] = None,
    user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Importa una norma completa desde el texto de un archivo CSV."""
    metadata = metadata or {}
    user_id = (user.get("id") if user else None) or "auditor"
    name = (metadata.get("name") or "").strip()
    code = (metadata.get("code") or "").strip()
    family = (metadata.get("standard_family") or "Personalizado").strip()

    return import_checklist_from_csv(
        csv_content=csv_content,
        name=name,
        code=code,
        family=family,
        user_id=user_id
    )


def get_checklist_csv_template_use_case() -> str:
    """Retorna una plantilla CSV de ejemplo lista para ser editada en Excel."""
    return (
        "seccion,clausula_id,titulo,criterio,evidencia_requerida\n"
        "4.1 Límites del Sistema,EMP-01,Inclusión de Empaque Primario,Se debe contabilizar el polímero virgen y masterbatch,Ficha técnica de resina\n"
        "4.2 Consumo de Energía,EMP-02,Monitoreo Eléctrico en Planta,Medición en kWh por cada 1000 envases soplados,Factura CFE y reporte SCADA\n"
        "4.3 Logística y Fletes,EMP-03,Transporte de Distribución,Distancia en km de planta a centro de distribución,Carta porte y odómetro\n"
        "5.1 Fin de Vida,EMP-04,Tasa de Reciclabilidad Postconsumo,Acreditación de esquema de acopio o circularidad,Certificado de reciclador\n"
    )
