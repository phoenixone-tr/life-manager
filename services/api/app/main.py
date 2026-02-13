from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings

app = FastAPI(title="Life Manager API", version="0.1.0")

settings = Settings()

if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {
        "message": "Life Manager API",
        "docs": "/docs",
    }
