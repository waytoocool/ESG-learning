from flask import Blueprint
from .auth import auth_bp
from .admin import admin_bp
from .user import user_bp
from .superadmin import superadmin_bp


# Register routes with blueprints
blueprints = [auth_bp, admin_bp, user_bp, superadmin_bp]