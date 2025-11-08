"""
Script to create database tables for issue reporting system.
"""
from app import create_app
from app.extensions import db
from app.models import IssueReport, IssueComment

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        print("Created tables:")
        print("  - issue_reports")
        print("  - issue_comments")
