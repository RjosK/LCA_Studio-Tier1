import os
import unittest
from econode_studio.infrastructure.simapro_adapter import (
    is_simapro_csv,
    parse_simapro_csv,
    simapro_process_to_econode_node,
    serialize_econode_to_simapro_csv
)

class TestSimaProAdapter(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.file_incineration = os.path.join(self.base_dir, "simaproexamples", "08_CO_IN_S1_IMPORT_SIMAPRO.CSV")
        self.file_grid = os.path.join(self.base_dir, "simaproexamples", "exampleprocessEXPORT_SOFTWARE.CSV")

    def test_detect_simapro_csv(self):
        with open(self.file_incineration, "rb") as f:
            raw = f.read()
        txt = raw.decode("utf-8-sig", errors="replace")
        self.assertTrue(is_simapro_csv(txt))

        normal_csv = "Name,Code,Unit\nProcess A,P01,kg\n"
        self.assertFalse(is_simapro_csv(normal_csv))

    def test_parse_cotton_incineration(self):
        with open(self.file_incineration, "rb") as f:
            raw = f.read()
        txt = raw.decode("utf-8-sig", errors="replace")
        
        header, processes = parse_simapro_csv(txt)
        self.assertEqual(len(processes), 1)
        
        proc = processes[0]
        meta = proc.get("meta", {})
        self.assertEqual(meta.get("Category type"), "material")

        # 122 exchanges total in the SimaPro file
        self.assertEqual(len(proc.get("exchanges", [])), 122)

        # Convert to ECONODE node
        node = simapro_process_to_econode_node(proc, idx=1)
        self.assertEqual(node["name"], "08_CO_IN_S1")
        
        # Verify inputs and outputs total 122
        total_node_exchanges = len(node["inputs"]) + len(node["outputs"])
        self.assertEqual(total_node_exchanges, 122)
        self.assertTrue(len(node["inputs"]) > 0)
        self.assertTrue(len(node["outputs"]) > 0)

    def test_parse_multi_process_with_formulas(self):
        with open(self.file_grid, "rb") as f:
            raw = f.read()
        txt = raw.decode("latin-1")

        header, processes = parse_simapro_csv(txt)
        self.assertEqual(len(processes), 5)

        # Convert all to nodes
        nodes = [simapro_process_to_econode_node(p, idx=i+1) for i, p in enumerate(processes)]
        self.assertEqual(len(nodes), 5)

        names = [n["name"] for n in nodes]
        self.assertIn("market group for electricity, medium voltage GLO", names)
        self.assertIn("electricity_A2200", names)

        # Verify formula preservation in electricity_A2200
        elec_node = next(n for n in nodes if n["name"] == "electricity_A2200")
        all_formulas = [x.get("formula") for x in elec_node["inputs"] + elec_node["outputs"] if x.get("formula")]
        self.assertEqual(len(all_formulas), 4)
        self.assertTrue(all("iff(dig_elec_region=" in f for f in all_formulas))

    def test_roundtrip_serialize_and_parse(self):
        with open(self.file_incineration, "rb") as f:
            raw = f.read()
        txt = raw.decode("utf-8-sig", errors="replace")
        
        header, procs = parse_simapro_csv(txt)
        node = simapro_process_to_econode_node(procs[0], idx=1)

        # Serialize node to SimaPro CSV
        csv_out = serialize_econode_to_simapro_csv([node])
        
        # Verify formatting
        self.assertTrue(csv_out.startswith("{SimaPro 9.5.0.0}"))
        self.assertIn("{CSV separator: Semicolon}", csv_out)
        self.assertIn("{Decimal separator: .}", csv_out)
        self.assertIn("{CSV Format version: 9.0.0}", csv_out)
        self.assertIn("Process", csv_out)
        self.assertIn("Products", csv_out)
        self.assertIn("Materials/fuels", csv_out)
        self.assertIn("Emissions to air", csv_out)

        # Re-parse generated CSV
        re_header, reparsed = parse_simapro_csv(csv_out)
        self.assertEqual(len(reparsed), 1)
        self.assertEqual(reparsed[0].get("meta", {}).get("Process name"), "08_CO_IN_S1")
        self.assertEqual(len(reparsed[0].get("exchanges", [])), 122)

    def test_import_use_case(self):
        from econode_studio.infrastructure import get_active_db_connection
        from econode_studio.application.product_systems import import_systems_csv_use_case, get_system_canvas_use_case
        
        conn = get_active_db_connection()
        try:
            with open(self.file_incineration, "rb") as f:
                raw = f.read()
            txt = raw.decode("utf-8-sig", errors="replace")
            
            res = import_systems_csv_use_case(conn, txt)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["systems_imported"], 1)
            self.assertTrue(len(res["systems_created"]) > 0)
            
            sys_id = res["systems_created"][0]
            canvas = get_system_canvas_use_case(conn, sys_id)
            self.assertIsNotNone(canvas)
            nodes = canvas.get("nodes", [])
            self.assertEqual(len(nodes), 1)
            self.assertEqual(nodes[0]["name"], "08_CO_IN_S1")
            total_exchanges = len(nodes[0]["inputs"]) + len(nodes[0]["outputs"])
            self.assertEqual(total_exchanges, 122)
        finally:
            conn.close()

if __name__ == "__main__":
    unittest.main()
