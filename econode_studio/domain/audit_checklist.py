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

EPEAT_CLAUSES: List[AuditClause] = [
    # 4.1 Mitigación del Cambio Climático (Climate Change Mitigation & Climate+)
    AuditClause("EPEAT-4.1.1", "4.1 Cambio Climático", "Huella de Carbono del Producto (PCF / ACV)", "Cuantificación de huella de carbono de ciclo de vida conforme a ISO 14040/14044 o ISO 14067 con revisión crítica independiente (Requerido para EPEAT Climate+).", "Reporte de ACV/PCF con dictamen de revisión crítica independiente (3ª parte)", True),
    AuditClause("EPEAT-4.1.2", "4.1 Cambio Climático", "Divulgación Pública del PCF", "Publicación abierta del informe o ficha ejecutiva de la huella de carbono con desglose por fases de ciclo de vida (Manufactura, Transporte, Uso, Fin de vida).", "URL pública de divulgación o Declaración Ambiental de Producto (EPD)", True),
    AuditClause("EPEAT-4.1.3", "4.1 Cambio Climático", "Inventario Corporativo de Emisiones GEI", "Inventario público verificado de emisiones corporativas Alcance 1, Alcance 2 (dual: Market y Location-Based) y Alcance 3 relevante según GHG Protocol.", "Reporte corporativo GEI verificado bajo ISO 14064-3 / CDP", True),
    AuditClause("EPEAT-4.1.4", "4.1 Cambio Climático", "Metas Basadas en Ciencia (SBTi 1.5 °C / Net-Zero)", "Compromiso formal o validación de metas corporativas de descarbonización alineadas con la trayectoria de 1.5 °C de la iniciativa Science Based Targets.", "Carta de validación o aprobación pública en el registro SBTi", True),
    AuditClause("EPEAT-4.1.5", "4.1 Cambio Climático", "Electricidad Renovable en Ensamble Final", "Uso documentado de electricidad renovable (mínimo 20%, 50% o 100%) en instalaciones de ensamble final mediante PPAs o certificados EAC (I-REC/CEL).", "Facturas y certificados contractuales de energía limpia (EACs)", True),
    AuditClause("EPEAT-4.1.6", "4.1 Cambio Climático", "Eficiencia Energética del Producto (ENERGY STAR)", "Cumplimiento certificado con la versión vigente de la especificación ENERGY STAR aplicable a la categoría de producto tecnológico.", "Certificado oficial de cumplimiento ENERGY STAR / Informe de pruebas acreditado", True),
    AuditClause("EPEAT-4.1.7", "4.1 Cambio Climático", "Materiales de Baja Huella de Carbono", "Uso documentado de insumos críticos de menor intensidad de carbono (aluminio bajo en carbono, semiconductores optimizados o resinas recicladas).", "Declaraciones ambientales de proveedores y factores de emisión trazables", False),

    # 4.2 Uso Sostenible de Recursos y Circularidad (Sustainable Use of Resources)
    AuditClause("EPEAT-4.2.1", "4.2 Circularidad", "Contenido de Plástico Reciclado Post-Consumo (PCR)", "Incorporación mínima verificada de plástico reciclado post-consumo (PCR) de al menos 5%, 10%, 25% o 50% en masa total de partes plásticas.", "Certificación de contenido reciclado ISO 14021 (UL 2809 / GRS / SCS)", True),
    AuditClause("EPEAT-4.2.2", "4.2 Circularidad", "Contenido de Metales Reciclados", "Uso de metales secundarios o reciclados (aluminio, acero, cobre, cobalto, estaño u oro) con cadena de custodia documentada.", "Certificado de cadena de custodia y especificación técnica de aleación", True),
    AuditClause("EPEAT-4.2.3", "4.2 Circularidad", "Diseño para Desensamble y Reparabilidad", "Uniones accesibles con herramientas comunes comerciales, ausencia de pegamentos ciegos en componentes clave y cumplimiento de EN 45554 / índice de reparabilidad.", "Manual técnico de servicio, diagrama de desensamble e índice de reparabilidad", True),
    AuditClause("EPEAT-4.2.4", "4.2 Circularidad", "Disponibilidad de Refacciones y Documentación", "Garantía pública de disponibilidad de partes de repuesto críticas y manuales de reparación por al menos 3 a 7 años posteriores al retiro del mercado.", "Declaración pública de política de refacciones y catálogo de partes", True),
    AuditClause("EPEAT-4.2.5", "4.2 Circularidad", "Longevidad y Reemplazabilidad de Baterías", "Baterías reemplazables por el usuario o técnicos calificados sin destruir el chasis, con garantía de retención de carga (>= 80% en 500-1000 ciclos).", "Reporte de prueba de ciclos de vida de batería y procedimiento de reemplazo", True),
    AuditClause("EPEAT-4.2.6", "4.2 Circularidad", "Empaque Sustentable y Libre de EPS", "Empaque secundario y terciario con mínimo 50% a 90% de fibra reciclada certificada FSC/PEFC y eliminación total de poliestireno expandido (EPS).", "Ficha técnica de empaque y certificado de cadena de custodia forestal", True),
    AuditClause("EPEAT-4.2.7", "4.2 Circularidad", "Programa de Retorno y Reciclaje de Fin de Vida (Takeback)", "Disponibilidad de canal formal de recolección y reciclaje de equipo obsoleto a través de procesadores certificados bajo R2v3 o e-Stewards.", "Contrato o convenio con reciclador acreditado R2v3 / e-Stewards", True),

    # 4.3 Reducción de Químicos de Preocupación (Chemicals of Concern)
    AuditClause("EPEAT-4.3.1", "4.3 Químicos", "Conformidad Obligatoria con Directivas RoHS y REACH", "Restricción estricta de plomo, mercurio, cadmio, cromo hexavalente, PBB, PBDE y ftalatos (DEHP, BBP, DBP, DIBP), y sustancias SVHC (< 0.1% peso/peso).", "Reporte de ensayos de laboratorio (XRF/ICP) y declaración formal de conformidad", True),
    AuditClause("EPEAT-4.3.2", "4.3 Químicos", "Eliminación de Retardantes Halogenados (BFR/CFR)", "Partes plásticas mayores a 25g y placas de circuito impreso (PCB) libres de halógenos (< 900 ppm Cl/Br y < 1500 ppm total según IEC 61249-2-21).", "Certificado de análisis libre de halógenos (Halogen-Free)", True),
    AuditClause("EPEAT-4.3.3", "4.3 Químicos", "Restricción y Monitoreo de Sustancias PFAS", "Eliminación o sustitución intencional de compuestos per- y polifluoroalquilados (PFAS) en piezas mecánicas, recubrimientos y empaques.", "Declaración de ausencia intencional de PFAS por proveedores de partes", False),
    AuditClause("EPEAT-4.3.4", "4.3 Químicos", "Declaración Completa de Materiales (Full Material Disclosure)", "Inventario químico y desglose de sustancias químicas de la lista de materiales (BOM) a un umbral mínimo de 1,000 ppm (0.1%).", "BOM de sustancias químicas y fichas técnicas de seguridad (FDS/MSDS)", True),

    # 4.4 Cadenas de Suministro Responsables (Responsible Supply Chains / ESG)
    AuditClause("EPEAT-4.4.1", "4.4 Cadena Responsable", "Sistema de Gestión Ambiental Certificado (ISO 14001)", "Certificación ISO 14001 o EMAS de gestión ambiental en la planta de ensamblado final y en proveedores clave de componentes.", "Copia del certificado ISO 14001 vigente emitido por organismo acreditado", True),
    AuditClause("EPEAT-4.4.2", "4.4 Cadena Responsable", "Auditorías Sociales y Laborales (Código RBA / SA8000)", "Auditoría laboral independiente en instalaciones de manufactura basada en el código de conducta de la Responsible Business Alliance (RBA VAP).", "Reporte de auditoría RBA VAP o certificación SA8000 sin hallazgos prioritarios", True),
    AuditClause("EPEAT-4.4.3", "4.4 Cadena Responsable", "Diligencia Debida en Minerales de Conflicto (3TG + Cobalto)", "Trazabilidad y debida diligencia de cadenas de suministro para estaño, tantalio, tungsteno, oro (3TG) y cobalto conforme a lineamientos OCDE.", "Plantilla de reporte de minerales de conflicto (CMRT / EMRT) con fundidoras RMI", True),
    AuditClause("EPEAT-4.4.4", "4.4 Cadena Responsable", "Salud y Seguridad en el Trabajo (ISO 45001)", "Sistema de gestión de seguridad y salud en el trabajo implementado y certificado en plantas principales de manufactura.", "Certificado ISO 45001 vigente en plantas de producción", True)
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
    ),
    "epeat_2024": AuditStandard(
        id="epeat_2024",
        name="EPEAT 2.0 / Climate+ (GEC — Criterios Armonizados)",
        code="EPEAT-2024",
        standard_family="Global Electronics Council (GEC) / Ecolabel",
        description="Estándar ecológico global para electrónica y TI: Huella de carbono (PCF/ACV verificado), contenido reciclado PCR, circularidad, restricción de químicos (RoHS/REACH/PFAS) y cadena ética (RBA/3TG).",
        version="2024/Climate+",
        is_official=True,
        created_by="system",
        clauses=EPEAT_CLAUSES
    )
}

# Alias de compatibilidad total con código previo
OFFICIAL_CLAUSES: List[AuditClause] = NOM070_CLAUSES
