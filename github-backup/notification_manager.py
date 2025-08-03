"""
Notification Manager Module
Handles notifications for backup operations via email, Slack, and webhooks.
"""

import os
import logging
import smtplib
import json
import requests
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from jinja2 import Template

class NotificationManager:
    """Manages notifications for backup operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize notification channels
        self.email_config = config.get('email', {})
        self.slack_config = config.get('slack', {})
        self.webhook_config = config.get('webhook', {})
    
    def send_backup_summary(self, summary: Dict):
        """Send backup summary notification."""
        try:
            # Email notification
            if self.email_config.get('enabled', False):
                self._send_email_notification(summary)
            
            # Slack notification
            if self.slack_config.get('enabled', False):
                self._send_slack_notification(summary)
            
            # Webhook notification
            if self.webhook_config.get('enabled', False):
                self._send_webhook_notification(summary)
                
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {str(e)}")
    
    def send_error_notification(self, error_message: str):
        """Send error notification."""
        try:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'error': error_message,
                'type': 'error'
            }
            
            # Email notification
            if self.email_config.get('enabled', False):
                self._send_email_error(error_data)
            
            # Slack notification
            if self.slack_config.get('enabled', False):
                self._send_slack_error(error_data)
            
            # Webhook notification
            if self.webhook_config.get('enabled', False):
                self._send_webhook_error(error_data)
                
        except Exception as e:
            self.logger.error(f"Failed to send error notifications: {str(e)}")
    
    def _send_email_notification(self, summary: Dict):
        """Send email notification with backup summary."""
        try:
            # Prepare email content
            subject = f"GitHub Backup Summary - {summary.get('timestamp', 'Unknown')}"
            body = self._generate_email_content(summary)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
    
    def _send_email_error(self, error_data: Dict):
        """Send email notification for errors."""
        try:
            subject = f"GitHub Backup Error - {error_data['timestamp']}"
            body = self._generate_error_email_content(error_data)
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Error email notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send error email notification: {str(e)}")
    
    def _generate_email_content(self, summary: Dict) -> str:
        """Generate HTML email content for backup summary."""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                .stat-box { 
                    background-color: #e9ecef; 
                    padding: 15px; 
                    border-radius: 5px; 
                    text-align: center;
                    flex: 1;
                    margin: 0 10px;
                }
                .success { background-color: #d4edda; color: #155724; }
                .error { background-color: #f8d7da; color: #721c24; }
                .warning { background-color: #fff3cd; color: #856404; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .failed-list { background-color: #f8d7da; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GitHub Organization Backup Summary</h1>
                <p><strong>Timestamp:</strong> {{ summary.timestamp }}</p>
                <p><strong>Duration:</strong> {{ "%.2f"|format(summary.duration_seconds) }} seconds</p>
            </div>
            
            <div class="summary">
                <h2>Overall Statistics</h2>
                <div class="stats">
                    <div class="stat-box">
                        <h3>Total</h3>
                        <p>{{ summary.total_backups }}</p>
                    </div>
                    <div class="stat-box success">
                        <h3>Successful</h3>
                        <p>{{ summary.successful }}</p>
                    </div>
                    <div class="stat-box error">
                        <h3>Failed</h3>
                        <p>{{ summary.failed }}</p>
                    </div>
                    {% if summary.dry_run > 0 %}
                    <div class="stat-box warning">
                        <h3>Dry Run</h3>
                        <p>{{ summary.dry_run }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            {% if summary.target_summary %}
            <div class="summary">
                <h2>Target Breakdown</h2>
                <table>
                    <tr>
                        <th>Target</th>
                        <th>Successful</th>
                        <th>Failed</th>
                        <th>Dry Run</th>
                    </tr>
                    {% for target, stats in summary.target_summary.items() %}
                    <tr>
                        <td>{{ target }}</td>
                        <td class="success">{{ stats.success }}</td>
                        <td class="error">{{ stats.failed }}</td>
                        <td class="warning">{{ stats.dry_run }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% endif %}
            
            {% set failed_backups = summary.results | selectattr('status', 'equalto', 'error') | list %}
            {% if failed_backups %}
            <div class="failed-list">
                <h2>Failed Backups ({{ failed_backups | length }})</h2>
                <ul>
                    {% for backup in failed_backups %}
                    <li><strong>{{ backup.repository }}</strong> → {{ backup.target }}: {{ backup.error }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(summary=summary)
    
    def _generate_error_email_content(self, error_data: Dict) -> str:
        """Generate HTML email content for error notifications."""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8d7da; padding: 20px; border-radius: 5px; }
                .error-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GitHub Backup Error</h1>
                <p><strong>Timestamp:</strong> {{ error_data.timestamp }}</p>
            </div>
            
            <div class="error-box">
                <h2>Error Details</h2>
                <p><strong>Error:</strong> {{ error_data.error }}</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(error_data=error_data)
    
    def _send_slack_notification(self, summary: Dict):
        """Send Slack notification with backup summary."""
        try:
            webhook_url = self._get_webhook_url('slack')
            if not webhook_url:
                return
            
            # Prepare Slack message
            message = self._generate_slack_message(summary)
            
            # Send to Slack
            response = requests.post(webhook_url, json=message)
            response.raise_for_status()
            
            self.logger.info("Slack notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _send_slack_error(self, error_data: Dict):
        """Send Slack notification for errors."""
        try:
            webhook_url = self._get_webhook_url('slack')
            if not webhook_url:
                return
            
            # Prepare error message
            message = self._generate_slack_error_message(error_data)
            
            # Send to Slack
            response = requests.post(webhook_url, json=message)
            response.raise_for_status()
            
            self.logger.info("Slack error notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack error notification: {str(e)}")
    
    def _generate_slack_message(self, summary: Dict) -> Dict:
        """Generate Slack message for backup summary."""
        # Determine color based on success/failure ratio
        if summary['failed'] == 0:
            color = "good"  # Green
        elif summary['successful'] == 0:
            color = "danger"  # Red
        else:
            color = "warning"  # Yellow
        
        # Create attachment fields
        fields = [
            {
                "title": "Total Backups",
                "value": str(summary['total_backups']),
                "short": True
            },
            {
                "title": "Successful",
                "value": str(summary['successful']),
                "short": True
            },
            {
                "title": "Failed",
                "value": str(summary['failed']),
                "short": True
            },
            {
                "title": "Duration",
                "value": f"{summary['duration_seconds']:.2f} seconds",
                "short": True
            }
        ]
        
        if summary.get('dry_run', 0) > 0:
            fields.append({
                "title": "Dry Run",
                "value": str(summary['dry_run']),
                "short": True
            })
        
        # Add target breakdown
        if summary.get('target_summary'):
            target_text = ""
            for target, stats in summary['target_summary'].items():
                target_text += f"• {target}: {stats['success']}✓ {stats['failed']}✗\n"
            
            fields.append({
                "title": "Target Breakdown",
                "value": target_text,
                "short": False
            })
        
        # Add failed backups if any
        failed_backups = [r for r in summary['results'] if r['status'] == 'error']
        if failed_backups:
            failed_text = ""
            for backup in failed_backups[:5]:  # Limit to first 5
                failed_text += f"• {backup['repository']} → {backup['target']}: {backup['error']}\n"
            
            if len(failed_backups) > 5:
                failed_text += f"... and {len(failed_backups) - 5} more"
            
            fields.append({
                "title": "Failed Backups",
                "value": failed_text,
                "short": False
            })
        
        return {
            "channel": self.slack_config.get('channel', '#backup-alerts'),
            "attachments": [
                {
                    "color": color,
                    "title": "GitHub Organization Backup Summary",
                    "text": f"Backup completed at {summary.get('timestamp', 'Unknown')}",
                    "fields": fields,
                    "footer": "GitHub Backup System"
                }
            ]
        }
    
    def _generate_slack_error_message(self, error_data: Dict) -> Dict:
        """Generate Slack message for error notifications."""
        return {
            "channel": self.slack_config.get('channel', '#backup-alerts'),
            "attachments": [
                {
                    "color": "danger",
                    "title": "GitHub Backup Error",
                    "text": f"Error occurred at {error_data['timestamp']}",
                    "fields": [
                        {
                            "title": "Error",
                            "value": error_data['error'],
                            "short": False
                        }
                    ],
                    "footer": "GitHub Backup System"
                }
            ]
        }
    
    def _send_webhook_notification(self, summary: Dict):
        """Send webhook notification with backup summary."""
        try:
            webhook_url = self._get_webhook_url('webhook')
            if not webhook_url:
                return
            
            # Prepare webhook payload
            payload = {
                'timestamp': summary.get('timestamp'),
                'type': 'backup_summary',
                'data': summary
            }
            
            # Add signature if configured
            headers = {}
            secret = self.webhook_config.get('secret')
            if secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    secret.encode('utf-8'),
                    json.dumps(payload).encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = f'sha256={signature}'
            
            # Send webhook
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
            self.logger.info("Webhook notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")
    
    def _send_webhook_error(self, error_data: Dict):
        """Send webhook notification for errors."""
        try:
            webhook_url = self._get_webhook_url('webhook')
            if not webhook_url:
                return
            
            # Prepare webhook payload
            payload = {
                'timestamp': error_data.get('timestamp'),
                'type': 'backup_error',
                'data': error_data
            }
            
            # Add signature if configured
            headers = {}
            secret = self.webhook_config.get('secret')
            if secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    secret.encode('utf-8'),
                    json.dumps(payload).encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = f'sha256={signature}'
            
            # Send webhook
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
            self.logger.info("Webhook error notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook error notification: {str(e)}")
    
    def _get_webhook_url(self, config_type: str) -> Optional[str]:
        """Get webhook URL from configuration."""
        if config_type == 'slack':
            url = self.slack_config.get('webhook_url', '')
        elif config_type == 'webhook':
            url = self.webhook_config.get('url', '')
        else:
            return None
        
        # Handle environment variable substitution
        if url.startswith('${') and url.endswith('}'):
            env_var = url[2:-1]
            url = os.getenv(env_var, '')
        
        return url if url else None 