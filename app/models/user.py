from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, login_manager

class User(db.Model, UserMixin):
    """User model for authentication and authorization."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    role = db.Column(db.Enum('SUPER_ADMIN', 'ADMIN', 'USER', name='user_role'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=True)
    # company_id is nullable to support SUPER_ADMIN users who operate across all companies
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)

    # Relationships
    company = db.relationship('Company', backref='users')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

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