from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

import json
import urllib.error
import urllib.request

from clints.models import FeaturedProject

GEMINI_API_KEY = "AIzaSyC44Fn05iUXJTyARTH9HOsmqgjy_zevjDo"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_STT_MODEL = "gemini-2.5-flash"


DEFAULT_FEATURED_PROJECTS = [
    {
        "title": "Living Structures",
        "category": "Website",
        "description": "Modern real estate website to professionally showcase projects and brand",
        "image_url": "/static/Screenshot 2026-02-01 134438.png",
        "project_url": "/projects/",
    },
    {
        "title": "Pulse Studio",
        "category": "Brand Identity",
        "description": "Complete brand system for a boutique music production house",
        "image_url": "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=800&h=600&fit=crop",
        "project_url": "/projects/",
    },
    {
        "title": "Aura Finance",
        "category": "Web App",
        "description": "Elegant dashboard for personal wealth management",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop",
        "project_url": "/projects/",
    },
]


def index(request):
    projects_qs = FeaturedProject.objects.filter(is_active=True)
    featured_projects = []
    for project in projects_qs:
        image_src = project.image_file.url if project.image_file else project.image_url
        featured_projects.append(
            {
                "title": project.title,
                "category": project.category,
                "description": project.description,
                "image_src": image_src,
                "project_url": project.project_url,
            }
        )

    if not featured_projects:
        featured_projects = [
            {
                "title": project["title"],
                "category": project["category"],
                "description": project["description"],
                "image_src": project["image_url"],
                "project_url": project["project_url"],
            }
            for project in DEFAULT_FEATURED_PROJECTS
        ]

    return render(request, 'index.html', {"featured_projects": featured_projects})


def about(request):
    return render(request, 'about.html')


def projects(request):
    projects_qs = FeaturedProject.objects.filter(is_active=True)
    project_items = []
    project_data = {}

    for project in projects_qs:
        image_src = project.image_file.url if project.image_file else project.image_url
        item = {
            "slug": project.slug or f"project-{project.id}",
            "title": project.title,
            "category": project.category,
            "description": project.description,
            "image_src": image_src,
            "project_url": project.project_url,
            "overview": project.overview,
            "problem": project.problem,
            "solution": project.solution,
            "outcome": project.outcome,
        }
        project_items.append(item)
        project_data[item["slug"]] = {
            "title": item["title"],
            "category": item["category"],
            "image": item["image_src"],
            "overview": item["overview"] or item["description"],
            "problem": item["problem"],
            "solution": item["solution"],
            "outcome": item["outcome"] or item["description"],
            "link": item["project_url"],
        }

    categories = sorted({item["category"] for item in project_items})

    return render(
        request,
        'projects.html',
        {
            "project_items": project_items,
            "project_data": project_data,
            "project_categories": categories,
        },
    )


def error(request):
    return render(request, 'error.html')
    

def ai_studio(request):
    return render(request, "ai_studio.html")

@require_POST
def ai_studio_tts(request):
    api_key = GEMINI_API_KEY
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        return JsonResponse({"error": "GEMINI API key is not set on the server."}, status=500)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    text_input = (payload.get("text") or "").strip()
    voice = (payload.get("voice") or "Kore").strip()

    if not text_input:
        return JsonResponse({"error": "Text is required."}, status=400)

    request_body = {
        "contents": [
            {
                "parts": [
                    {"text": text_input}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice
                    }
                }
            }
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", "ignore")
        return JsonResponse({"error": "Gemini TTS request failed.", "details": details}, status=getattr(exc, 'code', 502))
    except Exception as exc:
        return JsonResponse({"error": "Unexpected error while contacting Gemini.", "details": str(exc)}, status=502)

    audio_base64 = None
    mime_type = None
    for candidate in response_data.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            inline = part.get("inlineData") or {}
            if inline.get("data"):
                audio_base64 = inline.get("data")
                mime_type = inline.get("mimeType")
                break
        if audio_base64:
            break

    if not audio_base64:
        return JsonResponse({"error": "No audio returned from Gemini."}, status=502)

    return JsonResponse({"audio_base64": audio_base64, "mime_type": mime_type, "sample_rate": 24000})


@require_POST
def ai_studio_stt(request):
    api_key = GEMINI_API_KEY
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        return JsonResponse({"error": "GEMINI API key is not set on the server."}, status=500)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    audio_base64 = (payload.get("audio_base64") or "").strip()
    mime_type = (payload.get("mime_type") or "audio/webm").strip()

    if not audio_base64:
        return JsonResponse({"error": "Audio data is required."}, status=400)

    request_body = {
        "contents": [
            {
                "parts": [
                    {"inlineData": {"data": audio_base64, "mimeType": mime_type}},
                    {"text": "Transcribe the spoken words only, verbatim. Do not describe non-speech sounds. If no speech is present, return an empty string."}
                ]
            }
        ]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_STT_MODEL}:generateContent"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", "ignore")
        return JsonResponse({"error": "Gemini STT request failed.", "details": details}, status=getattr(exc, 'code', 502))
    except Exception as exc:
        return JsonResponse({"error": "Unexpected error while contacting Gemini.", "details": str(exc)}, status=502)

    text_parts = []
    for candidate in response_data.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if "text" in part:
                text_parts.append(part["text"])
        if text_parts:
            break

    transcript = "\n".join(text_parts).strip()
    if not transcript:
        transcript = "No speech detected."

    return JsonResponse({"text": transcript})

