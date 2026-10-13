"""
econode_studio/domain/audit_checklist.py - Entidad de Dominio para Auditoría Normativa Multi-Estándar
Estructura las cláusulas de auditoría y plantillas de normas (NOM-070, ISO 14044, ISO 14067, GHG Protocol y personalizadas).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set


@dataclass
class AuditClause:
    clause_id: str
    section: str
    title: str
    criterion: str
    evidence_required: str
    is_compliant: bool = True
    auditor_notes: str = ""
    verified_by: str = "Josué Rentería"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "section": self.section,
            "title": self.title,
            "criterion": self.criterion,
            "evidence_required": self.evidence_required,
            "is_compliant": self.is_compliant,
            "status_badge": "Conforme" if self.is_compliant else "Obs. Pendiente",
            "status_color": "#059669" if self.is_compliant else "#D97706",
            "auditor_notes": self.auditor_notes,
            "verified_by": self.verified_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditClause":
        return cls(
            clause_id=str(data.get("clause_id") or ""),
            section=str(data.get("section") or ""),
            title=str(data.get("title") or ""),
            criterion=str(data.get("criterion") or ""),
            evidence_required=str(data.get("evidence_required") or data.get("evidence") or ""),
            is_compliant=bool(data.get("is_compliant", True)),
            auditor_notes=str(data.get("auditor_notes") or ""),
            verified_by=str(data.get("verified_by") or "Josué Rentería")
        )


@dataclass
class AuditStandard:
    id: str
    name: str
    code: str
    standard_family: str
    description: str
    version: str = "1.0"
    is_official: bool = True
    created_by: str = "system"
    clauses: List[AuditClause] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "standard_family": self.standard_family,
            "description": self.description,
            "version": self.version,
            "is_official": self.is_official,
            "created_by": self.created_by,
            "total_clauses": len(self.clauses),
            "clauses": [c.to_dict() for c in self.clauses]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditStandard":
        clauses = [AuditClause.from_dict(c) for c in data.get("clauses", [])]
        return cls(
            id=str(data.get("id") or ""),
            name=str(data.get("name") or "Norma Personalizada"),
            code=str(data.get("code") or "STD-CUSTOM"),
            standard_family=str(data.get("standard_family") or "Personalizado"),
            description=str(data.get("description") or ""),
            version=str(data.get("version") or "1.0"),
            is_official=bool(data.get("is_official", False)),
            created_by=str(data.get("created_by") or "user"),
            clauses=clauses
        )


def calculate_audit_compliance(
    clauses: Any,
    override_states: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """Calcula el porcentaje de conformidad global y estadísticas normativas."""
    if hasattr(clauses, "clauses"):
        clauses = clauses.clauses
    override_states = override_states or {}
    total = len(clauses)
    compliant_count = 0

    evaluated_clauses = []
    for c in clauses:
        is_ok = override_states.get(c.clause_id, c.is_compliant)
        if is_ok:
            compliant_count += 1
        d = c.to_dict()
        d["is_compliant"] = is_ok
        d["status_badge"] = "Conforme" if is_ok else "Obs. Pendiente"
        d["status_color"] = "#059669" if is_ok else "#D97706"
        evaluated_clauses.append(d)

    rate = (compliant_count / total * 100.0) if total > 0 else 100.0
    can_sign = rate >= 90.0

    return {
        "total_clauses": total,
        "compliant_clauses": compliant_count,
        "compliance_rate": round(rate, 1),
        "compliance_label": f"{rate:.1f}% Conforme ({compliant_count} de {total} Cláusulas)",
        "can_sign": can_sign,
        "is_fully_compliant": (compliant_count == total and total > 0),
        "clauses": evaluated_clauses
    }


# =============================================================================
# CATÁLOGO OFICIAL DE NORMAS PRECONFIGURADAS (OUT-OF-THE-BOX)
# =============================================================================

NOM070_CLAUSES: List[AuditClause] = [
    AuditClause("NOM-4.1.1", "4.1 Generalidades", "Requisitos de Verificación Independiente", "Auditor calificado e independiente con acreditación NOM-070.", "Cédula de acreditación de auditoría", True),
    AuditClause("NOM-4.2.1", "4.2 Objetivo y Alcance", "Definición del Objetivo", "Objetivo del estudio de ACV formalmente especificado.", "Documento de objetivos corporativos", True),
    AuditClause("NOM-4.2.2", "4.2 Objetivo y Alcance", "Público Objetivo y Aplicación", "Identificación de audiencias y destinatarios del reporte EPD.", "Definición de partes interesadas", True),
    AuditClause("NOM-4.2.3.1", "4.2 Objetivo y Alcance", "Función del Sistema Producto", "Identificación de la función técnica y desempeño del envase.", "Ficha técnica de especificación de botella", True),
    AuditClause("NOM-4.2.3.2", "4.2 Objetivo y Alcance", "Unidad Funcional", "Unidad declarada cuantitativa y claramente especificada con UF de referencia.", "1.000 u (Botella 500ml con tapa)", True),
    AuditClause("NOM-4.2.3.3", "4.2 Objetivo y Alcance", "Límites del Sistema", "Límites Cradle-to-Gate definidos con diagrama de flujo de procesos unitarios.", "Diagrama de flujo validado en lienzo", True),
    AuditClause("NOM-4.2.3.4", "4.2 Objetivo y Alcance", "Requisitos de Calidad de Datos (DQI)", "Evaluación de datos con matriz Pedigree e indicadores DQI.", "Score 5/5 validado con ecoinvent 3.12", True),
    AuditClause("NOM-4.3.1", "4.3 Inventario (LCI)", "Procedimientos de Recopilación de Datos", "Protocolos de medición directa de energía, insumos y mermas en planta.", "Registros SCADA y facturas CFE", True),
    AuditClause("NOM-4.3.4.1", "4.3 Inventario (LCI)", "Criterios de Corte (Cut-off)", "Regla de corte del 1% de masa y energía verificada. Sin omisiones relevantes.", "Corte acumulado < 0.2% conforme", True),
    AuditClause("NOM-4.3.4.2", "4.3 Inventario (LCI)", "Balance de Masa y Materia", "Suma de entradas igual a salidas + mermas con tolerancia estricta.", "Balance elemental 100% equilibrado", True),
    AuditClause("NOM-4.3.5.1", "4.3 Inventario (LCI)", "Asignación y Coproductos", "Reglas de corte físico aplicadas a la merma conforme a jerarquía ISO.", "Cut-off estricto acreditado en bucle interno", True),
    AuditClause("NOM-4.4.1", "4.4 Impacto (LCIA)", "Marco Metodológico de Evaluación", "Enfoque midpoint ambiental conforme a estándares internacionales.", "Metodología ReCiPe / EF 3.1", True),
    AuditClause("NOM-4.4.2.1", "4.4 Impacto (LCIA)", "Selección de Métodos de Caracterización", "Métodos de caracterización ambiental justificados y estandarizados.", "IPCC 2021 GWP 100a", True),
    AuditClause("NOM-4.4.4.1", "4.4 Impacto (LCIA)", "Análisis de Contribución y Hotspots", "Identificación de procesos clave que concentran emisiones y consumo.", "Identificación de inyección y transporte", True),
    AuditClause("NOM-4.5.1", "4.5 Interpretación", "Evaluación de Incertidumbre y Sensibilidad", "Sensibilidad paramétrica de mermas y distancia de logística.", "Parámetros del sistema evaluados", True),
    AuditClause("NOM-4.5.2", "4.5 Interpretación", "Conclusiones y Recomendaciones", "Recomendaciones fundamentadas en los resultados del inventario.", "Recomendaciones de ecodiseño", True),
    AuditClause("NOM-4.5.3.1", "4.5 Trazabilidad", "Integridad Criptográfica SHA-256", "Snapshot del modelo firmado con hash SHA-256 e inmutable en libro mayor.", "Hash de integridad activo", True),
    AuditClause("NOM-4.6.1.1", "4.6 Revisión Crítica", "Dictamen de Verificación NOM-070", "Dictamen independiente de verificador acreditado sin conflicto de interés.", "Acreditación externa verificada", False)
]

ISO14044_CLAUSES: List[AuditClause] = [
    AuditClause("ISO-4.1", "4.1 Marco Metodológico", "Fases del Análisis de Ciclo de Vida", "Definición formal de las 4 fases: Objetivo, LCI, LCIA e Interpretación.", "Plan metodológico del estudio", True),
    AuditClause("ISO-4.2.2", "4.2 Alcance", "Unidad Funcional y Flujo de Referencia", "Unidad funcional medible y representativa de la función del producto.", "Especificación funcional del producto", True),
    AuditClause("ISO-4.2.3", "4.2 Alcance", "Límites del Sistema del Producto", "Identificación explícita de entradas elementales y operaciones excluidas.", "Diagrama de flujo de límites de sistema", True),
    AuditClause("ISO-4.2.4", "4.2 Alcance", "Criterios de Corte Inicial", "Criterios para la inclusión de insumos energéticos y masa (máx 1%).", "Justificación de reglas de corte", True),
    AuditClause("ISO-4.3.2", "4.3 Inventario (LCI)", "Recolección y Cálculo de Datos", "Validación cruzada de balances de masa y energía por proceso unitario.", "Hojas de cálculo de inventario de planta", True),
    AuditClause("ISO-4.3.4", "4.3 Inventario (LCI)", "Procedimientos de Asignación", "Aplicación de jerarquía de asignación: subdivisión, expansión o física.", "Documento de justificación de coproductos", True),
    AuditClause("ISO-4.4.2", "4.4 Impacto (LCIA)", "Elementos Obligatorios de Caracterización", "Selección de categorías de impacto ambiental y factores de caracterización.", "Factores de caracterización ReCiPe/EF", True),
    AuditClause("ISO-4.5.2", "4.5 Interpretación", "Identificación de Aspectos Significativos", "Identificación de los procesos que concentran la mayor carga ambiental.", "Análisis de contribución de emisiones", True),
    AuditClause("ISO-4.5.3", "4.5 Interpretación", "Evaluación de Exhaustividad y Sensibilidad", "Verificación de completitud y evaluación de sensibilidad de parámetros críticos.", "Análisis de sensibilidad paramétrico", True),
    AuditClause("ISO-6.1", "6.1 Revisión Crítica", "Revisión por Partes Interesadas", "Dictamen o panel de revisión crítica independiente bajo ISO/TS 14071.", "Informe de revisión crítica externa", True)
]

ISO14067_CLAUSES: List[AuditClause] = [
    AuditClause("CFP-5.2", "5.2 Principios", "Enfoque de Ciclo de Vida para Huella de Carbono", "Cuantificación de emisiones y remociones de GEI en todas las etapas relevantes.", "Inventario de GEI de ciclo de vida", True),
    AuditClause("CFP-6.3.2", "6.3 Límites", "Exclusión de Compensaciones (Offsets)", "Las compensaciones de carbono no deben ser restadas de la huella del producto.", "Declaración de no compensación", True),
    AuditClause("CFP-6.3.4", "6.3 Límites", "Cambio Directo de Uso del Suelo (dLUC)", "Contabilización de emisiones por deforestación o cambio de uso de suelo.", "Evaluación de riesgo de deforestación", True),
    AuditClause("CFP-6.4.2", "6.4 Inventario", "Emisiones de Electricidad Específicas", "Factores de emisión del mix de red eléctrica nacional o certificados de origen.", "Factor de emisión oficial CFE/CRE", True),
    AuditClause("CFP-6.4.9", "6.4 Inventario", "Almacenamiento de Carbono Biogénico", "Reporte diferenciado de emisiones fósiles y biogénicas según ISO 14067.", "Balance de carbono biogénico", True),
    AuditClause("CFP-6.5", "6.5 Impacto", "Factores de Emisión GWP 100a del IPCC", "Uso obligatorio de potenciales de calentamiento global a 100 años (IPCC AR6).", "Tabla de factores GWP 100a IPCC", True),
    AuditClause("CFP-7.1", "7.1 Reporte", "Informe de Estudio de Huella de Carbono (CFP)", "Reporte transparente con desglose por etapa: materia prima, manufactura y transporte.", "Reporte técnico CFP del producto", True),
    AuditClause("CFP-8.1", "8.1 Verificación", "Aseguramiento de Tercera Parte", "Verificación independiente conforme a ISO 14064-3 con nivel de aseguramiento razonable.", "Dictamen de verificación de huella", True)
]

GHG_PROTOCOL_CLAUSES: List[AuditClause] = [
    AuditClause("GHG-01", "1. Objetivos", "Propósito del Inventario de Producto", "Definición del propósito corporativo y alcance de la contabilidad de GEI.", "Plan de gestión climática", True),
    AuditClause("GHG-02", "2. Límites", "Límites Cradle-to-Gate o Cradle-to-Grave", "Definición estricta de la frontera temporal y geográfica del producto.", "Mapa de límites del GHG Protocol", True),
    AuditClause("GHG-03", "3. Alcances", "Emisiones de Alcance 1, 2 y 3 Upstream", "Cuantificación de emisiones directas, de electricidad comprada e insumos clave.", "Desglose por Alcances 1, 2 y 3", True),
    AuditClause("GHG-04", "4. Recolección", "Calidad de Datos Primarios vs Secundarios", "Mínimo 80% de datos primarios en procesos bajo control financiero.", "Auditoría de datos de planta", True),
    AuditClause("GHG-05", "5. Asignación", "Reglas de Asignación del GHG Protocol", "Aplicación de asignación económica o física documentada.", "Justificación de coproductos", True),
    AuditClause("GHG-06", "6. Calidad", "Evaluación de Incertidumbre del Modelo", "Estimación de rangos de incertidumbre en factores de emisión.", "Análisis de incertidumbre DQI", True),
    AuditClause("GHG-07", "7. Reporte", "Reporte Público del Estándar de Producto", "Publicación de inventario con desglose por gas (CO2, CH4, N2O, HFCs).", "Reporte público de emisiones", True)
]

# Diccionario oficial de estándares precargados
OFFICIAL_STANDARDS: Dict[str, AuditStandard] = {
    "nom070": AuditStandard(
        id="nom070",
        name="NOM-070-SE-2024 / ISO 14044 (Destilados & Ecodiseño)",
        code="NOM-070",
        standard_family="Norma Oficial Mexicana / Bebidas Alcohólicas",
        description="Verificación obligatoria de especificaciones técnicas, balance de materia, reglas de corte y trazabilidad ambiental para destilados y empaques.",
        version="2024",
        is_official=True,
        created_by="system",
        clauses=NOM070_CLAUSES
    ),
    "iso14044": AuditStandard(
        id="iso14044",
        name="ISO 14044:2006 — Requisitos Generales de ACV",
        code="ISO-14044",
        standard_family="Estándar Internacional ISO",
        description="Gestión ambiental — Análisis del ciclo de vida — Requisitos y directrices internacionales para inventario, impacto e interpretación.",
        version="2006/Amd 2:2020",
        is_official=True,
        created_by="system",
        clauses=ISO14044_CLAUSES
    ),
    "iso14067": AuditStandard(
        id="iso14067",
        name="ISO 14067:2018 — Huella de Carbono de Productos (CFP)",
        code="ISO-14067",
        standard_family="Gases de Efecto Invernadero",
        description="Requisitos para la cuantificación y reporte de la huella de carbono de productos con exclusión estricta de compensaciones y factores IPCC AR6.",
        version="2018",
        is_official=True,
        created_by="system",
        clauses=ISO14067_CLAUSES
    ),
    "ghg_protocol": AuditStandard(
        id="ghg_protocol",
        name="GHG Protocol — Product Life Cycle Standard",
        code="GHG-PRODUCT",
        standard_family="Greenhouse Gas Protocol",
        description="Estándar internacional de contabilidad y reporte corporativo de gases de efecto invernadero para el ciclo de vida completo del producto.",
        version="2011",
        is_official=True,
        created_by="system",
        clauses=GHG_PROTOCOL_CLAUSES
    )
}

# Alias de compatibilidad total con código previo
OFFICIAL_CLAUSES: List[AuditClause] = NOM070_CLAUSES
