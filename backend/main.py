from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager
import os

# Silenciar advertencias
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
from starlette.middleware.sessions import SessionMiddleware

# Import routers
from auth.router import router as auth_router
from users.router import router as user_router
from books.router import router as book_router
from assistant.router import router as assistant_router

# Import database connection pool closer
from retrieval.neon_fetch import close_pool
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    print("=" * 50)
    print("🚀 LitScholar API starting...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")
    print(f"🔌 Render detected: {settings.RENDER}")
    print("=" * 50)
    
    # Startup
    try:
        yield
    finally:
        # Shutdown - clean up resources
        print("=" * 50)
        print("🛑 LitScholar API shutting down...")
        
        # Close database connection pool
        try:
            await close_pool()
            print("✅ Database connection pool closed")
        except Exception as e:
            print(f"❌ Error closing database pool: {e}")
        
        print("=" * 50)


app = FastAPI(
    title="LitScholar API",
    description="Backend API for LitScholar - book recommendations & AI assistant",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else "/docs",  # Keep docs accessible
    redoc_url="/redoc" if not settings.is_production else "/redoc",
    openapi_url="/openapi.json" if not settings.is_production else "/openapi.json",
)

# Session middleware - Updated for production
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=3600 * 24 * 7,  # 7 days
    same_site="lax" if not settings.is_production else "none",  # 'none' for cross-site in production
    https_only=settings.is_production,  # True in production, False in development
    domain=None,  # Let browser handle domain
)

# CORS middleware - ensure localhost is always allowed in development
cors_origins = list(settings.cors_origins_list)
if not settings.is_production:
    dev_origin = "http://localhost:5173"
    if dev_origin not in cors_origins:
        cors_origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Include all routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(book_router, prefix="/books", tags=["Books"])
app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "message": "Welcome to LitScholar API",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "version": app.version,
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "books": "/books",
            "assistant": "/assistant"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "LitScholar API",
        "environment": settings.ENVIRONMENT,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

# Debug endpoint - only in development
if not settings.is_production:
    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to check configuration (only in development)"""
        return {
            "environment": settings.ENVIRONMENT,
            "cors_origins": settings.cors_origins_list,
            "database_configured": bool(settings.DB_URL_NEON),
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "render_detected": settings.RENDER,
        }

# For Render - bind to correct port
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not settings.is_production)