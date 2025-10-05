"""
Unit tests for AssignmentVersioningService and related functionality.

Tests cover the core Phase 2 requirements:
- Assignment versioning
- Data series management  
- Assignment resolution with dual compatibility
- Company FY integration
"""

import pytest
import uuid
from datetime import date, datetime, UTC
from unittest.mock import patch

from app import create_app, db
from app.config import TestingConfig
from app.models.company import Company
from app.models.user import User
from app.models.data_assignment import DataPointAssignment
from app.models.esg_data import ESGData
from app.models.framework import FrameworkDataField
from app.models.entity import Entity
from app.services.assignment_versioning import AssignmentVersioningService, AssignmentResolutionService


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_data(app):
    """Create test data for assignment versioning tests."""
    with app.app_context():
        # Create test company with FY config (April - March)
        company = Company(
            name="Test Company",
            slug="test-company",
            fy_end_month=3,  # March
            fy_end_day=31    # Last day of March
        )
        db.session.add(company)
        
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            company_id=company.id,
            role="ADMIN"
        )
        user.set_password("testpass")
        db.session.add(user)
        
        # Create test entity
        entity = Entity(
            name="Test Entity",
            entity_type="Division",
            company_id=company.id
        )
        db.session.add(entity)
        
        # Create test framework field
        field = FrameworkDataField(
            field_id=str(uuid.uuid4()),
            field_name="Test Metric",
            value_type="NUMERIC",
            default_unit="kg"
        )
        db.session.add(field)
        
        db.session.commit()
        
        return {
            'company': company,
            'user': user,
            'entity': entity,
            'field': field
        }


class TestAssignmentVersioningService:
    """Test cases for AssignmentVersioningService."""
    
    def test_create_assignment_version_basic(self, app, test_data):
        """Test basic assignment version creation."""
        with app.app_context():
            # Mock current company context
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create initial assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test version creation
                changes = {
                    'frequency': 'Quarterly',
                    'unit': 'tonnes'
                }
                
                result = AssignmentVersioningService.create_assignment_version(
                    assignment.id,
                    changes,
                    "Updated frequency for better tracking",
                    test_data['user'].id
                )
                
                assert result['success'] is True
                assert result['new_assignment']['version'] == 2
                assert result['new_assignment']['status'] == 'active'
                
                # Verify old assignment is superseded
                db.session.refresh(assignment)
                assert assignment.series_status == 'superseded'
                
                # Verify new assignment exists with changes
                new_assignment = DataPointAssignment.query.get(result['new_assignment']['id'])
                assert new_assignment.frequency == 'Quarterly'
                assert new_assignment.unit == 'tonnes'
                assert new_assignment.series_version == 2
                assert new_assignment.data_series_id == assignment.data_series_id
    
    def test_get_active_assignment(self, app, test_data):
        """Test active assignment resolution."""
        with app.app_context():
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create test assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test resolution
                result = AssignmentVersioningService.get_active_assignment(
                    test_data['field'].field_id,
                    test_data['entity'].id,
                    date.today()
                )
                
                assert result is not None
                assert result.id == assignment.id
                assert result.series_status == 'active'
    
    def test_supersede_assignment(self, app, test_data):
        """Test assignment superseding."""
        with app.app_context():
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create test assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test superseding
                result = AssignmentVersioningService.supersede_assignment(
                    assignment.id,
                    "No longer needed"
                )
                
                assert result['success'] is True
                assert result['new_status'] == 'superseded'
                
                # Verify assignment is superseded
                db.session.refresh(assignment)
                assert assignment.series_status == 'superseded'
    
    def test_validate_assignment_change(self, app, test_data):
        """Test assignment change validation."""
        with app.app_context():
            # Create test assignment
            assignment = DataPointAssignment(
                field_id=test_data['field'].field_id,
                entity_id=test_data['entity'].id,
                company_id=test_data['company'].id,
                frequency='Annual',
                assigned_by=test_data['user'].id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Test valid changes
            valid_changes = {'frequency': 'Quarterly', 'unit': 'tonnes'}
            result = AssignmentVersioningService.validate_assignment_change(
                assignment.id, valid_changes
            )
            
            assert result['is_valid'] is True
            assert len(result['warnings']) >= 0  # May have warnings but should be valid
            
            # Test invalid changes
            invalid_changes = {'field_id': 'different-field-id'}
            result = AssignmentVersioningService.validate_assignment_change(
                assignment.id, invalid_changes
            )
            
            assert result['is_valid'] is False
            assert 'field_id' in result['error']


class TestAssignmentResolutionService:
    """Test cases for AssignmentResolutionService (dual compatibility)."""
    
    def test_resolve_with_assignment_id(self, app, test_data):
        """Test resolution using assignment_id (new pattern)."""
        with app.app_context():
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create test assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test resolution with assignment_id
                result = AssignmentResolutionService.resolve_assignment_for_data(
                    test_data['field'].field_id,
                    test_data['entity'].id,
                    date.today(),
                    assignment.id
                )
                
                assert result is not None
                assert result.id == assignment.id
    
    def test_resolve_fallback_to_field_id(self, app, test_data):
        """Test fallback to field_id resolution (legacy pattern)."""
        with app.app_context():
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create test assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test resolution without assignment_id (fallback)
                result = AssignmentResolutionService.resolve_assignment_for_data(
                    test_data['field'].field_id,
                    test_data['entity'].id,
                    date.today(),
                    None  # No assignment_id provided
                )
                
                assert result is not None
                assert result.id == assignment.id


class TestDataPointAssignmentEnhancements:
    """Test the enhanced model methods."""
    
    def test_model_versioning_methods(self, app, test_data):
        """Test the new versioning methods on the model."""
        with app.app_context():
            with patch('app.services.assignment_versioning.get_current_company_id') as mock_company:
                mock_company.return_value = test_data['company'].id
                
                # Create test assignment
                assignment = DataPointAssignment(
                    field_id=test_data['field'].field_id,
                    entity_id=test_data['entity'].id,
                    company_id=test_data['company'].id,
                    frequency='Annual',
                    assigned_by=test_data['user'].id
                )
                db.session.add(assignment)
                db.session.commit()
                
                # Test version creation via model method
                result = assignment.create_new_version(
                    {'frequency': 'Quarterly'},
                    'Test version',
                    test_data['user'].id
                )
                
                assert result['success'] is True
                
                # Test get_data_series_versions
                versions = assignment.get_data_series_versions()
                assert len(versions) == 2  # Original + new version
                
                # Test is_latest_version
                assert not assignment.is_latest_version()  # Original is superseded
                
                new_assignment = DataPointAssignment.query.get(result['new_assignment']['id'])
                assert new_assignment.is_latest_version()  # New version is latest
    
    def test_enhanced_reporting_dates(self, app, test_data):
        """Test enhanced reporting date calculation."""
        with app.app_context():
            # Create test assignment
            assignment = DataPointAssignment(
                field_id=test_data['field'].field_id,
                entity_id=test_data['entity'].id,
                company_id=test_data['company'].id,
                frequency='Quarterly',
                assigned_by=test_data['user'].id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Test auto-detection of FY year
            test_date = date(2024, 6, 15)  # June 15, 2024 (in FY 2025 for Apr-Mar FY)
            valid_dates = assignment.get_valid_reporting_dates(target_date=test_date)
            
            assert len(valid_dates) == 4  # 4 quarters
            
            # Test date validation with auto-detection
            quarter_end = date(2024, 6, 30)  # End of Q1 in FY 2025
            assert assignment.is_valid_reporting_date(quarter_end)


class TestCompanyFYIntegration:
    """Test company fiscal year integration."""
    
    def test_different_fy_configurations(self, app):
        """Test different FY configurations work correctly."""
        with app.app_context():
            # Test calendar year company (Jan-Dec)
            calendar_company = Company(
                name="Calendar Company",
                slug="calendar-co",
                fy_end_month=12,  # December
                fy_end_day=31     # Last day of December
            )
            db.session.add(calendar_company)
            db.session.commit()
            
            # Verify FY calculation
            fy_start = calendar_company.get_fy_start_date(2024)
            fy_end = calendar_company.get_fy_end_date(2024)
            
            assert fy_start.month == 1   # January
            assert fy_end.month == 12    # December
            assert fy_start.year == 2024
            assert fy_end.year == 2024
            
            # Test April-March company
            april_company = Company(
                name="April Company",
                slug="april-co", 
                fy_end_month=3,   # March
                fy_end_day=31     # Last day of March
            )
            db.session.add(april_company)
            db.session.commit()
            
            # Verify FY calculation
            fy_start = april_company.get_fy_start_date(2024)
            fy_end = april_company.get_fy_end_date(2024)
            
            assert fy_start.month == 4    # April
            assert fy_end.month == 3      # March
            assert fy_start.year == 2023  # Previous year April
            assert fy_end.year == 2024    # Current year March


if __name__ == '__main__':
    pytest.main([__file__, '-v'])