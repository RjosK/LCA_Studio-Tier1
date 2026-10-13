"""
econode_studio/domain/ - Capa de Dominio (Enterprise Business Rules)
Siguiendo los principios de Clean Architecture:
Entidades puras y reglas de negocio esenciales sin dependencias de frameworks ni infraestructura.
"""

from .user_account import UserAccount, RoleEnum
from .product_system import ProductSystem, ProcessNode, SystemEdge
from .lci_exchange import LciExchange, LciProcessSummary
from .audit_checklist import (
    AuditClause, AuditStandard, OFFICIAL_CLAUSES, OFFICIAL_STANDARDS, calculate_audit_compliance
)
from .audit_comment import AuditComment
from .vault_document import VaultDocument
