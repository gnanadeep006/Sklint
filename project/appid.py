import base64
import json
import secrets
import time
from urllib import error, parse, request

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


SESSION_USER_KEY = "appid_user"
SESSION_STATE_KEY = "appid_oauth_state"
SESSION_NONCE_KEY = "appid_oauth_nonce"
SESSION_NEXT_KEY = "appid_next_url"
DEFAULT_PROTECTED_PATH_PREFIXES = ("/", "/about/", "/projects/", "/contact/")


def _is_configured():
    return bool(
        settings.APPID_CLIENT_ID
        and settings.APPID_CLIENT_SECRET
        and settings.APPID_DISCOVERY_ENDPOINT
    )


def _json_request(url, *, data=None, headers=None):
    body = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if data is not None:
        body = parse.urlencode(data).encode("utf-8")
        request_headers.setdefault(
            "Content-Type",
            "application/x-www-form-urlencoded",
        )
    req = request.Request(url, data=body, headers=request_headers)
    with request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _discovery():
    return _json_request(settings.APPID_DISCOVERY_ENDPOINT)


def _absolute_callback_uri(http_request):
    return http_request.build_absolute_uri(reverse("appid_callback"))


def _safe_next_url(next_url, default):
    if not next_url:
        return default
    parsed = parse.urlparse(str(next_url).strip())
    if parsed.scheme or parsed.netloc:
        return default
    path = parsed.path or "/"
    if not path.startswith("/"):
        return default
    safe_url = path
    if parsed.query:
        safe_url = f"{safe_url}?{parsed.query}"
    if parsed.fragment:
        safe_url = f"{safe_url}#{parsed.fragment}"
    return safe_url


def _path_matches_prefixes(path, prefixes):
    current_path = path or "/"
    for prefix in prefixes or ():
        normalized = str(prefix).strip()
        if not normalized:
            continue
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if normalized == "/":
            if current_path == "/":
                return True
            continue
        trimmed = normalized.rstrip("/")
        if current_path == trimmed or current_path.startswith(normalized):
            return True
    return False


def _basic_auth_header():
    credentials = f"{settings.APPID_CLIENT_ID}:{settings.APPID_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


def _decode_jwt_claims(token):
    try:
        _header, payload, _signature = token.split(".", 2)
        padded = payload + "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, json.JSONDecodeError):
        return {}


def _normalize_user(userinfo, id_claims):
    email = userinfo.get("email") or id_claims.get("email") or ""
    name = (
        userinfo.get("name")
        or id_claims.get("name")
        or userinfo.get("preferred_username")
        or email
        or "App ID user"
    )
    return {
        "sub": userinfo.get("sub") or id_claims.get("sub"),
        "name": name,
        "email": email,
        "picture": userinfo.get("picture") or id_claims.get("picture") or "",
    }


def appid_context(request):
    return {
        "appid_enabled": _is_configured(),
        "appid_user": request.session.get(SESSION_USER_KEY),
    }


def appid_login(request):
    if not _is_configured():
        messages.error(request, "IBM App ID is not configured yet.")
        return redirect("home")

    try:
        discovery = _discovery()
    except (error.URLError, json.JSONDecodeError):
        messages.error(request, "Could not reach IBM App ID. Please try again.")
        return redirect("home")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    next_url = _safe_next_url(
        request.GET.get("next") or request.META.get("HTTP_REFERER"),
        reverse("home"),
    )

    request.session[SESSION_STATE_KEY] = state
    request.session[SESSION_NONCE_KEY] = nonce
    request.session[SESSION_NEXT_KEY] = next_url

    params = {
        "response_type": "code",
        "client_id": settings.APPID_CLIENT_ID,
        "redirect_uri": _absolute_callback_uri(request),
        "scope": settings.APPID_SCOPE,
        "state": state,
        "nonce": nonce,
    }
    authorization_url = f"{discovery['authorization_endpoint']}?{parse.urlencode(params)}"
    return redirect(authorization_url)


def appid_callback(request):
    expected_state = request.session.pop(SESSION_STATE_KEY, None)
    expected_nonce = request.session.pop(SESSION_NONCE_KEY, None)
    next_url = request.session.pop(SESSION_NEXT_KEY, reverse("home"))

    if request.GET.get("error"):
        messages.error(request, request.GET.get("error_description") or "App ID sign in was cancelled.")
        return redirect("home")

    if not expected_state or request.GET.get("state") != expected_state:
        messages.error(request, "App ID sign in could not be verified.")
        return redirect("home")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "App ID did not return an authorization code.")
        return redirect("home")

    try:
        discovery = _discovery()
        tokens = _json_request(
            discovery["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _absolute_callback_uri(request),
            },
            headers=_basic_auth_header(),
        )
        id_claims = _decode_jwt_claims(tokens.get("id_token", ""))
        if id_claims.get("nonce") and id_claims["nonce"] != expected_nonce:
            raise ValueError("ID token nonce mismatch.")
        if id_claims.get("exp") and int(id_claims["exp"]) < int(time.time()):
            raise ValueError("ID token has expired.")
        audience = id_claims.get("aud")
        if audience and settings.APPID_CLIENT_ID not in (audience if isinstance(audience, list) else [audience]):
            raise ValueError("ID token audience mismatch.")

        userinfo = _json_request(
            discovery["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
    except (KeyError, ValueError, error.URLError, json.JSONDecodeError):
        messages.error(request, "App ID sign in failed. Please try again.")
        return redirect("home")

    request.session[SESSION_USER_KEY] = _normalize_user(userinfo, id_claims)
    request.session["appid_token_expires_at"] = int(time.time()) + int(tokens.get("expires_in", 3600))
    messages.success(request, "Signed in with IBM App ID.")
    return redirect(next_url)


def appid_logout(request):
    request.session.pop(SESSION_USER_KEY, None)
    request.session.pop("appid_token_expires_at", None)
    messages.success(request, "Signed out.")
    return redirect(_safe_next_url(request.GET.get("next"), reverse("home")))


class AppIDRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._must_redirect_to_login(request):
            login_url = f"{reverse('appid_login')}?{parse.urlencode({'next': request.get_full_path()})}"
            return redirect(login_url)
        return self.get_response(request)

    def _must_redirect_to_login(self, request):
        if not settings.APPID_REQUIRE_LOGIN or not _is_configured():
            return False
        if request.session.get(SESSION_USER_KEY):
            return False
        path = request.path
        protected_prefixes = getattr(
            settings,
            "APPID_PROTECTED_PATH_PREFIXES",
            DEFAULT_PROTECTED_PATH_PREFIXES,
        ) or DEFAULT_PROTECTED_PATH_PREFIXES
        exempt_prefixes = tuple(getattr(settings, "APPID_EXEMPT_PATH_PREFIXES", ()) or ())
        exempt_prefixes = (
            reverse("appid_login"),
            reverse("appid_callback"),
            reverse("appid_logout"),
            settings.STATIC_URL,
            settings.MEDIA_URL,
            "/admin/",
            *exempt_prefixes,
        )
        if _path_matches_prefixes(path, exempt_prefixes):
            return False
        return _path_matches_prefixes(path, protected_prefixes)
