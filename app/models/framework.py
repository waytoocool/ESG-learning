from ..extensions import db
import uuid
import re
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property


def generate_slug(field_name):
    """Generate a slug from field name for field_code."""
    if not field_name:
        return ""
    # Convert to lowercase, replace spaces and special chars with underscores
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', field_name.lower())
    slug = re.sub(r'[\s-]+', '_', slug).strip('_')
    return slug


class Framework(db.Model):
    """Framework model for ESG reporting frameworks."""
    
    __tablename__ = 'frameworks'
    
    framework_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    framework_name = db.Column(db.String(255), nullable=False)  # Removed unique=True for tenant scoping
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)  # CRITICAL FIX: Add company_id
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    data_fields = db.relationship('FrameworkDataField', back_populates='framework', cascade='all, delete-orphan')
    topics = db.relationship('Topic', back_populates='framework', cascade='all, delete-orphan')
    company = db.relationship('Company', backref='frameworks')
    
    # Add unique constraint within company
    __table_args__ = (
        db.UniqueConstraint('framework_name', 'company_id', name='uq_framework_name_company'),
        db.Index('idx_framework_company', 'company_id'),
    )

    def __repr__(self):
        return f'<Framework {self.framework_name}>'


class Topic(db.Model):
    """Topic model for organizing framework fields into categories.
    
    Supports hierarchical organization with parent-child relationships.
    Can be framework-specific or company-specific for custom categories.
    """
    
    __tablename__ = 'topics'
    
    topic_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.String(36), db.ForeignKey('topics.topic_id'), nullable=True)
    framework_id = db.Column(db.String(36), db.ForeignKey('frameworks.framework_id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # For custom company topics
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    framework = db.relationship('Framework', back_populates='topics')
    company = db.relationship('Company', backref='custom_topics')
    parent = db.relationship('Topic', remote_side=[topic_id], backref='children')
    data_fields = db.relationship('FrameworkDataField', back_populates='topic')
    
    # Table args for indexes
    __table_args__ = (
        db.Index('idx_topic_framework', 'framework_id'),
        db.Index('idx_topic_company', 'company_id'),
        db.Index('idx_topic_parent', 'parent_id'),
    )

    def __init__(self, name, framework_id=None, parent_id=None, company_id=None, description=None):
        self.name = name
        self.framework_id = framework_id
        self.parent_id = parent_id
        self.company_id = company_id
        self.description = description

    def get_full_path(self):
        """Get the full hierarchical path of this topic."""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " > ".join(path)

    def get_all_descendants(self):
        """Get all descendant topics recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_root_topic(self):
        """Get the root topic of this hierarchy."""
        current = self
        while current.parent:
            current = current.parent
        return current

    @property
    def is_custom_topic(self):
        """Check if this is a company-specific custom topic."""
        return self.company_id is not None

    @property
    def level(self):
        """Get the hierarchical level (0 for root, 1 for children, etc.)."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level

    def __repr__(self):
        return f'<Topic {self.name} (Level {self.level})>'


class FrameworkDataField(db.Model):
    """DataField model associated with ESG reporting frameworks.
    
    This model represents both raw and computed fields within a framework.
    Computed fields can reference raw fields from any framework through variable mappings.
    
    Attributes:
        field_id (str): Unique identifier for the field
        framework_id (str): ID of the framework this field belongs to
        field_name (str): Name of the field
        field_code (str): Business key - unique code across all frameworks
        description (str): Optional description of the field
        unit_category (str): Category for units (energy, money, emission, etc.)
        default_unit (str): Default unit for this field (kWh, USD, etc.)
        value_type (str): Type of value (NUMBER, BOOLEAN, TEXT, DATE)
        is_computed (bool): Whether this is a computed field
        formula_expression (str): For computed fields, the formula using variables (e.g., "A + B")
        constant_multiplier (float): Global multiplier applied to the entire formula result
    """
    
    __tablename__ = 'framework_data_fields'
    
    field_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    framework_id = db.Column(db.String(36), db.ForeignKey('frameworks.framework_id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)  # CRITICAL FIX: Add company_id
    field_name = db.Column(db.String(255), nullable=False)
    
    # Phase 1 new columns
    field_code = db.Column(db.String(64), nullable=False)  # Will add unique constraint in migration
    unit_category = db.Column(db.String(30))  # energy, money, emission, weight, volume, etc.
    default_unit = db.Column(db.String(20))   # kWh, USD, etc.
    value_type = db.Column(
        db.Enum('NUMBER', 'BOOLEAN', 'TEXT', 'DATE', name='value_type_enum'),
        nullable=False,
        default='NUMBER'
    )
    
    # Phase 2: Add topic relationship
    topic_id = db.Column(db.String(36), db.ForeignKey('topics.topic_id'), nullable=True)
    
    description = db.Column(db.Text)
    is_computed = db.Column(db.Boolean, default=False)
    formula_expression = db.Column(db.Text)  # Stores "(A + B)" - pure formula with variables
    constant_multiplier = db.Column(db.Float, default=1.0)  # For constants that apply to entire formula
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    framework = db.relationship('Framework', back_populates='data_fields')
    topic = db.relationship('Topic', back_populates='data_fields')
    company = db.relationship('Company', backref='framework_fields')
    variable_mappings = db.relationship('FieldVariableMapping', 
                                      back_populates='computed_field',
                                      foreign_keys='[FieldVariableMapping.computed_field_id]',
                                      cascade='all, delete-orphan')
    esg_data = db.relationship('ESGData', back_populates='field', cascade='all, delete-orphan')

    # Table args for indexes and constraints
    __table_args__ = (
        db.Index('idx_field_code', 'field_code'),
        db.Index('idx_framework_field_code', 'framework_id', 'field_code'),
        db.Index('idx_field_topic', 'topic_id'),
        db.Index('idx_field_company', 'company_id'),
        db.UniqueConstraint('field_code', 'company_id', name='uq_field_code_company'),
    )

    def __init__(self, **kwargs):
        # Auto-generate field_code if not provided
        if 'field_code' not in kwargs and 'field_name' in kwargs:
            kwargs['field_code'] = generate_slug(kwargs['field_name'])
        super().__init__(**kwargs)

    @validates('field_code')
    def validate_field_code(self, key, field_code):
        """Validate and ensure field_code uniqueness."""
        if not field_code:
            if hasattr(self, 'field_name') and self.field_name:
                field_code = generate_slug(self.field_name)
            else:
                raise ValueError("Field code cannot be empty")
        
        # Check for uniqueness within company scope
        from flask_login import current_user
        company_id = getattr(self, 'company_id', None) or (current_user.company_id if hasattr(current_user, 'company_id') else None)
        
        if company_id:
            existing = FrameworkDataField.query.filter(
                FrameworkDataField.field_code == field_code,
                FrameworkDataField.company_id == company_id,
                FrameworkDataField.field_id != self.field_id
            ).first()
            
            if existing:
                raise ValueError(f"Field code '{field_code}' already exists in your organization")
        
        return field_code

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

    def get_dependants(self):
        """Get all computed fields that depend on this field (Phase 3 dependency tracking)."""
        from . import FieldVariableMapping
        dependant_mappings = FieldVariableMapping.query.filter_by(raw_field_id=self.field_id).all()
        return [mapping.computed_field for mapping in dependant_mappings]

    def has_dependants(self):
        """Check if this field has any dependants (Phase 3)."""
        return len(self.get_dependants()) > 0

    def get_all_dependencies(self, visited=None):
        """
        Get all raw field dependencies recursively.
        Returns flat list of all dependency field objects.

        Args:
            visited (set): Set of visited field IDs to prevent circular dependencies

        Returns:
            list: List of FrameworkDataField objects that this field depends on
        """
        if not self.is_computed:
            return []

        if visited is None:
            visited = set()

        if self.field_id in visited:
            return []  # Circular dependency protection

        visited.add(self.field_id)
        dependencies = []

        for mapping in self.variable_mappings:
            raw_field = mapping.raw_field
            dependencies.append(raw_field)

            # Recursively get dependencies if raw field is also computed
            if raw_field.is_computed:
                dependencies.extend(raw_field.get_all_dependencies(visited))

        return dependencies

    def get_dependency_tree(self):
        """
        Get hierarchical dependency structure.
        Returns nested dictionary representing dependency tree.

        Returns:
            dict: Nested structure with field info and dependencies
        """
        if not self.is_computed:
            return None

        tree = {
            'field_id': self.field_id,
            'field_name': self.field_name,
            'is_computed': True,
            'formula': self.formula_expression,
            'dependencies': []
        }

        for mapping in self.variable_mappings:
            dep_info = {
                'variable': mapping.variable_name,
                'coefficient': mapping.coefficient,
                'field_id': mapping.raw_field_id,
                'field_name': mapping.raw_field.field_name,
                'is_computed': mapping.raw_field.is_computed
            }

            if mapping.raw_field.is_computed:
                dep_info['dependencies'] = mapping.raw_field.get_dependency_tree()

            tree['dependencies'].append(dep_info)

        return tree

    def validate_frequency_compatibility(self, proposed_frequency):
        """
        Check if proposed frequency is compatible with all dependencies.
        Returns (is_valid, incompatible_fields).

        Args:
            proposed_frequency (str): Frequency to validate (Annual, Quarterly, Monthly)

        Returns:
            tuple: (bool is_valid, list incompatible_fields)
        """
        if not self.is_computed:
            return (True, [])

        freq_hierarchy = {
            'Annual': 1,
            'Quarterly': 2,
            'Monthly': 3
        }

        proposed_level = freq_hierarchy.get(proposed_frequency, 1)
        incompatible = []

        for dep in self.get_all_dependencies():
            # Check if dependency has existing assignment
            from ..models.data_assignment import DataPointAssignment
            assignments = DataPointAssignment.query.filter_by(
                field_id=dep.field_id,
                series_status='active'
            ).all()

            for assignment in assignments:
                dep_level = freq_hierarchy.get(assignment.frequency, 3)
                if dep_level < proposed_level:
                    incompatible.append({
                        'field': dep.field_name,
                        'current_frequency': assignment.frequency,
                        'required_frequency': proposed_frequency
                    })

        return (len(incompatible) == 0, incompatible)

    def get_fields_depending_on_this(self):
        """
        Get all computed fields that depend on this field.
        Returns list of computed fields using this as dependency.

        Returns:
            list: List of FrameworkDataField objects that depend on this field
        """
        from . import FieldVariableMapping

        dependent_mappings = FieldVariableMapping.query.filter_by(
            raw_field_id=self.field_id
        ).all()

        dependent_fields = []
        for mapping in dependent_mappings:
            if mapping.computed_field and mapping.computed_field.is_computed:
                dependent_fields.append(mapping.computed_field)

        return dependent_fields

    def can_be_removed(self):
        """
        Check if this field can be safely removed from assignments.
        Returns (can_remove, blocking_computed_fields).

        Returns:
            tuple: (bool can_remove, list blocking_fields)
        """
        dependents = self.get_fields_depending_on_this()

        # Check if any dependent computed fields are assigned
        from ..models.data_assignment import DataPointAssignment
        blocking_fields = []

        for computed_field in dependents:
            assignments = DataPointAssignment.query.filter_by(
                field_id=computed_field.field_id,
                series_status='active'
            ).count()

            if assignments > 0:
                blocking_fields.append({
                    'field_id': computed_field.field_id,
                    'field_name': computed_field.field_name,
                    'assignment_count': assignments
                })

        return (len(blocking_fields) == 0, blocking_fields)

    def __repr__(self):
        return f'<FrameworkDataField {self.field_name} ({self.field_code})>'


class FieldVariableMapping(db.Model):
    """Maps variables in formulas to actual fields from any framework.
    
    This model creates the relationship between variables in computed field formulas
    and the actual fields they represent. Each variable can have a coefficient.
    
    Phase 2.5: Enhanced with dimension filtering support for complex aggregations.
    
    Attributes:
        mapping_id (str): Unique identifier for the mapping
        computed_field_id (str): ID of the computed field using this variable
        raw_field_id (str): ID of the field this variable represents
        variable_name (str): Single letter (A-Z) used in the formula
        coefficient (float): Multiplier for this variable's value
        dimension_filter (dict): JSON filter for specific dimensions {"gender": "Male", "age": "<30"}
        aggregation_type (str): How to handle dimensions - SUM_ALL_DIMENSIONS or SPECIFIC_DIMENSION
    """
    
    __tablename__ = 'field_variable_mappings'
    
    mapping_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    computed_field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    raw_field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    variable_name = db.Column(db.String(1), nullable=False)  # Stores the variable (A, B, C, etc.)
    coefficient = db.Column(db.Float, default=1.0)  # Stores the multiplier for each variable (3, 2.5, etc.)
    
    # Phase 2.5: Dimension support
    dimension_filter = db.Column(db.JSON)  # {"gender": "Male", "age": "<30"}
    aggregation_type = db.Column(
        db.Enum('SUM_ALL_DIMENSIONS', 'SPECIFIC_DIMENSION', name='aggregation_type_enum'),
        default='SUM_ALL_DIMENSIONS'
    )
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships - Phase 3: Enhanced dependency tracking
    computed_field = db.relationship('FrameworkDataField', 
                                   foreign_keys=[computed_field_id],
                                   back_populates='variable_mappings')
    raw_field = db.relationship('FrameworkDataField',
                              foreign_keys=[raw_field_id])

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('computed_field_id', 'variable_name', name='uq_computed_variable'),
        db.Index('idx_mapping_computed', 'computed_field_id'),
        db.Index('idx_mapping_raw', 'raw_field_id'),
    )

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
