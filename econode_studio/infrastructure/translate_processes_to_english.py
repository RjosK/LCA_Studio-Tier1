"""
translate_processes_to_english.py
Translates all user-created processes, custom flows, custom exchanges,
and product system parameters (canvas nodes & edges) to English in ecoinvent_312.db.
"""

import sqlite3
import json
import os

DB_PATH = r"C:\Users\Josue\Documents\Espacio\ECONODE\ecoinvent\ecoinvent_312.db"

def run_migration():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Update TBL_CATEGORIES 999999
    c.execute("""
        UPDATE TBL_CATEGORIES 
        SET NAME = 'Custom processes & flows', 
            DESCRIPTION = 'Custom processes and flows created by user in ECONODE Studio' 
        WHERE ID = 999999
    """)

    # 2. Update custom_processes
    c.execute("""
        UPDATE custom_processes 
        SET name = 'PET Preform Injection Molding', 
            description = 'Injection molding of clear PET preform with virgin input' 
        WHERE id = -899999
    """)
    c.execute("""
        UPDATE custom_processes 
        SET name = 'PET Bottle Stretch Blow Molding', 
            description = 'Stretch blow molding of 500ml PET bottle' 
        WHERE id = -899998
    """)
    c.execute("""
        UPDATE custom_processes 
        SET name = 'PET Bottle Distribution & Logistics', 
            description = 'Distribution logistics 350 km' 
        WHERE id = -899997
    """)
    c.execute("""
        UPDATE custom_processes 
        SET name = 'Trial Process', 
            description = 'User custom process created from canvas' 
        WHERE id = 30
    """)

    # 3. Update custom_flows
    c.execute("""
        UPDATE custom_flows 
        SET name = 'Trial Process', 
            category_name = 'Custom processes & flows', 
            description = 'Reference flow for Trial Process' 
        WHERE id = 9
    """)
    c.execute("""
        UPDATE custom_flows 
        SET category_name = 'Custom processes & flows' 
        WHERE category_name = 'Procesos y flujos propios'
    """)

    # 4. Update custom_exchanges
    c.execute("""
        UPDATE custom_exchanges 
        SET description = 'Reference flow: Trial Process' 
        WHERE id = 95
    """)

    c.execute("DELETE FROM custom_exchanges WHERE process_id IN (100001, 100002, 100003)")

    # 100001 exchanges
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_PREFORMA', 0, 'production', 1.0, 'kg', NULL, 'Clear PET preform')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_1', 1, 'technosphere', 1.05, 'kg', NULL, 'Virgin PET granulate [GLO]')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_2', 1, 'technosphere', 0.28, 'kWh', NULL, 'CFE electricity grid mix 230kV [MX]')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_INP_100001_3', 1, 'technosphere', 0.015, 'm3', NULL, 'Demineralized process cooling water [MX]')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_OUT_100001_2', 0, 'waste', 0.05, 'kg', NULL, 'Purge PET plastic scrap (Waste)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100001, 'FL_OUT_100001_3', 0, 'biosphere', 0.012, 'kg', NULL, 'Fossil CO2 emissions [Air]')")

    # 100002 exchanges
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_BOTELLA', 0, 'production', 1.0, 'u', NULL, 'Finished PET bottle 500ml')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_PREFORMA', 1, 'technosphere', 1.0, 'kg', 100001, 'Clear PET preform (Connected Flow)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_INP_100002_2', 1, 'technosphere', 0.45, 'm3', NULL, 'High-pressure compressed air (40 bar)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_INP_100002_3', 1, 'technosphere', 0.14, 'kWh', NULL, 'Thermoforming electricity CFE')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_OUT_100002_2', 0, 'waste', 0.002, 'kg', NULL, 'Plastic trimming scrap (Waste)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100002, 'FL_OUT_100002_3', 0, 'biosphere', 0.005, 'MJ', NULL, 'Dissipated waste heat [Air]')")

    # 100003 exchanges
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_LOGISTICA', 0, 'production', 1.0, 'u', NULL, 'Bottle distributed at distribution center')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_BOTELLA', 1, 'technosphere', 1.0, 'u', 100002, 'Finished PET bottle 500ml (Connected Flow)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_INP_100003_2', 1, 'technosphere', 0.008, 'l', NULL, 'Automotive diesel fuel')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_INP_100003_3', 1, 'technosphere', 0.0084, 't·km', NULL, 'Freight lorry transport 16-32t [MX]')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_OUT_100003_2', 0, 'waste', 0.0001, 'kg', NULL, 'Used lubricant oil (Waste)')")
    c.execute("INSERT INTO custom_exchanges (process_id, flow_id, is_input, exchange_type, amount, unit_symbol, default_provider_id, description) VALUES (100003, 'FL_OUT_100003_3', 0, 'biosphere', 0.021, 'kg', NULL, 'Diesel combustion emissions CO2 / NOx [Air]')")

    # 5. Update product_systems row 21
    sys21_nodes = [
        {
            "id": "node_inyeccion",
            "process_id": 100001,
            "name": "PET Preform Injection Molding",
            "category": "Polymer Transformation",
            "amount": 1.0,
            "unit": "kg",
            "x": 60.0,
            "y": 140.0,
            "pos_x": 60.0,
            "pos_y": 140.0,
            "reference_flow": {"name": "Clear PET preform", "amount": 1.0, "unit": "kg"},
            "inputs": [
                {"name": "Virgin PET granulate [GLO]", "amount": 1.05, "unit": "kg", "is_unit": True},
                {"name": "CFE electricity grid mix 230kV [MX]", "amount": 0.28, "unit": "kWh", "is_unit": False},
                {"name": "Demineralized process cooling water [MX]", "amount": 0.015, "unit": "m3", "is_unit": False}
            ],
            "outputs": [
                {"name": "Clear PET preform", "amount": 1.0, "unit": "kg", "is_reference": True},
                {"name": "Purge PET plastic scrap (Waste)", "amount": 0.05, "unit": "kg", "is_waste": True},
                {"name": "Fossil CO2 emissions [Air]", "amount": 0.012, "unit": "kg", "is_elementary": True}
            ]
        },
        {
            "id": "node_soplado",
            "process_id": 100002,
            "name": "PET Bottle Stretch Blow Molding",
            "category": "Thermoforming & Blow Molding",
            "amount": 1.0,
            "unit": "u",
            "x": 420.0,
            "y": 140.0,
            "pos_x": 420.0,
            "pos_y": 140.0,
            "reference_flow": {"name": "Finished PET bottle 500ml", "amount": 1.0, "unit": "u"},
            "inputs": [
                {"name": "Clear PET preform (Connected Flow)", "amount": 1.0, "unit": "kg", "is_unit": True},
                {"name": "High-pressure compressed air (40 bar)", "amount": 0.45, "unit": "m3", "is_unit": False},
                {"name": "Thermoforming electricity CFE", "amount": 0.14, "unit": "kWh", "is_unit": False}
            ],
            "outputs": [
                {"name": "Finished PET bottle 500ml", "amount": 1.0, "unit": "u", "is_reference": True},
                {"name": "Plastic trimming scrap (Waste)", "amount": 0.002, "unit": "kg", "is_waste": True},
                {"name": "Dissipated waste heat [Air]", "amount": 0.005, "unit": "MJ", "is_elementary": True}
            ]
        },
        {
            "id": "node_transporte",
            "process_id": 100003,
            "name": "PET Bottle Distribution & Logistics",
            "category": "Distribution & Transport",
            "amount": 1.0,
            "unit": "u",
            "x": 780.0,
            "y": 140.0,
            "pos_x": 780.0,
            "pos_y": 140.0,
            "reference_flow": {"name": "Bottle distributed at distribution center", "amount": 1.0, "unit": "u"},
            "inputs": [
                {"name": "Finished PET bottle 500ml (Connected Flow)", "amount": 1.0, "unit": "u", "is_unit": True},
                {"name": "Automotive diesel fuel", "amount": 0.008, "unit": "l", "is_unit": False},
                {"name": "Freight lorry transport 16-32t [MX]", "amount": 0.0084, "unit": "t·km", "is_unit": False}
            ],
            "outputs": [
                {"name": "Bottle distributed at distribution center", "amount": 1.0, "unit": "u", "is_reference": True},
                {"name": "Used lubricant oil (Waste)", "amount": 0.0001, "unit": "kg", "is_waste": True},
                {"name": "Diesel combustion emissions CO2 / NOx [Air]", "amount": 0.021, "unit": "kg", "is_elementary": True}
            ]
        }
    ]
    sys21_edges = [
        {"id": "edge_1_2", "from": "node_inyeccion", "to": "node_soplado", "flow": "Clear PET preform", "amount": 1.0, "unit": "kg", "type": "mass"},
        {"id": "edge_2_3", "from": "node_soplado", "to": "node_transporte", "flow": "Finished PET bottle 500ml", "amount": 1.0, "unit": "u", "type": "mass"}
    ]

    c.execute("SELECT parameters_json FROM product_systems WHERE id = 21")
    row = c.fetchone()
    p21 = json.loads(row[0]) if row and row[0] else {}
    p21["canvas_nodes"] = sys21_nodes
    p21["canvas_edges"] = sys21_edges
    c.execute("UPDATE product_systems SET parameters_json = ? WHERE id = 21", (json.dumps(p21, ensure_ascii=False),))

    # 6. Update product_systems row 390
    c.execute("SELECT parameters_json FROM product_systems WHERE id = 390")
    row390 = c.fetchone()
    if row390 and row390[0]:
        p390_str = row390[0]
        p390_str = p390_str.replace("prueba (Flujo Conectado)", "Trial Process (Connected Flow)")
        p390_str = p390_str.replace('"prueba"', '"Trial Process"')
        p390_str = p390_str.replace("Procesos y flujos propios", "Custom processes & flows")
        p390_str = p390_str.replace("Residuo plástico / Scrap (Waste)", "Plastic Scrap (Waste)")
        p390_str = p390_str.replace("Residuo pl\\u00e1stico / Scrap (Waste)", "Plastic Scrap (Waste)")
        p390_str = p390_str.replace('"Aire"', '"Air"')
        c.execute("UPDATE product_systems SET parameters_json = ? WHERE id = 390", (p390_str,))

    conn.commit()
    conn.close()
    print("MIGRATION COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    run_migration()

