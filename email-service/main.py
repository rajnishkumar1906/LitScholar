from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from email_app.router import router as email_router

app = FastAPI(
    title="LitScholar Email Service",
    description="Microservice for sending transactional emails",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(email_router, tags=["Email"])

@app.get("/")
async def root():
    return {"status": "online", "service": "email-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
