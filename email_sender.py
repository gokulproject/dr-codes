"""
Email sender module for Drug Intelligence Automation
Handles all email operations including sending with attachments
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import os
from logger import get_logger


class EmailSender:
    """Email sender class for sending notifications"""
    
    def __init__(self, email_config: dict):
        """
        Initialize email sender
        
        Args:
            email_config: Email configuration dictionary
        """
        self.config = email_config
        self.logger = get_logger()
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        cc_address: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email with optional attachments
        
        Args:
            to_address: Recipient email address (can be semicolon-separated)
            subject: Email subject
            body: Email body (can contain HTML)
            cc_address: CC email address (optional, semicolon-separated)
            attachments: List of file paths to attach (optional)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            self.logger.log_function_start(
                "send_email",
                to=to_address,
                subject=subject,
                has_attachments=bool(attachments)
            )
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['from_address']
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc_address:
                msg['Cc'] = cc_address
            
            # Attach body
            # Convert line breaks for HTML display
            html_body = body.replace('\n', '<br>')
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
                    else:
                        self.logger.warning(f"Attachment file not found: {file_path}")
            
            # Prepare recipient list
            recipients = self._parse_addresses(to_address)
            if cc_address:
                recipients.extend(self._parse_addresses(cc_address))
            
            # Send email
            with smtplib.SMTP(self.config['host'], self.config['port']) as server:
                server.starttls()
                server.login(
                    self.config['auth_user'],
                    self.config['auth_pass']
                )
                server.send_message(msg)
            
            self.logger.log_email_sent(to_address, subject, "Success")
            self.logger.log_function_end("send_email", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Send email")
            self.logger.log_email_sent(to_address, subject, f"Failed: {str(e)}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """
        Attach file to email message
        
        Args:
            msg: Email message object
            file_path: Path to file to attach
        """
        try:
            filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            self.logger.debug(f"Attached file: {filename}")
            
        except Exception as e:
            self.logger.log_exception(e, f"Attach file: {file_path}")
    
    def _parse_addresses(self, addresses: str) -> List[str]:
        """
        Parse semicolon-separated email addresses
        
        Args:
            addresses: Semicolon-separated email addresses
        
        Returns:
            List of email addresses
        """
        if not addresses:
            return []
        return [addr.strip() for addr in addresses.split(';') if addr.strip()]
    
    def send_success_email(
        self,
        mail_config: dict,
        success_files: List[tuple],
        failed_files: List[tuple],
        attachments: List[str]
    ) -> bool:
        """
        Send success notification email
        
        Args:
            mail_config: Mail configuration dictionary
            success_files: List of (customer_name, filename) tuples
            failed_files: List of (customer_name, filename, error) tuples
            attachments: List of file paths to attach
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Format success files
            if success_files:
                success_list = '\n'.join([
                    f"{i+1}) {item[0]} - {item[1]}"
                    for i, item in enumerate(success_files)
                ])
            else:
                success_list = "NA"
            
            # Format failed files
            if failed_files:
                failed_list = '\n'.join([
                    f"{i+1}) {item[0]} - {item[1]} - {item[2]}"
                    for i, item in enumerate(failed_files)
                ])
            else:
                failed_list = "NA"
            
            # Prepare email body
            files_info = f"Success Files:\n{success_list}\n\nFailed Files:\n{failed_list}"
            body = mail_config['success_mail_body'].replace('<FILES>', files_info)
            body = body.replace('<>', '\n')
            
            # Send email
            return self.send_email(
                to_address=mail_config['success_to_address'],
                subject=mail_config['success_mail_subject'],
                body=body,
                cc_address=mail_config.get('success_cc_address'),
                attachments=attachments
            )
            
        except Exception as e:
            self.logger.log_exception(e, "Send success email")
            return False
    
    def send_failure_email(
        self,
        mail_config: dict,
        process_id: str,
        filename: str,
        error_message: str,
        attachment: Optional[str] = None
    ) -> bool:
        """
        Send failure notification email
        
        Args:
            mail_config: Mail configuration dictionary
            process_id: Process ID
            filename: Master tracker filename
            error_message: Error message
            attachment: Optional attachment file path
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Prepare email body
            process_info = f"{process_id} - {filename} - {error_message}"
            body = mail_config['failure_mail_body'].replace('<process_id>', process_info)
            body = body.replace('<>', '\n')
            
            # Send email
            attachments = [attachment] if attachment else None
            
            return self.send_email(
                to_address=mail_config['failure_to_address'],
                subject=mail_config['failure_mail_subject'],
                body=body,
                cc_address=mail_config.get('failure_cc_address'),
                attachments=attachments
            )
            
        except Exception as e:
            self.logger.log_exception(e, "Send failure email")
            return False
