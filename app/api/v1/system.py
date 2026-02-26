from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from app.core.config import COOKIES_PATH, get_storage_health, get_db_connection, SEDA_BASE_URL, logger
from app.wrapper.seda_wrapper import SEDAClient, SEDASessionExpired
import json
import os
import requests
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """
    Reports the health of the API server, including:
    - Storage availability
    - Database connectivity
    - SEDA cookie health/validity
    """
    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "storage": {},
            "database": {},
            "seda_session": {}
        }
    }
    
    # 1. Storage Check
    storage_health = get_storage_health()
    result["checks"]["storage"] = {
        "status": storage_health["status"],
        "writable": storage_health["writable"],
        "cookies_exist": storage_health["cookies_exist"],
        "message": storage_health["message"]
    }
    
    # 2. Database Check
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        result["checks"]["database"] = {
            "status": "healthy",
            "connected": True
        }
    except Exception as e:
        result["checks"]["database"] = {
            "status": "error",
            "connected": False,
            "message": str(e)
        }
        result["status"] = "degraded"
    
    # 3. SEDA Cookie Check
    if not storage_health["cookies_exist"]:
        result["checks"]["seda_session"] = {
            "status": "missing",
            "valid": False,
            "message": "No cookies uploaded yet."
        }
        if result["status"] == "healthy":
            result["status"] = "warning"
    else:
        try:
            client = SEDAClient()
            # Perform a lightweight validation request
            response = client.session.get(f"{SEDA_BASE_URL}/profiles", timeout=10)
            
            if "/login" in response.url:
                result["checks"]["seda_session"] = {
                    "status": "expired",
                    "valid": False,
                    "message": "Session expired. Please re-login on SEDA portal."
                }
                result["status"] = "warning"
            elif response.status_code == 200:
                result["checks"]["seda_session"] = {
                    "status": "healthy",
                    "valid": True,
                    "message": "Session is active."
                }
            else:
                result["checks"]["seda_session"] = {
                    "status": "unknown",
                    "valid": None,
                    "message": f"Unexpected SEDA status code: {response.status_code}"
                }
        except SEDASessionExpired:
            result["checks"]["seda_session"] = {
                "status": "expired",
                "valid": False,
                "message": "Session expired."
            }
            result["status"] = "warning"
        except Exception as e:
            result["checks"]["seda_session"] = {
                "status": "error",
                "valid": False,
                "message": f"Connection error: {str(e)}"
            }
            result["status"] = "degraded"
            
    return result

@router.post("/update-cookies")
async def update_cookies(cookies: List[Dict[str, Any]] = Body(...)):
    """
    Updates the SEDA session cookies.
    Expects a list of cookie objects as returned by chrome.cookies.getAll().
    """
    try:
        if not cookies:
            raise HTTPException(status_code=400, detail="No cookies provided.")
            
        # Log basic info about cookies received (don't log the actual values for security)
        logger.info(f"Received {len(cookies)} cookies from extension for update.")
        
        # Save to cookies.json
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=4)
            
        # Verify the new cookies work
        try:
            client = SEDAClient()
            response = client.session.get(f"{SEDA_BASE_URL}/profiles", timeout=10)
            if "/login" in response.url:
                return {
                    "success": True,
                    "message": "Cookies saved, but they appear to be invalid or expired on SEDA.",
                    "valid": False
                }
            return {
                "success": True,
                "message": "Cookies updated and verified successfully.",
                "valid": True
            }
        except Exception as e:
            return {
                "success": True,
                "message": f"Cookies saved, but verification failed: {str(e)}",
                "valid": False
            }
            
    except Exception as e:
        logger.error(f"Failed to update cookies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
