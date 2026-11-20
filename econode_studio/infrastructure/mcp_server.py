"""
econode_studio/infrastructure/mcp_server.py - Servidor Oficial Model Context Protocol (MCP)
Estandar JSON-RPC 2.0 y SSE para integracion con Agentes de IA (Claude, Cursor, Antigravity, ChatGPT).
"""

import json
from typing import Dict, Any, List, Optional

def _get_app_services():
    try:
        from application import (
            get_dashboard_systems_use_case,
            get_system_canvas_use_case,
            compute_epd_report_use_case
        )
        from application.ghg_service import (
            list_inventories_use_case,
            get_inventory_by_id_use_case,
            add_entry_to_inventory_use_case,
            search_emission_factors
        )
    except (ImportError, ValueError):
        from econode_studio.application import (
            get_dashboard_systems_use_case,
            get_system_canvas_use_case,
            compute_epd_report_use_case
        )
        from econode_studio.application.ghg_service import (
            list_inventories_use_case,
            get_inventory_by_id_use_case,
            add_entry_to_inventory_use_case,
            search_emission_factors
        )
    return {
        "get_dashboard_systems_use_case": get_dashboard_systems_use_case,
        "get_system_canvas_use_case": get_system_canvas_use_case,
        "compute_epd_report_use_case": compute_epd_report_use_case,
        "list_inventories_use_case": list_inventories_use_case,
        "get_inventory_by_id_use_case": get_inventory_by_id_use_case,
        "add_entry_to_inventory_use_case": add_entry_to_inventory_use_case,
        "search_emission_factors": search_emission_factors
    }


# Definicion del catalogo oficial de herramientas MCP
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "econode_list_systems",
        "description": "Lista los sistemas producto de analisis de ciclo de vida (ACV) creados por el usuario en ECONODE.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de sistemas a consultar (por defecto 20).",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "econode_get_system",
        "description": "Obtiene la estructura completa de un sistema producto: nodos, procesos unitarios, insumos, emisiones y parametros.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "system_id": {
                    "type": "integer",
                    "description": "Identificador numerico del sistema producto."
                }
            },
            "required": ["system_id"]
        }
    },
    {
        "name": "econode_calculate_lcia",
        "description": "Calcula el impacto ambiental caracterizado (huella de carbono GWP, acidificacion, agotamiento de recursos) de un sistema producto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "system_id": {
                    "type": "integer",
                    "description": "ID del sistema producto a calcular."
                }
            },
            "required": ["system_id"]
        }
    },
    {
        "name": "econode_search_emission_factors",
        "description": "Busca factores de emision de referencia oficiales validados (electricidad, combustibles, transporte, materias primas).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Texto o combustible a buscar (ej. 'electricidad', 'diesel', 'gas natural', 'pet')."
                },
                "scope": {
                    "type": "string",
                    "description": "Alcance opcional: SCOPE_1, SCOPE_2, SCOPE_3 o ALL.",
                    "default": "ALL"
                },
                "limit": {
                    "type": "integer",
                    "description": "Limite maximo de resultados.",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "econode_record_ghg_activity",
        "description": "Registra un consumo o actividad de emision corporativa en Alcance 1, 2 o 3 (GHG Protocol Corporate Standard).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "inventory_id": {
                    "type": "integer",
                    "description": "ID del inventario corporativo (si se omite o es 0, se usa el inventario activo del ano)."
                },
                "scope": {
                    "type": "integer",
                    "description": "Alcance normativo: 1 (Directas), 2 (Energia / Electricidad) o 3 (Cadena de valor)."
                },
                "scope_category": {
                    "type": "string",
                    "description": "Categoria normativa (ej. 'combustion_estacionaria', 'electricidad_red', 'viajes_negocios')."
                },
                "facility_name": {
                    "type": "string",
                    "description": "Nombre de la instalacion o centro de trabajo (ej. 'Planta Monterrey')."
                },
                "activity_name": {
                    "type": "string",
                    "description": "Nombre descriptivo de la fuente o actividad (ej. 'Caldera No. 2 Gas Natural')."
                },
                "activity_amount": {
                    "type": "number",
                    "description": "Cantidad numerica de actividad consumida."
                },
                "activity_unit": {
                    "type": "string",
                    "description": "Unidad de medida (kWh, m3, L, t-km, kg)."
                },
                "fuel_type": {
                    "type": "string",
                    "description": "Tipo de combustible o fuente (ej. 'gas_natural', 'diesel', 'electricidad_cfe')."
                }
            },
            "required": ["scope", "activity_name", "activity_amount", "activity_unit"]
        }
    },
    {
        "name": "econode_get_ghg_summary",
        "description": "Consulta el resumen oficial del inventario corporativo de Gases de Efecto Invernadero (GEI) con dual accounting (location-based y market-based).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "inventory_id": {
                    "type": "integer",
                    "description": "ID del inventario corporativo (opcional; si se omite, retorna el inventario mas reciente)."
                }
            }
        }
    }
]


def execute_tool(name: str, arguments: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecuta una herramienta de MCP invocando los servicios de aplicacion de ECONODE."""
    srv = _get_app_services()
    get_dashboard_systems_use_case = srv["get_dashboard_systems_use_case"]
    get_system_canvas_use_case = srv["get_system_canvas_use_case"]
    compute_epd_report_use_case = srv["compute_epd_report_use_case"]
    list_inventories_use_case = srv["list_inventories_use_case"]
    get_inventory_by_id_use_case = srv["get_inventory_by_id_use_case"]
    add_entry_to_inventory_use_case = srv["add_entry_to_inventory_use_case"]
    search_emission_factors = srv["search_emission_factors"]

    try:
        if name == "econode_list_systems":
            limit = int(arguments.get("limit", 20))
            all_systems = get_dashboard_systems_use_case()
            systems = all_systems[:limit]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "total_count": len(all_systems),
                            "returned_count": len(systems),
                            "systems": systems
                        }, ensure_ascii=False, indent=2)
                    }
                ]
            }

        elif name == "econode_get_system":
            sys_id = int(arguments.get("system_id", 0))
            system = get_system_canvas_use_case(sys_id)
            if not system:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Error: Sistema con ID {sys_id} no encontrado."}]
                }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(system, ensure_ascii=False, indent=2)
                    }
                ]
            }

        elif name == "econode_calculate_lcia":
            sys_id = int(arguments.get("system_id", 0))
            report = compute_epd_report_use_case(sys_id)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(report, ensure_ascii=False, indent=2)
                    }
                ]
            }

        elif name == "econode_search_emission_factors":
            query = str(arguments.get("query", ""))
            scope = str(arguments.get("scope", "ALL"))
            limit = int(arguments.get("limit", 10))
            factors, _ = search_emission_factors(query=query, scope=scope, limit=limit)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(factors, ensure_ascii=False, indent=2)
                    }
                ]
            }

        elif name == "econode_record_ghg_activity":
            inv_id = int(arguments.get("inventory_id") or 0)
            if not inv_id:
                invs = list_inventories_use_case()
                if invs:
                    inv_id = invs[0]["id"]
                else:
                    return {
                        "isError": True,
                        "content": [{"type": "text", "text": "Error: No existe ningun inventario corporativo activo en ECONODE. Cree uno primero."}]
                    }

            entry_data = {
                "scope": int(arguments.get("scope", 1)),
                "scope_category": str(arguments.get("scope_category", "combustion_estacionaria")),
                "facility_name": str(arguments.get("facility_name", "Principal")),
                "activity_name": str(arguments.get("activity_name", "Actividad")),
                "activity_amount": float(arguments.get("activity_amount", 0.0)),
                "activity_unit": str(arguments.get("activity_unit", "kWh")),
                "fuel_type": str(arguments.get("fuel_type", "gas_natural")),
                "evidence_reference": f"Registrado via MCP por agente de IA ({user.get('display_name', 'API User')})"
            }

            created_entry = add_entry_to_inventory_use_case(inv_id, entry_data)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "message": f"Actividad '{entry_data['activity_name']}' registrada en Alcance {entry_data['scope']}.",
                            "inventory_id": inv_id,
                            "entry": created_entry
                        }, ensure_ascii=False, indent=2)
                    }
                ]
            }

        elif name == "econode_get_ghg_summary":
            inv_id = int(arguments.get("inventory_id") or 0)
            if not inv_id:
                invs = list_inventories_use_case()
                if not invs:
                    return {
                        "content": [{"type": "text", "text": json.dumps({"inventories": []})}]
                    }
                inv_id = invs[0]["id"]

            summary = get_inventory_by_id_use_case(inv_id)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(summary, ensure_ascii=False, indent=2)
                    }
                ]
            }

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error: Herramienta desconocida '{name}'."}]
            }

    except Exception as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error en ejecucion de herramienta {name}: {str(e)}"}]
        }


def handle_jsonrpc_request(request: Dict[str, Any], user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Procesa una solicitud estandar JSON-RPC 2.0 bajo el protocolo MCP."""
    if not isinstance(request, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"}
        }

    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {}) or {}

    # 1. Inicializacion MCP
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False}
                },
                "serverInfo": {
                    "name": "econode-mcp",
                    "version": "1.0.0"
                }
            }
        }

    # Notificaciones
    if method in ("notifications/initialized", "initialized"):
        return None

    # Ping
    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    # 2. Catalogo de Herramientas
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS
            }
        }

    # 3. Llamada a Herramienta
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        res = execute_tool(tool_name, arguments, user)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": res
        }

    # 4. Catalogo de Recursos
    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "resources": [
                    {
                        "uri": "econode://systems",
                        "name": "Sistemas Producto ACV",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "econode://ghg/current",
                        "name": "Inventario Corporativo GEI 2026",
                        "mimeType": "application/json"
                    }
                ]
            }
        }

    # Metodo no soportado
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method '{method}' not found."
        }
    }
