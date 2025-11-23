from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.user import User
from ..extensions import db
from ..services.email import send_password_reset_email
from ..services.redis import get_redis_client
from ..services.token import generate_password_reset_token, verify_password_reset_token, verify_registration_token
import redis

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def root():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        email = request.form['email'].lower().strip() if request.form['email'] else ''
        password = request.form['password']
        
        if not email or not password:
            message = 'Email and password are required'
            return jsonify({'success': False, 'message': message}) if is_ajax else flash(message)

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            # Determine redirect URL based on user role
            if user.role == 'SUPER_ADMIN':
                redirect_url = url_for('superadmin.dashboard')
            elif user.role == 'ADMIN':
                redirect_url = url_for('admin.home')
            elif user.role == 'USER':
                redirect_url = url_for('user_v2.dashboard')  # Redirect to new dashboard
            else:
                # Fallback for unknown roles
                redirect_url = url_for('auth.login')
                
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': redirect_url
                })
            return redirect(redirect_url)
        else:
            message = 'Invalid email or password'
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': message
                })
            flash(message)
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Clear any impersonation flags from session
    session.pop('impersonating', None)
    session.pop('original_user_id', None)
    session.pop('impersonated_user_id', None)

    # Logout the user
    logout_user()

    # Clear the entire session to ensure clean state
    session.clear()

    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower().strip() if request.form['email'] else ''
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_password_reset_token(user.id)
            send_password_reset_email(email, token)
            flash('Password reset email sent. Please check your inbox.', 'info')
        else:
            flash('Email address not found.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_password_reset_token(token)
    if user_id is None:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if user is None:
        flash('Invalid user.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        try:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Password reset successful. Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while resetting password.', 'danger')
            return render_template('reset_password.html', token=token)

    return render_template('reset_password.html', token=token)

@auth_bp.route('/register/<token>', methods=['GET', 'POST'])
def register_user(token):
    user_id = verify_registration_token(token)
    if user_id is None:
        flash('Invalid or expired registration token.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if user is None:
        flash('Invalid user.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register_user.html', user=user, token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_user.html', user=user, token=token)

        try:
            user.name = name
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            user.is_email_verified = True
            db.session.commit()

            session['registration_success'] = True
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'danger')
            return render_template('register_user.html', user=user, token=token)

    return render_template('register_user.html', user=user, token=token)

@auth_bp.route('/health/redis', methods=['GET'])
def redis_health_check():
    """
    Health check route to verify Redis connectivity.
    """
    redis_client = get_redis_client()
    if not redis_client:
        return jsonify({'status': 'unhealthy', 'message': 'Redis client not initialized'}), 503

    try:
        redis_client.ping()
        return jsonify({'status': 'healthy'})
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy'}), 503    
