#!/bin/bash
# Monitor OOS backtest progress on server

SERVER_IP="49.51.244.154"
SERVER_USER="ubuntu"
SSH_KEY="mishi/lianxi.pem"
LOG_FILE="/home/ubuntu/manip-ofi-joint-analysis/results/logs/oos_all.log"

echo "=========================================="
echo "OOS Backtest Progress Monitor"
echo "=========================================="
echo ""

# Check if process is running
echo "Checking if OOS process is running..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "ps aux | grep 'run_score_oos_all.py' | grep -v grep"

if [ $? -eq 0 ]; then
    echo "✅ OOS process is running"
else
    echo "❌ OOS process is not running"
fi

echo ""
echo "=========================================="
echo "Latest log output (last 30 lines):"
echo "=========================================="

ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "tail -30 $LOG_FILE"

echo ""
echo "=========================================="
echo "Progress summary:"
echo "=========================================="

ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "grep -E '(OOS SUMMARY|Train progress|Test progress)' $LOG_FILE | tail -20"

echo ""
echo "To view full log:"
echo "  ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'tail -f $LOG_FILE'"

