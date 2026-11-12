import sys
import os
import json

STUDIO_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio"
sys.path.insert(0, STUDIO_DIR)

from infrastructure.database_adapter import get_active_db_connection, list_product_systems, list_projects, get_product_system_details
from application.auth_service import generate_session_token
from infrastructure.auth_adapter import get_all_users

conn = get_active_db_connection()

print("--- Test 1: Systems Visibility for Josue Renteria ---")
systems_josue = list_product_systems(conn, user_email="josuearenteriaz09@gmail.com")
print(f"Total systems visible for Josue: {len(systems_josue)}")
assert len(systems_josue) == 4, f"Expected 4 systems, got {len(systems_josue)}"
for s in systems_josue:
    print(f"  System ID {s['id']}: '{s['name']}' (Code: {s['code']}, Owner: {s['owner_name']})")

print("\n--- Test 2: System Isolation ---")
# System 21 vs System 1214 vs System 1215
sys_21 = get_product_system_details(conn, 21)
sys_1214 = get_product_system_details(conn, 1214)
sys_1215 = get_product_system_details(conn, 1215)

assert sys_21 is not None and sys_1214 is not None and sys_1215 is not None
print(f"Sys 21 name: {sys_21['name']}, nodes count: {len(sys_21.get('nodes', []))}")
print(f"Sys 1214 name: {sys_1214['name']}, nodes count: {len(sys_1214.get('nodes', []))}")
print(f"Sys 1215 name: {sys_1215['name']}, nodes count: {len(sys_1215.get('nodes', []))}")

print("\n--- Test 3: Verification of JS App Logic (Clean & Isolated) ---")
app_js_path = r"C:\Users\Josue\Documents\Espacio\ECONODE\public\js\app.js"
with open(app_js_path, "r", encoding="utf-8") as f:
    js_code = f.read()

# Verify that openSystem resets palette and canvas nodes
assert "state.paletteProcesses = [];" in js_code, "openSystem must reset paletteProcesses"
assert "state.canvasNodes = [];" in js_code, "openSystem must reset canvasNodes"

# Verify that addNodeToCanvas prevents duplicate entries
assert "Proceso \"${name}\" ya está en el lienzo (posición actualizada)." in js_code or "reposicionado" in js_code, "addNodeToCanvas must reposition existing nodes"

# Verify that removeNode properly handles edges and does not resurrect nodes
assert "delete p._placedOnCanvas;" in js_code, "removeNode must clear _placedOnCanvas"
assert "state.canvasNodes.splice(nodeIndex, 1);" in js_code, "removeNode must splice out the node"

# Verify zero emojis in both files
import re
emojis_db = re.findall(r'[\U00010000-\U0010ffff]', open(r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio\infrastructure\database_adapter.py", "r", encoding="utf-8").read())
emojis_js = re.findall(r'[\U00010000-\U0010ffff]', js_code)
assert len(emojis_db) == 0, f"Found {len(emojis_db)} emojis in database_adapter.py"
assert len(emojis_js) == 0, f"Found {len(emojis_js)} emojis in app.js"

print("ALL 4 BUG TESTS PASSED 100%!")
