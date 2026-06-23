from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="CrisisNet Backend",
    description="Research Prototype — Not a real crisis service.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "CrisisNet backend is running"}

from app.api import websockets

app.include_router(websockets.router, tags=["websockets"])

# TODO: Include routers for messages and auth
