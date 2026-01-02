# 🚀 Quick Reference - Production Deployment

## Your Stack (100% Free)
- 🎨 Frontend: Vercel
- ⚡ Backend: Fly.io
- 🗄️ Database: Supabase (500MB free)
- 📦 Storage: Cloudflare R2 (10GB free)

---

## Essential Commands

### Fly.io Backend
```bash
# Login
flyctl auth login

# Deploy
flyctl deploy

# View logs
flyctl logs

# Check status
flyctl status

# SSH into container
flyctl ssh console

# Set environment variable
flyctl secrets set KEY=value

# List secrets
flyctl secrets list

# Scale (if needed - costs money!)
flyctl scale vm shared-cpu-1x --memory 512
```

### Vercel Frontend
```bash
# Deploy from git push
git push origin main  # Auto-deploys

# Or manual deploy
cd frontend
vercel --prod
```

### Database Migrations
```bash
# From local (after updating Supabase connection)
cd backend
alembic upgrade head

# Or from Fly.io console
flyctl ssh console
cd /app
alembic upgrade head
```

### Create Admin User
```bash
flyctl ssh console
python -m app.scripts.create_admin
```

---

## Environment Variables

### Required Fly.io Secrets
```bash
flyctl secrets set SECRET_KEY=xxx
flyctl secrets set FLAG_SECRET_KEY=xxx
flyctl secrets set POSTGRES_HOST=xxx.supabase.com
flyctl secrets set POSTGRES_PORT=6543
flyctl secrets set POSTGRES_USER=postgres
flyctl secrets set POSTGRES_PASSWORD=xxx
flyctl secrets set POSTGRES_DB=postgres
flyctl secrets set MINIO_ENDPOINT=xxx.r2.cloudflarestorage.com
flyctl secrets set MINIO_PUBLIC_ENDPOINT=https://xxx.r2.dev
flyctl secrets set MINIO_ACCESS_KEY=xxx
flyctl secrets set MINIO_SECRET_KEY=xxx
flyctl secrets set MINIO_BUCKET_NAME=forensic-ctf-artifacts
flyctl secrets set ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Vercel Environment Variables
```
NEXT_PUBLIC_API_URL=https://your-app.fly.dev/api/v1
```

---

## URLs to Remember

**Get Supabase Connection String:**
- Dashboard → Settings → Database → Connection String (Transaction pooler, port 6543)

**Get Cloudflare R2 Credentials:**
- Dashboard → R2 → Manage R2 API Tokens

**Get R2 Public URL:**
- Bucket → Settings → R2.dev subdomain

**Your Fly.io App URL:**
```bash
flyctl info  # Shows hostname
```

---

## Monitoring Free Tier Usage

### Fly.io (256MB free)
```bash
flyctl dashboard
```
Check: Machines, Usage

### Supabase (500MB free)
Dashboard → Settings → Usage

### Cloudflare R2 (10GB free)
Dashboard → R2 → Bucket → Metrics

### Vercel (100GB bandwidth free)
Dashboard → Project → Usage

---

## Troubleshooting

### Backend won't start
```bash
flyctl logs         # Check logs
flyctl status       # Check status
flyctl secrets list # Verify secrets
```

### Database connection fails
- Use **transaction pooler** (port 6543), not direct connection (port 5432)
- Check Supabase password
- Verify connection string format

### CORS errors
```bash
# Update CORS origins
flyctl secrets set ALLOWED_ORIGINS=https://new-url.vercel.app
flyctl deploy
```

### Upload to R2 fails
- Check R2 credentials
- Verify bucket exists
- Endpoint should NOT include https://

---

## Cost Tracking

You're safe as long as:
- ✅ Fly.io: 1 VM × 256MB (yours: ✅)
- ✅ Supabase: < 500MB DB (yours: ~100MB ✅)
- ✅ R2: < 10GB storage (yours: 2GB ✅)
- ✅ Vercel: < 100GB bandwidth/month ✅

**Current monthly cost: $0.00** 🎉

---

## Quick Deployment Workflow

1. **Make changes locally**
2. **Test locally** with `docker-compose up`
3. **Commit and push**
   ```bash
   git add .
   git commit -m "Update"
   git push origin main
   ```
4. **Deploy backend**
   ```bash
   flyctl deploy
   ```
5. **Frontend auto-deploys** from git push (Vercel)

---

## Support Links

- [Fly.io Docs](https://fly.io/docs/)
- [Supabase Docs](https://supabase.com/docs)
- [Cloudflare R2 Docs](https://developers.cloudflare.com/r2/)
- [Vercel Docs](https://vercel.com/docs)
