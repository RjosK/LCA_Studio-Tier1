"""
econode_studio/tests/test_domain.py - Pruebas Unitarias Aisladas de la Capa de Dominio
Valida entidades puras, catálogos de normas y funciones de cálculo de conformidad sin dependencias externas.
"""

import unittest
import sys
import os

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)
PARENT_DIR = os.path.dirname(STUDIO_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from domain.audit_checklist import (
    AuditStandard,
    OFFICIAL_STANDARDS,
    NOM070_CLAUSES,
    calculate_audit_compliance
)


class TestDomainAuditChecklist(unittest.TestCase):
    """Pruebas de las reglas de negocio de auditoría y estándares."""

    def test_official_standards_catalog(self):
        """Verifica que el catálogo oficial contenga las 4 normas estándar con cláusulas válidas."""
        self.assertIn("nom070", OFFICIAL_STANDARDS)
        self.assertIn("iso14044", OFFICIAL_STANDARDS)
        self.assertIn("iso14067", OFFICIAL_STANDARDS)
        self.assertIn("ghg_protocol", OFFICIAL_STANDARDS)

        nom070 = OFFICIAL_STANDARDS["nom070"]
        self.assertEqual(nom070.id, "nom070")
        self.assertEqual(len(nom070.clauses), 18)

        iso14044 = OFFICIAL_STANDARDS["iso14044"]
        self.assertGreater(len(iso14044.clauses), 0)

        iso14067 = OFFICIAL_STANDARDS["iso14067"]
        self.assertGreater(len(iso14067.clauses), 0)

        ghg = OFFICIAL_STANDARDS["ghg_protocol"]
        self.assertGreater(len(ghg.clauses), 0)

    def test_calculate_audit_compliance_all_compliant(self):
        """Calcula conformidad al 100% cuando todas las cláusulas son conformes."""
        std = OFFICIAL_STANDARDS["nom070"]
        active_states = {c.clause_id: True for c in std.clauses}
        res = calculate_audit_compliance(std, active_states)

        self.assertEqual(res["total_clauses"], 18)
        self.assertEqual(res["compliant_clauses"], 18)
        self.assertEqual(res["compliance_rate"], 100.0)
        self.assertTrue(res["is_fully_compliant"])

    def test_calculate_audit_compliance_partial(self):
        """Calcula conformidad parcial y porcentaje redondeado."""
        std = OFFICIAL_STANDARDS["nom070"]
        # Marcar solo 9 de 18 como conformes (50%)
        active_states = {c.clause_id: (i < 9) for i, c in enumerate(std.clauses)}
        res = calculate_audit_compliance(std, active_states)

        self.assertEqual(res["total_clauses"], 18)
        self.assertEqual(res["compliant_clauses"], 9)
        self.assertEqual(res["compliance_rate"], 50.0)
        self.assertFalse(res["is_fully_compliant"])

    def test_custom_standard_creation(self):
        """Verifica la instanciación de un estándar personalizado de empresa."""
        custom_std = AuditStandard(
            id="corp_pet_standard",
            name="Norma Interna BioPack 2026",
            code="STD-BIOPACK-01",
            standard_family="Corporativa",
            description="Verificación de trazabilidad rPET",
            clauses=[],
            version="1.0",
            created_by="Carla Méndez"
        )
        self.assertEqual(custom_std.id, "corp_pet_standard")
        self.assertEqual(custom_std.code, "STD-BIOPACK-01")
        self.assertEqual(custom_std.standard_family, "Corporativa")
        self.assertEqual(len(custom_std.clauses), 0)


if __name__ == "__main__":
    unittest.main()
