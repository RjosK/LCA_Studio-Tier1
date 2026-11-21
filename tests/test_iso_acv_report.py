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
        """Verify that export_system_pdf_bytes produces valid PDF bytes in both ES and EN."""
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            sys_id = systems[0]["id"] if systems else 21
            # ES
            pdf_bytes_es = export_system_pdf_bytes(conn, sys_id, lang="es")
            self.assertIsInstance(pdf_bytes_es, bytes)
            self.assertGreater(len(pdf_bytes_es), 2000)
            self.assertTrue(pdf_bytes_es.startswith(b"%PDF"))
            # EN
            pdf_bytes_en = export_system_pdf_bytes(conn, sys_id, lang="en")
            self.assertIsInstance(pdf_bytes_en, bytes)
            self.assertGreater(len(pdf_bytes_en), 2000)
            self.assertTrue(pdf_bytes_en.startswith(b"%PDF"))

    def test_export_system_docx_bytes_generates_valid_editable_word_file(self):
        """Verify that export_system_docx_bytes produces valid editable Word (.docx) documents in both ES and EN."""
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            sys_id = systems[0]["id"] if systems else 21

            # 1. Spanish export (default)
            docx_bytes_es = export_system_docx_bytes(conn, sys_id, lang="es")
            self.assertIsInstance(docx_bytes_es, bytes)
            self.assertGreater(len(docx_bytes_es), 5000)
            self.assertTrue(docx_bytes_es.startswith(b"PK\x03\x04"))

            doc_es = docx.Document(io.BytesIO(docx_bytes_es))
            self.assertGreaterEqual(len(doc_es.paragraphs), 20)
            self.assertGreaterEqual(len(doc_es.tables), 5)

            headings_es = [p.text for p in doc_es.paragraphs if p.text.startswith(("1.", "2.", "3.", "4.", "5.", "6."))]
            self.assertTrue(any("1. Introducción" in h for h in headings_es))
            self.assertTrue(any("2. Definición de Objetivo y Alcance" in h for h in headings_es))
            self.assertTrue(any("3. Análisis de Inventario" in h for h in headings_es))
            self.assertTrue(any("4. Resultados de Evaluación de Impacto" in h for h in headings_es))
            self.assertTrue(any("5. Interpretación del Ciclo de Vida" in h for h in headings_es))
            self.assertTrue(any("6. Conclusiones y Recomendaciones" in h for h in headings_es))

            # 2. English export
            docx_bytes_en = export_system_docx_bytes(conn, sys_id, lang="en")
            self.assertIsInstance(docx_bytes_en, bytes)
            self.assertGreater(len(docx_bytes_en), 5000)
            self.assertTrue(docx_bytes_en.startswith(b"PK\x03\x04"))

            doc_en = docx.Document(io.BytesIO(docx_bytes_en))
            self.assertGreaterEqual(len(doc_en.paragraphs), 20)
            self.assertGreaterEqual(len(doc_en.tables), 5)

            headings_en = [p.text for p in doc_en.paragraphs if p.text.startswith(("1.", "2.", "3.", "4.", "5.", "6."))]
            self.assertTrue(any("1. Introduction" in h for h in headings_en))
            self.assertTrue(any("2. Goal & Scope Definition" in h for h in headings_en))
            self.assertTrue(any("3. Life Cycle Inventory Analysis" in h for h in headings_en))
            self.assertTrue(any("4. Life Cycle Impact Assessment Results" in h for h in headings_en))
            self.assertTrue(any("5. Life Cycle Interpretation" in h for h in headings_en))
            self.assertTrue(any("6. Conclusions and Recommendations" in h for h in headings_en))

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
            # 1. Unauthenticated docx export (ES default)
            r_docx = requests.get(f"http://127.0.0.1:{port}/api/systems/21/export/docx")
            self.assertEqual(r_docx.status_code, 200, f"Expected 200 but got {r_docx.status_code}: {r_docx.text}")
            self.assertEqual(r_docx.headers.get("Content-Type"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.assertTrue(any(sub in r_docx.headers.get("Content-Disposition", "") for sub in ("Reporte_ACV_NOM070_Sistema_21.docx", "Reporte_ACV_NOM070_Sistema_21_ES.docx")))
            self.assertTrue(r_docx.content.startswith(b"PK\x03\x04"))

            # 1b. Unauthenticated docx export (EN explicit)
            r_docx_en = requests.get(f"http://127.0.0.1:{port}/api/systems/21/export/docx?lang=en")
            self.assertEqual(r_docx_en.status_code, 200)
            self.assertIn("LCA_Report_ISO14040_System_21_EN.docx", r_docx_en.headers.get("Content-Disposition", ""))
            self.assertTrue(r_docx_en.content.startswith(b"PK\x03\x04"))

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
        """Run node --check on all public JS files and verify runtime evaluation of app.js in a mock DOM."""
        import subprocess
        for script_name in ["app.js", "i18n.js"]:
            script_path = os.path.join(self.base_dir, "public", "js", script_name)
            res = subprocess.run(["node", "--check", script_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"JavaScript SyntaxError detected in {script_name}:\n{res.stderr}")

        # Test runtime initialization and scope integrity in Node mock environment
        eval_script = """
        const fs = require('fs');
        const vm = require('vm');
        function makeEl(id='') { return { id, style:{}, classList:{add:()=>{},remove:()=>{},toggle:()=>{}}, setAttribute:()=>{}, getAttribute:()=>'', removeAttribute:()=>{}, appendChild:()=>{}, removeChild:()=>{}, addEventListener:()=>{}, querySelector:()=>null, querySelectorAll:()=>[], value:'', textContent:'', innerHTML:'' }; }
        const dom = { getElementById: makeEl, querySelectorAll: ()=>[], querySelector: ()=>null, addEventListener: ()=>{}, createElement: makeEl, body: makeEl('body'), documentElement: { lang: 'es' }, readyState: 'complete' };
        const win = { document: dom, location: { hash: '', search: '', pathname: '/', href: '' }, localStorage: { getItem: ()=>null, setItem: ()=>{}, removeItem: ()=>{} }, sessionStorage: { getItem: ()=>null, setItem: ()=>{}, removeItem: ()=>{} }, navigator: { clipboard: { writeText: ()=>Promise.resolve() } }, fetch: ()=>Promise.resolve({ ok: true, json: ()=>Promise.resolve({}) }), addEventListener: ()=>{}, I18n: { t: (k, d)=>d||k, getCurrentLanguage: ()=>'es', setLanguage: ()=>{} }, scrollTo: ()=>{} };
        win.window = win;
        const ctx = vm.createContext({ window: win, document: dom, localStorage: win.localStorage, sessionStorage: win.sessionStorage, navigator: win.navigator, fetch: win.fetch, console: console, setTimeout, clearTimeout, setInterval, clearInterval, URL: { createObjectURL: ()=>'', revokeObjectURL: ()=>{} } });
        const code = fs.readFileSync(process.argv[1], 'utf8');
        vm.runInContext(code, ctx);
        if (!ctx.window.EconodeApp || typeof ctx.window.EconodeApp !== 'object') {
            console.error('window.EconodeApp is not defined or not an object');
            process.exit(1);
        }
        """
        app_js_path = os.path.join(self.base_dir, "public", "js", "app.js")
        run_res = subprocess.run(["node", "-e", eval_script, app_js_path], capture_output=True, text=True)
        self.assertEqual(run_res.returncode, 0, f"Runtime error evaluating public/js/app.js:\n{run_res.stderr}")

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
