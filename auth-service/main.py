from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

# Import routers
from auth.router import router as auth_router
from users.router import router as user_router

# Import database connection pool closer
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    print("=" * 50)
    print("🚀 LitScholar Auth Service starting...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("=" * 50)
    print("🛑 LitScholar Auth Service shutting down...")
    print("=" * 50)


app = FastAPI(
    title="LitScholar Auth API",
    description="Authentication and User Management Service for LitScholar",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=3600 * 24 * 7,  # 7 days
    same_site="lax" if not settings.is_production else "none",
    https_only=settings.is_production,
    domain=None,
)

# CORS middleware
cors_origins = list(settings.cors_origins_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "service": "auth-service",
        "message": "Welcome to LitScholar Auth API",
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
