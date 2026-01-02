# Quick deployment script for Fly.io (Windows)

Write-Host "🚀 Deploying Forensic CTF to Fly.io..." -ForegroundColor Green
Write-Host ""

# Check if flyctl is installed
if (!(Get-Command flyctl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Fly.io CLI not found. Install it first:" -ForegroundColor Red
    Write-Host "   pwsh -Command `"iwr https://fly.io/install.ps1 -useb | iex`"" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
$whoami = flyctl auth whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "🔐 Please login to Fly.io first:" -ForegroundColor Yellow
    flyctl auth login
}

Write-Host "✅ Fly.io CLI ready" -ForegroundColor Green
Write-Host ""

# Deploy
Write-Host "📦 Building and deploying..." -ForegroundColor Cyan
flyctl deploy --local-only

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Check status:" -ForegroundColor Cyan
Write-Host "   flyctl status" -ForegroundColor White
Write-Host ""
Write-Host "📋 View logs:" -ForegroundColor Cyan
Write-Host "   flyctl logs" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Your app:" -ForegroundColor Cyan
Write-Host "   flyctl info" -ForegroundColor White
