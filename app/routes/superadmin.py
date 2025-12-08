"""
Super Admin Routes

This module contains routes that are exclusively accessible to SUPER_ADMIN users.
These routes provide system-wide administration capabilities across all tenants.

Key Features:
- Cross-tenant data management
- System configuration
- User and company management
- Global reporting and analytics
- Comprehensive audit logging
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash, redirect, url_for, session, abort
from flask_login import login_required, current_user, login_user
from ..decorators.auth import role_required
from ..models.user import User
from ..models.company import Company
from ..models.entity import Entity
from ..models.esg_data import ESGData
from ..models.data_assignment import DataPointAssignment

from ..models.audit_log import AuditLog
from ..models.framework import Framework
from ..models.sync_operation import SyncOperation, FrameworkSyncJob, TenantTemplate, DataMigrationJob
from ..models.system_config import SystemConfig
from ..services.sync_service import FrameworkSyncService, TenantTemplateService
from ..services.analytics_service import CrossTenantAnalyticsService
from ..extensions import db
from datetime import datetime
import secrets
import string
from sqlalchemy import or_
import json
import time
from urllib.parse import urlunparse
import re

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')


@superadmin_bp.before_request
@login_required
def restrict_superadmin():
    """Ensure routes in this blueprint are only accessible to SUPER_ADMIN users.

    Exception: Allow the special `exit_impersonation` route when a user is
    currently impersonating. This enables an ADMIN / USER (impersonated)
    to call the endpoint that ends impersonation and restores the original
    SUPER_ADMIN session.
    
    Also ensures superadmin routes can only be accessed from root domain
    (not from tenant subdomains).
    """
    # Check if we're on a tenant subdomain (except for exit impersonation)
    if request.endpoint != 'superadmin.exit_impersonation':
        host = request.host.split(':')[0]
        subdomain = host.split('.')[0]
        
        # Detect if we're on a tenant subdomain
        is_tenant_subdomain = False
        
        # Handle nip.io development URLs
        if host.endswith('.nip.io'):
            parts = host.split('.')
            if len(parts) >= 4:  # tenant.127-0-0-1.nip.io format
                is_tenant_subdomain = True
        elif subdomain not in ("localhost", "127", "127-0-0-1", "www") and not re.fullmatch(r"\d+-\d+-\d+-\d+", subdomain):
            # Production or other environments with regular subdomains
            is_tenant_subdomain = True
        
        if is_tenant_subdomain:
            current_app.logger.warning(
                f"Access denied: Superadmin route {request.endpoint} accessed from tenant subdomain {host}"
            )
            abort(404)  # Return 404 to not reveal that superadmin exists on this domain

    # Allow the exit impersonation endpoint for impersonating users
    if session.get('impersonating') and request.endpoint == 'superadmin.exit_impersonation':
        # Let the request through so the impersonation can be cleared
        return None

    # For all other requests, enforce SUPER_ADMIN role
    if current_user.role != 'SUPER_ADMIN':
        current_app.logger.warning(
            f"Access denied: User {current_user.id} (role: {current_user.role}) attempted to access {request.endpoint}"
        )
        abort(403)
    
    # SUPER_ADMIN – allow request
    return None


def check_impersonation_status():
    """
    Helper function to validate and maintain impersonation status.
    This should be called in middleware or before_request handlers.
    """
    if session.get('impersonating') and session.get('impersonated_user_id'):
        # Verify the current user matches the impersonated user
        impersonated_user_id = session.get('impersonated_user_id')
        if current_user.is_authenticated and current_user.id != impersonated_user_id:
            # Session mismatch, clear impersonation
            session.pop('impersonating', None)
            session.pop('impersonated_user_id', None)
            session.pop('original_user_id', None)
    elif session.get('impersonating'):
        # Impersonating flag set but no user ID, clear it
        session.pop('impersonating', None)
        session.pop('original_user_id', None)


def log_audit_action(action, entity_type=None, entity_id=None, payload=None):
    """
    Helper function to log audit actions.
    
    Args:
        action (str): Action being performed (e.g., 'CREATE_COMPANY')
        entity_type (str, optional): Type of entity being affected
        entity_id (int, optional): ID of the affected entity
        payload (dict, optional): Additional data about the action
    """
    try:
        AuditLog.log_action(
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        current_app.logger.info(f'Audit log created: {action} by user {current_user.id}')
    except Exception as e:
        current_app.logger.error(f'Failed to create audit log: {str(e)}')


@superadmin_bp.route('/dashboard')
def dashboard():
    """
    Super Admin dashboard with system-wide statistics.
    
    Provides overview of:
    - Total companies and their status
    - User distribution across tenants
    - System-wide data metrics
    - Recent activity across all tenants
    """
    # Get system-wide statistics
    total_companies = Company.query.count()
    active_companies = Company.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    total_entities = Entity.query.count()
    total_data_points = DataPointAssignment.query.count()
    total_esg_records = ESGData.query.count()
    
    # Get user distribution by role
    user_stats = {
        'SUPER_ADMIN': User.query.filter_by(role='SUPER_ADMIN').count(),
        'ADMIN': User.query.filter_by(role='ADMIN').count(),
        'USER': User.query.filter_by(role='USER').count()
    }
    
    # Get recent companies
    recent_companies = Company.query.order_by(Company.created_at.desc()).limit(5).all()
    
    # Get recent audit activity
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template('superadmin/dashboard.html',
                         total_companies=total_companies,
                         active_companies=active_companies,
                         total_users=total_users,
                         total_entities=total_entities,
                         total_data_points=total_data_points,
                         total_esg_records=total_esg_records,
                         user_stats=user_stats,
                         recent_companies=recent_companies,
                         recent_audits=recent_audits)


@superadmin_bp.route('/companies')
def list_companies():
    """
    List all companies in the system.
    
    RESTful GET endpoint that provides comprehensive view of:
    - All companies regardless of tenant
    - Company status and metadata
    - User counts per company
    - Data activity metrics
    """
    companies = Company.query.order_by(Company.name).all()
    
    # Enhance company data with statistics
    company_data = []
    for company in companies:
        user_count = User.query.filter_by(company_id=company.id).count()
        active_user_count = User.query.filter_by(company_id=company.id, is_active=True).count()
        entity_count = Entity.query.filter_by(company_id=company.id).count()
        esg_data_count = ESGData.query.filter_by(company_id=company.id).count()
        
        company_data.append({
            'company': company,
            'user_count': user_count,
            'active_user_count': active_user_count,
            'entity_count': entity_count,
            'esg_data_count': esg_data_count
        })
    
    return render_template('superadmin/companies.html', company_data=company_data)


@superadmin_bp.route('/companies', methods=['POST'])
def create_company():
    """
    Create a new company.
    
    RESTful POST endpoint for company creation.
    Supports both form data and JSON payloads.
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            name = data.get('name', '').strip()
            slug = data.get('slug', '').strip().lower()
        else:
            name = request.form.get('name', '').strip()
            slug = request.form.get('slug', '').strip().lower()
        
        if not name or not slug:
            error_msg = 'Company name and slug are required.'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('superadmin/create_company.html')
        
        # Validate slug format (alphanumeric and hyphens only)
        if not re.match(r'^[a-z0-9-]+$', slug):
            error_msg = 'Slug must contain only lowercase letters, numbers, and hyphens.'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('superadmin/create_company.html')
        
        # Check if company with same name or slug exists
        existing_company = Company.query.filter(
            or_(Company.name == name, Company.slug == slug)
        ).first()
        
        if existing_company:
            error_msg = 'A company with this name or slug already exists.'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('superadmin/create_company.html')
        
        # Create new company
        company = Company(name=name, slug=slug)
        db.session.add(company)
        db.session.flush()  # Get the company ID

        # Log audit action for company creation
        log_audit_action(
            action='CREATE_COMPANY',
            entity_type='Company',
            entity_id=company.id,
            payload={'name': name, 'slug': slug}
        )
        
        # NOTE: No entity is created at this stage. The top-level entity will
        # be created (if necessary) when the first ADMIN user is provisioned
        # for the company.
        
        db.session.commit()
        
        success_msg = f'Company "{name}" created successfully!'
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': success_msg,
                'company_id': company.id
            }), 201
        
        flash(success_msg, 'success')
        return redirect(url_for('superadmin.list_companies'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating company: {str(e)}')
        error_msg = 'Failed to create company. Please try again.'
        
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return render_template('superadmin/create_company.html')


@superadmin_bp.route('/companies/create', methods=['GET'])
def show_create_company_form():
    """Show the create company form."""
    return render_template('superadmin/create_company.html')


@superadmin_bp.route('/companies/<int:company_id>')
def company_details(company_id):
    """
    Detailed view of a specific company.
    
    Provides:
    - Company information and settings
    - All users within the company
    - Entity hierarchy for the company
    - Data activity and metrics
    """
    company = Company.query.get_or_404(company_id)
    
    # Get company users
    users = User.query.filter_by(company_id=company_id).order_by(User.email).all()
    
    # Get company entities
    entities = Entity.query.filter_by(company_id=company_id).order_by(Entity.name).all()
    
    # Get recent ESG data entries
    recent_data = ESGData.query.filter_by(company_id=company_id)\
                              .order_by(ESGData.updated_at.desc())\
                              .limit(10).all()
    
    return render_template('superadmin/company_details.html',
                         company=company,
                         users=users,
                         entities=entities,
                         recent_data=recent_data)


@superadmin_bp.route('/companies/<int:company_id>', methods=['PATCH'])
def update_company(company_id):
    """
    Update a company (RESTful PATCH endpoint).
    
    Supports updating company properties like name, slug, and is_active status.
    """
    try:
        company = Company.query.get_or_404(company_id)
        
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        old_values = {
            'name': company.name,
            'slug': company.slug,
            'is_active': company.is_active
        }
        
        # Update allowed fields
        if 'name' in data:
            company.name = data['name'].strip()
        
        if 'slug' in data:
            new_slug = data['slug'].strip().lower()
            # Validate slug format
            if not re.match(r'^[a-z0-9-]+$', new_slug):
                return jsonify({
                    'success': False,
                    'error': 'Slug must contain only lowercase letters, numbers, and hyphens.'
                }), 400
            company.slug = new_slug
        
        if 'is_active' in data:
            company.is_active = bool(data['is_active'])
        
        company.updated_at = datetime.utcnow()
        
        # Log audit action
        log_audit_action(
            action='UPDATE_COMPANY',
            entity_type='Company',
            entity_id=company.id,
            payload={'old_values': old_values, 'new_values': data}
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Company updated successfully',
            'company': {
                'id': company.id,
                'name': company.name,
                'slug': company.slug,
                'is_active': company.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating company: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to update company'
        }), 500


@superadmin_bp.route('/companies/<int:company_id>', methods=['DELETE'])
def delete_company(company_id):
    """
    Delete a company (RESTful DELETE endpoint).
    
    Performs soft delete by deactivating the company and all its users.
    """
    try:
        company = Company.query.get_or_404(company_id)
        
        # Automatically deactivate any remaining users
        users = User.query.filter_by(company_id=company_id, is_active=True).all()
        for u in users:
            u.is_active = False
            log_audit_action(
                action='AUTO_DEACTIVATE_USER',
                entity_type='User',
                entity_id=u.id,
                payload={
                    'reason': 'Company deletion',
                    'user_email': u.email,
                    'company_name': company.name
                }
            )
        db.session.flush()  # now no active users remain
        
        # Log audit action before deletion
        log_audit_action(
            action='DELETE_COMPANY',
            entity_type='Company',
            entity_id=company.id,
            payload={'name': company.name, 'slug': company.slug}
        )
        
        # Soft delete by deactivating
        company.deactivate()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Company "{company.name}" and all its users have been deactivated.'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting company: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to delete company'
        }), 500


# Legacy endpoint for backward compatibility
@superadmin_bp.route('/companies/<int:company_id>/delete', methods=['POST'])
def delete_company_legacy(company_id):
    """Legacy delete endpoint for backward compatibility."""
    return delete_company(company_id)


@superadmin_bp.route('/users')
def list_users():
    """
    List all users across all tenants with pagination.
    
    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    - search: Search term for email/username
    - role: Filter by role
    - company: Filter by company ID
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('limit', 20, type=int), 100)  # Max 100 per page
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    company_filter = request.args.get('company', '', type=int)
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f'%{search}%'),
                User.name.ilike(f'%{search}%')
            )
        )
    
    # Apply role filter
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    # Apply company filter
    if company_filter:
        query = query.filter(User.company_id == company_filter)
    
    # Order and paginate
    query = query.order_by(User.email)
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    users = pagination.items
    
    # Get companies for filter dropdown
    companies = Company.query.order_by(Company.name).all()
    
    # Return JSON for API requests
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'email': user.email,
                'username': user.name,
                'name': user.name,
                'role': user.role,
                'company_id': user.company_id,
                'company_name': user.company.name if user.company else None,
                'is_active': user.is_active,
                'is_email_verified': user.is_email_verified
            } for user in users],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
    
    return render_template('superadmin/users.html', 
                         users=users,
                         pagination=pagination,
                         companies=companies,
                         search=search,
                         role_filter=role_filter,
                         company_filter=company_filter)


@superadmin_bp.route('/users/<int:user_id>')
def user_details(user_id):
    """
    Detailed view of a specific user.
    
    Provides:
    - User account information
    - Role and permissions
    - Company and entity associations
    - Activity history
    """
    user = User.query.get_or_404(user_id)
    
    # Get user's recent ESG data entries if they're a USER role
    recent_data = []
    if user.role == 'USER' and user.entity_id:
        recent_data = ESGData.query.filter_by(entity_id=user.entity_id)\
                                  .order_by(ESGData.updated_at.desc())\
                                  .limit(10).all()
    
    # Get user's audit history
    audit_history = AuditLog.query.filter_by(user_id=user_id)\
                                  .order_by(AuditLog.created_at.desc())\
                                  .limit(20).all()
    
    return render_template('superadmin/user_details.html',
                         user=user,
                         recent_data=recent_data,
                         audit_history=audit_history)


@superadmin_bp.route('/companies/<int:company_id>/create-admin', methods=['POST'])
def create_admin_user(company_id):
    """
    Create an admin user for a specific company.
    
    This internal endpoint creates an ADMIN user for the given company
    and generates a temporary password. In production, this would typically
    send an email invitation with a password reset link.
    """
    try:
        company = Company.query.get_or_404(company_id)
        
        if not company.is_active:
            return jsonify({
                'success': False,
                'error': 'Cannot create admin for inactive company'
            }), 400
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            name = data.get('username', '').strip()
        else:
            email = request.form.get('email', '').strip().lower()
            name = request.form.get('username', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'A user with this email already exists'
            }), 400
        
        # Generate a temporary password
        temp_password = generate_temporary_password()
        
        # ---------------------------------------------------------
        # Ensure a top-level entity for this company exists.
        # Name it exactly as the company name (as requested).
        # ---------------------------------------------------------
        top_level_entity = Entity.query.filter_by(company_id=company.id, parent_id=None).first()

        if not top_level_entity:
            top_level_entity = Entity(
                name=company.name,
                entity_type='Company',
                parent_id=None,
                company_id=company.id
            )
            db.session.add(top_level_entity)
            db.session.flush()  # Get the ID for foreign-key assignment

            # Audit the auto-creation of the top-level entity
            log_audit_action(
                action='AUTO_CREATE_TOP_LEVEL_ENTITY',
                entity_type='Entity',
                entity_id=top_level_entity.id,
                payload={'company_id': company.id, 'entity_name': top_level_entity.name}
            )

        # ---------------------------------------------------------
        # Create the admin user and link them to the top-level entity
        # ---------------------------------------------------------
        admin_user = User(
            email=email,
            name=name,
            password=temp_password,
            role='ADMIN',
            company_id=company.id,
            entity_id=top_level_entity.id,
            is_active=True,
            is_email_verified=False
        )
        
        db.session.add(admin_user)
        db.session.flush()  # Get the user ID
        
        # Log audit action
        log_audit_action(
            action='CREATE_ADMIN_USER',
            entity_type='User',
            entity_id=admin_user.id,
            payload={
                'email': email,
                'name': name,
                'company_id': company.id,
                'company_name': company.name
            }
        )
        
        db.session.commit()
        
        # In production, you would send an email with password reset link here
        # For now, we'll return the temporary password (NOT recommended for production)
        return jsonify({
            'success': True,
            'message': f'Admin user created for {company.name}',
            'user_email': email,
            'temporary_password': temp_password,
            'note': 'In production, a password reset email would be sent instead of showing the password'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating admin user: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to create admin user'
        }), 500


# Legacy API endpoints for backward compatibility
@superadmin_bp.route('/api/companies/<int:company_id>/toggle-status', methods=['POST'])
def toggle_company_status(company_id):
    """Legacy endpoint for toggling company status."""
    try:
        company = Company.query.get_or_404(company_id)
        old_status = company.is_active
        company.is_active = not company.is_active
        company.updated_at = datetime.utcnow()
        
        # Log audit action
        log_audit_action(
            action='TOGGLE_COMPANY_STATUS',
            entity_type='Company',
            entity_id=company.id,
            payload={'old_status': old_status, 'new_status': company.is_active}
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Company status updated to {"active" if company.is_active else "inactive"}',
            'is_active': company.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling company status: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to update company status'
        }), 500


@superadmin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Legacy endpoint for toggling user status."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent super admin from deactivating themselves
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot deactivate your own account'
            }), 400
        
        old_status = user.is_active
        user.is_active = not user.is_active
        
        # Log audit action
        log_audit_action(
            action='TOGGLE_USER_STATUS',
            entity_type='User',
            entity_id=user.id,
            payload={
                'old_status': old_status,
                'new_status': user.is_active,
                'user_email': user.email
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User status updated to {"active" if user.is_active else "inactive"}',
            'is_active': user.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling user status: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to update user status'
        }), 500


@superadmin_bp.route('/api/system-stats')
def get_system_stats():
    """
    API endpoint for system-wide statistics.
    
    Returns JSON with comprehensive system metrics for dashboard widgets.
    """
    try:
        stats = {
            'companies': {
                'total': Company.query.count(),
                'active': Company.query.filter_by(is_active=True).count(),
                'inactive': Company.query.filter_by(is_active=False).count()
            },
            'users': {
                'total': User.query.count(),
                'super_admin': User.query.filter_by(role='SUPER_ADMIN').count(),
                'admin': User.query.filter_by(role='ADMIN').count(),
                'user': User.query.filter_by(role='USER').count(),
                'verified': User.query.filter_by(is_email_verified=True).count(),
                'unverified': User.query.filter_by(is_email_verified=False).count()
            },
            'data': {
                'entities': Entity.query.count(),
                'data_points': DataPointAssignment.query.count(),
                'esg_records': ESGData.query.count()
            },
            'audit': {
                'total_actions': AuditLog.query.count(),
                'recent_actions': AuditLog.query.filter(
                    AuditLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching system stats: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to fetch system statistics'
        }), 500


@superadmin_bp.route('/audit-log')
def audit_log():
    """
    View audit log entries.
    
    Provides a detailed view of all administrative actions.
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('limit', 50, type=int), 100)
    
    # Get audit logs with pagination
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    audit_logs = pagination.items
    
    return render_template('superadmin/audit_log.html',
                         audit_logs=audit_logs,
                         pagination=pagination)


def generate_temporary_password(length=12):
    """Generate a secure temporary password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


# ================================
# T-8: Multi-tenant Synchronization
# ================================

@superadmin_bp.route('/sync')
def sync_dashboard():
    """
    Multi-tenant synchronization dashboard.
    
    Provides overview of sync operations, framework synchronization,
    tenant templates, and data migration activities.
    """
    # Get recent sync operations
    recent_operations = SyncOperation.query.order_by(SyncOperation.created_at.desc()).limit(10).all()
    
    # Get sync operation statistics
    operation_stats = {
        'total_operations': SyncOperation.query.count(),
        'running_operations': SyncOperation.query.filter_by(status='RUNNING').count(),
        'completed_operations': SyncOperation.query.filter_by(status='COMPLETED').count(),
        'failed_operations': SyncOperation.query.filter_by(status='FAILED').count()
    }
    
    # Get framework sync statistics
    framework_sync_stats = {
        'total_framework_syncs': FrameworkSyncJob.query.count(),
        'frameworks_available': Framework.query.count(),
        'companies_available': Company.query.filter_by(is_active=True).count()
    }
    
    # Get template statistics
    template_stats = {
        'total_templates': TenantTemplate.query.count(),
        'public_templates': TenantTemplate.query.filter_by(is_public=True).count(),
        'template_usage': db.session.query(db.func.sum(TenantTemplate.usage_count)).scalar() or 0
    }
    
    return render_template('superadmin/sync_dashboard.html',
                         recent_operations=recent_operations,
                         operation_stats=operation_stats,
                         framework_sync_stats=framework_sync_stats,
                         template_stats=template_stats)


# Framework Synchronization APIs
@superadmin_bp.route('/api/sync/frameworks/<framework_id>/distribute', methods=['POST'])
def distribute_framework(framework_id):
    """
    Distribute a framework to selected tenants.
    
    POST data should include:
    - target_company_ids: List of company IDs to sync to
    - conflict_resolution: How to handle conflicts ('SKIP', 'OVERWRITE', 'MERGE')
    - sync_options: Additional synchronization options
    """
    try:
        # Validate framework exists
        framework = Framework.query.get(framework_id)
        if not framework:
            return jsonify({
                'success': False,
                'error': 'Framework not found'
            }), 404
        
        # Get request data
        data = request.get_json()
        target_company_ids = data.get('target_company_ids', [])
        conflict_resolution = data.get('conflict_resolution', 'SKIP')
        sync_options = data.get('sync_options', {})
        
        # Validate input
        if not target_company_ids:
            return jsonify({
                'success': False,
                'error': 'No target companies specified'
            }), 400
        
        if conflict_resolution not in ['SKIP', 'OVERWRITE', 'MERGE']:
            return jsonify({
                'success': False,
                'error': 'Invalid conflict resolution strategy'
            }), 400
        
        # Check for conflicts first
        conflicts = FrameworkSyncService.get_framework_conflicts(
            framework_id, target_company_ids
        )
        
        # If there are conflicts and strategy is not handling them, return conflicts
        if conflicts and conflict_resolution == 'SKIP':
            conflict_companies = [c['company_id'] for c in conflicts if c['type'] in ['FRAMEWORK_EXISTS', 'DATA_POINT_EXISTS']]
            if conflict_companies:
                return jsonify({
                    'success': False,
                    'conflicts_detected': True,
                    'conflicts': conflicts,
                    'message': f'Conflicts detected with {len(conflict_companies)} companies. Choose a different conflict resolution strategy or exclude conflicting companies.'
                }), 409
        
        # Create sync job
        sync_operation_id = FrameworkSyncService.create_sync_job(
            framework_id=framework_id,
            target_company_ids=target_company_ids,
            initiated_by=current_user.id,
            sync_options=sync_options,
            conflict_resolution=conflict_resolution
        )
        
        # Execute sync job asynchronously (for now, execute synchronously)
        # In production, this would be queued for background processing
        success = FrameworkSyncService.execute_sync_job(sync_operation_id)
        
        return jsonify({
            'success': True,
            'sync_operation_id': sync_operation_id,
            'message': f'Framework synchronization {"completed" if success else "failed"}',
            'execution_status': 'completed' if success else 'failed'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error distributing framework: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to distribute framework'
        }), 500


@superadmin_bp.route('/api/sync/jobs/<sync_operation_id>/status', methods=['GET'])
def get_sync_job_status(sync_operation_id):
    """Get the status of a sync operation."""
    try:
        status = FrameworkSyncService.get_sync_job_status(sync_operation_id)
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Sync operation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting sync job status: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to get job status'
        }), 500


@superadmin_bp.route('/api/sync/frameworks/<framework_id>/conflicts', methods=['POST'])
def check_framework_conflicts(framework_id):
    """
    Check for potential conflicts before syncing a framework.
    
    POST data should include:
    - target_company_ids: List of company IDs to check
    """
    try:
        # Validate framework exists
        framework = Framework.query.get(framework_id)
        if not framework:
            return jsonify({
                'success': False,
                'error': 'Framework not found'
            }), 404
        
        # Get target companies
        data = request.get_json()
        target_company_ids = data.get('target_company_ids', [])
        
        if not target_company_ids:
            return jsonify({
                'success': False,
                'error': 'No target companies specified'
            }), 400
        
        # Check for conflicts
        conflicts = FrameworkSyncService.get_framework_conflicts(
            framework_id, target_company_ids
        )
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0
        })
        
    except Exception as e:
        current_app.logger.error(f'Error checking framework conflicts: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to check conflicts'
        }), 500


# Framework Synchronization UI Routes
@superadmin_bp.route('/frameworks/sync')
def framework_sync_interface():
    """
    Framework synchronization interface.
    
    Provides UI for selecting frameworks and target companies
    for synchronization operations.
    """
    # Get all frameworks
    frameworks = Framework.query.order_by(Framework.framework_name).all()
    
    # Get all active companies
    companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
    
    # Get recent framework sync jobs
    recent_sync_jobs = (FrameworkSyncJob.query
                       .join(SyncOperation)
                       .order_by(SyncOperation.created_at.desc())
                       .limit(5).all())
    
    # Identify global provider (for template logic)
    global_provider_id = Company.get_global_provider_id()
    
    return render_template('superadmin/framework_sync.html',
                         frameworks=frameworks,
                         companies=companies,
                         recent_sync_jobs=recent_sync_jobs,
                         global_provider_id=global_provider_id)


# Tenant Template APIs
@superadmin_bp.route('/api/templates', methods=['GET'])
def list_tenant_templates():
    """List all available tenant templates."""
    try:
        # Get query parameters
        include_private = request.args.get('include_private', 'false').lower() == 'true'
        industry_filter = request.args.get('industry')
        
        # Build query
        query = TenantTemplate.query
        
        if not include_private:
            query = query.filter_by(is_public=True)
        
        if industry_filter:
            query = query.filter_by(industry=industry_filter)
        
        templates = query.order_by(TenantTemplate.created_at.desc()).all()
        
        # Format response
        template_data = []
        for template in templates:
            template_data.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'industry': template.industry,
                'is_public': template.is_public,
                'is_builtin': template.is_builtin,
                'usage_count': template.usage_count,
                'created_at': template.created_at.isoformat(),
                'summary': template.get_template_summary(),
                'source_company': template.source_company.name if template.source_company else 'System'
            })
        
        return jsonify({
            'success': True,
            'templates': template_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Error listing templates: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to list templates'
        }), 500


@superadmin_bp.route('/api/templates/create-from-tenant/<int:company_id>', methods=['POST'])
def create_template_from_tenant(company_id):
    """
    Create a template from an existing tenant.
    
    POST data should include:
    - name: Template name
    - description: Template description (optional)
    - industry: Industry category (optional)
    - is_public: Whether template should be public (optional)
    """
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': 'Company not found'
            }), 404
        
        # Get request data
        data = request.get_json()
        template_name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        industry = data.get('industry', '').strip()
        is_public = data.get('is_public', False)
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'Template name is required'
            }), 400
        
        # Check if template name already exists
        existing_template = TenantTemplate.query.filter_by(name=template_name).first()
        if existing_template:
            return jsonify({
                'success': False,
                'error': 'Template name already exists'
            }), 400
        
        # Create template
        template_id = TenantTemplateService.create_template_from_tenant(
            company_id=company_id,
            template_name=template_name,
            created_by=current_user.id,
            description=description or None,
            industry=industry or None,
            is_public=is_public
        )
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'message': f'Template "{template_name}" created successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error creating template: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e) if 'not found' in str(e) else 'Failed to create template'
        }), 500


@superadmin_bp.route('/api/templates/<template_id>/provision', methods=['POST'])
def provision_tenant_from_template(template_id):
    """
    Provision a new tenant from a template.
    
    POST data should include:
    - company_name: Name for the new company
    - company_slug: Slug for the new company
    """
    try:
        # Get request data
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        company_slug = data.get('company_slug', '').strip().lower()
        
        if not company_name or not company_slug:
            return jsonify({
                'success': False,
                'error': 'Company name and slug are required'
            }), 400
        
        # Validate slug format
        if not re.match(r'^[a-z0-9-]+$', company_slug):
            return jsonify({
                'success': False,
                'error': 'Slug must contain only lowercase letters, numbers, and hyphens'
            }), 400
        
        # Check if company already exists
        existing_company = Company.query.filter(
            or_(Company.name == company_name, Company.slug == company_slug)
        ).first()
        
        if existing_company:
            return jsonify({
                'success': False,
                'error': 'Company with this name or slug already exists'
            }), 400
        
        # Start provisioning
        sync_operation_id = TenantTemplateService.provision_tenant_from_template(
            template_id=template_id,
            new_company_name=company_name,
            new_company_slug=company_slug,
            initiated_by=current_user.id
        )
        
        return jsonify({
            'success': True,
            'sync_operation_id': sync_operation_id,
            'message': f'Tenant provisioning started for "{company_name}"'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error provisioning tenant: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e) if 'not found' in str(e) else 'Failed to provision tenant'
        }), 500


@superadmin_bp.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_tenant_template(template_id):
    """Delete a tenant template."""
    try:
        template = TenantTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        # Check if template is built-in
        if template.is_builtin:
            return jsonify({
                'success': False,
                'error': 'Cannot delete built-in templates'
            }), 400
        
        # Log audit action
        log_audit_action(
            action='DELETE_TENANT_TEMPLATE',
            entity_type='TenantTemplate',
            entity_id=template.id,
            payload={
                'template_name': template.name,
                'usage_count': template.usage_count
            }
        )
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Template "{template.name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting template: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to delete template'
        }), 500


# Tenant Template UI Routes
@superadmin_bp.route('/templates')
def tenant_templates():
    """
    Tenant template management interface.
    
    Provides UI for managing templates, creating new templates
    from existing tenants, and provisioning new tenants.
    """
    # Get all templates
    templates = TenantTemplate.query.order_by(TenantTemplate.created_at.desc()).all()
    
    # Get all active companies for template creation
    companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
    
    # Get template usage statistics
    template_stats = {
        'total_templates': len(templates),
        'public_templates': len([t for t in templates if t.is_public]),
        'builtin_templates': len([t for t in templates if t.is_builtin]),
        'total_usage': sum(t.usage_count for t in templates)
    }
    
    return render_template('superadmin/tenant_templates.html',
                         templates=templates,
                         companies=companies,
                         template_stats=template_stats)


# Sync Operations Management
@superadmin_bp.route('/sync/operations')
def sync_operations():
    """
    Sync operations management interface.
    
    Provides detailed view of all synchronization operations
    with filtering and search capabilities.
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('limit', 20, type=int), 100)
    operation_type_filter = request.args.get('type', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    # Build query
    query = SyncOperation.query
    
    if operation_type_filter:
        query = query.filter(SyncOperation.operation_type == operation_type_filter)
    
    if status_filter:
        query = query.filter(SyncOperation.status == status_filter)
    
    # Order and paginate
    query = query.order_by(SyncOperation.created_at.desc())
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    operations = pagination.items
    
    return render_template('superadmin/sync_operations.html',
                         operations=operations,
                         pagination=pagination,
                         operation_type_filter=operation_type_filter,
                         status_filter=status_filter)


@superadmin_bp.route('/impersonate/<int:user_id>', methods=['POST'])
def impersonate_user(user_id):
    """
    T-8 Impersonation Feature
    
    Allows SUPER_ADMIN to impersonate any user for customer support purposes.
    Uses a token-based approach to preserve session across subdomain redirects.
    
    Args:
        user_id: ID of the user to impersonate
        
    Returns:
        JSON response with success/error status and redirect URL
    """
    try:
        # Get the target user
        target_user = User.query.get_or_404(user_id)
        
        if not target_user.is_active:
            return jsonify({
                'success': False,
                'error': 'Cannot impersonate inactive user'
            }), 400
        
        # Store original user in session before impersonation
        session['original_user_id'] = current_user.id
        session['impersonating'] = True
        session['impersonated_user_id'] = target_user.id
        
        # Make session permanent so it persists across subdomain redirects
        session.permanent = True
        
        # Log the impersonation action
        log_audit_action(
            action='START_IMPERSONATION',
            entity_type='User',
            entity_id=target_user.id,
            payload={
                'original_user_id': current_user.id,
                'original_user_email': current_user.email,
                'target_user_id': target_user.id,
                'target_user_email': target_user.email,
                'target_user_role': target_user.role
            }
        )
        
        # Login as the target user
        login_user(target_user, remember=True)
        
        # Build tenant-aware redirect for ADMIN or USER so that g.tenant is set
        def _build_tenant_url(path: str) -> str:
            """Helper to construct absolute URL on the target tenant sub-domain."""
            from urllib.parse import urlunparse
            from flask import request

            # Current host (may include port)
            host_parts = request.host.split(':')
            hostname = host_parts[0]
            port = host_parts[1] if len(host_parts) > 1 else None

            # For local development, use nip.io
            if hostname in ("localhost", "127.0.0.1") or hostname.count('.') == 0:
                # Direct localhost access - construct nip.io domain with embedded IP 127.0.0.1
                tenant_host = f"{target_user.company.slug}.127-0-0-1.nip.io"
            # Host is already an IP-based nip.io domain like 127-0-0-1.nip.io
            elif re.match(r"^\d+-\d+-\d+-\d+\.nip\.io$", hostname):
                # Prepend tenant slug to maintain IP mapping
                tenant_host = f"{target_user.company.slug}.{hostname}"
            else:
                # Production environment: use normal subdomain logic
                if hostname.startswith(f"{target_user.company.slug}."):
                    tenant_host = hostname  # already on tenant subdomain
                else:
                    # Replace current subdomain (if any) with tenant slug
                    parts = hostname.split('.', 1)
                    tenant_host = f"{target_user.company.slug}.{parts[1]}" if len(parts) > 1 else hostname

            if port:
                tenant_host += f":{port}"

            scheme = request.scheme
            return urlunparse((scheme, tenant_host, path, '', '', ''))

        if target_user.role == 'SUPER_ADMIN':
            redirect_url = url_for('superadmin.dashboard')
        elif target_user.role == 'ADMIN':
            redirect_url = _build_tenant_url(url_for('admin.home'))
        elif target_user.role == 'USER':
            redirect_url = _build_tenant_url(url_for('user_v2.dashboard'))
        else:
            redirect_url = url_for('auth.login')
        
        return jsonify({
            'success': True,
            'message': f'Now impersonating {target_user.email}',
            'redirect': redirect_url
        })
        
    except Exception as e:
        current_app.logger.error(f'Error during impersonation: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to impersonate user'
        }), 500


@superadmin_bp.route('/exit-impersonation', methods=['POST'])
def exit_impersonation():
    """
    Exit impersonation and restore original SUPER_ADMIN user.
    
    Returns:
        JSON response with success/error status and redirect URL
    """
    try:
        # Check if currently impersonating
        if not session.get('impersonating') or not session.get('original_user_id'):
            return jsonify({
                'success': False,
                'error': 'Not currently impersonating any user'
            }), 400
        
        # Get the original user
        original_user_id = session.get('original_user_id')
        original_user = User.query.get(original_user_id)
        
        if not original_user:
            return jsonify({
                'success': False,
                'error': 'Original user not found'
            }), 400
        
        # Store impersonated user info for logging
        impersonated_user_id = current_user.id
        impersonated_user_email = current_user.email
        
        # Clear impersonation session data
        session.pop('original_user_id', None)
        session.pop('impersonating', None)
        session.pop('impersonated_user_id', None)
        
        # Log the exit impersonation action
        log_audit_action(
            action='EXIT_IMPERSONATION',
            entity_type='User',
            entity_id=impersonated_user_id,
            payload={
                'original_user_id': original_user.id,
                'original_user_email': original_user.email,
                'impersonated_user_id': impersonated_user_id,
                'impersonated_user_email': impersonated_user_email
            }
        )
        
        # Login back as original user
        login_user(original_user)
        
        # Build redirect URL to root domain (without company slug)
        def _build_root_domain_url(path: str) -> str:
            """Helper to construct absolute URL on the root domain (without tenant slug)."""
            from urllib.parse import urlunparse
            from flask import request

            # Current host (may include port)
            host_parts = request.host.split(':')
            hostname = host_parts[0]
            port = host_parts[1] if len(host_parts) > 1 else None

            # Remove tenant slug from hostname to get root domain
            if hostname in ("localhost", "127.0.0.1") or hostname.count('.') == 0:
                # Direct localhost/IP access - keep as is
                root_host = hostname
            elif re.match(r"^\d+-\d+-\d+-\d+\.nip\.io$", hostname):
                # Already root nip.io domain like 127-0-0-1.nip.io
                root_host = hostname
            elif hostname.endswith('.nip.io'):
                # Remove tenant slug from nip.io domain (e.g., tenant.127-0-0-1.nip.io → 127-0-0-1.nip.io)
                parts = hostname.split('.')
                if len(parts) >= 4:  # tenant.127-0-0-1.nip.io
                    root_host = '.'.join(parts[1:])  # Remove first part (tenant slug)
                else:
                    root_host = hostname  # Already root domain
            else:
                # Production environment: remove subdomain
                parts = hostname.split('.', 1)
                if len(parts) > 1 and not hostname.startswith('www.'):
                    root_host = parts[1]  # Remove subdomain
                else:
                    root_host = hostname  # Already root domain

            if port:
                root_host += f":{port}"

            scheme = request.scheme
            return urlunparse((scheme, root_host, path, '', '', ''))
        
        redirect_url = _build_root_domain_url(url_for('superadmin.dashboard'))
        
        return jsonify({
            'success': True,
            'message': f'Exited impersonation, back to {original_user.email}',
            'redirect': redirect_url
        })
        
    except Exception as e:
        current_app.logger.error(f'Error exiting impersonation: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to exit impersonation'
        }), 500


@superadmin_bp.route('/api/templates/<int:template_id>/preview')
def get_template_preview(template_id):
    """
    Get detailed preview information for a template.
    
    Returns template structure, included frameworks, entities, and sample data counts.
    """
    try:
        template = TenantTemplate.query.get_or_404(template_id)
        
        # Parse template data
        template_data = json.loads(template.template_data)
        
        # Build preview information
        preview = {
            'template_name': template.name,
            'template_description': template.description,
            'industry': template.industry,
            'version': template.version,
            'entities_count': len(template_data.get('entities', [])),
            'users_count': len(template_data.get('users', [])),
            'admin_users_count': len([u for u in template_data.get('users', []) if u.get('role') == 'ADMIN']),
            'frameworks': [],
            'data_points_count': len(template_data.get('data_points', [])),
            'sample_data_count': len(template_data.get('sample_data', []))
        }
        
        # Add framework details
        for framework in template_data.get('frameworks', []):
            preview['frameworks'].append({
                'name': framework.get('name', 'Unknown Framework'),
                'description': framework.get('description', ''),
                'fields_count': len(framework.get('fields', []))
            })
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting template preview: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to load template preview'
        }), 500


# Cross-Tenant Analytics API Endpoints - T-8b Phase 3

@superadmin_bp.route('/api/analytics/global-metrics')
def get_global_analytics_metrics():
    """
    Get system-wide ESG analytics metrics.
    
    Returns global statistics including completion rates, industry distribution,
    framework usage, and recent activity across all tenants.
    """
    try:
        metrics = CrossTenantAnalyticsService.get_global_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        current_app.logger.error(f'Error getting global metrics: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve global metrics'
        }), 500


@superadmin_bp.route('/api/analytics/tenant-comparison')
def get_tenant_comparison():
    """
    Get anonymized tenant comparison data.
    
    Query parameters:
    - industry: Filter by specific industry
    - anonymize: Whether to anonymize tenant identifiers (default: true)
    """
    try:
        industry = request.args.get('industry')
        anonymize = request.args.get('anonymize', 'true').lower() == 'true'
        
        comparison = CrossTenantAnalyticsService.get_tenant_comparison(
            industry=industry,
            anonymize=anonymize
        )
        return jsonify(comparison)
        
    except Exception as e:
        current_app.logger.error(f'Error getting tenant comparison: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve tenant comparison'
        }), 500


@superadmin_bp.route('/api/analytics/benchmark-data')
def get_benchmark_data():
    """
    Get ESG benchmarking data with percentiles and statistics.
    
    Query parameters:
    - framework_id: Filter by specific framework
    - industry: Filter by specific industry
    """
    try:
        framework_id = request.args.get('framework_id', type=int)
        industry = request.args.get('industry')
        
        benchmarks = CrossTenantAnalyticsService.get_benchmark_data(
            framework_id=framework_id,
            industry=industry
        )
        return jsonify(benchmarks)
        
    except Exception as e:
        current_app.logger.error(f'Error getting benchmark data: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve benchmark data'
        }), 500


@superadmin_bp.route('/api/analytics/trend-analysis')
def get_trend_analysis():
    """
    Get trend analysis for ESG data over specified time period.
    
    Query parameters:
    - days: Number of days to analyze (default: 90)
    """
    try:
        days = request.args.get('days', 90, type=int)
        
        trends = CrossTenantAnalyticsService.get_trend_analysis(days=days)
        return jsonify(trends)
        
    except Exception as e:
        current_app.logger.error(f'Error getting trend analysis: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trend analysis'
        }), 500


@superadmin_bp.route('/api/analytics/export-report', methods=['POST'])
def export_analytics_report():
    """
    Export comprehensive analytics report.
    
    Request body:
    {
        "report_type": "global|comparison|benchmarks|trends",
        "filters": {
            "industry": "optional",
            "framework_id": "optional",
            "days": "optional",
            "anonymize": "optional"
        }
    }
    """
    try:
        data = request.get_json()
        report_type = data.get('report_type')
        filters = data.get('filters', {})
        
        if not report_type:
            return jsonify({
                'success': False,
                'error': 'Report type is required'
            }), 400
        
        report = CrossTenantAnalyticsService.export_analytics_report(
            report_type=report_type,
            filters=filters
        )
        
        # Log the export action
        log_audit_action(
            action='EXPORT_ANALYTICS_REPORT',
            entity_type='Analytics',
            entity_id=None,
            payload={
                'report_type': report_type,
                'filters': filters
            }
        )
        
        return jsonify(report)
        
    except Exception as e:
        current_app.logger.error(f'Error exporting analytics report: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to export analytics report'
        }), 500


# Analytics Dashboard UI Route
@superadmin_bp.route('/analytics-dashboard')
def analytics_dashboard():
    """
    Cross-tenant analytics dashboard interface.
    
    Provides comprehensive analytics visualization including:
    - Global ESG performance metrics
    - Anonymized tenant benchmarking
    - Industry-specific comparisons
    - Trend analysis and reporting
    """
    # Get available frameworks for filtering
    frameworks = Framework.query.order_by(Framework.name).all()
    
    # Get available industries
    industries = db.session.query(Company.industry).filter(
        Company.industry.isnot(None),
        Company.is_active == True
    ).distinct().order_by(Company.industry).all()
    industries = [industry[0] for industry in industries]
    
    return render_template('superadmin/analytics_dashboard.html',
                         frameworks=frameworks,
                         industries=industries)


# T-9 System Configuration Management
@superadmin_bp.route('/system-config')
def system_config():
    """
    System Configuration Management Dashboard - T-9
    
    Provides interface for managing system-wide settings including:
    - Application settings
    - Email configuration
    - Security settings
    - Performance tuning
    - Feature toggles
    """
    # Get all configuration categories
    categories = db.session.query(SystemConfig.category).distinct().all()
    categories = [cat[0] for cat in categories] if categories else []
    
    # Get configurations by category
    configs_by_category = {}
    for category in categories:
        configs_by_category[category] = SystemConfig.query.filter_by(category=category).order_by(SystemConfig.key).all()
    
    # If no configs exist, initialize defaults
    if not categories:
        SystemConfig.initialize_defaults()
        return redirect(url_for('superadmin.system_config'))
    
    # Get system health summary
    total_configs = SystemConfig.query.count()
    sensitive_configs = SystemConfig.query.filter_by(is_sensitive=True).count()
    readonly_configs = SystemConfig.query.filter_by(is_readonly=True).count()
    
    config_stats = {
        'total_configs': total_configs,
        'sensitive_configs': sensitive_configs,
        'readonly_configs': readonly_configs,
        'categories_count': len(categories)
    }
    
    return render_template('superadmin/system_config.html', 
                         configs_by_category=configs_by_category,
                         categories=categories,
                         config_stats=config_stats)


@superadmin_bp.route('/api/system-config', methods=['GET'])
def get_system_config():
    """
    Get system configuration (API endpoint).
    
    Returns all system configuration settings with proper security filtering.
    """
    try:
        category = request.args.get('category')
        include_sensitive = request.args.get('include_sensitive', 'false').lower() == 'true'
        
        # Build query
        query = SystemConfig.query
        if category:
            query = query.filter_by(category=category)
        
        configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
        
        # Format response
        config_data = {}
        for config in configs:
            if config.category not in config_data:
                config_data[config.category] = []
            
            config_data[config.category].append(config.to_dict(include_sensitive=include_sensitive))
        
        return jsonify({
            'success': True,
            'config': config_data,
            'total_count': len(configs)
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting system config: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system configuration'
        }), 500


@superadmin_bp.route('/api/system-config/<int:config_id>', methods=['PATCH'])
def update_system_config_item(config_id):
    """
    Update a specific system configuration item.
    
    RESTful PATCH endpoint for updating individual configuration values.
    """
    try:
        config = SystemConfig.query.get_or_404(config_id)
        
        if config.is_readonly:
            return jsonify({
                'success': False,
                'error': 'This configuration item is read-only'
            }), 400
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        old_value = config.get_value()
        
        # Update the value
        if 'value' in data:
            config.set_value(data['value'])
            config.updated_at = datetime.utcnow()
            config.updated_by = current_user.id
        
        # Update description if provided
        if 'description' in data:
            config.description = data['description']
        
        # Log audit action
        log_audit_action(
            action='UPDATE_CONFIG_ITEM',
            entity_type='SystemConfig',
            entity_id=config.id,
            payload={
                'key': config.key,
                'old_value': old_value,
                'new_value': config.get_value(),
                'category': config.category
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration "{config.key}" updated successfully',
            'config': config.to_dict(include_sensitive=True)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating config item: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to update configuration item'
        }), 500


@superadmin_bp.route('/api/system-config', methods=['POST'])
def create_system_config_item():
    """
    Create a new system configuration item.
    
    RESTful POST endpoint for creating new configuration values.
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        required_fields = ['key', 'value', 'value_type', 'category']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Check if key already exists
        existing_config = SystemConfig.query.filter_by(key=data['key']).first()
        if existing_config:
            return jsonify({
                'success': False,
                'error': 'Configuration key already exists'
            }), 400
        
        # Create new configuration
        config = SystemConfig(
            key=data['key'],
            value_type=data['value_type'],
            description=data.get('description', ''),
            category=data['category'],
            is_sensitive=data.get('is_sensitive', False),
            is_readonly=data.get('is_readonly', False)
        )
        config.set_value(data['value'])
        config.updated_by = current_user.id
        
        db.session.add(config)
        db.session.flush()  # Get the config ID
        
        # Log audit action
        log_audit_action(
            action='CREATE_CONFIG_ITEM',
            entity_type='SystemConfig',
            entity_id=config.id,
            payload={
                'key': config.key,
                'value': config.get_value(),
                'category': config.category
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration "{config.key}" created successfully',
            'config': config.to_dict(include_sensitive=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating config item: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to create configuration item'
        }), 500


@superadmin_bp.route('/api/system-config/<int:config_id>', methods=['DELETE'])
def delete_system_config_item(config_id):
    """
    Delete a system configuration item.
    
    RESTful DELETE endpoint for removing configuration values.
    """
    try:
        config = SystemConfig.query.get_or_404(config_id)
        
        if config.is_readonly:
            return jsonify({
                'success': False,
                'error': 'This configuration item is read-only and cannot be deleted'
            }), 400
        
        # Log audit action before deletion
        log_audit_action(
            action='DELETE_CONFIG_ITEM',
            entity_type='SystemConfig',
            entity_id=config.id,
            payload={
                'key': config.key,
                'value': config.get_value(),
                'category': config.category
            }
        )
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration "{config.key}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting config item: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to delete configuration item'
        }), 500


@superadmin_bp.route('/api/system-config/initialize-defaults', methods=['POST'])
def initialize_default_configs():
    """
    Initialize default system configuration values.
    
    This endpoint sets up the default configuration values for a new installation.
    """
    try:
        # Initialize default configurations
        SystemConfig.initialize_defaults()
        
        # Log audit action
        log_audit_action(
            action='INITIALIZE_DEFAULT_CONFIGS',
            entity_type='SystemConfig',
            entity_id=None,
            payload={'message': 'Default system configurations initialized'}
        )
        
        return jsonify({
            'success': True,
            'message': 'Default system configurations initialized successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error initializing default configs: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to initialize default configurations'
        }), 500


@superadmin_bp.route('/api/system-config/export', methods=['POST'])
def export_system_config():
    """
    Export system configuration for backup or migration.
    
    Creates a complete backup of all system configuration settings.
    """
    try:
        include_sensitive = request.args.get('include_sensitive', 'false').lower() == 'true'
        
        configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
        
        export_data = {
            'export_info': {
                'timestamp': datetime.utcnow().isoformat(),
                'exported_by': current_user.email,
                'total_configs': len(configs),
                'includes_sensitive': include_sensitive
            },
            'configurations': [config.to_dict(include_sensitive=include_sensitive) for config in configs]
        }
        
        # Log audit action
        log_audit_action(
            action='EXPORT_SYSTEM_CONFIG',
            entity_type='SystemConfig',
            entity_id=None,
            payload={
                'export_count': len(configs),
                'includes_sensitive': include_sensitive
            }
        )
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Error exporting system config: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to export system configuration'
        }), 500


# System Health and Monitoring - T-9
@superadmin_bp.route('/system-health')
def system_health():
    """
    System Health Dashboard - T-9
    
    Provides monitoring and health check information for the system.
    """
    # Get database statistics
    db_stats = {
        'total_companies': Company.query.count(),
        'active_companies': Company.query.filter_by(is_active=True).count(),
        'total_users': User.query.count(),
        'total_entities': Entity.query.count(),
        'total_data_points': DataPointAssignment.query.count(),
        'total_esg_records': ESGData.query.count(),
        'total_audit_logs': AuditLog.query.count()
    }
    
    # Get system configuration status
    config_stats = {
        'total_configs': SystemConfig.query.count(),
        'maintenance_mode': SystemConfig.get_config('app.maintenance_mode', False),
        'registration_enabled': SystemConfig.get_config('app.registration_enabled', True),
        'email_enabled': SystemConfig.get_config('email.enabled', False)
    }
    
    # Recent system activity
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    
    return render_template('superadmin/system_health.html',
                         db_stats=db_stats,
                         config_stats=config_stats,
                         recent_audits=recent_audits)


@superadmin_bp.route('/api/system-health/metrics')
def get_system_health_metrics():
    """
    Get system health metrics (API endpoint).
    
    Returns real-time system health and performance metrics.
    """
    try:
        import psutil
        import os
        from datetime import datetime, timedelta
        
        # System resource metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_activity = AuditLog.query.filter(AuditLog.created_at >= recent_cutoff).count()
        
        # Application metrics
        uptime_seconds = time.time() - psutil.Process(os.getpid()).create_time()
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': round((disk.used / disk.total) * 100, 2),
                'disk_free_gb': round(disk.free / (1024**3), 2)
            },
            'database': {
                'recent_activity_24h': recent_activity,
                'total_companies': Company.query.count(),
                'total_users': User.query.count(),
                'total_esg_records': ESGData.query.count()
            },
            'application': {
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'maintenance_mode': SystemConfig.get_config('app.maintenance_mode', False),
                'version': SystemConfig.get_config('app.version', '1.0.0')
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting system health metrics: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system health metrics'
        }), 500


# =============================
# HARD DELETE (irreversible)
# =============================
@superadmin_bp.route('/companies/<int:company_id>/hard-delete', methods=['POST'])
def hard_delete_company(company_id):
    """Permanently delete a company *and* all tenant-scoped data.

    This action is IRREVERSIBLE and should be exposed only to super-admins.
    It cascades through tenant-scoped tables then deletes the company row.
    """
    try:
        company = Company.query.get_or_404(company_id)

        # Safety: refuse if company is still active
        if company.is_active:
            return jsonify({
                'success': False,
                'error': 'Company must be deactivated (soft-deleted) before it can be hard-deleted.'
            }), 400

        # ---------------------------
        # Delete tenant-scoped tables in dependency order
        # ---------------------------
        
        # Import all necessary models
        from ..models.framework import FrameworkDataField, Topic, FieldVariableMapping
        from ..models.dimension import Dimension, DimensionValue, FieldDimension
        from ..models.sync_operation import SyncOperation, TenantTemplate, DataMigrationJob, FrameworkSyncJob
        
        # Delete in reverse dependency order to avoid foreign key constraints
        
        # 1. Delete ESG data and related records first (highest level dependencies)
        ESGData.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 2. Delete field dimension assignments
        FieldDimension.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 3. Delete dimension values
        DimensionValue.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 4. Delete dimensions
        Dimension.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 5. Delete data point assignments
        DataPointAssignment.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 6. Delete field variable mappings for framework fields belonging to this company
        framework_field_ids = db.session.query(FrameworkDataField.field_id).filter_by(company_id=company_id).subquery()
        FieldVariableMapping.query.filter(
            or_(
                FieldVariableMapping.computed_field_id.in_(framework_field_ids),
                FieldVariableMapping.raw_field_id.in_(framework_field_ids)
            )
        ).delete(synchronize_session=False)
        
        # 7. Delete framework data fields
        FrameworkDataField.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 8. Delete topics (both framework-specific and company-specific)
        Topic.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 9. Delete frameworks
        from ..models.framework import Framework
        Framework.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 10. Delete sync operations related to this company
        # Delete framework sync jobs where this company is the source
        FrameworkSyncJob.query.filter_by(source_company_id=company_id).delete(synchronize_session=False)
        
        # Delete tenant templates created from this company
        TenantTemplate.query.filter_by(source_company_id=company_id).delete(synchronize_session=False)
        
        # Delete data migration jobs targeting this company
        DataMigrationJob.query.filter_by(target_company_id=company_id).delete(synchronize_session=False)
        
        # 11. Delete entities (will cascade to any remaining ESGData)
        Entity.query.filter_by(company_id=company_id).delete(synchronize_session=False)
        
        # 12. Delete users
        User.query.filter_by(company_id=company_id).delete(synchronize_session=False)

        # Log audit action for hard delete
        log_audit_action(
            action='HARD_DELETE_COMPANY',
            entity_type='Company',
            entity_id=company.id,
            payload={'name': company.name, 'slug': company.slug}
        )

        # Finally remove the company record itself
        db.session.delete(company)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Company "{company.name}" and all tenant data have been permanently deleted.'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error hard-deleting company: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to hard delete company'
        }), 500 

# --- Framework Promotion API ---
@superadmin_bp.route('/api/frameworks/<framework_id>/promote', methods=['POST'])
def promote_framework(framework_id):
    """Promote a company-specific framework to the global provider.

    Expects no payload; simply moves the framework (and its field definitions)
    to the global provider tenant. Returns JSON indicating success/failure.
    """
    from ..services import frameworks_service

    try:
        result = frameworks_service.promote_framework_to_global(
            framework_id=framework_id,
            initiated_by_user_id=current_user.id
        )
        return jsonify({
            'success': True,
            'data': result
        })

    except ValueError as ve:
        # Expected validation errors
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400

    except Exception as e:
        current_app.logger.error(f'Error promoting framework {framework_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to promote framework. Please check server logs.'
        }), 500 