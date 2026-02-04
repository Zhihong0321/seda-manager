from fastapi import APIRouter, HTTPException, Query
from app.wrapper.seda_wrapper import SEDAClient, SEDASessionExpired
from typing import List, Optional, Dict, Any
import re

router = APIRouter()


@router.get("/search")
async def search_applications(
    keyword: Optional[str] = Query(None, description="Search keyword (name, IC, company reg no)"),
    ca: Optional[str] = Query(None, description="CA/SEDA Officer filter"),
    status: Optional[str] = Query(None, description="Application status filter")
):
    """
    Search applications with optional filters.
    Returns a list of applications matching the search criteria.
    """
    try:
        client = SEDAClient()
        
        # Build query parameters
        params = []
        if ca:
            params.append(f"ca={ca}")
        if keyword:
            params.append(f"keyword={keyword}")
        if status:
            params.append(f"status={status}")
        
        query_string = "&".join(params) if params else ""
        url = f"/applications?{query_string}" if query_string else "/applications"
        
        response = client.session.get(f"{client.base_url}{url}", timeout=30)
        client._validate_response(response)
        
        # Parse the HTML to extract applications
        applications = []
        
        # Look for application entries in the table
        # Pattern matches table rows with application data
        app_patterns = re.findall(
            r'<tr[^>]*>.*?<a href="/applications/(\d+)/applicant"[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>',
            response.text,
            re.DOTALL | re.IGNORECASE
        )
        
        for app_id, col1, col2, col3 in app_patterns:
            # Clean up HTML tags
            clean_col1 = re.sub(r'<[^>]+>', '', col1).strip()
            clean_col2 = re.sub(r'<[^>]+>', '', col2).strip()
            clean_col3 = re.sub(r'<[^>]+>', '', col3).strip()
            
            applications.append({
                "id": app_id,
                "applicant": clean_col1,
                "application_number": clean_col2,
                "status": clean_col3,
                "url": f"/applications/{app_id}/applicant"
            })
        
        # If no patterns matched, try alternative patterns
        if not applications:
            # Look for application links
            app_links = re.findall(r'href="(/applications/(\d+)/applicant)"[^>]*>([^<]*)', response.text)
            for url_path, app_id, text in app_links:
                applications.append({
                    "id": app_id,
                    "applicant": text.strip(),
                    "url": url_path
                })
        
        return {
            "success": True,
            "count": len(applications),
            "filters": {
                "keyword": keyword,
                "ca": ca,
                "status": status
            },
            "applications": applications
        }
        
    except SEDASessionExpired:
        raise HTTPException(status_code=401, detail="Session expired. Please update cookies.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search applications: {str(e)}")


@router.get("/")
async def list_applications(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    ca: Optional[str] = Query(None, description="CA filter"),
    status: Optional[str] = Query(None, description="Status filter")
):
    """
    List all applications with optional filtering.
    Same as search but with simpler naming.
    """
    return await search_applications(keyword=keyword, ca=ca, status=status)


@router.get("/{application_id}")
async def get_application_details(application_id: str):
    """
    Get detailed information for a specific application.
    Returns comprehensive application data including equipment details.
    """
    try:
        client = SEDAClient()
        
        url = f"{client.base_url}/applications/{application_id}/applicant"
        response = client.session.get(url, timeout=30)
        client._validate_response(response)
        
        html = response.text
        
        # Extract application number (ATP format)
        atp_match = re.search(r'ATP\d+', html)
        application_number = atp_match.group(0) if atp_match else None
        
        # Extract consumer/profile information
        consumer_info = {}
        
        # Look for consumer name
        consumer_match = re.search(
            r'consumer[^>]*>\s*([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL
        )
        if consumer_match:
            consumer_info["name"] = consumer_match.group(1).strip()
        
        # Extract all form data
        form_data = {}
        
        # Get all input fields
        inputs = re.findall(
            r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"[^>]*/?>',
            html,
            re.IGNORECASE
        )
        for name, value in inputs:
            if name not in ['_token', '_method']:
                form_data[name] = value
        
        # Get all select fields (selected values)
        selects = re.findall(
            r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        for name, options in selects:
            selected = re.search(
                r'<option[^>]*selected[^>]*>([^<]*)',
                options,
                re.IGNORECASE
            )
            if selected:
                form_data[name] = selected.group(1).strip()
        
        # Extract equipment details from table data
        equipment = []
        table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL)
        
        for row in table_rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.IGNORECASE | re.DOTALL)
            clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
            
            # Look for equipment data patterns
            if len(clean_cells) >= 4:
                # Check if this looks like equipment data
                if any(keyword in ' '.join(clean_cells).upper() for keyword in ['SOLAR', 'PANEL', 'INVERTER', 'Wp', 'kW']):
                    equipment.append({
                        "type": clean_cells[0] if len(clean_cells) > 0 else None,
                        "technology": clean_cells[1] if len(clean_cells) > 1 else None,
                        "model": clean_cells[2] if len(clean_cells) > 2 else None,
                        "capacity": clean_cells[3] if len(clean_cells) > 3 else None,
                        "quantity": clean_cells[4] if len(clean_cells) > 4 else None
                    })
        
        # Extract status information
        status_badges = re.findall(
            r'<span[^>]*class="[^"]*badge[^"]*"[^>]*>(.*?)</span>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        statuses = [re.sub(r'<[^>]+>', '', badge).strip() for badge in status_badges]
        
        return {
            "success": True,
            "application_id": application_id,
            "application_number": application_number,
            "url": f"/applications/{application_id}/applicant",
            "consumer": consumer_info,
            "form_data": form_data,
            "equipment": equipment,
            "status_badges": statuses
        }
        
    except SEDASessionExpired:
        raise HTTPException(status_code=401, detail="Session expired. Please update cookies.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get application details: {str(e)}")


@router.get("/{application_id}/raw")
async def get_application_raw_html(application_id: str):
    """
    Get raw HTML content for a specific application.
    Useful for debugging and development.
    """
    try:
        client = SEDAClient()
        
        url = f"{client.base_url}/applications/{application_id}/applicant"
        response = client.session.get(url, timeout=30)
        client._validate_response(response)
        
        return {
            "success": True,
            "application_id": application_id,
            "html_length": len(response.text),
            "html_preview": response.text[:2000]  # First 2000 chars
        }
        
    except SEDASessionExpired:
        raise HTTPException(status_code=401, detail="Session expired. Please update cookies.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get application: {str(e)}")
