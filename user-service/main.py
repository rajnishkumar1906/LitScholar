from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from auth.router import router as auth_router
from users.router import router as user_router

from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    print("=" * 50)
    print("🚀 LitScholar Identity Service starting...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("=" * 50)
    print("🛑 LitScholar Identity Service shutting down...")
    print("=" * 50)


app = FastAPI(
    title="LitScholar Identity API",
    description="Identity, Authentication and User Management Service for LitScholar",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware - MUST be first
if settings.ENVIRONMENT == "development":
    # Use explicit origins instead of "*" when allow_credentials=True
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

# Global Exception Handler for better error logging and CORS on error
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print("=" * 50)
    print(f"!!! UNHANDLED EXCEPTION: {type(exc).__name__}: {str(exc)}")
    print(f"Path: {request.url.path}")
    print(traceback.format_exc())
    print("=" * 50)
    
    # Return 500 with a detail message
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        # CORS headers are usually handled by middleware, 
        # but in case of early crash we can add them here
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "false",
        }
    )

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "service": "identity-service",
        "message": "Welcome to LitScholar Identity API",
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)