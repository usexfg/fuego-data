"""
Utilities Module
Helper functions for configuration, logging, and validation.
"""

import os
import yaml
import logging
import logging.handlers
from typing import Dict, Any, Optional
from pathlib import Path

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if not config:
        raise ValueError("Configuration file is empty or invalid")
    
    return config

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        config: Logging configuration dictionary
        
    Returns:
        Configured logger instance
    """
    # Get logging configuration
    level = getattr(logging, config.get('level', 'INFO').upper())
    log_file = config.get('file', 'backup.log')
    max_size = config.get('max_size_mb', 100) * 1024 * 1024  # Convert to bytes
    backup_count = config.get('backup_count', 5)
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration structure and required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    # Check required top-level sections
    required_sections = ['github']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate GitHub configuration
    github_config = config['github']
    if 'organization' not in github_config:
        raise ValueError("GitHub organization name is required")
    
    if 'token' not in github_config:
        raise ValueError("GitHub token is required")
    
    # Validate backup targets
    backup_targets = config.get('backup_targets', {})
    if not backup_targets:
        raise ValueError("At least one backup target must be configured")
    
    # Check if any target is enabled
    enabled_targets = []
    for target_name, target_config in backup_targets.items():
        if target_config.get('enabled', False):
            enabled_targets.append(target_name)
    
    if not enabled_targets:
        raise ValueError("At least one backup target must be enabled")
    
    # Validate specific target configurations
    for target_name, target_config in backup_targets.items():
        if target_config.get('enabled', False):
            validate_target_config(target_name, target_config)
    
    return True

def validate_target_config(target_name: str, config: Dict[str, Any]):
    """
    Validate configuration for a specific backup target.
    
    Args:
        target_name: Name of the backup target
        config: Target configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    if target_name == 'gitlab':
        if not config.get('token'):
            raise ValueError("GitLab token is required when GitLab backup is enabled")
        if not config.get('group_id'):
            raise ValueError("GitLab group ID is required when GitLab backup is enabled")
    
    elif target_name == 'gitea':
        if not config.get('token'):
            raise ValueError("Gitea token is required when Gitea backup is enabled")
        if not config.get('url'):
            raise ValueError("Gitea URL is required when Gitea backup is enabled")
        if not config.get('organization'):
            raise ValueError("Gitea organization is required when Gitea backup is enabled")
    
    elif target_name == 'bitbucket':
        if not config.get('username'):
            raise ValueError("Bitbucket username is required when Bitbucket backup is enabled")
        if not config.get('app_password'):
            raise ValueError("Bitbucket app password is required when Bitbucket backup is enabled")
        if not config.get('workspace'):
            raise ValueError("Bitbucket workspace is required when Bitbucket backup is enabled")
    
    elif target_name == 'local_backup':
        backup_path = config.get('path', './backups')
        if not os.path.exists(backup_path):
            try:
                os.makedirs(backup_path, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create local backup directory {backup_path}: {str(e)}")

def resolve_environment_variables(value: str) -> str:
    """
    Resolve environment variable references in configuration values.
    
    Args:
        value: Configuration value that may contain environment variable references
        
    Returns:
        Resolved value with environment variables substituted
    """
    if not isinstance(value, str):
        return value
    
    if value.startswith('${') and value.endswith('}'):
        env_var = value[2:-1]
        resolved = os.getenv(env_var, '')
        if not resolved:
            raise ValueError(f"Environment variable {env_var} is not set")
        return resolved
    
    return value

def resolve_config_environment_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively resolve environment variables in configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with environment variables resolved
    """
    resolved_config = {}
    
    for key, value in config.items():
        if isinstance(value, dict):
            resolved_config[key] = resolve_config_environment_variables(value)
        elif isinstance(value, list):
            resolved_config[key] = [
                resolve_config_environment_variables(item) if isinstance(item, dict)
                else resolve_environment_variables(item) if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            resolved_config[key] = resolve_environment_variables(value)
        else:
            resolved_config[key] = value
    
    return resolved_config

def create_backup_directory(path: str) -> str:
    """
    Create backup directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        Absolute path to the created directory
        
    Raises:
        OSError: If directory cannot be created
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed'
    
    return filename

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def check_git_installed() -> bool:
    """
    Check if Git is installed and available.
    
    Returns:
        True if Git is available, False otherwise
    """
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_git_version() -> Optional[str]:
    """
    Get Git version string.
    
    Returns:
        Git version string or None if Git is not available
    """
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None 