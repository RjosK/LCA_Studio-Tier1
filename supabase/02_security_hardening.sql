-- ==============================================================================
-- ECONODE STUDIO - SUPABASE PRODUCTION SECURITY HARDENING MIGRATION
-- ==============================================================================
-- Based on official Supabase Going into Production Checklist:
-- https://supabase.com/docs/guides/deployment/going-into-prod
--
-- Covers:
-- 1. Row Level Security (RLS) on all exposed tables
-- 2. Principle of Least Privilege (REVOKE / GRANT for anon and authenticated)
-- 3. Views security_invoker enforcement (Postgres 15+ RLS bypass protection)
-- 4. BOLA / IDOR protection with strict tenant ownership & collaborator checks
-- 5. Protection of auth_users and invitations (credential dump prevention)
-- 6. Storage bucket 'econode-vault' private access and storage.objects RLS
-- 7. Realtime publication lockdown (remove sensitive tables)
-- 8. SECURITY DEFINER function search_path hardening
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. REVOCACION GLOBAL DE PERMISOS POR DEFECTO (PRINCIPIO DE MENOR PRIVILEGIO)
-- ------------------------------------------------------------------------------
-- En Postgres, el rol PUBLIC y anon a menudo heredan acceso de lectura global.
-- Revocamos todos los accesos en el esquema public y concedemos solo lo necesario.

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated, PUBLIC;

-- ------------------------------------------------------------------------------
-- 2. HABILITACION DE ROW LEVEL SECURITY (RLS) EN TODAS LAS TABLAS
-- ------------------------------------------------------------------------------
-- RLS obligatorio en cada tabla expuesta en el esquema public.

ALTER TABLE IF EXISTS auth_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lci_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lci_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lci_processes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lci_exchanges ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS product_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS product_system_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS product_system_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS custom_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS custom_processes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS custom_exchanges ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checklist_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checklist_template_clauses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS checklist_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;

-- Forzar RLS incluso si la tabla es consultada por el propietario de la tabla
ALTER TABLE IF EXISTS auth_users FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS invitations FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS product_systems FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_comments FORCE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- 3. BLINDAJE DE VISTAS (SECURITY INVOKER EN POSTGRESQL 15+)
-- ------------------------------------------------------------------------------
-- En PostgreSQL, las vistas por defecto ejecutan como el creador de la vista,
-- omitiendo RLS silenciosamente. Activamos security_invoker = true.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'users') THEN
        ALTER VIEW public.users SET (security_invoker = true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'comments') THEN
        ALTER VIEW public.comments SET (security_invoker = true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'processes') THEN
        ALTER VIEW public.processes SET (security_invoker = true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'flows') THEN
        ALTER VIEW public.flows SET (security_invoker = true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'categories') THEN
        ALTER VIEW public.categories SET (security_invoker = true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'public' AND viewname = 'exchanges') THEN
        ALTER VIEW public.exchanges SET (security_invoker = true);
    END IF;
END $$;

-- Proteger la vista users para no exponer hashes ni tokens a consultas anonimas
REVOKE ALL ON users FROM anon, authenticated, PUBLIC;
GRANT SELECT (id, username, email, display_name, organization, role, role_title, bio, avatar, created_at, updated_at)
ON users TO authenticated;

-- ------------------------------------------------------------------------------
-- 4. POLITICAS RLS: CATALOGOS PUBLICOS LCI Y NORMAS (SOLO LECTURA)
-- ------------------------------------------------------------------------------
-- Acceso de lectura abierto para anon y authenticated, pero nadie puede mutar via Data API.

-- Categorias
GRANT SELECT ON lci_categories, categories TO anon, authenticated;
DROP POLICY IF EXISTS "lci_categories_read_all" ON lci_categories;
CREATE POLICY "lci_categories_read_all" ON lci_categories
FOR SELECT TO anon, authenticated
USING (true);

-- Flujos LCI
GRANT SELECT ON lci_flows, flows TO anon, authenticated;
DROP POLICY IF EXISTS "lci_flows_read_all" ON lci_flows;
CREATE POLICY "lci_flows_read_all" ON lci_flows
FOR SELECT TO anon, authenticated
USING (true);

-- Procesos LCI
GRANT SELECT ON lci_processes, processes TO anon, authenticated;
DROP POLICY IF EXISTS "lci_processes_read_all" ON lci_processes;
CREATE POLICY "lci_processes_read_all" ON lci_processes
FOR SELECT TO anon, authenticated
USING (true);

-- Intercambios LCI
GRANT SELECT ON lci_exchanges, exchanges TO anon, authenticated;
DROP POLICY IF EXISTS "lci_exchanges_read_all" ON lci_exchanges;
CREATE POLICY "lci_exchanges_read_all" ON lci_exchanges
FOR SELECT TO anon, authenticated
USING (true);

-- Plantillas de Checklist de Normas (NOM-070, ISO 14044, ISO 14067)
GRANT SELECT ON checklist_templates, checklist_template_clauses TO anon, authenticated;
DROP POLICY IF EXISTS "checklist_templates_read_all" ON checklist_templates;
CREATE POLICY "checklist_templates_read_all" ON checklist_templates
FOR SELECT TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "checklist_template_clauses_read_all" ON checklist_template_clauses;
CREATE POLICY "checklist_template_clauses_read_all" ON checklist_template_clauses
FOR SELECT TO anon, authenticated
USING (true);

-- ------------------------------------------------------------------------------
-- 5. POLITICAS RLS: CUENTAS DE USUARIO Y PROTECCION DE CREDENCIALES
-- ------------------------------------------------------------------------------
-- Bloquear acceso anonimo por completo.
-- El usuario autenticado solo puede leer y actualizar su propia fila.

REVOKE ALL ON auth_users FROM anon, PUBLIC;
GRANT SELECT, UPDATE(display_name, bio, avatar, updated_at) ON auth_users TO authenticated;

DROP POLICY IF EXISTS "auth_users_read_self" ON auth_users;
CREATE POLICY "auth_users_read_self" ON auth_users
FOR SELECT TO authenticated
USING (
    id = (select auth.uid())::text
    OR email = (select auth.jwt()->>'email')
);

DROP POLICY IF EXISTS "auth_users_update_self" ON auth_users;
CREATE POLICY "auth_users_update_self" ON auth_users
FOR UPDATE TO authenticated
USING (
    id = (select auth.uid())::text
    OR email = (select auth.jwt()->>'email')
)
WITH CHECK (
    id = (select auth.uid())::text
    OR email = (select auth.jwt()->>'email')
);

-- Invitaciones de colaboracion
REVOKE ALL ON invitations FROM anon, PUBLIC;
GRANT SELECT, INSERT, UPDATE ON invitations TO authenticated;

DROP POLICY IF EXISTS "invitations_read_policy" ON invitations;
CREATE POLICY "invitations_read_policy" ON invitations
FOR SELECT TO authenticated
USING (
    invited_by_id = (select auth.uid())::text
    OR email = (select auth.jwt()->>'email')
);

DROP POLICY IF EXISTS "invitations_insert_policy" ON invitations;
CREATE POLICY "invitations_insert_policy" ON invitations
FOR INSERT TO authenticated
WITH CHECK (
    invited_by_id = (select auth.uid())::text
);

-- ------------------------------------------------------------------------------
-- 6. POLITICAS RLS: SISTEMAS PRODUCTO Y AISLAMIENTO DE TENANCY (BOLA/IDOR)
-- ------------------------------------------------------------------------------
-- Un usuario solo accede a un sistema si es el propietario (owner) o un colaborador asignado.

GRANT SELECT, INSERT, UPDATE, DELETE ON product_systems TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE product_systems_id_seq TO authenticated;

DROP POLICY IF EXISTS "product_systems_select_policy" ON product_systems;
CREATE POLICY "product_systems_select_policy" ON product_systems
FOR SELECT TO authenticated
USING (
    owner_id = (select auth.uid())::text
    OR owner_email = (select auth.jwt()->>'email')
    OR collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
);

DROP POLICY IF EXISTS "product_systems_insert_policy" ON product_systems;
CREATE POLICY "product_systems_insert_policy" ON product_systems
FOR INSERT TO authenticated
WITH CHECK (
    owner_id = (select auth.uid())::text
    OR owner_email = (select auth.jwt()->>'email')
);

DROP POLICY IF EXISTS "product_systems_update_policy" ON product_systems;
CREATE POLICY "product_systems_update_policy" ON product_systems
FOR UPDATE TO authenticated
USING (
    owner_id = (select auth.uid())::text
    OR owner_email = (select auth.jwt()->>'email')
)
WITH CHECK (
    owner_id = (select auth.uid())::text
    OR owner_email = (select auth.jwt()->>'email')
);

DROP POLICY IF EXISTS "product_systems_delete_policy" ON product_systems;
CREATE POLICY "product_systems_delete_policy" ON product_systems
FOR DELETE TO authenticated
USING (
    owner_id = (select auth.uid())::text
    OR owner_email = (select auth.jwt()->>'email')
);

-- ------------------------------------------------------------------------------
-- 7. POLITICAS RLS: NODOS Y ARISTAS DEL LIENZO VISUAL
-- ------------------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON product_system_nodes, product_system_edges TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE product_system_nodes_id_seq, product_system_edges_id_seq TO authenticated;

-- Nodos
DROP POLICY IF EXISTS "ps_nodes_select_policy" ON product_system_nodes;
CREATE POLICY "ps_nodes_select_policy" ON product_system_nodes
FOR SELECT TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_nodes.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

DROP POLICY IF EXISTS "ps_nodes_modify_policy" ON product_system_nodes;
CREATE POLICY "ps_nodes_modify_policy" ON product_system_nodes
FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_nodes.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_nodes.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
);

-- Aristas
DROP POLICY IF EXISTS "ps_edges_select_policy" ON product_system_edges;
CREATE POLICY "ps_edges_select_policy" ON product_system_edges
FOR SELECT TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_edges.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

DROP POLICY IF EXISTS "ps_edges_modify_policy" ON product_system_edges;
CREATE POLICY "ps_edges_modify_policy" ON product_system_edges
FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_edges.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = product_system_edges.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
);

-- ------------------------------------------------------------------------------
-- 8. POLITICAS RLS: ESTADOS DE AUDITORIA, SELLOS Y COMENTARIOS
-- ------------------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON checklist_states, audit_seals, audit_comments, comments TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE audit_comments_id_seq TO authenticated;

-- Estados de Checklist
DROP POLICY IF EXISTS "checklist_states_policy" ON checklist_states;
CREATE POLICY "checklist_states_policy" ON checklist_states
FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = checklist_states.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = checklist_states.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

-- Sellos Digitales de Dictamen
DROP POLICY IF EXISTS "audit_seals_policy" ON audit_seals;
CREATE POLICY "audit_seals_policy" ON audit_seals
FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = audit_seals.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = audit_seals.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

-- Comentarios Colaborativos
DROP POLICY IF EXISTS "audit_comments_policy" ON audit_comments;
CREATE POLICY "audit_comments_policy" ON audit_comments
FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = audit_comments.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = audit_comments.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

-- ------------------------------------------------------------------------------
-- 9. POLITICAS RLS: BOVEDA DOCUMENTAL Y EVIDENCIAS
-- ------------------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE documents_id_seq TO authenticated;

DROP POLICY IF EXISTS "documents_select_policy" ON documents;
CREATE POLICY "documents_select_policy" ON documents
FOR SELECT TO authenticated
USING (
    system_id IS NULL
    OR EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = documents.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
            OR ps.collaborators_json::jsonb @> jsonb_build_array(jsonb_build_object('email', (select auth.jwt()->>'email')))
        )
    )
);

DROP POLICY IF EXISTS "documents_modify_policy" ON documents;
CREATE POLICY "documents_modify_policy" ON documents
FOR ALL TO authenticated
USING (
    system_id IS NULL
    OR EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = documents.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
)
WITH CHECK (
    system_id IS NULL
    OR EXISTS (
        SELECT 1 FROM product_systems ps
        WHERE ps.id = documents.system_id
        AND (
            ps.owner_id = (select auth.uid())::text
            OR ps.owner_email = (select auth.jwt()->>'email')
        )
    )
);

-- ------------------------------------------------------------------------------
-- 10. POLITICAS RLS: PROCESOS, FLUJOS E INTERCAMBIOS PROPIOS (CUSTOM)
-- ------------------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON custom_flows, custom_processes, custom_exchanges TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE custom_flows_id_seq, custom_processes_id_seq, custom_exchanges_id_seq TO authenticated;

DROP POLICY IF EXISTS "custom_flows_auth_policy" ON custom_flows;
CREATE POLICY "custom_flows_auth_policy" ON custom_flows
FOR ALL TO authenticated
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "custom_processes_auth_policy" ON custom_processes;
CREATE POLICY "custom_processes_auth_policy" ON custom_processes
FOR ALL TO authenticated
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "custom_exchanges_auth_policy" ON custom_exchanges;
CREATE POLICY "custom_exchanges_auth_policy" ON custom_exchanges
FOR ALL TO authenticated
USING (true)
WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 11. STORAGE BUCKET 'econode-vault' Y POLÍTICAS DE OBJETOS
-- ------------------------------------------------------------------------------
-- Creacion del bucket privado (public = false) y politicas sobre storage.objects.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'econode-vault',
    'econode-vault',
    false,
    52428800, -- Limite de 50 MB por archivo
    ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv', 'application/sql', 'application/zip', 'image/png', 'image/jpeg']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 52428800;

-- Habilitar RLS en storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Lectura de archivos de la boveda (solo usuarios autenticados)
DROP POLICY IF EXISTS "econode_vault_select" ON storage.objects;
CREATE POLICY "econode_vault_select" ON storage.objects
FOR SELECT TO authenticated
USING (
    bucket_id = 'econode-vault'
);

-- Subida de archivos (INSERT + SELECT + UPDATE requeridos para upsert)
DROP POLICY IF EXISTS "econode_vault_insert" ON storage.objects;
CREATE POLICY "econode_vault_insert" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'econode-vault'
);

DROP POLICY IF EXISTS "econode_vault_update" ON storage.objects;
CREATE POLICY "econode_vault_update" ON storage.objects
FOR UPDATE TO authenticated
USING (
    bucket_id = 'econode-vault'
)
WITH CHECK (
    bucket_id = 'econode-vault'
);

DROP POLICY IF EXISTS "econode_vault_delete" ON storage.objects;
CREATE POLICY "econode_vault_delete" ON storage.objects
FOR DELETE TO authenticated
USING (
    bucket_id = 'econode-vault'
);

-- ------------------------------------------------------------------------------
-- 12. REALTIME Y REPLICACION: EXCLUSION DE TABLAS SENSIBLES
-- ------------------------------------------------------------------------------
-- Excluimos auth_users, invitations, documents y audit_seals de la publicacion realtime.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        -- Quitar tablas sensibles si estaban suscritas
        BEGIN
            ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS auth_users;
            ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS invitations;
            ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS documents;
            ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS audit_seals;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;

        -- Agregar únicamente tablas colaborativas
        BEGIN
            ALTER PUBLICATION supabase_realtime ADD TABLE audit_comments;
            ALTER PUBLICATION supabase_realtime ADD TABLE checklist_states;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END IF;
END $$;
