# Deploy to Google Cloud Run

## Why Cloud Run?
- **Generous free tier**: 2 million requests/month, 360,000 GB-seconds
- **Up to 4GB RAM** (way more than other free tiers!)
- Scales to zero (no cost when idle)
- Very reliable infrastructure
- Fast deployments

## Free Tier Limits
- 2 million requests/month
- 360,000 GB-seconds of compute time/month
- 1GB outbound data/month
- **Example**: 1GB RAM app running 24/7 = ~100 hours free/month
- Perfect for CTF with light usage

## Quick Start

### 1. Prerequisites
- Google account
- Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install

Or use Cloud Shell (built into Google Cloud Console - no installation needed!)

### 2. Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Click project dropdown → **"New Project"**
3. Name: `forensic-ctf`
4. Click **"Create"**
5. Wait for project creation, then select it

### 3. Enable Required APIs
In Cloud Console:
1. Go to **"APIs & Services"** → **"Enable APIs and Services"**
2. Search and enable:
   - **Cloud Run API**
   - **Cloud Build API**
   - **Artifact Registry API**

Or via CLI:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 4. Deploy from GitHub (Easiest Method)

#### Option A: Using Cloud Console (Recommended)

1. Go to **Cloud Run** in Google Cloud Console
2. Click **"Create Service"**
3. Select **"Continuously deploy from a repository"**
4. Click **"Set up with Cloud Build"**
5. Connect your GitHub:
   - Provider: **GitHub**
   - Repository: `adikul1023/myCTF`
   - Branch: `^main$`
   - Build type: **Dockerfile**
   - Dockerfile path: `docker/Dockerfile.backend`
6. Click **"Next"**

Configure service:
- **Service name**: `forensic-ctf`
- **Region**: `us-central1` (or closest to you)
- **CPU allocation**: CPU is only allocated during request processing
- **Ingress**: Allow all traffic
- **Authentication**: Allow unauthenticated invocations

Expand **"Container, Variables & Secrets, Connections, Security"**:

**Container:**
- Port: `8000`
- Memory: `1 GiB` (start here, can increase to 4GB if needed)
- CPU: `1`
- Request timeout: `300` seconds
- Maximum requests per container: `80`

**Variables & Secrets** - Add environment variables:
```
SECRET_KEY=iqduiLnGQkfmWfhbmbJ8hsKad5RREsgRlQTmYyGU5fg
FLAG_SECRET_KEY=l1IsjSzw6cMDv-ZpM33uuJuLPwjSvhPtCCqggcUddYk
DEBUG=false
MINIO_USE_SSL=true
POSTGRES_PORT=5432
ARGON2_MEMORY_COST=32768
ARGON2_TIME_COST=4
ARGON2_PARALLELISM=2

POSTGRES_HOST=<your-supabase-host>
POSTGRES_USER=<your-supabase-user>
POSTGRES_PASSWORD=<your-supabase-password>
POSTGRES_DB=postgres

MINIO_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_PUBLIC_ENDPOINT=<account-id>.r2.cloudflarestorage.com
MINIO_ACCESS_KEY=<your-r2-access-key>
MINIO_SECRET_KEY=<your-r2-secret-key>
MINIO_BUCKET_NAME=forensic-ctf-artifacts

ALLOWED_ORIGINS=https://ctf.adi-kulkarni.in
```

7. Click **"Create"**
8. Wait 3-5 minutes for first build

#### Option B: Using gcloud CLI

```bash
# Clone your repo locally
cd "D:\My projects\CTF"

# Set your project
gcloud config set project forensic-ctf

# Deploy
gcloud run deploy forensic-ctf \
  --source . \
  --dockerfile docker/Dockerfile.backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "DEBUG=false,MINIO_USE_SSL=true,POSTGRES_PORT=5432,ARGON2_MEMORY_COST=32768,ARGON2_TIME_COST=4,ARGON2_PARALLELISM=2" \
  --set-secrets "SECRET_KEY=SECRET_KEY:latest,FLAG_SECRET_KEY=FLAG_SECRET_KEY:latest" \
  # ... add more env vars
```

### 5. Get Your Service URL

After deployment:
```bash
gcloud run services describe forensic-ctf --region us-central1 --format 'value(status.url)'
```

Your URL will be like: `https://forensic-ctf-XXXXX-uc.a.run.app`

### 6. Update Frontend (Vercel)

```bash
# Set new backend URL
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://forensic-ctf-XXXXX-uc.a.run.app

# Redeploy
vercel --prod
```

### 7. Update CORS

Go back to Cloud Run → Your Service → **Edit & Deploy New Revision**

Update environment variable:
```
ALLOWED_ORIGINS=https://ctf.adi-kulkarni.in
```

Click **"Deploy"**

## Cost Optimization

### Monitor Usage
1. Go to **Cloud Run** → Your Service → **Metrics**
2. Check request count and memory usage
3. Adjust memory if needed (can go as low as 512Mi)

### Set Budget Alerts
1. Go to **Billing** → **Budgets & Alerts**
2. Create budget: $5/month
3. Set alerts at 50%, 90%, 100%

### Reduce Costs
- **Memory**: Start with 1GB, reduce to 512MB if stable
- **Min instances**: Keep at 0 (scales to zero when idle)
- **Max instances**: Set to 3-5 to prevent runaway costs

## Testing

```powershell
# Test health
Invoke-WebRequest -Uri "https://forensic-ctf-XXXXX-uc.a.run.app/health"

# Test login
Invoke-WebRequest -Uri "https://forensic-ctf-XXXXX-uc.a.run.app/api/v1/auth/login" `
  -Method POST `
  -Body '{"email":"admin@forensic-ctf.local","password":"your-password"}' `
  -ContentType "application/json"
```

## Continuous Deployment

Once set up with Cloud Build, every push to `main` branch will:
1. Trigger automatic build
2. Deploy new revision
3. Zero downtime (gradual traffic shift)

View builds: **Cloud Build** → **History**

## Troubleshooting

### View Logs
```bash
gcloud run services logs read forensic-ctf --region us-central1 --limit 50
```

Or in Console: **Cloud Run** → Your Service → **Logs**

### Common Issues

**"Service unhealthy"**
- Check logs for startup errors
- Verify environment variables
- Ensure port 8000 is correct

**"Memory limit exceeded"**
- Increase memory: Edit service → Change to 2GB
- Check for memory leaks in logs

**"Cold starts slow"**
- Set min instances to 1 (costs ~$4/month but eliminates cold starts)

## Custom Domain (Optional)

1. Go to **Cloud Run** → Your Service → **Manage Custom Domains**
2. Add your domain
3. Verify ownership
4. Update DNS records

## Advantages Over Other Platforms

✅ **1GB RAM free tier** (vs 256MB Fly.io, 512MB Render/Koyeb)
✅ **No build errors** - Google infrastructure is rock solid
✅ **Scales automatically** - handles traffic spikes
✅ **Pay per use** - only charged for actual usage
✅ **Fast cold starts** - ~1 second
✅ **Built-in CDN** - fast globally

## Monthly Cost Estimate

**Free tier usage (typical CTF):**
- 10,000 requests/month: **FREE** (under 2M limit)
- 100 hours at 1GB: **FREE** (under 360k GB-seconds)
- Data transfer: Minimal

**If exceeded (unlikely):**
- $0.00002400 per request (after 2M)
- $0.00001800 per GB-second (after free tier)
- Usually stays under $1/month for small CTF

## Next Steps

1. Deploy to Cloud Run (steps above)
2. Test thoroughly
3. Update Vercel frontend URL
4. Set up budget alerts
5. Monitor for a few days

Good luck! Cloud Run is very reliable and should work perfectly for your CTF platform.
