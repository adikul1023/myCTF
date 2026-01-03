# Deploy to Render.com

## Why Render?
- **512MB RAM** (2x Fly.io's 256MB)
- Free tier
- Easy Docker deployment
- No crashes on login!

## Quick Start

### 1. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub

### 2. Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository: `adikul1023/myCTF`
3. Configure:
   - **Name**: `forensic-ctf`
   - **Region**: Singapore (closest to you)
   - **Branch**: `main`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./docker/Dockerfile.backend`
   - **Docker Context**: `.`
   - **Plan**: Free

### 3. Add Environment Variables

**Click "Advanced" and add these secrets:**

```bash
# Application Secrets (from Fly.io)
SECRET_KEY=<your-secret-key>
FLAG_SECRET_KEY=<your-flag-secret-key>

# Database (Supabase - same as before)
POSTGRES_HOST=<your-supabase-host>
POSTGRES_USER=postgres.your-project
POSTGRES_PASSWORD=<your-supabase-password>
POSTGRES_DB=postgres

# Storage (Cloudflare R2 - same as before)
MINIO_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_PUBLIC_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_ACCESS_KEY=<your-r2-access-key>
MINIO_SECRET_KEY=<your-r2-secret-key>
MINIO_BUCKET_NAME=forensic-ctf-artifacts

# CORS - UPDATE THIS!
ALLOWED_ORIGINS=https://ctf.adi-kulkarni.in
```

**Get secrets from Fly.io:**
```powershell
flyctl secrets list
```

### 4. Deploy
1. Click "Create Web Service"
2. Wait 3-5 minutes for first deploy
3. Your backend URL will be: `https://forensic-ctf.onrender.com`

### 5. Update Frontend (Vercel)

Update environment variable in Vercel:
- **Variable**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://forensic-ctf.onrender.com`

Or via CLI:
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://forensic-ctf.onrender.com
```

Then redeploy frontend:
```bash
vercel --prod
```

### 6. Update CORS on Render

Once frontend is deployed, go back to Render dashboard:
1. Click your service → "Environment"
2. Update `ALLOWED_ORIGINS` to: `https://ctf.adi-kulkarni.in`
3. Save (auto-redeploys)

## Important Notes

### Cold Starts
- Free tier **sleeps after 15 minutes** of inactivity
- First request after sleep takes **30-60 seconds**
- Subsequent requests are instant
- **Solution**: Use a service like [UptimeRobot](https://uptimerobot.com/) to ping every 10 minutes (keeps it awake)

### Memory
- 512MB RAM is plenty for logins and downloads
- Argon2 configured for 32MB (still secure)
- Presigned URLs mean zero memory for downloads

## Testing

After deployment:
```powershell
# Test health
Invoke-WebRequest -Uri "https://forensic-ctf.onrender.com/health"

# Test login (should NOT crash!)
Invoke-WebRequest -Uri "https://forensic-ctf.onrender.com/api/v1/auth/login" -Method POST -Body '{"email":"admin@forensic-ctf.local","password":"your-password"}' -ContentType "application/json"
```

## Monitoring

View logs:
1. Render Dashboard → Your Service → "Logs"
2. Real-time logs visible in browser

## Troubleshooting

### "Service Unavailable"
- Wait 60 seconds (cold start)
- Check logs for errors

### CORS Errors
- Verify `ALLOWED_ORIGINS` includes your Vercel domain
- Must be exact match (no trailing slash)

### Database Connection Failed
- Verify Supabase credentials
- Check if Supabase allows connections from Render IPs

## Cost
- **Free tier**: 512MB RAM, 750 hours/month
- Zero cost if you don't exceed limits
- Auto-sleep keeps you well under 750 hours
