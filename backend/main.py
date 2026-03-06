from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from auth.router import router as auth_router
from books.router import router as books_router
from assistant.router import router as assistant_router
from users.router import router as user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("BookBuddy API starting...")
    yield
    print("BookBuddy API shutting down...")

app = FastAPI(
    title="BookBuddy API",
    description="Backend API for BookBuddy - book recommendations & AI assistant",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    SessionMiddleware,
    secret_key='AKxS4ffc9FtsVfzBwsVfzBwKxS4ffc9fc9FtsVfzBwsVfzB'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,  # Must be True for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["*"],
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}