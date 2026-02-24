from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from auth.router import router as auth_router
from books.router import router as books_router
from assistant.router import router as assistant_router
from users.router import router as user_router

# Optional: if you have startup/shutdown logic (e.g. Chroma client, DB pool, etc.)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 BookBuddy API starting...")
    yield
    # Shutdown: runs when server stops
    print("🛑 BookBuddy API shutting down...")


app = FastAPI(
    title="BookBuddy API",
    description="Backend API for BookBuddy - book recommendations & AI assistant",
    version="0.1.0",
    lifespan=lifespan,  # optional but nice
    docs_url="/docs",   # Swagger UI
    redoc_url="/redoc", # ReDoc UI (alternative docs)
    openapi_url="/openapi.json",
)

app.add_middleware(
    SessionMiddleware,
    secret_key='AKxS4ffc9FtsVfzBwsVfzBwKxS4ffc9fc9FtsVfzBwsVfzB'
)

# Enable CORS - VERY IMPORTANT for React frontend running on different port (5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # if you ever use create-react-app
        "*"                       # ← temporary for dev; tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(books_router, prefix="/books", tags=["Books"])
app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])


@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to BookBuddy API",
        "docs": "/docs",
        "version": app.version
    }


# Optional: health check endpoint (useful for monitoring/load balancers)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "uptime": "running"}