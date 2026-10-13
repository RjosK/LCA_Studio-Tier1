-- ==============================================================================
-- ECONODE STUDIO - SUPABASE POSTGRESQL SCHEMA & SEED SCRIPT (TIER 1 STUDIO)
-- ==============================================================================
-- Compatible con Supabase PostgreSQL 15+, Row Level Security (RLS) y Vercel Serverless.
-- Ejecuta este script en el SQL Editor de tu proyecto en https://supabase.com/dashboard
-- o de forma 100% automática con: python supabase/migrate_to_supabase.py "<DATABASE_URL>"
-- ==============================================================================

-- 1. Habilitar Extensiones Necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ------------------------------------------------------------------------------
-- 2. Autenticación y Cuentas de Usuario (RBAC)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    organization TEXT DEFAULT 'BioPack Industrial S.A. de C.V.',
    role TEXT NOT NULL DEFAULT 'analyst', -- 'analyst', 'auditor', 'client'
    role_title TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    avatar TEXT DEFAULT '',
    token TEXT DEFAULT '',
    permissions_json TEXT DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(lower(email));
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(lower(username));

-- Vista de compatibilidad para código que consulte 'users'
CREATE OR REPLACE VIEW users AS
SELECT 
    id,
    username,
    email,
    password_hash,
    display_name,
    organization,
    role,
    role_title,
    bio,
    avatar,
    token,
    permissions_json,
    created_at,
    updated_at
FROM auth_users;

-- ------------------------------------------------------------------------------
-- 3. Categorías Industriales LCI
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lci_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_type VARCHAR(64) DEFAULT 'process',
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_lci_categories_name ON lci_categories(name);

-- ------------------------------------------------------------------------------
-- 4. Catálogo de Flujos (Materiales, Insumos, Emisiones)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lci_flows (
    id VARCHAR(128) PRIMARY KEY,
    code VARCHAR(128),
    name VARCHAR(512) NOT NULL,
    flow_type VARCHAR(64) DEFAULT 'PRODUCT_FLOW',
    category_name VARCHAR(255) DEFAULT 'General',
    unit_symbol VARCHAR(32) DEFAULT 'kg',
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_lci_flows_name_trgm ON lci_flows USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_lci_flows_flow_type ON lci_flows(flow_type);

-- ------------------------------------------------------------------------------
-- 5. Catálogo Global de Procesos Unitarios LCI (ecoinvent 3.12 + Propios)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lci_processes (
    id BIGINT PRIMARY KEY,
    code VARCHAR(128) NOT NULL,
    name VARCHAR(512) NOT NULL,
    category_id INTEGER REFERENCES lci_categories(id) ON DELETE SET NULL,
    category_name VARCHAR(255) DEFAULT 'General',
    location VARCHAR(32) DEFAULT 'GLO',
    reference_flow_id VARCHAR(128),
    reference_flow_name VARCHAR(512),
    reference_amount NUMERIC DEFAULT 1.0,
    reference_unit VARCHAR(32) DEFAULT 'kg',
    description TEXT,
    is_custom BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lci_processes_name_trgm ON lci_processes USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_lci_processes_cat ON lci_processes(category_id);
CREATE INDEX IF NOT EXISTS idx_lci_processes_code ON lci_processes(code);

-- ------------------------------------------------------------------------------
-- 6. Intercambios Unitarios de Procesos (Entradas y Salidas)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lci_exchanges (
    id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES lci_processes(id) ON DELETE CASCADE,
    flow_id VARCHAR(128) NOT NULL,
    is_input BOOLEAN NOT NULL,
    exchange_type VARCHAR(32) NOT NULL, -- 'production', 'technosphere', 'biosphere', 'waste'
    amount NUMERIC NOT NULL DEFAULT 0.0,
    unit_symbol VARCHAR(32) DEFAULT 'kg',
    default_provider_id BIGINT,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_lci_exchanges_process_id ON lci_exchanges(process_id);
CREATE INDEX IF NOT EXISTS idx_lci_exchanges_type ON lci_exchanges(exchange_type);

-- ------------------------------------------------------------------------------
-- 7. Sistemas Producto (Proyectos de Ciclo de Vida y Modelado)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_systems (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(64) NOT NULL,
    target_amount NUMERIC DEFAULT 1.0,
    unit VARCHAR(32) DEFAULT 'u',
    functional_unit TEXT,
    boundary TEXT,
    description TEXT,
    reference_process_id BIGINT,
    owner_id TEXT REFERENCES auth_users(id) ON DELETE SET NULL,
    owner_email VARCHAR(255),
    owner_name VARCHAR(255),
    owner_role VARCHAR(32),
    owner_org VARCHAR(255),
    category VARCHAR(128) DEFAULT 'Polímeros',
    geography VARCHAR(64) DEFAULT '[MX]',
    status VARCHAR(64) DEFAULT 'in_audit', -- 'draft', 'in_audit', 'verified', 'archived'
    compliance_rate VARCHAR(32) DEFAULT '100.0%',
    collaborators_json TEXT DEFAULT '[]',
    parameters_json TEXT DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_systems_owner ON product_systems(owner_id);
CREATE INDEX IF NOT EXISTS idx_product_systems_code ON product_systems(code);

-- ------------------------------------------------------------------------------
-- 8. Nodos del Lienzo Visual (Normalización Relacional)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_system_nodes (
    id BIGSERIAL PRIMARY KEY,
    system_id BIGINT NOT NULL REFERENCES product_systems(id) ON DELETE CASCADE,
    process_id BIGINT NOT NULL,
    pos_x NUMERIC DEFAULT 100,
    pos_y NUMERIC DEFAULT 140,
    custom_name VARCHAR(255),
    node_metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_ps_nodes_system_id ON product_system_nodes(system_id);

-- ------------------------------------------------------------------------------
-- 9. Aristas y Conexiones del Lienzo Visual (Cables de Flujo)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_system_edges (
    id BIGSERIAL PRIMARY KEY,
    system_id BIGINT NOT NULL REFERENCES product_systems(id) ON DELETE CASCADE,
    source_process_id BIGINT,
    target_process_id BIGINT,
    flow_id VARCHAR(128),
    amount NUMERIC DEFAULT 1.0,
    unit VARCHAR(32) DEFAULT 'kg',
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_ps_edges_system_id ON product_system_edges(system_id);

-- ------------------------------------------------------------------------------
-- 10. Procesos, Flujos e Intercambios Propios Creados por Usuarios
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS custom_flows (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    flow_type VARCHAR(64) DEFAULT 'PRODUCT_FLOW',
    category_name VARCHAR(255) DEFAULT 'Custom processes & flows',
    unit_symbol VARCHAR(32) DEFAULT 'kg',
    description TEXT
);

CREATE TABLE IF NOT EXISTS custom_processes (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER DEFAULT 999999,
    location VARCHAR(32) DEFAULT 'GLO',
    reference_flow_id VARCHAR(128),
    reference_amount NUMERIC DEFAULT 1.0,
    description TEXT
);

CREATE TABLE IF NOT EXISTS custom_exchanges (
    id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL,
    flow_id VARCHAR(128) NOT NULL,
    is_input INTEGER NOT NULL CHECK(is_input IN (0, 1)),
    exchange_type VARCHAR(32) NOT NULL,
    amount NUMERIC NOT NULL,
    unit_symbol VARCHAR(32),
    default_provider_id BIGINT,
    description TEXT
);

-- ------------------------------------------------------------------------------
-- 11. Auditoría Normativa Multi-Estándar (Checklists & Dictámenes)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS checklist_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    standard_family TEXT NOT NULL,
    description TEXT,
    version TEXT DEFAULT '1.0',
    is_official INTEGER DEFAULT 0,
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checklist_template_clauses (
    checklist_id TEXT NOT NULL REFERENCES checklist_templates(id) ON DELETE CASCADE,
    clause_id TEXT NOT NULL,
    section TEXT NOT NULL,
    title TEXT NOT NULL,
    criterion TEXT NOT NULL,
    evidence_required TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    PRIMARY KEY (checklist_id, clause_id)
);

CREATE TABLE IF NOT EXISTS checklist_states (
    system_id BIGINT NOT NULL REFERENCES product_systems(id) ON DELETE CASCADE,
    clause_id TEXT NOT NULL,
    is_compliant INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    checklist_id TEXT DEFAULT 'nom070',
    PRIMARY KEY (system_id, clause_id)
);

CREATE TABLE IF NOT EXISTS audit_seals (
    system_id BIGINT PRIMARY KEY REFERENCES product_systems(id) ON DELETE CASCADE,
    digital_seal TEXT NOT NULL,
    signed_by TEXT,
    compliance_rate REAL,
    signed_at TEXT NOT NULL,
    checklist_id TEXT DEFAULT 'nom070'
);

-- ------------------------------------------------------------------------------
-- 12. Hilos de Observaciones y Comentarios Colaborativos
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_comments (
    id BIGSERIAL PRIMARY KEY,
    system_id BIGINT NOT NULL REFERENCES product_systems(id) ON DELETE CASCADE,
    author_name TEXT NOT NULL,
    author_role TEXT NOT NULL DEFAULT 'auditor',
    content TEXT NOT NULL,
    node_id TEXT,
    x REAL,
    y REAL,
    status TEXT NOT NULL DEFAULT 'open',
    resolved_by TEXT,
    resolved_at TEXT,
    reply TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_comments_sys ON audit_comments(system_id);

-- Vista de compatibilidad para código que consulte 'comments'
CREATE OR REPLACE VIEW comments AS
SELECT * FROM audit_comments;

-- ------------------------------------------------------------------------------
-- 13. Bóveda Documental y Evidencias de Auditoría
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    system_id BIGINT REFERENCES product_systems(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    disk_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_by TEXT NOT NULL,
    user_role TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_system ON documents(system_id);

-- ------------------------------------------------------------------------------
-- 14. Vistas de Compatibilidad hacia la Lógica de Negocio
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW processes AS
SELECT 
    p.id,
    p.code,
    p.name,
    p.category_id,
    p.location,
    p.reference_flow_id,
    p.reference_amount,
    p.description
FROM lci_processes p
UNION ALL
SELECT 
    cp.id + 1000000 as id,
    cp.code,
    cp.name,
    cp.category_id,
    cp.location,
    cp.reference_flow_id,
    cp.reference_amount,
    cp.description
FROM custom_processes cp;

CREATE OR REPLACE VIEW flows AS
SELECT 
    f.id,
    f.code,
    f.name,
    f.flow_type,
    f.category_name,
    f.unit_symbol,
    f.description
FROM lci_flows f
UNION ALL
SELECT 
    cf.code as id,
    cf.code,
    cf.name,
    cf.flow_type,
    cf.category_name,
    cf.unit_symbol,
    cf.description
FROM custom_flows cf;

CREATE OR REPLACE VIEW categories AS
SELECT 
    c.id,
    c.name,
    lower(c.category_type) as category_type,
    c.description
FROM lci_categories c;

CREATE OR REPLACE VIEW exchanges AS
SELECT 
    e.id,
    e.process_id,
    e.flow_id,
    case when e.is_input then 1 else 0 end as is_input,
    e.exchange_type,
    e.amount,
    e.unit_symbol,
    e.default_provider_id,
    e.description
FROM lci_exchanges e
UNION ALL
SELECT 
    ce.id + 5000000 as id,
    ce.process_id,
    ce.flow_id,
    ce.is_input,
    ce.exchange_type,
    ce.amount,
    ce.unit_symbol,
    ce.default_provider_id,
    ce.description
FROM custom_exchanges ce;

-- ==============================================================================
-- 15. SEED DATA OPERATIVO OFICIAL (TIER 1 STUDIO)
-- ==============================================================================

-- Categoría para procesos y flujos propios
INSERT INTO lci_categories (id, name, category_type, description)
VALUES (999999, 'Custom processes & flows', 'process', 'Processes and flows created by the user in ECONODE Studio')
ON CONFLICT (id) DO NOTHING;

-- Usuarios Oficiales Demo (Contraseña demo hash: pbkdf2 'demo1234')
INSERT INTO auth_users (id, username, email, password_hash, display_name, role, organization, role_title)
VALUES 
  ('analyst_carla', 'carla.mendez', 'carla.mendez@econode.io', '3278546b45a05b33fae991206f4ee590$e27d8ce673bce49635bf2a2cf67d4fdf894f79601a9791fa482c3c907147a5fb', 'Carla Méndez', 'analyst', 'BioPack Industrial S.A. de C.V.', 'Analista Senior de Ciclo de Vida'),
  ('auditor_lead', 'josue.auditor', 'josuearenteriaz09@gmail.com', '3278546b45a05b33fae991206f4ee590$e27d8ce673bce49635bf2a2cf67d4fdf894f79601a9791fa482c3c907147a5fb', 'Josué Arentería', 'auditor', 'Bureau Veritas / NOM Auditoría', 'Auditor Líder Certificado NOM-070'),
  ('client_elena', 'elena.ramirez', 'elena.ramirez@biopack-mexico.com', '3278546b45a05b33fae991206f4ee590$e27d8ce673bce49635bf2a2cf67d4fdf894f79601a9791fa482c3c907147a5fb', 'Elena Ramírez', 'client', 'BioPack Industrial S.A. de C.V.', 'Directora de Sostenibilidad')
ON CONFLICT (id) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  role = EXCLUDED.role,
  organization = EXCLUDED.organization;

-- Plantillas Oficiales de Normas
INSERT INTO checklist_templates (id, name, code, standard_family, description, version, is_official, created_by)
VALUES 
  ('nom070', 'NOM-070-SE-2024 (Verificación ACV y EPD)', 'NOM-070', 'Norma Oficial Mexicana', 'Estándar obligatorio para la verificación independiente de declaraciones ambientales de producto y huella de carbono en México.', '2024', 1, 'system'),
  ('iso14044', 'ISO 14044:2006 / Amd 2:2020 (Requisitos y Directrices ACV)', 'ISO-14044', 'ISO Internacional', 'Requisitos internacionales para inventario (LCI), evaluación de impacto (LCIA) e interpretación.', '2020', 1, 'system'),
  ('iso14067', 'ISO 14067:2018 (Huella de Carbono de Productos)', 'ISO-14067', 'ISO Huella de Carbono', 'Requisitos y directrices para la cuantificación de la huella de carbono de productos.', '2018', 1, 'system')
ON CONFLICT (id) DO NOTHING;

-- 18 Cláusulas de Auditoría Oficiales NOM-070
INSERT INTO checklist_template_clauses (checklist_id, clause_id, section, title, criterion, evidence_required, display_order)
VALUES
('nom070', 'NOM-4.1.1', '4.1 Generalidades', 'Requisitos de Verificación Independiente', 'Auditor calificado e independiente con acreditación NOM-070.', 'Cédula de acreditación de auditoría', 1),
('nom070', 'NOM-4.2.1', '4.2 Objetivo y Alcance', 'Definición del Objetivo', 'Objetivo del estudio de ACV formalmente especificado.', 'Documento de objetivos corporativos', 2),
('nom070', 'NOM-4.2.2', '4.2 Objetivo y Alcance', 'Público Objetivo y Aplicación', 'Identificación de audiencias y destinatarios del reporte EPD.', 'Definición de partes interesadas', 3),
('nom070', 'NOM-4.2.3.1', '4.2 Objetivo y Alcance', 'Función del Sistema Producto', 'Identificación de la función técnica y desempeño del envase.', 'Ficha técnica de especificación de botella', 4),
('nom070', 'NOM-4.2.3.2', '4.2 Objetivo y Alcance', 'Unidad Funcional', 'Unidad declarada cuantitativa y claramente especificada con UF de referencia.', '1.000 u (Botella 500ml con tapa)', 5),
('nom070', 'NOM-4.2.3.3', '4.2 Objetivo y Alcance', 'Límites del Sistema', 'Límites Cradle-to-Gate definidos con diagrama de flujo de procesos unitarios.', 'Diagrama de flujo validado en lienzo', 6),
('nom070', 'NOM-4.2.3.4', '4.2 Objetivo y Alcance', 'Requisitos de Calidad de Datos (DQI)', 'Evaluación de datos con matriz Pedigree e indicadores DQI.', 'Score 5/5 validado con ecoinvent 3.12', 7),
('nom070', 'NOM-4.3.1', '4.3 Inventario (LCI)', 'Procedimientos de Recopilación de Datos', 'Protocolos de medición directa de energía, insumos y mermas en planta.', 'Registros SCADA y facturas CFE', 8),
('nom070', 'NOM-4.3.4.1', '4.3 Inventario (LCI)', 'Criterios de Corte (Cut-off)', 'Regla de corte del 1% de masa y energía verificada. Sin omisiones relevantes.', 'Corte acumulado < 0.2% conforme', 9),
('nom070', 'NOM-4.3.4.2', '4.3 Inventario (LCI)', 'Balance de Masa y Materia', 'Suma de entradas igual a salidas + mermas con tolerancia estricta.', 'Balance elemental 100% equilibrado', 10),
('nom070', 'NOM-4.3.5.1', '4.3 Inventario (LCI)', 'Asignación y Coproductos', 'Reglas de corte físico aplicadas a la merma conforme a jerarquía ISO.', 'Cut-off estricto acreditado en bucle interno', 11),
('nom070', 'NOM-4.4.1', '4.4 Impacto (LCIA)', 'Marco Metodológico de Evaluación', 'Enfoque midpoint ambiental conforme a estándares internacionales.', 'Metodología ReCiPe / EF 3.1', 12),
('nom070', 'NOM-4.4.2.1', '4.4 Impacto (LCIA)', 'Selección de Métodos de Caracterización', 'Métodos de caracterización ambiental justificados y estandarizados.', 'IPCC 2021 GWP 100a', 13),
('nom070', 'NOM-4.4.4.1', '4.4 Impacto (LCIA)', 'Análisis de Contribución y Hotspots', 'Identificación de procesos clave que concentran emisiones y consumo.', 'Identificación de inyección y transporte', 14),
('nom070', 'NOM-4.5.1', '4.5 Interpretación', 'Evaluación de Incertidumbre y Sensibilidad', 'Sensibilidad paramétrica de mermas y distancia de logística.', 'Parámetros del sistema evaluados', 15),
('nom070', 'NOM-4.5.2', '4.5 Interpretación', 'Conclusiones y Recomendaciones', 'Recomendaciones fundamentadas en los resultados del inventario.', 'Recomendaciones de ecodiseño', 16),
('nom070', 'NOM-4.5.3.1', '4.5 Trazabilidad', 'Integridad Criptográfica SHA-256', 'Snapshot del modelo firmado con hash SHA-256 e inmutable en libro mayor.', 'Hash de integridad activo', 17),
('nom070', 'NOM-4.6.1.1', '4.6 Revisión Crítica', 'Dictamen de Verificación NOM-070', 'Dictamen independiente de verificador acreditado sin conflicto de interés.', 'Acreditación externa verificada', 18)
ON CONFLICT (checklist_id, clause_id) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 16. Sistema Producto Oficial (ID 21: Circular PET Bottle 500ml)
-- ------------------------------------------------------------------------------
INSERT INTO product_systems (
    id, name, code, target_amount, unit, functional_unit, boundary, description,
    reference_process_id, owner_id, owner_email, owner_name, owner_role, owner_org,
    category, geography, status, compliance_rate, collaborators_json
)
VALUES (
    21,
    'Official Product System: Circular PET Bottle 500ml',
    'SYS-PET-CIRCULAR-01',
    1.000,
    'u',
    '1.000 u (500ml PET bottle with cap and label)',
    'Cradle-to-Gate (From cradle to distribution center gate)',
    'Official reference product system for NOM-070-SE-2024 and ISO 14067 compliance audit. Models the complete polymer chain from preform injection molding to regional distribution center.',
    100003,
    'analyst_carla',
    'carla.mendez@econode.io',
    'Carla Méndez',
    'analyst',
    'BioPack Industrial S.A. de C.V.',
    'Polímeros',
    '[MX]',
    'verified',
    '100.0%',
    '[{"email": "josuearenteriaz09@gmail.com", "name": "Josué A.", "role": "auditor", "display_name": "Josué Arentería"}, {"email": "elena.ramirez@biopack-mexico.com", "name": "Elena R.", "role": "client", "display_name": "Elena Ramírez"}]'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    code = EXCLUDED.code,
    status = EXCLUDED.status,
    collaborators_json = EXCLUDED.collaborators_json;

-- Nodos del Sistema 21 en el Lienzo
INSERT INTO product_system_nodes (system_id, process_id, pos_x, pos_y, custom_name)
VALUES
  (21, 100001, 60, 140, 'PET Preform Injection Molding'),
  (21, 100002, 420, 140, 'PET Bottle Stretch Blow Molding'),
  (21, 100003, 780, 140, 'PET Bottle Distribution & Logistics')
ON CONFLICT DO NOTHING;

-- Aristas / Cables de Flujo del Sistema 21
INSERT INTO product_system_edges (system_id, source_process_id, target_process_id, flow_id, amount, unit, description)
VALUES
  (21, 100001, 100002, 'FL_PREFORMA', 1.000, 'kg', 'Clear PET preform'),
  (21, 100002, 100003, 'FL_BOTELLA', 1.000, 'u', 'Finished PET bottle 500ml')
ON CONFLICT DO NOTHING;

-- Sello de Auditoría Oficial del Sistema 21
INSERT INTO audit_seals (system_id, digital_seal, signed_by, compliance_rate, signed_at, checklist_id)
VALUES (
  21,
  'a4b892c90e1f72834b67d512a88e990c3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
  'Josué Arentería (Lead LCA Auditor)',
  100.0,
  NOW()::text,
  'nom070'
)
ON CONFLICT (system_id) DO NOTHING;

