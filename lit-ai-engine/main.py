from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager

# Silence warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Import routers
from books.router import router as book_router
from assistant.router import router as assistant_router
from assistant.quiz_router import router as quiz_router

# Import database connection pool closer
from retrieval.neon_fetch import close_pool
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    print("=" * 50)
    print("🚀 LitScholar lit-ai-engine starting...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")
    print(f"🔌 User Service URL: {settings.USER_SERVICE_URL}")
    print("=" * 50)
    
    try:
        yield
    finally:
        print("=" * 50)
        print("🛑 LitScholar lit-ai-engine shutting down...")
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

# REMOVED: SessionMiddleware (no longer needed)

# CORS middleware - allow_credentials=True since we use cookies
if settings.ENVIRONMENT == "development":
    cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
else:
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

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print("=" * 50)
    print(f"!!! RAG SERVICE UNHANDLED EXCEPTION: {type(exc).__name__}: {str(exc)}")
    print(f"Path: {request.url.path}")
    print(traceback.format_exc())
    print("=" * 50)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "false",
        }
    )

# Include routers
app.include_router(book_router, prefix="/books", tags=["Books"])
app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])
app.include_router(quiz_router, prefix="/quiz", tags=["Quiz"])

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "service": "lit-ai-engine",
        "message": "Welcome to LitScholar RAG API",
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)