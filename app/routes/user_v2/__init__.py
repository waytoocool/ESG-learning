from flask import Blueprint

# Create the user_v2 blueprint for new modal-based data entry interface
user_v2_bp = Blueprint('user_v2', __name__, url_prefix='/user/v2')

# Import route modules to register them with the blueprint
from . import dashboard
from . import preferences_api
from . import feedback_api
from . import dimensional_data_api
from . import attachment_api  # Enhancement #3: File attachments

# Import and register API blueprints
from .entity_api import entity_api_bp
from .field_api import field_api_bp
from .data_api import data_api_bp
from .computation_context_api import computation_context_api_bp
from .draft_api import draft_api_bp  # Phase 4: Auto-save draft API
from .export_api import export_api_bp  # Phase 4 Polish: Historical data export
from .bulk_upload_api import bulk_upload_bp  # Enhancement #4: Bulk Excel Upload
from .validation_api import validation_api  # Validation Engine: Automated validation

# Export all blueprints for registration in app factory
__all__ = [
    'user_v2_bp',
    'entity_api_bp',
    'field_api_bp',
    'data_api_bp',
    'computation_context_api_bp',
    'draft_api_bp',  # Phase 4
    'export_api_bp',  # Phase 4 Polish
    'bulk_upload_bp',  # Enhancement #4
    'validation_api'  # Validation Engine
]
