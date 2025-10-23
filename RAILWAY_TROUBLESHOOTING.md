# Railway Deployment Troubleshooting

## Common Issues and Solutions

### Issue 1: `exec: uv: not found` or `exec: bun: not found`

**Problem:** Railway is running `start.sh` instead of using the Dockerfile.

**Solution:**

1. **Verify Railway is set to use Dockerfile:**
   - Go to your service in Railway
   - Click **Settings** → **Build**
   - Ensure **Builder** is set to `Dockerfile`
   - Ensure **Root Directory** is set correctly:
     - Backend: `backend`
     - Frontend: `frontend/audit`

2. **Check `railway.json` exists in the root directory:**
   - Backend: `backend/railway.json`
   - Frontend: `frontend/audit/railway.json`

3. **Disable auto-detection:**
   - Railway might be auto-detecting and ignoring your Dockerfile
   - In **Settings** → **Build**, explicitly set:
     - Build Command: (leave empty - Dockerfile will handle it)
     - Start Command: (leave empty - Dockerfile CMD will handle it)

### Issue 2: Files Not Found During Build

**Problem:** `COPY` commands fail in Dockerfile.

**Solution for Backend:**

Ensure you've run the setup script:
```bash
./RAILWAY_SETUP_SCRIPT.sh
git add .
git commit -m "Add checklists to backend"
git push origin main
```

This copies checklists to `backend/checklists/` which the Dockerfile expects.

**Solution for Frontend:**

Make sure these files exist in `frontend/audit/`:
- `package.json`
- `bun.lock`
- All source files in `src/`

### Issue 3: Port Binding Issues

**Problem:** Application starts but Railway can't connect to it.

**Solution:**

Railway provides `$PORT` environment variable. Our Dockerfiles now use this:

**Backend Dockerfile:**
```dockerfile
CMD ["sh", "-c", "uv run granian --host 0.0.0.0 --port ${PORT:-8000} ..."]
```

**Frontend:** Automatically handled by Next.js standalone mode.

### Issue 4: Build Context Problems

**Problem:** Different behavior between local Docker and Railway.

**Explanation:**

We have different build contexts:

**For Docker Compose** (local):
- Context: Project root (`/Users/pat/Desktop/clearai-audit`)
- Uses: `docker-compose.yml` with root context
- Dockerfile: Expects files from root

**For Railway**:
- Context: Service root directory (`backend/` or `frontend/audit/`)
- Uses: `railway.json` to specify Dockerfile
- Dockerfile: Expects files relative to service root

**Solution:**

We maintain service-specific files:
- `backend/Dockerfile` - Works with `backend/` as context (for Railway)
- `backend/Dockerfile.compose` - Works with root as context (for docker-compose)

Railway should use `backend/Dockerfile` with root directory set to `backend`.

### Issue 5: Environment Variables Not Set

**Problem:** Application fails with missing API keys or config.

**Solution:**

1. Go to Railway service → **Variables**
2. Add all required environment variables:

**Backend:**
```bash
GOOGLE_API_KEY=your_actual_api_key
AUTH_TOKEN=your_secure_token
OUTPUT_DIRECTORY=/app/output
DEBUG=false
RATE_LIMIT_ENABLED=true
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://your-backend-xxx.up.railway.app
NODE_ENV=production
```

### Issue 6: Checklist Files Not Found

**Problem:** Runtime error: `Checklist file not found`

**Solution:**

1. Ensure checklists were copied to backend:
   ```bash
   ls -la backend/checklists/
   # Should show: au_checklist.json, nz_checklist.json
   ```

2. If missing, run setup script:
   ```bash
   ./RAILWAY_SETUP_SCRIPT.sh
   ```

3. Commit and push:
   ```bash
   git add backend/checklists/
   git commit -m "Add checklists for Railway"
   git push origin main
   ```

4. Redeploy in Railway (or it will auto-deploy on push)

### Issue 7: Volume/Output Directory Issues

**Problem:** Files saved but disappear after restart.

**Solution:**

1. Add persistent volume in Railway:
   - Go to service → **Settings** → **Volumes**
   - Click **Add Volume**
   - Mount path: `/app/output`
   - Size: 1GB or more

2. Ensure environment variable is set:
   ```bash
   OUTPUT_DIRECTORY=/app/output
   ```

### Issue 8: CORS Errors

**Problem:** Frontend can't connect to backend.

**Solution:**

1. Verify environment variables in frontend:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-actual-backend-url.up.railway.app
   ```

2. Ensure backend CORS is configured (already done in code):
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Allows all origins
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. Check backend logs for connection attempts

## Railway Configuration Checklist

### Backend Service Setup

- [ ] **Root Directory:** `backend`
- [ ] **Builder:** Dockerfile
- [ ] **Dockerfile Path:** `Dockerfile` (or leave empty)
- [ ] **Environment Variables:** Added from template
- [ ] **Volume:** `/app/output` mounted
- [ ] **Domain:** Generated
- [ ] **Health Check:** `/health` (optional)

### Frontend Service Setup

- [ ] **Root Directory:** `frontend/audit`
- [ ] **Builder:** Dockerfile
- [ ] **Dockerfile Path:** `Dockerfile` (or leave empty)
- [ ] **Environment Variables:** `NEXT_PUBLIC_API_URL` set with backend URL
- [ ] **Domain:** Generated

## Debugging Commands

### View Railway Logs

**Dashboard:**
- Click service → **Logs** tab

**CLI:**
```bash
railway logs --service backend
railway logs --service frontend
```

### Check Build Logs

Look for these indicators of success:

**Backend:**
```
Successfully installed dependencies
Collecting src...
Building Docker image...
Pushing to registry...
```

**Frontend:**
```
Installing dependencies with bun...
Building Next.js application...
Creating standalone output...
```

### Test Endpoints

**Backend Health:**
```bash
curl https://your-backend.up.railway.app/health
# Should return: {"status":"healthy","service":"ai-classifier"}
```

**Frontend:**
```bash
curl https://your-frontend.up.railway.app
# Should return HTML
```

## Still Having Issues?

1. **Check Railway Status:** https://status.railway.app
2. **Review Full Logs:** Railway dashboard → Service → Logs
3. **Verify GitHub Sync:** Railway should show latest commit
4. **Try Manual Redeploy:** Service → Settings → Redeploy
5. **Check Railway Discord:** https://discord.gg/railway

## Quick Fix Checklist

If your deployment is failing:

1. ✅ Confirm root directory is set correctly
2. ✅ Verify builder is set to "Dockerfile"
3. ✅ Check all environment variables are present
4. ✅ Ensure `backend/checklists/` directory exists in repo
5. ✅ Verify Dockerfile has correct COPY paths
6. ✅ Check logs for specific error messages
7. ✅ Ensure latest code is pushed to GitHub
8. ✅ Try manual redeploy after fixes

## Contact & Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Your Repo:** https://github.com/Phat0101/AI-classifier

