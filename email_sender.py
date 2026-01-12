
"""
Email notification module for Drug Intelligence Automation
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
import os

from logger import get_logger


class EmailSender:
    """Handle email notifications"""
    
    def __init__(self, email_config: Dict[str, Any]):
        self.config = email_config
        self.logger = get_logger()
    
    def send_email(self, to_address: str, subject: str, body: str,
                   attachments: Optional[List[str]] = None,
                   cc_address: Optional[str] = None):
        """Send email with optional attachments"""
        try:
            self.logger.info(f"Sending email to: {to_address}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['from_address']
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc_address:
                msg['Cc'] = cc_address
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                            msg.attach(part)
                        self.logger.debug(f"Attached file: {filepath}")
            
            # Connect to SMTP server
            with smtplib.SMTP(self.config['host'], self.config['port']) as server:
                server.starttls()
                server.login(self.config['auth_user'], self.config['auth_pass'])
                
                # Send email
                recipients = [to_address]
                if cc_address:
                    recipients.extend([addr.strip() for addr in cc_address.split(',')])
                
                server.send_message(msg)
                self.logger.info(f"Email sent successfully to {to_address}")
                
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            raise
    
    def send_success_email(self, to_address: str, cc_address: str,
                          subject: str, body_template: str,
                          completed_files: List[tuple],
                          failed_files: List[tuple],
                          attachments: List[str]):
        """Send success notification email"""
        try:
            # Format file lists
            success_list = "Success Files:\n"
            if completed_files:
                success_list += "\n".join([
                    f"{i+1}) {file[0]} - {file[1]}" 
                    for i, file in enumerate(completed_files)
                ])
            else:
                success_list += "NA"
            
            failed_list = "\nFailed Files:\n"
            if failed_files:
                failed_list += "\n".join([
                    f"{i+1}) {file[0]} - {file[1]} - {file[2]}" 
                    for i, file in enumerate(failed_files)
                ])
            else:
                failed_list += "NA"
            
            file_summary = success_list + "\n" + failed_list
            
            # Replace placeholders
            body = body_template.replace('<FILES>', file_summary)
            body = body.replace('<>', '\n')
            
            # Send email
            self.send_email(to_address, subject, body, attachments, cc_address)
            
        except Exception as e:
            self.logger.error(f"Failed to send success email: {str(e)}", exc_info=True)
            raise
    
    def send_failure_email(self, to_address: str, cc_address: str,
                          subject: str, body_template: str,
                          process_id: str, filename: str,
                          error_message: str, attachment: str):
        """Send failure notification email"""
        try:
            # Format error message
            error_details = f" {process_id} - {filename} - {error_message}"
            
            # Replace placeholders
            body = body_template.replace('<process_id>', error_details)
            body = body.replace('<>', '\n')
            
            # Send email
            attachments = [attachment] if attachment and os.path.exists(attachment) else None
            self.send_email(to_address, subject, body, attachments, cc_address)
            
        except Exception as e:
            self.logger.error(f"Failed to send failure email: {str(e)}", exc_info=True)
            raise