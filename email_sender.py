"""
Email Sender Module - Drug Intelligence Automation
Handles all email notifications with attachments
Supports success/failure notifications with templates
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any
import os


class EmailSender:
    """
    Email sender class for sending notifications with attachments
    """
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize email sender with SMTP configuration
        
        Args:
            config: Email configuration dictionary containing:
                - host: SMTP server host
                - port: SMTP server port
                - auth_user: SMTP authentication username
                - auth_pass: SMTP authentication password
                - from_address: Sender email address
                - use_tls: Whether to use TLS (default: True)
            logger: Logger instance for logging email operations
        """
        self.config = config
        self.logger = logger
        
        # SMTP Configuration
        self.smtp_host = config.get('host')
        self.smtp_port = config.get('port', 587)
        self.auth_user = config.get('auth_user')
        self.auth_pass = config.get('auth_pass')
        self.from_address = config.get('from_address')
        self.use_tls = config.get('use_tls', True)
        
        if self.logger:
            self.logger.debug(f"Email sender initialized with host: {self.smtp_host}:{self.smtp_port}")
    
    def send_email(
        self,
        to_addresses: str,
        subject: str,
        body: str,
        cc_addresses: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        Send email with optional attachments
        
        Args:
            to_addresses: Semicolon-separated recipient email addresses
            subject: Email subject
            body: Email body content
            cc_addresses: Semicolon-separated CC email addresses
            attachments: List of file paths to attach
            is_html: Whether body is HTML content
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if self.logger:
                self.logger.log_function_entry(
                    "send_email",
                    to=to_addresses,
                    subject=subject,
                    cc=cc_addresses,
                    attachments_count=len(attachments) if attachments else 0
                )
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['Subject'] = subject
            
            # Parse TO addresses
            to_list = [addr.strip() for addr in to_addresses.split(';') if addr.strip()]
            msg['To'] = ', '.join(to_list)
            
            # Parse CC addresses if provided
            cc_list = []
            if cc_addresses:
                cc_list = [addr.strip() for addr in cc_addresses.split(';') if addr.strip()]
                if cc_list:
                    msg['Cc'] = ', '.join(cc_list)
            
            # Combine all recipients
            all_recipients = to_list + cc_list
            
            if not all_recipients:
                raise ValueError("No valid recipient email addresses provided")
            
            # Attach body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    try:
                        self._attach_file(msg, file_path)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"⚠️ Failed to attach file {file_path}: {str(e)}")
            
            # Connect to SMTP server and send
            if self.logger:
                self.logger.info(f"⏳ Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                # Enable TLS if configured
                if self.use_tls:
                    server.starttls()
                
                # Login
                if self.logger:
                    self.logger.debug("Authenticating with SMTP server...")
                
                server.login(self.auth_user, self.auth_pass)
                
                # Send email
                if self.logger:
                    self.logger.info(f"⏳ Sending email to {len(all_recipients)} recipient(s)...")
                
                server.send_message(msg)
            
            if self.logger:
                self.logger.log_email_status(
                    recipient=', '.join(to_list),
                    subject=subject,
                    status="SUCCESS"
                )
                self.logger.log_function_exit("send_email", result="SUCCESS")
            
            return True
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error while sending email: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.log_exception("send_email", e)
            return False
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.log_exception("send_email", e)
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """
        Attach a file to the email message
        
        Args:
            msg: MIMEMultipart message object
            file_path: Path to file to attach
            
        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If file cannot be read or attached
        """
        try:
            file_path_obj = Path(file_path)
            
            # Check if file exists
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Attachment file not found: {file_path}")
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                raise PermissionError(f"Cannot read attachment file: {file_path}")
            
            # Read file and attach
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            # Encode file in base64
            encoders.encode_base64(part)
            
            # Add header with filename
            filename = file_path_obj.name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            # Attach to message
            msg.attach(part)
            
            if self.logger:
                self.logger.debug(f"✅ File attached: {filename}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to attach file {file_path}: {str(e)}")
            raise
    
    def send_success_notification(
        self,
        mail_config: Dict[str, str],
        process_id: str,
        filename: str,
        success_files: List[tuple],
        failed_files: List[tuple],
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send success notification email with summary
        
        Args:
            mail_config: Dictionary containing email template configuration
            process_id: Process ID
            filename: Master tracker filename
            success_files: List of tuples (customer_name, filename)
            failed_files: List of tuples (customer_name, filename, error_message)
            attachments: List of file paths to attach
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if self.logger:
                self.logger.info("⏳ Preparing success notification email...")
            
            # Format success files
            if success_files:
                success_list = "\n".join([
                    f"{i+1}) {customer} - {file}" 
                    for i, (customer, file) in enumerate(success_files)
                ])
            else:
                success_list = "NA"
            
            # Format failed files
            if failed_files:
                failed_list = "\n".join([
                    f"{i+1}) {customer} - {file} - {error}" 
                    for i, (customer, file, error) in enumerate(failed_files)
                ])
            else:
                failed_list = "NA"
            
            # Combine success and failed files
            files_summary = f"Success Files:\n{success_list}\n\nFailed Files:\n{failed_list}"
            
            # Get email template from config
            subject = mail_config.get('Success Mail Subject', 'Drug Intelligence - Process Completed')
            body_template = mail_config.get('Success Mail Body', 'Process completed. <FILES>')
            
            # Replace placeholders
            body = body_template.replace('<FILES>', files_summary)
            body = body.replace('<>', '\n')  # Replace custom line break markers
            
            # Get recipients
            to_addresses = mail_config.get('Success To Address', '')
            cc_addresses = mail_config.get('Success Cc Address', '')
            
            # Send email
            return self.send_email(
                to_addresses=to_addresses,
                subject=subject,
                body=body,
                cc_addresses=cc_addresses,
                attachments=attachments,
                is_html=False
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to send success notification: {str(e)}")
            return False
    
    def send_failure_notification(
        self,
        mail_config: Dict[str, str],
        process_id: str,
        filename: str,
        error_message: str,
        attachment_path: Optional[str] = None
    ) -> bool:
        """
        Send failure notification email
        
        Args:
            mail_config: Dictionary containing email template configuration
            process_id: Process ID
            filename: Master tracker filename
            error_message: Error message describing the failure
            attachment_path: Optional path to failed file
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if self.logger:
                self.logger.info("⏳ Preparing failure notification email...")
            
            # Get email template from config
            subject = mail_config.get('Failure Mail Subject', 'Drug Intelligence - Process Failed')
            body_template = mail_config.get('Failure Mail Body', 'Process failed. <process_id>')
            
            # Format error details
            error_details = f"{process_id} - {filename} - {error_message}"
            
            # Replace placeholders
            body = body_template.replace('<process_id>', error_details)
            body = body.replace('<>', '\n')  # Replace custom line break markers
            
            # Get recipients
            to_addresses = mail_config.get('Failure To Address', '')
            cc_addresses = mail_config.get('Failure Cc Address', '')
            
            # Prepare attachments
            attachments = [attachment_path] if attachment_path and os.path.exists(attachment_path) else None
            
            # Send email
            return self.send_email(
                to_addresses=to_addresses,
                subject=subject,
                body=body,
                cc_addresses=cc_addresses,
                attachments=attachments,
                is_html=False
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to send failure notification: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Testing SMTP connection to {self.smtp_host}:{self.smtp_port}...")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.auth_user, self.auth_pass)
            
            if self.logger:
                self.logger.success("✅ SMTP connection test successful")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ SMTP connection test failed: {str(e)}")
            return False
