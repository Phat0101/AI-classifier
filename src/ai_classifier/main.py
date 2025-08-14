import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
async def root():
    return {
        "message": "AI Classifier API",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-classifier"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Add your AI classification endpoints here
@app.post("/classify")
async def classify_item(item: dict):
    # Your classification logic here
    return {
        "item": item,
        "classification": "example",
        "confidence": 0.95
    }