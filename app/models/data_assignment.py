from ..extensions import db
import uuid
from datetime import datetime, UTC
from sqlalchemy import Enum

class DataPointAssignment(db.Model):
    """Data Point Assignment model with FY and frequency configuration."""
    
    __tablename__ = 'data_point_assignments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_point_id = db.Column(db.String(36), db.ForeignKey('data_point.id'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    
    # Financial Year Configuration
    fy_start_month = db.Column(db.Integer, nullable=False, default=4)  # April = 4, January = 1
    fy_start_year = db.Column(db.Integer, nullable=False)  # e.g., 2024
    fy_end_year = db.Column(db.Integer, nullable=False)    # e.g., 2025
    
    # Data Collection Frequency
    frequency = db.Column(Enum('Monthly', 'Quarterly', 'Annual', name='frequency_type'), 
                         nullable=False, default='Annual')
    
    # Metadata
    assigned_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    data_point = db.relationship('DataPoint', backref='assignments')
    entity = db.relationship('Entity', backref='data_assignments')
    assigned_by_user = db.relationship('User', backref='assigned_data_points')
    
    # Add indexes for better query performance
    __table_args__ = (
        db.Index('idx_assignment_data_entity', 'data_point_id', 'entity_id'),
        db.Index('idx_assignment_fy', 'fy_start_year', 'fy_end_year'),
    )

    def __init__(self, data_point_id, entity_id, fy_start_month, fy_start_year, fy_end_year, 
                 frequency, assigned_by):
        self.data_point_id = data_point_id
        self.entity_id = entity_id
        self.fy_start_month = fy_start_month
        self.fy_start_year = fy_start_year
        self.fy_end_year = fy_end_year
        self.frequency = frequency
        self.assigned_by = assigned_by

    def get_valid_reporting_dates(self):
        """Generate list of valid reporting dates based on frequency and FY."""
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        valid_dates = []
        
        # Calculate FY start and end dates
        fy_start = date(self.fy_start_year, self.fy_start_month, 1)
        fy_end = date(self.fy_end_year, self.fy_start_month, 1) - timedelta(days=1)
        
        if self.frequency == 'Annual':
            # Only FY end date
            valid_dates.append(fy_end)
            
        elif self.frequency == 'Quarterly':
            # Generate quarterly dates
            current_date = fy_start
            while current_date <= fy_end:
                # Last day of quarter
                quarter_end = (current_date + relativedelta(months=3)) - timedelta(days=1)
                if quarter_end <= fy_end:
                    valid_dates.append(quarter_end)
                current_date = current_date + relativedelta(months=3)
                    
        elif self.frequency == 'Monthly':
            # Generate monthly dates
            current_date = fy_start
            while current_date <= fy_end:
                # Last day of month
                month_end = (current_date + relativedelta(months=1)) - timedelta(days=1)
                if month_end <= fy_end:
                    valid_dates.append(month_end)
                current_date = current_date + relativedelta(months=1)
        
        return valid_dates
    
    def is_valid_reporting_date(self, reporting_date):
        """Check if a given date is valid for this assignment."""
        valid_dates = self.get_valid_reporting_dates()
        return reporting_date in valid_dates
    
    def get_fy_display(self):
        """Get human-readable FY display."""
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{month_names[self.fy_start_month]} {self.fy_start_year} - {month_names[self.fy_start_month]} {self.fy_end_year}"

    def __repr__(self):
        return f'<DataPointAssignment {self.data_point_id}:{self.entity_id}>' 