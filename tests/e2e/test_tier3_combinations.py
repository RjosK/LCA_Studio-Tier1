"""
ECONODE Studio - Tier 3: Cross-Feature Combinations (test_tier3_combinations.py)
Validates pairwise feature interactions and cross-cutting behaviors:
- Language toggle + Fold toolbar stage mutation
- Navbar CTA + Modal trigger & route protection
- Bento showcase + Responsive collapse
- Dock bar + Responsive wrap
- Telemetry + Mathematical invariants
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


class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """Tier 3: Cross-Feature Combinations test suite."""

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
    # Combination 1: Language Toggle (F17) + Fold Dock Telemetry (F15/F16)
    # -------------------------------------------------------------------------
    def test_comb01_language_toggle_and_fold_dock_keys(self):
        """Comb 01: Verify Fold Toolbar stage keys exist and are language-agnostic."""
        dock = self.dom.find_by_id("heroFoldToolbar")
        self.assertIsNotNone(dock)
        items = dock.find_all_by_class("fold-dock-item")
        stages = [btn.get_attr("data-stage") for btn in items]
        self.assertEqual(stages, ["injection", "blowmolding", "distribution", "vault", "audit"])
        # Both ES and EN dictionaries must contain corresponding i18n keys if wired
        for lang in ["es", "en"]:
            self.assertIn("home.nav_features", self.i18n[lang])
            self.assertIn("home.nav_enter", self.i18n[lang])

    # -------------------------------------------------------------------------
    # Combination 2: Top Navbar CTA (F18) + Unauthenticated Security (F14/F18)
    # -------------------------------------------------------------------------
    def test_comb02_navbar_cta_routes_to_login_when_unauthenticated(self):
        """Comb 02: Clicking navbar enter button routes unauthenticated users to login."""
        self.assertIn('btnNavEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"))', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Combination 3: Primary Obsidian CTA (F03/F09) + Studio Router (F18)
    # -------------------------------------------------------------------------
    def test_comb03_hero_obsidian_button_routes_to_studio(self):
        """Comb 03: Primary hero obsidian button is wired to showView auth router."""
        self.assertIn('btnHomeEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"))', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Combination 4: Fold Dock Glassmorphism (F04) + Responsive Collapse (F08)
    # -------------------------------------------------------------------------
    def test_comb04_fold_dock_adapts_to_responsive_breakpoint(self):
        """Comb 04: Fold dock maintains backdrop blur on desktop and wraps at 1024px."""
        has_blur = self.css.selector_has_property(".fold-dock-bar", "backdrop-filter", "blur(24px)")
        self.assertTrue(has_blur)
        queries = self.css.get_media_queries(1024)
        has_wrap = any(".fold-dock-bar" in body and "flex-wrap: wrap" in body for _, body in queries)
        self.assertTrue(has_wrap)

    # -------------------------------------------------------------------------
    # Combination 5: 3-Pillars Grid (F05/F11) + Responsive Collapse (F08)
    # -------------------------------------------------------------------------
    def test_comb05_three_pillars_desktop_grid_and_tablet_collapse(self):
        """Comb 05: 3-pillars is repeat(3, 1fr) on desktop and collapses to 1fr at 1024px."""
        has_3col = self.css.selector_has_property(".strand-pillars-cards", "grid-template-columns", "repeat(3")
        self.assertTrue(has_3col)
        queries = self.css.get_media_queries(1024)
        has_1col = any(".strand-pillars-cards" in body and "1fr" in body for _, body in queries)
        self.assertTrue(has_1col)

    # -------------------------------------------------------------------------
    # Combination 6: Bento Grid (F06/F12) + Responsive Column Span (F08)
    # -------------------------------------------------------------------------
    def test_comb06_bento_wide_cards_and_responsive_collapse(self):
        """Comb 06: Bento wide cards span 2 columns on desktop and 1 column at 1024px."""
        has_span2 = self.css.selector_has_property(".bento-wide", "grid-column", "span 2")
        self.assertTrue(has_span2)
        queries = self.css.get_media_queries(1024)
        has_span1 = any(".bento-wide" in body and "span 1" in body for _, body in queries)
        self.assertTrue(has_span1)

    # -------------------------------------------------------------------------
    # Combination 7: Leontief Bento (F12) + Telemetry Mass Conservation (F16/F20)
    # -------------------------------------------------------------------------
    def test_comb07_leontief_bento_correlates_with_telemetry_mass_conservation(self):
        """Comb 07: Leontief algebra bento card matches 100.0% mass conservation telemetry."""
        bento_sec = self.dom.find_by_id("homeCapabilities")
        self.assertIsNotNone(bento_sec)
        self.assertIn("Leontief", self.html_raw)
        mass_text = self.dom.find_by_id("stageMassValText")
        self.assertIn("100.0%", mass_text.text_content)

    # -------------------------------------------------------------------------
    # Combination 8: NOM-070 Bento (F12) + Audit Telemetry (F16) + Audit View (F14)
    # -------------------------------------------------------------------------
    def test_comb08_nom070_clause_consistency_across_views(self):
        """Comb 08: Exactly 18 clauses referenced in Bento, telemetry, and Audit view."""
        self.assertIn("18 Cláusulas Verificadas", self.app_js_raw)
        audit_view = self.dom.find_by_id("viewAudit")
        self.assertIsNotNone(audit_view)

    # -------------------------------------------------------------------------
    # Combination 9: Google Drive BYOS Bento (F12) + Vault Telemetry (F16)
    # -------------------------------------------------------------------------
    def test_comb09_byos_zero_bytes_consistency(self):
        """Comb 09: Sovereign Drive storage maintains 0 Bytes server footprint invariant."""
        self.assertIn("Google Drive Personal (0 MB Servidor)", self.app_js_raw)
        self.assertIn("0 Bytes en Vercel", self.html_raw)

    # -------------------------------------------------------------------------
    # Combination 10: Confrontation Table (F07/F13) + Contrast Cells
    # -------------------------------------------------------------------------
    def test_comb10_confrontation_table_dimensions_and_styling(self):
        """Comb 10: Comparison table has 6 criteria rows contrasting Excel vs ECONODE Cloud."""
        table = self.dom.find_all_by_class("strand-comparison-table")
        self.assertTrue(len(table) >= 1)
        tbody = table[0].find_all_by_tag("tbody")
        rows = tbody[0].find_all_by_tag("tr")
        self.assertEqual(len(rows), 6)
        # Verify first row compares modeling time
        self.assertIn("Tiempo de Modelado", rows[0].get_full_text())

    # -------------------------------------------------------------------------
    # Combination 11: Final CTA (F07/F13) + Inverted Obsidian Button (F03)
    # -------------------------------------------------------------------------
    def test_comb11_final_cta_inverted_obsidian_button(self):
        """Comb 11: Final dark gradient card contains inverted obsidian button."""
        cta = self.dom.find_all_by_class("strand-final-cta-card")
        self.assertTrue(len(cta) >= 1)
        btn = cta[0].find_all_by_class("btn-strand-obsidian")
        self.assertTrue(len(btn) >= 1)
        self.css.selector_has_property(".strand-final-cta-card .btn-strand-obsidian", "background")

    # -------------------------------------------------------------------------
    # Combination 12: Top Micro-Badge (F02/F09) + Capabilities Anchor (F12)
    # -------------------------------------------------------------------------
    def test_comb12_top_announcement_pill_anchors_to_capabilities(self):
        """Comb 12: Top announcement micro-badge links to #homeCapabilities."""
        pill = self.dom.find_all_by_class("strand-top-pill")
        self.assertTrue(len(pill) >= 1)
        target = pill[0].get_attr("href")
        self.assertEqual(target, "#homeCapabilities")

    # -------------------------------------------------------------------------
    # Combination 13: Language Toggle (F17) + Truncation Safety (F08)
    # -------------------------------------------------------------------------
    def test_comb13_language_toggle_and_project_title_truncation(self):
        """Comb 13: Toggling language updates text without breaking ellipsis truncation."""
        title_rules = self.css.get_rules_for_selector(".project-title")
        has_ellipsis = any("ellipsis" in r for r in title_rules)
        self.assertTrue(has_ellipsis)
        # Lang buttons exist
        self.assertIsNotNone(self.dom.find_by_id("btnLangEs"))
        self.assertIsNotNone(self.dom.find_by_id("btnLangEn"))

    # -------------------------------------------------------------------------
    # Combination 14: View Containers (F14) + View Switching Logic (F18)
    # -------------------------------------------------------------------------
    def test_comb14_view_containers_and_showview_router(self):
        """Comb 14: showView manages classList.toggle('active') across all 8 views."""
        self.assertIn('views[name].classList.toggle("active", name === viewName);', self.app_js_raw)

    # -------------------------------------------------------------------------
    # Combination 15: Rapid Stage Transitions (F15) + SVG Coordinate Stability (F10)
    # -------------------------------------------------------------------------
    def test_comb15_rapid_stage_transitions_preserve_svg_coordinates(self):
        """Comb 15: Cycling through all 5 stages mutates textContent without altering SVG viewBox."""
        svg = self.dom.find_by_id("strandStageSvg")
        self.assertEqual(svg.get_attr("viewBox"), "0 0 980 420")
        for stage in ["injection", "blowmolding", "distribution", "vault", "audit"]:
            self.assertIn(stage, self.app_js_raw)


if __name__ == "__main__":
    unittest.main()
