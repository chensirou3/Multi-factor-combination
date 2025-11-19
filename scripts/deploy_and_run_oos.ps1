# Deploy OOS framework to server and run tests
# PowerShell script for Windows

# Configuration
$SERVER_IP = "49.51.244.154"
$SERVER_USER = "ubuntu"
$SSH_KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "/home/ubuntu/manip-ofi-joint-analysis"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OOS Framework Deployment & Execution" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Server: $SERVER_USER@$SERVER_IP"
Write-Host "Remote directory: $REMOTE_DIR"
Write-Host ""

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SSH not found. Please install OpenSSH or use Git Bash." -ForegroundColor Red
    exit 1
}

# Step 1: Sync code to server using SCP
Write-Host "Step 1: Syncing code to server..." -ForegroundColor Yellow

# Create a temporary exclude file
$excludeFile = "temp_exclude.txt"
@"
*.pyc
__pycache__
.git
data/cache/*
results/oos/*
"@ | Out-File -FilePath $excludeFile -Encoding ASCII

# Use SCP to copy files (simpler than rsync on Windows)
Write-Host "Copying files to server..."
scp -i $SSH_KEY -r `
    -o "StrictHostKeyChecking=no" `
    config src scripts requirements.txt README.md CHANGELOG.md PROGRESS.md `
    "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"

Remove-Item $excludeFile -ErrorAction SilentlyContinue

Write-Host "✅ Code synced successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Test OOS setup on server
Write-Host "Step 2: Testing OOS setup on server..." -ForegroundColor Yellow

$testCommand = @"
cd $REMOTE_DIR
echo 'Current directory: ' `$(pwd)
echo 'Python version: ' `$(python3 --version)
echo ''
echo 'Running OOS setup test...'
python3 scripts/test_oos_setup.py
"@

ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" $testCommand

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup test completed!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 3: Ask user if they want to proceed
$proceed = Read-Host "Setup test passed. Do you want to run OOS backtest? (y/n)"

if ($proceed -eq 'y' -or $proceed -eq 'Y') {
    Write-Host ""
    Write-Host "Available symbols: BTCUSD, ETHUSD, XAUUSD, XAGUSD, EURUSD" -ForegroundColor Cyan
    $symbol = Read-Host "Enter symbol to test (or 'all' for all symbols)"
    
    if ($symbol -eq 'all') {
        Write-Host "Running OOS for all symbols..." -ForegroundColor Yellow
        
        $runCommand = @"
cd $REMOTE_DIR
nohup python3 scripts/run_score_oos_all.py > results/logs/oos_all_`$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo 'OOS backtest started in background.'
echo 'To monitor progress: tail -f results/logs/oos_all_*.log'
"@
        
        ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" $runCommand
        
        Write-Host ""
        Write-Host "✅ OOS backtest started in background on server" -ForegroundColor Green
        Write-Host "To check progress, run: ssh -i $SSH_KEY ${SERVER_USER}@${SERVER_IP} 'tail -f $REMOTE_DIR/results/logs/oos_all_*.log'"
        
    } else {
        Write-Host "Running OOS for $symbol..." -ForegroundColor Yellow
        
        $runCommand = @"
cd $REMOTE_DIR
python3 scripts/run_score_oos_per_symbol.py --symbol $symbol
"@
        
        ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" $runCommand
        
        Write-Host ""
        Write-Host "✅ OOS backtest completed!" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "To download results:" -ForegroundColor Cyan
    Write-Host "  .\scripts\download_oos_results.ps1" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Cyan
    
} else {
    Write-Host "Skipping OOS backtest." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

