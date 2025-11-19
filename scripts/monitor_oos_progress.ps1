# Monitor OOS backtest progress on server
# PowerShell script for Windows

$SERVER_IP = "49.51.244.154"
$SERVER_USER = "ubuntu"
$SSH_KEY = "mishi/lianxi.pem"
$LOG_FILE = "/home/ubuntu/manip-ofi-joint-analysis/results/logs/oos_all.log"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OOS Backtest Progress Monitor" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if process is running
Write-Host "Checking if OOS process is running..." -ForegroundColor Yellow
$processCheck = ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" "ps aux | grep 'run_score_oos_all.py' | grep -v grep"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ OOS process is running" -ForegroundColor Green
    Write-Host $processCheck
} else {
    Write-Host "❌ OOS process is not running" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Latest log output (last 30 lines):" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" "tail -30 $LOG_FILE"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Progress summary:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" "grep -E '(OOS SUMMARY|Train progress|Test progress)' $LOG_FILE | tail -20"

Write-Host ""
Write-Host "To view full log:" -ForegroundColor Yellow
Write-Host "  ssh -i $SSH_KEY ${SERVER_USER}@${SERVER_IP} 'tail -f $LOG_FILE'" -ForegroundColor Gray

