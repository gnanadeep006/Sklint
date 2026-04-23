# SklinT / CodeGuilt Project

This repository contains the SklinT Django website together with the CodeGuilt code-roasting experience, IBM App ID authentication support, and an optional IBM Cloudant asset catalog integration.

## What Is Included
- Public website pages for home, about, projects, contact, and error states.
- `CodeGuilt` / `CodeRoast` experience for code analysis, roast captions, meme drops, and voice playback.
- IBM App ID sign-in flow wired through the Django project.
- Optional IBM Cloudant asset integration for meme, gif, and SFX metadata.
- Local static fallback assets so the website can run even when Cloudant is disabled or empty.

## Project Structure
- `project/`: Django settings, routes, IBM App ID middleware, auth flow, and site views.
- `clints/`: App models, forms, admin, and related routes/views.
- `coderoast/`: CodeGuilt page, roast endpoint, Cloudant asset endpoint, and template logic.
- `templates/`: Main website templates.
- `templates/includes/`: Shared auth and UI includes.
- `statics/`: Stylesheets, images, fonts, and CodeGuilt sound assets.
- `media/`: Uploaded media used by the site.

## Local Setup
1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Fill in the environment variables you need.
5. Run `python manage.py migrate`.
6. Start the development server with `python manage.py runserver`.

## Environment Notes
- `.env` is intentionally local and should not be committed.
- `.env.example` contains the expected keys without real secrets.
- `GOOGLE_AI_STUDIO_API_KEY` powers the Gemini-based roast flow.
- `CODEROAST_TTS_PROVIDER=browser` keeps voice generation local to the browser by default.

## IBM Integrations

### IBM App ID
IBM App ID is used for sign-in and protected route handling.

Set these values in `.env` when you want App ID enabled:
- `APPID_CLIENT_ID`
- `APPID_CLIENT_SECRET`
- `APPID_DISCOVERY_ENDPOINT`
- `APPID_OAUTH_SERVER_URL`
- `APPID_SERVICE_ENDPOINT`
- `APPID_TENANT_ID`
- `APPID_MANAGEMENT_URL`
- `APPID_SCOPE`
- `APPID_REQUIRE_LOGIN`

For production, add the callback URL:
- `https://your-domain/auth/callback/`

### IBM Cloudant
Cloudant support is present for asset catalog storage, but it is optional.

Current design:
- Cloudant can store meme, gif, and SFX documents.
- The live website can ignore Cloudant entirely when `CLOUDANT_ASSETS_ENABLED=false`.
- Local static assets remain the safe default fallback.

Cloudant keys:
- `CLOUDANT_ASSETS_ENABLED`
- `CLOUDANT_URL`
- `CLOUDANT_DATABASE`
- `CLOUDANT_USERNAME`
- `CLOUDANT_PASSWORD`
- `CLOUDANT_BEARER_TOKEN`
- `CLOUDANT_ASSET_GROUP`

Example asset document types:
- `meme`
- `gif`
- `sfx`

Example SFX buckets:
- `crowd`
- `evil`
- `cheer`

### Sarvam AI
Sarvam AI is used here as an optional text-to-speech provider for CodeGuilt roast playback. When configured, the backend can return generated roast audio; otherwise the project falls back to browser-based voice playback.

## CodeGuilt Notes
- The roast flow uses Gemini with configured fallback model candidates.
- The frontend rotates memes/gifs and supports browser speech with optional server TTS.
- Cloudant-backed assets can be enabled later, but the current project is safe with local/static assets only.

## Deployment Checklist
- Set `DJANGO_DEBUG=false`.
- Set a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to your live domain.
- Set `DJANGO_CSRF_TRUSTED_ORIGINS` to your live HTTPS origin.
- Add the IBM App ID production redirect URL.
- Keep real secrets only in deployment environment variables or local `.env`, never in Git.

## Repository Notes
- `db.sqlite3` should stay out of commits for normal development workflows.
- Python cache files should not be committed.
- Cloudant is currently configured as optional infrastructure, not a required dependency for the website.
