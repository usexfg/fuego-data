# Decentralized Backup Guide

This guide covers setting up and using decentralized backup options for your GitHub organization repositories.

## Why Decentralized Backups?

Decentralized backups offer several advantages over traditional centralized solutions:

- **Resilience**: No single point of failure
- **Censorship Resistance**: Content cannot be easily removed
- **Privacy**: No central authority controls your data
- **Cost**: Often cheaper than cloud storage
- **Ownership**: You maintain full control over your data

## Supported Decentralized Networks

### 1. Radicle 🌱
**Peer-to-peer Git network with decentralized identity**

**Features:**
- Native Git protocol support
- Cryptographic identities
- No central servers required
- Built-in code review and collaboration

**Setup:**
```bash
# Install Radicle
curl -sSf https://radicle.xyz/install.sh | sh

# Set up your identity
rad auth

# Start Radicle node
rad node start
```

**Configuration:**
```yaml
radicle:
  enabled: true
  rad_home: "~/.rad"
  node_id: "your-node-id"
  create_project: true
```

### 2. IPFS 🌐
**InterPlanetary File System for distributed storage**

**Features:**
- Content-addressed storage
- Distributed across multiple nodes
- Immutable content
- Gateway access via HTTP

**Setup:**
```bash
# Install IPFS
wget https://dist.ipfs.io/go-ipfs/v0.20.0/go-ipfs_v0.20.0_linux-amd64.tar.gz
tar -xvzf go-ipfs_v0.20.0_linux-amd64.tar.gz
cd go-ipfs
sudo bash install.sh

# Initialize IPFS
ipfs init

# Start IPFS daemon
ipfs daemon &
```

**Configuration:**
```yaml
ipfs:
  enabled: true
  api_url: "http://localhost:5001"
  gateway_url: "https://ipfs.io"
  pin_on_upload: true
  compression: true
```

### 3. GitTorrent 🌊
**BitTorrent-based Git repository distribution**

**Features:**
- Leverages existing torrent infrastructure
- Efficient delta transfers
- Multiple peer support
- Built-in redundancy

**Setup:**
```bash
# Install GitTorrent
npm install -g git-torrent

# Set up tracker server (optional)
# You can use public trackers or run your own
```

**Configuration:**
```yaml
gittorrent:
  enabled: true
  tracker_url: "http://localhost:6881"
  port: 6882
  upload_limit: 0
```

### 4. Dat Protocol 📦
**Distributed data sharing protocol**

**Features:**
- Versioned data
- Real-time synchronization
- End-to-end encryption
- Efficient delta transfers

**Setup:**
```bash
# Install Dat CLI
npm install -g dat

# Dat daemon runs automatically when needed
```

**Configuration:**
```yaml
dat:
  enabled: true
  dat_path: "~/.dat"
  create_archive: true
```

## Installation

### Quick Install
```bash
# Install all decentralized dependencies
./scripts/install-decentralized.sh
```

### Manual Install
```bash
# Install Node.js (required for GitTorrent and Dat)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Go (required for IPFS)
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz

# Install individual tools
curl -sSf https://radicle.xyz/install.sh | sh
npm install -g git-torrent dat
```

## Configuration Examples

### Minimal Decentralized Setup
```yaml
backup_targets:
  ipfs:
    enabled: true
    api_url: "http://localhost:5001"
    pin_on_upload: true
    compression: true
```

### Multi-Network Redundancy
```yaml
backup_targets:
  radicle:
    enabled: true
    create_project: true
    
  ipfs:
    enabled: true
    api_url: "http://localhost:5001"
    pin_on_upload: true
    
  gittorrent:
    enabled: true
    tracker_url: "http://localhost:6881"
    
  dat:
    enabled: true
    create_archive: true
```

### Production Setup
```yaml
backup_targets:
  # Primary: IPFS with pinning
  ipfs:
    enabled: true
    api_url: "http://localhost:5001"
    gateway_url: "https://ipfs.io"
    pin_on_upload: true
    compression: true
    sync_interval_hours: 6
    
  # Secondary: Radicle for Git-native backup
  radicle:
    enabled: true
    node_id: "your-node-id"
    create_project: true
    sync_interval_hours: 12
    
  # Tertiary: Local compressed backup
  local_backup:
    enabled: true
    path: "./backups"
    keep_versions: 10
    compress: true
    sync_interval_hours: 24
```

## Network Management

### Starting Services
```bash
# Start IPFS daemon
ipfs daemon &

# Start Radicle node
rad node start &

# Check service status
ipfs id
rad node status
```

### Monitoring Network Health
```bash
# IPFS network status
ipfs swarm peers
ipfs stats repo

# Radicle network status
rad node status
rad ls

# Dat network status
dat doctor
```

## Performance Optimization

### Bandwidth Management
```yaml
performance:
  max_concurrent_backups: 3  # Reduce for slower networks
  timeout_seconds: 600       # Increase for large repos
  retry_attempts: 5
  retry_delay_seconds: 120
```

### Compression Settings
```yaml
ipfs:
  compression: true  # Enable for large repositories
  
local_backup:
  compress: true     # Always compress local backups
```

### Sync Intervals
```yaml
# Frequent updates for active repositories
radicle:
  sync_interval_hours: 6

# Less frequent for stable repositories
ipfs:
  sync_interval_hours: 24
```

## Security Considerations

### Private Repositories
- **IPFS**: Content is public by default, consider encryption
- **Radicle**: Supports private projects with access control
- **GitTorrent**: Torrent files are public, content may be accessible
- **Dat**: End-to-end encrypted by default

### Access Control
```yaml
# Use environment variables for sensitive data
radicle:
  node_id: "${RADICLE_NODE_ID}"

ipfs:
  api_url: "${IPFS_API_URL}"
```

### Network Privacy
- Use VPNs for additional privacy
- Configure firewalls appropriately
- Monitor network traffic

## Troubleshooting

### Common Issues

#### IPFS Daemon Not Starting
```bash
# Check if port 5001 is available
netstat -tulpn | grep 5001

# Reset IPFS configuration
rm -rf ~/.ipfs
ipfs init
```

#### Radicle Node Issues
```bash
# Check node status
rad node status

# Restart node
rad node stop
rad node start
```

#### GitTorrent Tracker Problems
```bash
# Test tracker connectivity
curl http://localhost:6881/announce

# Use alternative trackers
gittorrent:
  tracker_url: "https://tracker.example.com"
```

### Performance Issues

#### Slow Uploads
- Reduce concurrent backups
- Enable compression
- Use local network for initial sync

#### Network Timeouts
- Increase timeout values
- Check network connectivity
- Use alternative gateways/nodes

### Recovery Procedures

#### IPFS Content Recovery
```bash
# Check if content is pinned
ipfs pin ls | grep <hash>

# Re-pin content
ipfs pin add <hash>

# Download from gateway
curl https://ipfs.io/ipfs/<hash>
```

#### Radicle Project Recovery
```bash
# List available projects
rad ls

# Clone specific project
rad clone <project-id>
```

## Best Practices

### 1. Multi-Network Strategy
- Use multiple decentralized networks for redundancy
- Combine with local backups
- Monitor network health regularly

### 2. Content Management
- Pin important content in IPFS
- Use descriptive project names in Radicle
- Maintain backup metadata

### 3. Network Maintenance
- Keep nodes updated
- Monitor disk space usage
- Regular health checks

### 4. Documentation
- Document your setup
- Keep recovery procedures handy
- Monitor backup logs

## Advanced Configuration

### Custom IPFS Configuration
```bash
# Edit IPFS config
ipfs config edit

# Set custom storage limits
ipfs config Datastore.StorageMax "10GB"
```

### Radicle Network Configuration
```bash
# Configure seed nodes
rad config set node.seeds "seed1.example.com,seed2.example.com"

# Set custom network
rad config set node.network "mainnet"
```

### GitTorrent Advanced Settings
```yaml
gittorrent:
  tracker_url: "http://localhost:6881"
  port: 6882
  upload_limit: 1024  # 1MB/s
  download_limit: 2048  # 2MB/s
  max_connections: 50
```

## Monitoring and Alerts

### Health Checks
```bash
# Create monitoring script
#!/bin/bash
ipfs id > /dev/null && echo "IPFS: OK" || echo "IPFS: FAILED"
rad node status > /dev/null && echo "Radicle: OK" || echo "Radicle: FAILED"
```

### Log Monitoring
```bash
# Monitor backup logs
tail -f backup.log | grep -E "(ERROR|WARNING)"

# Check network status
watch -n 30 'ipfs swarm peers | wc -l'
```

This decentralized backup approach ensures your GitHub repositories are safely distributed across multiple networks, providing maximum resilience and availability. 