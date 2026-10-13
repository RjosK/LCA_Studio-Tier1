"""
econode_studio/domain/lci_exchange.py - Entidad de Dominio para Procesos e Intercambios LCI
Basado en especificación ecoinvent 3.12 y el estándar internacional openLCA v2.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class LciExchange:
    id: int
    process_id: int
    flow_id: str
    flow_name: str
    is_input: bool
    exchange_type: str  # 'technosphere', 'biosphere', 'production'
    amount: float
    unit_symbol: str
    default_provider_id: Optional[int] = None
    default_provider_name: Optional[str] = None
    description: str = ""

    def is_biosphere(self) -> bool:
        """Indica si es un intercambio elemental con la naturaleza (emisión o recurso)."""
        return self.exchange_type == "biosphere"

    def is_technosphere(self) -> bool:
        """Indica si es un intercambio de productos o servicios con otro proceso industrial."""
        return self.exchange_type == "technosphere"

    def is_production(self) -> bool:
        """Indica si representa la salida del producto de referencia de la actividad."""
        return self.exchange_type == "production"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "process_id": self.process_id,
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "is_input": self.is_input,
            "exchange_type": self.exchange_type,
            "amount": self.amount,
            "unit_symbol": self.unit_symbol,
            "default_provider_id": self.default_provider_id,
            "default_provider_name": self.default_provider_name,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LciExchange":
        return cls(
            id=int(data.get("id") or 0),
            process_id=int(data.get("process_id") or 0),
            flow_id=str(data.get("flow_id") or ""),
            flow_name=str(data.get("flow_name") or ""),
            is_input=bool(data.get("is_input", True)),
            exchange_type=str(data.get("exchange_type") or "technosphere"),
            amount=float(data.get("amount") or 0.0),
            unit_symbol=str(data.get("unit_symbol") or "kg"),
            default_provider_id=data.get("default_provider_id"),
            default_provider_name=data.get("default_provider_name"),
            description=str(data.get("description") or "")
        )


@dataclass(frozen=True)
class LciProcessSummary:
    id: int
    code: str
    name: str
    location: str
    category_name: str
    reference_flow_name: str
    reference_amount: float
    unit_symbol: str
    technosphere_count: int = 0
    biosphere_count: int = 0
    dqi_score: str = "5/5"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "location": self.location,
            "category_name": self.category_name,
            "reference_flow_name": self.reference_flow_name,
            "reference_amount": self.reference_amount,
            "unit_symbol": self.unit_symbol,
            "technosphere_count": self.technosphere_count,
            "biosphere_count": self.biosphere_count,
            "dqi_score": self.dqi_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LciProcessSummary":
        return cls(
            id=int(data.get("id") or 0),
            code=str(data.get("code") or ""),
            name=str(data.get("name") or ""),
            location=str(data.get("location") or "[GLO]"),
            category_name=str(data.get("category_name") or "General"),
            reference_flow_name=str(data.get("reference_flow_name") or ""),
            reference_amount=float(data.get("reference_amount") or 1.0),
            unit_symbol=str(data.get("unit_symbol") or "kg"),
            technosphere_count=int(data.get("technosphere_count") or 0),
            biosphere_count=int(data.get("biosphere_count") or 0),
            dqi_score=str(data.get("dqi_score") or "5/5")
        )
