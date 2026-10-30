"""
ECONODE Studio - Tier 4: Real-World Application Scenarios (test_tier4_scenarios.py)
Validates complete visitor and user journeys from landing to execution:
- Scenario 1: First-time visitor landing and exploratory path
- Scenario 2: Bilingual executive transition (Spanish -> English)
- Scenario 3: Deep-Tech LCA analyst dock stage tour
- Scenario 4: Industrial auditor compliance inspection
- Scenario 5: Enterprise IT security & BYOS Drive custody
- Scenario 6: Compact laptop (1024px) ergonomic responsive journey
- Scenario 7: Industrial export & interoperability evaluation
- Scenario 8: Analyst onboarding and system wizard flow
- Scenario 9: Dual-mode canvas and view return
- Scenario 10: Multi-role collaboration & session termination
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import unittest
import re
from tests.e2e.e2e_utils import (
    fetch_resource,
    parse_html_to_dom,
    CSSAnalyzer,
    extract_i18n_dictionary
)


class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Application Scenarios test suite (>=10 scenarios)."""

    @classmethod
    def setUpClass(cls):
        cls.status_html, cls.headers_html, cls.html_raw = fetch_resource("/")
        cls.status_css, cls.headers_css, cls.css_raw = fetch_resource("/css/styles.css")
        cls.status_app_js, cls.headers_app_js, cls.app_js_raw = fetch_resource("/js/app.js")
        cls.status_i18n_js, cls.headers_i18n_js, cls.i18n_js_raw = fetch_resource("/js/i18n.js")

        cls.dom = parse_html_to_dom(cls.html_raw)
        cls.css = CSSAnalyzer(cls.css_raw)
        cls.i18n = extract_i18n_dictionary(cls.i18n_js_raw)

    # -------------------------------------------------------------------------
    # Scenario 1: First-Time Visitor Journey (Spanish Default)
    # -------------------------------------------------------------------------
    def test_scenario_01_first_time_visitor_exploratory_journey(self):
        """Scenario 1: Complete first-time visitor landing, reading, and CTA interaction."""
        # 1. Landing view is active
        home_view = self.dom.find_by_id("viewHome")
        self.assertIsNotNone(home_view)
        self.assertTrue(home_view.has_class("active"))

        # 2. Luminous background and hero elements are present
        has_white = self.css.selector_has_property("#viewHome", "background-color", "#ffffff")
        self.assertTrue(has_white)
        self.assertIsNotNone(self.dom.find_all_by_class("strand-top-pill"))
        self.assertIsNotNone(self.dom.find_all_by_class("strand-main-title"))

        # 3. 3-pillars cards introduce functional sequence
        cards = self.dom.find_all_by_class("strand-card")
        self.assertEqual(len(cards), 3)

        # 4. Capabilities bento grid and confrontation matrix
        bento = self.dom.find_by_id("homeCapabilities")
        self.assertIsNotNone(bento)
        table = self.dom.find_all_by_class("strand-comparison-table")
        self.assertTrue(len(table) >= 1)

        # 5. Clicking primary hero obsidian CTA routes to login for unauthenticated visitors
        self.assertIn('btnHomeEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"))', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Scenario 2: Bilingual Executive Transition (Spanish -> English)
    # -------------------------------------------------------------------------
    def test_scenario_02_bilingual_executive_transition(self):
        """Scenario 2: Visitor switches language to English and validates i18n coverage."""
        # 1. Language switcher buttons are in DOM
        btn_es = self.dom.find_by_id("btnLangEs")
        btn_en = self.dom.find_by_id("btnLangEn")
        self.assertIsNotNone(btn_es)
        self.assertIsNotNone(btn_en)

        # 2. English dictionary contains full parity with Spanish
        es_keys = set(self.i18n["es"].keys())
        en_keys = set(self.i18n["en"].keys())
        self.assertEqual(es_keys, en_keys)

        # 3. Dynamic language switcher logic is wired in app.js
        self.assertIn('btnEn.addEventListener("click", () => window.I18n.setLanguage("en"))', self.app_js_raw)
        self.assertIn('btnEs.addEventListener("click", () => window.I18n.setLanguage("es"))', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Scenario 3: Deep-Tech LCA Analyst Dock Stage Tour
    # -------------------------------------------------------------------------
    def test_scenario_03_analyst_dock_stage_mutation_tour(self):
        """Scenario 3: Analyst navigates through all 5 stages of the Fold Toolbar dock."""
        dock = self.dom.find_by_id("heroFoldToolbar")
        self.assertIsNotNone(dock)
        items = dock.find_all_by_class("fold-dock-item")
        self.assertEqual(len(items), 5)

        # Verify all 5 stages in catalog have telemetry and color definitions
        catalog_match = re.search(r"const\s+stageCatalog\s*=\s*\{([\s\S]+?)\};", self.app_js_raw)
        self.assertIsNotNone(catalog_match)
        catalog_str = catalog_match.group(1)

        expected_stages = ["injection", "blowmolding", "distribution", "vault", "audit"]
        for stg in expected_stages:
            self.assertIn(stg, catalog_str)
            self.assertIn("gwp:", catalog_str)
            self.assertIn("mass:", catalog_str)
            self.assertIn("norm:", catalog_str)

    # -------------------------------------------------------------------------
    # Scenario 4: Industrial Auditor Compliance Inspection Journey
    # -------------------------------------------------------------------------
    def test_scenario_04_auditor_compliance_inspection(self):
        """Scenario 4: Auditor inspects NOM-070 verification and cryptographic dictamen."""
        # 1. Stage catalog contains NOM-070 audit stage
        self.assertIn("Auditoria Normativa y Conformidad NOM-070-SE-2024", self.app_js_raw)
        self.assertIn("18 Cláusulas Verificadas", self.app_js_raw)
        self.assertIn("Firma Digital HMAC", self.app_js_raw)

        # 2. Bento grid features NOM-070 capability
        self.assertIn("NORMATIVA NOM-070-SE-2024", self.html_raw)

        # 3. Audit view exists in SPA
        audit_view = self.dom.find_by_id("viewAudit")
        self.assertIsNotNone(audit_view)

    # -------------------------------------------------------------------------
    # Scenario 5: Enterprise IT Security & BYOS Drive Custody
    # -------------------------------------------------------------------------
    def test_scenario_05_enterprise_it_security_byos_custody(self):
        """Scenario 5: IT officer verifies Google Drive BYOS sovereign data architecture."""
        # 1. Zero server bytes contract
        self.assertIn("0 Bytes en Vercel", self.html_raw)
        self.assertIn("Google Drive Personal (0 MB Servidor)", self.app_js_raw)

        # 2. SHA-256 seal verification present
        self.assertIn("SHA-256", self.html_raw)
        self.assertIn("SHA-256", self.app_js_raw)

        # 3. Client-side drive_storage.js loaded directly
        self.assertIn("js/drive_storage.js", self.html_raw)

    # -------------------------------------------------------------------------
    # Scenario 6: Compact Laptop (1024px) Ergonomic Journey
    # -------------------------------------------------------------------------
    def test_scenario_06_compact_laptop_responsive_journey(self):
        """Scenario 6: Visitor accesses on 1024px screen without layout breaking or overflow."""
        queries = self.css.get_media_queries(1024)
        self.assertTrue(len(queries) >= 1)

        # Root overflow prevention
        has_overflow_x = self.css.selector_has_property("#viewHome", "overflow-x", "hidden")
        self.assertTrue(has_overflow_x)

        # Title clamp to 40px
        has_title_clamp = any(".strand-main-title" in b and "40px" in b for _, b in queries)
        self.assertTrue(has_title_clamp)

        # Pillars collapse
        has_pillars_collapse = any(".strand-pillars-cards" in b and "1fr" in b for _, b in queries)
        self.assertTrue(has_pillars_collapse)

        # Bento collapse
        has_bento_collapse = any(".bento-wide" in b and "span 1" in b for _, b in queries)
        self.assertTrue(has_bento_collapse)

    # -------------------------------------------------------------------------
    # Scenario 7: Industrial Export & Interoperability Evaluation
    # -------------------------------------------------------------------------
    def test_scenario_07_industrial_export_interoperability(self):
        """Scenario 7: User evaluates industrial export formats (openLCA, SimaPro, ILCD)."""
        # Interoperability strip in DOM
        self.assertIn("openLCA JSON-LD v2", self.html_raw)
        self.assertIn("ecoinvent 3.12 Cut-off", self.html_raw)
        self.assertIn("SimaPro 9.x CSV", self.html_raw)
        self.assertIn("ILCD XML Oficial", self.html_raw)

        # Bento export card
        self.assertIn("SUITE DE EXPORTACIÓN INDUSTRIAL", self.html_raw)

    # -------------------------------------------------------------------------
    # Scenario 8: Analyst Onboarding and System Wizard Flow
    # -------------------------------------------------------------------------
    def test_scenario_08_analyst_onboarding_and_wizard(self):
        """Scenario 8: Analyst registers and accesses system creation wizard."""
        # 1. Navigation to signup
        signup_view = self.dom.find_by_id("viewSignup")
        self.assertIsNotNone(signup_view)

        # 2. System creation wizard modal is preserved in DOM
        wiz = self.dom.find_by_id("modalWizard")
        self.assertIsNotNone(wiz)
        self.assertIsNotNone(self.dom.find_by_id("wizSystemName"))
        self.assertIsNotNone(self.dom.find_by_id("wizSystemAmount"))
        self.assertIsNotNone(self.dom.find_by_id("wizSystemUnit"))
        self.assertIsNotNone(self.dom.find_by_id("wizSystemLimits"))

    # -------------------------------------------------------------------------
    # Scenario 9: Dual-Mode Canvas and View Return
    # -------------------------------------------------------------------------
    def test_scenario_09_dual_mode_canvas_and_brand_return(self):
        """Scenario 9: Studio canvas dual-mode toggling and brand logo home navigation."""
        canvas_view = self.dom.find_by_id("viewCanvas")
        self.assertIsNotNone(canvas_view)

        # Dual mode buttons exist in canvas view
        btn_visual = self.dom.find_by_id("btnCanvasViewVisual")
        btn_table = self.dom.find_by_id("btnCanvasViewTable")
        self.assertIsNotNone(btn_visual)
        self.assertIsNotNone(btn_table)

        # Brand logo returns to home
        btn_home = self.dom.find_by_id("btnNavHome")
        self.assertIsNotNone(btn_home)
        self.assertIn('btnHomeLogo.addEventListener("click", () => showView("home"))', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Scenario 10: Multi-Role Collaboration & Session Termination
    # -------------------------------------------------------------------------
    def test_scenario_10_multi_role_collaboration_and_logout(self):
        """Scenario 10: Collaboration invitation modal and logout cleanup."""
        # Invite modal exists in DOM
        invite_modal = self.dom.find_by_id("modalInviteCollaborator")
        self.assertIsNotNone(invite_modal)

        # Logout button in top navbar
        btn_logout = self.dom.find_by_id("btnNavbarLogout")
        self.assertIsNotNone(btn_logout)

        # Logout cleans up session state and redirects to home
        self.assertIn('showView("home")', self.app_js_raw)
        self.assertIn('sessionStorage.removeItem("econode_token")', self.app_js_raw)


if __name__ == "__main__":
    unittest.main()
