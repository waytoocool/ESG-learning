from flask import Blueprint

# Create the user_v2 blueprint for new modal-based data entry interface
user_v2_bp = Blueprint('user_v2', __name__, url_prefix='/user/v2')

# Import route modules to register them with the blueprint
from . import dashboard
from . import preferences_api
from . import feedback_api
from . import dimensional_data_api

# Import and register API blueprints
from .entity_api import entity_api_bp
from .field_api import field_api_bp
from .data_api import data_api_bp
from .computation_context_api import computation_context_api_bp
from .draft_api import draft_api_bp  # Phase 4: Auto-save draft API

# Export all blueprints for registration in app factory
__all__ = [
    'user_v2_bp',
    'entity_api_bp',
    'field_api_bp',
    'data_api_bp',
    'computation_context_api_bp',
    'draft_api_bp'  # Phase 4
]
