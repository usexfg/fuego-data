# Quick Start Guide

Get your GitHub organization backup system running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Git installed
- GitHub Personal Access Token with `repo` and `read:org` permissions

## Step 1: Install the System

```bash
# Clone or download the backup system
cd github-backup

# Run the installation script
./scripts/install.sh
```

## Step 2: Configure Your Settings

### 2.1 Set up Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit the file with your credentials
nano .env
```

**Required variables:**
```bash
GITHUB_TOKEN=your_github_personal_access_token_here
```

**Optional variables (depending on your backup targets):**
```bash
GITLAB_TOKEN=your_gitlab_token_here
GITEA_TOKEN=your_gitea_token_here
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password
```

### 2.2 Configure Backup Targets

```bash
# Copy the example configuration
cp config.example.yaml config.yaml

# Edit the configuration
nano config.yaml
```

**Minimal configuration:**
```yaml
github:
  organization: "your-organization-name"
  token: "${GITHUB_TOKEN}"

backup_targets:
  gitlab:
    enabled: true
    url: "https://gitlab.com"
    token: "${GITLAB_TOKEN}"
    group_id: "your-gitlab-group-id"
    create_mirrors: true
```

## Step 3: Test Your Setup

```bash
# Test all connections
python scripts/test-connections.py

# List repositories that will be backed up
python backup_organization.py --list-repos

# Run a dry run (no actual backups)
python backup_organization.py --dry-run
```

## Step 4: Run Your First Backup

```bash
# Run the backup
python backup_organization.py
```

## Step 5: Set Up Automated Backups

### Option A: GitHub Actions (Recommended)

1. Push your backup system to a GitHub repository
2. Add your secrets to the repository settings
3. The GitHub Actions workflow will run automatically

### Option B: Cron Jobs

```bash
# Set up cron jobs for automated backups
./scripts/cron-setup.sh
```

## Common Issues & Solutions

### "GitHub token not found"
- Make sure you've set the `GITHUB_TOKEN` environment variable
- Verify your token has the required permissions

### "No repositories found"
- Check your organization name in `config.yaml`
- Ensure your token has access to the organization

### "GitLab connection failed"
- Verify your GitLab token and group ID
- Check if the group exists and you have access

### "Permission denied" errors
- Make sure Git is installed and in your PATH
- Check file permissions on the backup directory

## Next Steps

- [Read the full documentation](README.md)
- [Configure notifications](README.md#notifications)
- [Set up monitoring](README.md#monitoring)
- [Customize backup filters](README.md#repository-filters)

## Getting Help

- Check the logs: `tail -f backup.log`
- Run the test script: `python scripts/test-connections.py`
- Review the [full documentation](README.md) 