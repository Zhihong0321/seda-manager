import requests
import json
import re
import os
import html as _html
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
        details = {name: value for name, value in inputs if name not in ['_token', '_method']}
        
        # 2. Extract selected values from dropdowns
        select_names = re.findall(r'<select[^>]*name="([^"]+)"', response.text)
        for name in select_names:
            select_regex = fr'<select[^>]*name="{name}"[\s\S]*?</select>'
            select_block = re.search(select_regex, response.text)
            if select_block:
                selected_opt = re.search(r'<option[^>]*selected[^>]*>(.*?)</option>', select_block.group(0))
                details[name] = selected_opt.group(1).strip() if selected_opt else ""
        
        # 3. Map to clean API keys
        clean_mapping = {
            'mykad_passport': 'ic_number',
            'contact_salutation': 'emergency_salutation',
            'contact_name': 'emergency_name',
            'contact_mykad_passport': 'emergency_ic_number',
            'contact_citizenship': 'emergency_citizenship',
            'contact_relationship': 'emergency_relationship',
            'contact_email': 'emergency_email',
            'contact_phone': 'emergency_phone',
            'contact_mobile': 'emergency_mobile'
        }
        
        return {clean_mapping.get(k, k): v for k, v in details.items()}

    def _map_profile_data(self, data: Dict) -> List[tuple]:
        """Maps clean API field names to legacy SEDA portal field names."""
        mapping = {
            'salutation': 'salutation',
            'name': 'name',
            'citizenship': 'citizenship',
            'mykad_passport': 'ic_number',
            'email': 'email',
            'address_line_1': 'address_line_1',
            'address_line_2': 'address_line_2',
            'address_line_3': 'address_line_3',
            'postcode': 'postcode',
            'town': 'town',
            'state': 'state',
            'phone': 'phone',
            'mobile': 'mobile',
            'contact_salutation': 'emergency_salutation',
            'contact_name': 'emergency_name',
            'contact_mykad_passport': 'emergency_ic_number',
            'contact_citizenship': 'emergency_citizenship',
            'contact_relationship': 'emergency_relationship',
            'contact_email': 'emergency_email',
            'contact_phone': 'emergency_phone',
            'contact_mobile': 'emergency_mobile'
        }
        
        payload = []
        for seda_field, data_key in mapping.items():
            value = data.get(data_key, "")
            
            # Legacy logic: Title/Salutation formatting
            if seda_field == 'salutation' and value and not str(value).endswith('.'):
                value = f"{value}."
            
            # Legacy logic: IC/Passport cleaning
            if seda_field in ['mykad_passport', 'contact_mykad_passport'] and value:
                value = re.sub(r'[^0-9A-Za-z]', '', str(value))
            
            # Legacy logic: Fallback for missing contact phone
            if seda_field == 'contact_phone' and not value:
                value = data.get('emergency_mobile', '')
                
            payload.append((seda_field, str(value) if value is not None else ""))
        
        return payload

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
            
            # 1. Map API data to SEDA fields
            payload.extend(self._map_profile_data(data))
            
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
            
            # Extract registration number for later verification (handles new clean key)
            reg_no = data.get('ic_number') or data.get('mykad_passport') or data.get('registration_number')
            
            # Map and add fields to payload
            payload.extend(self._map_profile_data(data))
            
            logger.info(f"Submitting update for individual {profile_id}. Note: SEDA will assign a new ID.")
            response = self.session.post(url, data=payload, headers={'Referer': url})
            self._validate_response(response)
            
            # Success check: SEDA usually redirects to /profiles or displays a success message
            if "Profile updated successfully" in response.text or response.status_code == 200:
                logger.info(f"Update submitted for {profile_id}. Verifying new ID...")
                
                # Search by registration number to find the NEWLY created profile ID
                if reg_no:
                    # Search specifically for this registration number
                    # We might need to check more than 1 page if they have TONS of history
                    matches = self.fetch_profile_list(registration_number=reg_no, max_pages=3)
                    if matches:
                        # Find the highest numeric ID among all matches
                        # The IDs are strings in 'profiles', so we convert to int for comparison
                        try:
                            sorted_matches = sorted(matches, key=lambda x: int(x['id']), reverse=True)
                            new_id = sorted_matches[0]['id']
                            logger.info(f"Profile {profile_id} updated. Latest active ID is {new_id} (Found among {len(matches)} historical records)")
                            return new_id
                        except (ValueError, KeyError, IndexError):
                            # Fallback if ID is not an integer or list is empty
                            return matches[0]['id']
                
                return profile_id # Fallback if we can't find the new one
            
            return None

        except Exception as e:
            logger.error(f"Update failed for profile {profile_id}: {e}")
            return None

    def _extract_form_by_action(self, html: str, action_substring: str) -> str:
        """
        Returns the first <form>...</form> block whose action contains action_substring.
        This is intentionally lightweight (regex-based) to avoid extra deps.
        """
        sub = re.escape(action_substring)
        patterns = [
            r'(<form\b[^>]*\baction="[^"]*' + sub + r'[^"]*"[^>]*>[\s\S]*?</form>)',
            r"(<form\b[^>]*\baction='[^']*" + sub + r"[^']*'[^>]*>[\s\S]*?</form>)",
            r'(<form\b[^>]*\baction=[^\s>]*' + sub + r'[^\s>]*[^>]*>[\s\S]*?</form>)',
        ]
        for pat in patterns:
            m = re.search(pat, html, flags=re.IGNORECASE)
            if m:
                return m.group(1)

        raise SEDAParsingError(f"Form not found for action containing: {action_substring}")

    def _parse_form_successful_controls(self, form_html: str) -> List[tuple]:
        """
        Parse "successful controls" from a form (approximation of browser submission rules).
        Returns a list of (name, value) tuples; preserves duplicates and order.
        """
        # Drop inert/template/script content that can contain placeholder inputs not actually submitted.
        form_html = re.sub(r'<!--[\s\S]*?-->', '', form_html, flags=re.IGNORECASE)
        form_html = re.sub(r'<template\b[\s\S]*?</template>', '', form_html, flags=re.IGNORECASE)
        form_html = re.sub(r'<script\b[\s\S]*?</script>', '', form_html, flags=re.IGNORECASE)

        # Attribute parser: supports key="value", key='value', key=value, and boolean attrs.
        attr_re = re.compile(
            r"([:\w-]+)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'=<>`]+)))?",
            re.IGNORECASE,
        )

        def parse_attrs(tag: str) -> Dict[str, str]:
            attrs: Dict[str, str] = {}
            s = tag.strip()
            # If we got a full tag like "<input ...>", drop angle brackets + tag name.
            if s.startswith("<") and s.endswith(">"):
                inner = s[1:-1].strip()
                parts = inner.split(None, 1)
                s = parts[1] if len(parts) > 1 else ""

            for k, v1, v2, v3 in attr_re.findall(s):
                key = k.lower()
                val = v1 or v2 or v3
                # Boolean attributes appear with no value; store as empty string but keep presence.
                attrs[key] = "" if val is None else val
            return attrs

        controls: List[tuple] = []

        # Inputs
        for tag in re.findall(r'<input\b[^>]*>', form_html, flags=re.IGNORECASE):
            attrs = parse_attrs(tag)
            name = attrs.get("name")
            if not name or "disabled" in attrs:
                continue
            t = (attrs.get("type") or "text").lower()
            if t in ("submit", "button", "image", "reset", "file"):
                continue
            if t in ("checkbox", "radio") and "checked" not in attrs:
                continue
            value = attrs.get("value", "")
            if t in ("checkbox", "radio") and value == "":
                value = "on"
            controls.append((name, _html.unescape(value)))

        # Textareas
        for attr_str, body in re.findall(r'<textarea\b([^>]*)>([\s\S]*?)</textarea>', form_html, flags=re.IGNORECASE):
            attrs = parse_attrs(attr_str)
            name = attrs.get("name")
            if not name or "disabled" in attrs:
                continue
            controls.append((name, _html.unescape(body)))

        # Selects
        for select_attr, options_html in re.findall(r'<select\b([^>]*)>([\s\S]*?)</select>', form_html, flags=re.IGNORECASE):
            attrs = parse_attrs(select_attr)
            name = attrs.get("name")
            if not name or "disabled" in attrs:
                continue

            multiple = "multiple" in attrs
            option_tags = re.findall(r'<option\b[^>]*>', options_html, flags=re.IGNORECASE)

            selected_vals: List[str] = []
            for opt_tag in option_tags:
                opt_attrs = parse_attrs(opt_tag)
                if "selected" in opt_attrs:
                    selected_vals.append(_html.unescape(opt_attrs.get("value", "")))

            # If nothing explicitly selected and not multiple, browsers submit first option's value.
            if not selected_vals and not multiple and option_tags:
                first_attrs = parse_attrs(option_tags[0])
                selected_vals = [_html.unescape(first_attrs.get("value", ""))]

            if multiple:
                for v in selected_vals:
                    controls.append((name, v))
            else:
                selected = selected_vals[0] if selected_vals else ""
                # If a required select is currently empty, the portal UI would normally block submit.
                # In practice these are often conditional fields (hidden/disabled by JS), so omit them.
                if "required" in attrs and not selected:
                    continue
                controls.append((name, selected))

        return controls

    def update_application(self, application_id: str, updates: Dict) -> Dict:
        """
        Updates an application by replicating the browser form submit behavior.

        Portal behavior (from UPDATE-APPLICATION.har):
        - POST to /applications/{id}/edit
        - Include _method=PUT (Laravel method spoofing)
        - Include CSRF _token
        - Send application/x-www-form-urlencoded form fields (many of them)
        """
        url = f"{SEDA_BASE_URL}/applications/{application_id}/edit"
        logger.info(f"Updating application {application_id} via {url}")

        # Single GET: obtain CSRF token + current form fields so we can do partial updates safely.
        r = self.session.get(url, timeout=30)
        self._validate_response(r)

        token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
        if not token_match:
            raise SEDAParsingError(f"CSRF token not found at {url}")
        token = token_match.group(1)

        form = self._extract_form_by_action(r.text, f"/applications/{application_id}/edit")
        fields = self._parse_form_successful_controls(form)

        # Build payload: method spoofing + double token (matches portal patterns seen in other forms).
        payload: List[tuple] = [('_method', 'PUT'), ('_token', token), ('_token', token)]
        for k, v in fields:
            if k in ('_method', '_token'):
                continue
            payload.append((k, v))

        # Apply updates: replace all occurrences of the field name (duplicates exist in the portal).
        if updates:
            for key, val in updates.items():
                sval = "" if val is None else str(val)
                replaced = False
                new_payload: List[tuple] = []
                for k, v in payload:
                    if k == key and k not in ('_method', '_token'):
                        new_payload.append((k, sval))
                        replaced = True
                    else:
                        new_payload.append((k, v))
                if not replaced:
                    new_payload.append((key, sval))
                payload = new_payload

        response = self.session.post(
            url,
            data=payload,
            headers={'Referer': url},
            allow_redirects=True,
            timeout=30
        )
        self._validate_response(response)

        # Heuristic success signal: portal usually lands on supporting documents after save.
        success = f"/applications/{application_id}/supporting_documents" in response.url

        if not success:
            # Try to surface validation errors if present.
            error_msgs = []
            error_msgs.extend(re.findall(
                r'<span class="invalid-feedback" role="alert">[\\s\\S]*?<strong>(.*?)</strong>',
                response.text
            ))
            error_msgs.extend(re.findall(
                r'alert alert-danger[\\s\\S]*?>(.*?)</div>',
                response.text,
                re.DOTALL
            ))
            error_msgs.extend(re.findall(r'toastr\\.error\\(\"(.*?)\"', response.text))
            if error_msgs:
                clean = [re.sub(r'<[^>]+>', '', e).strip() for e in error_msgs if e and e.strip()]
                return {"success": False, "application_id": application_id, "error": ", ".join(sorted(set(clean)))}

        return {
            "success": bool(success),
            "application_id": application_id,
            "final_url": response.url,
            "redirect_chain": [h.headers.get("Location") for h in response.history],
        }
