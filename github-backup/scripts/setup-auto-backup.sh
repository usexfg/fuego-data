#!/bin/bash
# Setup Automatic GitHub Organization Backup
# Configures continuous backup with monitoring and notifications

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Setting up Automatic GitHub Organization Backup${NC}"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "$BACKUP_DIR/backup_organization.py" ]; then
    echo -e "${RED}❌ Error: backup_organization.py not found${NC}"
    echo "Please run this script from the backup directory"
    exit 1
fi

# Function to prompt for input
prompt() {
    echo -e "${YELLOW}$1${NC}"
    read -p "> " response
    echo "$response"
}

# Function to create systemd service (Linux)
create_systemd_service() {
    echo -e "${BLUE}📋 Creating systemd service for automatic backup...${NC}"
    
    SERVICE_FILE="/etc/systemd/system/github-backup.service"
    SERVICE_CONTENT="[Unit]
Description=GitHub Organization Backup Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKUP_DIR
ExecStart=$BACKUP_DIR/scripts/auto-backup.sh start
ExecStop=$BACKUP_DIR/scripts/auto-backup.sh stop
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target"

    echo "$SERVICE_CONTENT" | sudo tee "$SERVICE_FILE" > /dev/null
    
    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable github-backup.service
    sudo systemctl start github-backup.service
    
    echo -e "${GREEN}✅ Systemd service created and started${NC}"
    echo "Service: github-backup.service"
    echo "Status: $(sudo systemctl is-active github-backup.service)"
}

# Function to create launchd service (macOS)
create_launchd_service() {
    echo -e "${BLUE}📋 Creating launchd service for automatic backup...${NC}"
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.github.backup.plist"
    PLIST_CONTENT="<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>Label</key>
    <string>com.github.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BACKUP_DIR/scripts/auto-backup.sh</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$BACKUP_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$BACKUP_DIR/auto-backup.log</string>
    <key>StandardErrorPath</key>
    <string>$BACKUP_DIR/auto-backup.log</string>
</dict>
</plist>"

    echo "$PLIST_CONTENT" > "$PLIST_FILE"
    
    # Load the service
    launchctl load "$PLIST_FILE"
    
    echo -e "${GREEN}✅ Launchd service created and loaded${NC}"
    echo "Service: com.github.backup"
    echo "Plist: $PLIST_FILE"
}

# Function to create cron job
create_cron_job() {
    echo -e "${BLUE}📋 Creating cron job for automatic backup...${NC}"
    
    # Ask for backup frequency
    echo -e "${YELLOW}Select backup frequency:${NC}"
    echo "1. Every 6 hours (recommended)"
    echo "2. Every 12 hours"
    echo "3. Daily at 2 AM"
    echo "4. Custom schedule"
    
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1) CRON_SCHEDULE="0 */6 * * *" ;;
        2) CRON_SCHEDULE="0 */12 * * *" ;;
        3) CRON_SCHEDULE="0 2 * * *" ;;
        4)
            echo -e "${YELLOW}Enter custom cron schedule (e.g., '0 */6 * * *' for every 6 hours):${NC}"
            read -p "> " CRON_SCHEDULE
            ;;
        *) CRON_SCHEDULE="0 */6 * * *" ;;
    esac
    
    # Create cron job
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $BACKUP_DIR/scripts/auto-backup.sh start") | crontab -
    
    echo -e "${GREEN}✅ Cron job created${NC}"
    echo "Schedule: $CRON_SCHEDULE"
    echo "Command: $BACKUP_DIR/scripts/auto-backup.sh start"
}

# Function to setup monitoring
setup_monitoring() {
    echo -e "${BLUE}📊 Setting up monitoring and notifications...${NC}"
    
    # Create monitoring script
    MONITOR_SCRIPT="$BACKUP_DIR/scripts/monitor-backup.sh"
    cat > "$MONITOR_SCRIPT" << 'EOF'
#!/bin/bash
# Monitor backup health and send notifications

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BACKUP_DIR/auto-backup.log"
PID_FILE="$BACKUP_DIR/auto-backup.pid"

# Check if backup is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "Backup process not running (PID: $PID)"
        # Send notification here
        exit 1
    fi
else
    echo "No PID file found"
    exit 1
fi

# Check log for recent errors
if [ -f "$LOG_FILE" ]; then
    RECENT_ERRORS=$(tail -n 100 "$LOG_FILE" | grep -c "ERROR")
    if [ "$RECENT_ERRORS" -gt 5 ]; then
        echo "Too many recent errors: $RECENT_ERRORS"
        exit 1
    fi
fi

echo "Backup system healthy"
exit 0
EOF

    chmod +x "$MONITOR_SCRIPT"
    
    # Create health check cron job
    (crontab -l 2>/dev/null; echo "*/30 * * * * $MONITOR_SCRIPT") | crontab -
    
    echo -e "${GREEN}✅ Monitoring setup complete${NC}"
    echo "Health check: Every 30 minutes"
    echo "Script: $MONITOR_SCRIPT"
}

# Function to setup notifications
setup_notifications() {
    echo -e "${BLUE}🔔 Setting up notifications...${NC}"
    
    # Ask for notification preferences
    echo -e "${YELLOW}Would you like to set up email notifications? (y/n)${NC}"
    read -p "> " setup_email
    
    if [ "$setup_email" = "y" ] || [ "$setup_email" = "Y" ]; then
        echo -e "${YELLOW}Enter email address for notifications:${NC}"
        read -p "> " email_address
        
        # Add to config
        if [ -f "$BACKUP_DIR/config.yaml" ]; then
            # Update config with email notifications
            sed -i.bak "s/enabled: false/enabled: true/" "$BACKUP_DIR/config.yaml"
            sed -i.bak "s/admin@your-org.com/$email_address/" "$BACKUP_DIR/config.yaml"
        fi
        
        echo -e "${GREEN}✅ Email notifications configured${NC}"
    fi
    
    echo -e "${YELLOW}Would you like to set up Slack notifications? (y/n)${NC}"
    read -p "> " setup_slack
    
    if [ "$setup_slack" = "y" ] || [ "$setup_slack" = "Y" ]; then
        echo -e "${YELLOW}Enter Slack webhook URL:${NC}"
        read -p "> " slack_webhook
        
        # Add to .env
        echo "SLACK_WEBHOOK_URL=$slack_webhook" >> "$BACKUP_DIR/.env"
        
        echo -e "${GREEN}✅ Slack notifications configured${NC}"
    fi
}

# Main setup process
echo -e "${BLUE}🔧 Starting automatic backup setup...${NC}"

# 1. Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"
if ! command -v python3 > /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

if ! command -v git > /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# 2. Setup configuration
echo -e "${BLUE}⚙️  Setting up configuration...${NC}"

# Get organization name
ORG_NAME=$(prompt "Enter your GitHub organization name:")
GITHUB_TOKEN=$(prompt "Enter your GitHub personal access token:")

# Create config if it doesn't exist
if [ ! -f "$BACKUP_DIR/config.yaml" ]; then
    cp "$BACKUP_DIR/config.example.yaml" "$BACKUP_DIR/config.yaml"
fi

# Update config with organization details
sed -i.bak "s/your-organization-name/$ORG_NAME/" "$BACKUP_DIR/config.yaml"

# Create .env file
if [ ! -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/env.example" "$BACKUP_DIR/.env"
fi

# Update .env with token
sed -i.bak "s/your_github_personal_access_token_here/$GITHUB_TOKEN/" "$BACKUP_DIR/.env"

echo -e "${GREEN}✅ Configuration updated${NC}"

# 3. Setup Python environment
echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
cd "$BACKUP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo -e "${GREEN}✅ Python environment ready${NC}"

# 4. Test configuration
echo -e "${BLUE}🧪 Testing configuration...${NC}"
python scripts/test-connections.py
echo -e "${GREEN}✅ Configuration test passed${NC}"

# 5. Setup notifications
setup_notifications

# 6. Setup monitoring
setup_monitoring

# 7. Choose automation method
echo -e "${BLUE}🤖 Choose automation method:${NC}"
echo "1. Systemd service (Linux)"
echo "2. Launchd service (macOS)"
echo "3. Cron job (any system)"
echo "4. Manual control only"

read -p "Enter choice (1-4): " automation_choice

case $automation_choice in
    1)
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            create_systemd_service
        else
            echo -e "${RED}❌ Systemd is only available on Linux${NC}"
            create_cron_job
        fi
        ;;
    2)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            create_launchd_service
        else
            echo -e "${RED}❌ Launchd is only available on macOS${NC}"
            create_cron_job
        fi
        ;;
    3)
        create_cron_job
        ;;
    4)
        echo -e "${YELLOW}Manual control selected. Use:${NC}"
        echo "  $BACKUP_DIR/scripts/auto-backup.sh start"
        echo "  $BACKUP_DIR/scripts/auto-backup.sh stop"
        echo "  $BACKUP_DIR/scripts/auto-backup.sh status"
        ;;
    *)
        create_cron_job
        ;;
esac

# 8. Final instructions
echo -e "${GREEN}🎉 Automatic backup setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Edit $BACKUP_DIR/config.yaml to customize backup targets"
echo "2. Edit $BACKUP_DIR/.env to add additional credentials"
echo "3. Test the backup: $BACKUP_DIR/scripts/auto-backup.sh start"
echo "4. Monitor logs: $BACKUP_DIR/scripts/auto-backup.sh logs"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "- Status: $BACKUP_DIR/scripts/auto-backup.sh status"
echo "- Logs: $BACKUP_DIR/auto-backup.log"
echo "- Health check: Every 30 minutes"
echo ""
echo -e "${BLUE}🛠️  Management:${NC}"
echo "- Start: $BACKUP_DIR/scripts/auto-backup.sh start"
echo "- Stop: $BACKUP_DIR/scripts/auto-backup.sh stop"
echo "- Restart: $BACKUP_DIR/scripts/auto-backup.sh restart" 