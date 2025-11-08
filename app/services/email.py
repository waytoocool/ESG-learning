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


def send_issue_confirmation_email(issue):
    """
    Send confirmation email to user after issue submission.

    Args:
        issue: IssueReport instance that was created

    Returns:
        tuple: (success: bool, message: str)
    """
    from datetime import datetime, UTC
    from ..extensions import db

    try:
        # Get user email
        if not issue.user or not issue.user.email:
            current_app.logger.warning(f"Cannot send confirmation email for {issue.ticket_number}: User email not found")
            return False, "User email not found"

        msg = Message(
            f"Issue Report Confirmation - {issue.ticket_number}",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[issue.user.email]
        )

        # Create HTML email body
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .ticket-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .ticket-box strong {{
            color: #667eea;
            font-size: 18px;
        }}
        .details {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .details ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .details li {{
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .details li:last-child {{
            border-bottom: none;
        }}
        .details strong {{
            color: #555;
            display: inline-block;
            width: 120px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
            border-radius: 0 0 8px 8px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: #28a745;
            color: white;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #dc3545; }}
        .severity-high {{ background: #fd7e14; }}
        .severity-medium {{ background: #ffc107; color: #333; }}
        .severity-low {{ background: #17a2b8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Thank You for Your Report</h1>
        <p>We've received your issue and our team will review it shortly</p>
    </div>

    <div class="content">
        <p>Hello {issue.user.name},</p>

        <p>Thank you for taking the time to report an issue. Your feedback helps us improve the ESG DataVault platform.</p>

        <div class="ticket-box">
            <strong>Ticket Number: {issue.ticket_number}</strong>
            <p style="margin: 5px 0 0 0; color: #666;">Please reference this number in any future communications about this issue.</p>
        </div>

        <h3>Issue Details:</h3>
        <div class="details">
            <ul>
                <li><strong>Title:</strong> {issue.title}</li>
                <li><strong>Category:</strong> {issue.category.replace('_', ' ').title()}</li>
                <li>
                    <strong>Severity:</strong>
                    <span class="status-badge severity-{issue.severity}">{issue.severity.upper()}</span>
                </li>
                <li><strong>Status:</strong> <span class="status-badge">{issue.status.replace('_', ' ').title()}</span></li>
                <li><strong>Submitted:</strong> {issue.created_at.strftime('%B %d, %Y at %I:%M %p UTC') if issue.created_at else 'N/A'}</li>
            </ul>
        </div>

        <h3>What happens next?</h3>
        <ol>
            <li>Our support team will review your report</li>
            <li>We may reach out for additional information if needed</li>
            <li>You'll be notified of any updates to your issue</li>
            <li>Once resolved, you'll receive a confirmation email</li>
        </ol>

        {f'<p style="background: #e7f3ff; padding: 15px; border-radius: 6px; border-left: 4px solid #0066cc;"><strong>GitHub Issue:</strong> Your report has been tracked on GitHub: <a href="{issue.github_issue_url}" target="_blank">{issue.github_issue_url}</a></p>' if issue.github_issue_url else ''}

        <p>If you have any questions or need to provide additional information, please reply to this email with your ticket number.</p>

        <p>Best regards,<br>
        <strong>ESG DataVault Support Team</strong></p>
    </div>

    <div class="footer">
        <p>This is an automated message. Please do not reply directly to this email.</p>
        <p>ESG DataVault - Your Partner in Sustainability Reporting</p>
    </div>
</body>
</html>
        """

        # Also include plain text version
        msg.body = f"""
Thank you for reporting an issue!

Ticket Number: {issue.ticket_number}
(Please reference this number in any future communications)

Issue Details:
- Title: {issue.title}
- Category: {issue.category.replace('_', ' ').title()}
- Severity: {issue.severity.upper()}
- Status: {issue.status.replace('_', ' ').title()}
- Submitted: {issue.created_at.strftime('%B %d, %Y at %I:%M %p UTC') if issue.created_at else 'N/A'}

What happens next?
1. Our support team will review your report
2. We may reach out for additional information if needed
3. You'll be notified of any updates to your issue
4. Once resolved, you'll receive a confirmation email

{f'GitHub Issue: {issue.github_issue_url}' if issue.github_issue_url else ''}

If you have any questions, please reply with your ticket number.

Best regards,
ESG DataVault Support Team
        """

        mail.send(msg)

        # Update issue record
        issue.email_sent = True
        issue.email_sent_at = datetime.now(UTC)
        db.session.commit()

        return True, "Confirmation email sent successfully"

    except Exception as e:
        current_app.logger.error(f"Failed to send issue confirmation email for {issue.ticket_number}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
