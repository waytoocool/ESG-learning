"""
Role-Based Access Control Decorators

This module provides decorators for enforcing role-based access control
with tenant validation in the ESG DataVault application.

Key Features:
- tenant_required_for(*roles): Validates user role and tenant membership
- role_required(required_role): Validates exact role match (for SUPER_ADMIN)
- Comprehensive logging for security auditing
- Integration with Flask-Login and tenant middleware
"""

from functools import wraps
from flask import abort, g, current_app
from flask_login import current_user


def tenant_required_for(*roles):
    """
    Decorator that requires user to have one of the specified roles AND
    belong to the current tenant (company_id must match g.tenant.id).
    
    This decorator enforces both role-based access control and tenant isolation.
    It should be used for routes that require specific roles within a tenant context.
    
    Args:
        *roles: Variable number of role strings that are allowed access
                (e.g., 'ADMIN', 'USER')
    
    Usage:
        @tenant_required_for('ADMIN', 'USER')
        def some_endpoint():
            # Only ADMIN or USER roles from the current tenant can access
            pass
            
        @tenant_required_for('ADMIN')
        def admin_only_endpoint():
            # Only ADMIN role from the current tenant can access
            pass
    
    Security Checks:
        1. User must be authenticated (handled by @login_required)
        2. User role must be in the allowed roles list
        3. Tenant context must be available (g.tenant is not None)
        4. User's company_id must match the current tenant's id
    
    Returns:
        403 Forbidden if any security check fails
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Check if user role is in allowed roles
            if current_user.role not in roles:
                current_app.logger.warning(
                    f"Access denied: User {current_user.id} (role: {current_user.role}) "
                    f"attempted to access {f.__name__} requiring roles: {roles}"
                )
                abort(403)
            
            # Check if tenant context is available
            if g.tenant is None:
                current_app.logger.warning(
                    f"Access denied: User {current_user.id} attempted to access {f.__name__} "
                    f"without tenant context"
                )
                abort(403)
            
            # Check if user belongs to the current tenant
            if current_user.company_id != g.tenant.id:
                current_app.logger.warning(
                    f"Cross-tenant access attempt: User {current_user.id} "
                    f"(company_id: {current_user.company_id}) attempted to access "
                    f"tenant {g.tenant.id} endpoint {f.__name__}"
                )
                abort(403)
            
            # All checks passed, proceed with the request
            current_app.logger.debug(
                f"Access granted: User {current_user.id} (role: {current_user.role}) "
                f"accessing {f.__name__} for tenant {g.tenant.id}"
            )
            return f(*args, **kwargs)
        return wrapped
    return decorator


def role_required(required_role):
    """
    Decorator that requires user to have an exact role match.
    
    This decorator is primarily intended for SUPER_ADMIN routes that should
    be accessible regardless of tenant context. SUPER_ADMIN users typically
    have company_id = None and can operate across all tenants.
    
    Args:
        required_role: Exact role string required (e.g., 'SUPER_ADMIN')
    
    Usage:
        @role_required('SUPER_ADMIN')
        def super_admin_endpoint():
            # Only SUPER_ADMIN role can access, regardless of tenant
            pass
    
    Security Checks:
        1. User must be authenticated (handled by @login_required)
        2. User role must exactly match the required role
    
    Returns:
        403 Forbidden if role check fails
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Check if user has the exact required role
            if current_user.role != required_role:
                current_app.logger.warning(
                    f"Access denied: User {current_user.id} (role: {current_user.role}) "
                    f"attempted to access {f.__name__} requiring role: {required_role}"
                )
                abort(403)
            
            # Role check passed, proceed with the request
            current_app.logger.debug(
                f"Access granted: User {current_user.id} (role: {current_user.role}) "
                f"accessing {f.__name__}"
            )
            return f(*args, **kwargs)
        return wrapped
    return decorator


def admin_or_super_admin_required(f):
    """
    Convenience decorator for routes that should be accessible to both
    ADMIN (with tenant validation) and SUPER_ADMIN (without tenant validation).
    
    This decorator handles the common pattern where an endpoint should be
    accessible to:
    - ADMIN users within their tenant context
    - SUPER_ADMIN users across all tenants
    
    Usage:
        @admin_or_super_admin_required
        def admin_endpoint():
            # ADMIN users see their tenant's data
            # SUPER_ADMIN users see all data
            pass
    
    Security Logic:
        - If user is SUPER_ADMIN: Allow access regardless of tenant
        - If user is ADMIN: Require tenant context and company_id match
        - Otherwise: Deny access
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role == 'SUPER_ADMIN':
            # SUPER_ADMIN can access without tenant validation
            current_app.logger.debug(
                f"SUPER_ADMIN access: User {current_user.id} accessing {f.__name__}"
            )
            return f(*args, **kwargs)
        elif current_user.role == 'ADMIN':
            # ADMIN requires tenant validation
            if g.tenant is None:
                current_app.logger.warning(
                    f"Access denied: ADMIN user {current_user.id} attempted to access "
                    f"{f.__name__} without tenant context"
                )
                abort(403)
            
            if current_user.company_id != g.tenant.id:
                current_app.logger.warning(
                    f"Cross-tenant access attempt: ADMIN user {current_user.id} "
                    f"(company_id: {current_user.company_id}) attempted to access "
                    f"tenant {g.tenant.id} endpoint {f.__name__}"
                )
                abort(403)
            
            current_app.logger.debug(
                f"ADMIN access: User {current_user.id} accessing {f.__name__} "
                f"for tenant {g.tenant.id}"
            )
            return f(*args, **kwargs)
        else:
            # Neither ADMIN nor SUPER_ADMIN
            current_app.logger.warning(
                f"Access denied: User {current_user.id} (role: {current_user.role}) "
                f"attempted to access admin endpoint {f.__name__}"
            )
            abort(403)
    
    return wrapped 

# Convenience alias for backward compatibility and cleaner code
require_admin = admin_or_super_admin_required 

# A simplified decorator that only ensures a tenant context exists. This avoids
# the unintended side-effect of denying access to every role when no roles are
# passed to `tenant_required_for()`.

def tenant_required(f):
    """Ensure the request is being made within a tenant context."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if g.tenant is None:
            current_app.logger.warning(
                f"Access denied: Tenant context required for {f.__name__}"
            )
            abort(404)
        return f(*args, **kwargs)
    return wrapped

# Backward-compatibility: expose the name expected by existing imports.
# (Some modules do `from ..decorators.auth import tenant_required`.)

__all__ = [
    "tenant_required_for",
    "role_required",
    "admin_or_super_admin_required",
    "require_admin",
    "tenant_required",
] 