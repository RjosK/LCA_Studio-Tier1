"""
tests/test_system_info_modal.py - Test Suite for Product System Info Modal
Validates:
1. Backend list_product_systems returns created_at, updated_at, db_profile, and counts.
2. Backend get_product_system_details returns timestamps and database metadata.
3. DOM verification for modal elements in public/index.html.
4. Javascript logic and exports in public/js/app.js.
5. 100% Bilingual dictionary entries in public/js/i18n.js.
"""

import os
import sys
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from econode_studio.infrastructure.database_adapter import (
    get_active_db_connection,
    list_product_systems,
    get_product_system_details
)


class TestSystemInfoModal(unittest.TestCase):

    def test_list_product_systems_metadata(self):
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            self.assertGreater(len(systems), 0, "Should return at least one product system")
            for sys_item in systems:
                self.assertIn("created_at", sys_item)
                self.assertIsNotNone(sys_item["created_at"])
                self.assertIn("updated_at", sys_item)
                self.assertIsNotNone(sys_item["updated_at"])
                self.assertIn("db_profile", sys_item)
                self.assertTrue(len(sys_item["db_profile"]) > 0)
                self.assertIn("nodes_count", sys_item)
                self.assertIn("edges_count", sys_item)
                self.assertIn("parameters_count", sys_item)

    def test_simapro_and_epd_db_profile_deduction(self):
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            simapro_sys = next((s for s in systems if "simapro" in s["name"].lower() or s["code"].startswith("SP-")), None)
            if simapro_sys:
                self.assertIn("SimaPro", simapro_sys["db_profile"])
                self.assertIn("ecoinvent", simapro_sys["db_profile"])

    def test_get_product_system_details_metadata(self):
        with get_active_db_connection() as conn:
            systems = list_product_systems(conn)
            first_id = systems[0]["id"]
            details = get_product_system_details(conn, first_id)
            self.assertIsNotNone(details)
            self.assertIn("created_at", details)
            self.assertIn("updated_at", details)
            self.assertIn("db_profile", details)
            self.assertIn("category", details)
            self.assertIn("geography", details)

    def test_html_modal_dom_structure(self):
        html_path = os.path.join(BASE_DIR, "public", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        required_ids = [
            "modalSystemInfo",
            "infoSysTitle",
            "infoSysCode",
            "infoSysSubtitle",
            "infoSysDbBadge",
            "infoSysStatus",
            "infoSysProjectBadge",
            "infoSysGeoBadge",
            "infoSysDbName",
            "infoSysDbAllocation",
            "infoSysCreatedAt",
            "infoSysCreatedAtRel",
            "infoSysUpdatedAt",
            "infoSysUpdatedAtRel",
            "infoSysAge",
            "infoSysCompliance",
            "infoSysFuncUnit",
            "infoSysNodesCount",
            "infoSysEdgesCount",
            "infoSysParamsCount",
            "infoSysOwner",
            "infoSysOrg",
            "infoSysGeoCat",
            "infoSysProject",
            "infoSysCollabs",
            "secInfoEpd",
            "infoEpdPcr",
            "infoEpdDeclUnit",
            "infoEpdModules",
            "infoEpdBalance",
            "btnInfoOpenVault",
            "btnInfoOpenCanvas",
            "btnCloseSystemInfoModal"
        ]

        for req_id in required_ids:
            self.assertIn(f'id="{req_id}"', html, f"Missing required element ID: {req_id}")

    def test_i18n_bilingual_coverage(self):
        i18n_path = os.path.join(BASE_DIR, "public", "js", "i18n.js")
        with open(i18n_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        required_keys = [
            "dash.info_btn",
            "dash.info_tooltip",
            "sys_info.modal_title",
            "sys_info.modal_subtitle",
            "sys_info.sec_database",
            "sys_info.db_primary",
            "sys_info.db_allocation",
            "sys_info.lcia_methods",
            "sys_info.sec_timestamps",
            "sys_info.created_at",
            "sys_info.updated_at",
            "sys_info.age",
            "sys_info.compliance",
            "sys_info.sec_architecture",
            "sys_info.func_unit",
            "sys_info.nodes",
            "sys_info.edges",
            "sys_info.params",
            "sys_info.sec_governance",
            "sys_info.author",
            "sys_info.sec_epd",
            "sys_info.btn_open_canvas",
            "sys_info.btn_open_vault",
            "sys_info.btn_close"
        ]

        for key in required_keys:
            self.assertIn(f'"{key}"', js_content, f"Missing i18n key: {key}")

    def test_app_js_exports_and_handlers(self):
        app_path = os.path.join(BASE_DIR, "public", "js", "app.js")
        with open(app_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        self.assertIn("openSystemInfoModal", js_content)
        self.assertIn("closeSystemInfoModal", js_content)
        self.assertIn("openCanvasFromInfo", js_content)
        self.assertIn("openVaultFromInfo", js_content)
        self.assertIn("formatSystemAuditDateTime", js_content)
        self.assertIn("btn-sys-info", js_content)


if __name__ == "__main__":
    unittest.main()
