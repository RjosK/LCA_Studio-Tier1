import unittest
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from econode_studio.domain.audit_checklist import (
    OFFICIAL_STANDARDS,
    EPEAT_CLAUSES,
    calculate_audit_compliance
)
from econode_studio.infrastructure.audit_adapter import (
    list_all_checklist_templates,
    get_checklist_template
)
from econode_studio.application.normative_audit import (
    get_audit_checklist_use_case,
    update_clause_status_use_case
)


class TestEpeatAuditChecklist(unittest.TestCase):
    """Test suite for EPEAT 2.0 / Climate+ audit checklist integration."""

    def test_epeat_standard_registered_in_domain(self):
        """Verify epeat_2024 exists in OFFICIAL_STANDARDS with 22 clauses across 4 modules."""
        self.assertIn("epeat_2024", OFFICIAL_STANDARDS)
        std = OFFICIAL_STANDARDS["epeat_2024"]
        self.assertEqual(std.code, "EPEAT-2024")
        self.assertEqual(len(std.clauses), 22)
        self.assertEqual(len(EPEAT_CLAUSES), 22)

        # Verify the 4 core GEC modules
        sections = {c.section for c in std.clauses}
        self.assertIn("4.1 Cambio Climático", sections)
        self.assertIn("4.2 Circularidad", sections)
        self.assertIn("4.3 Químicos", sections)
        self.assertIn("4.4 Cadena Responsable", sections)

        # Check key specific criteria
        clause_ids = {c.clause_id for c in std.clauses}
        self.assertIn("EPEAT-4.1.1", clause_ids)  # PCF / LCA
        self.assertIn("EPEAT-4.1.2", clause_ids)  # Public PCF disclosure
        self.assertIn("EPEAT-4.1.3", clause_ids)  # Corporate GHG
        self.assertIn("EPEAT-4.1.4", clause_ids)  # SBTi
        self.assertIn("EPEAT-4.1.5", clause_ids)  # Renewable Electricity
        self.assertIn("EPEAT-4.1.6", clause_ids)  # ENERGY STAR
        self.assertIn("EPEAT-4.2.1", clause_ids)  # PCR Plastics
        self.assertIn("EPEAT-4.2.2", clause_ids)  # Recycled Metals
        self.assertIn("EPEAT-4.2.3", clause_ids)  # Design for Disassembly
        self.assertIn("EPEAT-4.3.1", clause_ids)  # RoHS / REACH
        self.assertIn("EPEAT-4.3.3", clause_ids)  # PFAS
        self.assertIn("EPEAT-4.4.1", clause_ids)  # ISO 14001
        self.assertIn("EPEAT-4.4.2", clause_ids)  # RBA VAP / Labor

    def test_epeat_compliance_calculation(self):
        """Verify calculation of compliance rate for EPEAT clauses."""
        res = calculate_audit_compliance(EPEAT_CLAUSES)
        self.assertEqual(res["total_clauses"], 22)
        self.assertGreater(res["compliant_clauses"], 0)
        self.assertIsInstance(res["compliance_rate"], float)
        self.assertTrue(res["can_sign"])

    def test_epeat_template_retrieval_and_listing(self):
        """Verify get_checklist_template and list_all_checklist_templates include epeat_2024."""
        template = get_checklist_template("epeat_2024")
        self.assertIsNotNone(template)
        self.assertEqual(template["id"], "epeat_2024")
        self.assertEqual(template["code"], "EPEAT-2024")
        self.assertEqual(len(template["clauses"]), 22)

        all_templates = list_all_checklist_templates()
        template_ids = {t["id"] for t in all_templates}
        self.assertIn("epeat_2024", template_ids)

    def test_epeat_audit_use_case_and_status_toggle(self):
        """Verify get_audit_checklist_use_case and update_clause_status_use_case for EPEAT."""
        sys_id = 21
        checklist = get_audit_checklist_use_case(sys_id, "epeat_2024")
        self.assertIsNotNone(checklist)
        self.assertEqual(checklist["checklist_id"], "epeat_2024")
        self.assertEqual(checklist["total_clauses"], 22)

        # Toggle an uncompliant clause to compliant
        res = update_clause_status_use_case(sys_id, "EPEAT-4.1.7", True, checklist_id="epeat_2024")
        self.assertIsNotNone(res)
        clause_map = {c["clause_id"]: c["is_compliant"] for c in res["clauses"]}
        self.assertTrue(clause_map.get("EPEAT-4.1.7"))

        # Toggle back to False
        res2 = update_clause_status_use_case(sys_id, "EPEAT-4.1.7", False, checklist_id="epeat_2024")
        clause_map2 = {c["clause_id"]: c["is_compliant"] for c in res2["clauses"]}
        self.assertFalse(clause_map2.get("EPEAT-4.1.7"))


if __name__ == "__main__":
    unittest.main()
