import pytest
from app import create_app
from app.extensions import db
from app.models import User, Company, Framework, FrameworkDataField, DataPointAssignment, Topic, Entity
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime, timedelta

@pytest.fixture(scope='module')
def test_client():
    app = create_app()
    app.config.from_object('app.config.TestingConfig')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            super_admin_password = "superadminpassword"
            # Fetch the super admin user created by initial data seeding
            super_admin_user = User.query.filter_by(role="SUPER_ADMIN").first()
            if not super_admin_user:
                super_admin_user = User(
                    name="Super Admin",
                    email="superadmin@example.com",
                    password=generate_password_hash(super_admin_password),
                    role="SUPER_ADMIN",
                    is_active=True,
                    is_email_verified=True
                )
                db.session.add(super_admin_user)
                db.session.commit()
                db.session.refresh(super_admin_user) # Refresh to get the auto-generated ID

            # Create a test company and admin user
            test_company = Company(
                name="Test Company",
                slug="test-company"
            )
            db.session.add(test_company)
            db.session.commit()
            db.session.refresh(test_company) # Refresh to get the auto-generated ID

            admin_password = "adminpassword"
            admin_user = User(
                    name="Test Admin",
                    email="admin@test.com",
                    password=generate_password_hash(admin_password),
                    role="ADMIN",
                    company_id=test_company.id, # Use the auto-generated company ID
                    is_active=True,
                    is_email_verified=True
                )
            db.session.add(admin_user)
            db.session.commit()
            db.session.refresh(admin_user) # Refresh to get the auto-generated ID

            # Create a test entity for the company
            test_entity = Entity(
                name="Test Entity",
                entity_type="Office",
                company_id=test_company.id # Use the auto-generated company ID
            )
            db.session.add(test_entity)
            db.session.commit()
            db.session.refresh(test_entity) # Refresh to get the auto-generated ID

            # Store users and company in client for easy access
            client.super_admin_user = super_admin_user
            client.super_admin_password = super_admin_password
            client.admin_user = admin_user
            client.admin_password = admin_password
            client.test_company = test_company
            client.test_entity = test_entity

        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

@pytest.fixture(scope='function')
def auth_client(test_client):
    # Log in the admin user
    with test_client.session_transaction() as sess:
        sess['user_id'] = test_client.admin_user.id
        sess['company_id'] = test_client.test_company.company_id
    yield test_client
    with test_client.session_transaction() as sess:
        sess.pop('user_id', None)
        sess.pop('company_id', None)

@pytest.fixture(scope='function')
def super_admin_auth_client(test_client):
    # Log in the super admin user
    with test_client.session_transaction() as sess:
        sess['user_id'] = test_client.super_admin_user.id
        sess['company_id'] = None # Super admin has no company_id
    yield test_client
    with test_client.session_transaction() as sess:
        sess.pop('user_id', None)
        sess.pop('company_id', None)

@pytest.fixture(scope='function')
def setup_framework_data(auth_client):
    with auth_client.application.app_context():
        # Re-fetch objects to ensure they are attached to the current session
        company = db.session.get(Company, auth_client.test_company.id)
        admin_user = db.session.get(User, auth_client.admin_user.id)
        test_entity = db.session.get(Entity, auth_client.test_entity.id)

        company_id = company.id
        admin_user_id = admin_user.id
        test_entity_id = test_entity.id

        # Framework 1: High Coverage
        fw1 = Framework(framework_id=str(uuid.uuid4()), framework_name="High Coverage FW", description="FW1 desc", company_id=company_id)
        db.session.add(fw1)
        db.session.flush()

        topic1_fw1 = Topic(topic_id=str(uuid.uuid4()), name="Energy", framework_id=fw1.framework_id, company_id=company_id)
        db.session.add(topic1_fw1)
        db.session.flush()

        fields_fw1 = []
        for i in range(10):
            field = FrameworkDataField(
                field_id=str(uuid.uuid4()), framework_id=fw1.framework_id, company_id=company_id,
                field_name=f"FW1 Field {i}", field_code=f"FW1_F{i}", value_type="Numeric",
                topic_id=topic1_fw1.topic_id
            )
            fields_fw1.append(field)
            db.session.add(field)
        db.session.flush()

        # Assign 80% of fields for coverage
        for i, field in enumerate(fields_fw1):
            if i % 10 < 8: # 80% coverage
                assignment = DataPointAssignment(
                    assignment_id=str(uuid.uuid4()), field_id=field.field_id, entity_id=test_entity_id,
                    company_id=company_id, assigned_by=admin_user_id, assigned_date=datetime.utcnow() - timedelta(days=i),
                    frequency="Annual"
                )
                db.session.add(assignment)
        db.session.commit()

        # Framework 2: Low Coverage
        fw2 = Framework(framework_id=str(uuid.uuid4()), framework_name="Low Coverage FW", description="FW2 desc", company_id=company_id)
        db.session.add(fw2)
        db.session.flush()

        topic1_fw2 = Topic(topic_id=str(uuid.uuid4()), name="Water", framework_id=fw2.framework_id, company_id=company_id)
        db.session.add(topic1_fw2)
        db.session.flush()

        fields_fw2 = []
        for i in range(10):
            field = FrameworkDataField(
                field_id=str(uuid.uuid4()), framework_id=fw2.framework_id, company_id=company_id,
                field_name=f"FW2 Field {i}", field_code=f"FW2_F{i}", value_type="Numeric",
                topic_id=topic1_fw2.topic_id
            )
            fields_fw2.append(field)
            db.session.add(field)
        db.session.flush()

        # Assign 20% of fields for coverage
        for i, field in enumerate(fields_fw2):
            if i % 10 < 2: # 20% coverage
                assignment = DataPointAssignment(
                    assignment_id=str(uuid.uuid4()), field_id=field.field_id, entity_id=test_entity_id,
                    company_id=company_id, assigned_by=admin_user_id, assigned_date=datetime.utcnow() - timedelta(days=i),
                    frequency="Annual"
                )
                db.session.add(assignment)
        db.session.commit()

        # Framework 3: No Coverage, Recent Activity
        fw3 = Framework(framework_id=str(uuid.uuid4()), framework_name="New FW", description="FW3 desc", company_id=company_id, created_at=datetime.utcnow() - timedelta(minutes=5))
        db.session.add(fw3)
        db.session.flush()

        topic1_fw3 = Topic(topic_id=str(uuid.uuid4()), name="Waste", framework_id=fw3.framework_id, company_id=company_id)
        db.session.add(topic1_fw3)
        db.session.flush()

        fields_fw3 = []
        for i in range(5):
            field = FrameworkDataField(
                field_id=str(uuid.uuid4()), framework_id=fw3.framework_id, company_id=company_id,
                field_name=f"FW3 Field {i}", field_code=f"FW3_F{i}", value_type="Numeric",
                topic_id=topic1_fw3.topic_id
            )
            fields_fw3.append(field)
            db.session.add(field)
        db.session.commit()

        # Framework 4: Another Framework for list/search
        fw4 = Framework(framework_id=str(uuid.uuid4()), framework_name="Another FW", description="Another framework for testing.", company_id=company_id)
        db.session.add(fw4)
        db.session.commit()

        # Framework 5: For search
        fw5 = Framework(framework_id=str(uuid.uuid4()), framework_name="Searchable Framework", description="This framework is for search tests.", company_id=company_id)
        db.session.add(fw5)
        db.session.commit()

        yield {
            "fw1": fw1, "fw2": fw2, "fw3": fw3, "fw4": fw4, "fw5": fw5,
            "fields_fw1": fields_fw1, "fields_fw2": fields_fw2, "fields_fw3": fields_fw3,
            "topic1_fw1": topic1_fw1, "topic1_fw2": topic1_fw2, "topic1_fw3": topic1_fw3
        }

class TestFrameworksAPI:

    def test_get_framework_stats(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/stats')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert data['total_frameworks'] == 5
        assert data['active_assignments'] > 0
        assert 'overall_coverage' in data
        assert 'recent_activity' in data

    def test_get_framework_stats_super_admin(self, super_admin_auth_client, setup_framework_data):
        response = super_admin_auth_client.get('/admin/frameworks/stats')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        # Super admin sees all frameworks across all companies (if any)
        assert data['total_frameworks'] >= 5 
        assert data['active_assignments'] > 0
        assert 'overall_coverage' in data
        assert 'recent_activity' in data

    def test_get_framework_chart_data(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/chart_data')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert 'top_5_frameworks' in data
        assert len(data['top_5_frameworks']) <= 5
        assert 'framework_type_distribution' in data
        assert 'custom' in data['framework_type_distribution']
        assert 'standard' in data['framework_type_distribution']

    def test_list_frameworks_no_search_no_sort(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/list')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert len(data['frameworks']) == 5
        # Check that coverage is included
        assert 'coverage_percentage' in data['frameworks'][0]

    def test_list_frameworks_search(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/list?search=searchable')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert len(data['frameworks']) == 1
        assert data['frameworks'][0]['framework_name'] == "Searchable Framework"

    def test_list_frameworks_sort_by_name_desc(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/list?sort=name_desc')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert data['frameworks'][0]['framework_name'] == "Searchable Framework"
        assert data['frameworks'][-1]['framework_name'] == "Another FW" # Assuming alphabetical order

    def test_list_frameworks_sort_by_coverage_asc(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/list?sort=coverage_asc')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        # Low Coverage FW should have lower coverage than High Coverage FW
        assert data['frameworks'][0]['framework_name'] == "New FW" # 0% coverage
        assert data['frameworks'][1]['framework_name'] == "Low Coverage FW" # 20% coverage

    def test_get_framework_coverage(self, auth_client, setup_framework_data):
        fw1_id = setup_framework_data['fw1'].framework_id
        response = auth_client.get(f'/admin/frameworks/coverage/{fw1_id}')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert data['coverage_percentage'] == 80.0
        assert data['total_fields'] == 10
        assert data['fields_with_data'] == 8
        assert 'last_updated' in data

    def test_get_framework_coverage_non_existent(self, auth_client):
        response = auth_client.get(f'/admin/frameworks/coverage/{uuid.uuid4()}')
        assert response.status_code == 404
        assert response.json['success'] == False

    def test_get_framework_details(self, auth_client, setup_framework_data):
        fw1_id = setup_framework_data['fw1'].framework_id
        response = auth_client.get(f'/admin/frameworks/{fw1_id}/details')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert data['framework_name'] == "High Coverage FW"
        assert 'description' in data
        assert 'total_fields' in data
        assert 'computed_fields' in data
        assert 'data_points' in data
        assert len(data['data_points']) == 10 # All fields for FW1

    def test_get_framework_details_non_existent(self, auth_client):
        response = auth_client.get(f'/admin/frameworks/{uuid.uuid4()}/details')
        assert response.status_code == 404
        assert response.json['success'] == False

    def test_get_recent_activity(self, auth_client, setup_framework_data):
        response = auth_client.get('/admin/frameworks/recent_activity')
        assert response.status_code == 200
        data = response.json
        assert data['success'] == True
        assert len(data['activities']) > 0
        assert 'type' in data['activities'][0]
        assert 'name' in data['activities'][0]
        assert 'date' in data['activities'][0]
        # Check if the most recent activity is the New FW creation
        assert data['activities'][0]['type'] == 'Framework Created'
        assert data['activities'][0]['name'] == 'New FW'
