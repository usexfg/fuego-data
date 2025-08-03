#!/usr/bin/env python3
"""
GitHub Organization Backup System
Main script to backup all repositories in a GitHub organization to multiple Git hosting services.
"""

import os
import sys
import yaml
import logging
import click
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import schedule
import time

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from dotenv import load_dotenv

from github_backup import GitHubBackup
from backup_targets import BackupTargetFactory
from notification_manager import NotificationManager
from utils import setup_logging, load_config, validate_config

# Load environment variables
load_dotenv()

console = Console()

class OrganizationBackup:
    """Main class to handle organization-wide repository backups."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config.get('logging', {}))
        self.github_backup = GitHubBackup(self.config['github'])
        self.notification_manager = NotificationManager(self.config.get('notifications', {}))
        self.backup_targets = BackupTargetFactory.create_targets(self.config.get('backup_targets', {}))
        
    def get_repositories(self) -> List[Dict]:
        """Get list of repositories to backup based on configuration."""
        filters = self.config.get('repositories', {})
        return self.github_backup.get_repositories(
            include_private=filters.get('include_private', True),
            include_archived=filters.get('include_archived', False),
            include_forks=filters.get('include_forks', False),
            exclude_patterns=filters.get('exclude_patterns', []),
            include_patterns=filters.get('include_patterns', [])
        )
    
    def backup_repository(self, repo: Dict, target_name: str, target) -> Dict:
        """Backup a single repository to a specific target."""
        try:
            self.logger.info(f"Backing up {repo['name']} to {target_name}")
            result = target.backup_repository(repo)
            return {
                'repository': repo['name'],
                'target': target_name,
                'status': 'success',
                'result': result
            }
        except Exception as e:
            self.logger.error(f"Failed to backup {repo['name']} to {target_name}: {str(e)}")
            return {
                'repository': repo['name'],
                'target': target_name,
                'status': 'error',
                'error': str(e)
            }
    
    def run_backup(self, dry_run: bool = False) -> Dict:
        """Run the complete backup process."""
        start_time = datetime.now()
        self.logger.info("Starting organization backup")
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No actual backups will be performed[/yellow]")
        
        # Get repositories to backup
        repositories = self.get_repositories()
        self.logger.info(f"Found {len(repositories)} repositories to backup")
        
        if not repositories:
            console.print("[red]No repositories found to backup[/red]")
            return {'status': 'no_repositories'}
        
        # Prepare backup tasks
        backup_tasks = []
        for repo in repositories:
            for target_name, target in self.backup_targets.items():
                if target.is_enabled():
                    backup_tasks.append((repo, target_name, target))
        
        if not backup_tasks:
            console.print("[red]No backup targets configured[/red]")
            return {'status': 'no_targets'}
        
        # Execute backups
        results = []
        max_workers = self.config.get('performance', {}).get('max_concurrent_backups', 5)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Backing up repositories...", total=len(backup_tasks))
            
            if dry_run:
                # Simulate backup process
                for repo, target_name, target in backup_tasks:
                    progress.update(task, description=f"Would backup {repo['name']} to {target_name}")
                    results.append({
                        'repository': repo['name'],
                        'target': target_name,
                        'status': 'dry_run',
                        'result': 'Simulated backup'
                    })
                    progress.advance(task)
            else:
                # Execute actual backups
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_task = {
                        executor.submit(self.backup_repository, repo, target_name, target): (repo, target_name)
                        for repo, target_name, target in backup_tasks
                    }
                    
                    for future in as_completed(future_to_task):
                        repo, target_name = future_to_task[future]
                        try:
                            result = future.result()
                            results.append(result)
                            progress.update(task, description=f"Completed {repo['name']} -> {target_name}")
                        except Exception as e:
                            results.append({
                                'repository': repo['name'],
                                'target': target_name,
                                'status': 'error',
                                'error': str(e)
                            })
                        progress.advance(task)
        
        # Generate summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        summary = self.generate_summary(results, duration)
        self.display_summary(summary)
        
        # Send notifications
        if not dry_run:
            self.notification_manager.send_backup_summary(summary)
        
        return summary
    
    def generate_summary(self, results: List[Dict], duration: timedelta) -> Dict:
        """Generate a summary of the backup results."""
        total = len(results)
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'error'])
        dry_run_count = len([r for r in results if r['status'] == 'dry_run'])
        
        # Group by target
        target_summary = {}
        for result in results:
            target = result['target']
            if target not in target_summary:
                target_summary[target] = {'success': 0, 'failed': 0, 'dry_run': 0}
            
            if result['status'] == 'success':
                target_summary[target]['success'] += 1
            elif result['status'] == 'error':
                target_summary[target]['failed'] += 1
            elif result['status'] == 'dry_run':
                target_summary[target]['dry_run'] += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration.total_seconds(),
            'total_backups': total,
            'successful': successful,
            'failed': failed,
            'dry_run': dry_run_count,
            'target_summary': target_summary,
            'results': results
        }
    
    def display_summary(self, summary: Dict):
        """Display a formatted summary of the backup results."""
        console.print("\n" + "="*60)
        console.print("[bold blue]BACKUP SUMMARY[/bold blue]")
        console.print("="*60)
        
        # Overall statistics
        table = Table(title="Overall Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Backups", str(summary['total_backups']))
        table.add_row("Successful", f"[green]{summary['successful']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed']}[/red]")
        if summary['dry_run'] > 0:
            table.add_row("Dry Run", f"[yellow]{summary['dry_run']}[/yellow]")
        table.add_row("Duration", f"{summary['duration_seconds']:.2f} seconds")
        
        console.print(table)
        
        # Target breakdown
        if summary['target_summary']:
            console.print("\n[bold]Target Breakdown:[/bold]")
            target_table = Table()
            target_table.add_column("Target", style="cyan")
            target_table.add_column("Successful", style="green")
            target_table.add_column("Failed", style="red")
            target_table.add_column("Dry Run", style="yellow")
            
            for target, stats in summary['target_summary'].items():
                target_table.add_row(
                    target,
                    str(stats['success']),
                    str(stats['failed']),
                    str(stats['dry_run'])
                )
            
            console.print(target_table)
        
        # Failed backups
        failed_backups = [r for r in summary['results'] if r['status'] == 'error']
        if failed_backups:
            console.print(f"\n[bold red]Failed Backups ({len(failed_backups)}):[/bold red]")
            for backup in failed_backups:
                console.print(f"  • {backup['repository']} -> {backup['target']}: {backup['error']}")
    
    def run_scheduled_backup(self):
        """Run scheduled backup (for use with schedule library)."""
        try:
            self.run_backup()
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {str(e)}")
            self.notification_manager.send_error_notification(f"Scheduled backup failed: {str(e)}")
    
    def start_scheduler(self):
        """Start the scheduled backup service."""
        # Schedule backups based on configuration
        for target_name, target_config in self.config.get('backup_targets', {}).items():
            if target_config.get('enabled', False):
                interval_hours = target_config.get('sync_interval_hours', 24)
                schedule.every(interval_hours).hours.do(self.run_scheduled_backup)
                self.logger.info(f"Scheduled backup every {interval_hours} hours for {target_name}")
        
        console.print("[green]Scheduler started. Press Ctrl+C to stop.[/green]")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            console.print("\n[yellow]Scheduler stopped by user[/yellow]")

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Perform a dry run without actual backups')
@click.option('--schedule', is_flag=True, help='Start the scheduled backup service')
@click.option('--list-repos', is_flag=True, help='List repositories that would be backed up')
def main(config: str, dry_run: bool, schedule: bool, list_repos: bool):
    """GitHub Organization Backup Tool"""
    
    try:
        # Validate configuration
        if not os.path.exists(config):
            console.print(f"[red]Configuration file not found: {config}[/red]")
            sys.exit(1)
        
        # Initialize backup system
        backup_system = OrganizationBackup(config)
        
        if list_repos:
            # List repositories
            repos = backup_system.get_repositories()
            console.print(f"\n[bold]Repositories to backup ({len(repos)}):[/bold]")
            for repo in repos:
                visibility = "🔒" if repo['private'] else "🌐"
                archived = "📦" if repo['archived'] else ""
                console.print(f"  {visibility} {repo['name']} {archived}")
            return
        
        if schedule:
            # Start scheduled backup service
            backup_system.start_scheduler()
        else:
            # Run single backup
            backup_system.run_backup(dry_run=dry_run)
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 