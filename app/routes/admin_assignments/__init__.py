"""
Admin Assignments Blueprint Package
Progressive refactoring of assignment functionality

This package will contain modular assignment routes:
- core.py: Main assignment routes and views
- api.py: RESTful API endpoints
- versioning.py: Version lifecycle management endpoints
- history.py: History viewing and comparison endpoints
- bulk_operations.py: Bulk import/export endpoints
- validation.py: Input validation and sanitization
- utils.py: Shared utility functions
"""

from flask import Blueprint

# Blueprint will be populated in future phases
# admin_assignments_bp = Blueprint('admin_assignments', __name__, url_prefix='/api/v1/assignments')