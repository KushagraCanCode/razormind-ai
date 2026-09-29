"""
RazorMind AI - FastAPI Backend Application
Intelligent Payment Risk & Merchant Intelligence Platform
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.services.model_registry import registry
from backend.database import engine, Base
from backend.routes import fraud, prediction, analytics, assistant, transactions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB schema, seed data if empty, and load ML models
    print("[*] Starting up RazorMind AI...")
    Base.metadata.create_all(bind=engine)
    
    # Initialize DB if database file doesn't exist
    if not os.path.exists(settings.DATABASE_PATH):
        print("[*] Seeding database for first run...")
        from database.init_db import initialize_database
        initialize_database()
        
    # Preload and train models
    registry.initialize()
    print("[+] RazorMind AI engine ready to serve requests!")
    yield
    print("[*] Shutting down RazorMind AI...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Payment Risk & Merchant Intelligence Platform for Razorpay Ecosystem",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(fraud.router, prefix=settings.API_V1_STR)
app.include_router(prediction.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)

# Mount Frontend static files
FRONTEND_DIR = os.path.join(settings.BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard/", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def serve_frontend_root():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Welcome to RazorMind AI API", "docs": "/docs"}

    @app.get("/styles.css", include_in_schema=False)
    def serve_styles_direct():
        css_file = os.path.join(FRONTEND_DIR, "styles.css")
        if os.path.exists(css_file):
            return FileResponse(css_file, media_type="text/css")
        return {"error": "styles.css not found"}

    @app.get("/app.js", include_in_schema=False)
    def serve_app_js_direct():
        js_file = os.path.join(FRONTEND_DIR, "app.js")
        if os.path.exists(js_file):
            return FileResponse(js_file, media_type="application/javascript")
        return {"error": "app.js not found"}

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if os.path.exists(settings.DATABASE_PATH) else "initializing"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
