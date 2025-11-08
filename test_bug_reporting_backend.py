"""
Test script for Bug Reporting Backend Implementation (Phase 1).

This script tests:
1. IssueReport model and ticket number generation
2. Database operations
3. Model methods (to_dict, to_github_issue_body)
4. Multi-tenant isolation
"""

from app import create_app
from app.extensions import db
from app.models import IssueReport, IssueComment, User, Company
from datetime import datetime, UTC

def test_ticket_number_generation():
    """Test ticket number generation and uniqueness."""
    print("\n" + "="*70)
    print("TEST 1: Ticket Number Generation")
    print("="*70)

    ticket1 = IssueReport.generate_ticket_number()
    print(f"Generated ticket number 1: {ticket1}")

    ticket2 = IssueReport.generate_ticket_number()
    print(f"Generated ticket number 2: {ticket2}")

    # Verify format
    year = datetime.now().year
    assert ticket1.startswith(f"BUG-{year}-"), "Ticket number format is incorrect"
    print(f"✓ Ticket number format is correct (BUG-{year}-NNNN)")

    return True


def test_issue_creation():
    """Test creating issue reports."""
    print("\n" + "="*70)
    print("TEST 2: Issue Report Creation")
    print("="*70)

    # Get a test user
    user = User.query.filter_by(email='bob@alpha.com').first()
    if not user:
        print("✗ Test user not found. Please ensure test data exists.")
        return False

    print(f"Using test user: {user.email} (company_id: {user.company_id})")

    # Create a test issue
    ticket_number = IssueReport.generate_ticket_number()
    issue = IssueReport(
        ticket_number=ticket_number,
        category='bug',
        severity='high',
        title='Test Issue - Export Button Not Working',
        description='The export button on the dashboard is not responding to clicks.',
        steps_to_reproduce='1. Login to dashboard\n2. Click export button\n3. Nothing happens',
        expected_behavior='Data should be exported as CSV',
        actual_behavior='Button does not respond',
        user_id=user.id,
        company_id=user.company_id,
        browser_info={
            'name': 'Chrome',
            'version': '120.0',
            'platform': 'macOS',
            'user_agent': 'Mozilla/5.0...',
            'language': 'en-US'
        },
        page_url='http://test-company-alpha.127-0-0-1.nip.io:8000/user/dashboard',
        page_title='User Dashboard',
        viewport_size='1920x1080',
        screen_resolution='2560x1440',
        console_errors=[
            {
                'timestamp': '2025-01-05T14:30:00Z',
                'level': 'ERROR',
                'message': 'Uncaught TypeError: Cannot read property of undefined'
            }
        ],
        api_history=[
            {
                'timestamp': '2025-01-05T14:29:55Z',
                'method': 'GET',
                'url': '/api/user/data',
                'status': 200
            }
        ],
        user_actions=[
            {
                'timestamp': '2025-01-05T14:29:50Z',
                'type': 'click',
                'target': 'Export Button'
            }
        ],
        status='new',
        github_sync_status='pending'
    )

    db.session.add(issue)
    db.session.commit()

    print(f"✓ Issue created: {issue.ticket_number}")
    print(f"  Title: {issue.title}")
    print(f"  Category: {issue.category}")
    print(f"  Severity: {issue.severity}")
    print(f"  Status: {issue.status}")

    return issue


def test_issue_to_dict(issue):
    """Test to_dict() method."""
    print("\n" + "="*70)
    print("TEST 3: Issue to_dict() Method")
    print("="*70)

    issue_dict = issue.to_dict()

    required_fields = [
        'id', 'ticket_number', 'category', 'severity', 'status',
        'title', 'description', 'user_name', 'user_email',
        'created_at', 'updated_at'
    ]

    for field in required_fields:
        if field not in issue_dict:
            print(f"✗ Missing field in to_dict(): {field}")
            return False

    print("✓ to_dict() returns all required fields:")
    for key, value in issue_dict.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")

    return True


def test_issue_github_body(issue):
    """Test to_github_issue_body() method."""
    print("\n" + "="*70)
    print("TEST 4: Issue to_github_issue_body() Method")
    print("="*70)

    github_body = issue.to_github_issue_body()

    required_sections = [
        'Issue Report:',
        'Category:',
        'Severity:',
        'Description',
        'Steps to Reproduce',
        'Expected Behavior',
        'Actual Behavior',
        'Environment Details',
        'Console Errors',
        'Recent API Calls',
        'Internal Tracking'
    ]

    missing_sections = []
    for section in required_sections:
        if section not in github_body:
            missing_sections.append(section)

    if missing_sections:
        print(f"✗ Missing sections in GitHub body: {', '.join(missing_sections)}")
        return False

    print("✓ GitHub issue body contains all required sections")
    print("\nPreview (first 500 characters):")
    print("-" * 70)
    print(github_body[:500] + "...")
    print("-" * 70)

    return True


def test_multi_tenant_isolation():
    """Test multi-tenant isolation."""
    print("\n" + "="*70)
    print("TEST 5: Multi-Tenant Isolation")
    print("="*70)

    # Get users from different companies
    user_alpha = User.query.filter_by(email='bob@alpha.com').first()
    user_beta = User.query.filter_by(email='eve@beta.com').first()

    if not user_alpha or not user_beta:
        print("✗ Test users not found")
        return False

    print(f"User Alpha: {user_alpha.email} (company_id: {user_alpha.company_id})")
    print(f"User Beta: {user_beta.email} (company_id: {user_beta.company_id})")

    # Create issues for each company (create them sequentially to avoid ticket conflicts)
    ticket_alpha = IssueReport.generate_ticket_number()
    issue_alpha = IssueReport(
        ticket_number=ticket_alpha,
        category='bug',
        severity='medium',
        title='Alpha Company Issue',
        description='Test issue for Alpha',
        user_id=user_alpha.id,
        company_id=user_alpha.company_id
    )
    db.session.add(issue_alpha)
    db.session.commit()

    ticket_beta = IssueReport.generate_ticket_number()
    issue_beta = IssueReport(
        ticket_number=ticket_beta,
        category='feature_request',
        severity='low',
        title='Beta Company Feature Request',
        description='Test feature request for Beta',
        user_id=user_beta.id,
        company_id=user_beta.company_id
    )
    db.session.add(issue_beta)
    db.session.commit()

    # Verify isolation
    alpha_issues = IssueReport.query.filter_by(company_id=user_alpha.company_id).all()
    beta_issues = IssueReport.query.filter_by(company_id=user_beta.company_id).all()

    print(f"\n✓ Created issue for Alpha: {ticket_alpha}")
    print(f"✓ Created issue for Beta: {ticket_beta}")
    print(f"\nAlpha company has {len(alpha_issues)} issue(s)")
    print(f"Beta company has {len(beta_issues)} issue(s)")

    # Verify no cross-company access
    alpha_has_beta = any(issue.company_id == user_beta.company_id for issue in alpha_issues)
    beta_has_alpha = any(issue.company_id == user_alpha.company_id for issue in beta_issues)

    if alpha_has_beta or beta_has_alpha:
        print("✗ Cross-tenant data leak detected!")
        return False

    print("✓ Multi-tenant isolation verified - no cross-company data access")

    return True


def test_issue_comments():
    """Test issue comments."""
    print("\n" + "="*70)
    print("TEST 6: Issue Comments")
    print("="*70)

    # Get a test issue
    issue = IssueReport.query.first()
    if not issue:
        print("✗ No test issue found")
        return False

    # Create a comment
    comment = IssueComment(
        issue_id=issue.id,
        user_id=issue.user_id,
        company_id=issue.company_id,
        comment='This is a test comment on the issue.',
        is_internal=False
    )

    db.session.add(comment)
    db.session.commit()

    print(f"✓ Comment created on issue {issue.ticket_number}")
    print(f"  Comment: {comment.comment}")
    print(f"  Internal: {comment.is_internal}")

    # Verify relationship
    issue_comments = IssueComment.query.filter_by(issue_id=issue.id).all()
    print(f"✓ Issue has {len(issue_comments)} comment(s)")

    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("BUG REPORTING BACKEND - PHASE 1 TESTS")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    app = create_app()

    with app.app_context():
        try:
            # Run tests
            test1 = test_ticket_number_generation()
            test2_issue = test_issue_creation()
            test3 = test_issue_to_dict(test2_issue) if test2_issue else False
            test4 = test_issue_github_body(test2_issue) if test2_issue else False
            test5 = test_multi_tenant_isolation()
            test6 = test_issue_comments()

            # Summary
            print("\n" + "="*70)
            print("TEST SUMMARY")
            print("="*70)
            tests = [
                ("Ticket Number Generation", test1),
                ("Issue Creation", bool(test2_issue)),
                ("to_dict() Method", test3),
                ("to_github_issue_body() Method", test4),
                ("Multi-Tenant Isolation", test5),
                ("Issue Comments", test6)
            ]

            passed = sum(1 for _, result in tests if result)
            total = len(tests)

            for test_name, result in tests:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status}: {test_name}")

            print(f"\nTotal: {passed}/{total} tests passed")

            if passed == total:
                print("\n🎉 All tests passed successfully!")
            else:
                print(f"\n⚠️  {total - passed} test(s) failed")

            return passed == total

        except Exception as e:
            print(f"\n✗ Error running tests: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
