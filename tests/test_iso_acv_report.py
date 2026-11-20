"""
Test Suite: ISO 14040/14044 Dynamic LCA Report Verification (Chapters 1 to 6).
Ensures adherence to international LCA standards, bilingual i18n support,
correct PDF generation, and strict zero-emoji enforcement.
"""

import unittest
import os
import re
from econode_studio.infrastructure.database_adapter import get_active_db_connection, list_product_systems
from econode_studio.infrastructure.exporters_adapter import export_system_pdf_bytes

class TestIsoAcvReport(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.index_html_path = os.path.join(self.base_dir, "public", "index.html")
        self.i18n_js_path = os.path.join(self.base_dir, "public", "js", "i18n.js")
        self.app_js_path = os.path.join(self.base_dir, "public", "js", "app.js")
        self.exporters_path = os.path.join(self.base_dir, "econode_studio", "infrastructure", "exporters_adapter.py")

    def test_index_html_has_all_six_chapters(self):
        """Verify that Chapters 1 through 6 exist in index.html and Chapter 7 is omitted."""
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Check TOC Bar
        self.assertIn('id="reportTocBar"', html)
        self.assertIn('href="#sec-1-intro"', html)
        self.assertIn('href="#sec-2-goal-scope"', html)
        self.assertIn('href="#sec-3-lci"', html)
        self.assertIn('href="#sec-4-lcia"', html)
        self.assertIn('href="#sec-5-interpretation"', html)
        self.assertIn('href="#sec-6-conclusions"', html)

        # Check Chapter IDs
        self.assertIn('id="sec-1-intro"', html)
        self.assertIn('id="sec-2-goal-scope"', html)
        self.assertIn('id="sec-3-lci"', html)
        self.assertIn('id="sec-4-lcia"', html)
        self.assertIn('id="sec-5-interpretation"', html)
        self.assertIn('id="sec-6-conclusions"', html)

        # Check Chapter 7 is omitted
        self.assertNotIn('Non-Confidential Appendix', html)
        self.assertNotIn('sec-7-appendix', html)
        self.assertNotIn('7. Non-Confidential', html)

        # Check dynamic tables and badges
        self.assertIn('id="reportProcessesTable"', html)
        self.assertIn('id="reportLciTable"', html)
        self.assertIn('id="reportLciaResultsTable"', html)
        self.assertIn('id="reportContributionTable"', html)
        self.assertIn('id="reportCompletenessBadge"', html)
        self.assertIn('id="reportConsistencyBadge"', html)
        self.assertIn('id="reportSignOffCard"', html)

    def test_i18n_bilingual_coverage(self):
        """Verify that i18n dictionary contains bilingual keys for chapters 1 through 6."""
        with open(self.i18n_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        required_keys = [
            "report.toc_label",
            "report.ch1_nav",
            "report.ch2_nav",
            "report.ch3_nav",
            "report.ch4_nav",
            "report.ch5_nav",
            "report.ch6_nav",
            "report.ch1_title",
            "report.ch2_title",
            "report.ch3_title",
            "report.ch4_title",
            "report.ch5_title",
            "report.ch6_title"
        ]

        for k in required_keys:
            # Check key appears in both ES and EN blocks (at least twice)
            matches = js_content.count(f'"{k}"')
            self.assertGreaterEqual(matches, 2, f"Key {k} must exist in both Spanish and English blocks")

    def test_export_system_pdf_bytes_generates_all_six_chapters(self):
        """Verify that export_system_pdf_bytes produces valid PDF bytes containing the 6 chapters."""
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            sys_id = systems[0]["id"] if systems else 21
            pdf_bytes = export_system_pdf_bytes(conn, sys_id)
            self.assertIsInstance(pdf_bytes, bytes)
            self.assertGreater(len(pdf_bytes), 2000)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_zero_emojis_in_report_files(self):
        """Enforce strict zero emoji rule across all modified report files."""
        # Genuine Unicode Emojis (SMP emoji code points: faces, symbols, emoticons, pictographs)
        emoji_pattern = re.compile(
            "[\U0001F300-\U0001F64F"  # Symbols, emoticons
            "\U0001F680-\U0001F6FF"  # Transport and map symbols
            "\U0001F1E6-\U0001F1FF"  # Regional indicator symbols (flags)
            "\U0001F900-\U0001F9FF"  # Supplemental symbols & pictographs
            "\U0001FA70-\U0001FAFF"  # Symbols and pictographs extended-A
            "]+", flags=re.UNICODE
        )

        files_to_check = [
            self.index_html_path,
            self.i18n_js_path,
            self.app_js_path,
            self.exporters_path
        ]

        for filepath in files_to_check:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                matches = emoji_pattern.findall(content)
                self.assertEqual(matches, [], f"Found forbidden emoji in {os.path.basename(filepath)}: {matches}")

if __name__ == "__main__":
    unittest.main()
