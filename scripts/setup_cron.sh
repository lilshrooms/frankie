#!/bin/bash

# Frankie Rate Collection Cron Setup Script
# This script sets up a daily cron job to collect mortgage rates

# Configuration
FRANKIE_DIR="/path/to/frankie"
CRON_TIME="0 9 * * *"  # Daily at 9:00 AM
LOG_FILE="/var/log/frankie_rate_collection.log"

echo "Setting up Frankie Rate Collection Cron Job..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Create log file if it doesn't exist
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Create the cron job entry
CRON_ENTRY="$CRON_TIME cd $FRANKIE_DIR/ingest && $FRANKIE_DIR/venv/bin/python rate_scheduler.py --once >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "rate_scheduler.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "rate_scheduler.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "Cron job installed successfully!"
echo "Schedule: $CRON_TIME"
echo "Log file: $LOG_FILE"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e"
echo ""
echo "To test the rate collection manually:"
echo "cd $FRANKIE_DIR/ingest && $FRANKIE_DIR/venv/bin/python rate_scheduler.py --once" 