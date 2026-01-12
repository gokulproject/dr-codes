# email_creation.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from Config import Config
from Logger import LOGGER

def send_email(to_address, subject, body, attachments=None, cc_address=None):
    """Send email using SMTP."""
    LOGGER.info(f"Starting email send to {to_address} with subject: {subject}")
    msg = MIMEMultipart()
    msg['From'] = Config.FROM_ADDRESS
    msg['To'] = to_address
    msg['Subject'] = subject
    if cc_address:
        msg['Cc'] = cc_address
    
    msg.attach(MIMEText(body, 'plain'))
    
    if attachments:
        attachment_list = [attachments] if ';' not in attachments else attachments.split(';')
        for attachment in attachment_list:
            if not os.path.exists(attachment):
                LOGGER.warning(f"Attachment not found: {attachment}")
                continue
            try:
                part = MIMEBase('application', 'octet-stream')
                with open(attachment, 'rb') as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment)}")
                msg.attach(part)
                LOGGER.info(f"Attached file: {attachment}")
            except Exception as e:
                LOGGER.error(f"Attachment failed: {attachment} - {e}")
    
    try:
        server = smtplib.SMTP(Config.E_HOST, Config.E_PORT)
        server.starttls()
        server.login(Config.E_AUTHUSER, Config.E_AUTHPASS)
        recipients = [to_address] + ([cc_address] if cc_address else [])
        server.sendmail(Config.FROM_ADDRESS, recipients, msg.as_string())
        server.quit()
        LOGGER.info(f"Email sent successfully to: {to_address}")
    except Exception as e:
        LOGGER.error(f"Email sending failed: {e}")
        raise e