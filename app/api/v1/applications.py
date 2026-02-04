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
        
        # Find all table rows with application data
        # SEDA uses full URLs like https://atap.seda.gov.my/applications/{id}/applicant
        rows = re.findall(
            r'<tr>\s*<td>(\d+)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>',
            response.text,
            re.DOTALL | re.IGNORECASE
        )
        
        for row_num, name_cell, status_cell, date_cell, actions_cell in rows:
            # Extract app ID and name from name_cell
            app_link_match = re.search(
                r'href="https://atap\.seda\.gov\.my/applications/(\d+)/applicant"[^>]*>([^<]+)</a>',
                name_cell
            )
            
            if app_link_match:
                app_id = app_link_match.group(1)
                applicant_name = app_link_match.group(2).strip()
                
                # Extract registration number
                reg_no_match = re.search(r'Reg\. No: ([^<]+)', name_cell)
                reg_no = reg_no_match.group(1).strip() if reg_no_match else None
                
                # Extract category
                category_match = re.search(r'Category: ([^<]+)', name_cell)
                category = category_match.group(1).strip() if category_match else None
                
                # Extract ATP number (application number)
                atp_match = re.search(r'<strong>(ATP\d+)</strong>', name_cell)
                atp_number = atp_match.group(1) if atp_match else None
                
                # Extract status from status_cell
                status_match = re.search(r'>([^<]+)</span>', status_cell)
                app_status = status_match.group(1).strip() if status_match else "Unknown"
                
                applications.append({
                    "id": app_id,
                    "applicant": applicant_name,
                    "application_number": atp_number,
                    "registration_number": reg_no,
                    "category": category,
                    "status": app_status,
                    "row_number": int(row_num),
                    "url": f"/applications/{app_id}/applicant"
                })
        
        # Fallback: if table parsing didn't work, try link patterns
        if not applications:
            app_links = re.findall(
                r'href="https://atap\.seda\.gov\.my/applications/(\d+)/applicant"[^>]*>([^<]+)</a>',
                response.text
            )
            for app_id, name in app_links:
                applications.append({
                    "id": app_id,
                    "applicant": name.strip(),
                    "url": f"/applications/{app_id}/applicant"
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
