"""
Multi-tenant subdomain resolution middleware

This middleware implements subdomain-based tenant resolution for the ESG DataVault
application. It extracts the subdomain from the request host and resolves it to
a Company model instance, making it available through Flask's g object.

Key Features:
- Extracts subdomain from host (handles port stripping)
- Resolves subdomain to Company model via slug lookup
- Provides fallback for root domain/localhost access
- Thread-safe using Flask's request-scoped g object
- Early 404 abort for unknown tenants

Usage:
    The middleware sets g.tenant to either:
    - Company object for valid tenant subdomains (e.g., acme.localhost → Company(slug='acme'))
    - None for root domain access (localhost, 127.0.0.1)
    - Aborts with 404 for unknown subdomains
"""

import re
from flask import g, request, abort
from app.models.company import Company


def load_tenant():
    """
    Resolves the current request's tenant based on subdomain.
    
    This function is called before each request to determine the tenant context.
    It extracts the subdomain from the Host header and attempts to resolve it
    to a Company record in the database.
    
    Resolution Logic:
    1. Extract hostname and strip port (localhost:5000 → localhost)
    2. Extract subdomain (first part before first dot)
    3. Handle special cases: localhost, 127.x.x.x (set g.tenant = None)
    4. Query Company by slug for tenant resolution
    5. Abort with 404 if tenant not found
    
    Examples:
        acme.localhost:5000    → g.tenant = Company(slug='acme')
        localhost:5000         → g.tenant = None (root domain)
        127.0.0.1:5000        → g.tenant = None (IP access)
        unknown.localhost      → 404 (tenant not found)
    
    Raises:
        404: When subdomain doesn't match any Company slug
    """
    host = request.host.split(':')[0]

    # Special handling for ngrok tunnels (both free and paid domains)
    if host.endswith('.ngrok-free.app') or host.endswith('.ngrok.app'):
        parts = host.split('.')
        # pattern: <id>.ngrok-free.app  → no tenant
        if len(parts) == 3:
            g.tenant = None
            return
        # pattern: <tenant>.<id>.ngrok-free.app  → tenant is first label
        elif len(parts) >= 4:
            subdomain = parts[0]
        # proceed with normal flow below using updated subdomain
    else:
        # Extract subdomain (first part before first dot)
        subdomain = host.split('.')[0]

    # Handle root domain, localhost access, and nip.io development URLs
    # Allow non-tenant access for marketing pages, admin panels, etc.
    if subdomain in ("localhost", "127", "127-0-0-1") or re.fullmatch(r"\d+-\d+-\d+-\d+", subdomain):
        g.tenant = None
        return
    
    # Resolve tenant by slug lookup
    g.tenant = Company.query.filter_by(slug=subdomain).first()
    
    # Abort early for unknown tenants
    if g.tenant is None:
        abort(404)


def get_current_tenant():
    """
    Helper function to get the current tenant context.
    
    Returns:
        Company: Current tenant Company object or None for root domain
        
    Example:
        tenant = get_current_tenant()
        if tenant:
            # Filter data by tenant
            data = ESGData.query.filter_by(company_id=tenant.id).all()
        else:
            # Handle root domain access
            return render_template('marketing/homepage.html')
    """
    return getattr(g, 'tenant', None)


def require_tenant():
    """
    Helper function to enforce tenant context for protected operations.
    
    This function should be called in views or services that require tenant
    isolation to ensure that a valid tenant is loaded.
    
    Raises:
        404: If no tenant is loaded in the current request context
        
    Example:
        @app.route('/tenant-protected-endpoint')
        def protected_endpoint():
            require_tenant()  # Ensures tenant is loaded
            entities = Entity.query_for_tenant(db.session).all()
            return render_template('entities.html', entities=entities)
    """
    if not hasattr(g, 'tenant') or g.tenant is None:
        abort(404)  # No tenant context available 