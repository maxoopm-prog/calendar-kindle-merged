#!/bin/sh
#
# Setup script for Kindle Dashboard
# Tested on Kindle 6th gen (BusyBox v1.28.3)
# Run this ONCE to set up automatic screen updates
#
# Usage:
#   mkdir -p /mnt/us/STARTUP   # 首次需手动创建（越狱后）
#   bash setup_kindle.sh
#

echo "=== Kindle Dashboard Setup ==="

# Directories in user storage (survives reboot)
INSTALL_DIR="/mnt/us/dashboard"
LOG_DIR="/mnt/us/logs"
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"

SCRIPT_PATH="$INSTALL_DIR/update_kindle.sh"
echo "Installing update script to $SCRIPT_PATH..."

cat > "$SCRIPT_PATH" << 'SCRIPT_EOF'
#!/bin/sh
# update_kindle.sh - Download image from server and display on Kindle screen
#
# Fixes applied:
#   - BusyBox wget uses -T for timeout (not the `timeout` command)
#   - lipc commands for proper WiFi enable/disable on Kindle
#   - route add default gw to fix missing gateway after WiFi up
#   - sleep 10 after WiFi enable to ensure IP is ready
#   - eips -c clears screen before display to eliminate ghost images

SERVER="http://localhost:5008"
IMAGE_PATH="/tmp/kindle.png"
LOG_FILE="/mnt/us/logs/kindle_update.log"
LOCK_FILE="/tmp/kindle_update.lock"
TIMEOUT=60
GATEWAY="192.168.100.1"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

cleanup() {
    rm -f "$LOCK_FILE"
}

trap cleanup EXIT

if [ -f "$LOCK_FILE" ]; then
    log "Update already in progress, skipping"
    exit 0
fi
touch "$LOCK_FILE"

log "=== Starting Kindle update ==="

# Enable WiFi via Kindle native lipc command
log "Enabling WiFi..."
lipc-set-prop com.lab126.cmd wirelessEnable 1
sleep 10

# Ensure default gateway exists
route add default gw $GATEWAY 2>/dev/null || true

# Download image using BusyBox wget (-T for timeout)
log "Downloading image..."
if wget -T $TIMEOUT -O "$IMAGE_PATH" -q "$SERVER/kindle.png"; then
    log "Downloaded successfully"
else
    log "ERROR: Download failed"
    exit 1
fi

# Clear screen first to eliminate ghost images, then display
log "Displaying image..."
eips -c
sleep 1
if eips -g "$IMAGE_PATH" 2>/dev/null; then
    log "Image displayed"
else
    log "ERROR: Display failed"
    exit 1
fi

# Disable WiFi via Kindle native lipc command
log "Disabling WiFi..."
killall udhcpc 2>/dev/null || true
lipc-set-prop com.lab126.cmd wirelessEnable 0
log "=== Update completed ==="
SCRIPT_EOF

chmod +x "$SCRIPT_PATH"
echo "✓ Update script installed"

# -----------------------------------------------
# Setup cron job
# -----------------------------------------------
echo "Setting up cron job..."

CRON_DIR="/var/spool/cron"
mkdir -p "$CRON_DIR"

CRON_JOB="*/30 * * * * $SCRIPT_PATH"

if grep -q "update_kindle" "$CRON_DIR/root" 2>/dev/null; then
    echo "⚠ Cron job already exists, skipping"
else
    echo "$CRON_JOB" >> "$CRON_DIR/root"
    echo "✓ Cron job written to $CRON_DIR/root"
fi

# Restart crond and explicitly point to cron directory
echo "Restarting crond..."
killall crond 2>/dev/null || true
sleep 1
busybox crond -c /var/spool/cron 2>/dev/null || crond 2>/dev/null || echo "⚠ Could not start crond"
sleep 1
if pgrep -x crond > /dev/null 2>&1; then
    echo "✓ crond started successfully"
else
    echo "⚠ crond not running - try manually: busybox crond -c /var/spool/cron"
fi

# -----------------------------------------------
# Setup boot auto-start (requires jailbroken Kindle)
# -----------------------------------------------
STARTUP_DIR="/mnt/us/STARTUP"
mkdir -p "$STARTUP_DIR"
STARTUP_SCRIPT="$STARTUP_DIR/update_kindle_boot.sh"

cat > "$STARTUP_SCRIPT" << BOOT_EOF
#!/bin/sh
# Auto-start kindle dashboard cron on boot
mkdir -p /var/spool/cron
echo "*/30 * * * * $SCRIPT_PATH" > /var/spool/cron/root
busybox crond -c /var/spool/cron 2>/dev/null || crond 2>/dev/null || true
BOOT_EOF

chmod +x "$STARTUP_SCRIPT"
echo "✓ Boot startup script installed to $STARTUP_SCRIPT"

# -----------------------------------------------
echo ""
echo "=== Installation Summary ==="
echo "Update script   : $SCRIPT_PATH"
echo "Log file        : $LOG_DIR/kindle_update.log"
echo "Update interval : Every 30 minutes"
echo "Cron file       : $CRON_DIR/root"
echo "Boot script     : $STARTUP_SCRIPT"
echo ""
echo "✓ Setup complete!"
echo ""
echo "To test manually : bash $SCRIPT_PATH"
echo "To view logs     : tail -f $LOG_DIR/kindle_update.log"
echo "To change server : edit SERVER= in $SCRIPT_PATH"
