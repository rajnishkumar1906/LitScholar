from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager

# Silenciar advertencias de FutureWarning de transformers
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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Session middleware (use secret from settings if available, otherwise fallback)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY or 'AKxS4ffc9FtsVfzBwsVfzBwKxS4ffc9fc9FtsVfzBwsVfzB',
    max_age=3600 * 24 * 7,  # 7 days
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Use from settings
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include all routers with proper prefixes
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
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (only in development)"""
    if settings.ENVIRONMENT != "development":
        return {"error": "Debug endpoint only available in development"}
    
    return {
        "environment": settings.ENVIRONMENT,
        "cors_origins": settings.CORS_ORIGINS,
        "database_configured": bool(settings.DB_URL_NEON),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "google_auth_configured": bool(settings.GOOGLE_CLIENT_ID),
    }