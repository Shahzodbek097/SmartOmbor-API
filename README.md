# SmartOmbor — API backend (separate frontend)

Kichik do'konlar uchun mahsulotlar ombori, sotuvlar va hisobotlarni boshqaradigan web dastur.

## Architecture
- **Backend (this repo):** Django 5.2 + DRF + SimpleJWT. No Django templates.
- **Frontend (separate):** `SmartOmbor-main/frontend` — standalone SPA (`index.html` + `app.js` + `styles.css` + `config.js`), `fetch()` → `http://127.0.0.1:8000/api`.

## API base
```
/api/auth/token/           POST  {username,password} -> {access,refresh}
/api/auth/token/refresh/   POST  {refresh}
/api/auth/me/              GET   current user (+role/groups)
/api/auth/profile/         GET/PATCH
/api/auth/change-password/ POST
/api/users/                GET/POST/PATCH/DELETE  (Rahbar)
/api/users/{id}/toggle-status/ POST
/api/categories/           CRUD
/api/products/             CRUD (?q=, ?category=)
/api/movements/            GET/POST (?q=, movement_type, date_from/to, user)  (Omborchi)
/api/orders/               GET (own)/POST/DELETE + /{id}/finish/ /cancel/ (Sotuvchi)
/api/manager/orders/       GET/DELETE (all orders, Rahbar/superuser)
/api/reports/dashboard/    GET (?date_from, ?date_to)
/api/reports/sellers/      GET (Rahbar)
/api/reports/inventory/    GET (Rahbar)
 -> exports: /api/reports/export/.../excel|pdf/
/api/schema/ /api/docs/ /api/redoc/  /  /health/
```

## Run backend
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Docs: http://127.0.0.1:8000/api/docs/
# Root / -> JSON pointer to frontend
```

## Run frontend (separate, in ../frontend)
```bash
cd ../frontend
npx serve . -l 5173
# open: http://localhost:5173  (API_BASE default http://127.0.0.1:8000/api)
```
Same `README.md` in `frontend/` has full steps.

Create roles if missing: `Omborchi`, `Sotuvchi`, `Rahbar`:
```bash
python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); from django.contrib.auth.models import Group; [Group.objects.get_or_create(name=n) for n in ['Omborchi','Sotuvchi','Rahbar']]"
```
Superuser has full access.

## Example order create (Sotuvchi)
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product":1,"soni":2}]}'
curl -X POST http://127.0.0.1:8000/api/orders/1/finish/ -H "Authorization: Bearer $ACCESS"
```

## Cleaned up
Deleted (proven unused via `grep`): all `*/templates/` (26 template HTMLs), `templates/403.html`, root `templates/`, `products/sales/inventory/forms.py`, `accounts/forms.py`, `accounts/decorators.py` (→ `SmartOmbor-main/SmartOmbor-main/accounts/permissions.py`), `config/frontend.py`, `static/frontend/` (moved out).
Kept: `models.py`, `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `services.py`, `admin.py`, migrations.
