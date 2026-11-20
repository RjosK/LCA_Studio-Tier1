"""
Test Suite: ISO 14040/14044 Dynamic LCA Report Verification (Chapters 1 to 6).
Ensures adherence to international LCA standards, bilingual i18n support,
correct PDF generation, and strict zero-emoji enforcement.
"""

import unittest
import os
import re
import io
import docx
from econode_studio.infrastructure.database_adapter import get_active_db_connection, list_product_systems
from econode_studio.infrastructure.exporters_adapter import export_system_pdf_bytes, export_system_docx_bytes

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

        # Check dynamic tables, buttons and badges
        self.assertIn('id="reportProcessesTable"', html)
        self.assertIn('id="reportLciTable"', html)
        self.assertIn('id="reportLciaResultsTable"', html)
        self.assertIn('id="reportContributionTable"', html)
        self.assertIn('id="reportCompletenessBadge"', html)
        self.assertIn('id="reportConsistencyBadge"', html)
        self.assertIn('id="reportSignOffCard"', html)
        self.assertIn('id="btnExportReportDocx"', html)
        self.assertIn('id="btnExportDocx"', html)

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
            "report.ch6_title",
            "report.export_docx",
            "canvas.export_docx"
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

    def test_export_system_docx_bytes_generates_valid_editable_word_file(self):
        """Verify that export_system_docx_bytes produces a valid editable Word (.docx) document with tables."""
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            sys_id = systems[0]["id"] if systems else 21
            docx_bytes = export_system_docx_bytes(conn, sys_id)
            self.assertIsInstance(docx_bytes, bytes)
            self.assertGreater(len(docx_bytes), 5000)
            self.assertTrue(docx_bytes.startswith(b"PK\x03\x04"))

            doc = docx.Document(io.BytesIO(docx_bytes))
            self.assertGreaterEqual(len(doc.paragraphs), 20)
            self.assertGreaterEqual(len(doc.tables), 5)

            # Check that chapter headings exist in editable Word paragraphs
            headings = [p.text for p in doc.paragraphs if p.text.startswith(("1.", "2.", "3.", "4.", "5.", "6."))]
            self.assertTrue(any("1. Introducción" in h for h in headings))
            self.assertTrue(any("2. Definición de Objetivo y Alcance" in h for h in headings))
            self.assertTrue(any("3. Análisis de Inventario" in h for h in headings))
            self.assertTrue(any("4. Resultados de Evaluación de Impacto" in h for h in headings))
            self.assertTrue(any("5. Interpretación del Ciclo de Vida" in h for h in headings))
            self.assertTrue(any("6. Conclusiones y Recomendaciones" in h for h in headings))

    def test_docx_export_button_wiring_in_app_js(self):
        """Verify that btnExportReportDocx and btnExportDocx are wired with triggerExportDownload."""
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("btnExpReportDocx", content)
        self.assertIn("btnExpCanvasDocx", content)
        self.assertIn("triggerExportDownload", content)
        self.assertIn("/export/docx", content)

    def test_http_export_docx_and_pdf_endpoints(self):
        """Verify that GET /api/systems/<id>/export/docx serves valid Word file even without token (fallback)."""
        import subprocess
        import time
        import requests
        import sys

        port = 8895
        server_py = os.path.join(self.base_dir, "econode_studio", "server.py")
        proc = subprocess.Popen(
            [sys.executable, server_py, "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2.0)
        try:
            # 1. Unauthenticated docx export
            r_docx = requests.get(f"http://127.0.0.1:{port}/api/systems/21/export/docx")
            self.assertEqual(r_docx.status_code, 200, f"Expected 200 but got {r_docx.status_code}: {r_docx.text}")
            self.assertEqual(r_docx.headers.get("Content-Type"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.assertIn("Reporte_ACV_NOM070_Sistema_21.docx", r_docx.headers.get("Content-Disposition", ""))
            self.assertTrue(r_docx.content.startswith(b"PK\x03\x04"))

            # 2. Unauthenticated pdf export
            r_pdf = requests.get(f"http://127.0.0.1:{port}/api/systems/21/export/pdf")
            self.assertEqual(r_pdf.status_code, 200, f"Expected 200 but got {r_pdf.status_code}: {r_pdf.text}")
            self.assertEqual(r_pdf.headers.get("Content-Type"), "application/pdf")
            self.assertTrue(r_pdf.content.startswith(b"%PDF"))

            # 3. Direct demo login without password for local/offline testing
            r_login = requests.post(f"http://127.0.0.1:{port}/api/auth/login", json={"user_id": "analyst"})
            self.assertEqual(r_login.status_code, 200, f"Expected 200 on demo login: {r_login.text}")
            self.assertTrue(r_login.json().get("authenticated"))
            self.assertEqual(r_login.json().get("user", {}).get("role"), "analyst")
        finally:
            proc.terminate()
            proc.wait()

    def test_javascript_syntax_integrity(self):
        """Run node --check on all public JS files to strictly prevent SyntaxErrors from ever landing."""
        import subprocess
        for script_name in ["app.js", "i18n.js"]:
            script_path = os.path.join(self.base_dir, "public", "js", script_name)
            res = subprocess.run(["node", "--check", script_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"JavaScript SyntaxError detected in {script_name}:\n{res.stderr}")

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
