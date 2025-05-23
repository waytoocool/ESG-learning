from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.user import User
from ..extensions import db
from ..services.email import send_password_reset_email
from ..services.redis import get_redis_client
from ..services.token import generate_password_reset_token, verify_password_reset_token, verify_registration_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def root():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        email = request.form['email']
        password = request.form['password']
        
        if not email or not password:
            message = 'Email and password are required'
            return jsonify({'success': False, 'message': message}) if is_ajax else flash(message)

        user = User.query.filter_by(email=email).first()
        print('RTTTTTT',user.password,password)
        print('************',check_password_hash(generate_password_hash(user.password,method='pbkdf2:sha256'), password))
        if user and check_password_hash(user.password, password):
            login_user(user)
            redirect_url = url_for('user.dashboard' if user.role == 'User' else 'admin.home')
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': redirect_url
                })
            return redirect(redirect_url)
        else:
            print('User Is: ',User.query.all())
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
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_password_reset_token(user.email)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            send_password_reset_email(user.email, reset_link)
            flash('Password reset instructions have been sent to your email.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('No user found with that email address.', 'danger')
    return render_template('forgot_password.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_password_reset_token(token)
    if email is None:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        user.set_password(password)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

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
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register_user.html', user=user, token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_user.html', user=user, token=token)

        try:
            user.username = username
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
