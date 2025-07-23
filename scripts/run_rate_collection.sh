#!/bin/bash

# Frankie Rate Collection Script
# This script runs the rate collection once and logs the results

# Set the working directory to the Frankie project
cd /path/to/frankie/ingest

# Activate virtual environment
source ../venv/bin/activate

# Run rate collection
python rate_scheduler.py --once

# Log completion
echo "$(date): Rate collection completed" >> /var/log/frankie_rate_collection.log 