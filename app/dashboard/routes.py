from fastapi import APIRouter, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.config import COOKIES_PATH, logger, get_storage_health, get_db_connection, STORAGE_DIR
from app.wrapper.seda_wrapper import SEDAClient, SEDASessionExpired
import shutil
import os
import requests
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, handshake: str = None):
    status = "Active" if os.path.exists(COOKIES_PATH) else "No Session"
    storage_health = get_storage_health()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "status": status,
        "storage": storage_health,
        "handshake": handshake
    })


@router.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...)):
    logger.info(f"Uploading new session cookies to {COOKIES_PATH}")
    
    with open(COOKIES_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return RedirectResponse(url="/", status_code=303)


@router.get("/api/handshake")
async def api_handshake():
    """
    Comprehensive health check that verifies:
    1. Storage system (Railway volume or local)
    2. Database connectivity
    3. SEDA cookie validity (by making a test request)
    """
    result = {
        "overall_status": "unknown",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "storage": {},
            "database": {},
            "seda_cookies": {}
        },
        "message": ""
    }
    
    # 1. Storage Check
    storage_health = get_storage_health()
    result["checks"]["storage"] = {
        "status": storage_health["status"],
        "path": storage_health["path"],
        "is_railway_volume": storage_health["is_railway_volume"],
        "writable": storage_health["writable"],
        "cookies_exist": storage_health["cookies_exist"],
        "cookies_size_kb": round(storage_health["cookies_size"] / 1024, 2) if storage_health["cookies_size"] > 0 else 0
    }
    
    # 2. Database Check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        result["checks"]["database"] = {
            "status": "healthy",
            "connected": True,
            "message": "Database connection successful"
        }
    except Exception as e:
        result["checks"]["database"] = {
            "status": "error",
            "connected": False,
            "message": str(e)
        }
    
    # 3. SEDA Cookie Validity Check
    if not storage_health["cookies_exist"]:
        result["checks"]["seda_cookies"] = {
            "status": "error",
            "valid": False,
            "message": "No cookies file found. Please upload cookies."
        }
    else:
        try:
            client = SEDAClient()
            # Make a lightweight request to verify session
            response = client.session.get(f"{client.session.headers.get('Host', 'https://atap.seda.gov.my')}/profiles", 
                                         timeout=10,
                                         allow_redirects=True)
            
            # Check if we got redirected to login
            if "/login" in response.url:
                result["checks"]["seda_cookies"] = {
                    "status": "error",
                    "valid": False,
                    "message": "Session expired. Cookies are invalid or expired.",
                    "redirected_to": response.url
                }
            elif response.status_code == 200:
                # Try to extract profile count as additional verification
                profiles = client.fetch_profile_list()
                result["checks"]["seda_cookies"] = {
                    "status": "healthy",
                    "valid": True,
                    "message": f"Session valid. Found {len(profiles)} profiles.",
                    "profile_count": len(profiles)
                }
            else:
                result["checks"]["seda_cookies"] = {
                    "status": "warning",
                    "valid": None,
                    "message": f"Unexpected status code: {response.status_code}"
                }
        except SEDASessionExpired:
            result["checks"]["seda_cookies"] = {
                "status": "error",
                "valid": False,
                "message": "Session expired. Please upload fresh cookies from SEDA portal."
            }
        except requests.RequestException as e:
            result["checks"]["seda_cookies"] = {
                "status": "error",
                "valid": False,
                "message": f"Network error: {str(e)}"
            }
        except Exception as e:
            result["checks"]["seda_cookies"] = {
                "status": "error",
                "valid": False,
                "message": f"Error: {str(e)}"
            }
    
    # Determine overall status
    statuses = [
        result["checks"]["storage"]["status"],
        result["checks"]["database"]["status"],
        result["checks"]["seda_cookies"]["status"]
    ]
    
    if all(s == "healthy" for s in statuses):
        result["overall_status"] = "healthy"
        result["message"] = "All systems operational. SEDA connection verified."
    elif "error" in statuses:
        result["overall_status"] = "error"
        error_checks = [k for k, v in result["checks"].items() if v["status"] == "error"]
        result["message"] = f"Issues detected in: {', '.join(error_checks)}"
    else:
        result["overall_status"] = "warning"
        result["message"] = "Some systems may have issues. Review details below."
    
    return JSONResponse(content=result)
