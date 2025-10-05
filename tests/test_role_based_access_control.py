"""
Unit Tests for Role-Based Access Control Decorators (T6)

This test suite validates the role-based access control decorators:
- tenant_required_for(*roles): Role + tenant validation
- role_required(required_role): Exact role validation
- admin_or_super_admin_required: Convenience decorator

Test Coverage:
- ❌ ADMIN from Company A tries to access Company B's data → 403 Forbidden
- ❌ USER accesses /admin/* → 403 Forbidden  
- ✅ SUPER_ADMIN accesses /superadmin/* → 200 OK
- ✅ ADMIN accesses their own company's /admin page → 200 OK
- ✅ USER accesses their own company's /user page → 200 OK
- Cross-tenant isolation validation
- Proper logging of access attempts
"""

import pytest
from flask import Flask, g
from unittest.mock import patch, MagicMock
from app.decorators.auth import tenant_required_for, role_required, admin_or_super_admin_required


class MockUser:
    """Mock user object for testing."""
    def __init__(self, user_id, role, company_id=None):
        self.id = user_id
        self.role = role
        self.company_id = company_id


class MockTenant:
    """Mock tenant object for testing."""
    def __init__(self, tenant_id, name):
        self.id = tenant_id
        self.name = name


class TestRoleBasedAccessControl:
    """Test suite for role-based access control decorators."""
    
    @pytest.fixture
    def app(self):
        """Create minimal test Flask application."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def mock_users(self):
        """Create mock users for testing."""
        return {
            'super_admin': MockUser(1, 'SUPER_ADMIN', None),
            'admin_a': MockUser(2, 'ADMIN', 100),
            'admin_b': MockUser(3, 'ADMIN', 200),
            'user_a': MockUser(4, 'USER', 100),
            'user_b': MockUser(5, 'USER', 200),
        }
    
    @pytest.fixture
    def mock_tenants(self):
        """Create mock tenants for testing."""
        return {
            'company_a': MockTenant(100, 'Company A'),
            'company_b': MockTenant(200, 'Company B'),
        }

    def test_tenant_required_for_decorator_valid_access(self, app, mock_users, mock_tenants):
        """Test that tenant_required_for allows valid access."""
        with app.app_context():
            # Create a test route with the decorator
            @app.route('/test-tenant-user')
            @tenant_required_for('USER')
            def test_tenant_user():
                return 'Success', 200
            
            # Mock current_user as USER from Company A
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-tenant-user'):
                    g.tenant = mock_tenants['company_a']
                    result = test_tenant_user()
                    assert result[1] == 200
                    assert result[0] == 'Success'

    def test_tenant_required_for_decorator_wrong_role(self, app, mock_users, mock_tenants):
        """Test that tenant_required_for denies access for wrong role."""
        with app.app_context():
            @app.route('/test-admin-only')
            @tenant_required_for('ADMIN')
            def test_admin_only():
                return 'Success', 200
            
            # Mock current_user as USER (wrong role) from Company A
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-admin-only'):
                    g.tenant = mock_tenants['company_a']
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_admin_only()

    def test_tenant_required_for_decorator_cross_tenant_access(self, app, mock_users, mock_tenants):
        """Test that tenant_required_for prevents cross-tenant access."""
        with app.app_context():
            @app.route('/test-cross-tenant')
            @tenant_required_for('ADMIN')
            def test_cross_tenant():
                return 'Success', 200
            
            # Mock current_user as ADMIN from Company A trying to access Company B
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-cross-tenant'):
                    g.tenant = mock_tenants['company_b']
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_cross_tenant()

    def test_tenant_required_for_decorator_no_tenant_context(self, app, mock_users):
        """Test that tenant_required_for denies access without tenant context."""
        with app.app_context():
            @app.route('/test-no-tenant')
            @tenant_required_for('USER')
            def test_no_tenant():
                return 'Success', 200
            
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-no-tenant'):
                    g.tenant = None
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_no_tenant()

    def test_role_required_decorator_super_admin_access(self, app, mock_users):
        """Test that role_required allows SUPER_ADMIN access."""
        with app.app_context():
            @app.route('/test-super-admin')
            @role_required('SUPER_ADMIN')
            def test_super_admin():
                return 'Super Admin Success', 200
            
            with patch('app.decorators.auth.current_user', mock_users['super_admin']):
                with app.test_request_context('/test-super-admin'):
                    result = test_super_admin()
                    assert result[1] == 200
                    assert result[0] == 'Super Admin Success'

    def test_role_required_decorator_wrong_role(self, app, mock_users):
        """Test that role_required denies access for wrong role."""
        with app.app_context():
            @app.route('/test-super-admin-only')
            @role_required('SUPER_ADMIN')
            def test_super_admin_only():
                return 'Success', 200
            
            # Try to access with ADMIN role (should fail)
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-super-admin-only'):
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_super_admin_only()

    def test_admin_or_super_admin_required_super_admin(self, app, mock_users):
        """Test admin_or_super_admin_required allows SUPER_ADMIN access."""
        with app.app_context():
            @app.route('/test-admin-or-super')
            @admin_or_super_admin_required
            def test_admin_or_super():
                return 'Admin or Super Success', 200
            
            with patch('app.decorators.auth.current_user', mock_users['super_admin']):
                with app.test_request_context('/test-admin-or-super'):
                    result = test_admin_or_super()
                    assert result[1] == 200
                    assert result[0] == 'Admin or Super Success'

    def test_admin_or_super_admin_required_admin_with_tenant(self, app, mock_users, mock_tenants):
        """Test admin_or_super_admin_required allows ADMIN with proper tenant."""
        with app.app_context():
            @app.route('/test-admin-with-tenant')
            @admin_or_super_admin_required
            def test_admin_with_tenant():
                return 'Admin Success', 200
            
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-admin-with-tenant'):
                    g.tenant = mock_tenants['company_a']
                    result = test_admin_with_tenant()
                    assert result[1] == 200
                    assert result[0] == 'Admin Success'

    def test_admin_or_super_admin_required_admin_cross_tenant(self, app, mock_users, mock_tenants):
        """Test admin_or_super_admin_required denies ADMIN cross-tenant access."""
        with app.app_context():
            @app.route('/test-admin-cross-tenant')
            @admin_or_super_admin_required
            def test_admin_cross_tenant():
                return 'Success', 200
            
            # ADMIN from Company A trying to access Company B
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-admin-cross-tenant'):
                    g.tenant = mock_tenants['company_b']
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_admin_cross_tenant()

    def test_admin_or_super_admin_required_user_denied(self, app, mock_users, mock_tenants):
        """Test admin_or_super_admin_required denies USER access."""
        with app.app_context():
            @app.route('/test-user-denied')
            @admin_or_super_admin_required
            def test_user_denied():
                return 'Success', 200
            
            # USER should be denied access
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-user-denied'):
                    g.tenant = mock_tenants['company_a']
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_user_denied()

    def test_multiple_roles_in_tenant_required_for(self, app, mock_users, mock_tenants):
        """Test tenant_required_for with multiple allowed roles."""
        with app.app_context():
            @app.route('/test-multiple-roles')
            @tenant_required_for('ADMIN', 'USER')
            def test_multiple_roles():
                return 'Multiple Roles Success', 200
            
            # Test ADMIN access
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-multiple-roles'):
                    g.tenant = mock_tenants['company_a']
                    result = test_multiple_roles()
                    assert result[1] == 200
            
            # Test USER access
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-multiple-roles'):
                    g.tenant = mock_tenants['company_a']
                    result = test_multiple_roles()
                    assert result[1] == 200

    def test_logging_unauthorized_access(self, app, mock_users, mock_tenants):
        """Test that unauthorized access attempts are properly logged."""
        with app.app_context():
            with patch('app.decorators.auth.current_app.logger') as mock_logger:
                @app.route('/test-logging')
                @tenant_required_for('ADMIN')
                def test_logging():
                    return 'Success', 200
                
                # ADMIN from Company A trying to access Company B (should log warning)
                with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                    with app.test_request_context('/test-logging'):
                        g.tenant = mock_tenants['company_b']
                        with pytest.raises(Exception):
                            test_logging()
                        
                        # Verify warning was logged
                        mock_logger.warning.assert_called()
                        call_args = mock_logger.warning.call_args[0][0]
                        assert 'Cross-tenant access attempt' in call_args

    def test_logging_successful_access(self, app, mock_users, mock_tenants):
        """Test that successful access is properly logged."""
        with app.app_context():
            with patch('app.decorators.auth.current_app.logger') as mock_logger:
                @app.route('/test-success-logging')
                @tenant_required_for('USER')
                def test_success_logging():
                    return 'Success', 200
                
                with patch('app.decorators.auth.current_user', mock_users['user_a']):
                    with app.test_request_context('/test-success-logging'):
                        g.tenant = mock_tenants['company_a']
                        result = test_success_logging()
                        assert result[1] == 200
                        
                        # Verify debug log was called
                        mock_logger.debug.assert_called()
                        call_args = mock_logger.debug.call_args[0][0]
                        assert 'Access granted' in call_args

    def test_tenant_required_for_admin_no_tenant_context(self, app, mock_users):
        """Test that ADMIN requires tenant context."""
        with app.app_context():
            @app.route('/test-admin-no-tenant')
            @admin_or_super_admin_required
            def test_admin_no_tenant():
                return 'Success', 200
            
            # ADMIN without tenant context should be denied
            with patch('app.decorators.auth.current_user', mock_users['admin_a']):
                with app.test_request_context('/test-admin-no-tenant'):
                    g.tenant = None
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_admin_no_tenant()

    def test_role_validation_edge_cases(self, app, mock_users, mock_tenants):
        """Test edge cases in role validation."""
        with app.app_context():
            # Test case-sensitive role matching
            @app.route('/test-case-sensitive')
            @tenant_required_for('user')  # lowercase
            def test_case_sensitive():
                return 'Success', 200
            
            # Should fail because role is 'USER' (uppercase) but decorator expects 'user' (lowercase)
            with patch('app.decorators.auth.current_user', mock_users['user_a']):
                with app.test_request_context('/test-case-sensitive'):
                    g.tenant = mock_tenants['company_a']
                    with pytest.raises(Exception):  # Should raise 403 abort
                        test_case_sensitive()

    def test_super_admin_bypasses_tenant_validation(self, app, mock_users, mock_tenants):
        """Test that SUPER_ADMIN can access admin routes without tenant validation."""
        with app.app_context():
            @app.route('/test-super-admin-bypass')
            @admin_or_super_admin_required
            def test_super_admin_bypass():
                return 'Super Admin Bypass Success', 200
            
            # SUPER_ADMIN should work even with different tenant or no tenant
            with patch('app.decorators.auth.current_user', mock_users['super_admin']):
                # Test with different tenant
                with app.test_request_context('/test-super-admin-bypass'):
                    g.tenant = mock_tenants['company_a']  # SUPER_ADMIN has no company_id
                    result = test_super_admin_bypass()
                    assert result[1] == 200
                
                # Test with no tenant
                with app.test_request_context('/test-super-admin-bypass'):
                    g.tenant = None
                    result = test_super_admin_bypass()
                    assert result[1] == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 