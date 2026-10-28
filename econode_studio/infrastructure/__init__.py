"""
econode_studio/infrastructure/ - Adaptadores de Infraestructura (Database, Auth, Audit, Documents, Exporters, OAuth, Crypto)
"""
from .database_adapter import (
    get_active_db_connection,
    list_product_systems,
    get_product_system_details,
    create_product_system,
    save_system_canvas,
    search_lci_processes,
    get_process_technical_sheet
)
from .auth_adapter import (
    get_auth_db_connection,
    init_auth_db,
    get_all_users,
    get_user_by_id,
    get_user_by_identifier,
    get_user_by_role_or_identifier,
    insert_user,
    update_user_token,
    insert_invitation,
    get_invitation_by_token,
    get_pending_invitation_by_email,
    list_invitations_by_analyst,
    get_all_invitations,
    mark_invitation_accepted,
    cancel_invitation
)
from .audit_adapter import (
    get_audit_db_connection,
    init_audit_db,
    get_comments_by_system,
    insert_comment,
    resolve_comment,
    delete_comment,
    list_all_checklist_templates,
    get_checklist_template,
    save_custom_checklist_template,
    import_checklist_from_csv,
    delete_custom_checklist_template,
    get_checklist_clause_states,
    set_checklist_clause_state,
    get_audit_seal,
    save_audit_seal
)
from .documents_adapter import (
    init_documents_db,
    save_document,
    list_documents,
    get_document_file,
    delete_document
)
from .exporters_adapter import (
    export_openlca_jsonld_zip,
    export_ilcd_xml_zip,
    export_simapro_csv,
    export_lci_consolidated_csv,
    export_expediente_nom070_zip
)
from .google_oauth_adapter import verify_google_id_token, get_configured_client_id, resolve_role_for_email
from .crypto_signer import compute_model_sha256, sign_audit_dossier
