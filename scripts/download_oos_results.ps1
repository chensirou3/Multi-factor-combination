# Download OOS results from server
# PowerShell script for Windows

# Configuration
$SERVER_IP = "49.51.244.154"
$SERVER_USER = "ubuntu"
$SSH_KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "/home/ubuntu/manip-ofi-joint-analysis"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Downloading OOS Results from Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Server: $SERVER_USER@$SERVER_IP"
Write-Host ""

# Create local results directory if not exists
New-Item -ItemType Directory -Force -Path "results/oos" | Out-Null

# Download OOS results
Write-Host "Downloading OOS results..." -ForegroundColor Yellow

scp -i $SSH_KEY -r `
    "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/results/oos/*" `
    "./results/oos/"

Write-Host ""
Write-Host "✅ Results downloaded successfully!" -ForegroundColor Green
Write-Host ""

# List downloaded files
Write-Host "Downloaded files:" -ForegroundColor Cyan
Get-ChildItem -Path "results/oos" -Filter "*.csv" -ErrorAction SilentlyContinue | 
    Format-Table Name, Length, LastWriteTime -AutoSize

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

