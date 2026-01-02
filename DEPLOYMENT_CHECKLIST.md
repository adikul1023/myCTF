# 🎯 Production Deployment Checklist

Use this checklist to ensure everything is configured correctly before going live.

---

## ☁️ **1. Cloud Accounts Setup**

### Vercel (Frontend)
- [ ] Account created at vercel.com
- [ ] GitHub connected to Vercel
- [ ] Repository access granted

### Fly.io (Backend)
- [ ] Account created at fly.io
- [ ] Credit card added (for verification, won't be charged on free tier)
- [ ] flyctl CLI installed
- [ ] Logged in: `flyctl auth login`

### Supabase (Database)
- [ ] Account created at supabase.com
- [ ] New project created
- [ ] Database password saved securely
- [ ] Connection string copied (transaction pooler, port 6543)

### Cloudflare (Storage)
- [ ] Account created at cloudflare.com
- [ ] R2 bucket created
- [ ] R2 API token generated
- [ ] R2.dev subdomain enabled OR custom domain configured
- [ ] Endpoint and credentials saved

---

## 🔐 **2. Secrets & Configuration**

### Generated Secrets
- [ ] SECRET_KEY generated (32+ bytes)
- [ ] FLAG_SECRET_KEY generated (32+ bytes)
- [ ] All secrets saved in password manager

### Supabase Configuration
- [ ] Connection string format verified:
  ```
  postgresql://postgres.[ref]:[pwd]@aws-0-[region].pooler.supabase.com:6543/postgres
  ```
- [ ] Using transaction pooler (port 6543, NOT 5432)
- [ ] Database accessible from internet

### Cloudflare R2 Configuration
- [ ] Endpoint format correct: `account-id.r2.cloudflarestorage.com`
- [ ] Public URL configured (R2.dev or custom domain)
- [ ] API token has Object Read & Write permissions
- [ ] Bucket name recorded

---

## 📦 **3. Code Preparation**

### Environment Files
- [ ] `.env.production.example` reviewed
- [ ] `.env.production` created locally (NOT committed)
- [ ] All placeholder values replaced with real credentials

### Git Repository
- [ ] Code committed to GitHub/GitLab
- [ ] `.env` files in `.gitignore`
- [ ] No hardcoded secrets in code
- [ ] Latest changes pushed to main branch

### Database
- [ ] Migration files present in `backend/alembic/versions/`
- [ ] All 4 migrations ready: 001, 002, 003, 004
- [ ] Challenge data seeded

---

## 🚀 **4. Backend Deployment (Fly.io)**

### Initial Setup
- [ ] `flyctl launch` completed
- [ ] App name chosen and available
- [ ] Region selected (closest to target users)
- [ ] PostgreSQL: Selected "NO" (using Supabase)
- [ ] fly.toml file created

### Environment Variables Set
```bash
- [ ] SECRET_KEY
- [ ] FLAG_SECRET_KEY
- [ ] POSTGRES_HOST
- [ ] POSTGRES_PORT=6543
- [ ] POSTGRES_USER=postgres
- [ ] POSTGRES_PASSWORD
- [ ] POSTGRES_DB=postgres
- [ ] MINIO_ENDPOINT
- [ ] MINIO_PUBLIC_ENDPOINT
- [ ] MINIO_ACCESS_KEY
- [ ] MINIO_SECRET_KEY
- [ ] MINIO_BUCKET_NAME
- [ ] ALLOWED_ORIGINS (will update after Vercel)
```

### Deployment
- [ ] `flyctl deploy` successful
- [ ] No build errors
- [ ] Health checks passing: `flyctl status`
- [ ] Logs clean: `flyctl logs`
- [ ] API accessible: `curl https://your-app.fly.dev/health`

### Database Migrations
- [ ] Migrations run: `flyctl ssh console` → `alembic upgrade head`
- [ ] Tables created in Supabase (check via SQL Editor)
- [ ] Challenges table has 5 challenges
- [ ] No migration errors

### Admin User
- [ ] Admin user created: `python -m app.scripts.create_admin`
- [ ] Admin login tested
- [ ] Invite code generated for testing

---

## 🎨 **5. Frontend Deployment (Vercel)**

### Environment Configuration
- [ ] `.env.production` created in frontend/
- [ ] `NEXT_PUBLIC_API_URL` set to Fly.io URL
- [ ] Format: `https://your-app.fly.dev/api/v1`

### Vercel Project Setup
- [ ] Repository imported in Vercel
- [ ] Framework preset: Next.js
- [ ] Root directory: `./frontend`
- [ ] Build command: `npm run build`
- [ ] Environment variables added in Vercel dashboard

### Deployment
- [ ] Build successful
- [ ] No build errors
- [ ] Site accessible at Vercel URL
- [ ] No console errors in browser

### CORS Update
- [ ] Copy Vercel URL
- [ ] Update backend CORS: `flyctl secrets set ALLOWED_ORIGINS=https://your-app.vercel.app`
- [ ] Backend redeployed: `flyctl deploy`

---

## 📦 **6. Storage Setup (Cloudflare R2)**

### Artifacts Upload
- [ ] All artifact files zipped
- [ ] Files uploaded to R2 bucket (via dashboard or CLI)
- [ ] Correct folder structure: `cases/[case-id]/`
- [ ] Files publicly accessible via R2.dev URL

### Database Records
- [ ] Artifacts table has correct R2 paths
- [ ] File sizes match actual files
- [ ] Storage paths start with `cases/`
- [ ] Download links work from frontend

---

## ✅ **7. Testing**

### Backend API
- [ ] Health check: `curl https://your-app.fly.dev/health`
- [ ] Ready check: `curl https://your-app.fly.dev/health/ready`
- [ ] API docs (if DEBUG=true): `https://your-app.fly.dev/docs`

### Frontend
- [ ] Homepage loads
- [ ] Login page accessible
- [ ] No CORS errors in console
- [ ] API requests working

### User Flow
- [ ] Can register with invite code
- [ ] Can login
- [ ] Can view cases
- [ ] Can download artifacts
- [ ] Can submit challenges
- [ ] Correct answers accepted
- [ ] Incorrect answers rejected
- [ ] Points awarded correctly

### Admin Flow
- [ ] Admin can login
- [ ] Admin dashboard accessible
- [ ] Can create invite codes
- [ ] Can view submissions

---

## 📊 **8. Monitoring**

### Resource Usage
- [ ] Fly.io dashboard checked
- [ ] 1 VM running, 256MB memory
- [ ] Supabase usage < 500MB
- [ ] R2 storage < 10GB
- [ ] Vercel bandwidth monitored

### Logs
- [ ] Backend logs monitored: `flyctl logs`
- [ ] No error spikes
- [ ] Authentication working
- [ ] Submissions logging correctly

---

## 🔒 **9. Security**

### Configuration
- [ ] DEBUG=false in production
- [ ] HTTPS enforced everywhere
- [ ] Secure secrets (32+ bytes)
- [ ] CORS properly restricted
- [ ] Rate limiting enabled

### Secrets
- [ ] No secrets in Git
- [ ] Secrets stored in Fly.io secrets
- [ ] .env files in .gitignore
- [ ] Database password strong (16+ chars)

### Access
- [ ] Supabase password not default
- [ ] R2 tokens have minimal permissions
- [ ] Admin password strong
- [ ] Invite codes generated

---

## 📝 **10. Documentation**

- [ ] DEPLOYMENT_GUIDE.md read
- [ ] QUICK_REFERENCE.md bookmarked
- [ ] Credentials saved in password manager
- [ ] URLs documented:
  - Frontend: ________________
  - Backend: ________________
  - Database: ________________
  - Storage: ________________

---

## 🎉 **Ready to Launch!**

If all checkboxes are ticked, you're ready to go live! 🚀

**Post-Launch:**
- Monitor logs for first 24 hours
- Test with real users
- Watch for errors
- Monitor free tier usage

**Need Help?**
- Fly.io: https://fly.io/docs/
- Supabase: https://supabase.com/docs
- Cloudflare: https://developers.cloudflare.com/r2/
- Vercel: https://vercel.com/docs

---

**Current Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete
