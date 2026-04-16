# SklinT AI Web Integration Kit

This folder contains the SklinT Django project and its website templates, static assets, and app code.

## Files Included:
- `index.html`: The frontend structure using Tailwind CSS.
- `script.js`: The core logic using the Gemini AI SDK.
- `django_backend.py`: Sample Django code (View, URL, Template logic).

## Quick Start:
1. Copy the contents of `index.html` into a new Django template (e.g., `templates/sklint/index.html`).
1. Place `script.js` in your static files directory.
1. Update `script.js` with your **Gemini API Key**.
1. Add the view and URL patterns from `django_backend.py` to your Django project.

## Features:
- **Responsive Design**: Fully responsive layout built with Tailwind CSS.

## API Key:
You can get your Gemini API Key from the [Google AI Studio](https://aistudio.google.com/app/apikey).

**Note:** For security, ensure you do not commit your API key to public repositories. Use environment variables in your Django settings.

