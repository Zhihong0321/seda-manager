from fastapi import APIRouter, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import COOKIES_PATH, logger
import shutil
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    status = "Active" if os.path.exists(COOKIES_PATH) else "No Session"
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "status": status
    })

@router.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...)):
    logger.info(f"Uploading new session cookies to {COOKIES_PATH}")
    
    with open(COOKIES_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return RedirectResponse(url="/", status_code=303)
