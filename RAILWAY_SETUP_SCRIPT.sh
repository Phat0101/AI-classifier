#!/bin/bash
# Railway Deployment Setup Script
# This script prepares your repository for Railway deployment

set -e

echo "🚂 Setting up ClearAI Audit for Railway deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Copy checklists to backend directory for Railway build
echo -e "${BLUE}[1/4]${NC} Copying checklists to backend directory..."
if [ -d "checklists" ]; then
    cp -r checklists backend/
    echo -e "${GREEN}✓${NC} Checklists copied to backend/"
else
    echo -e "${YELLOW}⚠${NC} Warning: checklists directory not found in project root"
fi

# 2. Ensure .railwayignore exists
echo -e "${BLUE}[2/4]${NC} Checking for .railwayignore..."
if [ -f ".railwayignore" ]; then
    echo -e "${GREEN}✓${NC} .railwayignore found"
else
    echo -e "${YELLOW}⚠${NC} Warning: .railwayignore not found"
fi

# 3. Check required files
echo -e "${BLUE}[3/4]${NC} Verifying required files..."

required_files=(
    "backend/Dockerfile"
    "backend/pyproject.toml"
    "backend/uv.lock"
    "frontend/audit/Dockerfile"
    "frontend/audit/package.json"
)

all_files_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓${NC} $file"
    else
        echo -e "${YELLOW}  ✗${NC} $file (missing)"
        all_files_present=false
    fi
done

# 4. Create environment variable template
echo -e "${BLUE}[4/4]${NC} Creating environment variable template..."

cat > RAILWAY_ENV_TEMPLATE.txt << 'EOF'
# Railway Environment Variables Template
# Copy these to your Railway service settings

# ============================================
# BACKEND SERVICE VARIABLES
# ============================================

# Required
GOOGLE_API_KEY=your_gemini_api_key_here
AUTH_TOKEN=your_secure_random_token_here

# Optional - adjust as needed
DEBUG=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
OUTPUT_DIRECTORY=/app/output
PYTHONUNBUFFERED=1

# ============================================
# FRONTEND SERVICE VARIABLES
# ============================================

# Required - Update after backend is deployed
NEXT_PUBLIC_API_URL=https://your-backend-service.up.railway.app
API_URL=http://backend.railway.internal:8000

# Node environment (set automatically by Railway)
NODE_ENV=production

# ============================================
# NOTES
# ============================================
# 1. Replace 'your_gemini_api_key_here' with your actual Google Gemini API key
# 2. Replace 'your_secure_random_token_here' with a secure random string
# 3. After deploying backend, copy its Railway URL to NEXT_PUBLIC_API_URL
# 4. The API_URL uses Railway's internal networking for server-side requests
EOF

echo -e "${GREEN}✓${NC} Environment variable template created: RAILWAY_ENV_TEMPLATE.txt"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Railway Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Commit and push these changes to GitHub:"
echo "   ${YELLOW}git add .${NC}"
echo "   ${YELLOW}git commit -m 'Setup for Railway deployment'${NC}"
echo "   ${YELLOW}git push origin main${NC}"
echo ""
echo "2. Go to railway.app and create a new project"
echo ""
echo "3. Deploy Backend Service:"
echo "   - Connect your GitHub repository"
echo "   - Set root directory: ${YELLOW}backend${NC}"
echo "   - Add environment variables from ${YELLOW}RAILWAY_ENV_TEMPLATE.txt${NC}"
echo "   - Add volume: ${YELLOW}/app/output${NC} (for persistent storage)"
echo ""
echo "4. Deploy Frontend Service:"
echo "   - Connect same GitHub repository"
echo "   - Set root directory: ${YELLOW}frontend/audit${NC}"
echo "   - Add environment variables (update with backend URL)"
echo ""
echo "5. Full guide available in: ${YELLOW}RAILWAY_DEPLOYMENT.md${NC}"
echo ""
echo -e "${GREEN}🎉 Ready to deploy to Railway!${NC}"

