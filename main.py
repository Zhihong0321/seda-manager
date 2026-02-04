import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.v1 import profiles, applications
from app.dashboard import routes as dashboard
from app.wrapper.seda_wrapper import SEDASessionExpired, SEDAException
from app.core.config import APP_NAME, logger

app = FastAPI(
    title=APP_NAME,
    description="Refined Wrapper API for SEDA Malaysia",
    version="1.1.0"
)

# Global Exception Handlers
@app.exception_handler(SEDASessionExpired)
async def session_expired_handler(request: Request, exc: SEDASessionExpired):
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "message": str(exc)},
    )

@app.exception_handler(SEDAException)
async def seda_exception_handler(request: Request, exc: SEDAException):
    return JSONResponse(
        status_code=500,
        content={"error": "SEDA Integration Error", "message": str(exc)},
    )

# Static Files
if not os.path.exists("app/static"):
    os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["Applications"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "app": APP_NAME}

import os