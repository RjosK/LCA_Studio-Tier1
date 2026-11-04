"""
Test ECONODE server endpoints locally
"""
import threading
import time
import urllib.request
import json
import sys
import os

os.chdir(r"C:\Users\Josue\Documents\Espacio\ECONODE")
sys.path.insert(0, r"C:\Users\Josue\Documents\Espacio\ECONODE")

from econode_studio.server import EconodeRequestHandler
import http.server

test_port = 8085
httpd = http.server.ThreadingHTTPServer(("127.0.0.1", test_port), EconodeRequestHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.5)

base_url = f"http://127.0.0.1:{test_port}"
print("Testing ECONODE API on", base_url)

endpoints = [
    ("Sources", f"{base_url}/api/sources"),
    ("All Processes", f"{base_url}/api/processes?source=all&limit=5"),
    ("ecoinvent Processes", f"{base_url}/api/processes?source=ecoinvent_312&q=electricity&limit=5"),
    ("GLAD Processes", f"{base_url}/api/processes?source=glad_network&limit=5"),
    ("OEKOBAUDAT Processes", f"{base_url}/api/processes?source=oekobaudat_de&limit=5"),
    ("ADEME Processes", f"{base_url}/api/processes?source=ademe_base_carbone&limit=5"),
    ("Custom Processes", f"{base_url}/api/processes?source=user_custom&limit=5"),
    ("Process Sheet ecoinvent", f"{base_url}/api/processes/1/sheet"),
    ("Process Sheet GLAD", f"{base_url}/api/processes/cat_1/sheet")
]

for name, url in endpoints:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            if "sources" in data:
                count = len(data["sources"])
                print(f"[PASS] {name}: HTTP 200 -> {count} sources")
            elif "items" in data:
                count = len(data["items"])
                first_name = data["items"][0]["name"][:30] if count > 0 else "None"
                print(f"[PASS] {name}: HTTP 200 -> {count} items (First: '{first_name}')")
            elif "sheet" in data:
                s_name = data["sheet"]["name"][:30]
                print(f"[PASS] {name}: HTTP 200 -> sheet name='{s_name}'")
            else:
                print(f"[PASS] {name}: HTTP 200 -> {list(data.keys())}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")

httpd.shutdown()
print("All ECONODE endpoint tests finished.")
