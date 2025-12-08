from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, login_manager
from sqlalchemy import event
from sqlalchemy.orm import validates

class User(db.Model, UserMixin):
    """User model for authentication and authorization."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    role = db.Column(db.Enum('SUPER_ADMIN', 'ADMIN', 'USER', name='user_role'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=True)
    # company_id is nullable to support SUPER_ADMIN users who operate across all companies
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)

    # Phase 0: Feature toggle for new data entry interface
    use_new_data_entry = db.Column(db.Boolean, default=False)

    # Relationships
    company = db.relationship('Company', backref='users')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

    @validates('email')
    def validate_email(self, key, email):
        """Ensure email is always stored in lowercase."""
        if email:
            return email.lower().strip()
        return email

    def set_password(self, password):
        """Set hashed password."""
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password, password)

    def get_id(self):
        """Required for Flask-Login."""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Required for Flask-Login."""
        return True

    @property
    def is_anonymous(self):
        """Required for Flask-Login."""
        return False
    
    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == 'SUPER_ADMIN'
    
    def is_admin(self):
        """Check if user is an admin (company-level)."""
        return self.role == 'ADMIN'
    
    def is_user(self):
        """Check if user is a regular user."""
        return self.role == 'USER'

    def __repr__(self):
        return f'<User {self.email}>'


# Set up the user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------------------------------------------------
# SQLAlchemy event listeners
# -------------------------------------------------------------------------
# Ensure the "role" column is always stored in upper-case so that it matches
# the Enum declaration (SUPER_ADMIN, ADMIN, USER) and we never again get a
# LookupError caused by e.g. "User" or "Admin".

@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def _normalize_role(mapper, connection, target):  # pylint: disable=unused-argument
    if target.role:
        target.role = target.role.upper()

@event.listens_for(User, "before_insert")
def _validate_super_admin_uniqueness(mapper, connection, target):  # pylint: disable=unused-argument
    """Ensure only one SUPER_ADMIN user exists in the system."""
    if target.role and target.role.upper() == 'SUPER_ADMIN':
        # Check if there's already a SUPER_ADMIN user
        existing_super_admin = connection.execute(
            db.text('SELECT COUNT(*) FROM "user" WHERE role = :role'),
            {"role": "SUPER_ADMIN"}
        ).scalar()
        
        if existing_super_admin > 0:
            raise ValueError(
                "Cannot create multiple SUPER_ADMIN users. "
                "Only one SUPER_ADMIN user is allowed in the system. "
                "If you need to change the SUPER_ADMIN, please contact system administrator."
            )

@event.listens_for(User, "before_update")
def _validate_super_admin_role_change(mapper, connection, target):  # pylint: disable=unused-argument
    """Prevent changing existing users to SUPER_ADMIN if one already exists."""
    if target.role and target.role.upper() == 'SUPER_ADMIN':
        # Get the current role of this user
        current_role = connection.execute(
            db.text('SELECT role FROM "user" WHERE id = :user_id'),
            {"user_id": target.id}
        ).scalar()
        
        # If this user is not currently a SUPER_ADMIN, check if another one exists
        if current_role != 'SUPER_ADMIN':
            existing_super_admin = connection.execute(
                db.text('SELECT COUNT(*) FROM "user" WHERE role = :role'),
                {"role": "SUPER_ADMIN"}
            ).scalar()
            
            if existing_super_admin > 0:
                raise ValueError(
                    "Cannot change user role to SUPER_ADMIN. "
                    "Only one SUPER_ADMIN user is allowed in the system. "
                    "If you need to change the SUPER_ADMIN, please contact system administrator."
                )

@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def _normalize_email(mapper, connection, target):  # pylint: disable=unused-argument
    """Ensure email is always stored in lowercase for consistency."""
    if target.email:
        target.email = target.email.lower().strip()