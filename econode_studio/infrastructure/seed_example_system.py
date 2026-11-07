"""
econode_studio/infrastructure/seed_example_system.py - Sembrador del Sistema Producto Oficial
Crea el sistema producto de referencia solicitado por el usuario:
- 3 procesos integrados en la cadena de valor
- Proceso 1 (Inyección): 3 inputs (incluye 1 flujo unitario), 1 reference flow, 3 outputs (1 waste, 1 producto, 1 elemental)
- Proceso 2 (Soplado): 3 inputs (incluye 1 flujo unitario conectado), 1 reference flow, 3 outputs (1 waste, 1 producto, 1 elemental)
- Proceso 3 (Transporte): 3 inputs (incluye 1 flujo unitario conectado), 1 reference flow, 3 outputs (1 waste, 1 producto, 1 elemental)
"""

import sqlite3
import os
import json

def seed_official_system(conn: sqlite3.Connection) -> int:
    # Asegurar que los 3 procesos oficiales existan en la tabla custom_processes
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO custom_processes (id, code, name, category_id, location, reference_flow_id, reference_amount, description)
            VALUES 
            (-899999, 'PR-PET-INJ-01', 'PET Preform Injection Molding', 5456, 'MX', 'FL_PREFORMA', 1.0, 'Injection molding of clear PET preform with virgin input'),
            (-899998, 'PR-PET-BLOW-02', 'PET Bottle Stretch Blow Molding', 5456, 'MX', 'FL_BOTELLA', 1.0, 'Stretch blow molding of 500ml PET bottle'),
            (-899997, 'PR-PET-DIST-03', 'PET Bottle Distribution & Logistics', 4923, 'MX', 'FL_LOGISTICA', 1.0, 'Distribution logistics 350 km');
        """)

    # Verificar si ya existe el sistema producto
    cur = conn.execute("SELECT id FROM product_systems WHERE code = 'SYS-PET-CIRCULAR-01';")
    row = cur.fetchone()
    if row:
        return row[0]

    # Crear Sistema
    with conn:
        cur = conn.execute("""
            INSERT INTO product_systems (
                name, code, target_amount, description, parameters_json
            ) VALUES (
                'Official Product System: Circular PET Bottle 500ml',
                'SYS-PET-CIRCULAR-01',
                1.0,
                'Official reference model with 3 processes: Preform injection molding, Bottle stretch blow molding and Distribution logistics (Cradle-to-Gate NOM-070).',
                '{"merma_inyeccion_pct": 5.0, "merma_soplado_pct": 0.2, "distancia_km": 350}'
            );
        """)
        sys_id = cur.lastrowid

        # Insertar nodos en product_system_nodes
        # Usamos IDs de procesos simbólicos o existentes en la base
        # Proceso 1: Inyección (pos: 40, 140)
        # Proceso 2: Soplado (pos: 340, 140)
        # Proceso 3: Distribución (pos: 640, 140)

        # En la tabla de nodos persistimos las coordenadas
        conn.execute("""
            INSERT OR REPLACE INTO product_system_nodes (system_id, process_id, pos_x, pos_y)
            VALUES (?, 100001, 50, 140);
        """, (sys_id,))
        conn.execute("""
            INSERT OR REPLACE INTO product_system_nodes (system_id, process_id, pos_x, pos_y)
            VALUES (?, 100002, 380, 140);
        """, (sys_id,))
        conn.execute("""
            INSERT OR REPLACE INTO product_system_nodes (system_id, process_id, pos_x, pos_y)
            VALUES (?, 100003, 710, 140);
        """, (sys_id,))

        # Insertar intercambios oficiales (exchanges) para que openLCA y LCI tengan todos los flujos conectados
        conn.execute("DELETE FROM custom_exchanges WHERE process_id IN (100001, 100002, 100003);")
        
        # Proceso 1: Inyección (100001)
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_PREFORMA', 0, 'production', 1.0, 'kg', NULL, 'Clear PET preform');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_1', 1, 'technosphere', 1.05, 'kg', NULL, 'Virgin PET granulate [GLO]');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_2', 1, 'technosphere', 0.28, 'kWh', NULL, 'CFE electricity grid mix 230kV [MX]');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_3', 1, 'technosphere', 0.015, 'm3', NULL, 'Demineralized process cooling water [MX]');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_OUT_100001_2', 0, 'waste', 0.05, 'kg', NULL, 'Purge PET plastic scrap (Waste)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_OUT_100001_3', 0, 'biosphere', 0.012, 'kg', NULL, 'Fossil CO2 emissions [Air]');")

        # Proceso 2: Soplado (100002) - conectado a 100001 vía FL_PREFORMA
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_BOTELLA', 0, 'production', 1.0, 'u', NULL, 'Finished PET bottle 500ml');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_PREFORMA', 1, 'technosphere', 1.0, 'kg', 100001, 'Clear PET preform (Connected Flow)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_INP_100002_2', 1, 'technosphere', 0.45, 'm3', NULL, 'High-pressure compressed air (40 bar)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_INP_100002_3', 1, 'technosphere', 0.14, 'kWh', NULL, 'Thermoforming electricity CFE');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_OUT_100002_2', 0, 'waste', 0.002, 'kg', NULL, 'Plastic trimming scrap (Waste)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_OUT_100002_3', 0, 'biosphere', 0.005, 'MJ', NULL, 'Dissipated waste heat [Air]');")

        # Proceso 3: Distribución (100003) - conectado a 100002 vía FL_BOTELLA
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_LOGISTICA', 0, 'production', 1.0, 'u', NULL, 'Bottle distributed at distribution center');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_BOTELLA', 1, 'technosphere', 1.0, 'u', 100002, 'Finished PET bottle 500ml (Connected Flow)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_INP_100003_2', 1, 'technosphere', 0.008, 'l', NULL, 'Automotive diesel fuel');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_INP_100003_3', 1, 'technosphere', 0.0084, 't·km', NULL, 'Freight lorry transport 16-32t [MX]');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_OUT_100003_2', 0, 'waste', 0.0001, 'kg', NULL, 'Used lubricant oil (Waste)');")
        conn.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_OUT_100003_3', 0, 'biosphere', 0.021, 'kg', NULL, 'Diesel combustion emissions CO2 / NOx [Air]');")

        # Conectar edges:
        # Edge 1: 100001 -> 100002 (Clear PET preform, 1.0 kg)
        # Edge 2: 100002 -> 100003 (Finished PET bottle 500ml, 1.0 u)
        conn.execute("""
            INSERT OR REPLACE INTO product_system_edges (
                system_id, source_process_id, target_process_id, flow_id, amount, description
            ) VALUES (?, 100001, 100002, 'FL_PREFORMA', 1.000, 'Injected clear PET preform');
        """, (sys_id,))
        conn.execute("""
            INSERT OR REPLACE INTO product_system_edges (
                system_id, source_process_id, target_process_id, flow_id, amount, description
            ) VALUES (?, 100002, 100003, 'FL_BOTELLA', 1.000, 'Blow molded 500ml PET bottle');
        """, (sys_id,))

        # Fijar proceso de referencia al proceso final (100003 - Distribución)
        conn.execute("UPDATE product_systems SET reference_process_id = 100003 WHERE id = ?;", (sys_id,))

    return sys_id

# Datos enriquecidos estructurados para frontend y exportadores
OFFICIAL_SYSTEM_SPEC = {
    "system_id": "SYS-PET-CIRCULAR-01",
    "name": "Official Product System: Circular PET Bottle 500ml",
    "code": "SYS-PET-CIRCULAR-01",
    "functional_unit": "1.000 u (500ml PET bottle with cap and label)",
    "boundary": "Cradle-to-Gate (From cradle to distribution center gate)",
    "processes": [
        {
            "id": "node_inyeccion",
            "process_id": 100001,
            "code": "PR-PET-INJ-01",
            "name": "PET Preform Injection Molding",
            "category": "Polymer Transformation",
            "location": "[MX] Querétaro",
            "x": 60,
            "y": 140,
            "reference_flow": {
                "name": "Clear PET preform",
                "amount": 1.000,
                "unit": "kg",
                "type": "PRODUCT_FLOW"
            },
            "inputs": [
                {
                    "name": "Virgin PET granulate [GLO]",
                    "amount": 1.050,
                    "unit": "kg",
                    "type": "UNIT_PROCESS_FLOW",
                    "origin": "ecoinvent 3.12 Cutoff CPC 34710",
                    "is_unit": True,
                    "comment": "Resina PET virgen grado inyección con IV 0.82 dl/g",
                    "assumptions": "Considera 5% de merma de purga según estándar Husky HyPET",
                    "external_links": "https://www.petcore-europe.org"
                },
                {
                    "name": "CFE electricity grid mix 230kV [MX]",
                    "amount": 0.280,
                    "unit": "kWh",
                    "type": "TECHNOSPHERE_INPUT",
                    "origin": "CFE National Grid 2026",
                    "is_unit": False,
                    "comment": "Factor de emisión oficial del Sistema Eléctrico Nacional SEN",
                    "assumptions": "0.438 kg CO2 eq/kWh publicado por la Comisión Reguladora de Energía",
                    "external_links": "https://www.gob.mx/cre"
                },
                {
                    "name": "Demineralized process cooling water [MX]",
                    "amount": 0.015,
                    "unit": "m3",
                    "type": "RESOURCE_INPUT",
                    "origin": "Plant Industrial Well",
                    "is_unit": False,
                    "comment": "Agua de enfriamiento de circuito semicerrado industrial",
                    "assumptions": "Reposición de pérdidas por evaporación del 1.5% del volumen circulante",
                    "external_links": "https://www.conagua.gob.mx"
                }
            ],
            "outputs": [
                {
                    "name": "Clear PET preform",
                    "amount": 1.000,
                    "unit": "kg",
                    "type": "REFERENCE_PRODUCT",
                    "is_reference": True,
                    "comment": "Preforma transparente cuello PCO 1881 de 24.0 gramos",
                    "assumptions": "Flujo de referencia cuantitativo del proceso unitario (1 kg = 41.67 preformas)",
                    "external_links": "https://www.isbt.com"
                },
                {
                    "name": "Purge PET plastic scrap (Waste)",
                    "amount": 0.050,
                    "unit": "kg",
                    "type": "WASTE_FLOW",
                    "is_waste": True,
                    "fate": "Closed-loop internal mechanical recycling",
                    "comment": "Merma de purga de arranque y cambio de molde",
                    "assumptions": "100% segregado y triturado para recirculación interna en circuito cerrado",
                    "external_links": "https://iso.org/standard/38498.html"
                },
                {
                    "name": "Fossil CO2 emissions [Air]",
                    "amount": 0.012,
                    "unit": "kg",
                    "type": "ELEMENTARY_FLOW",
                    "is_elementary": True,
                    "compartment": "Air",
                    "comment": "Emisiones directas por calentamiento térmico de cilindro",
                    "assumptions": "Cálculo estequiométrico basado en Directrices IPCC 2006 (Volumen 3)",
                    "external_links": "https://www.ipcc-nggip.iges.or.jp"
                }
            ]
        },
        {
            "id": "node_soplado",
            "process_id": 100002,
            "code": "PR-PET-BLOW-02",
            "name": "PET Bottle Stretch Blow Molding",
            "category": "Thermoforming & Blow Molding",
            "location": "[MX] Estado de México",
            "x": 420,
            "y": 140,
            "reference_flow": {
                "name": "Finished PET bottle 500ml",
                "amount": 1.000,
                "unit": "u",
                "type": "PRODUCT_FLOW"
            },
            "inputs": [
                {
                    "name": "Clear PET preform (Connected Flow)",
                    "amount": 1.000,
                    "unit": "kg",
                    "type": "UNIT_PROCESS_FLOW",
                    "origin": "PET Preform Injection Molding",
                    "is_unit": True,
                    "comment": "Preforma alimentada directamente desde el proceso de inyeccion previo",
                    "assumptions": "Relacion 1:1 estequiometrica con factor de perdida por calentamiento infrarrojo del 0.2%",
                    "external_links": "https://www.sidel.com"
                },
                {
                    "name": "High-pressure compressed air (40 bar)",
                    "amount": 0.450,
                    "unit": "m3",
                    "type": "TECHNOSPHERE_INPUT",
                    "origin": "Plant blow compressor",
                    "is_unit": False,
                    "comment": "Aire comprimido grado alimentario libre de aceite para soplado bi-orientado",
                    "assumptions": "Presion de 40 bar generada con compresor reciprocante Belliss & Morcom",
                    "external_links": "https://www.gardnerdenver.com"
                },
                {
                    "name": "Thermoforming electricity CFE",
                    "amount": 0.140,
                    "unit": "kWh",
                    "type": "TECHNOSPHERE_INPUT",
                    "origin": "CFE National Grid 2026",
                    "is_unit": False,
                    "comment": "Consumo electrico de lamparas infrarrojas y soplado rotativo",
                    "assumptions": "Consumo promedio medido en linea de 12000 botellas/hora",
                    "external_links": "https://www.cfe.mx"
                }
            ],
            "outputs": [
                {
                    "name": "Finished PET bottle 500ml",
                    "amount": 1.000,
                    "unit": "u",
                    "type": "REFERENCE_PRODUCT",
                    "is_reference": True,
                    "comment": "Botella PET estirada y soplada cuello 28mm lista para embotellado",
                    "assumptions": "Peso final unitario de 24.0 gramos verificado en bascula analitica",
                    "external_links": "https://www.petcore-europe.org"
                },
                {
                    "name": "Plastic trimming scrap (Waste)",
                    "amount": 0.002,
                    "unit": "kg",
                    "type": "WASTE_FLOW",
                    "is_waste": True,
                    "fate": "Regrind for secondary pallets",
                    "comment": "Botellas con deformacion dimensional o defecto de pared en prueba optica",
                    "assumptions": "Tasa de rechazo controlada en 0.2%, triturada para reuso externo",
                    "external_links": "https://www.iso.org/standard/38498.html"
                },
                {
                    "name": "Dissipated waste heat [Air]",
                    "amount": 0.005,
                    "unit": "MJ",
                    "type": "ELEMENTARY_FLOW",
                    "is_elementary": True,
                    "compartment": "Air",
                    "comment": "Calor residual disipado por ventilacion forzada en tunel de enfriamiento",
                    "assumptions": "Entalpia de conveccion calculada a partir del gradiente termico de 95C a 25C",
                    "external_links": "https://www.ashrae.org"
                }
            ]
        },
        {
            "id": "node_transporte",
            "process_id": 100003,
            "code": "PR-PET-LOG-03",
            "name": "PET Bottle Distribution & Logistics",
            "category": "Distribution & Transport",
            "location": "[MX] Central-Northern Corridor",
            "x": 780,
            "y": 140,
            "reference_flow": {
                "name": "Bottle distributed at distribution center",
                "amount": 1.000,
                "unit": "u",
                "type": "PRODUCT_FLOW"
            },
            "inputs": [
                {
                    "name": "Finished PET bottle 500ml (Connected Flow)",
                    "amount": 1.000,
                    "unit": "u",
                    "type": "UNIT_PROCESS_FLOW",
                    "origin": "PET Bottle Stretch Blow Molding",
                    "is_unit": True,
                    "comment": "Botellas paletizadas en corrugado con film estirable",
                    "assumptions": "Embalaje terciario de 2400 botellas por palet europeo estandar",
                    "external_links": "https://www.epal-pallets.org"
                },
                {
                    "name": "Automotive diesel fuel",
                    "amount": 0.008,
                    "unit": "l",
                    "type": "TECHNOSPHERE_INPUT",
                    "origin": "Fuel Distribution Terminal",
                    "is_unit": False,
                    "comment": "Diesel ultra bajo azufre (UBA) para transporte de carga pesada",
                    "assumptions": "Consumo de 2.8 km por litro bajo regimen de autopista",
                    "external_links": "https://www.pemex.com"
                },
                {
                    "name": "Freight lorry transport 16-32t [MX]",
                    "amount": 0.0084,
                    "unit": "t·km",
                    "type": "TECHNOSPHERE_INPUT",
                    "origin": "ecoinvent 3.12 Cutoff (350 km)",
                    "is_unit": False,
                    "comment": "Camion articulado de 3 ejes con carga util promedio de 24 toneladas",
                    "assumptions": "Distancia de traslado de 350 km entre planta y centro de distribucion",
                    "external_links": "https://www.sct.gob.mx"
                }
            ],
            "outputs": [
                {
                    "name": "Bottle distributed at distribution center",
                    "amount": 1.000,
                    "unit": "u",
                    "type": "REFERENCE_PRODUCT",
                    "is_reference": True,
                    "comment": "Botella entregada en muelle de recepcion de CEDIS regional",
                    "assumptions": "Criterio de asignacion Cradle-to-Gate + Distribution segun ISO 14044",
                    "external_links": "https://www.iso.org/standard/37456.html"
                },
                {
                    "name": "Used lubricant oil (Waste)",
                    "amount": 0.0001,
                    "unit": "kg",
                    "type": "WASTE_FLOW",
                    "is_waste": True,
                    "fate": "Certified cement co-processing",
                    "comment": "Aceite lubricante usado drenado durante mantenimiento preventivo de tractocamion",
                    "assumptions": "Generacion de 100g por cada 1000 km recorridos, entregado a co-procesamiento",
                    "external_links": "https://www.semarnat.gob.mx"
                },
                {
                    "name": "Diesel combustion emissions CO2 / NOx [Air]",
                    "amount": 0.021,
                    "unit": "kg",
                    "type": "ELEMENTARY_FLOW",
                    "is_elementary": True,
                    "compartment": "Air",
                    "comment": "Emisiones directas de escape de tractocamion norma Euro V / NOM-044",
                    "assumptions": "Factores de emision de ecoinvent 3.12 Cutoff para camiones 16-32t",
                    "external_links": "https://www.eea.europa.eu"
                }
            ]
        }
    ],
    "edges": [
        {
            "id": "edge_1_2",
            "from": "node_inyeccion",
            "to": "node_soplado",
            "flow": "Clear PET preform",
            "amount": 1.000,
            "unit": "kg",
            "type": "mass"
        },
        {
            "id": "edge_2_3",
            "from": "node_soplado",
            "to": "node_transporte",
            "flow": "Finished PET bottle 500ml",
            "amount": 1.000,
            "unit": "u",
            "type": "mass"
        }
    ]
}

