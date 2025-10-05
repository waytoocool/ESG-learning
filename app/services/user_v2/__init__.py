"""
User V2 Services
=================

Service layer for the new user dashboard interface.

Modules:
- entity_service: Entity management and switching logic
- field_service: Field details and metadata retrieval
- historical_data_service: Historical data queries and aggregation
- dimensional_data_service: Dimensional data matrix operations (Phase 2)
- aggregation_service: Data aggregation across dimensions and entities (Phase 2)
- computation_context_service: Computation context and dependency analysis (Phase 3)
"""

from .entity_service import EntityService
from .field_service import FieldService
from .historical_data_service import HistoricalDataService
from .dimensional_data_service import DimensionalDataService
from .aggregation_service import AggregationService
from .computation_context_service import ComputationContextService
from .draft_service import DraftService  # Phase 4: Auto-save draft service

__all__ = [
    'EntityService',
    'FieldService',
    'HistoricalDataService',
    'DimensionalDataService',
    'AggregationService',
    'ComputationContextService',
    'DraftService'  # Phase 4
]
