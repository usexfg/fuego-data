# GitHub Organization Backup System

This system provides automated backup of all repositories in a GitHub organization to multiple Git hosting services including centralized platforms (GitLab, Gitea) and decentralized networks (Radicle, IPFS, GitTorrent, Dat).

## Features

- **Multi-platform backup**: Backup to centralized and decentralized Git hosting services
- **Organization-wide**: Automatically discovers and backs up all repositories in your GitHub organization
- **Incremental updates**: Only syncs new changes, not full re-clones
- **Mirror management**: Maintains proper mirror relationships
- **Authentication support**: Supports personal access tokens and SSH keys
- **Logging and monitoring**: Comprehensive logging and error reporting
- **Scheduled backups**: Can be run as cron jobs or GitHub Actions

## Supported Platforms

### Centralized Platforms
- **GitLab**: Full mirror support with API integration
- **Gitea**: Mirror repositories with webhook support
- **Bitbucket**: Repository mirroring
- **Azure DevOps**: Git repository mirroring
- **Self-hosted Git**: Any Git server supporting mirror push

### Decentralized Networks
- **Radicle**: Peer-to-peer Git network with decentralized identity
- **IPFS**: InterPlanetary File System for distributed storage
- **GitTorrent**: BitTorrent-based Git repository distribution
- **Dat**: Distributed data sharing protocol
- **Local Storage**: Compressed backups with version management

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your settings**:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your organization and credentials
   ```

3. **Run the backup**:
   ```bash
   python backup_organization.py
   ```

## Configuration

Edit `config.yaml` to specify:
- GitHub organization name
- Target Git hosting services (centralized and decentralized)
- Authentication credentials
- Repository filters and exclusions
- Backup schedules

### Decentralized Backup Configuration

#### Radicle
```yaml
radicle:
  enabled: true
  rad_home: "~/.rad"
  node_id: "your-node-id"
  create_project: true
```

#### IPFS
```yaml
ipfs:
  enabled: true
  api_url: "http://localhost:5001"
  gateway_url: "https://ipfs.io"
  pin_on_upload: true
  compression: true
```

#### GitTorrent
```yaml
gittorrent:
  enabled: true
  tracker_url: "http://localhost:6881"
  port: 6882
  upload_limit: 0
```

#### Dat Protocol
```yaml
dat:
  enabled: true
  dat_path: "~/.dat"
  create_archive: true
```

## Decentralized Backup Benefits

### Radicle
- **Peer-to-peer**: No central server required
- **Decentralized identity**: Cryptographic identities for users
- **Built-in Git**: Native Git protocol support
- **Resilient**: Network survives node failures

### IPFS
- **Content-addressed**: Content is identified by its hash
- **Distributed**: Files are stored across multiple nodes
- **Immutable**: Content cannot be changed once uploaded
- **Gateway access**: Access via HTTP gateways

### GitTorrent
- **BitTorrent-based**: Leverages existing torrent infrastructure
- **Efficient**: Only download changed data
- **Scalable**: Multiple peers can share the load
- **Resilient**: Network redundancy through multiple seeders

### Dat Protocol
- **Versioned**: Built-in version control
- **Real-time**: Live synchronization between peers
- **Efficient**: Only transfer changed data
- **Secure**: End-to-end encryption

## Security

- Credentials are stored securely using environment variables
- SSH key authentication supported
- Repository access controls are preserved
- Audit logging for all backup operations
- Decentralized options provide additional security through distribution

## Monitoring

- Backup status dashboard
- Email/Slack notifications for failures
- Detailed logs for troubleshooting
- Repository sync status tracking
- Decentralized network health monitoring

## Installation Requirements

### For Centralized Backups
- Python 3.8+
- Git
- API tokens for target services

### For Decentralized Backups

#### Radicle
```bash
# Install Radicle CLI
curl -sSf https://radicle.xyz/install.sh | sh
rad auth  # Set up your identity
```

#### IPFS
```bash
# Install IPFS
wget https://dist.ipfs.io/go-ipfs/v0.20.0/go-ipfs_v0.20.0_linux-amd64.tar.gz
tar -xvzf go-ipfs_v0.20.0_linux-amd64.tar.gz
cd go-ipfs
sudo bash install.sh
ipfs init
ipfs daemon &  # Start IPFS daemon
```

#### GitTorrent
```bash
# Install GitTorrent
npm install -g git-torrent
# Set up tracker server
```

#### Dat Protocol
```bash
# Install Dat CLI
npm install -g dat
```

## Performance Considerations

### Centralized vs Decentralized
- **Centralized**: Faster uploads, single point of failure
- **Decentralized**: Slower initial upload, better resilience

### Network Requirements
- **IPFS**: Requires IPFS daemon running
- **Radicle**: Requires Radicle node running
- **GitTorrent**: Requires tracker server
- **Dat**: Requires Dat daemon

## Troubleshooting

### Decentralized Network Issues
- **IPFS**: Check if daemon is running (`ipfs daemon`)
- **Radicle**: Verify node status (`rad node status`)
- **GitTorrent**: Check tracker connectivity
- **Dat**: Ensure Dat daemon is active

### Performance Optimization
- Use compression for large repositories
- Configure appropriate sync intervals
- Monitor network bandwidth usage
- Consider using multiple decentralized networks for redundancy 