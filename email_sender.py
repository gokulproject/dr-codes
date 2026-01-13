"""
Email Sender - Email notification functions
Exact Robot Framework EmailLibrary logic
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os


def send_mail(from_address, auth_user, auth_pass, to_address, subject, body, 
              attachments="", cc_address="", host="", port=587):
    """
    Send Mail - Exact Robot Framework EmailLibrary.Send Mail
    
    Robot: EmailLibrary.Send Mail ${from_address} ${e_authuser} ${e_authpass} 
           ${success_to_address} ${success_mail_subject} ${success_mail_body}
           ${attchments} ${success_cc_address} ${e_host} ${e_port}
    """
    try:
        print(f"   Sending email to: {to_address}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = to_address
        msg['Subject'] = subject
        
        if cc_address:
            msg['Cc'] = cc_address
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments
        if attachments:
            attachment_list = attachments.split(';') if isinstance(attachments, str) else attachments
            for filepath in attachment_list:
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                        msg.attach(part)
        
        # Connect to SMTP server
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(auth_user, auth_pass)
            
            # Send email
            recipients = [to_address]
            if cc_address:
                recipients.extend([addr.strip() for addr in cc_address.split(',')])
            
            server.send_message(msg)
        
        print(f"   ✅ Email sent successfully to {to_address}")
        
    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")
        # Don't raise - email failure shouldn't stop process


def send_success_email(config, completed_files, failed_files, attachments):
    """Send success notification email"""
    mail_config = config.mail_config
    
    # Format file lists
    success_list = "Success Files:\n"
    if completed_files:
        success_list += "\n".join([
            f"{i+1}) {file['customer_name']} - {file['filename']}" 
            for i, file in enumerate(completed_files)
        ])
    else:
        success_list += "NA"
    
    failed_list = "\n\nFailed Files:\n"
    if failed_files:
        failed_list += "\n".join([
            f"{i+1}) {file['customer_name']} - {file['filename']} - {file.get('failure_message', '')}" 
            for i, file in enumerate(failed_files)
        ])
    else:
        failed_list += "NA"
    
    file_summary = success_list + failed_list
    
    # Replace placeholders
    body = mail_config['success_mail_body'].replace('<FILES>', file_summary)
    body = body.replace('<>', '\n')
    
    # Send email
    send_mail(
        mail_config['from_address'],
        mail_config['e_authuser'],
        mail_config['e_authpass'],
        mail_config['success_to_address'],
        mail_config['success_mail_subject'],
        body,
        attachments,
        mail_config['success_cc_address'],
        mail_config['e_host'],
        mail_config['e_port']
    )


def send_failure_email(config, process_id, filename, error_message, attachment):
    """Send failure notification email"""
    mail_config = config.mail_config
    
    # Format error message
    error_details = f" {process_id} - {filename} - {error_message}"
    
    # Replace placeholders
    body = mail_config['failure_mail_body'].replace('<process_id>', error_details)
    body = body.replace('<>', '\n')
    
    # Send email
    send_mail(
        mail_config['from_address'],
        mail_config['e_authuser'],
        mail_config['e_authpass'],
        mail_config['failure_to_address'],
        mail_config['failure_mail_subject'],
        body,
        attachment if attachment and os.path.exists(attachment) else "",
        mail_config['failure_cc_address'],
        mail_config['e_host'],
        mail_config['e_port']
    )