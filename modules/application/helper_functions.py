import os
import json

from dotenv import load_dotenv

from sqlalchemy.exc import IntegrityError
from common.database_v2 import make_connection
from common.email_sender import send_email_background
from common.gdb_helper_v2 import GDBHelper
from common.helpers import format_date, MakeTimedUniqueId
from modules.application.models import UserSession, User
from common.exceptions import GeneralException


async def fetch_session(gdb, session_id, _raise=True):
    query = gdb.query(UserSession).filter(UserSession.session_id == session_id)
    session = await gdb.one_or_none(query)
    if session is None:
        if _raise:
            raise GeneralException(401, 'Unauthorized')
        else:
            return None

    return json.loads(session.session_data)


def make_profile_data(user, role):

    # avatar = user.avatar or '/assets/images/avatars/placeholder.png'
    # if avatar is not None and 'googleuser' not in user.avatar:
    #     avatar = f'{os.getenv("BASE_URL")}{avatar}'

    avatar = user.avatar or '/assets/images/avatars/placeholder.png'
    avatar = f'{os.getenv("BASE_URL")}{avatar}'

    profile = {
        'uuid': user.user_id,
        'role': [role.role],
        'data': {
            'id': user.user_id,
            'displayName': user.name,
            'roleName': role.name,
            'role': role.role,
            'avatar': avatar,
            'status': user.status,
            'about': user.about,
            'email': user.email,
            'phone': user.phone,
            'is_email_verified': user.email_verified,
            'stripe_customer_id': user.stripe_customer_id,
            'last_login': user.last_login,
            'intro_offer_availed': user.intro_offer_availed,
            'trial_availed': user.trial_availed
        },
        'permissions': []
    }

    return profile


def confirmation_email(payload):
    name = payload['name']
    token = payload['token']
    base_url = payload['base_url']
    subject = 'Confirm you email'
    verification_link = f'{base_url}/verification/confirm-email?token={token}'

    print(verification_link)
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Thank you for creating an account with Identify. To ensure the security of your information and activate your account, we kindly request you to confirm your email address. This step is essential to provide you with a smooth and secure user experience.</p>
    <p>To confirm your email address, please follow the instructions below:</p>
    <p><a href="{verification_link}" target="_blank" style="color: #007bff; text-decoration: none;">Click here</a> to verify your email address.</p>
    <p>You will be redirected to a confirmation page confirming the successful verification of your email address.</p>
    <p>Please note that your account will remain inactive until you confirm your email address. Once verified, you will gain access to all the features and benefits of our platform.</p>
    <p>We thank you for choosing Identify and look forward to serving you.</p>
</div>
    """

    return subject, email_body


def welcome_email(payload):
    name = payload['name']
    base_url = payload['base_url']
    subject = 'Welcome to Identify'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>We're thrilled to welcome you to Identify</p>
    <p>Great news - your email has been successfully verified, and your account is now ready for action. You can now log in using your credentials and explore all the exciting features we have to offer.</p>
    <p><strong>Login here:</strong> <a href="{base_url}" style="color: #007bff; text-decoration: none;">Login Link</a></p>
    <p>Thank you for choosing Identify. We're excited to have you on board!</p>
</div>
    """

    return subject, email_body


def reset_link_email(payload):
    name = payload['name']
    token = payload['token']
    base_url = payload['base_url']
    subject = 'Reset your password - Identify'
    reset_password_link = f'{base_url}/reset-password/{token}'
    email_body = f"""
<div>
    <p>Hi {name},</p>
    <p>Please <a href="{reset_password_link}" target="_blank" style="color: #007bff; text-decoration: none;">Click here</a> to reset your password.</p>
    <p>Regards,<br>Team Identify</p>
</div>
"""

    return subject, email_body


def reset_successful_email(payload):
    name = payload['name']
    subject = 'Password Reset Successful - Identify'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Your password has been successfully reset. You can now log in to your account using your new password.</p>
    <p>If you did not request this password reset or believe this is an error, please contact our support team immediately.</p>
    <p>Thank you for choosing Identify.</p>
</div>
"""

    return subject, email_body


def email_new_login(payload):
    name = payload['name']
    subject = 'New Device Sign in'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Your Identify account was just signed in from a new device. You're getting this email to make sure it was you.</p>
</div>
"""

    return subject, email_body


def stripe_payment_email_content(payload):
    name = payload['name']
    amount = payload['amount']
    date = payload['date']
    invoice_number = payload['invoice_number']
    plan = payload['plan']
    billing_cycle = payload['billing_cycle']

    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Thank you for your recent payment for your {plan} subscription!</p>
    <p><strong>Payment Details:</strong></p>
    <ul>
        <li>Amount: $ {amount}</li>
        <li>Date: {date}</li>
        <li>Invoice No: {invoice_number}</li>
    </ul>
    <p><strong>Subscription Information:</strong></p>
    <ul>
        <li>Plan: {plan}</li>
        <li>Billing Cycle: {billing_cycle}</li>
    </ul>
    <p>Attached is a PDF receipt of your payment for your records. Please review it for more detailed information about the transaction.</p>
    <p>Thank you again for choosing {plan} subscription.</p>
</div>
"""
    return email_body


def payment_fail_email(payload):
    name = payload['name']
    plan = payload['plan']
    subject = f'Identify {plan} Subscription Payment Failure'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>We regret to inform you that the payment for your {plan} subscription failed. As a result, your subscription may be suspended or canceled.</p>
    <p>To ensure uninterrupted access to our services, please take the following actions:</p>
    <ul>
        <li>Verify that your payment information is up to date and correct.</li>
        <li>Ensure that there are sufficient funds available in your account.</li>
        <li>Contact your bank or payment provider for further assistance if needed.</li>
    </ul>
    <p>Once the payment issue is resolved, please retry the payment on Identify portal.</p>
    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
    <p>Thank you for your understanding.</p>
</div>
"""

    return subject, email_body


def subscription_update_email(payload):
    name = payload['name']
    plan = payload['plan']
    old_duration = payload['old_duration']
    new_duration = payload['new_duration']
    date = payload['date']
    subject = f'{plan} Subscription Updated - Identify'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>We're writing to inform you that your {plan} subscription with Identify has been successfully updated.</p>
    <p><strong>Previous Plan: </strong>{old_duration}</p>
    <p><strong>New Plan: </strong>{new_duration}</p>
    <p>The changes to your subscription duration will take effect on {date}.</p>
    <p>If you have any questions or concerns regarding this update, please don't hesitate to contact our support team.</p>
    <p>Thank you for choosing Identify.</p>
</div>
"""

    return subject, email_body


def basic_plan_email(payload):
    name = payload['name']
    plan = payload['plan']
    billing_cycle = payload['billing_cycle']

    subject = f'Thank You for Choosing Our {plan} Subscription'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Thank you choosing our {plan} subscription!</p>
    <p><strong>Subscription Information:</strong></p>
    <ul>
        <li>Plan: {plan} Subscription</li>
        <li>Billing Cycle: {billing_cycle}</li>
    </ul>
</div>
"""
    return subject, email_body


def trial_subscription_email(payload):
    name = payload['name']
    plan = payload['plan']
    trial_days = payload['trial_days']
    date = payload['date']

    subject = f'Thank You for Choosing Our Trial of {plan} Subscription'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>Thank you for signing up for the trial of our {plan} subscription!</p>
    <p><strong>Subscription Information:</strong></p>
    <ul>
        <li>Plan: {plan} Subscription</li>
        <li>Trial Days: {trial_days}</li>
    </ul>
    <p>Your trial period will give you access to all the features of our {plan} subscription for a limited time.</p>
    <p>After the trial period ends, your payment will be automatically deducted on {date} to continue your subscription.</p>
    <p>If you have any questions or need assistance during your trial, feel free to contact our support team.</p>
    <p>Thank you again for choosing our trial subscription. We hope you enjoy the {plan} features!</p>
</div>
"""
    return subject, email_body


def subscription_cancel_email(payload):
    name = payload['name']
    plan = payload['plan']
    billing_cycle = payload['billing_cycle']
    subscription_end_date = payload['date']

    subject = f'Subscription Cancellation Confirmation - Identify'
    email_body = f"""
<div>
    <p>Dear {name},</p>
    <p>We're sorry to see you go, but we have received your request to cancel your subscription.</p>
    <p><strong>Subscription Details:</strong></p>
    <ul>
        <li>Plan: {plan} Subscription</li>
        <li>Billing Cycle: {billing_cycle}</li>
        <li>Subscription End Date: {subscription_end_date}</li>
    </ul>
    <p>You will still have access to all the features and benefits of your subscription until the end of your current billing cycle on {subscription_end_date}. After this date, your access will be revoked, and you will no longer be able to use the services provided under this subscription.</p>
    <p>If you have any questions or need assistance, please feel free to contact our support team.</p>
    <p>We appreciate your support and hope to serve you again in the future.</p>
</div>
"""
    return subject, email_body


def set_password_email(payload):
    name = payload['name']
    token = payload['token']
    base_url = payload['base_url']
    role = payload['role']
    subject = f'Activate Your {role} Account – Set Your Password Now'
    set_password_link = f'{base_url}/reset-password/{token}'
    email_body = f"""
<div>
    <p>Hi {name},</p>
    <p>We are excited to welcome you as the new {role} on our web portal. To get started, please <a href="{set_password_link}" target="_blank" style="color: #007bff; text-decoration: none;">Click here</a> to set your password and access your account.</p>
    <p>Once you've set your password, you can log in and begin managing your Prep Center.</p>
</div>
"""

    return subject, email_body
