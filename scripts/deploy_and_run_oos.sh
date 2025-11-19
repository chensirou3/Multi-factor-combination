#!/bin/bash
# Deploy OOS framework to server and run tests

set -e  # Exit on error

# Configuration
SERVER_IP="49.51.244.154"
SERVER_USER="ubuntu"
SSH_KEY="mishi/lianxi.pem"
REMOTE_DIR="/home/ubuntu/manip-ofi-joint-analysis"

echo "=========================================="
echo "OOS Framework Deployment & Execution"
echo "=========================================="
echo "Server: $SERVER_USER@$SERVER_IP"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Step 1: Sync code to server
echo "Step 1: Syncing code to server..."
rsync -avz --progress \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='data/cache/*' \
    --exclude='results/oos/*' \
    -e "ssh -i $SSH_KEY" \
    ./ $SERVER_USER@$SERVER_IP:$REMOTE_DIR/

echo "✅ Code synced successfully"
echo ""

# Step 2: Test OOS setup on server
echo "Step 2: Testing OOS setup on server..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/ubuntu/manip-ofi-joint-analysis
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo ""

# Run setup test
echo "Running OOS setup test..."
python3 scripts/test_oos_setup.py
ENDSSH

echo ""
echo "=========================================="
echo "Setup test completed!"
echo "=========================================="
echo ""

# Step 3: Ask user if they want to proceed
read -p "Setup test passed. Do you want to run OOS backtest? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Step 3: Running OOS backtest on server..."
    
    # Ask which symbol to test first
    echo ""
    echo "Available symbols: BTCUSD, ETHUSD, XAUUSD, XAGUSD, EURUSD"
    read -p "Enter symbol to test (or 'all' for all symbols): " SYMBOL
    
    if [ "$SYMBOL" = "all" ]; then
        echo "Running OOS for all symbols..."
        ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/ubuntu/manip-ofi-joint-analysis
nohup python3 scripts/run_score_oos_all.py > results/logs/oos_all_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "OOS backtest started in background. Check logs in results/logs/"
echo "To monitor progress: tail -f results/logs/oos_all_*.log"
ENDSSH
    else
        echo "Running OOS for $SYMBOL..."
        ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << ENDSSH
cd /home/ubuntu/manip-ofi-joint-analysis
python3 scripts/run_score_oos_per_symbol.py --symbol $SYMBOL
ENDSSH
    fi
    
    echo ""
    echo "=========================================="
    echo "OOS backtest completed!"
    echo "=========================================="
    echo ""
    echo "To download results:"
    echo "  ./scripts/download_oos_results.sh"
else
    echo "Skipping OOS backtest."
fi

echo ""
echo "Done!"

