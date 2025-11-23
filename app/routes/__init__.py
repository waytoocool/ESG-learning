from flask import Blueprint
from .auth import auth_bp
from .admin import admin_bp
# Legacy user dashboard removed - use user_v2 instead
from .superadmin import superadmin_bp
from .admin_frameworks_api import admin_frameworks_api_bp
from .admin_assignments_api import assignment_api_bp
from .admin_assignment_history import assignment_history_bp
from .admin_assign_data_points import admin_assign_data_points_bp
from .admin_assignDataPoints_Additional import admin_assign_additional_bp
# Note: admin_dimensions routes are registered via register_dimension_routes(admin_bp) in admin.py
from .user_v2 import user_v2_bp, entity_api_bp, field_api_bp, data_api_bp, computation_context_api_bp, draft_api_bp, export_api_bp, bulk_upload_bp, validation_api
from .support import support_bp
# from .admin_bulk_operations import admin_bulk_operations_bp  # Integrated into main assignment interface


# Register routes with blueprints
blueprints = [
    auth_bp,
    admin_bp,
    admin_frameworks_api_bp,
    assignment_api_bp,
    assignment_history_bp,
    admin_assign_data_points_bp,
    admin_assign_additional_bp,
    # admin_dimensions routes registered in admin_bp via register_dimension_routes()
    # Legacy user_bp removed - use user_v2_bp instead
    user_v2_bp,
    entity_api_bp,  # User V2 Entity API
    field_api_bp,   # User V2 Field API
    data_api_bp,    # User V2 Data API
    computation_context_api_bp,  # User V2 Computation Context API (Phase 3)
    draft_api_bp,   # User V2 Draft API (Phase 4)
    export_api_bp,  # User V2 Export API (Phase 4 Polish)
    bulk_upload_bp,  # User V2 Bulk Upload API (Enhancement #4)
    validation_api,  # User V2 Validation API (Validation Engine)
    support_bp,     # Support and issue reporting API
    superadmin_bp
]