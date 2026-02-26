<<<<<<< HEAD
# sklint
=======
# SklinT

SklinT is a Django-based portfolio website with a custom admin workflow to manage:

- Featured projects (home + projects pages)
- Project modal content (overview/problem/solution/outcome)
- Contact page content
- Contact form submissions and CSV export

## Tech Stack

- Python
- Django
- SQLite (default)
- HTML/CSS/JavaScript (Django templates + static assets)

## Project Structure

```text
sklint/
  manage.py
  project/          # Django project settings, URLs, base views
  clints/           # App models/admin/forms/views for dynamic content
  templates/        # Frontend templates
  statics/          # CSS/JS/images
  media/            # Uploaded files (e.g., project images)
```

## Setup (Local)

1. Clone repository and enter project:
```bash
git clone <your-repo-url>
cd sklint
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
```

3. Install Django:
```bash
pip install django
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create admin user:
```bash
python manage.py createsuperuser
```

6. Run server:
```bash
python manage.py runserver
```

Open:
- Site: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Dynamic Content (Admin)

Use **Featured projects** in admin to control:

- Home featured cards
- Projects page cards
- Projects modal details

Image priority:
1. `image_file` (uploaded file)
2. `image_url` fallback

Use **Contact Page Content**, **Contact steps**, and **Budget options** to edit the contact page.

Use **Contact submissions** to review leads and export selected rows as CSV.

## Media & Static

- Static files served from `statics/`
- Media uploads served from `media/`
- In development, media URL routing is enabled when `DEBUG=True`

## Notes

- Default DB is SQLite (`db.sqlite3`).
- This project currently has no automated tests; add tests in `clints/tests.py` and run:
```bash
python manage.py test
```

>>>>>>> 316ede6 (any commit)
