#!/bin/bash
# GitHub Organization Backup System - Cron Setup Script

set -e

echo "⏰ Setting up automated backup scheduling with cron..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$SCRIPT_DIR")"

# Check if we're in the right directory
if [ ! -f "$BACKUP_DIR/backup_organization.py" ]; then
    echo "❌ Error: backup_organization.py not found. Please run this script from the backup directory."
    exit 1
fi

# Create a wrapper script for cron
WRAPPER_SCRIPT="$BACKUP_DIR/run_backup.sh"

cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# Wrapper script for GitHub Organization Backup

# Set the backup directory
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKUP_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the backup
python backup_organization.py >> backup.log 2>&1
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "✅ Created wrapper script: $WRAPPER_SCRIPT"

# Function to add cron job
add_cron_job() {
    local schedule="$1"
    local description="$2"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$WRAPPER_SCRIPT"; then
        echo "⚠️  Cron job already exists for $description"
        return
    fi
    
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$schedule $WRAPPER_SCRIPT # $description") | crontab -
    echo "✅ Added cron job for $description"
}

# Ask user for backup frequency
echo ""
echo "Select backup frequency:"
echo "1. Every 6 hours (recommended)"
echo "2. Every 12 hours"
echo "3. Daily at 2 AM"
echo "4. Custom schedule"
echo "5. Skip cron setup"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        add_cron_job "0 */6 * * *" "Every 6 hours"
        ;;
    2)
        add_cron_job "0 */12 * * *" "Every 12 hours"
        ;;
    3)
        add_cron_job "0 2 * * *" "Daily at 2 AM"
        ;;
    4)
        echo ""
        echo "Enter custom cron schedule (e.g., '0 */6 * * *' for every 6 hours):"
        echo "Format: minute hour day month weekday"
        echo "Examples:"
        echo "  '0 */6 * * *'  - Every 6 hours"
        echo "  '0 2 * * *'    - Daily at 2 AM"
        echo "  '0 2 * * 0'    - Weekly on Sunday at 2 AM"
        read -p "Cron schedule: " custom_schedule
        add_cron_job "$custom_schedule" "Custom schedule"
        ;;
    5)
        echo "⏭️  Skipping cron setup"
        ;;
    *)
        echo "❌ Invalid choice. Skipping cron setup."
        ;;
esac

# Show current cron jobs
echo ""
echo "📋 Current cron jobs:"
crontab -l 2>/dev/null | grep -v '^#' || echo "No cron jobs found"

echo ""
echo "🎉 Cron setup completed!"
echo ""
echo "To manually run a backup:"
echo "  $WRAPPER_SCRIPT"
echo ""
echo "To view logs:"
echo "  tail -f $BACKUP_DIR/backup.log"
echo ""
echo "To remove cron jobs:"
echo "  crontab -e"
echo "  (then delete the lines with $WRAPPER_SCRIPT)" 