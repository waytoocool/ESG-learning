from ..extensions import db
from .mixins import TenantScopedQueryMixin, TenantScopedModelMixin

class Entity(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Entity model for organizational hierarchy."""
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uq_entity_company_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    # The name must be unique ONLY within the scope of a single company, not globally.
    name = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(20), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=True)
    # Add company_id for tenant isolation - temporarily nullable until T-3 seed data
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Relationships
    parent = db.relationship('Entity', 
                           backref=db.backref('children', lazy='dynamic'),
                           remote_side=[id])
    users = db.relationship('User', backref='entity')
    esg_data = db.relationship('ESGData', 
                              back_populates='entity',
                              cascade='all, delete-orphan')
    company = db.relationship('Company', backref='entities')

    def __init__(self, name, entity_type, company_id=None, parent_id=None):
        self.name = name
        self.entity_type = entity_type
        self.company_id = company_id
        self.parent_id = parent_id

    def get_hierarchy_level(self):
        """Calculate the level of this entity in the hierarchy."""
        level = 1
        current = self
        while current.parent_id is not None:
            level += 1
            current = current.parent
        return level

    def __repr__(self):
        return f'<Entity {self.name}>'