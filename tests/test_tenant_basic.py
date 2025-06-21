"""
Basic tenant middleware tests (Epic 2, Task T4)

Simplified tests that focus on core tenant resolution logic
without complex database dependencies.
"""

import pytest
import os
from flask import Flask, g
from app.middleware.tenant import load_tenant, get_current_tenant, require_tenant
from app.models.company import Company
from app.extensions import db


class TestTenantBasic:
    """Basic tests for tenant middleware functionality."""

    @pytest.fixture
    def simple_app(self):
        """Create a minimal Flask app for testing."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Set testing environment
        os.environ['TESTING'] = '1'
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            
            # Create test companies
            acme = Company(name="Acme Corp", slug="acme")
            beta = Company(name="Beta Inc", slug="beta")
            
            db.session.add(acme)
            db.session.add(beta)
            db.session.commit()
            
            yield app
            
            db.drop_all()
        
        # Clean up
        if 'TESTING' in os.environ:
            del os.environ['TESTING']

    def test_localhost_fallback(self, simple_app):
        """Test that localhost access sets tenant to None."""
        with simple_app.test_request_context('/', headers={'Host': 'localhost'}):
            load_tenant()
            assert g.tenant is None

        with simple_app.test_request_context('/', headers={'Host': 'localhost:5000'}):
            load_tenant()
            assert g.tenant is None

    def test_ip_address_fallback(self, simple_app):
        """Test that IP address access sets tenant to None."""
        with simple_app.test_request_context('/', headers={'Host': '127.0.0.1'}):
            load_tenant()
            assert g.tenant is None

        with simple_app.test_request_context('/', headers={'Host': '127.0.0.1:5000'}):
            load_tenant()
            assert g.tenant is None

    def test_known_tenant_resolution(self, simple_app):
        """Test that known tenant subdomains resolve correctly."""
        with simple_app.test_request_context('/', headers={'Host': 'acme.localhost'}):
            load_tenant()
            assert g.tenant is not None
            assert g.tenant.slug == 'acme'
            assert g.tenant.name == 'Acme Corp'

        with simple_app.test_request_context('/', headers={'Host': 'beta.localhost:5000'}):
            load_tenant()
            assert g.tenant is not None
            assert g.tenant.slug == 'beta'
            assert g.tenant.name == 'Beta Inc'

    def test_unknown_tenant_404(self, simple_app):
        """Test that unknown tenant subdomains return 404."""
        with pytest.raises(Exception):  # Should abort(404)
            with simple_app.test_request_context('/', headers={'Host': 'unknown.localhost'}):
                load_tenant()

    def test_get_current_tenant_helper(self, simple_app):
        """Test the get_current_tenant helper function."""
        with simple_app.test_request_context('/', headers={'Host': 'acme.localhost'}):
            load_tenant()
            current_tenant = get_current_tenant()
            assert current_tenant == g.tenant
            assert current_tenant.slug == 'acme'

        with simple_app.test_request_context('/', headers={'Host': 'localhost'}):
            load_tenant()
            current_tenant = get_current_tenant()
            assert current_tenant is None

    def test_require_tenant_helper(self, simple_app):
        """Test the require_tenant helper function."""
        # Should not raise for valid tenant
        with simple_app.test_request_context('/', headers={'Host': 'acme.localhost'}):
            load_tenant()
            require_tenant()  # Should not raise

        # Should raise for root domain
        with pytest.raises(Exception):  # Should abort(404)
            with simple_app.test_request_context('/', headers={'Host': 'localhost'}):
                load_tenant()
                require_tenant()

    def test_port_handling(self, simple_app):
        """Test proper port stripping in subdomain extraction."""
        test_cases = [
            ('acme.localhost:5000', 'acme'),
            ('beta.localhost:8080', 'beta'),
            ('acme.example.com:443', 'acme'),
        ]
        
        for host, expected_slug in test_cases:
            with simple_app.test_request_context('/', headers={'Host': host}):
                load_tenant()
                assert g.tenant.slug == expected_slug 