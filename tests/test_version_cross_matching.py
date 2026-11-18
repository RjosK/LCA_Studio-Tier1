"""
tests/test_version_cross_matching.py - Comprehensive Test Suite for Multi-Database Version Cross-Matching
Validates:
1. Database catalog enumeration (get_available_databases).
2. Process search across multiple versions (ecoinvent 3.11, ecoinvent 3.12, catalog, custom).
3. System matching engine (match_system_to_database) computing exact matches, location diffs, and flow issues.
4. Automated system version conversion (convert_product_system_version) with auto-naming.
5. Server API endpoints via live HTTP requests.
6. DOM elements in public/index.html.
7. JS exports and methods in public/js/app.js.
8. Bilingual translations in public/js/i18n.js.
9. Strict ZERO EMOJI rule verification.
"""

import os
import sys
import json
import time
import requests
import subprocess
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STUDIO_DIR = os.path.join(BASE_DIR, "econode_studio")
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from application.auth_service import generate_session_token
from infrastructure.auth_adapter import get_all_users
from infrastructure.database_adapter import (
    get_active_db_connection,
    list_product_systems
)
from infrastructure.version_matcher_adapter import (
    get_available_databases,
    search_database_processes,
    search_database_flows,
    match_system_to_database,
    convert_product_system_version
)


class TestVersionCrossMatching(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup test server for HTTP endpoint verification
        try:
            users = get_all_users()
            analyst_user = next((u for u in users if u.get("role") == "analyst"), {"id": "analyst_carla"})
            cls.token = generate_session_token(analyst_user["id"], "analyst")
        except Exception:
            cls.token = "test_token"

        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.port = 8898
        cls.base_url = f"http://localhost:{cls.port}"

        server_script = os.path.join(BASE_DIR, "econode_studio", "server.py")
        cls.server_proc = subprocess.Popen(
            [sys.executable, server_script, "--port", str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server_proc") and cls.server_proc:
            try:
                cls.server_proc.terminate()
                cls.server_proc.wait(timeout=3)
            except Exception:
                pass

    def test_01_available_databases(self):
        with get_active_db_connection() as conn:
            dbs = get_available_databases(conn)
            self.assertIsInstance(dbs, list)
            self.assertGreaterEqual(len(dbs), 3, "Should have at least 3 databases available")
            
            db_ids = [d["id"] for d in dbs]
            self.assertIn("ecoinvent_312", db_ids, "ecoinvent 3.12 must be in catalog")
            self.assertIn("ecoinvent_311", db_ids, "ecoinvent 3.11 must be in catalog")
            
            for db in dbs:
                self.assertIn("name", db)
                self.assertIn("version", db)
                self.assertIn("process_count", db)
                self.assertGreater(db["process_count"], 0, f"Database {db['id']} should have processes")

    def test_02_search_database_processes_311_and_312(self):
        with get_active_db_connection() as conn:
            # Search in 3.11
            res_311 = search_database_processes(conn, "ecoinvent_311", "electricity", limit=5)
            self.assertIsInstance(res_311, list)
            self.assertGreater(len(res_311), 0, "Should find electricity in ecoinvent 3.11")
            self.assertEqual(res_311[0]["database"], "ecoinvent 3.11")
            
            # Search in 3.12
            res_312 = search_database_processes(conn, "ecoinvent_312", "electricity", limit=5)
            self.assertIsInstance(res_312, list)
            self.assertGreater(len(res_312), 0, "Should find electricity in ecoinvent 3.12")
            self.assertIn("ecoinvent 3.12", res_312[0]["database"])

    def test_03_search_database_flows_311(self):
        with get_active_db_connection() as conn:
            flows_311 = search_database_flows(conn, "ecoinvent_311", "carbon dioxide", limit=5)
            self.assertIsInstance(flows_311, list)
            self.assertGreater(len(flows_311), 0, "Should find carbon dioxide flows in 3.11")

    def test_04_match_system_to_database(self):
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            self.assertGreater(len(systems), 0, "Needs at least one system to test matching")
            test_sys_id = systems[0]["id"]
            
            report = match_system_to_database(conn, test_sys_id, "ecoinvent_311")
            self.assertIsNotNone(report)
            self.assertEqual(report["system_id"], test_sys_id)
            self.assertEqual(report["target_version"], "ecoinvent_311")
            self.assertIn("total_nodes", report)
            self.assertIn("exact_matches", report)
            self.assertIn("location_diffs", report)
            self.assertIn("no_matches", report)
            self.assertIn("compatibility_score", report)
            self.assertIn("auto_generated_name", report)
            self.assertIn("auto_generated_code", report)
            self.assertIn("nodes", report)
            self.assertIn("flow_issues", report)
            
            # Auto-generated naming verification
            self.assertTrue(report["auto_generated_name"].endswith("(v3.11)"))

    def test_05_convert_product_system_version(self):
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            source_sys = systems[0]
            sys_id = source_sys["id"]
            
            # Match first to get suggested mappings
            report = match_system_to_database(conn, sys_id, "ecoinvent_311")
            process_mappings = {}
            for node in report["nodes"]:
                if node.get("suggested_match"):
                    process_mappings[node["node_id"]] = node["suggested_match"]["id"]
                else:
                    process_mappings[node["node_id"]] = "mock_substitute_id"

            res = convert_product_system_version(conn, sys_id, "ecoinvent_311", process_mappings)
            self.assertTrue(res.get("success", False))
            self.assertIn("new_system_id", res)
            new_sys_id = res["new_system_id"]
            
            # Verify new system exists in database
            cur = conn.cursor()
            cur.execute("SELECT id, name, code, db_profile FROM product_systems WHERE id = ?", (new_sys_id,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertIn("ecoinvent 3.11", row[3])

    def test_06_server_api_endpoints(self):
        # 1. GET /api/version/databases
        res_db = requests.get(f"{self.base_url}/api/version/databases", headers=self.headers)
        self.assertEqual(res_db.status_code, 200)
        data_db = res_db.json()
        self.assertEqual(data_db["status"], "success")
        self.assertIn("databases", data_db)
        
        # 2. GET /api/version/search-target
        res_search = requests.get(f"{self.base_url}/api/version/search-target?target_version=ecoinvent_311&q=cement", headers=self.headers)
        self.assertEqual(res_search.status_code, 200)
        data_search = res_search.json()
        self.assertEqual(data_search["status"], "success")
        self.assertIn("items", data_search)
        
        # 3. GET /api/version/match-system
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            sys_id = systems[0]["id"]
            
        res_match = requests.get(f"{self.base_url}/api/version/match-system?system_id={sys_id}&target_version=ecoinvent_311", headers=self.headers)
        self.assertEqual(res_match.status_code, 200)
        data_match = res_match.json()
        self.assertEqual(data_match["status"], "success")
        self.assertEqual(data_match["system_id"], sys_id)

    def test_07_html_dom_structure(self):
        html_path = os.path.join(BASE_DIR, "public", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        required_ids = [
            "btnOpenVersionMatchModal",
            "modalVersionMatch",
            "selectTargetDatabase",
            "verMatchTotalProcs",
            "verMatchExactMatches",
            "verMatchLocDiffs",
            "verMatchNoMatches",
            "verMatchCompatScore",
            "verMatchAutoNamePreview",
            "verMatchAutoCodePreview",
            "verMatchFlowsAlert",
            "verMatchFlowsItems",
            "verMatchTableBody",
            "btnSubmitVersionConversion"
        ]
        for elem_id in required_ids:
            self.assertIn(f'id="{elem_id}"', html, f"Missing #{elem_id} in index.html")

        # Also check LCI explorer ecoinvent 3.11 tab
        self.assertIn('data-source="ecoinvent_311"', html, "LCI explorer must have ecoinvent 3.11 tab")

    def test_08_javascript_exports_and_methods(self):
        js_path = os.path.join(BASE_DIR, "public", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        required_methods = [
            "openVersionMatchModal",
            "closeVersionMatchModal",
            "onTargetDatabaseChange",
            "onSelectLocationVariation",
            "onSearchSubstituteProcess",
            "onSelectSubstituteProcess",
            "toggleVersionMatchFlowsList",
            "submitVersionConversion"
        ]
        for method in required_methods:
            self.assertIn(method, js, f"Missing method {method} in app.js")

    def test_09_i18n_bilingual_coverage(self):
        i18n_path = os.path.join(BASE_DIR, "public", "js", "i18n.js")
        with open(i18n_path, "r", encoding="utf-8") as f:
            i18n_text = f.read()

        required_keys = [
            "canvas.version_match_btn",
            "canvas.version_match_title",
            "ver_match.modal_title",
            "ver_match.select_target_db",
            "ver_match.total_procs",
            "ver_match.exact_matches",
            "ver_match.loc_diffs",
            "ver_match.no_matches",
            "ver_match.proc_table_title",
            "ver_match.col_source_proc",
            "ver_match.col_status",
            "ver_match.col_target_proc",
            "ver_match.btn_convert_and_switch",
            "ver_match.auto_name_label",
            "ver_match.auto_name_notice",
            "ver_match.review_flows",
            "ver_match.flows_substitute_header",
            "ver_match.select_substitute_placeholder",
            "ver_match.success_toast"
        ]
        for key in required_keys:
            self.assertIn(f'"{key}"', i18n_text, f"Missing translation key {key} in i18n.js")

    def test_10_zero_emoji_integrity(self):
        # Ensure zero emojis in all newly added and modified files
        files_to_check = [
            "econode_studio/infrastructure/version_matcher_adapter.py",
            "econode_studio/server.py",
            "econode_studio/infrastructure/database_adapter.py",
            "public/index.html",
            "public/js/app.js",
            "public/js/i18n.js",
            "public/css/styles.css"
        ]
        for rel_path in files_to_check:
            full_path = os.path.join(BASE_DIR, rel_path)
            if not os.path.exists(full_path):
                continue
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            for char in content:
                cp = ord(char)
                if (0x1F600 <= cp <= 0x1F64F) or (0x1F300 <= cp <= 0x1F5FF) or (0x1F680 <= cp <= 0x1F6FF) or (0x1F900 <= cp <= 0x1F9FF):
                    self.fail(f"Emoji detected '{char}' (U+{cp:X}) in {rel_path}")


if __name__ == "__main__":
    unittest.main()
