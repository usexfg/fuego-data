"""
GitHub Backup Module
Handles GitHub API interactions and repository discovery for organization backups.
"""

import os
import re
import logging
from typing import Dict, List, Optional
from github import Github, GithubException
from github.Repository import Repository
from github.Organization import Organization

class GitHubBackup:
    """Handles GitHub organization repository discovery and metadata extraction."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize GitHub client
        token = self._get_token()
        api_url = config.get('api_url', 'https://api.github.com')
        
        if api_url != 'https://api.github.com':
            # GitHub Enterprise
            self.github = Github(base_url=api_url, login_or_token=token)
        else:
            self.github = Github(token)
        
        self.organization_name = config['organization']
        self.organization = self.github.get_organization(self.organization_name)
    
    def _get_token(self) -> str:
        """Get GitHub token from environment or config."""
        token = self.config.get('token', '')
        
        # Handle environment variable substitution
        if token.startswith('${') and token.endswith('}'):
            env_var = token[2:-1]
            token = os.getenv(env_var, '')
        
        if not token:
            raise ValueError("GitHub token not found. Set GITHUB_TOKEN environment variable or configure in config.yaml")
        
        return token
    
    def get_repositories(self, 
                        include_private: bool = True,
                        include_archived: bool = False,
                        include_forks: bool = False,
                        exclude_patterns: List[str] = None,
                        include_patterns: List[str] = None) -> List[Dict]:
        """
        Get list of repositories from the organization based on filters.
        
        Args:
            include_private: Include private repositories
            include_archived: Include archived repositories
            include_forks: Include forked repositories
            exclude_patterns: List of regex patterns to exclude repositories
            include_patterns: List of regex patterns to include repositories (if empty, include all)
        
        Returns:
            List of repository dictionaries with metadata
        """
        self.logger.info(f"Fetching repositories from organization: {self.organization_name}")
        
        repositories = []
        exclude_patterns = exclude_patterns or []
        include_patterns = include_patterns or []
        
        try:
            # Get all repositories from the organization
            for repo in self.organization.get_repos():
                repo_data = self._extract_repository_data(repo)
                
                # Apply filters
                if not self._should_include_repository(repo_data, 
                                                      include_private, 
                                                      include_archived, 
                                                      include_forks,
                                                      exclude_patterns,
                                                      include_patterns):
                    continue
                
                repositories.append(repo_data)
                self.logger.debug(f"Added repository: {repo_data['name']}")
            
            self.logger.info(f"Found {len(repositories)} repositories matching criteria")
            return repositories
            
        except GithubException as e:
            self.logger.error(f"GitHub API error: {str(e)}")
            raise
    
    def _extract_repository_data(self, repo: Repository) -> Dict:
        """Extract relevant data from a GitHub repository object."""
        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description or '',
            'private': repo.private,
            'archived': repo.archived,
            'fork': repo.fork,
            'default_branch': repo.default_branch,
            'clone_url': repo.clone_url,
            'ssh_url': repo.ssh_url,
            'html_url': repo.html_url,
            'language': repo.language,
            'size': repo.size,
            'stargazers_count': repo.stargazers_count,
            'forks_count': repo.forks_count,
            'open_issues_count': repo.open_issues_count,
            'created_at': repo.created_at.isoformat() if repo.created_at else None,
            'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
            'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None,
            'topics': list(repo.get_topics()) if hasattr(repo, 'get_topics') else [],
            'license': repo.license.name if repo.license else None,
            'has_wiki': repo.has_wiki,
            'has_issues': repo.has_issues,
            'has_projects': repo.has_projects,
            'has_downloads': repo.has_downloads,
            'allow_squash_merge': repo.allow_squash_merge,
            'allow_merge_commit': repo.allow_merge_commit,
            'allow_rebase_merge': repo.allow_rebase_merge,
            'delete_branch_on_merge': repo.delete_branch_on_merge,
            'web_commit_signoff_required': repo.web_commit_signoff_required,
            'visibility': repo.visibility if hasattr(repo, 'visibility') else ('private' if repo.private else 'public')
        }
    
    def _should_include_repository(self, 
                                  repo_data: Dict,
                                  include_private: bool,
                                  include_archived: bool,
                                  include_forks: bool,
                                  exclude_patterns: List[str],
                                  include_patterns: List[str]) -> bool:
        """Determine if a repository should be included based on filters."""
        repo_name = repo_data['name']
        
        # Check visibility
        if repo_data['private'] and not include_private:
            return False
        
        # Check archived status
        if repo_data['archived'] and not include_archived:
            return False
        
        # Check fork status
        if repo_data['fork'] and not include_forks:
            return False
        
        # Check exclude patterns
        for pattern in exclude_patterns:
            if re.match(pattern, repo_name):
                self.logger.debug(f"Excluding {repo_name} due to pattern: {pattern}")
                return False
        
        # Check include patterns (if specified)
        if include_patterns:
            for pattern in include_patterns:
                if re.match(pattern, repo_name):
                    return True
            # If include patterns are specified but none match, exclude
            self.logger.debug(f"Excluding {repo_name} - no include pattern matched")
            return False
        
        return True
    
    def get_repository_branches(self, repo_name: str) -> List[str]:
        """Get list of branches for a specific repository."""
        try:
            repo = self.organization.get_repo(repo_name)
            branches = [branch.name for branch in repo.get_branches()]
            return branches
        except GithubException as e:
            self.logger.error(f"Error getting branches for {repo_name}: {str(e)}")
            return []
    
    def get_repository_tags(self, repo_name: str) -> List[Dict]:
        """Get list of tags for a specific repository."""
        try:
            repo = self.organization.get_repo(repo_name)
            tags = []
            for tag in repo.get_tags():
                tags.append({
                    'name': tag.name,
                    'commit_sha': tag.commit.sha,
                    'created_at': tag.commit.commit.author.date.isoformat() if tag.commit.commit.author.date else None
                })
            return tags
        except GithubException as e:
            self.logger.error(f"Error getting tags for {repo_name}: {str(e)}")
            return []
    
    def get_repository_webhooks(self, repo_name: str) -> List[Dict]:
        """Get list of webhooks for a specific repository."""
        try:
            repo = self.organization.get_repo(repo_name)
            webhooks = []
            for webhook in repo.get_hooks():
                webhooks.append({
                    'id': webhook.id,
                    'name': webhook.name,
                    'url': webhook.config.get('url', ''),
                    'events': list(webhook.events),
                    'active': webhook.active
                })
            return webhooks
        except GithubException as e:
            self.logger.error(f"Error getting webhooks for {repo_name}: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """Test the GitHub API connection."""
        try:
            # Try to access the organization
            org_name = self.organization.name
            self.logger.info(f"Successfully connected to GitHub organization: {org_name}")
            return True
        except GithubException as e:
            self.logger.error(f"Failed to connect to GitHub: {str(e)}")
            return False
    
    def get_organization_info(self) -> Dict:
        """Get organization information."""
        try:
            return {
                'name': self.organization.name,
                'login': self.organization.login,
                'description': self.organization.description or '',
                'public_repos': self.organization.public_repos,
                'total_private_repos': self.organization.total_private_repos,
                'created_at': self.organization.created_at.isoformat() if self.organization.created_at else None,
                'updated_at': self.organization.updated_at.isoformat() if self.organization.updated_at else None,
                'html_url': self.organization.html_url,
                'avatar_url': self.organization.avatar_url,
                'billing_email': self.organization.billing_email if hasattr(self.organization, 'billing_email') else None,
                'plan': self.organization.plan.name if self.organization.plan else None
            }
        except GithubException as e:
            self.logger.error(f"Error getting organization info: {str(e)}")
            return {} 