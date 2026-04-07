#!/bin/sh
#
# Setup script for Kindle Dashboard
# Tested on Kindle 6th gen (BusyBox v1.28.3)
# Run this ONCE to set up automatic screen updates
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
# update_kindle.sh - Download image from server and display on screen
# Fixed for BusyBox wget (uses -T for timeout, not the timeout command)

SERVER="http://localhost:5008"
IMAGE_PATH="/tmp/kindle.png"
LOG_FILE="/mnt/us/logs/kindle_update.log"
LOCK_FILE="/tmp/kindle_update.lock"
TIMEOUT=60

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

# Bring up WiFi if needed
if ! ifconfig wlan0 | grep -q "UP"; then
    log "WiFi down, bringing up..."
    ifconfig wlan0 up
    sleep 2
fi

# Get IP if needed
if ! ifconfig wlan0 | grep -q "inet addr"; then
    log "Requesting DHCP lease..."
    udhcpc -i wlan0 -q 2>/dev/null || true
    sleep 2
fi

# Download image using BusyBox wget with -T for timeout
log "Downloading image..."
if wget -T $TIMEOUT -O "$IMAGE_PATH" -q "$SERVER/kindle.png"; then
    log "Downloaded successfully"
else
    log "ERROR: Download failed"
    exit 1
fi

# Display image on e-ink screen
log "Displaying image..."
if eips -g "$IMAGE_PATH" 2>/dev/null; then
    log "Image displayed"
else
    log "ERROR: Display failed"
    exit 1
fi

# Turn off WiFi to save battery
log "Disabling WiFi..."
killall udhcpc 2>/dev/null || true
ifconfig wlan0 down
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
