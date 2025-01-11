import asyncio
import os
import traceback
import ssl
import tornado
import smtplib
import concurrent.futures

from email.utils import formataddr
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


executor = concurrent.futures.ThreadPoolExecutor(100)


async def send_email_async(email, subject, body, files=None):
    """Send email within tornado application"""

    try:
        current_loop = tornado.ioloop.IOLoop.current()
        result = await current_loop.run_in_executor(executor, send_email, email, subject, body, files)
    except Exception as e:
        print('Exception while sending email')
        print(e)


def send_email_background(email, subject, body, files=None):
    asyncio.ensure_future(send_email_async(email, subject, body, files))


def send_email(receiver_email, subject, body, files=None):

    enable_email = bool(int(os.environ.get('enable_email', '1')))
    if not enable_email:
        print('Please enable email')
        return

    sender_email = os.getenv('sender_email')
    sender_name = os.getenv('sender_name')
    password = os.getenv('password')
    smtp_address = os.getenv('smtp_address')
    smtp_port = int(os.getenv('smtp_port'))

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message['From'] = formataddr((sender_name, sender_email))
    message["To"] = receiver_email
    message["Subject"] = subject

    base_url = os.getenv('BASE_URL')

    # final_body = f"""
    #     <div style="max-width: 600px; margin: 0 auto;">
    #         <div style="padding: 25px 0; text-align: center;">
    #             <img src="{base_url}/assets/images/logo-full.png" style="width: 50%">
    #         </div>
    #         <div>
    #             <h2 style="font-family: 'Mulish', sans-serif;">{subject}</h2>
    #             {body}
    #         </div>
    #         <div>
    #             <p  style="font-family: 'Mulish', sans-serif; font-style: italic; font-size: 13px;">This is an automated message please do not reply</p>
    #         </div>
    #     </div>
    # """

    # Add body to email

    signature = f"""
<div class="email-signature">
    <p>Best Regards,</p>
    <p>The Identify Team</p>
    <p><img src="https://www.identifysuite.com/wp-content/uploads/2024/01/Identify-Logo-02-2-1536x589.png" class="logo" alt="Identify Logo"></p>
    <p class="contact-info">
        <strong>Identify</strong><br>
        Website: <a href="https://www.identifysuite.com/">www.identifysuite.com</a><br>
        Email: <a href="mailto:support@identifysuite.com">support@identifysuite.com</a><br>
    </p>
    <p class="app-links">
        <a href="https://platform.identifysuite.com"><img src="https://www.identifysuite.com/wp-content/uploads/2024/01/Identify-Logo-02-2-1536x589.png" alt="Web App"></a>
        <a href="https://chromewebstore.google.com/detail/identifysuite/badjclfpffbkcgnndpgfnbnbafldgked"><img src="{base_url}/assets/logos/chrome_extension.png" alt="Chrome Extension"></a>
        <a href="**APP_STORE_LINK_HERE**"><img src="https://www.identifysuite.com/wp-content/uploads/2024/06/appstore.png" alt="App Store"></a>
        <a href="**GOOGLE_PLAY_LINK_HERE**"><img src="https://www.identifysuite.com/wp-content/uploads/2024/06/googleplay.png" alt="Google Play"></a>
    </p>
    <p class="social-icons">
        <a href="https://www.facebook.com/Identify"><img src="{base_url}/assets/logos/facebook.png" alt="Facebook"></a>
        <a href="https://www.twitter.com/Identify"><img src="{base_url}/assets/logos/thread.png" alt="Twitter"></a>
        <a href="https://www.instagram.com/identifysuite/"><img src="{base_url}/assets/logos/instagram.png" alt="Instagram"></a>
        <a href="https://www.youtube.com/Identify"><img src="{base_url}/assets/logos/youtube.png" alt="YouTube"></a>
        <a href="https://www.linkedin.com/company/Identify"><img src="{base_url}/assets/logos/linkedin.png" alt="LinkedIn"></a>
    </p>
    <p class="legal">
        This email and any attachments are confidential and may be privileged. If you are not the intended recipient, please notify the sender immediately and delete this email from your system.
    </p>
</div>
"""

    # Combine the body and signature
    final_body = f"""
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700" rel="stylesheet" type="text/css">
        <style>
            .email-signature {{
                font-family: 'Montserrat', sans-serif;
                color: #333;
                font-size: 14px;
                line-height: 21px;
                padding: 20px;
                background-color: #e0eff1;
                border-radius: 8px;
            }}
            .email-signature a {{
                color: #1A73E8;
                text-decoration: none;
            }}
            .email-signature a:hover {{
                text-decoration: underline;
            }}
            .email-signature .logo {{
                width: 120px; /* Adjust the logo size as needed */
                height: auto;
            }}
            .email-signature .social-icons img {{
                width: 24px;
                height: 24px;
                margin-right: 12px;
            }}
            .email-signature .app-links img {{
                width: 120px;
                height: auto;
                margin-right: 12px;
            }}
            .email-signature .contact-info {{
                margin-top: 10px;
            }}
            .email-signature .legal {{
                font-size: 11px;
                color: #777;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div style="max-width: 600px; margin: 0 auto;">
            <div style="padding: 25px 0; text-align: center;">
                <img src="{base_url}/assets/images/logo-full.png" style="width: 50%">
            </div>
            <div>
                <h2 style="font-family: 'Mulish', sans-serif;">{subject}</h2>
                {body}
            </div>
            {signature}
        </div>
    </body>
    </html>
"""
    message.attach(MIMEText(final_body, "html"))

    # filename = "document.pdf"  # In same directory as script

    if files is not None:

        for file_path in files:  # add files to the message

            head, filename = os.path.split(file_path)

            # Open PDF file in binary mode
            with open(file_path, "rb") as attachment:
                # Add file as application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

                # Encode file in ASCII characters to send by email
                encoders.encode_base64(part)

                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )

                # Add attachment to message and convert message to string
                message.attach(part)

    try:

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as ex:
        traceback.print_exc()
