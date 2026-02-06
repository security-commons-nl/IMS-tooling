from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.db import init_db
from app.api.v1.api import api_router

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Te veel inlogpogingen. Probeer het later opnieuw."},
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to the IMS API - The Gatekeeper"}
