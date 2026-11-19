"""
tests/test_simapro_multiprocess.py - Tests for SimaPro Multi-Process Inspection & Graph Construction (Option C)
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STUDIO_DIR = os.path.join(BASE_DIR, "econode_studio")
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from infrastructure.simapro_adapter import (
    inspect_simapro_csv,
    build_simapro_graph,
    parse_simapro_csv
)


class TestSimaProMultiProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.examples_dir = os.path.join(BASE_DIR, "simaproexamples")
        cls.landfill_file = os.path.join(cls.examples_dir, "landfill_example_envver.CSV")
        cls.single_proc_file = os.path.join(cls.examples_dir, "08_CO_IN_S1_IMPORT_SIMAPRO.CSV")

    def test_01_inspect_single_process_csv(self):
        if not os.path.exists(self.single_proc_file):
            self.skipTest("Single process example file not found")
        with open(self.single_proc_file, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()

        meta = inspect_simapro_csv(content)
        self.assertFalse(meta["is_multi_process"])
        self.assertEqual(meta["total_processes"], 1)
        self.assertIn("08_CO_IN_S1", meta["root_process_name"])

    def test_02_inspect_multiprocess_landfill_csv(self):
        if not os.path.exists(self.landfill_file):
            self.skipTest("Landfill example file not found")
        with open(self.landfill_file, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()

        meta = inspect_simapro_csv(content)
        self.assertTrue(meta["is_multi_process"])
        self.assertEqual(meta["total_processes"], 57)
        self.assertEqual(meta["waste_treatments_count"], 12)
        self.assertEqual(meta["root_process_name"], "01_CO_LF_baseline")

    def test_03_build_graph_root_mode(self):
        if not os.path.exists(self.landfill_file):
            self.skipTest("Landfill example file not found")
        with open(self.landfill_file, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()

        header, raw_procs = parse_simapro_csv(content)
        nodes, edges = build_simapro_graph(raw_procs, mode="root")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(edges), 0)
        root_node = nodes[0]
        self.assertEqual(root_node["name"], "01_CO_LF_baseline")
        self.assertGreaterEqual(len(root_node["inputs"]) + len(root_node["outputs"]), 150)

    def test_04_build_graph_full_network_mode(self):
        if not os.path.exists(self.landfill_file):
            self.skipTest("Landfill example file not found")
        with open(self.landfill_file, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()

        header, raw_procs = parse_simapro_csv(content)
        nodes, edges = build_simapro_graph(raw_procs, mode="full")
        self.assertEqual(len(nodes), 57)
        self.assertGreater(len(edges), 300)

        # Check tiered DAG coordinates
        xs = [n["x"] for n in nodes]
        ys = [n["y"] for n in nodes]
        self.assertGreater(max(xs), min(xs))
        self.assertGreater(max(ys), min(ys))

    def test_05_zero_emoji_integrity(self):
        files_to_check = [
            "econode_studio/infrastructure/simapro_adapter.py",
            "econode_studio/application/product_systems.py",
            "tests/test_simapro_multiprocess.py"
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
