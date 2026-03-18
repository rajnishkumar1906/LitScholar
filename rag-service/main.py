from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager

# Silenciar advertencias
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
from starlette.middleware.sessions import SessionMiddleware

# Import routers
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
    print("🚀 LitScholar RAG Service starting...")
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
        print("🛑 LitScholar RAG Service shutting down...")
        
        # Close database connection pool
        try:
            await close_pool()
            print("✅ Database connection pool closed")
        except Exception as e:
            print(f"❌ Error closing database pool: {e}")
        
        print("=" * 50)


app = FastAPI(
    title="LitScholar RAG API",
    description="Book Recommendations and AI Assistant Service for LitScholar",
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
app.include_router(book_router, prefix="/books", tags=["Books"])
app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "service": "rag-service",
        "message": "Welcome to LitScholar RAG API",
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
