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

    def fetch_profile_list(self) -> List[Dict]:
        """Scrapes the client profile list from the portal."""
        url = f"{SEDA_BASE_URL}/profiles"
        logger.info("Fetching client profiles...")
        
        response = self.session.get(url)
        self._validate_response(response)

        profiles = []
        # Pattern to extract ID, Type, Name, and Reg No from table rows
        row_pattern = re.compile(
            r'<tr>\s*<td>.*?</td>\s*<td><a href="([^"]+)">\s*(.*?)\s*</a>\s*</td>\s*<td>\s*(.*?)\s*</td>\s*<td>\s*(.*?)\s*</td>',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in row_pattern.findall(response.text):
            url_path = match[0]
            # URL format: https://.../profiles/individuals/123/edit
            parts = url_path.split('/')
            profiles.append({
                "id": parts[-2],
                "type": parts[-3],  # 'individuals' or 'companies'
                "name": match[1].strip(),
                "registration_number": match[2].strip(),
                "category": match[3].strip(),
                "url": url_path
            })
            
        logger.info(f"Extracted {len(profiles)} profiles.")
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
            
            for key, value in data.items():
                if key not in ['_method', '_token']:
                    payload.append((key, value))
            
            logger.info("Submitting new individual profile")
            response = self.session.post(url, data=payload, headers={'Referer': url})
            self._validate_response(response)
            
            # Check for redirect to extract the new profile ID
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                import re
                match = re.search(r'/profiles/individuals/(\d+)/edit', location)
                if match:
                    profile_id = match.group(1)
                    logger.info(f"Profile created successfully with ID: {profile_id}")
                    return {
                        "success": True,
                        "profile_id": profile_id,
                        "redirect_url": location
                    }
                elif '/profiles/individuals' in location:
                    # Redirected to list page - profile created but ID not in URL
                    logger.info("Profile created successfully (ID not in redirect URL)")
                    return {
                        "success": True,
                        "profile_id": None,
                        "redirect_url": location,
                        "message": "Profile created. Check the profiles list for the new entry."
                    }
            
            logger.error(f"Unexpected response status: {response.status_code}")
            return {
                "success": False,
                "error": f"Unexpected response: {response.status_code}"
            }

        except Exception as e:
            logger.error(f"Profile creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_individual_profile(self, profile_id: str, data: Dict) -> bool:
        """Performs a PUT update for an individual profile."""
        url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
        
        try:
            token = self._fetch_csrf_token(url)
            
            # Replicate browser behavior: Laravel PUT spoofing + double token
            payload = [
                ('_method', 'PUT'),
                ('_token', token),
                ('_token', token)
            ]
            
            for key, value in data.items():
                if key not in ['_method', '_token']:
                    payload.append((key, value))
            
            logger.info(f"Submitting update for individual {profile_id}")
            response = self.session.post(url, data=payload, headers={'Referer': url})
            self._validate_response(response)
            
            success = "Profile updated successfully" in response.text or response.status_code == 200
            if success:
                logger.info(f"Profile {profile_id} updated successfully.")
            return success

        except Exception as e:
            logger.error(f"Update failed for profile {profile_id}: {e}")
            return False