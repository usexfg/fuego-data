#!/bin/bash
# Automated GitHub Organization Backup Script
# Continuously monitors and backs up all repositories to decentralized networks

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${BACKUP_DIR}/config.yaml"
LOG_FILE="${BACKUP_DIR}/auto-backup.log"
PID_FILE="${BACKUP_DIR}/auto-backup.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            error "Auto-backup is already running (PID: $PID)"
            exit 1
        else
            warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi
}

# Start auto-backup
start_backup() {
    log "Starting automated GitHub organization backup..."
    
    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        error "Configuration file not found: $CONFIG_FILE"
        error "Please run the setup first: ./scripts/install.sh"
        exit 1
    fi
    
    # Check if Python environment is ready
    if [ ! -f "${BACKUP_DIR}/venv/bin/activate" ]; then
        warning "Virtual environment not found. Creating..."
        python3 -m venv "${BACKUP_DIR}/venv"
    fi
    
    # Activate virtual environment
    source "${BACKUP_DIR}/venv/bin/activate"
    
    # Install dependencies if needed
    if [ ! -f "${BACKUP_DIR}/venv/lib/python*/site-packages/github" ]; then
        log "Installing Python dependencies..."
        pip install -r "${BACKUP_DIR}/requirements.txt"
    fi
    
    # Check if services are running
    check_services
    
    # Start continuous backup loop
    continuous_backup
}

# Check if required services are running
check_services() {
    log "Checking required services..."
    
    # Check IPFS
    if ! curl -s http://localhost:5001/api/v0/version > /dev/null; then
        warning "IPFS daemon not running. Starting..."
        ipfs daemon &
        sleep 5
    else
        info "IPFS daemon is running"
    fi
    
    # Check Radicle (if configured)
    if command -v rad > /dev/null; then
        if ! rad node status > /dev/null 2>&1; then
            warning "Radicle node not running. Starting..."
            rad node start &
            sleep 3
        else
            info "Radicle node is running"
        fi
    fi
    
    # Check Dat (no daemon needed)
    if command -v dat > /dev/null; then
        info "Dat CLI is available"
    fi
}

# Continuous backup loop
continuous_backup() {
    log "Starting continuous backup loop..."
    
    while true; do
        log "Running backup cycle..."
        
        # Run the backup
        cd "$BACKUP_DIR"
        python backup_organization.py --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
        
        # Check exit status
        if [ $? -eq 0 ]; then
            log "Backup cycle completed successfully"
        else
            error "Backup cycle failed"
        fi
        
        # Wait for next cycle (default: 6 hours)
        log "Waiting 6 hours until next backup cycle..."
        sleep 21600  # 6 hours in seconds
    done
}

# Stop auto-backup
stop_backup() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Stopping auto-backup (PID: $PID)..."
            kill "$PID"
            rm -f "$PID_FILE"
            log "Auto-backup stopped"
        else
            warning "Process not found, removing stale PID file"
            rm -f "$PID_FILE"
        fi
    else
        error "No PID file found. Auto-backup may not be running."
    fi
}

# Show status
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Auto-backup is running (PID: $PID)"
            echo "Log file: $LOG_FILE"
            echo "Recent logs:"
            tail -n 20 "$LOG_FILE"
        else
            error "PID file exists but process is not running"
            rm -f "$PID_FILE"
        fi
    else
        error "Auto-backup is not running"
    fi
}

# Show logs
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        error "Log file not found: $LOG_FILE"
    fi
}

# Setup function
setup() {
    log "Setting up automated backup..."
    
    # Check if config exists
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "${BACKUP_DIR}/config.example.yaml" ]; then
            log "Creating configuration from template..."
            cp "${BACKUP_DIR}/config.example.yaml" "$CONFIG_FILE"
            warning "Please edit $CONFIG_FILE with your organization settings"
        else
            error "No configuration template found"
            exit 1
        fi
    fi
    
    # Check if .env exists
    if [ ! -f "${BACKUP_DIR}/.env" ]; then
        if [ -f "${BACKUP_DIR}/env.example" ]; then
            log "Creating environment file from template..."
            cp "${BACKUP_DIR}/env.example" "${BACKUP_DIR}/.env"
            warning "Please edit ${BACKUP_DIR}/.env with your credentials"
        fi
    fi
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}/backups"
    
    # Test configuration
    log "Testing configuration..."
    cd "$BACKUP_DIR"
    python scripts/test-connections.py
    
    log "Setup complete! Edit configuration files and run: $0 start"
}

# Main script logic
case "${1:-}" in
    start)
        check_running
        echo $$ > "$PID_FILE"
        start_backup
        ;;
    stop)
        stop_backup
        ;;
    restart)
        stop_backup
        sleep 2
        check_running
        echo $$ > "$PID_FILE"
        start_backup
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    setup)
        setup
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|setup}"
        echo ""
        echo "Commands:"
        echo "  start   - Start automated backup"
        echo "  stop    - Stop automated backup"
        echo "  restart - Restart automated backup"
        echo "  status  - Show backup status and recent logs"
        echo "  logs    - Show live logs"
        echo "  setup   - Initial setup and configuration"
        echo ""
        echo "Examples:"
        echo "  $0 setup    # First time setup"
        echo "  $0 start    # Start continuous backup"
        echo "  $0 status   # Check if running"
        echo "  $0 logs     # Monitor logs"
        echo "  $0 stop     # Stop backup"
        exit 1
        ;;
esac 