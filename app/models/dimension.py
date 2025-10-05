from ..extensions import db
import uuid
from sqlalchemy.orm import validates
from .mixins import TenantScopedQueryMixin, TenantScopedModelMixin


class Dimension(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Dimension model for categorizing ESG data breakdowns.
    
    Dimensions represent categories for data breakdowns like Gender, Age, Department, etc.
    Each dimension can have multiple values (e.g., Gender: Male, Female, Other).
    
    Attributes:
        dimension_id (str): Unique identifier for the dimension
        name (str): Name of the dimension (e.g., "Gender", "Age Group")
        description (str): Description of what this dimension represents
        company_id (int): Company this dimension belongs to (tenant isolation)
        is_system_default (bool): Whether this is a system-provided dimension
        created_at (datetime): When the dimension was created
        updated_at (datetime): When the dimension was last updated
    """
    
    __tablename__ = 'dimensions'
    
    dimension_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    is_system_default = db.Column(db.Boolean, default=False)  # For predefined dimensions like Gender, Age
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    company = db.relationship('Company', backref='dimensions')
    dimension_values = db.relationship('DimensionValue', back_populates='dimension', cascade='all, delete-orphan')
    field_dimensions = db.relationship('FieldDimension', back_populates='dimension', cascade='all, delete-orphan')
    
    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('name', 'company_id', name='uq_dimension_name_company'),
        db.Index('idx_dimension_company', 'company_id'),
    )

    def __init__(self, name, company_id, description=None, is_system_default=False):
        self.name = name
        self.company_id = company_id
        self.description = description
        self.is_system_default = is_system_default

    @validates('name')
    def validate_name(self, key, name):
        """Validate dimension name."""
        if not name or not name.strip():
            raise ValueError("Dimension name cannot be empty")
        return name.strip()

    def get_ordered_values(self):
        """Get dimension values ordered by display_order."""
        return sorted(self.dimension_values, key=lambda v: v.display_order)

    def __repr__(self):
        return f'<Dimension {self.name} ({len(self.dimension_values)} values)>'


class DimensionValue(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """DimensionValue model for specific values within a dimension.
    
    Each dimension can have multiple values. For example:
    - Gender dimension: Male, Female, Other
    - Age Group dimension: <30, 30-50, >50
    - Department dimension: IT, Finance, HR
    
    Attributes:
        value_id (str): Unique identifier for the dimension value
        dimension_id (str): ID of the parent dimension
        value (str): The actual value (e.g., "Male", "<30", "IT")
        display_name (str): User-friendly display name
        display_order (int): Order for display purposes
        company_id (int): Company this value belongs to (tenant isolation)
        is_active (bool): Whether this value is currently active
        created_at (datetime): When the value was created
    """
    
    __tablename__ = 'dimension_values'
    
    value_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dimension_id = db.Column(db.String(36), db.ForeignKey('dimensions.dimension_id'), nullable=False)
    value = db.Column(db.String(100), nullable=False)  # The actual value
    display_name = db.Column(db.String(100), nullable=True)  # User-friendly name
    display_order = db.Column(db.Integer, default=0)  # For ordering in UI
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    dimension = db.relationship('Dimension', back_populates='dimension_values')
    company = db.relationship('Company', backref='dimension_values')
    
    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('dimension_id', 'value', name='uq_dimension_value'),
        db.Index('idx_dimension_value_dimension', 'dimension_id'),
        db.Index('idx_dimension_value_company', 'company_id'),
    )

    def __init__(self, dimension_id, value, company_id, display_name=None, display_order=0):
        self.dimension_id = dimension_id
        self.value = value
        self.company_id = company_id
        self.display_name = display_name or value
        self.display_order = display_order

    @validates('value')
    def validate_value(self, key, value):
        """Validate dimension value."""
        if not value or not value.strip():
            raise ValueError("Dimension value cannot be empty")
        return value.strip()

    @property
    def effective_display_name(self):
        """Get the effective display name (display_name or value if none set)."""
        return self.display_name or self.value

    def __repr__(self):
        return f'<DimensionValue {self.dimension.name}: {self.value}>'


class FieldDimension(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Junction table linking framework fields to their applicable dimensions.
    
    This model defines which dimensions are applicable to which fields.
    For example, an "Employee Count" field might have Gender and Age dimensions.
    
    Attributes:
        field_dimension_id (str): Unique identifier for the relationship
        field_id (str): ID of the framework field
        dimension_id (str): ID of the dimension
        company_id (int): Company this relationship belongs to (tenant isolation)
        is_required (bool): Whether this dimension is required for data entry
        created_at (datetime): When the relationship was created
    """
    
    __tablename__ = 'field_dimensions'
    
    field_dimension_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    dimension_id = db.Column(db.String(36), db.ForeignKey('dimensions.dimension_id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    is_required = db.Column(db.Boolean, default=True)  # Whether dimension is required for data entry
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    field = db.relationship('FrameworkDataField', backref='field_dimensions')
    dimension = db.relationship('Dimension', back_populates='field_dimensions')
    company = db.relationship('Company', backref='field_dimensions')
    
    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('field_id', 'dimension_id', name='uq_field_dimension'),
        db.Index('idx_field_dimension_field', 'field_id'),
        db.Index('idx_field_dimension_dimension', 'dimension_id'),
        db.Index('idx_field_dimension_company', 'company_id'),
    )

    def __init__(self, field_id, dimension_id, company_id, is_required=True):
        self.field_id = field_id
        self.dimension_id = dimension_id
        self.company_id = company_id
        self.is_required = is_required

    def __repr__(self):
        return f'<FieldDimension {self.field.field_name} -> {self.dimension.name}>' 