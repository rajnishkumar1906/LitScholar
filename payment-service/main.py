from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from payment_app.router import router as payment_router

app = FastAPI(
    title="LitScholar Payment Service",
    description="Microservice for handling payments and subscriptions",
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
app.include_router(payment_router, tags=["Payment"])

@app.get("/")
async def root():
    return {"status": "online", "service": "payment-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
