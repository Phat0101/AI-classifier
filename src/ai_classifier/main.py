import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# Load .env from project root explicitly
_ROOT_DOTENV = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=_ROOT_DOTENV, override=False)

# Get environment variables
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

app = FastAPI(
    title="AI Classifier",
    version="0.1.0",
    debug=DEBUG,
    docs_url="/docs" if DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount AU classifier routes first
from .au.classifier import router as au_router
app.include_router(au_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-classifier"}

@app.get("/api/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Mount static files for frontend
frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if frontend_path.exists():
    print(f"Mounting frontend from: {frontend_path}")
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Root route to serve the frontend
@app.get("/")
async def serve_frontend():
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(frontend_file))
    else:
        return {"message": "AI Classifier API", "version": "0.1.0", "frontend": "not found"}