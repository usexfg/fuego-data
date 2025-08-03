# Automatic Transfer Guide

This guide shows you how to set up **automatic transfer** of all your GitHub organization repositories to decentralized networks.

## 🚀 Quick Start

### 1. **Run the Setup Wizard**
```bash
./scripts/setup-auto-backup.sh
```

This interactive script will:
- Configure your GitHub organization and token
- Set up Python environment and dependencies
- Configure notifications (email/Slack)
- Set up monitoring and health checks
- Choose automation method (systemd/launchd/cron)

### 2. **Start Automatic Backup**
```bash
./scripts/auto-backup.sh start
```

### 3. **Monitor Progress**
```bash
./scripts/auto-backup.sh logs
```

## 🤖 Automation Methods

### **Option 1: Systemd Service (Linux)**
```bash
# Automatic startup and restart
sudo systemctl enable github-backup.service
sudo systemctl start github-backup.service
sudo systemctl status github-backup.service
```

### **Option 2: Launchd Service (macOS)**
```bash
# Automatic startup and restart
launchctl load ~/Library/LaunchAgents/com.github.backup.plist
launchctl list | grep github.backup
```

### **Option 3: Cron Job (Any System)**
```bash
# Runs every 6 hours automatically
# View cron jobs: crontab -l
# Edit cron jobs: crontab -e
```

### **Option 4: Manual Control**
```bash
# Start: ./scripts/auto-backup.sh start
# Stop: ./scripts/auto-backup.sh stop
# Status: ./scripts/auto-backup.sh status
# Logs: ./scripts/auto-backup.sh logs
```

## 📊 What Gets Transferred Automatically

### **Repository Content**
- ✅ All source code and files
- ✅ Git history and commits
- ✅ Branches and tags
- ✅ Repository metadata
- ✅ Issues and pull requests (if supported)

### **Backup Targets**
- 🌐 **IPFS** - Distributed file storage
- 🌱 **Radicle** - Peer-to-peer Git network
- 📦 **Dat Protocol** - Versioned data sharing
- 💾 **Local Storage** - Compressed backups

### **Transfer Frequency**
- **Default**: Every 6 hours
- **Customizable**: 1-24 hours
- **Real-time**: On repository changes (webhook-based)

## 🔧 Configuration Options

### **Backup Schedule**
```yaml
# In config.yaml
backup_targets:
  ipfs:
    sync_interval_hours: 6  # Every 6 hours
    
  radicle:
    sync_interval_hours: 12  # Every 12 hours
    
  local_backup:
    sync_interval_hours: 24  # Daily
```

### **Repository Filters**
```yaml
repositories:
  include_private: true      # Backup private repos
  include_archived: false    # Skip archived repos
  include_forks: false       # Skip forked repos
  exclude_patterns:          # Skip specific repos
    - "temp-*"
    - "test-*"
  include_patterns: []       # Only backup specific repos
```

### **Performance Settings**
```yaml
performance:
  max_concurrent_backups: 5  # Parallel backups
  timeout_seconds: 300       # 5 minute timeout
  retry_attempts: 3          # Retry failed backups
  retry_delay_seconds: 60    # Wait between retries
```

## 📈 Monitoring and Alerts

### **Health Checks**
- ✅ Process monitoring (every 30 minutes)
- ✅ Service status checks
- ✅ Error rate monitoring
- ✅ Disk space monitoring

### **Notifications**
- 📧 **Email**: Backup status and failures
- 💬 **Slack**: Real-time alerts
- 🔗 **Webhook**: Custom integrations

### **Logging**
```bash
# View live logs
tail -f auto-backup.log

# View recent activity
tail -n 100 auto-backup.log

# Search for errors
grep "ERROR" auto-backup.log
```

## 🛠️ Management Commands

### **Start/Stop**
```bash
# Start automatic backup
./scripts/auto-backup.sh start

# Stop automatic backup
./scripts/auto-backup.sh stop

# Restart automatic backup
./scripts/auto-backup.sh restart
```

### **Status and Monitoring**
```bash
# Check if running
./scripts/auto-backup.sh status

# View live logs
./scripts/auto-backup.sh logs

# Test connections
python scripts/test-connections.py
```

### **Manual Backup**
```bash
# Run one-time backup
python backup_organization.py

# Dry run (no actual transfer)
python backup_organization.py --dry-run

# List repositories
python backup_organization.py --list-repos
```

## 🔍 Troubleshooting

### **Common Issues**

#### **Backup Process Not Starting**
```bash
# Check if already running
./scripts/auto-backup.sh status

# Check logs
tail -f auto-backup.log

# Restart process
./scripts/auto-backup.sh restart
```

#### **Service Not Starting on Boot**
```bash
# Linux (systemd)
sudo systemctl enable github-backup.service
sudo systemctl status github-backup.service

# macOS (launchd)
launchctl load ~/Library/LaunchAgents/com.github.backup.plist
launchctl list | grep github.backup
```

#### **Permission Issues**
```bash
# Fix script permissions
chmod +x scripts/auto-backup.sh
chmod +x scripts/setup-auto-backup.sh

# Check file ownership
ls -la scripts/
```

#### **Network Issues**
```bash
# Test IPFS connection
curl http://localhost:5001/api/v0/version

# Test GitHub API
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Check firewall settings
sudo ufw status  # Linux
sudo pfctl -s rules  # macOS
```

### **Performance Issues**

#### **Slow Transfers**
```yaml
# Reduce concurrent backups
performance:
  max_concurrent_backups: 2  # Reduce from 5 to 2
  timeout_seconds: 600       # Increase timeout
```

#### **High Resource Usage**
```yaml
# Enable compression
ipfs:
  compression: true

local_backup:
  compress: true
```

## 📊 Monitoring Dashboard

### **Key Metrics to Monitor**
- **Backup Success Rate**: Should be >95%
- **Transfer Speed**: MB/s per repository
- **Error Rate**: Should be <5%
- **Disk Usage**: Monitor backup storage
- **Network Usage**: Bandwidth consumption

### **Health Check Commands**
```bash
# Check IPFS health
ipfs id
ipfs swarm peers | wc -l

# Check Radicle health
rad node status

# Check backup status
./scripts/auto-backup.sh status

# Check disk usage
df -h backups/
```

## 🔐 Security Considerations

### **Access Control**
- Use GitHub Personal Access Tokens with minimal permissions
- Store credentials in environment variables
- Use SSH keys for private repositories

### **Network Security**
- Use VPN for additional privacy
- Configure firewalls appropriately
- Monitor network traffic

### **Data Privacy**
- **IPFS**: Content is public by default
- **Radicle**: Supports private projects
- **Dat**: End-to-end encrypted
- **Local**: Private to your machine

## 🎯 Best Practices

### **1. Start Small**
- Begin with a few test repositories
- Verify transfers work correctly
- Gradually add more repositories

### **2. Monitor Regularly**
- Check logs daily
- Monitor disk space usage
- Review error rates weekly

### **3. Test Recovery**
- Periodically test restoring from backups
- Verify data integrity
- Document recovery procedures

### **4. Update Regularly**
- Keep backup tools updated
- Monitor for security updates
- Test after major updates

## 📞 Support

### **Getting Help**
1. Check the logs: `tail -f auto-backup.log`
2. Run diagnostics: `python scripts/test-connections.py`
3. Review configuration: `cat config.yaml`
4. Check service status: `./scripts/auto-backup.sh status`

### **Useful Commands**
```bash
# Full system check
./scripts/test-connections.py && ./scripts/auto-backup.sh status

# Quick health check
ipfs id && rad node status && ./scripts/auto-backup.sh status

# View all logs
tail -f auto-backup.log backup.log
```

## 🎉 Success Indicators

Your automatic transfer system is working correctly when:

- ✅ Backup process runs every 6 hours
- ✅ All repositories transfer successfully
- ✅ No errors in logs
- ✅ Notifications work properly
- ✅ Services start automatically on boot
- ✅ Health checks pass consistently

With this setup, your entire GitHub organization will be automatically transferred to multiple decentralized networks, ensuring maximum resilience and availability of your codebase! 