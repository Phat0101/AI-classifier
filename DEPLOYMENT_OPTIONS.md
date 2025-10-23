# Deployment Options

This document outlines all available deployment options for the ClearAI Audit system.

## 🎯 Choose Your Deployment Method

| Method | Best For | Setup Time | Cost | Guide |
|--------|----------|------------|------|-------|
| **Local Dev** | Development & Testing | 2 min | Free | [Below](#local-development) |
| **Docker Compose** | Self-hosting, Local Production | 5 min | Free | [DOCKER_SETUP.md](DOCKER_SETUP.md) |
| **Railway** | Cloud hosting, Easy deployment | 5 min | ~$10-20/mo | [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md) |

## 🖥️ Local Development

**Quick start for development:**

```bash
./dev.sh
```

Runs:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

**Features:**
- ✅ Hot reload for both services
- ✅ Live code updates
- ✅ Full logging output
- ✅ Perfect for development

**Requirements:**
- Python 3.11+ with `uv`
- Node.js 18+ with `bun`
- `.env` file in backend directory

## 🐳 Docker Compose

**Quick start for local production:**

```bash
docker-compose up --build
```

**Features:**
- ✅ Production-like environment
- ✅ Persistent output storage
- ✅ Easy to share and reproduce
- ✅ No local dependencies needed

**Guide:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

## ☁️ Railway (Cloud)

**Quick start for cloud deployment:**

```bash
# 1. Prepare
./RAILWAY_SETUP_SCRIPT.sh

# 2. Commit and push
git add .
git commit -m "Setup for Railway"
git push

# 3. Deploy on Railway
# Follow: RAILWAY_QUICKSTART.md
```

**Features:**
- ✅ Auto-deploy from GitHub
- ✅ Built-in SSL/HTTPS
- ✅ Custom domains
- ✅ Automatic scaling
- ✅ Persistent volumes
- ✅ Zero DevOps needed

**Guides:**
- Quick: [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)
- Detailed: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

## 📁 File Paths & Configuration

All deployment methods now support automatic path detection:

### Checklists
- **Local Dev**: `/path/to/project/checklists/`
- **Docker**: `/app/checklists/` (copied or mounted)
- **Railway**: `/app/checklists/` (copied during build)

The code automatically detects the correct path!

### Output Files
- **Local Dev**: `./output/` (relative to project root)
- **Docker**: `/app/output/` (mounted to host `./output/`)
- **Railway**: `/app/output/` (persistent volume)

## 🔧 Environment Variables

### Backend

Required for all deployments:

```bash
GOOGLE_API_KEY=your_gemini_api_key
AUTH_TOKEN=your_secure_token
```

Optional:

```bash
DEBUG=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
OUTPUT_DIRECTORY=/app/output  # or custom path
```

### Frontend

Required:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # or your backend URL
```

Optional:

```bash
API_URL=http://backend:8000  # for server-side calls
```

## 🎯 Comparison Matrix

| Feature | Local Dev | Docker Compose | Railway |
|---------|-----------|----------------|---------|
| Setup Time | ⚡ 2 min | ⚡ 5 min | ⚡ 5 min |
| Cost | 💰 Free | 💰 Free | 💰 $10-20/mo |
| Internet Required | ❌ No | ❌ No | ✅ Yes |
| Hot Reload | ✅ Yes | ❌ No | ❌ No |
| Auto Deploy | ❌ No | ❌ No | ✅ Yes |
| SSL/HTTPS | ❌ No | ❌ No | ✅ Yes |
| Custom Domain | ❌ No | ⚠️ Manual | ✅ Easy |
| Persistent Storage | ✅ Yes | ✅ Yes | ✅ Yes |
| Scales Automatically | ❌ No | ❌ No | ✅ Yes |
| Maintenance | 🔧 You | 🔧 You | 🔧 Railway |

## 📝 Pre-Deployment Checklist

Before deploying to any environment:

- [ ] `.env` file configured (for local/Docker)
- [ ] Google Gemini API key obtained
- [ ] Checklists exist in `/checklists/` directory
- [ ] Dependencies installed (`uv` and `bun` for local)
- [ ] Code committed to git (for Railway)

## 🚀 Quick Command Reference

### Local Development
```bash
./dev.sh                    # Start dev servers
./backend/dev.sh           # Backend only
```

### Docker Compose
```bash
docker-compose up --build   # Build and start
docker-compose down         # Stop
docker-compose logs -f      # View logs
```

### Railway
```bash
railway login              # Login to Railway
railway link               # Link to project
railway up                 # Deploy
railway logs               # View logs
railway open               # Open in browser
```

## 📚 Additional Documentation

- **System Logic**: [AUDIT_SYSTEM_LOGIC.md](AUDIT_SYSTEM_LOGIC.md)
- **Checklist System**: [CHECKLIST_SYSTEM_SUMMARY.md](CHECKLIST_SYSTEM_SUMMARY.md)
- **Output Browser**: [OUTPUT_BROWSER_README.md](OUTPUT_BROWSER_README.md)
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## 🆘 Getting Help

**Common Issues:**
- Path resolution: [PATH_FIXES_SUMMARY.md](PATH_FIXES_SUMMARY.md)
- Docker setup: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- Railway deployment: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

**Support:**
- Check the relevant guide above
- Review logs for error messages
- Ensure environment variables are set correctly

---

Choose the deployment method that best fits your needs and follow the corresponding guide!

