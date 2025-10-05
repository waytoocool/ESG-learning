from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from ..models.user import User
from ..models.entity import Entity
from ..models.framework import Framework, FrameworkDataField, FieldVariableMapping
from ..extensions import db
from ..models.esg_data import ESGDataAuditLog, ESGData
from ..models.data_assignment import DataPointAssignment
from ..middleware.tenant import get_current_tenant
from ..decorators.auth import admin_or_super_admin_required, tenant_required_for, require_admin
import json
import re
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from ..models import (Framework, FrameworkDataField, DataPointAssignment, Entity,
                      ESGData, User, AuditLog, ESGDataAuditLog, Company, Topic,
                      FieldVariableMapping)
from sqlalchemy.sql import func

# Create blueprint for modular assign data points
admin_assign_data_points_bp = Blueprint('admin_assign_data_points', __name__, url_prefix='/admin')

def require_tenant_for_admin():
    """Require tenant context for admin operations (copied from admin.py)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role == 'SUPER_ADMIN':
                # Super admin can access without tenant, but should use impersonation
                # for company-specific operations
                return f(*args, **kwargs)
            elif current_user.company_id is None:
                flash('Access denied: No company association found.', 'error')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def is_super_admin():
    """Check if current user is a super admin (no company_id)"""
    return current_user.role == 'SUPER_ADMIN'

def get_admin_entities():
    """Get entities for admin interface (copied from admin.py logic)"""
    if is_super_admin():
        # Super admin sees all entities (typically used with impersonation)
        entities = Entity.query.all()
    else:
        # Regular admin sees only their company's entities
        entities = Entity.query.filter_by(company_id=current_user.company_id).all()
    return entities

def get_admin_data_points():
    """Get data points for admin interface (copied from admin.py logic)"""
    if is_super_admin():
        # Super admin sees all data points
        data_points = FrameworkDataField.query.all()
    else:
        # Regular admin sees data points based on their company's frameworks
        # This would need to be refined based on actual business logic
        data_points = FrameworkDataField.query.all()
    return data_points

@admin_assign_data_points_bp.route('/assign-data-points', methods=['GET'])
@login_required
@require_tenant_for_admin()
def assign_data_points():
    """Modular assign data points interface - PRODUCTION"""
    from ..services import frameworks_service  # Local import to avoid circular deps

    if is_super_admin():
        frameworks = Framework.query.all()
    else:
        frameworks_by_type = frameworks_service.separate_frameworks_by_type(current_user.company_id)
        frameworks = frameworks_by_type['company'] + frameworks_by_type['global']

    entities = get_admin_entities()
    data_points = get_admin_data_points()

    return render_template('admin/assign_data_points_v2.html',
                         frameworks=frameworks,
                         entities=entities,
                         data_points=data_points)