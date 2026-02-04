# eATAP (SEDA Malaysia) API Reverse Engineering Documentation

This document tracks the patterns, endpoints, and logic discovered during the reverse engineering of the SEDA Solar PV Roof Application Submission Site.

## 1. Authentication & Session Management

### 1.1 Cookies
The site uses the following primary cookies for authentication:
- `eatap_session`: The main encrypted Laravel session cookie.
- `XSRF-TOKEN`: Laravel CSRF protection token (must be sent back in headers for POST/PUT/DELETE).
- `remember_web_...`: Long-lived session cookie.

### 1.2 Headers
To mimic a valid browser request, the following headers are required:
- `User-Agent`: (Standard browser string)
- `X-XSRF-TOKEN`: The decoded value of the `XSRF-TOKEN` cookie (usually required for POST requests).

---

## 2. Resource Endpoints

### 2.1 Profiles (List Clients)
- **URL:** `https://atap.seda.gov.my/profiles`
- **Method:** `GET`
- **Data Type:** HTML (Server-Side Rendered)
- **Wrapper Logic:** `app/wrapper/seda_wrapper.py` (`fetch_profile_list`)
- **API Feature (Search):** Supports searching by name with strict uniqueness checks (returns 409 if ambiguous).

### 2.2 Profile Detail (Edit/View)
- **URL Pattern:** 
  - Individuals: `https://atap.seda.gov.my/profiles/individuals/{id}/edit`
  - Companies: `https://atap.seda.gov.my/profiles/companies/{id}/edit`
- **Method:** `GET`
- **UID Schema:** Simple integer ID (e.g., `1`, `12`, `250`). IDs appear to be sequential across the system.
- **Form Schema (Individuals):**
  - `salutation`: (e.g., MR, MS, DR)
  - `name`: Full Name
  - `mykad_passport`: IC Number or Passport
  - `email`: Email Address
  - `citizenship`: (Select field)
  - `address_line_1`, `address_line_2`, `address_line_3`, `postcode`, `town`, `state`
  - `phone`, `mobile`: Contact numbers
  - **Emergency/Secondary Contact:** `contact_salutation`, `contact_name`, `contact_mykad_passport`, `contact_relationship`, `contact_citizenship`, `contact_email`, `contact_mobile`, `contact_phone`.

### 2.3 Create Individual Profile
- **URL:** `https://atap.seda.gov.my/profiles/individuals`
- **Method:** `POST`
- **Required Fields:** `_token` (sent twice), and all form fields from section 2.2
- **Response:** `302 Found` redirect to either:
  - Edit page with new profile ID: `/profiles/individuals/{id}/edit`
  - List page: `/profiles/individuals` (if ID not in URL)
- **Critical Pattern:** Must send `_token` twice in the POST body to mimic browser behavior.

### 2.4 Profile Update
- **URL:** Same as GET (edit endpoint)
- **Method:** `POST` (with `_method: PUT` in form data)
- **Required Fields:** `_token` (CSRF), `_method`, and all form fields above.
- **Critical Pattern:** Must send `_token` twice in the POST body to mimic browser behavior.

---

## 3. Discovered Patterns
- **Framework:** Laravel (identified via `eatap_session` and `data-framework="laravel"` in HTML).
- **ID Management:** Resources use simple integer IDs in the URL path.
- **Method Spoofing:** Uses `_method: PUT` inside a `POST` request for updates (standard Laravel pattern).
- **CSRF:** Every form contains a hidden `_token` input.
- **Rendering:** Primarily Server-Side Rendering (SSR). Most data is embedded in HTML rather than fetched via JSON APIs.

---

## 4. Pending Investigation
- [ ] Create Company Profile (POST structure)
- [ ] Submit Application (Multi-step form logic?)
- [ ] File Upload Handling (Mechanism for attachments)