import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock

from app import create_app
from app.extensions import db
from app.models import User, Company
from app.services.initial_data import ensure_super_admin, verify_seed_state, create_initial_data
from app.config import TestingConfig


class TestSeedData(unittest.TestCase):
    """Test suite for T3 seed data functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Configure test app with temporary database
        class TestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{self.db_path}'
            TESTING = True
        
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_empty_db_creates_super_admin(self):
        """Test that starting with empty DB creates exactly one SUPER_ADMIN and zero companies."""
        # Verify initial state is empty
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(Company.query.count(), 0)
        
        # Run seed data
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'test@example.com',
            'SUPER_ADMIN_PASSWORD': 'testpass123',
            'SUPER_ADMIN_USERNAME': 'testadmin'
        }):
            result = create_initial_data()
        
        # Verify expected outcome
        self.assertTrue(result['success'])
        self.assertTrue(result['super_admin_created'])
        
        # Verify exactly one SUPER_ADMIN created
        super_admin_count = User.query.filter_by(role='SUPER_ADMIN').count()
        total_user_count = User.query.count()
        company_count = Company.query.count()
        
        self.assertEqual(super_admin_count, 1)
        self.assertEqual(total_user_count, 1)
        self.assertEqual(company_count, 0)
        
        # Verify super admin properties
        super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        self.assertEqual(super_admin.email, 'test@example.com')
        self.assertEqual(super_admin.username, 'testadmin')
        self.assertIsNone(super_admin.company_id)  # SUPER_ADMIN has no company
        self.assertTrue(super_admin.is_active)
        self.assertTrue(super_admin.is_email_verified)
        self.assertTrue(super_admin.is_super_admin())
    
    def test_super_admin_already_exists_no_duplicate(self):
        """Test that if SUPER_ADMIN already exists, no new user is created."""
        # Create existing SUPER_ADMIN
        existing_admin = User(
            username='existing',
            email='existing@example.com',
            role='SUPER_ADMIN',
            password='existingpass',
            is_active=True
        )
        db.session.add(existing_admin)
        db.session.commit()
        
        initial_count = User.query.count()
        
        # Run seed data
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'new@example.com',
            'SUPER_ADMIN_PASSWORD': 'newpass123'
        }):
            result = create_initial_data()
        
        # Verify no new user created
        self.assertTrue(result['success'])
        self.assertFalse(result['super_admin_created'])
        
        final_count = User.query.count()
        super_admin_count = User.query.filter_by(role='SUPER_ADMIN').count()
        
        self.assertEqual(final_count, initial_count)
        self.assertEqual(super_admin_count, 1)
        
        # Verify original admin still exists
        original_admin = User.query.filter_by(email='existing@example.com').first()
        self.assertIsNotNone(original_admin)
        self.assertEqual(original_admin.role, 'SUPER_ADMIN')
    
    def test_env_var_defaults_used_when_missing(self):
        """Test that default values are used when environment variables are missing."""
        # Clear environment variables
        env_vars = ['SUPER_ADMIN_EMAIL', 'SUPER_ADMIN_PASSWORD', 'SUPER_ADMIN_USERNAME']
        with patch.dict(os.environ, {var: '' for var in env_vars}, clear=True):
            # Remove any existing values
            for var in env_vars:
                os.environ.pop(var, None)
            
            result = ensure_super_admin()
        
        # Verify user created with defaults
        self.assertTrue(result)
        
        super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        self.assertIsNotNone(super_admin)
        self.assertEqual(super_admin.email, 'admin@example.com')
        self.assertEqual(super_admin.username, 'superadmin')
    
    def test_env_var_custom_values_used(self):
        """Test that custom environment variable values are used when provided."""
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'custom@test.com',
            'SUPER_ADMIN_PASSWORD': 'custompass456',
            'SUPER_ADMIN_USERNAME': 'customadmin'
        }):
            result = ensure_super_admin()
        
        # Verify user created with custom values
        self.assertTrue(result)
        
        super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        self.assertIsNotNone(super_admin)
        self.assertEqual(super_admin.email, 'custom@test.com')
        self.assertEqual(super_admin.username, 'customadmin')
    
    def test_idempotent_multiple_runs(self):
        """Test that running seed data multiple times is safe (idempotent)."""
        # First run
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'test@example.com',
            'SUPER_ADMIN_PASSWORD': 'testpass123'
        }):
            result1 = create_initial_data()
        
        # Verify first run created user
        self.assertTrue(result1['success'])
        self.assertTrue(result1['super_admin_created'])
        
        first_count = User.query.count()
        first_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        
        # Second run
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'different@example.com',  # Different email
            'SUPER_ADMIN_PASSWORD': 'differentpass'
        }):
            result2 = create_initial_data()
        
        # Verify second run didn't create new user
        self.assertTrue(result2['success'])
        self.assertFalse(result2['super_admin_created'])
        
        second_count = User.query.count()
        second_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        
        # Verify counts and that original admin unchanged
        self.assertEqual(first_count, second_count)
        self.assertEqual(first_admin.id, second_admin.id)
        self.assertEqual(first_admin.email, second_admin.email)  # Original email preserved
    
    def test_verify_seed_state_function(self):
        """Test the verify_seed_state function returns correct information."""
        # Create test data
        super_admin = User(
            username='admin',
            email='admin@test.com',
            role='SUPER_ADMIN',
            password='pass123'
        )
        regular_user = User(
            username='user',
            email='user@test.com',
            role='USER',
            password='pass123'
        )
        company = Company(name='Test Company', slug='test-co')
        
        db.session.add_all([super_admin, regular_user, company])
        db.session.commit()
        
        # Verify state
        state = verify_seed_state()
        
        self.assertEqual(state['super_admin_count'], 1)
        self.assertEqual(state['total_user_count'], 2)
        self.assertEqual(state['company_count'], 1)
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        test_password = 'testpassword123'
        
        with patch.dict(os.environ, {
            'SUPER_ADMIN_EMAIL': 'test@example.com',
            'SUPER_ADMIN_PASSWORD': test_password
        }):
            ensure_super_admin()
        
        super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
        
        # Verify password is hashed (not stored in plain text)
        self.assertNotEqual(super_admin.password, test_password)
        self.assertTrue(super_admin.password.startswith('pbkdf2:sha256:'))
        
        # Verify password check works
        self.assertTrue(super_admin.check_password(test_password))
        self.assertFalse(super_admin.check_password('wrongpassword'))
    
    def test_database_rollback_on_error(self):
        """Test that database session is rolled back on errors."""
        # Mock db.session.commit to raise an exception
        with patch('app.extensions.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Database error")
            
            with patch.dict(os.environ, {
                'SUPER_ADMIN_EMAIL': 'test@example.com',
                'SUPER_ADMIN_PASSWORD': 'testpass123'
            }):
                with self.assertRaises(Exception):
                    ensure_super_admin()
        
        # Verify no user was created due to rollback
        user_count = User.query.count()
        self.assertEqual(user_count, 0)


if __name__ == '__main__':
    unittest.main() 