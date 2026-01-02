# Setup Script for Production Deployment
# Run this after creating Supabase and R2 accounts

Write-Host "🚀 Forensic CTF - Production Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
$prereqs = @("flyctl", "git", "python")
$missing = @()

foreach ($cmd in $prereqs) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        $missing += $cmd
    }
}

if ($missing.Count -gt 0) {
    Write-Host "❌ Missing prerequisites:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Install Fly.io CLI:" -ForegroundColor Cyan
    Write-Host "   pwsh -Command `"iwr https://fly.io/install.ps1 -useb | iex`"" -ForegroundColor White
    exit 1
}

Write-Host "✅ Prerequisites installed" -ForegroundColor Green
Write-Host ""

# Generate secrets
Write-Host "🔐 Generating production secrets..." -ForegroundColor Cyan
$SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$FLAG_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"

Write-Host "✅ Secrets generated" -ForegroundColor Green
Write-Host ""

# Prompt for Supabase details
Write-Host "📊 Supabase Database Configuration" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan
Write-Host "Get connection string from: Supabase Dashboard → Settings → Database" -ForegroundColor Yellow
Write-Host ""
$POSTGRES_HOST = Read-Host "Supabase Host (e.g., aws-0-us-east-1.pooler.supabase.com)"
$POSTGRES_PASSWORD = Read-Host "Supabase Password" -AsSecureString
$POSTGRES_PASSWORD_TEXT = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($POSTGRES_PASSWORD))
Write-Host ""

# Prompt for R2 details
Write-Host "📦 Cloudflare R2 Configuration" -ForegroundColor Cyan
Write-Host "------------------------------" -ForegroundColor Cyan
Write-Host "Get credentials from: Cloudflare Dashboard → R2 → Manage R2 API Tokens" -ForegroundColor Yellow
Write-Host ""
$R2_ENDPOINT = Read-Host "R2 Endpoint (e.g., xxx.r2.cloudflarestorage.com)"
$R2_PUBLIC = Read-Host "R2 Public URL (e.g., https://bucket.xxx.r2.dev)"
$R2_ACCESS_KEY = Read-Host "R2 Access Key"
$R2_SECRET = Read-Host "R2 Secret Key" -AsSecureString
$R2_SECRET_TEXT = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($R2_SECRET))
$R2_BUCKET = Read-Host "R2 Bucket Name (default: forensic-ctf-artifacts)" 
if ([string]::IsNullOrWhiteSpace($R2_BUCKET)) { $R2_BUCKET = "forensic-ctf-artifacts" }
Write-Host ""

# Confirm Fly.io setup
Write-Host "✈️  Fly.io Setup" -ForegroundColor Cyan
Write-Host "----------------" -ForegroundColor Cyan
$DEPLOY_NOW = Read-Host "Deploy to Fly.io now? (y/n)"

if ($DEPLOY_NOW -eq "y" -or $DEPLOY_NOW -eq "Y") {
    Write-Host ""
    Write-Host "🚀 Initializing Fly.io app..." -ForegroundColor Cyan
    
    # Launch app
    flyctl launch --no-deploy
    
    Write-Host ""
    Write-Host "🔑 Setting secrets..." -ForegroundColor Cyan
    
    # Set all secrets
    flyctl secrets set `
        "SECRET_KEY=$SECRET_KEY" `
        "FLAG_SECRET_KEY=$FLAG_SECRET_KEY" `
        "POSTGRES_HOST=$POSTGRES_HOST" `
        "POSTGRES_PORT=6543" `
        "POSTGRES_USER=postgres" `
        "POSTGRES_PASSWORD=$POSTGRES_PASSWORD_TEXT" `
        "POSTGRES_DB=postgres" `
        "MINIO_ENDPOINT=$R2_ENDPOINT" `
        "MINIO_PUBLIC_ENDPOINT=$R2_PUBLIC" `
        "MINIO_ACCESS_KEY=$R2_ACCESS_KEY" `
        "MINIO_SECRET_KEY=$R2_SECRET_TEXT" `
        "MINIO_BUCKET_NAME=$R2_BUCKET"
    
    Write-Host ""
    Write-Host "📦 Deploying to Fly.io..." -ForegroundColor Cyan
    flyctl deploy --local-only
    
    Write-Host ""
    Write-Host "✅ Backend deployed!" -ForegroundColor Green
    
    # Get app URL
    Write-Host ""
    Write-Host "🌐 Getting your app URL..." -ForegroundColor Cyan
    flyctl info
    
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Update ALLOWED_ORIGINS with your Vercel URL:" -ForegroundColor Yellow
    Write-Host "   flyctl secrets set ALLOWED_ORIGINS=https://your-app.vercel.app" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Deploy frontend to Vercel:" -ForegroundColor Yellow
    Write-Host "   - Push to GitHub" -ForegroundColor White
    Write-Host "   - Import in Vercel dashboard" -ForegroundColor White
    Write-Host "   - Set NEXT_PUBLIC_API_URL to your Fly.io URL" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Run database migrations:" -ForegroundColor Yellow
    Write-Host "   flyctl ssh console" -ForegroundColor White
    Write-Host "   alembic upgrade head" -ForegroundColor White
    
} else {
    # Save to .env.production
    Write-Host ""
    Write-Host "💾 Saving configuration to .env.production..." -ForegroundColor Cyan
    
    $envContent = @"
# Production Environment Variables
# NEVER commit this file!

DEBUG=false
SECRET_KEY=$SECRET_KEY
FLAG_SECRET_KEY=$FLAG_SECRET_KEY

POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=6543
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD_TEXT
POSTGRES_DB=postgres

MINIO_ENDPOINT=$R2_ENDPOINT
MINIO_PUBLIC_ENDPOINT=$R2_PUBLIC
MINIO_ACCESS_KEY=$R2_ACCESS_KEY
MINIO_SECRET_KEY=$R2_SECRET_TEXT
MINIO_BUCKET_NAME=$R2_BUCKET
MINIO_USE_SSL=true

ALLOWED_ORIGINS=https://your-app.vercel.app
"@

    $envContent | Out-File -FilePath ".env.production" -Encoding UTF8
    
    Write-Host "✅ Configuration saved to .env.production" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 To deploy later:" -ForegroundColor Cyan
    Write-Host "   flyctl launch" -ForegroundColor White
    Write-Host "   .\deploy.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 See DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Cyan
Write-Host "📋 See QUICK_REFERENCE.md for command reference" -ForegroundColor Cyan
