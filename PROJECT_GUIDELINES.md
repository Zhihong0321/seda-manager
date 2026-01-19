# Project Guidelines: eATAP Wrapper API

## 1. Architectural Vision
This project is a **Monolithic REST Wrapper**. Its purpose is to provide a clean, modern JSON API interface for the eATAP (SEDA Malaysia) legacy web portal.

### Layers:
1. **FastAPI Layer (`app/api`):** Handles HTTP requests, authentication to *this* API, and JSON validation.
2. **Service Layer (`app/services`):** Orchestrates business logic (e.g., "Create a profile and then start a submission").
3. **Wrapper Layer (`app/wrapper`):** The "Dirty" layer. Handles HTML parsing (Regex), CSRF token extraction, and Laravel-specific session logic.

---

## 2. Technical Stack
- **Backend:** Python 3.12+
- **Web Framework:** FastAPI
- **Data Validation:** Pydantic v2
- **HTTP Client:** `requests.Session` (for stateful cookie handling)
- **HTML Parsing:** Regex (preferred for speed/zero-dependency) or BeautifulSoup4.
- **Deployment:** Railway (Production site: https://atap.solar/)

---

## 3. Mandatory Development Rules

### 3.1 Reverse Engineering Workflow
1. **Analyze:** Capture network traffic (HAR/cURL).
2. **Document:** Update `API-REVERSE-ENG.md` with the endpoint, method, and payload schema.
3. **Research:** Ask the user for specific logic/plan before writing code.
4. **Implement:** Write the wrapper logic first, then the FastAPI route.

### 3.2 Database & State
- **Database:** PostgreSQL (Provided via `DATABASE_URL`).
- **No Migrations:** Database schema changes are handled via direct SQL. Do NOT use Alembic or similar tools.
- **Persistent Storage:** Use `/storage` for ephemeral state like `cookies.json`.
- **Railway Volume:** In production, a Railway Volume MUST be mounted at `/storage`.

### 3.3 Coding Standards
- **Type Hinting:** All functions must have Python type hints.
- **Pydantic Models:** Every API input and output must have a Pydantic model. No "raw dicts" allowed in the API layer.
- **Method Spoofing:** Correctly handle Laravel's `_method: PUT` and double `_token` patterns as discovered in `API-REVERSE-ENG.md`.

---

## 4. API Documentation Strategy
- **Interactive Docs:** FastAPI `/docs` (Swagger) is the primary documentation for end-users.
- **Internal Docs:** `API-REVERSE-ENG.md` is the primary documentation for developers regarding the target site's behavior.

---

## 5. UI/UX Preferences (For future Front-end)
- **No Card Boxes:** Use lines to divide divs/blocks.
- **No Margins:** Blocks should be flush against each other.
- **Cleanliness:** Modern, professional, high-density information display.
