"""
econode_studio/domain/product_system.py - Entidad de Dominio Sistema Producto y Topología Nodal
Define las reglas de negocio para modelado de ciclo de vida (ISO 14040 / ISO 14044),
balance de masas elementales, validación topológica de grafos dirigidos (DAG) y multi-inquilino.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set


@dataclass
class ProcessNode:
    process_id: int
    process_code: str
    process_name: str
    location: str
    reference_amount: float
    category_name: str
    pos_x: float = 100.0
    pos_y: float = 100.0
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "process_code": self.process_code,
            "process_name": self.process_name,
            "location": self.location,
            "reference_amount": self.reference_amount,
            "category_name": self.category_name,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "inputs": self.inputs,
            "outputs": self.outputs
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessNode":
        return cls(
            process_id=int(data.get("process_id") or data.get("id") or 0),
            process_code=str(data.get("process_code") or data.get("code") or ""),
            process_name=str(data.get("process_name") or data.get("name") or "Proceso"),
            location=str(data.get("location") or "[GLO]"),
            reference_amount=float(data.get("reference_amount") or 1.0),
            category_name=str(data.get("category_name") or data.get("category") or "General"),
            pos_x=float(data.get("pos_x") or data.get("x") or 100.0),
            pos_y=float(data.get("pos_y") or data.get("y") or 100.0),
            inputs=list(data.get("inputs") or []),
            outputs=list(data.get("outputs") or [])
        )


@dataclass
class SystemEdge:
    source_process_id: int
    target_process_id: int
    flow_id: str
    flow_name: str
    amount: float
    unit_symbol: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_process_id": self.source_process_id,
            "target_process_id": self.target_process_id,
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "amount": self.amount,
            "unit_symbol": self.unit_symbol,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemEdge":
        return cls(
            source_process_id=int(data.get("source_process_id") or data.get("source") or 0),
            target_process_id=int(data.get("target_process_id") or data.get("target") or 0),
            flow_id=str(data.get("flow_id") or ""),
            flow_name=str(data.get("flow_name") or ""),
            amount=float(data.get("amount") or 1.0),
            unit_symbol=str(data.get("unit_symbol") or data.get("unit") or "kg"),
            description=str(data.get("description") or "")
        )


@dataclass
class ProductSystem:
    id: Optional[int]
    name: str
    code: str
    target_amount: float
    unit_symbol: str
    description: str = ""
    reference_process_id: Optional[int] = None
    status: str = "draft"  # 'draft', 'in_audit', 'certified'
    db_profile: str = "ecoinvent"
    owner_id: str = "analyst_carla"
    owner_email: str = "carla.mendez@econode.io"
    owner_name: str = "Carla Méndez"
    owner_role: str = "analyst"
    owner_org: str = "BioPack & Circularity Lab"
    category: str = "Polímeros"
    geography: str = "[MX]"
    nodes: List[ProcessNode] = field(default_factory=list)
    edges: List[SystemEdge] = field(default_factory=list)
    compliance_rate: float = 0.0

    def calculate_mass_balance(self) -> Dict[str, Any]:
        """Calcula el balance elemental de masa con normalización de unidades a kilogramos."""
        total_input_kg = 0.0

        for edge in self.edges:
            unit = (edge.unit_symbol or "").strip().lower()
            amt = edge.amount
            if unit in ("kg", "kilogram", "kilogramo", "kilo"):
                total_input_kg += amt
            elif unit in ("g", "gram", "gramo"):
                total_input_kg += (amt * 0.001)
            elif unit in ("t", "ton", "tonne", "tonelada"):
                total_input_kg += (amt * 1000.0)
            elif unit in ("mg", "milligram"):
                total_input_kg += (amt * 1e-6)

        total_output_kg = self.target_amount
        diff = abs(total_input_kg - total_output_kg)
        tolerance = 0.10 * max(total_output_kg, 1.0)
        is_balanced = diff <= tolerance or len(self.edges) == 0

        return {
            "total_input_kg": round(total_input_kg, 4),
            "total_output_kg": round(total_output_kg, 4),
            "difference_kg": round(diff, 4),
            "tolerance_allowed_kg": round(tolerance, 4),
            "is_balanced": is_balanced,
            "status_label": "Validado 100%" if is_balanced else "Diferencia detectada"
        }

    def get_process_ids(self) -> Set[int]:
        """Retorna el conjunto de identificadores de procesos que conforman el grafo."""
        return {node.process_id for node in self.nodes}

    def validate_graph_connectivity(self) -> Dict[str, Any]:
        """Verifica que el grafo no contenga nodos desconectados ni inconsistencias de ID."""
        node_ids = self.get_process_ids()
        connected_ids = set()
        for edge in self.edges:
            connected_ids.add(edge.source_process_id)
            connected_ids.add(edge.target_process_id)

        orphan_nodes = [n.process_id for n in self.nodes if n.process_id not in connected_ids] if len(self.nodes) > 1 else []
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "is_connected": len(orphan_nodes) == 0,
            "orphan_nodes": orphan_nodes
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "target_amount": self.target_amount,
            "unit_symbol": self.unit_symbol,
            "description": self.description,
            "reference_process_id": self.reference_process_id,
            "status": self.status,
            "db_profile": self.db_profile,
            "owner_id": self.owner_id,
            "owner_email": self.owner_email,
            "owner_name": self.owner_name,
            "owner_role": self.owner_role,
            "owner_org": self.owner_org,
            "category": self.category,
            "geography": self.geography,
            "compliance_rate": self.compliance_rate,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductSystem":
        nodes = [ProcessNode.from_dict(n) for n in data.get("nodes", [])]
        edges = [SystemEdge.from_dict(e) for e in data.get("edges", [])]
        return cls(
            id=data.get("id"),
            name=str(data.get("name") or "Sistema Producto"),
            code=str(data.get("code") or "SKU-000"),
            target_amount=float(data.get("target_amount") or 1.0),
            unit_symbol=str(data.get("unit_symbol") or "u"),
            description=str(data.get("description") or ""),
            reference_process_id=data.get("reference_process_id"),
            status=str(data.get("status") or "draft"),
            db_profile=str(data.get("db_profile") or "ecoinvent"),
            owner_id=str(data.get("owner_id") or "analyst_carla"),
            owner_email=str(data.get("owner_email") or "carla.mendez@econode.io"),
            owner_name=str(data.get("owner_name") or "Carla Méndez"),
            owner_role=str(data.get("owner_role") or "analyst"),
            owner_org=str(data.get("owner_org") or "BioPack & Circularity Lab"),
            category=str(data.get("category") or "Polímeros"),
            geography=str(data.get("geography") or "[MX]"),
            nodes=nodes,
            edges=edges,
            compliance_rate=float(data.get("compliance_rate") or 0.0)
        )
