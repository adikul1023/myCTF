# Deploy to Koyeb

## Why Koyeb?
- **512MB RAM free tier** (always-on, no sleep!)
- No cold starts
- Easy Docker deployment
- Fast and reliable

## Quick Start

### 1. Create Koyeb Account
1. Go to https://koyeb.com
2. Sign up with GitHub

### 2. Create New App
1. Click **"Create App"**
2. Select **"GitHub"** as deployment method
3. Connect your repository: `adikul1023/myCTF`
4. Configure:
   - **Repository**: `adikul1023/myCTF`
   - **Branch**: `main`
   - **Builder**: Docker
   - **Dockerfile**: `docker/Dockerfile.backend`
   - **Port**: `8000`
   - **Name**: `forensic-ctf`
   - **Region**: Any (Frankfurt or Washington DC recommended)
   - **Instance**: Free (Eco - 512MB RAM)

### 3. Add Environment Variables

Click **"Advanced"** → **"Environment Variables"** and add:

```bash
# Application Secrets
SECRET_KEY=iqduiLnGQkfmWfhbmbJ8hsKad5RREsgRlQTmYyGU5fg
FLAG_SECRET_KEY=l1IsjSzw6cMDv-ZpM33uuJuLPwjSvhPtCCqggcUddYk

# Configuration
DEBUG=false
MINIO_USE_SSL=true
POSTGRES_PORT=5432
ARGON2_MEMORY_COST=32768
ARGON2_TIME_COST=4
ARGON2_PARALLELISM=2

# Database (Supabase)
POSTGRES_HOST=<your-supabase-host>
POSTGRES_USER=<your-supabase-user>
POSTGRES_PASSWORD=<your-supabase-password>
POSTGRES_DB=postgres

# Storage (Cloudflare R2)
MINIO_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_PUBLIC_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_ACCESS_KEY=<your-r2-access-key>
MINIO_SECRET_KEY=<your-r2-secret-key>
MINIO_BUCKET_NAME=forensic-ctf-artifacts

# CORS
ALLOWED_ORIGINS=https://ctf.adi-kulkarni.in
```

### 4. Deploy
1. Click **"Deploy"**
2. Wait 3-5 minutes for build
3. Your backend URL will be: `https://forensic-ctf-XXXXX.koyeb.app`

### 5. Update Frontend (Vercel)

Update environment variable in Vercel:
```bash
NEXT_PUBLIC_API_URL=https://forensic-ctf-XXXXX.koyeb.app
```

Then redeploy:
```bash
vercel --prod
```

### 6. Update CORS

Once you have your Koyeb URL, go back and verify `ALLOWED_ORIGINS` includes your Vercel domain.

## Benefits vs Render
- ✅ No sleep (always-on)
- ✅ No cold starts
- ✅ More reliable build servers
- ✅ Same 512MB RAM
- ✅ Free tier

## Testing

After deployment:
```powershell
# Test health
Invoke-WebRequest -Uri "https://forensic-ctf-XXXXX.koyeb.app/health"

# Test login
Invoke-WebRequest -Uri "https://forensic-ctf-XXXXX.koyeb.app/api/v1/auth/login" -Method POST -Body '{"email":"admin@forensic-ctf.local","password":"your-password"}' -ContentType "application/json"
```

## Monitoring

- View logs in Koyeb Dashboard → Your App → "Logs" tab
- Check metrics in "Metrics" tab

## Cost
- **Free tier**: 512MB RAM, always-on
- No time limits
- Zero cost for single app
