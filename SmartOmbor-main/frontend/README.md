# SmartOmbor Frontend (separate SPA)

This is a **standalone frontend** — it does NOT need Django templates.
All data is `fetch()` → Django REST API (backend).

## Files
- `index.html` — SPA shell with all pages (`#dashboard`, `#products`, ... via hash)
- `app.js` — router + `fetch(window.API_BASE + path)`
- `styles.css` — Bootstrap 5 + custom layout
- `config.js` — `window.API_BASE = "http://127.0.0.1:8000/api"` (change for prod)

## Run (2 terminals)

**Terminal 1 — backend (Django, in `SmartOmbor-main/SmartOmbor-main`):**
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# API docs: http://127.0.0.1:8000/api/docs/
```

**Terminal 2 — frontend (this folder):**
```bash
npx serve . -l 5173
# open: http://localhost:5173
```
Or without Node: `python -m http.server 5173 -d .`

Then log in with your Django user (JWT → `POST {API_BASE}/auth/token/`).

Backend CORS is open in dev (`CORS_ALLOW_ALL_ORIGINS = True`), so any origin works.

## Config
Edit `config.js`:
```js
window.API_BASE = "http://127.0.0.1:8000/api"; // prod: "https://api.example.com/api"
```
