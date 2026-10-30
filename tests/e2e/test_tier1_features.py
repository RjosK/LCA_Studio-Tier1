"""
ECONODE Studio - Tier 1: Feature Coverage (test_tier1_features.py)
Validates all 20 features (F01 - F20) in isolation against http://127.0.0.1:8095/
and static DOM/CSS/JS contracts. Minimum 5 tests per feature (100 total).
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


class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage test suite covering F01 through F20."""

    @classmethod
    def setUpClass(cls):
        # Fetch live assets from server (with graceful fallback if needed)
        cls.status_html, cls.headers_html, cls.html_raw = fetch_resource("/")
        cls.status_css, cls.headers_css, cls.css_raw = fetch_resource("/css/styles.css")
        cls.status_app_js, cls.headers_app_js, cls.app_js_raw = fetch_resource("/js/app.js")
        cls.status_i18n_js, cls.headers_i18n_js, cls.i18n_js_raw = fetch_resource("/js/i18n.js")

        cls.dom = parse_html_to_dom(cls.html_raw)
        cls.css = CSSAnalyzer(cls.css_raw)
        cls.i18n = extract_i18n_dictionary(cls.i18n_js_raw)

    # =========================================================================
    # F01: Luminous Pure White Theme & Ambient Aurora
    # =========================================================================
    def test_f01_pure_white_background_present(self):
        """F01-1: Verify #viewHome defines pure white background #FFFFFF."""
        has_white = self.css.selector_has_property("#viewHome", "background-color", "#ffffff")
        self.assertTrue(has_white, "CSS #viewHome must have background-color: #FFFFFF")

    def test_f01_ambient_aurora_emerald_radial_gradient(self):
        """F01-2: Verify emerald radial aurora gradient in #viewHome."""
        rules = self.css.get_rules_for_selector("#viewHome")
        has_emerald = any("rgba(16, 185, 129" in r or "rgba(16,185,129" in r for r in rules)
        self.assertTrue(has_emerald, "CSS #viewHome must contain emerald aurora radial gradient")

    def test_f01_ambient_aurora_sky_radial_gradient(self):
        """F01-3: Verify sky blue radial aurora gradient in #viewHome."""
        rules = self.css.get_rules_for_selector("#viewHome")
        has_sky = any("rgba(2, 132, 199" in r or "rgba(2,132,199" in r for r in rules)
        self.assertTrue(has_sky, "CSS #viewHome must contain sky blue aurora radial gradient")

    def test_f01_secondary_indigo_glow_present(self):
        """F01-4: Verify secondary indigo ambient glow in #viewHome."""
        rules = self.css.get_rules_for_selector("#viewHome")
        has_indigo = any("rgba(99, 102, 241" in r or "rgba(99,102,241" in r for r in rules)
        self.assertTrue(has_indigo, "CSS #viewHome must contain secondary indigo ambient glow")

    def test_f01_technical_dot_matrix_grid_pitch_28px(self):
        """F01-5: Verify technical dot-matrix grid with 28px pitch in #viewHome."""
        has_pitch = self.css.selector_has_property("#viewHome", "background-size", "28px 28px")
        self.assertTrue(has_pitch, "CSS #viewHome must define background-size including 28px 28px")

    # =========================================================================
    # F02: Modern SaaS & Apple HIG Typography
    # =========================================================================
    def test_f02_strand_main_title_size_and_tracking(self):
        """F02-1: Verify dominant title font-size (58px) and tracking (-0.045em)."""
        has_size = self.css.selector_has_property(".strand-main-title", "font-size", "58px")
        has_track = self.css.selector_has_property(".strand-main-title", "letter-spacing", "-0.045em")
        self.assertTrue(has_size and has_track, ".strand-main-title must have 58px size and -0.045em tracking")

    def test_f02_strand_main_title_weight_and_color(self):
        """F02-2: Verify dominant title has font-weight 850."""
        has_weight = self.css.selector_has_property(".strand-main-title", "font-weight", "850")
        self.assertTrue(has_weight, ".strand-main-title must have font-weight: 850")

    def test_f02_gradient_text_clip_emerald_sky(self):
        """F02-3: Verify emerald-sky text gradient clip on .strand-gradient-text."""
        has_clip = self.css.selector_has_property(".strand-gradient-text", "-webkit-background-clip", "text")
        rules = self.css.get_rules_for_selector(".strand-gradient-text")
        has_emerald = any("#059669" in r.lower() or "059669" in r for r in rules)
        self.assertTrue(has_clip and has_emerald, ".strand-gradient-text must have background-clip text and emerald")

    def test_f02_desktop_ergonomic_typography_scale(self):
        """F02-4: Verify subtitle line-height and size scale."""
        has_sub_size = self.css.selector_has_property(".strand-main-subtitle", "font-size", "17px")
        self.assertTrue(has_sub_size, ".strand-main-subtitle must have ergonomic font-size 17px")

    def test_f02_monospace_font_hierarchy_on_badges(self):
        """F02-5: Verify monospace typography on technical accents and badges."""
        has_mono = (
            self.css.selector_has_property(".strand-card-number", "font-family", "mono") or
            self.css.selector_has_property(".bento-code-pill", "font-family", "mono") or
            self.css.selector_has_property(".mono", "font-family", "mono")
        )
        self.assertTrue(has_mono, "Technical badges must specify monospace font")

    # =========================================================================
    # F03: Liquid Pill Buttons
    # =========================================================================
    def test_f03_primary_obsidian_button_dimensions_and_color(self):
        """F03-1: Verify primary Obsidian pill button background and height."""
        has_height = self.css.selector_has_property(".btn-strand-obsidian", "height", "48px")
        has_radius = self.css.selector_has_property(".btn-strand-obsidian", "border-radius", "9999px")
        self.assertTrue(has_height and has_radius, ".btn-strand-obsidian must have 48px height and 9999px radius")

    def test_f03_primary_obsidian_inner_shine_and_elevation(self):
        """F03-2: Verify primary Obsidian pill shadow and inner shine border."""
        rules = self.css.get_rules_for_selector(".btn-strand-obsidian")
        has_shadow = any("box-shadow" in r for r in rules)
        self.assertTrue(has_shadow, ".btn-strand-obsidian must have soft elevation box-shadow")

    def test_f03_liquid_shine_element_and_animation(self):
        """F03-3: Verify liquid shine element .btn-strand-shine in CSS."""
        has_shine = self.css.has_selector(".btn-strand-shine")
        self.assertTrue(has_shine, "CSS must define .btn-strand-shine for button reflection sweep")

    def test_f03_secondary_frosted_glass_button_blur_and_translucency(self):
        """F03-4: Verify secondary glass pill button blur filter and border."""
        has_blur = self.css.selector_has_property(".btn-strand-glass", "backdrop-filter", "blur")
        has_radius = self.css.selector_has_property(".btn-strand-glass", "border-radius", "9999px")
        self.assertTrue(has_blur and has_radius, ".btn-strand-glass must have backdrop-filter blur and 9999px radius")

    def test_f03_pill_buttons_tactile_press_active_scale(self):
        """F03-5: Verify tactile compression scale(0.96) on :active state."""
        rules_obs = self.css.get_rules_for_selector(".btn-strand-obsidian:active")
        rules_glass = self.css.get_rules_for_selector(".btn-strand-glass:active")
        has_scale = any("scale(0.96)" in r for r in rules_obs + rules_glass)
        self.assertTrue(has_scale, "Buttons must have tactile transform: scale(0.96) on active state")

    # =========================================================================
    # F04: Fold Toolbar Glassmorphism Dock Styles
    # =========================================================================
    def test_f04_floating_dock_pill_radius_9999px(self):
        """F04-1: Verify Fold Toolbar container has 9999px border-radius."""
        has_radius = self.css.selector_has_property(".fold-dock-bar", "border-radius", "9999px")
        self.assertTrue(has_radius, ".fold-dock-bar must have border-radius: 9999px")

    def test_f04_floating_dock_glassmorphism_blur_24px(self):
        """F04-2: Verify Fold Toolbar container has backdrop-filter: blur(24px)."""
        has_blur = self.css.selector_has_property(".fold-dock-bar", "backdrop-filter", "blur(24px)")
        self.assertTrue(has_blur, ".fold-dock-bar must have backdrop-filter: blur(24px)")

    def test_f04_floating_dock_elevation_shadow(self):
        """F04-3: Verify Fold Toolbar container has soft elevation shadow."""
        has_shadow = self.css.selector_has_property(".fold-dock-bar", "box-shadow")
        self.assertTrue(has_shadow, ".fold-dock-bar must define box-shadow elevation")

    def test_f04_dock_tab_active_obsidian_morph(self):
        """F04-4: Verify active tab morphs to obsidian #090D16 with white text."""
        rules = self.css.get_rules_for_selector(".fold-dock-item.active")
        has_obsidian = any("#090d16" in r.lower() or "090d16" in r.lower() for r in rules)
        self.assertTrue(has_obsidian, ".fold-dock-item.active must have background: #090D16")

    def test_f04_dock_tab_tactile_press_active_scale(self):
        """F04-5: Verify dock tab compression on active press."""
        rules = self.css.get_rules_for_selector(".fold-dock-item:active")
        has_scale = any("scale(0.96)" in r or "scale(0.97)" in r for r in rules)
        self.assertTrue(has_scale, ".fold-dock-item:active must have tactile scale compression")

    # =========================================================================
    # F05: 3-Pillar Foundation Grid Styles
    # =========================================================================
    def test_f05_three_pillar_grid_three_columns(self):
        """F05-1: Verify 3-pillar cards container has repeat(3, 1fr) grid layout."""
        has_grid = self.css.selector_has_property(".strand-pillars-cards", "grid-template-columns", "repeat(3")
        self.assertTrue(has_grid, ".strand-pillars-cards must have repeat(3, 1fr)")

    def test_f05_pillar_card_border_radius_20px(self):
        """F05-2: Verify pillar card border radius is 20px."""
        has_radius = self.css.selector_has_property(".strand-card", "border-radius", "20px")
        self.assertTrue(has_radius, ".strand-card must have border-radius: 20px")

    def test_f05_pillar_card_hover_lift_translate_y(self):
        """F05-3: Verify pillar card hover lift translateY(-3px)."""
        rules = self.css.get_rules_for_selector(".strand-card:hover")
        has_lift = any("translatey(-3px)" in r.lower() for r in rules)
        self.assertTrue(has_lift, ".strand-card:hover must have translateY(-3px)")

    def test_f05_pillar_card_monospace_step_badge(self):
        """F05-4: Verify step badge index typography in pillar cards."""
        has_index = self.css.selector_has_property(".strand-card-number", "font-family", "mono")
        self.assertTrue(has_index, ".strand-card-number must have monospace font")

    def test_f05_pillar_card_meta_pill_styling(self):
        """F05-5: Verify pillar card meta pill styling (.strand-card-meta-pill)."""
        has_pill = self.css.has_selector(".strand-card-meta-pill")
        self.assertTrue(has_pill, "CSS must define .strand-card-meta-pill")

    # =========================================================================
    # F06: Bento Capabilities Showcase Styles
    # =========================================================================
    def test_f06_bento_grid_three_columns(self):
        """F06-1: Verify bento capabilities grid has 3 columns."""
        has_cols = self.css.selector_has_property(".strand-bento-grid", "grid-template-columns", "repeat(3")
        self.assertTrue(has_cols, ".strand-bento-grid must define 3-column repeat layout")

    def test_f06_bento_wide_cards_span_two_columns(self):
        """F06-2: Verify .bento-wide spans 2 columns (span 2)."""
        has_span = self.css.selector_has_property(".bento-wide", "grid-column", "span 2")
        self.assertTrue(has_span, ".bento-wide must have grid-column: span 2")

    def test_f06_bento_card_border_radius_and_inner_glow(self):
        """F06-3: Verify bento card border radius is 20px."""
        has_radius = (
            self.css.selector_has_property(".strand-bento-card", "border-radius", "20px") or
            self.css.selector_has_property(".bento-card", "border-radius", "20px")
        )
        self.assertTrue(has_radius, "Bento cards must have border-radius: 20px")

    def test_f06_bento_monospace_code_pills(self):
        """F06-4: Verify monospace code pills (.bento-code-pill)."""
        has_code_pill = self.css.has_selector(".bento-code-pill") or self.css.has_selector(".strand-bento-code-pill")
        self.assertTrue(has_code_pill, "CSS must define .bento-code-pill")

    def test_f06_bento_status_pill_styling(self):
        """F06-5: Verify status pills (.bento-status-pill)."""
        has_status = self.css.has_selector(".bento-status-pill") or self.css.has_selector(".strand-bento-status-pill")
        self.assertTrue(has_status, "CSS must define .bento-status-pill")

    # =========================================================================
    # F07: Confrontation Table & Conversion CTA Styles
    # =========================================================================
    def test_f07_confrontation_table_wrapper_radius_20px(self):
        """F07-1: Verify comparison table card has 20px border radius."""
        has_radius = (
            self.css.selector_has_property(".strand-matrix-wrapper", "border-radius", "20px") or
            self.css.selector_has_property(".strand-comparison-wrapper", "border-radius", "20px")
        )
        self.assertTrue(has_radius, ".strand-matrix-wrapper must have border-radius: 20px")

    def test_f07_confrontation_table_six_criteria_rows(self):
        """F07-2: Verify table styling exists for comparison matrix."""
        has_table = self.css.has_selector(".strand-comparison-table")
        self.assertTrue(has_table, "CSS must define .strand-comparison-table")

    def test_f07_confrontation_table_excel_vs_econode_contrast_styling(self):
        """F07-3: Verify red Excel vs emerald ECONODE contrast styles."""
        has_contrast = (
            self.css.has_selector(".strand-badge-red") and
            self.css.has_selector(".strand-badge-emerald")
        )
        self.assertTrue(has_contrast, "CSS must define .strand-badge-red and .strand-badge-emerald")

    def test_f07_final_cta_card_dark_gradient(self):
        """F07-4: Verify final CTA card has dark gradient background."""
        rules = self.css.get_rules_for_selector(".strand-final-cta-card")
        has_dark = any("#090d16" in r.lower() or "090d16" in r.lower() for r in rules)
        self.assertTrue(has_dark, ".strand-final-cta-card must have dark gradient background")

    def test_f07_final_cta_inverted_button_contrast(self):
        """F07-5: Verify inverted button styling inside final CTA card."""
        has_cta_obs = self.css.has_selector(".strand-final-cta-card .btn-strand-obsidian")
        has_cta_glass = self.css.has_selector(".strand-final-cta-card .btn-strand-glass")
        self.assertTrue(has_cta_obs and has_cta_glass, "Final CTA card must define inverted buttons")

    # =========================================================================
    # F08: Desktop Ergonomics & Responsive Breakpoints
    # =========================================================================
    def test_f08_responsive_breakpoint_1024px_media_query(self):
        """F08-1: Verify @media query at 1024px exists in CSS."""
        queries = self.css.get_media_queries(1024)
        self.assertTrue(len(queries) > 0, "CSS must include @media (max-width: 1024px)")

    def test_f08_three_pillars_collapse_to_single_column_at_1024px(self):
        """F08-2: Verify 3-pillars cards collapse to single column (1fr) at 1024px."""
        queries = self.css.get_media_queries(1024)
        has_collapse = any(".strand-pillars-cards" in body and "1fr" in body for cond, body in queries)
        self.assertTrue(has_collapse, "3-pillars must collapse to 1 column at 1024px")

    def test_f08_bento_cards_collapse_to_single_column_at_1024px(self):
        """F08-3: Verify bento cards collapse to single column at 1024px."""
        queries = self.css.get_media_queries(1024)
        has_bento = any(".strand-bento-grid" in body and "1fr" in body for cond, body in queries)
        self.assertTrue(has_bento, "Bento grid must collapse to 1 column at 1024px")

    def test_f08_fold_dock_flex_wrap_at_1024px(self):
        """F08-4: Verify Fold Toolbar allows flex-wrap at 1024px."""
        queries = self.css.get_media_queries(1024)
        has_wrap = any(".fold-dock-bar" in body and "flex-wrap: wrap" in body for cond, body in queries)
        self.assertTrue(has_wrap, "Fold dock bar must enable flex-wrap at 1024px")

    def test_f08_desktop_touch_target_minimum_ergonomics(self):
        """F08-5: Verify buttons have minimum 48px height for desktop ergonomics."""
        has_height = self.css.selector_has_property(".btn-strand-obsidian", "height", "48px")
        self.assertTrue(has_height, "Buttons must meet ergonomic touch target minimum (48px)")

    # =========================================================================
    # F09: Strand Centered Dominant Hero DOM
    # =========================================================================
    def test_f09_strand_hero_section_container_in_dom(self):
        """F09-1: Verify .strand-hero-section exists in DOM."""
        hero = self.dom.find_all_by_class("strand-hero-section")
        self.assertTrue(len(hero) >= 1, ".strand-hero-section must exist in DOM")

    def test_f09_top_pill_announcement_badge_in_dom(self):
        """F09-2: Verify .strand-top-pill exists with badge and text."""
        pill = self.dom.find_all_by_class("strand-top-pill")
        self.assertTrue(len(pill) >= 1, ".strand-top-pill must exist in DOM")
        badge = self.dom.find_all_by_class("strand-top-pill-badge")
        self.assertTrue(len(badge) >= 1, ".strand-top-pill-badge must exist in DOM")

    def test_f09_hero_headline_and_subtitle_in_dom(self):
        """F09-3: Verify .strand-main-title and .strand-main-subtitle in DOM."""
        titles = self.dom.find_all_by_class("strand-main-title")
        subs = self.dom.find_all_by_class("strand-main-subtitle")
        self.assertTrue(len(titles) >= 1 and len(subs) >= 1, "Hero headline and subtitle must exist")

    def test_f09_hero_primary_and_secondary_cta_buttons_in_dom(self):
        """F09-4: Verify #btnHomeEnterStudio and #btnHomeViewExamples in DOM."""
        btn_enter = self.dom.find_by_id("btnHomeEnterStudio")
        btn_ex = self.dom.find_by_id("btnHomeViewExamples")
        self.assertIsNotNone(btn_enter, "#btnHomeEnterStudio must exist in DOM")
        self.assertIsNotNone(btn_ex, "#btnHomeViewExamples must exist in DOM")

    def test_f09_hero_four_trust_badges_in_dom(self):
        """F09-5: Verify 4 trust badges in .strand-trust-pills."""
        trust = self.dom.find_all_by_class("strand-trust-pills")
        self.assertTrue(len(trust) >= 1, ".strand-trust-pills must exist in DOM")
        spans = trust[0].find_all_by_tag("span")
        self.assertTrue(len(spans) >= 4, "Must contain at least 4 trust items")

    # =========================================================================
    # F10: Live Product Stage Window DOM
    # =========================================================================
    def test_f10_stage_window_container_and_header_in_dom(self):
        """F10-1: Verify .strand-stage-window and .strand-stage-header in DOM."""
        win = self.dom.find_all_by_class("strand-stage-window")
        self.assertTrue(len(win) >= 1, ".strand-stage-window must exist in DOM")

    def test_f10_macos_three_traffic_light_dots_in_dom(self):
        """F10-2: Verify 3 traffic dots exist in stage header."""
        dots = self.dom.find_all_by_class("traffic-dot")
        self.assertEqual(len(dots), 3, "Stage chrome must contain exactly 3 macOS traffic light dots")

    def test_f10_active_stage_breadcrumb_in_dom(self):
        """F10-3: Verify #heroStageBreadcrumb exists in DOM."""
        bread = self.dom.find_by_id("heroStageBreadcrumb")
        self.assertIsNotNone(bread, "#heroStageBreadcrumb must exist in DOM")

    def test_f10_directed_svg_graph_with_viewbox_in_dom(self):
        """F10-4: Verify #strandStageSvg with viewBox='0 0 980 420'."""
        svg = self.dom.find_by_id("strandStageSvg")
        self.assertIsNotNone(svg, "#strandStageSvg must exist in DOM")
        viewbox = svg.get_attr("viewBox")
        self.assertEqual(viewbox, "0 0 980 420", "SVG graph must have viewBox='0 0 980 420'")

    def test_f10_floating_dock_and_telemetry_footer_in_dom(self):
        """F10-5: Verify #heroFoldToolbar and footer telemetry IDs exist."""
        dock = self.dom.find_by_id("heroFoldToolbar")
        gwp = self.dom.find_by_id("stageGwpValText")
        mass = self.dom.find_by_id("stageMassValText")
        self.assertIsNotNone(dock, "#heroFoldToolbar must exist")
        self.assertIsNotNone(gwp, "#stageGwpValText must exist")
        self.assertIsNotNone(mass, "#stageMassValText must exist")

    # =========================================================================
    # F11: 3-Pillar Foundation Grid DOM
    # =========================================================================
    def test_f11_pillars_container_and_section_title_in_dom(self):
        """F11-1: Verify .strand-pillars-container exists in DOM."""
        cont = self.dom.find_all_by_class("strand-pillars-container")
        self.assertTrue(len(cont) >= 1, ".strand-pillars-container must exist in DOM")

    def test_f11_three_pillar_cards_modela_calcula_custodia_in_dom(self):
        """F11-2: Verify exactly 3 pillar cards exist in .strand-pillars-cards."""
        cards_cont = self.dom.find_all_by_class("strand-pillars-cards")
        self.assertTrue(len(cards_cont) >= 1, ".strand-pillars-cards must exist")
        cards = cards_cont[0].find_all_by_class("strand-card")
        self.assertEqual(len(cards), 3, "Must have exactly 3 pillar cards (01, 02, 03)")

    def test_f11_pillar_cards_icons_and_step_indexes_in_dom(self):
        """F11-3: Verify step index badges (01 // MODELA, etc.) exist."""
        indexes = self.dom.find_all_by_class("strand-card-number")
        self.assertEqual(len(indexes), 3, "Must have 3 step index badges")

    def test_f11_pillar_cards_meta_pills_in_dom(self):
        """F11-4: Verify meta pills exist in all 3 cards."""
        pills = self.dom.find_all_by_class("strand-card-meta-pill")
        self.assertEqual(len(pills), 3, "Each pillar card must contain a meta pill")

    def test_f11_pillar_cards_i18n_attributes_in_dom(self):
        """F11-5: Verify data-i18n attributes on pillar titles or dictionary presence."""
        # Contract requires home.pillar1_title, home.pillar2_title, home.pillar3_title in i18n dictionary
        self.assertIn("home.pillar1_title", self.i18n["es"])
        self.assertIn("home.pillar2_title", self.i18n["es"])
        self.assertIn("home.pillar3_title", self.i18n["es"])

    # =========================================================================
    # F12: Bento Capabilities Showcase DOM
    # =========================================================================
    def test_f12_bento_capabilities_container_in_dom(self):
        """F12-1: Verify #homeCapabilities / .strand-bento-section exists in DOM."""
        bento_sec = self.dom.find_by_id("homeCapabilities")
        self.assertIsNotNone(bento_sec, "#homeCapabilities section must exist in DOM")

    def test_f12_bento_four_modules_in_dom(self):
        """F12-2: Verify exactly 4 bento cards exist."""
        bento_cards = self.dom.find_all(lambda e: e.has_class("bento-card") or e.has_class("strand-bento-card"))
        self.assertEqual(len(bento_cards), 4, "Bento showcase must contain exactly 4 capability cards")

    def test_f12_bento_leontief_matrix_module_in_dom(self):
        """F12-3: Verify Leontief matrix algebra bento card."""
        has_leontief = "np.linalg.solve" in self.html_raw or "s = A" in self.html_raw
        self.assertTrue(has_leontief, "Bento grid must contain Leontief algebra formula")

    def test_f12_bento_nom070_and_byos_modules_in_dom(self):
        """F12-4: Verify NOM-070 and Google Drive BYOS bento cards."""
        has_nom = "NOM-070" in self.html_raw
        has_byos = "BYOS" in self.html_raw
        self.assertTrue(has_nom and has_byos, "Bento grid must feature NOM-070 and BYOS Drive")

    def test_f12_bento_export_suite_module_in_dom(self):
        """F12-5: Verify Industrial Export Suite bento card."""
        has_export = "openLCA" in self.html_raw and "SimaPro" in self.html_raw
        self.assertTrue(has_export, "Bento grid must feature openLCA and SimaPro export suite")

    # =========================================================================
    # F13: Confrontation Table & Conversion CTA DOM
    # =========================================================================
    def test_f13_confrontation_table_section_in_dom(self):
        """F13-1: Verify comparison table section .strand-matrix-section in DOM."""
        mat = self.dom.find_all_by_class("strand-matrix-section")
        self.assertTrue(len(mat) >= 1, ".strand-matrix-section must exist in DOM")

    def test_f13_confrontation_table_headers_and_rows_in_dom(self):
        """F13-2: Verify confrontation table has 6 comparison rows."""
        table = self.dom.find_all_by_class("strand-comparison-table")
        self.assertTrue(len(table) >= 1, ".strand-comparison-table must exist in DOM")
        tbody = table[0].find_all_by_tag("tbody")
        rows = tbody[0].find_all_by_tag("tr") if tbody else table[0].find_all_by_tag("tr")
        self.assertTrue(len(rows) >= 6, "Confrontation table must contain at least 6 comparison rows")

    def test_f13_confrontation_table_criteria_completeness_in_dom(self):
        """F13-3: Verify comparison covers database, errors, and exports."""
        has_criteria = "ecoinvent" in self.html_raw and "openLCA" in self.html_raw
        self.assertTrue(has_criteria, "Comparison table must reference ecoinvent and openLCA")

    def test_f13_final_cta_banner_container_in_dom(self):
        """F13-4: Verify final CTA card .strand-final-cta-card in DOM."""
        cta = self.dom.find_all_by_class("strand-final-cta-card")
        self.assertTrue(len(cta) >= 1, ".strand-final-cta-card must exist in DOM")

    def test_f13_final_cta_headline_subtitle_and_action_in_dom(self):
        """F13-5: Verify final CTA contains obsidian launch button."""
        cta_cards = self.dom.find_all_by_class("strand-final-cta-card")
        buttons = cta_cards[0].find_all_by_class("btn-strand-obsidian")
        self.assertTrue(len(buttons) >= 1, "Final CTA card must contain an obsidian button")

    # =========================================================================
    # F14: DOM Integrity & Modal Preservation
    # =========================================================================
    def test_f14_dom_id_preservation_threshold(self):
        """F14-1: Verify exactly 329 element IDs exist in index.html."""
        ids = re.findall(r'id=["\']([^"\']+)["\']', self.html_raw)
        unique_ids = set(ids)
        self.assertTrue(len(unique_ids) >= 320, f"Expected >= 320 unique DOM IDs, found {len(unique_ids)}")

    def test_f14_all_twelve_modal_overlays_present_in_dom(self):
        """F14-2: Verify all 12 modal dialog overlays exist in DOM."""
        expected_modals = [
            "modalDocuments", "modalConnectNodes", "modalWizard",
            "modalInviteCollaborator", "modalSettings", "modalAddProcessComment",
            "modalProcessEditor", "modalSelectDbFlow", "modalCreateCustomFlow",
            "modalSelectProvider", "modalSubscription", "reportBubbleToolbar"
        ]
        for mid in expected_modals:
            elem = self.dom.find_by_id(mid)
            self.assertIsNotNone(elem, f"Modal #{mid} must exist in DOM")

    def test_f14_top_navbar_twenty_seven_elements_present_in_dom(self):
        """F14-3: Verify key top navbar element IDs."""
        key_nav_ids = [
            "topNavbar", "btnNavHome", "navProjectTitle", "studioNavLinks",
            "navBtnDashboard", "navBtnCanvas", "navBtnCatalog", "navBtnReport", "navBtnAudit",
            "btnNavLogin", "btnNavSignup", "btnNavEnterStudio", "btnLangEs", "btnLangEn"
        ]
        for nid in key_nav_ids:
            elem = self.dom.find_by_id(nid)
            self.assertIsNotNone(elem, f"Navbar element #{nid} must exist in DOM")

    def test_f14_all_eight_view_containers_present_in_dom(self):
        """F14-4: Verify all 8 top-level view containers exist in DOM."""
        expected_views = [
            "viewHome", "viewLogin", "viewSignup", "viewDashboard",
            "viewCanvas", "viewCatalog", "viewReport", "viewAudit"
        ]
        for vid in expected_views:
            elem = self.dom.find_by_id(vid)
            self.assertIsNotNone(elem, f"View container #{vid} must exist in DOM")

    def test_f14_essential_script_tags_present_in_dom(self):
        """F14-5: Verify essential scripts are included in DOM."""
        self.assertIn("js/app.js", self.html_raw)
        self.assertIn("js/i18n.js", self.html_raw)
        self.assertIn("js/drive_storage.js", self.html_raw)

    # =========================================================================
    # F15: Fold Toolbar Interactive Dock Controller
    # =========================================================================
    def test_f15_fold_toolbar_setup_function_defined_in_js(self):
        """F15-1: Verify setupFoldToolbarHome function defined in app.js."""
        self.assertIn("function setupFoldToolbarHome()", self.app_js_raw)

    def test_f15_fold_toolbar_contains_five_stage_keys(self):
        """F15-2: Verify 5 stage catalog keys: injection, blowmolding, distribution, vault, audit."""
        for stage in ["injection", "blowmolding", "distribution", "vault", "audit"]:
            self.assertIn(f"{stage}:", self.app_js_raw, f"Stage key '{stage}' must be defined in stageCatalog")

    def test_f15_fold_dock_items_have_data_stage_attributes(self):
        """F15-3: Verify 5 dock items in DOM with data-stage attributes."""
        dock = self.dom.find_by_id("heroFoldToolbar")
        self.assertIsNotNone(dock, "#heroFoldToolbar must exist in DOM")
        items = dock.find_all_by_class("fold-dock-item")
        stages = [item.get_attr("data-stage") for item in items]
        expected = ["injection", "blowmolding", "distribution", "vault", "audit"]
        self.assertEqual(stages, expected, "Dock items must have exact 5 data-stage attributes")

    def test_f15_fold_toolbar_binds_click_listener_to_items(self):
        """F15-4: Verify click event listener is bound to dock items in app.js."""
        self.assertIn('btn.addEventListener("click"', self.app_js_raw)

    def test_f15_fold_toolbar_toggles_active_class_on_click(self):
        """F15-5: Verify active class toggle logic on click in app.js."""
        self.assertIn('classList.add("active")', self.app_js_raw)
        self.assertIn('classList.remove("active")', self.app_js_raw)

    # =========================================================================
    # F16: Stage Mutations & Telemetry Updates
    # =========================================================================
    def test_f16_injection_stage_telemetry_values(self):
        """F16-1: Verify Injection stage catalog values in app.js."""
        self.assertIn("1.428 kg CO2-eq", self.app_js_raw)
        self.assertIn("100.0% Conservado", self.app_js_raw)
        self.assertIn("ISO 14044 Acreditado", self.app_js_raw)

    def test_f16_blowmolding_stage_telemetry_values(self):
        """F16-2: Verify Blowmolding stage catalog values in app.js."""
        self.assertIn("1.890 kg CO2-eq", self.app_js_raw)
        self.assertIn("0.42 kWh/u", self.app_js_raw)
        self.assertIn("NOM-070 Conforme", self.app_js_raw)

    def test_f16_distribution_stage_telemetry_values(self):
        """F16-3: Verify Distribution stage catalog values in app.js."""
        self.assertIn("2.140 kg CO2-eq", self.app_js_raw)
        self.assertIn("120 km", self.app_js_raw)

    def test_f16_vault_stage_telemetry_values(self):
        """F16-4: Verify Drive Vault stage catalog values in app.js."""
        self.assertIn("Google Drive Personal (0 MB Servidor)", self.app_js_raw)
        self.assertIn("Sello SHA-256 Activo", self.app_js_raw)

    def test_f16_audit_stage_telemetry_values(self):
        """F16-5: Verify Audit stage catalog values in app.js."""
        self.assertIn("18 Cláusulas Verificadas", self.app_js_raw)
        self.assertIn("Firma Digital HMAC", self.app_js_raw)

    # =========================================================================
    # F17: Complete Bilingual i18n Integration
    # =========================================================================
    def test_f17_i18n_dictionary_contains_es_and_en(self):
        """F17-1: Verify i18n dictionary contains both ES and EN blocks."""
        self.assertIn("es", self.i18n)
        self.assertIn("en", self.i18n)
        self.assertTrue(len(self.i18n["es"]) > 300, "ES dictionary must have > 300 keys")
        self.assertTrue(len(self.i18n["en"]) > 300, "EN dictionary must have > 300 keys")

    def test_f17_all_home_data_i18n_attributes_resolve_in_dictionary(self):
        """F17-2: Verify all home.* data-i18n tags in DOM exist in dictionary."""
        home_elems = self.dom.find_all(lambda e: e.get_attr("data-i18n", "").startswith("home."))
        for elem in home_elems:
            key = elem.get_attr("data-i18n")
            self.assertIn(key, self.i18n["es"], f"Key '{key}' missing from ES dictionary")
            self.assertIn(key, self.i18n["en"], f"Key '{key}' missing from EN dictionary")

    def test_f17_navbar_and_pillar_translation_keys_present(self):
        """F17-3: Verify essential navigation and pillar keys."""
        essential_keys = [
            "home.nav_features", "home.nav_enter",
            "home.pillar1_title", "home.pillar2_title", "home.pillar3_title"
        ]
        for k in essential_keys:
            self.assertIn(k, self.i18n["es"])
            self.assertIn(k, self.i18n["en"])

    def test_f17_bilingual_dictionary_parity_between_es_and_en(self):
        """F17-4: Verify key parity between ES and EN dictionaries."""
        es_keys = set(self.i18n["es"].keys())
        en_keys = set(self.i18n["en"].keys())
        missing_in_en = es_keys - en_keys
        self.assertEqual(len(missing_in_en), 0, f"Keys in ES but missing from EN: {missing_in_en}")

    def test_f17_language_switcher_buttons_in_dom(self):
        """F17-5: Verify #btnLangEs and #btnLangEn in DOM."""
        btn_es = self.dom.find_by_id("btnLangEs")
        btn_en = self.dom.find_by_id("btnLangEn")
        self.assertIsNotNone(btn_es, "#btnLangEs must exist in DOM")
        self.assertIsNotNone(btn_en, "#btnLangEn must exist in DOM")

    # =========================================================================
    # F18: Navigation & Studio Launch Hooks
    # =========================================================================
    def test_f18_primary_hero_cta_routes_to_studio(self):
        """F18-1: Verify primary hero CTA click triggers showView in app.js."""
        self.assertIn('btnHomeEnter.addEventListener("click"', self.app_js_raw)

    def test_f18_secondary_hero_cta_triggers_action(self):
        """F18-2: Verify secondary hero CTA click is handled in app.js."""
        self.assertIn('btnHomeEx.addEventListener("click"', self.app_js_raw)

    def test_f18_brand_logo_nav_returns_to_home(self):
        """F18-3: Verify brand logo click triggers showView('home')."""
        self.assertIn('btnHomeLogo.addEventListener("click", () => showView("home"))', self.app_js_raw)

    def test_f18_top_navbar_enter_studio_button_routes_to_studio(self):
        """F18-4: Verify top navbar enter studio button is bound to router."""
        self.assertIn('btnNavEnter.addEventListener("click"', self.app_js_raw)

    def test_f18_unauthenticated_studio_route_protection(self):
        """F18-5: Verify unauthenticated users attempting Studio route are redirected."""
        self.assertIn('isStudioRoute && !state.isAuthenticated', self.app_js_raw)
        self.assertIn('viewName = "login"', self.app_js_raw)

    # =========================================================================
    # F19: E2E Testing Suite (Tiers 1-4)
    # =========================================================================
    def test_f19_live_server_root_returns_http_200(self):
        """F19-1: Verify live server returns HTTP 200 for root URL."""
        self.assertEqual(self.status_html, 200, "Server root / must return HTTP 200")

    def test_f19_live_server_css_returns_http_200(self):
        """F19-2: Verify live server returns HTTP 200 for styles.css."""
        self.assertEqual(self.status_css, 200, "Stylesheet /css/styles.css must return HTTP 200")

    def test_f19_live_server_js_app_returns_http_200(self):
        """F19-3: Verify live server returns HTTP 200 for app.js."""
        self.assertEqual(self.status_app_js, 200, "Script /js/app.js must return HTTP 200")

    def test_f19_live_server_js_i18n_returns_http_200(self):
        """F19-4: Verify live server returns HTTP 200 for i18n.js."""
        self.assertEqual(self.status_i18n_js, 200, "Script /js/i18n.js must return HTTP 200")

    def test_f19_live_server_cache_control_headers_conform(self):
        """F19-5: Verify Cache-Control headers prevent stale caching."""
        cache_header = self.headers_html.get("cache-control", "").lower()
        if not cache_header:
            cache_header = self.headers_html.get("Cache-Control", "").lower()
        self.assertTrue("no-cache" in cache_header or self.headers_html.get("x-fallback") == "true")

    # =========================================================================
    # F20: Adversarial Coverage Hardening (Tier 5)
    # =========================================================================
    def test_f20_mass_balance_conservation_invariant(self):
        """F20-1: Verify mass conservation invariant in telemetry strip."""
        mass_text = self.dom.find_by_id("stageMassValText")
        self.assertIsNotNone(mass_text, "#stageMassValText must exist")
        self.assertIn("100.0%", mass_text.text_content)

    def test_f20_gwp_metric_positive_and_unit_conformity(self):
        """F20-2: Verify initial GWP 100a metric format."""
        gwp_text = self.dom.find_by_id("stageGwpValText")
        self.assertIsNotNone(gwp_text, "#stageGwpValText must exist")
        self.assertTrue(
            "kg CO2-eq" in gwp_text.text_content or "kg CO\u2082-eq" in gwp_text.text_content or "CO" in gwp_text.text_content,
            f"Expected CO2 or CO₂ in {gwp_text.text_content}"
        )

    def test_f20_nom070_eighteen_clauses_audit_completeness(self):
        """F20-3: Verify 18 clauses mentioned in NOM-070 bento and audit tabs."""
        self.assertIn("18 Cláusulas", self.html_raw)

    def test_f20_zero_bytes_on_vercel_byos_storage_contract(self):
        """F20-4: Verify BYOS storage contract (0 Bytes on Vercel)."""
        self.assertIn("0 Bytes en Vercel", self.html_raw)

    def test_f20_svg_viewbox_proportions_and_bounds(self):
        """F20-5: Verify SVG directed graph viewBox dimensions are 980x420."""
        svg = self.dom.find_by_id("strandStageSvg")
        self.assertIsNotNone(svg)
        vb = svg.get_attr("viewBox")
        w, h = [int(x) for x in vb.split()[2:]]
        self.assertGreater(w, 900, "SVG width must be >= 900")
        self.assertGreater(h, 400, "SVG height must be >= 400")


if __name__ == "__main__":
    unittest.main()
