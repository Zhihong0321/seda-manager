import requests
import json
import re
import os
from typing import List, Dict, Optional
from app.core.config import SEDA_BASE_URL, USER_AGENT, COOKIES_PATH, logger

class SEDAException(Exception):
    """Base exception for SEDA Client errors."""
    pass

class SEDASessionExpired(SEDAException):
    """Raised when the session is no longer valid."""
    pass

class SEDAParsingError(SEDAException):
    """Raised when HTML parsing fails."""
    pass

class SEDAClient:
    """
    Reverse-engineered client for interacting with the SEDA eATAP portal.
    Handles authentication, CSRF tokens, and resource management.
    """
    
    def __init__(self, cookies_path: str = COOKIES_PATH):
        self.cookies_path = cookies_path
        self.base_url = SEDA_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self._initialize_session()

    def _initialize_session(self):
        """Loads cookies from storage if available."""
        if not os.path.exists(self.cookies_path):
            logger.warning(f"Cookies file not found at {self.cookies_path}")
            return

        try:
            with open(self.cookies_path, 'r') as f:
                cookie_list = json.load(f)
            
            for cookie in cookie_list:
                self.session.cookies.set(
                    name=cookie['name'], 
                    value=cookie['value'], 
                    domain=cookie.get('domain', '')
                )
            logger.info("Successfully initialized SEDA session from cookies.")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")

    def _validate_response(self, response: requests.Response):
        """Checks if the response indicates an expired session or error."""
        if "/login" in response.url:
            logger.error("Session expired: Redirected to login page.")
            raise SEDASessionExpired("The SEDA session has expired. Please update cookies.")
        response.raise_for_status()

    def _fetch_csrf_token(self, url: str) -> str:
        """Extracts the CSRF token from the specified page."""
        logger.debug(f"Fetching CSRF token from {url}")
        response = self.session.get(url)
        self._validate_response(response)
        
        match = re.search(r'name="_token" value="([^"]+)"', response.text)
        if not match:
            raise SEDAParsingError(f"CSRF token not found at {url}")
        
        return match.group(1)

    def fetch_profile_list(self, search: Optional[str] = None, registration_number: Optional[str] = None, profile_type: Optional[str] = None, max_pages: int = 5) -> List[Dict]:
        """
        Scrapes the client profile list from the portal.
        Supports server-side search and multi-page fetching.
        """
        profiles = []
        seen_ids = set()
        
        base_url = f"{SEDA_BASE_URL}/profiles"
        params = {
            'search': search or "",
            'registration_number': registration_number or "",
            'type': profile_type or ""
        }

        for page in range(1, max_pages + 1):
            current_params = params.copy()
            if page > 1:
                current_params['page'] = page
            
            logger.info(f"Fetching client profiles page {page} with params {current_params}...")
            response = self.session.get(base_url, params=current_params)
            self._validate_response(response)

            # Pattern to extract ID, Type, Name, and Reg No from table rows
            row_pattern = re.compile(
                r'<tr>\s*<td>.*?</td>\s*<td><a href="([^"]+)">\s*(.*?)\s*</a>\s*</td>\s*<td>\s*(.*?)\s*</td>\s*<td>\s*(.*?)\s*</td>',
                re.DOTALL | re.IGNORECASE
            )
            
            page_matches = 0
            for match in row_pattern.findall(response.text):
                url_path = match[0]
                parts = url_path.split('/')
                profile_id = parts[-2]
                
                if profile_id not in seen_ids:
                    profiles.append({
                        "id": profile_id,
                        "type": parts[-3],  # 'individuals' or 'companies'
                        "name": match[1].strip(),
                        "registration_number": match[2].strip(),
                        "category": match[3].strip(),
                        "url": url_path
                    })
                    seen_ids.add(profile_id)
                    page_matches += 1
            
            if page_matches == 0:
                break
                
            # If we got fewer than 10 rows, it's likely the last page (SEDA uses 10 per page)
            if page_matches < 10:
                break
                
        logger.info(f"Extracted {len(profiles)} profiles across {page} pages.")
        return profiles

    def fetch_individual_details(self, profile_id: str) -> Dict:
        """Retrieves all form fields for a specific individual profile."""
        url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
        logger.info(f"Fetching details for individual profile {profile_id}")
        
        response = self.session.get(url)
        self._validate_response(response)

        # 1. Extract standard text/hidden inputs
        inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', response.text)
        details = {name: value for name, value in inputs if name != '_token'}
        
        # 2. Extract selected values from dropdowns
        select_names = re.findall(r'<select[^>]*name="([^"]+)"', response.text)
        for name in select_names:
            select_regex = fr'<select[^>]*name="{name}"[\s\S]*?</select>'
            select_block = re.search(select_regex, response.text)
            if select_block:
                selected_opt = re.search(r'<option[^>]*selected[^>]*>(.*?)</option>', select_block.group(0))
                details[name] = selected_opt.group(1).strip() if selected_opt else ""
                
        return details

    def create_individual_profile(self, data: Dict) -> Dict:
        """Creates a new individual profile."""
        url = f"{SEDA_BASE_URL}/profiles/individuals"
        
        try:
            token = self._fetch_csrf_token(url)
            
            # Replicate browser behavior: Double CSRF token (Laravel pattern)
            payload = [
                ('_token', token),
                ('_token', token)
            ]
            
            # 1. Define the full set of fields required by SEDA (from HAR)
            seda_fields = [
                'salutation', 'name', 'citizenship', 'mykad_passport', 'email',
                'address_line_1', 'address_line_2', 'address_line_3', 'postcode',
                'town', 'state', 'phone', 'mobile',
                'contact_salutation', 'contact_name', 'contact_mykad_passport',
                'contact_citizenship', 'contact_relationship', 'contact_email',
                'contact_phone', 'contact_mobile'
            ]
            
            # 2. Build the payload ensuring ALL fields are present
            for field in seda_fields:
                value = data.get(field, "")
                
                # HAR Source of Truth: salutation has '.', contact_salutation does NOT
                if field == 'salutation' and value and not str(value).endswith('.'):
                    value = f"{value}."
                
                if field in ['mykad_passport', 'contact_mykad_passport'] and value:
                    # Remove dashes/spaces from MyKad/Passport
                    value = re.sub(r'[^0-9A-Za-z]', '', str(value))
                
                # SEDA validation fix: contact_phone cannot be blank. Fallback to contact_mobile.
                if field == 'contact_phone' and not value:
                    value = data.get('contact_mobile', '')
                
                payload.append((field, str(value) if value is not None else ""))
            
            logger.debug(f"Final SEDA Payload: {payload}")
            logger.info(f"Submitting new individual profile for: {data.get('name')}")
            # allow_redirects=False so we can see the exact redirect
            response = self.session.post(url, data=payload, headers={'Referer': url}, allow_redirects=True)
            
            # Success check 1: Redirected to list or LANDED on list?
            # On success, SEDA redirects to /profiles/individuals
            target_name = data.get('name', '').strip().upper()
            
            if response.url.endswith('/profiles/individuals') or target_name in response.text.upper():
                # Try to find ID in the current response (it might be the list already)
                match = re.search(fr'href="[^"]*/profiles/individuals/(\d+)/edit"[^>]*>\s*{re.escape(target_name)}', response.text, re.IGNORECASE)
                profile_id = match.group(1) if match else None
                
                # If not found on the immediate page, check the first 2 pages of the list
                if not profile_id:
                    for page in [1, 2]:
                        list_page = self.session.get(f"{SEDA_BASE_URL}/profiles/individuals?page={page}")
                        match = re.search(fr'href="[^"]*/profiles/individuals/(\d+)/edit"[^>]*>\s*{re.escape(target_name)}', list_page.text, re.IGNORECASE)
                        if match:
                            profile_id = match.group(1)
                            break
                
                logger.info(f"Profile creation confirmed for {target_name} (ID: {profile_id})")
                return {
                    "success": True,
                    "profile_id": profile_id,
                    "redirect_url": response.url,
                    "message": "Profile created successfully."
                }
            
            # Search for ANY kind of error message (Flash, Toastr, etc.)
            error_msgs = []
            # 1. Laravel Validation Errors
            error_msgs.extend(re.findall(r'<span class="invalid-feedback" role="alert">[\s\S]*?<strong>(.*?)</strong>', response.text))
            
            # 2. Flash Messages (Success/Danger alerts)
            error_msgs.extend(re.findall(r'alert alert-danger[\s\S]*?>(.*?)</div>', response.text, re.DOTALL))
            
            # 3. Toastr/Swal errors
            error_msgs.extend(re.findall(r'toastr\.error\("(.*?)"', response.text))
            error_msgs.extend(re.findall(r'swal\(\{[\s\S]*?text:\s*"(.*?)"', response.text))
            
            if error_msgs:
                clean_errors = [re.sub(r'<[^>]+>', '', e).strip() for e in error_msgs]
                return {"success": False, "error": f"Portal Error: {', '.join(set(clean_errors))}"}
            
            return {
                "success": False, 
                "error": "Profile not found in list. It might be a duplicate MyKad or the session timed out.",
                "final_url": response.url
            }
            
        except Exception as e:
            logger.error(f"Profile creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_individual_profile(self, profile_id: str, data: Dict) -> Optional[str]:
        """
        Performs a PUT update for an individual profile.
        Note: SEDA creates a NEW profile ID for every update. This method searches
        for and returns the newly generated ID.
        """
        url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
        
        try:
            token = self._fetch_csrf_token(url)
            
            # Replicate browser behavior: Laravel PUT spoofing + double token
            payload = [
                ('_method', 'PUT'),
                ('_token', token),
                ('_token', token)
            ]
            
            # Extract registration number for later verification
            reg_no = data.get('mykad_passport') or data.get('registration_number')
            
            for key, value in data.items():
                if key not in ['_method', '_token']:
                    payload.append((key, value))
            
            logger.info(f"Submitting update for individual {profile_id}. Note: SEDA will assign a new ID.")
            response = self.session.post(url, data=payload, headers={'Referer': url})
            self._validate_response(response)
            
            # Success check: SEDA usually redirects to /profiles or displays a success message
            if "Profile updated successfully" in response.text or response.status_code == 200:
                logger.info(f"Update submitted for {profile_id}. Verifying new ID...")
                
                # Search by registration number to find the NEWLY created profile ID
                if reg_no:
                    # Search specifically for this registration number
                    matches = self.fetch_profile_list(registration_number=reg_no, max_pages=1)
                    if matches:
                        new_id = matches[0]['id']
                        logger.info(f"Profile {profile_id} updated. New ID is {new_id}")
                        return new_id
                
                return profile_id # Fallback if we can't find the new one
            
            return None

        except Exception as e:
            logger.error(f"Update failed for profile {profile_id}: {e}")
            return None