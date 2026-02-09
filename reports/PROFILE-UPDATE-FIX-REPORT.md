# Technical Report: Resolving SEDA Profile Update Failures (405 Method Not Allowed)

## 1. Executive Summary
This report documents the resolution of a critical failure in the SEDA Profile Update functionality. The system was encountering `405 Method Not Allowed` errors when attempting to update individual profiles. The root cause was identified as a routing mismatch in the SEDA portal's Laravel-based architecture, which requires specific URL pathing for spoofed `PUT` requests.

## 2. Problem Diagnosis
### 2.1 Error Observed
When calling the `update_individual_profile` method, the following error was logged:
`2026-02-10 01:14:58 [ERROR] eATAP: UPDATE FAILED.for profile 4169: 405 Client Error: Method Not Allowed`

### 2.2 Network Analysis (HAR Findings)
A deep analysis of the `UPDATE-PROFILE.har` file and subsequent network sniffing revealed that even though the application uses `_method: PUT` for updates, the **target URL** in the browser's raw request must include the `/edit` suffix to be accepted by the portal's form handler.

- **Failing URL (in code):** `https://atap.seda.gov.my/profiles/individuals/{id}`
- **Working URL (in HAR/Browser):** `https://atap.seda.gov.my/profiles/individuals/{id}/edit`

## 3. Root Cause
The SEDA portal is built on the Laravel framework. In Laravel's default resource routing, a `POST` request with `_method=PUT` (Method Spoofing) is often routed specifically to the `update` action only if it matches the specific pattern defined in the `web.php` routes. 

For SEDA, the form handler for updates is bound to the `/edit` path. By appending `/edit` to our `POST` target, we align with the portal's expectation for administrative form submissions, allowing the CSRF validation and method spoofing to be processed correctly.

## 4. Implementation Details
The fix was applied in `app/wrapper/seda_wrapper.py` within the `update_individual_profile` method.

### Code Change:
```python
# Before
update_url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}"

# After
update_url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
```

## 5. Verification
Verification was performed using the `debug_update_name.py` script, which targets a test profile associated with MyKad `020202012051`.

### Test Results:
- **Status:** Success
- **Action:** Updated Name to `GAN ZHI HONG 1770657416`
- **Result:** SEDA accepted the request and generated a new internal ID `4173`.
- **Confirmation:** A subsequent search for the MyKad confirmed that the newest record `4173` reflects the updated name, while the old record `4172` remains as the historical version.

## 6. Impact Assessment
- **API Schema Compatibility:** High. The FastAPI `PUT /api/v1/profiles/{id}` endpoint schema remains **unchanged**.
- **Downstream Apps:** No updates required. Other applications consuming this API can continue to use the same logic.
- **Data Integrity:** The fix preserves SEDA's "Create-on-Update" logic, which ensures a complete audit trail of user data changes within the SEDA portal.

---
**Date:** 2026-02-10  
**Author:** Antigravity AI  
**Project:** eATAP Wrapper API  
