# Railway Deployment Guide

This guide will help you deploy the ClearAI Audit system to Railway with both backend and frontend services.

## Overview

You'll deploy two services on Railway:
1. **Backend** (FastAPI + Python)
2. **Frontend** (Next.js)

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub
3. **Railway CLI** (optional): `npm i -g @railway/cli`

## Architecture on Railway

```
Railway Project: clearai-audit
├── Service 1: Backend (Python/FastAPI)
│   ├── Port: 8000
│   ├── Volume: /app/output (for persistent storage)
│   └── Volume: /app/checklists (mounted)
└── Service 2: Frontend (Next.js)
    ├── Port: 3000
    └── Connects to Backend via internal URL
```

## Step 1: Prepare Your Repository

### 1.1 Create `.railwayignore` files

**Root `.railwayignore`:**
```
node_modules/
.next/
.git/
.vscode/
__pycache__/
*.pyc
.env
.DS_Store
output/
.uv/
```

### 1.2 Backend Configuration

The backend is already configured with the Dockerfile at `backend/Dockerfile`.

### 1.3 Frontend Configuration  

The frontend has its Dockerfile at `frontend/audit/Dockerfile`.

## Step 2: Create Railway Project

### Option A: Using Railway Dashboard (Recommended)

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `clearai-audit` repository
5. Railway will detect it's a monorepo

### Option B: Using Railway CLI

```bash
cd /Users/pat/Desktop/clearai-audit
railway login
railway init
```

## Step 3: Deploy Backend Service

### 3.1 Create Backend Service

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"**
3. Choose your repository
4. Railway will create a service

### 3.2 Configure Backend Build

**Set Root Directory:**
- Go to **Settings** → **Source**
- Set **Root Directory**: `backend`

**Build Configuration:**
- **Builder**: `Dockerfile`
- **Dockerfile Path**: `backend/Dockerfile` (Railway will find it automatically)

**Or use custom build command if not using Dockerfile:**
- **Build Command**: `pip install uv && uv sync`
- **Start Command**: `uv run granian --host 0.0.0.0 --port $PORT --interface asgi --access-log --log-level info src.ai_classifier.main:app`

### 3.3 Set Backend Environment Variables

Go to **Variables** tab and add:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
AUTH_TOKEN=your_secure_token_here

# Optional - adjust as needed
DEBUG=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
OUTPUT_DIRECTORY=/app/output

# Python/UV
PYTHONUNBUFFERED=1
```

### 3.4 Add Persistent Volume for Output

1. Go to **Settings** → **Volumes**
2. Click **"Add Volume"**
3. **Mount Path**: `/app/output`
4. **Size**: 1GB (or more depending on your needs)

### 3.5 Copy Checklists

Since checklists are small, they're already copied into the Docker image during build.

If you want to update them without rebuilding:
1. Add another volume for `/app/checklists`
2. Or set `CHECKLISTS_DIR` env var to point to a different location

## Step 4: Deploy Frontend Service

### 4.1 Create Frontend Service

1. Click **"+ New"** in your project
2. Select **"GitHub Repo"**  
3. Choose your repository again (yes, same repo, different service)

### 4.2 Configure Frontend Build

**Set Root Directory:**
- Go to **Settings** → **Source**
- Set **Root Directory**: `frontend/audit`

**Build Configuration:**
- **Builder**: `Dockerfile`
- **Dockerfile Path**: `frontend/audit/Dockerfile`

### 4.3 Set Frontend Environment Variables

Go to **Variables** tab and add:

```bash
# Backend URL - Use Railway's internal networking
# After backend is deployed, copy its internal URL
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

# For server-side calls (within Railway network)
API_URL=http://backend.railway.internal:8000
```

**Important**: Replace `your-backend.up.railway.app` with your actual backend URL from Railway.

## Step 5: Get Your Backend URL

1. Open your **Backend** service
2. Go to **Settings** → **Networking**
3. Click **"Generate Domain"** if not already generated
4. Copy the URL (e.g., `https://clearai-audit-backend.up.railway.app`)
5. Update the `NEXT_PUBLIC_API_URL` in your frontend service

## Step 6: Configure Networking

### Backend Service

1. **Settings** → **Networking**
2. **Public Networking**: ✅ Enabled
3. Note the generated domain

### Frontend Service

1. **Settings** → **Networking**
2. **Public Networking**: ✅ Enabled
3. This will be your main application URL

## Step 7: Deploy & Test

### 7.1 Deploy

Both services should auto-deploy when you:
1. Push changes to GitHub
2. Railway detects changes and rebuilds

### 7.2 Test Endpoints

**Backend Health Check:**
```bash
curl https://your-backend.up.railway.app/health
```

**Frontend:**
```bash
curl https://your-frontend.up.railway.app
```

## Step 8: Domain Setup (Optional)

### Add Custom Domain

1. Go to your **Frontend** service
2. **Settings** → **Networking**
3. Click **"Custom Domain"**
4. Add your domain (e.g., `audit.yourdomain.com`)
5. Update DNS with the provided CNAME record

## Troubleshooting

### Backend Issues

**Checklist not loading:**
```bash
# Check logs in Railway dashboard
railway logs --service backend

# The logs should show:
# "Using Docker checklist directory: /app/checklists"
```

**Fix**: Checklists should be in the Docker image. Check `backend/Dockerfile` includes:
```dockerfile
COPY checklists ./checklists
```

### Frontend Can't Connect to Backend

**Issue**: CORS or network errors

**Fix**: 
1. Ensure `NEXT_PUBLIC_API_URL` is set correctly
2. Check backend CORS settings allow your frontend domain
3. In `backend/src/ai_classifier/main.py`, update CORS if needed:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your Railway domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Volume Not Persisting

**Issue**: Output files disappear after redeploy

**Fix**:
1. Verify volume is mounted at `/app/output`
2. Check `OUTPUT_DIRECTORY=/app/output` is set
3. Volume should survive redeployments

### Build Fails

**Backend build error:**
- Check `backend/pyproject.toml` and `backend/uv.lock` are present
- Ensure Dockerfile is at `backend/Dockerfile`

**Frontend build error:**
- Check `frontend/audit/package.json` is present
- Verify `frontend/audit/Dockerfile` exists

## Monorepo Configuration

Railway supports monorepos! Key points:

1. **Same GitHub Repo**: Both services use the same repository
2. **Different Root Directories**: 
   - Backend: `backend/`
   - Frontend: `frontend/audit/`
3. **Independent Deploys**: Changes to one service don't redeploy the other

## Environment Variables Summary

### Backend
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GOOGLE_API_KEY | ✅ Yes | - | Gemini API key |
| AUTH_TOKEN | ✅ Yes | - | API authentication token |
| OUTPUT_DIRECTORY | No | ./output | Where to store output files |
| DEBUG | No | false | Enable debug mode |
| RATE_LIMIT_ENABLED | No | true | Enable rate limiting |

### Frontend
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| NEXT_PUBLIC_API_URL | ✅ Yes | - | Backend URL (browser) |
| API_URL | No | - | Backend URL (server-side) |
| NODE_ENV | Auto | production | Set by Railway |

## Cost Optimization

Railway offers:
- **Free Tier**: $5/month of usage included
- **Pay-as-you-go**: After free tier

**Tips to save costs:**
1. **Sleep inactive services**: Railway auto-sleeps after 24h of no requests
2. **Use volumes efficiently**: Only mount what you need
3. **Optimize builds**: Smaller Docker images = faster builds = lower costs

## Continuous Deployment

Railway automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Railway detects push and redeploys automatically
```

## Monitoring

### View Logs

**Dashboard:**
- Click on a service → **Logs** tab

**CLI:**
```bash
railway logs --service backend
railway logs --service frontend
```

### Metrics

Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Build time
- Response time

## Alternative: Railway Template

You can also create a Railway template button for one-click deployment:

**railway.json** (in repository root):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app

## Next Steps

1. ✅ Deploy backend service
2. ✅ Configure environment variables
3. ✅ Add persistent volume for output
4. ✅ Deploy frontend service
5. ✅ Connect frontend to backend
6. ✅ Test the application
7. 🎉 Share your deployment URL!

Your app will be live at: `https://your-frontend.up.railway.app`

