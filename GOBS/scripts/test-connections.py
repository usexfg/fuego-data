#!/usr/bin/env python3
"""
Test Connections Script
Test all connections and configurations before running backups.
"""

import os
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from github_backup import GitHubBackup
from backup_targets import BackupTargetFactory
from utils import load_config, setup_logging

# Load environment variables
load_dotenv()

console = Console()

def test_github_connection(config):
    """Test GitHub API connection."""
    console.print("\n[bold blue]Testing GitHub Connection...[/bold blue]")
    
    try:
        github_backup = GitHubBackup(config['github'])
        
        # Test basic connection
        if github_backup.test_connection():
            console.print("✅ GitHub connection successful")
            
            # Get organization info
            org_info = github_backup.get_organization_info()
            if org_info:
                console.print(f"📁 Organization: {org_info.get('name', 'Unknown')}")
                console.print(f"👥 Public repos: {org_info.get('public_repos', 0)}")
                console.print(f"🔒 Private repos: {org_info.get('total_private_repos', 0)}")
            
            # Test repository access
            repos = github_backup.get_repositories(include_private=True, include_archived=False)
            console.print(f"📚 Found {len(repos)} repositories")
            
            return True
        else:
            console.print("❌ GitHub connection failed")
            return False
            
    except Exception as e:
        console.print(f"❌ GitHub connection error: {str(e)}")
        return False

def test_backup_targets(config):
    """Test all configured backup targets."""
    console.print("\n[bold blue]Testing Backup Targets...[/bold blue]")
    
    backup_targets = BackupTargetFactory.create_targets(config.get('backup_targets', {}))
    
    if not backup_targets:
        console.print("⚠️  No backup targets configured")
        return False
    
    results = {}
    
    for target_name, target in backup_targets.items():
        console.print(f"\n🔍 Testing {target_name}...")
        
        if not target.is_enabled():
            console.print(f"⏭️  {target_name} is disabled")
            results[target_name] = "disabled"
            continue
        
        try:
            if target.test_connection():
                console.print(f"✅ {target_name} connection successful")
                results[target_name] = "success"
            else:
                console.print(f"❌ {target_name} connection failed")
                results[target_name] = "failed"
        except Exception as e:
            console.print(f"❌ {target_name} connection error: {str(e)}")
            results[target_name] = "error"
    
    return results

def test_local_backup(config):
    """Test local backup configuration."""
    console.print("\n[bold blue]Testing Local Backup...[/bold blue]")
    
    local_config = config.get('local_backup', {})
    
    if not local_config.get('enabled', False):
        console.print("⏭️  Local backup is disabled")
        return False
    
    backup_path = local_config.get('path', './backups')
    
    try:
        # Test if directory exists or can be created
        os.makedirs(backup_path, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(backup_path, '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        console.print(f"✅ Local backup directory accessible: {backup_path}")
        return True
        
    except Exception as e:
        console.print(f"❌ Local backup error: {str(e)}")
        return False

def test_notifications(config):
    """Test notification configurations."""
    console.print("\n[bold blue]Testing Notifications...[/bold blue]")
    
    notifications = config.get('notifications', {})
    results = {}
    
    # Test email configuration
    email_config = notifications.get('email', {})
    if email_config.get('enabled', False):
        console.print("📧 Email notifications enabled")
        try:
            import smtplib
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.quit()
            console.print("✅ Email configuration valid")
            results['email'] = "success"
        except Exception as e:
            console.print(f"❌ Email configuration error: {str(e)}")
            results['email'] = "failed"
    else:
        console.print("⏭️  Email notifications disabled")
        results['email'] = "disabled"
    
    # Test Slack configuration
    slack_config = notifications.get('slack', {})
    if slack_config.get('enabled', False):
        console.print("💬 Slack notifications enabled")
        webhook_url = slack_config.get('webhook_url', '')
        if webhook_url.startswith('${') and webhook_url.endswith('}'):
            env_var = webhook_url[2:-1]
            webhook_url = os.getenv(env_var, '')
        
        if webhook_url:
            console.print("✅ Slack webhook URL configured")
            results['slack'] = "success"
        else:
            console.print("❌ Slack webhook URL not found")
            results['slack'] = "failed"
    else:
        console.print("⏭️  Slack notifications disabled")
        results['slack'] = "disabled"
    
    # Test webhook configuration
    webhook_config = notifications.get('webhook', {})
    if webhook_config.get('enabled', False):
        console.print("🔗 Webhook notifications enabled")
        webhook_url = webhook_config.get('url', '')
        if webhook_url.startswith('${') and webhook_url.endswith('}'):
            env_var = webhook_url[2:-1]
            webhook_url = os.getenv(env_var, '')
        
        if webhook_url:
            console.print("✅ Webhook URL configured")
            results['webhook'] = "success"
        else:
            console.print("❌ Webhook URL not found")
            results['webhook'] = "failed"
    else:
        console.print("⏭️  Webhook notifications disabled")
        results['webhook'] = "disabled"
    
    return results

def test_git_installation():
    """Test Git installation."""
    console.print("\n[bold blue]Testing Git Installation...[/bold blue]")
    
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, check=True)
        console.print(f"✅ Git installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("❌ Git not installed or not in PATH")
        return False

def display_summary(github_result, target_results, local_result, notification_results, git_result):
    """Display test summary."""
    console.print("\n" + "="*60)
    console.print("[bold blue]CONNECTION TEST SUMMARY[/bold blue]")
    console.print("="*60)
    
    # Create summary table
    table = Table(title="Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    # GitHub
    status = "✅ PASS" if github_result else "❌ FAIL"
    table.add_row("GitHub API", status, "Organization access")
    
    # Backup targets
    if target_results:
        for target, result in target_results.items():
            if result == "success":
                status = "✅ PASS"
                details = "Connected"
            elif result == "disabled":
                status = "⏭️  SKIP"
                details = "Disabled"
            else:
                status = "❌ FAIL"
                details = "Connection failed"
            table.add_row(f"Target: {target}", status, details)
    else:
        table.add_row("Backup Targets", "⚠️  WARN", "None configured")
    
    # Local backup
    if local_result:
        status = "✅ PASS"
        details = "Directory accessible"
    else:
        status = "⏭️  SKIP"
        details = "Disabled or failed"
    table.add_row("Local Backup", status, details)
    
    # Notifications
    if notification_results:
        for notification, result in notification_results.items():
            if result == "success":
                status = "✅ PASS"
                details = "Configured"
            elif result == "disabled":
                status = "⏭️  SKIP"
                details = "Disabled"
            else:
                status = "❌ FAIL"
                details = "Configuration error"
            table.add_row(f"Notification: {notification}", status, details)
    else:
        table.add_row("Notifications", "⏭️  SKIP", "None configured")
    
    # Git
    status = "✅ PASS" if git_result else "❌ FAIL"
    table.add_row("Git", status, "Version control")
    
    console.print(table)
    
    # Overall status
    all_passed = (github_result and git_result and 
                  any(r == "success" for r in target_results.values()) if target_results else False)
    
    if all_passed:
        console.print("\n🎉 [bold green]All critical tests passed! Ready to run backups.[/bold green]")
    else:
        console.print("\n⚠️  [bold yellow]Some tests failed. Please fix issues before running backups.[/bold yellow]")

def main():
    """Main test function."""
    console.print(Panel.fit("GitHub Organization Backup - Connection Test", style="blue"))
    
    # Check if config file exists
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        console.print(f"[red]Configuration file not found: {config_path}[/red]")
        console.print("Please run the installation script first or create config.yaml")
        return 1
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Test GitHub connection
        github_result = test_github_connection(config)
        
        # Test backup targets
        target_results = test_backup_targets(config)
        
        # Test local backup
        local_result = test_local_backup(config)
        
        # Test notifications
        notification_results = test_notifications(config)
        
        # Test Git installation
        git_result = test_git_installation()
        
        # Display summary
        display_summary(github_result, target_results, local_result, notification_results, git_result)
        
        return 0 if github_result and git_result else 1
        
    except Exception as e:
        console.print(f"[red]Test failed with error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 