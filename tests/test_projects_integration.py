import subprocess
import time
import requests
import sys
import os

STUDIO_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio"
sys.path.insert(0, STUDIO_DIR)
from application.auth_service import generate_session_token
from infrastructure.auth_adapter import get_all_users

analyst_user = next(u for u in get_all_users() if u.get("role") == "analyst")
token = generate_session_token(analyst_user["id"], "analyst")

# Start server on port 8899
proc = subprocess.Popen(
    [sys.executable, r"C:\Users\Josue\Documents\Espacio\ECONODE\econode_studio\server.py", "--port", "8899"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(2.5)

base_url = "http://localhost:8899"
headers = {"Authorization": f"Bearer {token}"}

try:
    # 1. GET /api/systems
    r1 = requests.get(f"{base_url}/api/systems", headers=headers)
    systems_list = r1.json().get("items", [])
    print("GET /api/systems status:", r1.status_code, "count:", len(systems_list))
    assert r1.status_code == 200
    assert len(systems_list) >= 2
    first_sys_id = systems_list[0]["id"]
    second_sys_id = systems_list[1]["id"]

    # 2. GET /api/projects
    r2 = requests.get(f"{base_url}/api/projects", headers=headers)
    print("GET /api/projects status:", r2.status_code, "count:", len(r2.json().get("items", [])))
    assert r2.status_code == 200

    # 3. POST /api/projects/create
    test_code = f"PRJ-BOT-{int(time.time()) % 10000:04d}"
    r3 = requests.post(f"{base_url}/api/projects/create", headers=headers, json={
        "name": "Proyecto Botellas Bio 2026",
        "code": test_code,
        "category": "Polímeros & Empaque",
        "description": "Comparativa de envases sostenibles"
    })
    print("POST /api/projects/create status:", r3.status_code, r3.json().get("status"))
    assert r3.status_code == 200
    proj_id = r3.json()["project"]["id"]

    # 4. POST /api/systems/{first_sys_id}/assign-project
    r4 = requests.post(f"{base_url}/api/systems/{first_sys_id}/assign-project", headers=headers, json={
        "project_id": proj_id
    })
    print(f"Assign system {first_sys_id} status:", r4.status_code, r4.json().get("status"))
    assert r4.status_code == 200

    # 5. POST /api/systems/{second_sys_id}/assign-project
    r5 = requests.post(f"{base_url}/api/systems/{second_sys_id}/assign-project", headers=headers, json={
        "project_id": proj_id
    })
    print(f"Assign system {second_sys_id} status:", r5.status_code, r5.json().get("status"))
    assert r5.status_code == 200

    # 6. GET /api/projects/{proj_id}/compare
    r6 = requests.get(f"{base_url}/api/projects/{proj_id}/compare", headers=headers)
    print("GET compare status:", r6.status_code, "systems in comp:", len(r6.json().get("systems", [])))
    assert r6.status_code == 200
    comp_data = r6.json()
    assert comp_data["systems_count"] == 2
    for s in comp_data["systems"]:
        print(f"  -> System '{s['name']}' GWP: {s['lcia_scores']['global_warming']} kg CO2-eq, Best: {s.get('is_best_carbon')}")

    # 7. Cleanup: unassign and delete project
    requests.post(f"{base_url}/api/systems/{first_sys_id}/assign-project", headers=headers, json={"project_id": None})
    requests.post(f"{base_url}/api/systems/{second_sys_id}/assign-project", headers=headers, json={"project_id": None})
    r7 = requests.post(f"{base_url}/api/projects/delete", headers=headers, json={"project_id": proj_id})
    print("Delete project status:", r7.status_code, r7.json().get("status"))
    assert r7.status_code == 200

    print("ALL API ENDPOINT INTEGRATION TESTS PASSED 100%!")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
