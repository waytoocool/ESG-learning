# services/__init__.py

# This makes the services package importable and can also contain shared functionality
from .email import send_registration_email
from .token import generate_registration_token, verify_registration_token
from .redis import init_redis, check_rate_limit

# This allows other parts of the application to import services directly from the services package
__all__ = [
    'send_registration_email',
    'generate_registration_token',
    'verify_registration_token',
    'init_redis',
    'check_rate_limit'
]
