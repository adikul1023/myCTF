# 🚀 Deployment Guide - 100% Free Stack

**Stack**: Vercel + Fly.io + Supabase + Cloudflare R2  
**Cost**: $0/month (guaranteed free forever)

---

## 📋 Prerequisites

1. GitHub account
2. Vercel account (sign up with GitHub)
3. Fly.io account
4. Supabase account
5. Cloudflare account

---

## 🗄️ Step 1: Setup Supabase Database (5 min)

### 1.1 Create Project
```bash
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Enter:
   - Name: forensic-ctf
   - Database Password: (generate strong password, save it!)
   - Region: Choose closest to you
4. Click "Create new project" (wait 2-3 minutes)
```

### 1.2 Get Connection String
```bash
1. Project Dashboard -> Settings -> Database
2. Scroll to "Connection String" section
3. Select "URI" tab
4. Copy the connection pooler string (port 6543):
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   
5. Replace [password] with your actual password
```

### 1.3 Run Database Migrations
```bash
# Install Supabase CLI (optional, can use their web SQL editor)
npm install -g supabase

# OR use the Supabase SQL Editor in dashboard:
# 1. Go to SQL Editor in Supabase dashboard
# 2. Copy and paste the migration files from backend/alembic/versions/
# 3. Run them in order (001, 002, 003, 004)
```

**Alternative**: Run migrations from local:
```bash
cd backend
# Update .env with Supabase connection string
alembic upgrade head
```

---

## 📦 Step 2: Setup Cloudflare R2 Storage (5 min)

### 2.1 Create R2 Bucket
```bash
1. Cloudflare Dashboard -> R2 Object Storage
2. Click "Create bucket"
3. Name: forensic-ctf-artifacts
4. Location: Automatic (or choose region)
5. Click "Create bucket"
```

### 2.2 Generate API Tokens
```bash
1. R2 -> Manage R2 API Tokens
2. Click "Create API token"
3. Token name: forensic-ctf-production
4. Permissions: Object Read & Write
5. TTL: Forever
6. Click "Create API Token"
7. Copy and save:
   - Access Key ID
   - Secret Access Key
   - Endpoint URL (format: https://[account-id].r2.cloudflarestorage.com)
```

### 2.3 Enable Public Access (for downloads)
```bash
1. Go to your bucket -> Settings
2. Public Access -> Connect Domain (optional - adds custom domain)
   OR
3. Use R2.dev subdomain:
   - Bucket Settings -> R2.dev subdomain -> Enable
   - Save the subdomain URL: https://[bucket-name].[account-id].r2.dev
```

### 2.4 Upload Artifacts
```bash
cd cases/001-the-disappearance/artifacts

# Upload to R2 using AWS CLI (R2 is S3-compatible)
# Or use Cloudflare dashboard UI to upload files
# Or use the upload script (update for R2):
```

Update `backend/scripts/upload_artifacts_001.py` to use R2:
```python
# Change MINIO_ENDPOINT to your R2 endpoint
MINIO_ENDPOINT = "[account-id].r2.cloudflarestorage.com"
```

---

## ✈️ Step 3: Deploy Backend to Fly.io (10 min)

### 3.1 Install Fly CLI
```bash
# Windows (PowerShell)
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Or download from: https://fly.io/docs/hands-on/install-flyctl/
```

### 3.2 Login and Initialize
```bash
flyctl auth login

cd D:\My projects\CTF
flyctl launch
```

When prompted:
- App name: `forensic-ctf` (or your preferred name)
- Region: Choose closest to you (sin = Singapore, iad = US East)
- Would you like to set up a Postgresql database? **NO** (we're using Supabase)
- Would you like to set up an Upstash Redis database? **NO**
- Would you like to deploy now? **NO** (we need to set secrets first)

### 3.3 Set Environment Variables
```bash
# Generate new secrets
flyctl secrets set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
flyctl secrets set FLAG_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set Supabase credentials
flyctl secrets set POSTGRES_HOST=aws-0-[region].pooler.supabase.com
flyctl secrets set POSTGRES_PORT=6543
flyctl secrets set POSTGRES_USER=postgres
flyctl secrets set POSTGRES_PASSWORD=your-supabase-password
flyctl secrets set POSTGRES_DB=postgres

# Set Cloudflare R2 credentials
flyctl secrets set MINIO_ENDPOINT=[account-id].r2.cloudflarestorage.com
flyctl secrets set MINIO_PUBLIC_ENDPOINT=https://[bucket].r2.dev
flyctl secrets set MINIO_ACCESS_KEY=your-r2-access-key
flyctl secrets set MINIO_SECRET_KEY=your-r2-secret-key
flyctl secrets set MINIO_BUCKET_NAME=forensic-ctf-artifacts

# Set other configs
flyctl secrets set ALLOWED_ORIGINS=https://your-app.vercel.app
```

### 3.4 Deploy
```bash
flyctl deploy
```

Wait 2-3 minutes for deployment. Check status:
```bash
flyctl status
flyctl logs
```

Get your app URL:
```bash
flyctl info
# Look for "Hostname: your-app.fly.dev"
```

---

## 🌐 Step 4: Deploy Frontend to Vercel (5 min)

### 4.1 Update Frontend Environment
```bash
cd frontend

# Create .env.production
echo "NEXT_PUBLIC_API_URL=https://your-app.fly.dev/api/v1" > .env.production
```

### 4.2 Push to GitHub
```bash
cd ..
git add .
git commit -m "Production deployment configuration"
git push origin main
```

### 4.3 Deploy to Vercel
```bash
1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Configure:
   - Framework Preset: Next.js
   - Root Directory: ./frontend
   - Build Command: npm run build
   - Output Directory: .next
5. Environment Variables:
   - NEXT_PUBLIC_API_URL: https://your-app.fly.dev/api/v1
6. Click "Deploy"
```

Wait 2-3 minutes. Your frontend will be live at: `https://your-project.vercel.app`

### 4.4 Update Backend CORS
```bash
# Update ALLOWED_ORIGINS with your Vercel URL
flyctl secrets set ALLOWED_ORIGINS=https://your-project.vercel.app

# Redeploy backend
flyctl deploy
```

---

## 🎯 Step 5: Run Database Migrations

```bash
# Connect to Fly.io console
flyctl ssh console

# Inside the container
cd /app
alembic upgrade head

# Exit
exit
```

---

## ✅ Step 6: Verify Deployment

### Check Backend Health
```bash
curl https://your-app.fly.dev/health
curl https://your-app.fly.dev/health/ready
```

### Check Frontend
Visit: `https://your-project.vercel.app`

### Test Full Flow
1. Register a new user (need invite code first!)
2. Create admin user:
```bash
flyctl ssh console
cd /app
python -m app.scripts.create_admin
# Enter email and password
exit
```

3. Login and test challenge submissions

---

## 📊 Monitor Your Free Resources

### Fly.io Usage
```bash
flyctl status
flyctl scale show
flyctl dashboard
```

### Supabase Usage
- Dashboard -> Settings -> Usage

### Cloudflare R2 Usage
- Dashboard -> R2 -> Your Bucket -> Metrics

---

## 🔄 Future Deployments

### Update Backend
```bash
cd D:\My projects\CTF
git push origin main
flyctl deploy
```

### Update Frontend
```bash
git push origin main
# Vercel auto-deploys from GitHub
```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
flyctl logs
flyctl status
```

### Database connection issues
- Check Supabase connection string
- Verify secrets: `flyctl secrets list`
- Check pooler is enabled (port 6543)

### Storage upload fails
- Verify R2 credentials
- Check bucket permissions
- Test connection from local first

### CORS errors
- Update ALLOWED_ORIGINS in Fly.io secrets
- Redeploy backend

---

## 💰 Cost Monitoring

All services show 0 charges if staying in free tier:
- ✅ Vercel: 100GB bandwidth/month
- ✅ Fly.io: 3 VMs × 256MB (yours uses 1)
- ✅ Supabase: 500MB database
- ✅ Cloudflare R2: 10GB storage

**You're currently using:**
- Backend: ~2GB (artifacts)
- Database: ~50-100MB
- Bandwidth: Minimal

**You're safe! 🎉**

---

## 🔐 Security Checklist

- [x] DEBUG=false in production
- [x] Strong SECRET_KEY and FLAG_SECRET_KEY
- [x] Supabase password is strong
- [x] R2 tokens have minimal permissions
- [x] CORS properly configured
- [x] HTTPS enforced everywhere
- [x] Secrets stored in Fly.io secrets (not .env files)

---

## 🚀 You're Live!

Your CTF platform is now deployed and completely free:
- Frontend: https://your-project.vercel.app
- Backend API: https://your-app.fly.dev
- Database: Supabase
- Storage: Cloudflare R2

**Total Monthly Cost: $0.00** ✨
