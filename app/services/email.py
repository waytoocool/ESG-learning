# services/email.py
from flask import current_app, url_for
from flask_mail import Message
from ..extensions import mail

def send_registration_email(email, token):
    """
    Send registration email to user with verification link
    
    Args:
        email (str): Recipient email address
        token (str): Registration token for verification
    """
    try:
        registration_link = url_for('auth.register_user', token=token, _external=True)
        
        msg = Message(
            "Complete Your Registration",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""
            Welcome to our ESG Data Platform!
            
            Please click the following link to complete your registration:
            {registration_link}
            
            This link will expire in 24 hours.
            
            If you did not request this registration, please ignore this email.
        """
        
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        current_app.logger.error(f"Failed to send registration email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"

def send_password_reset_email(email, reset_link):
    """
    Send password reset email to user
    
    Args:
        email (str): Recipient email address
        reset_link (str): URL link to reset password
    """
    try:

        msg = Message(
            "Password Reset Request",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""
            You have requested to reset your password.
            
            Please click the following link to reset your password:
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you did not request this reset, please ignore this email.
        """
        
        mail.send(msg)
        return True, "Password reset email sent successfully"
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
