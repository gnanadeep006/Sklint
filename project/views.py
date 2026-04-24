import random

from django.shortcuts import render

from clints.models import FeaturedProject
from project.appid import appid_callback, appid_login, appid_logout


DEFAULT_FEATURED_PROJECTS = [
    {
        "title": "Living Structures",
        "category": "Website",
        "description": "Modern real estate website to professionally showcase projects and brand",
        "image_src": "/static/Screenshot 2026-02-01 134438.png",
        "project_url": "/projects/",
    },
    {
        "title": "Pulse Studio",
        "category": "Brand Identity",
        "description": "Complete brand system for a boutique music production house",
        "image_src": "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=800&h=600&fit=crop",
        "project_url": "/projects/",
    },
    {
        "title": "Aura Finance",
        "category": "Web App",
        "description": "Elegant dashboard for personal wealth management",
        "image_src": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop",
        "project_url": "/projects/",
    },
]
ERROR_MEMES = {
    "404": [
        {"type": "image", "url": "https://http.cat/404", "alt": "Cat in box"},
        {"type": "image", "url": "https://httpstatus.io/404-cat.png", "alt": "Lost cat"},
        {"type": "gif", "url": "https://media.giphy.com/media/8Lh18E4Ar3zZ2/giphy.gif", "alt": "Confused cat"},
        {"type": "image", "url": "https://http.cat/404", "alt": "404 cat"},
    ],
    "500": [
        {"type": "image", "url": "https://http.cat/500", "alt": "Cat on fire"},
        {"type": "gif", "url": "https://media.giphy.com/media/l378giAZgxPw3eO52/giphy.gif", "alt": "Panic cat"},
        {"type": "image", "url": "https://http.cat/500", "alt": "Server cat"},
    ],
    "403": [
        {"type": "image", "url": "https://http.cat/403", "alt": "Cat blocking"},
        {"type": "gif", "url": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif", "alt": "No cat"},
        {"type": "image", "url": "https://http.cat/403", "alt": "Forbidden cat"},
    ],
    "default": [
        {"type": "image", "url": "https://http.cat/400", "alt": "Cat confused"},
        {"type": "gif", "url": "https://media.giphy.com/media/MDJDe4K7n5X7W/giphy.gif", "alt": "Sad cat"},
        {"type": "image", "url": "https://http.cat/418", "alt": "Teapot cat"},
        {"type": "gif", "url": "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif", "alt": "Shocked cat"},
    ],
}


def _active_projects():
    return FeaturedProject.objects.filter(is_active=True)


def _serialize_project(project):
    return {
        "slug": project.resolved_slug,
        "title": project.title,
        "category": project.category,
        "description": project.description,
        "image_src": project.image_src,
        "project_url": project.project_url,
        "overview": project.overview,
        "problem": project.problem,
        "solution": project.solution,
        "outcome": project.outcome,
    }


def _default_featured_projects():
    return [project.copy() for project in DEFAULT_FEATURED_PROJECTS]


def _project_modal_data(project_items):
    return {
        item["slug"]: {
            "title": item["title"],
            "category": item["category"],
            "image": item["image_src"],
            "overview": item["overview"] or item["description"],
            "problem": item["problem"],
            "solution": item["solution"],
            "outcome": item["outcome"] or item["description"],
            "link": item["project_url"],
        }
        for item in project_items
    }


def index(request):
    featured_projects = [_serialize_project(project) for project in _active_projects()]
    if not featured_projects:
        featured_projects = _default_featured_projects()
    return render(request, "index.html", {"featured_projects": featured_projects})


def about(request):
    return render(request, "about.html")


def projects(request):
    project_items = [_serialize_project(project) for project in _active_projects()]
    categories = sorted({item["category"] for item in project_items})
    return render(
        request,
        "projects.html",
        {
            "project_items": project_items,
            "project_data": _project_modal_data(project_items),
            "project_categories": categories,
        },
    )


def error(request):
    error_code = request.GET.get("code", "404")
    memes = ERROR_MEMES.get(str(error_code), ERROR_MEMES["default"])
    return render(
        request,
        "error.html",
        {
            "error_code": error_code,
            "meme": random.choice(memes),
        },
    )
