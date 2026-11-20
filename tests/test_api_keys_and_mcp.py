"""
tests/test_api_keys_and_mcp.py - Pruebas Unitarias e Integración para API Keys y Servidor MCP
Valida:
1. Generación y almacenamiento criptográfico seguro de Personal Access Tokens (eco_live_...).
2. Persistencia, listado, revocación y control de tasa (rate limiting).
3. Servidor MCP JSON-RPC 2.0 (initialize, tools/list, tools/call, resources/list).
4. Endpoints REST v1 y autenticación Bearer token.
"""

import os
import sys
import json
import hashlib
from io import BytesIO

# Configurar path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
sys.path.insert(0, PROJECT_ROOT)

from econode_studio.domain.api_key import ApiKey, ApiScopeEnum
from econode_studio.infrastructure import (
    save_api_key,
    get_api_key_by_hash,
    list_user_api_keys,
    revoke_api_key,
    check_and_increment_rate_limit,
    handle_jsonrpc_request,
    MCP_TOOLS
)
from econode_studio.server import EconodeRequestHandler


class DummyHTTPChannel:
    """Canal simulado para pruebas de solicitudes HTTP sin levantar socket de red."""
    def __init__(self, request_bytes: bytes):
        self.rfile = BytesIO(request_bytes)
        self.wfile = BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile


def test_api_key_domain_generation():
    """Valida que la clave se genere con prefijo eco_live_ y hash SHA-256 inmutable."""
    key, raw_token = ApiKey.generate(
        user_id="user_test_123",
        organization_id="Org Test",
        name="Clave Asistente Claude",
        scopes=["all"]
    )
    assert raw_token.startswith("eco_live_")
    assert key.key_prefix.startswith("eco_live_")
    assert len(key.hashed_secret) == 64  # SHA-256 hex
    assert key.is_active() is True
    assert key.has_scope("systems:read") is True
    assert hashlib.sha256(raw_token.encode("utf-8")).hexdigest() == key.hashed_secret


def test_api_key_persistence_and_revocation():
    """Valida guardado, búsqueda por hash y revocación en la base de datos."""
    key, raw_token = ApiKey.generate(
        user_id="analyst_test_pers",
        name="Clave Script Python",
        rate_limit_per_minute=100
    )
    saved = save_api_key(key)
    assert saved is True

    # Búsqueda por hash
    found = get_api_key_by_hash(key.hashed_secret)
    assert found is not None
    assert found.id == key.id
    assert found.name == "Clave Script Python"
    assert found.is_active() is True

    # Listado por usuario
    user_keys = list_user_api_keys("analyst_test_pers")
    assert any(k.id == key.id for k in user_keys)

    # Revocación
    revoked = revoke_api_key(key.id, "analyst_test_pers")
    assert revoked is True

    # Tras revocación, get_api_key_by_hash no debe retornar claves revocadas
    assert get_api_key_by_hash(key.hashed_secret) is None


def test_rate_limiting():
    """Valida control de tasa por ventana deslizante en memoria."""
    test_key_id = "key_rate_limit_test"
    # Límite bajo de 3 llamadas por minuto
    for _ in range(3):
        assert check_and_increment_rate_limit(test_key_id, limit_per_minute=3) is True
    # La cuarta debe ser rechazada
    assert check_and_increment_rate_limit(test_key_id, limit_per_minute=3) is False


def test_mcp_initialize():
    """Valida protocolo de inicialización MCP JSON-RPC 2.0."""
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "claude-desktop", "version": "1.0.0"}
        }
    }
    user = {"id": "user_1", "role": "analyst"}
    resp = handle_jsonrpc_request(req, user)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "econode-mcp"
    assert "tools" in resp["result"]["capabilities"]


def test_mcp_tools_list():
    """Valida que MCP exponga las 6 herramientas oficiales."""
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = handle_jsonrpc_request(req, {"id": "user_1"})
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "econode_list_systems" in tool_names
    assert "econode_get_system" in tool_names
    assert "econode_calculate_lcia" in tool_names
    assert "econode_search_emission_factors" in tool_names
    assert "econode_record_ghg_activity" in tool_names
    assert "econode_get_ghg_summary" in tool_names


def test_mcp_tools_call_systems_and_factors():
    """Valida ejecución real de herramientas MCP sobre los servicios de ECONODE."""
    user = {"id": "user_1", "role": "analyst", "display_name": "Test Analyst"}
    
    # 1. Herramienta list_systems
    req_sys = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "econode_list_systems", "arguments": {"limit": 5}}
    }
    resp_sys = handle_jsonrpc_request(req_sys, user)
    assert "result" in resp_sys
    content_txt = resp_sys["result"]["content"][0]["text"]
    data = json.loads(content_txt)
    assert "systems" in data
    assert data["returned_count"] <= 5

    # 2. Herramienta search_emission_factors
    req_factors = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {"name": "econode_search_emission_factors", "arguments": {"query": "diesel"}}
    }
    resp_factors = handle_jsonrpc_request(req_factors, user)
    assert "result" in resp_factors
    content_factors = json.loads(resp_factors["result"]["content"][0]["text"])
    assert isinstance(content_factors, list)


def test_mcp_tools_call_record_ghg_activity():
    """Valida registro corporativo de actividad GEI a través de llamada MCP."""
    user = {"id": "user_mcp_agent", "role": "analyst", "display_name": "Agente Claude"}
    req = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "econode_record_ghg_activity",
            "arguments": {
                "scope": 1,
                "scope_category": "combustion_estacionaria",
                "activity_name": "Caldera de Prueba Unitaria MCP",
                "activity_amount": 1250.5,
                "activity_unit": "m3",
                "fuel_type": "gas_natural"
            }
        }
    }
    resp = handle_jsonrpc_request(req, user)
    assert "result" in resp
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["status"] == "success"
    assert "Caldera de Prueba Unitaria MCP" in content["message"]


def test_http_api_v1_and_mcp_endpoints():
    """Valida flujo HTTP completo: generacion de key, consulta REST v1 y ejecucion MCP con Bearer token."""
    import http.server
    import threading
    import urllib.request
    import urllib.error
    import time

    port = 8095
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), EconodeRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # 1. Generar clave para analista
        key, raw_token = ApiKey.generate(
            user_id="analyst_carla",
            name="Clave MCP Agente Claude",
            scopes=["all"]
        )
        save_api_key(key)

        def make_call(path, data=None, method="GET", headers=None):
            url = f"http://127.0.0.1:{port}{path}"
            hdrs = {"Content-Type": "application/json"}
            if headers:
                hdrs.update(headers)
            body = json.dumps(data).encode("utf-8") if data is not None else None
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.getcode(), resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8")

        # 2. Probar GET /mcp/sse (stream SSE inicial)
        url_sse = f"http://127.0.0.1:{port}/mcp/sse"
        req_sse = urllib.request.Request(url_sse)
        with urllib.request.urlopen(req_sse, timeout=5) as resp_sse:
            assert resp_sse.getcode() == 200
            line1 = resp_sse.readline().decode("utf-8")
            line2 = resp_sse.readline().decode("utf-8")
            assert "event: endpoint" in line1
            assert "/api/v1/mcp/rpc" in line2

        # 3. Probar GET /api/v1/systems con Bearer token
        code_sys, text_sys = make_call("/api/v1/systems", headers={"Authorization": f"Bearer {raw_token}"})
        assert code_sys == 200
        data_sys = json.loads(text_sys)
        assert data_sys["status"] == "success"
        assert len(data_sys["systems"]) > 0

        # 4. Probar POST /api/v1/mcp/rpc con Bearer token y JSON-RPC tools/call
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/call",
            "params": {
                "name": "econode_search_emission_factors",
                "arguments": {"query": "diesel"}
            }
        }
        code_rpc, text_rpc = make_call("/api/v1/mcp/rpc", data=rpc_payload, method="POST", headers={"Authorization": f"Bearer {raw_token}"})
        assert code_rpc == 200
        data_rpc = json.loads(text_rpc)
        assert data_rpc["jsonrpc"] == "2.0"
        assert data_rpc["id"] == 99

        # 5. Revocar clave y comprobar rechazo 401
        revoke_api_key(key.id, "analyst_carla")
        code_rej, _ = make_call("/api/v1/systems", headers={"Authorization": f"Bearer {raw_token}"})
        assert code_rej == 401
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    print("Iniciando suite de pruebas de API Keys y Servidor MCP...")
    test_api_key_domain_generation()
    print("PASS: test_api_key_domain_generation")
    test_api_key_persistence_and_revocation()
    print("PASS: test_api_key_persistence_and_revocation")
    test_rate_limiting()
    print("PASS: test_rate_limiting")
    test_mcp_initialize()
    print("PASS: test_mcp_initialize")
    test_mcp_tools_list()
    print("PASS: test_mcp_tools_list")
    test_mcp_tools_call_systems_and_factors()
    print("PASS: test_mcp_tools_call_systems_and_factors")
    test_mcp_tools_call_record_ghg_activity()
    print("PASS: test_mcp_tools_call_record_ghg_activity")
    test_http_api_v1_and_mcp_endpoints()
    print("PASS: test_http_api_v1_and_mcp_endpoints")
    print("TODAS LAS PRUEBAS DE API KEYS, HTTP REST V1 Y MCP PASARON SATISFACTORIAMENTE (8/8)!")
