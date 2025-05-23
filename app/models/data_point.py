from ..extensions import db
import uuid

# Association table for entity-data point relationship
entity_data_point = db.Table('entity_data_point',
    db.Column('entity_id', db.Integer, db.ForeignKey('entity.id'), primary_key=True),
    db.Column('data_point_id', db.String(36), db.ForeignKey('data_point.id'), primary_key=True)
)

class DataPoint(db.Model):
    """Data Point model for ESG metrics."""
    
    __tablename__ = 'data_point'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    value_type = db.Column(db.String(10), nullable=False)
    unit = db.Column(db.String(10), nullable=True)
    framework_id = db.Column(db.String(36), db.ForeignKey('frameworks.framework_id'), nullable=False)
    
    # Updated relationships
    framework = db.relationship('Framework', back_populates='data_points')
    esg_data = db.relationship('ESGData', back_populates='data_point')

    def __init__(self, name, value_type, framework_id, unit=None):
        self.name = name
        self.value_type = value_type
        self.framework_id = framework_id
        self.unit = unit

    def __repr__(self):
        return f'<DataPoint {self.name}>'
