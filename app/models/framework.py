from ..extensions import db
import uuid
import re
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property


class Framework(db.Model):
    """Framework model for ESG reporting frameworks."""
    
    __tablename__ = 'frameworks'
    
    framework_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    framework_name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    data_fields = db.relationship('FrameworkDataField', back_populates='framework', cascade='all, delete-orphan')
    data_points = db.relationship('DataPoint', back_populates='framework', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Framework {self.framework_name}>'


class FrameworkDataField(db.Model):
    """DataField model associated with ESG reporting frameworks.
    
    This model represents both raw and computed fields within a framework.
    Computed fields can reference raw fields from any framework through variable mappings.
    
    Attributes:
        field_id (str): Unique identifier for the field
        framework_id (str): ID of the framework this field belongs to
        field_name (str): Name of the field
        description (str): Optional description of the field
        is_computed (bool): Whether this is a computed field
        formula_expression (str): For computed fields, the formula using variables (e.g., "A + B")
        constant_multiplier (float): Global multiplier applied to the entire formula result
    """
    
    __tablename__ = 'framework_data_fields'
    
    field_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    framework_id = db.Column(db.String(36), db.ForeignKey('frameworks.framework_id'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_computed = db.Column(db.Boolean, default=False)
    formula_expression = db.Column(db.Text)  # Stores "(A + B)" - pure formula with variables
    constant_multiplier = db.Column(db.Float, default=1.0)  # For constants that apply to entire formula
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    framework = db.relationship('Framework', back_populates='data_fields')
    variable_mappings = db.relationship('FieldVariableMapping', 
                                      back_populates='computed_field',
                                      foreign_keys='[FieldVariableMapping.computed_field_id]',
                                      cascade='all, delete-orphan')
    esg_data = db.relationship('ESGData', back_populates='field', cascade='all, delete-orphan')

    @validates('formula_expression')
    def validate_formula(self, key, formula):
        """Validate formula expression contains only valid characters and structure."""
        if formula and self.is_computed:
            # Check for valid characters: A-Z, +, -, *, /, (, ), and whitespace
            if not re.match(r'^[A-Z\+\-\*\/\(\)\s]*$', formula):
                raise ValueError("Formula can only contain variables (A-Z), operators (+,-,*,/), and parentheses")
            
            # Check for balanced parentheses
            if formula.count('(') != formula.count(')'):
                raise ValueError("Formula has unbalanced parentheses")
        return formula

    @validates('constant_multiplier')
    def validate_multiplier(self, key, value):
        """Ensure multiplier is non-zero."""
        if value == 0:
            raise ValueError("Constant multiplier cannot be zero")
        return value

    def get_dependencies(self):
        """Get all fields this computed field depends on."""
        if not self.is_computed:
            return []
        return [mapping.raw_field for mapping in self.variable_mappings]

    def check_circular_dependency(self, visited=None):
        """Check for circular dependencies in computed fields.
        
        Args:
            visited (set): Set of visited field IDs to detect cycles
            
        Returns:
            bool: True if circular dependency found
        """
        if visited is None:
            visited = set()
            
        if self.field_id in visited:
            return True
            
        if not self.is_computed:
            return False
            
        visited.add(self.field_id)
        
        for mapping in self.variable_mappings:
            if mapping.raw_field.check_circular_dependency(visited):
                return True
                
        visited.remove(self.field_id)
        return False

    def __repr__(self):
        return f'<FrameworkDataField {self.field_name}>'


class FieldVariableMapping(db.Model):
    """Maps variables in formulas to actual fields from any framework.
    
    This model creates the relationship between variables in computed field formulas
    and the actual fields they represent. Each variable can have a coefficient.
    
    Attributes:
        mapping_id (str): Unique identifier for the mapping
        computed_field_id (str): ID of the computed field using this variable
        raw_field_id (str): ID of the field this variable represents
        variable_name (str): Single letter (A-Z) used in the formula
        coefficient (float): Multiplier for this variable's value
    """
    
    __tablename__ = 'field_variable_mappings'
    
    mapping_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    computed_field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    raw_field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    variable_name = db.Column(db.String(1), nullable=False)  # Stores the variable (A, B, C, etc.)
    coefficient = db.Column(db.Float, default=1.0)  # Stores the multiplier for each variable (3, 2.5, etc.)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    computed_field = db.relationship('FrameworkDataField', 
                                   foreign_keys=[computed_field_id],
                                   back_populates='variable_mappings')
    raw_field = db.relationship('FrameworkDataField',
                              foreign_keys=[raw_field_id])

    @validates('variable_name')
    def validate_variable(self, key, name):
        """Ensure variable name is a single uppercase letter."""
        if not re.match(r'^[A-Z]$', name):
            raise ValueError("Variable name must be a single uppercase letter (A-Z)")
        return name

    @validates('coefficient')
    def validate_coefficient(self, key, value):
        """Ensure coefficient is non-zero."""
        if value == 0:
            raise ValueError("Coefficient cannot be zero")
        return value

    def __repr__(self):
        return f'<FieldVariableMapping {self.coefficient}*{self.variable_name}={self.raw_field_id}>'
