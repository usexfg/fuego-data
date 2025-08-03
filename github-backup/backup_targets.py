"""
Backup Targets Module
Handles backup operations to different Git hosting services including decentralized options.
"""

import os
import logging
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import gitlab
import requests
from git import Repo, GitCommandError
from datetime import datetime

class BackupTarget(ABC):
    """Abstract base class for backup targets."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = config.get('enabled', False)
    
    def is_enabled(self) -> bool:
        """Check if this backup target is enabled."""
        return self.enabled
    
    @abstractmethod
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to this target."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the target service."""
        pass
    
    def _get_token(self, token_key: str) -> str:
        """Get token from environment or config."""
        token = self.config.get(token_key, '')
        
        # Handle environment variable substitution
        if token.startswith('${') and token.endswith('}'):
            env_var = token[2:-1]
            token = os.getenv(env_var, '')
        
        return token

class GitLabBackupTarget(BackupTarget):
    """GitLab backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get('url', 'https://gitlab.com')
        self.token = self._get_token('token')
        self.group_id = config.get('group_id')
        self.create_mirrors = config.get('create_mirrors', True)
        
        if self.enabled and self.token:
            self.gl = gitlab.Gitlab(url=self.url, private_token=self.token)
    
    def test_connection(self) -> bool:
        """Test GitLab API connection."""
        try:
            if not self.enabled or not self.token:
                return False
            
            user = self.gl.user
            self.logger.info(f"Connected to GitLab as: {user.username}")
            return True
        except Exception as e:
            self.logger.error(f"GitLab connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to GitLab."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} to GitLab")
            
            # Check if repository already exists
            project = self._get_or_create_project(repo_data)
            
            if self.create_mirrors:
                # Set up mirror
                self._setup_mirror(project, repo_data)
            else:
                # Clone and push
                self._clone_and_push(project, repo_data)
            
            return {
                'status': 'success',
                'project_id': project.id,
                'project_url': project.web_url,
                'method': 'mirror' if self.create_mirrors else 'clone_push'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} to GitLab: {str(e)}")
            raise
    
    def _get_or_create_project(self, repo_data: Dict):
        """Get existing project or create new one."""
        repo_name = repo_data['name']
        
        try:
            # Try to find existing project
            if self.group_id:
                group = self.gl.groups.get(self.group_id)
                project = group.projects.get(repo_name)
                self.logger.info(f"Found existing GitLab project: {repo_name}")
                return project
        except gitlab.exceptions.GitlabGetError:
            pass
        
        # Create new project
        project_data = {
            'name': repo_name,
            'description': repo_data.get('description', ''),
            'visibility': 'private' if repo_data.get('private', False) else 'public',
            'import_url': repo_data['clone_url'],
            'mirror': self.create_mirrors
        }
        
        if self.group_id:
            group = self.gl.groups.get(self.group_id)
            project = group.projects.create(project_data)
        else:
            project = self.gl.projects.create(project_data)
        
        self.logger.info(f"Created new GitLab project: {repo_name}")
        return project
    
    def _setup_mirror(self, project, repo_data: Dict):
        """Set up GitLab mirror for the repository."""
        try:
            # Configure mirror settings
            mirror_data = {
                'url': repo_data['clone_url'],
                'enabled': True,
                'only_protected_branches': False,
                'keep_divergent_refs': True
            }
            
            project.remote_mirrors.create(mirror_data)
            self.logger.info(f"Mirror configured for {repo_data['name']}")
            
        except Exception as e:
            self.logger.warning(f"Failed to set up mirror for {repo_data['name']}: {str(e)}")
    
    def _clone_and_push(self, project, repo_data: Dict):
        """Clone repository and push to GitLab."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    # Use SSH URL for private repos if available
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Add GitLab as remote and push
                gitlab_url = project.http_url_to_repo
                repo.create_remote('gitlab', gitlab_url)
                
                # Push all branches and tags
                repo.remotes.gitlab.push('--all')
                repo.remotes.gitlab.push('--tags')
                
                self.logger.info(f"Successfully pushed {repo_data['name']} to GitLab")
                
            except GitCommandError as e:
                self.logger.error(f"Git operation failed for {repo_data['name']}: {str(e)}")
                raise

class GiteaBackupTarget(BackupTarget):
    """Gitea backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get('url')
        self.token = self._get_token('token')
        self.organization = config.get('organization')
        self.create_mirrors = config.get('create_mirrors', True)
    
    def test_connection(self) -> bool:
        """Test Gitea API connection."""
        try:
            if not self.enabled or not self.token or not self.url:
                return False
            
            headers = {'Authorization': f'token {self.token}'}
            response = requests.get(f"{self.url}/api/v1/user", headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            self.logger.info(f"Connected to Gitea as: {user_data['username']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Gitea connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to Gitea."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} to Gitea")
            
            # Check if repository exists
            existing_repo = self._get_repository(repo_name)
            
            if existing_repo:
                self.logger.info(f"Repository {repo_name} already exists in Gitea")
                if self.create_mirrors:
                    self._update_mirror(existing_repo['id'], repo_data)
            else:
                # Create new repository
                repo_id = self._create_repository(repo_data)
                if self.create_mirrors:
                    self._setup_mirror(repo_id, repo_data)
            
            return {
                'status': 'success',
                'repository_name': repo_name,
                'method': 'mirror' if self.create_mirrors else 'clone_push'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} to Gitea: {str(e)}")
            raise
    
    def _get_repository(self, repo_name: str) -> Optional[Dict]:
        """Get repository from Gitea."""
        try:
            headers = {'Authorization': f'token {self.token}'}
            url = f"{self.url}/api/v1/repos/{self.organization}/{repo_name}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting repository {repo_name}: {str(e)}")
            return None
    
    def _create_repository(self, repo_data: Dict) -> int:
        """Create new repository in Gitea."""
        headers = {'Authorization': f'token {self.token}'}
        data = {
            'name': repo_data['name'],
            'description': repo_data.get('description', ''),
            'private': repo_data.get('private', False),
            'auto_init': False
        }
        
        url = f"{self.url}/api/v1/orgs/{self.organization}/repos"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        repo_info = response.json()
        self.logger.info(f"Created Gitea repository: {repo_data['name']}")
        return repo_info['id']
    
    def _setup_mirror(self, repo_id: int, repo_data: Dict):
        """Set up Gitea mirror."""
        try:
            headers = {'Authorization': f'token {self.token}'}
            data = {
                'mirror': True,
                'mirror_interval': '8h',
                'clone_addr': repo_data['clone_url']
            }
            
            url = f"{self.url}/api/v1/repositories/{repo_id}"
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            
            self.logger.info(f"Mirror configured for {repo_data['name']}")
            
        except Exception as e:
            self.logger.warning(f"Failed to set up mirror for {repo_data['name']}: {str(e)}")
    
    def _update_mirror(self, repo_id: int, repo_data: Dict):
        """Update existing mirror."""
        try:
            headers = {'Authorization': f'token {self.token}'}
            url = f"{self.url}/api/v1/repos/{self.organization}/{repo_data['name']}/mirror-sync"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            self.logger.info(f"Mirror sync triggered for {repo_data['name']}")
            
        except Exception as e:
            self.logger.warning(f"Failed to sync mirror for {repo_data['name']}: {str(e)}")

class BitbucketBackupTarget(BackupTarget):
    """Bitbucket backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get('url', 'https://api.bitbucket.org')
        self.username = self._get_token('username')
        self.app_password = self._get_token('app_password')
        self.workspace = config.get('workspace')
        self.create_mirrors = config.get('create_mirrors', True)
    
    def test_connection(self) -> bool:
        """Test Bitbucket API connection."""
        try:
            if not self.enabled or not self.username or not self.app_password:
                return False
            
            auth = (self.username, self.app_password)
            response = requests.get(f"{self.url}/2.0/user", auth=auth)
            response.raise_for_status()
            
            user_data = response.json()
            self.logger.info(f"Connected to Bitbucket as: {user_data['username']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Bitbucket connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to Bitbucket."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} to Bitbucket")
            
            # Check if repository exists
            existing_repo = self._get_repository(repo_name)
            
            if existing_repo:
                self.logger.info(f"Repository {repo_name} already exists in Bitbucket")
            else:
                # Create new repository
                self._create_repository(repo_data)
            
            # Clone and push (Bitbucket doesn't have built-in mirrors)
            self._clone_and_push(repo_name, repo_data)
            
            return {
                'status': 'success',
                'repository_name': repo_name,
                'method': 'clone_push'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} to Bitbucket: {str(e)}")
            raise
    
    def _get_repository(self, repo_name: str) -> Optional[Dict]:
        """Get repository from Bitbucket."""
        try:
            auth = (self.username, self.app_password)
            url = f"{self.url}/2.0/repositories/{self.workspace}/{repo_name}"
            response = requests.get(url, auth=auth)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting repository {repo_name}: {str(e)}")
            return None
    
    def _create_repository(self, repo_data: Dict):
        """Create new repository in Bitbucket."""
        auth = (self.username, self.app_password)
        data = {
            'name': repo_data['name'],
            'description': repo_data.get('description', ''),
            'is_private': repo_data.get('private', False),
            'scm': 'git'
        }
        
        url = f"{self.url}/2.0/repositories/{self.workspace}/{repo_data['name']}"
        response = requests.post(url, auth=auth, json=data)
        response.raise_for_status()
        
        self.logger.info(f"Created Bitbucket repository: {repo_data['name']}")
    
    def _clone_and_push(self, repo_name: str, repo_data: Dict):
        """Clone repository and push to Bitbucket."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Add Bitbucket as remote and push
                bitbucket_url = f"https://{self.username}:{self.app_password}@bitbucket.org/{self.workspace}/{repo_name}.git"
                repo.create_remote('bitbucket', bitbucket_url)
                
                # Push all branches and tags
                repo.remotes.bitbucket.push('--all')
                repo.remotes.bitbucket.push('--tags')
                
                self.logger.info(f"Successfully pushed {repo_name} to Bitbucket")
                
            except GitCommandError as e:
                self.logger.error(f"Git operation failed for {repo_name}: {str(e)}")
                raise

class LocalBackupTarget(BackupTarget):
    """Local backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.backup_path = config.get('path', './backups')
        self.keep_versions = config.get('keep_versions', 5)
        self.compress = config.get('compress', True)
        
        # Ensure backup directory exists
        if self.enabled:
            os.makedirs(self.backup_path, exist_ok=True)
    
    def test_connection(self) -> bool:
        """Test local backup directory access."""
        try:
            if not self.enabled:
                return False
            
            test_file = os.path.join(self.backup_path, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            self.logger.info(f"Local backup directory accessible: {self.backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Local backup directory not accessible: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Create local backup of repository."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Creating local backup of {repo_name}")
            
            # Create timestamped backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.backup_path, f"{repo_name}_{timestamp}")
            
            # Clone repository
            repo_url = repo_data['clone_url']
            if repo_data.get('private', False):
                repo_url = repo_data.get('ssh_url', repo_url)
            
            repo = Repo.clone_from(repo_url, backup_dir)
            
            # Compress if enabled
            if self.compress:
                compressed_path = f"{backup_dir}.tar.gz"
                shutil.make_archive(backup_dir, 'gztar', backup_dir)
                shutil.rmtree(backup_dir)
                backup_path = compressed_path
            else:
                backup_path = backup_dir
            
            # Clean up old versions
            self._cleanup_old_versions(repo_name)
            
            return {
                'status': 'success',
                'backup_path': backup_path,
                'method': 'local_clone'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create local backup of {repo_data['name']}: {str(e)}")
            raise
    
    def _cleanup_old_versions(self, repo_name: str):
        """Remove old backup versions beyond keep_versions limit."""
        try:
            pattern = f"{repo_name}_*"
            if self.compress:
                pattern += ".tar.gz"
            
            backups = []
            for item in os.listdir(self.backup_path):
                if item.startswith(f"{repo_name}_") and (self.compress and item.endswith('.tar.gz') or not self.compress):
                    backups.append(item)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: os.path.getctime(os.path.join(self.backup_path, x)), reverse=True)
            
            # Remove old versions
            for old_backup in backups[self.keep_versions:]:
                old_path = os.path.join(self.backup_path, old_backup)
                if os.path.isfile(old_path):
                    os.remove(old_path)
                elif os.path.isdir(old_path):
                    shutil.rmtree(old_path)
                self.logger.info(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old versions for {repo_name}: {str(e)}")

class RadicleBackupTarget(BackupTarget):
    """Radicle decentralized Git backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.rad_home = config.get('rad_home', os.path.expanduser('~/.rad'))
        self.node_id = config.get('node_id')
        self.seed_nodes = config.get('seed_nodes', [])
        self.create_project = config.get('create_project', True)
    
    def test_connection(self) -> bool:
        """Test Radicle connection and node status."""
        try:
            if not self.enabled:
                return False
            
            # Check if rad CLI is installed
            result = subprocess.run(['rad', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info(f"Radicle CLI found: {result.stdout.strip()}")
            
            # Check node status
            result = subprocess.run(['rad', 'node', 'status'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info("Radicle node is running")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Radicle connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to Radicle."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} to Radicle")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Initialize Radicle project
                if self.create_project:
                    self._create_radicle_project(temp_dir, repo_data)
                else:
                    # Push to existing project
                    self._push_to_radicle_project(temp_dir, repo_data)
                
                return {
                    'status': 'success',
                    'repository_name': repo_name,
                    'method': 'radicle_push',
                    'node_id': self.node_id
                }
                
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} to Radicle: {str(e)}")
            raise
    
    def _create_radicle_project(self, repo_path: str, repo_data: Dict):
        """Create a new Radicle project."""
        try:
            # Initialize Radicle project
            subprocess.run(['rad', 'init', '--name', repo_data['name']], 
                         cwd=repo_path, check=True)
            
            # Set description
            if repo_data.get('description'):
                subprocess.run(['rad', 'patch', '--message', repo_data['description']], 
                             cwd=repo_path, check=True)
            
            # Push to network
            subprocess.run(['rad', 'push'], cwd=repo_path, check=True)
            
            self.logger.info(f"Created Radicle project: {repo_data['name']}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create Radicle project: {str(e)}")
            raise
    
    def _push_to_radicle_project(self, repo_path: str, repo_data: Dict):
        """Push to existing Radicle project."""
        try:
            # Add Radicle remote
            project_id = self._get_project_id(repo_data['name'])
            if project_id:
                subprocess.run(['rad', 'remote', 'add', 'rad', project_id], 
                             cwd=repo_path, check=True)
                subprocess.run(['rad', 'push'], cwd=repo_path, check=True)
            else:
                self.logger.warning(f"Radicle project not found: {repo_data['name']}")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push to Radicle project: {str(e)}")
            raise
    
    def _get_project_id(self, repo_name: str) -> Optional[str]:
        """Get Radicle project ID by name."""
        try:
            result = subprocess.run(['rad', 'ls'], 
                                  capture_output=True, text=True, check=True)
            # Parse output to find project ID
            for line in result.stdout.split('\n'):
                if repo_name in line:
                    return line.split()[0]  # Assuming first column is project ID
            return None
        except subprocess.CalledProcessError:
            return None

class GitTorrentBackupTarget(BackupTarget):
    """GitTorrent decentralized backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.tracker_url = config.get('tracker_url', 'http://localhost:6881')
        self.port = config.get('port', 6882)
        self.upload_limit = config.get('upload_limit', 0)  # 0 = unlimited
    
    def test_connection(self) -> bool:
        """Test GitTorrent setup."""
        try:
            if not self.enabled:
                return False
            
            # Check if git-torrent is installed
            result = subprocess.run(['git-torrent', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info(f"GitTorrent found: {result.stdout.strip()}")
            
            # Test tracker connection
            response = requests.get(f"{self.tracker_url}/announce", timeout=5)
            if response.status_code == 200:
                self.logger.info("GitTorrent tracker is accessible")
                return True
            else:
                self.logger.warning("GitTorrent tracker returned non-200 status")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError, requests.RequestException) as e:
            self.logger.error(f"GitTorrent connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository using GitTorrent."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} using GitTorrent")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Create GitTorrent bundle
                torrent_file = self._create_torrent_bundle(temp_dir, repo_data)
                
                # Upload to tracker
                self._upload_to_tracker(torrent_file, repo_data)
                
                return {
                    'status': 'success',
                    'repository_name': repo_name,
                    'method': 'gittorrent_bundle',
                    'torrent_file': torrent_file
                }
                
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} with GitTorrent: {str(e)}")
            raise
    
    def _create_torrent_bundle(self, repo_path: str, repo_data: Dict) -> str:
        """Create GitTorrent bundle from repository."""
        try:
            bundle_name = f"{repo_data['name']}.bundle"
            bundle_path = os.path.join(repo_path, bundle_name)
            
            # Create Git bundle
            subprocess.run(['git', 'bundle', 'create', bundle_path, '--all'], 
                         cwd=repo_path, check=True)
            
            # Create torrent file
            torrent_file = f"{bundle_path}.torrent"
            subprocess.run([
                'git-torrent', 'create',
                '--tracker', self.tracker_url,
                '--port', str(self.port),
                '--name', repo_data['name'],
                '--comment', repo_data.get('description', ''),
                bundle_path, torrent_file
            ], cwd=repo_path, check=True)
            
            return torrent_file
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create torrent bundle: {str(e)}")
            raise
    
    def _upload_to_tracker(self, torrent_file: str, repo_data: Dict):
        """Upload torrent to tracker."""
        try:
            with open(torrent_file, 'rb') as f:
                files = {'torrent': f}
                response = requests.post(f"{self.tracker_url}/upload", files=files)
                response.raise_for_status()
                
            self.logger.info(f"Uploaded torrent for {repo_data['name']}")
            
        except (requests.RequestException, IOError) as e:
            self.logger.error(f"Failed to upload torrent: {str(e)}")
            raise

class IPFSBackupTarget(BackupTarget):
    """IPFS decentralized backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.ipfs_api_url = config.get('api_url', 'http://localhost:5001')
        self.ipfs_gateway = config.get('gateway_url', 'https://ipfs.io')
        self.pin_on_upload = config.get('pin_on_upload', True)
        self.compression = config.get('compression', True)
    
    def test_connection(self) -> bool:
        """Test IPFS connection."""
        try:
            if not self.enabled:
                return False
            
            # Check if IPFS daemon is running
            response = requests.post(f"{self.ipfs_api_url}/api/v0/version", timeout=5)
            response.raise_for_status()
            
            version_info = response.json()
            self.logger.info(f"IPFS daemon running: {version_info.get('Version', 'Unknown')}")
            
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"IPFS connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository to IPFS."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} to IPFS")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Create archive
                archive_path = self._create_archive(temp_dir, repo_data)
                
                # Upload to IPFS
                ipfs_hash = self._upload_to_ipfs(archive_path, repo_data)
                
                # Pin if configured
                if self.pin_on_upload:
                    self._pin_content(ipfs_hash)
                
                return {
                    'status': 'success',
                    'repository_name': repo_name,
                    'method': 'ipfs_archive',
                    'ipfs_hash': ipfs_hash,
                    'gateway_url': f"{self.ipfs_gateway}/ipfs/{ipfs_hash}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} to IPFS: {str(e)}")
            raise
    
    def _create_archive(self, repo_path: str, repo_data: Dict) -> str:
        """Create compressed archive of repository."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"{repo_data['name']}_{timestamp}.tar.gz"
            archive_path = os.path.join(repo_path, archive_name)
            
            if self.compression:
                shutil.make_archive(
                    os.path.splitext(archive_path)[0], 
                    'gztar', 
                    repo_path
                )
            else:
                shutil.make_archive(
                    os.path.splitext(archive_path)[0], 
                    'tar', 
                    repo_path
                )
            
            return archive_path
            
        except Exception as e:
            self.logger.error(f"Failed to create archive: {str(e)}")
            raise
    
    def _upload_to_ipfs(self, file_path: str, repo_data: Dict) -> str:
        """Upload file to IPFS."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.ipfs_api_url}/api/v0/add", files=files)
                response.raise_for_status()
            
            result = response.json()
            ipfs_hash = result['Hash']
            
            self.logger.info(f"Uploaded {repo_data['name']} to IPFS: {ipfs_hash}")
            return ipfs_hash
            
        except (requests.RequestException, IOError) as e:
            self.logger.error(f"Failed to upload to IPFS: {str(e)}")
            raise
    
    def _pin_content(self, ipfs_hash: str):
        """Pin content in IPFS."""
        try:
            response = requests.post(f"{self.ipfs_api_url}/api/v0/pin/add", 
                                   params={'arg': ipfs_hash})
            response.raise_for_status()
            
            self.logger.info(f"Pinned content: {ipfs_hash}")
            
        except requests.RequestException as e:
            self.logger.warning(f"Failed to pin content: {str(e)}")

class DatBackupTarget(BackupTarget):
    """Dat protocol backup target implementation."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.dat_path = config.get('dat_path', os.path.expanduser('~/.dat'))
        self.create_archive = config.get('create_archive', True)
        self.share_key = config.get('share_key')
    
    def test_connection(self) -> bool:
        """Test Dat protocol setup."""
        try:
            if not self.enabled:
                return False
            
            # Check if dat CLI is installed
            result = subprocess.run(['dat', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info(f"Dat CLI found: {result.stdout.strip()}")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Dat connection failed: {str(e)}")
            return False
    
    def backup_repository(self, repo_data: Dict) -> Dict:
        """Backup a repository using Dat protocol."""
        try:
            repo_name = repo_data['name']
            self.logger.info(f"Backing up {repo_name} using Dat protocol")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone from GitHub
                repo_url = repo_data['clone_url']
                if repo_data.get('private', False):
                    repo_url = repo_data.get('ssh_url', repo_url)
                
                repo = Repo.clone_from(repo_url, temp_dir)
                
                # Create Dat archive
                dat_key = self._create_dat_archive(temp_dir, repo_data)
                
                return {
                    'status': 'success',
                    'repository_name': repo_name,
                    'method': 'dat_archive',
                    'dat_key': dat_key,
                    'dat_url': f"dat://{dat_key}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to backup {repo_data['name']} with Dat: {str(e)}")
            raise
    
    def _create_dat_archive(self, repo_path: str, repo_data: Dict) -> str:
        """Create Dat archive from repository."""
        try:
            # Initialize Dat archive
            subprocess.run(['dat', 'init'], cwd=repo_path, check=True)
            
            # Add all files
            subprocess.run(['dat', 'add', '.'], cwd=repo_path, check=True)
            
            # Create initial version
            subprocess.run(['dat', 'commit', '-m', f"Initial backup of {repo_data['name']}"], 
                         cwd=repo_path, check=True)
            
            # Get the archive key
            result = subprocess.run(['dat', 'keys'], 
                                  cwd=repo_path, capture_output=True, text=True, check=True)
            
            # Parse the key from output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'dat://' in line:
                    key = line.split('dat://')[1].strip()
                    self.logger.info(f"Created Dat archive: {key}")
                    return key
            
            raise Exception("Could not retrieve Dat archive key")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create Dat archive: {str(e)}")
            raise

class BackupTargetFactory:
    """Factory for creating backup targets."""
    
    @staticmethod
    def create_targets(config: Dict) -> Dict[str, BackupTarget]:
        """Create backup targets based on configuration."""
        targets = {}
        
        # Centralized targets
        if 'gitlab' in config:
            targets['gitlab'] = GitLabBackupTarget(config['gitlab'])
        
        if 'gitea' in config:
            targets['gitea'] = GiteaBackupTarget(config['gitea'])
        
        if 'bitbucket' in config:
            targets['bitbucket'] = BitbucketBackupTarget(config['bitbucket'])
        
        # Decentralized targets
        if 'radicle' in config:
            targets['radicle'] = RadicleBackupTarget(config['radicle'])
        
        if 'gittorrent' in config:
            targets['gittorrent'] = GitTorrentBackupTarget(config['gittorrent'])
        
        if 'ipfs' in config:
            targets['ipfs'] = IPFSBackupTarget(config['ipfs'])
        
        if 'dat' in config:
            targets['dat'] = DatBackupTarget(config['dat'])
        
        # Local backup
        if 'local_backup' in config:
            targets['local'] = LocalBackupTarget(config['local_backup'])
        
        return targets 