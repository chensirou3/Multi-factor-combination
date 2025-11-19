#!/bin/bash
# Download OOS results from server

set -e

# Configuration
SERVER_IP="49.51.244.154"
SERVER_USER="ubuntu"
SSH_KEY="mishi/lianxi.pem"
REMOTE_DIR="/home/ubuntu/manip-ofi-joint-analysis"

echo "=========================================="
echo "Downloading OOS Results from Server"
echo "=========================================="
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# Create local results directory if not exists
mkdir -p results/oos

# Download OOS results
echo "Downloading OOS results..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    $SERVER_USER@$SERVER_IP:$REMOTE_DIR/results/oos/ \
    ./results/oos/

echo ""
echo "✅ Results downloaded successfully!"
echo ""

# List downloaded files
echo "Downloaded files:"
ls -lh results/oos/*.csv 2>/dev/null || echo "No CSV files found"

echo ""
echo "Done!"

