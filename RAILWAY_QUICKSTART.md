# Railway Deployment - Quick Start

## 🚀 5-Minute Railway Deploy

### Prerequisites
- [ ] Railway account ([sign up here](https://railway.app))
- [ ] Code pushed to GitHub
- [ ] Google Gemini API key

### Step 1: Prepare Repository (2 min)

Run the setup script:
```bash
./RAILWAY_SETUP_SCRIPT.sh
```

This will:
- Copy checklists to backend directory
- Create environment variable template
- Verify all required files

Then commit and push:
```bash
git add .
git commit -m "Setup for Railway deployment"
git push origin main
```

### Step 2: Deploy Backend (2 min)

1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository
4. Click **"Add service"** → **"GitHub Repo"**

**Configure Backend:**
- **Name**: `clearai-audit-backend`
- **Settings** → **Source** → **Root Directory**: `backend`
- **Settings** → **Variables**: Copy from `RAILWAY_ENV_TEMPLATE.txt` (backend section)
  ```
  GOOGLE_API_KEY=your_actual_api_key
  AUTH_TOKEN=generate_random_string_here
  OUTPUT_DIRECTORY=/app/output
  ```
- **Settings** → **Volumes** → **Add Volume**: 
  - Mount path: `/app/output`
  - Size: 1GB

5. **Deploy** (builds automatically)
6. **Settings** → **Networking** → **Generate Domain**
7. **Copy the backend URL** (e.g., `https://clearai-audit-backend-xxx.up.railway.app`)

### Step 3: Deploy Frontend (1 min)

1. In same Railway project → **"Add service"** → **"GitHub Repo"**
2. Choose your repository again

**Configure Frontend:**
- **Name**: `clearai-audit-frontend`
- **Settings** → **Source** → **Root Directory**: `frontend/audit`
- **Settings** → **Variables**:
  ```
  NEXT_PUBLIC_API_URL=https://your-backend-url-from-step-2.up.railway.app
  ```

3. **Deploy** (builds automatically)
4. **Settings** → **Networking** → **Generate Domain**
5. **Your app is live!** 🎉

### Step 4: Test Your Deployment

Visit your frontend URL: `https://your-frontend-xxx.up.railway.app`

Test the backend health:
```bash
curl https://your-backend-xxx.up.railway.app/health
```

Should return:
```json
{"status": "healthy", "service": "ai-classifier"}
```

## 📁 What Gets Deployed

**Backend** (`backend/` directory):
- FastAPI application
- Python dependencies via `uv`
- Checklists (copied during build)
- Persistent volume for output files

**Frontend** (`frontend/audit/` directory):
- Next.js application
- Connected to backend via Railway's network
- Static assets and pages

## 🔧 Configuration Files Created

| File | Purpose |
|------|---------|
| `.railwayignore` | Exclude unnecessary files from deployment |
| `backend/railway.json` | Backend service configuration |
| `frontend/audit/railway.json` | Frontend service configuration |
| `backend/Dockerfile.railway` | Railway-optimized Docker build (optional) |
| `RAILWAY_ENV_TEMPLATE.txt` | Environment variables template |

## 🔄 Auto-Deploy

Railway automatically redeploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Railway detects and deploys automatically
```

## 💰 Costs

Railway pricing:
- **Free trial**: $5 credit
- **Hobby plan**: $5/month minimum
- **Usage based**: ~$0.000463 per GB-hour

Typical monthly cost for this app: **$10-20**

## 🐛 Troubleshooting

### Checklist Not Loading

**Check logs:**
```bash
railway logs --service clearai-audit-backend
```

**Should see:**
```
[INFO] Using Docker checklist directory: /app/checklists
```

**Fix:** Run `./RAILWAY_SETUP_SCRIPT.sh` to copy checklists to backend/

### Frontend Can't Reach Backend

**Problem**: CORS or 404 errors

**Fix:**
1. Verify `NEXT_PUBLIC_API_URL` is set correctly in frontend
2. Make sure backend URL includes `https://`
3. Check backend has generated domain

### Build Fails

**Backend:**
- Ensure `backend/checklists/` exists
- Check `pyproject.toml` and `uv.lock` are present

**Frontend:**
- Verify `package.json` exists
- Check `next.config.ts` is valid

## 📚 More Help

- **Full guide**: See `RAILWAY_DEPLOYMENT.md`
- **Railway docs**: https://docs.railway.app
- **Support**: Railway Discord

## ✅ Checklist

Before deploying:
- [ ] Run `./RAILWAY_SETUP_SCRIPT.sh`
- [ ] Commit and push to GitHub
- [ ] Have Google Gemini API key ready
- [ ] Railway account created

During deployment:
- [ ] Backend service created
- [ ] Backend environment variables set
- [ ] Backend volume added (`/app/output`)
- [ ] Backend domain generated and copied
- [ ] Frontend service created
- [ ] Frontend environment variables set (with backend URL)
- [ ] Frontend domain generated

After deployment:
- [ ] Test backend health endpoint
- [ ] Test frontend loads
- [ ] Upload and process a test file
- [ ] Check output browser works
- [ ] Verify checklists load correctly

---

**That's it!** Your ClearAI Audit system is now live on Railway 🚀

