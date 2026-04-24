import json
import re
import time
from base64 import b64decode, b64encode
from urllib import error, request
from urllib.parse import quote

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={api_key}"
)
SARVAM_TTS_API_URL = "https://api.sarvam.ai/text-to-speech"
ERROR_TYPES = {"syntax", "logic", "indent", "missing", "typo", "general"}
RETRYABLE_STATUS_CODES = {429, 503}
DEFAULT_GEMINI_FALLBACK_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
)
ROAST_LANGUAGE_RULES = {
    "english": {
        "label": "English (India)",
        "instruction": (
            "Write all user-facing text in simple English that is easy for an Indian English speaker to understand. "
            "For the roast only, you may naturally use casual Indian slang like bhai, yaar, arre, or bro when it fits."
        ),
    },
    "hindi": {
        "label": "Hindi",
        "instruction": (
            "Write all user-facing text in simple natural Hindi using Devanagari script. "
            "Keep code, variable names, symbols, and fixCode unchanged."
        ),
    },
    "telugu": {
        "label": "Telugu",
        "instruction": (
            "Write all user-facing text in simple natural Telugu using Telugu script. "
            "Keep code, variable names, symbols, and fixCode unchanged."
        ),
    },
}
DEFAULT_RESPONSE = {
    "hasError": True,
    "errorType": "general",
    "errorMessage": "CodeRoast AI could not roast that snippet right now.",
    "mistakeLine": "The AI response was unavailable, so the roast engine needs a retry.",
    "roast": "Even the roast bot glitched. Give it another shot and we'll drag the bug properly.",
    "fix": "Try again in a moment, and make sure your Gemini API key is configured.",
    "fixCode": "// Roast engine could not prepare a corrected snippet yet.",
}
SARVAM_LANGUAGE_CODES = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "telugu": "te-IN",
}


@ensure_csrf_cookie
def index(request):
    return render(request, "coderoast/index.html")


def _corsify(response):
    allowed_origins = settings.CORS_ALLOWED_ORIGINS or []
    origin = allowed_origins[0] if allowed_origins else "*"
    response["Access-Control-Allow-Origin"] = origin
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response


def _json_response(payload, status=200):
    return _corsify(JsonResponse(payload, status=status))


def _normalize_payload(payload):
    normalized = DEFAULT_RESPONSE.copy()
    normalized.update({key: payload.get(key, value) for key, value in DEFAULT_RESPONSE.items()})
    normalized["hasError"] = bool(normalized.get("hasError"))

    error_type = str(normalized.get("errorType", "general")).lower()
    normalized["errorType"] = error_type if error_type in ERROR_TYPES else "general"

    for key in ("errorMessage", "mistakeLine", "roast", "fix", "fixCode"):
        value = normalized.get(key, "")
        normalized[key] = value if isinstance(value, str) else str(value)
    return normalized


def _error_response(message, mistake_line, fix, *, status, roast=None, fix_code=None):
    payload = {
        "errorMessage": message,
        "mistakeLine": mistake_line,
        "fix": fix,
    }
    if roast:
        payload["roast"] = roast
    if fix_code is not None:
        payload["fixCode"] = fix_code
    return _json_response(_normalize_payload(payload), status=status)


def _extract_text(response_data):
    candidates = response_data.get("candidates") or []
    if not candidates:
        raise ValueError("No candidates returned by Gemini.")

    parts = candidates[0].get("content", {}).get("parts", [])
    combined = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not combined:
        raise ValueError("Gemini returned an empty response body.")
    return combined


def _extract_json_object(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Gemini did not return a JSON object.")
    return cleaned[start : end + 1]


def _parse_roast_payload(response_data):
    raw_text = _extract_text(response_data)
    return json.loads(_extract_json_object(raw_text))


def _build_http_error_payload(exc):
    payload = {
        "errorMessage": "Gemini request failed.",
        "mistakeLine": "The AI provider rejected the roast request before it returned usable JSON.",
        "fix": "Verify the API key, model name, and billing or provider access, then try again.",
        "roast": "The roast bot got bounced at the door before it could even insult the code.",
    }
    try:
        details = exc.read().decode("utf-8", errors="replace")
    except Exception:
        details = str(exc)

    lowered = details.lower()
    if exc.code == 429 or "quota exceeded" in lowered or "resource_exhausted" in lowered:
        payload.update(
            {
                "errorMessage": "Gemini quota exceeded.",
                "mistakeLine": "The current Google AI Studio quota for this model or project has been exhausted.",
                "fix": "Wait for quota to reset, add billing, or switch to a model with available quota and retry.",
                "roast": "The roast bot spent the whole daily budget before it could roast this snippet. The API meter tapped out first.",
            }
        )
    elif exc.code == 503 or "high demand" in lowered or "unavailable" in lowered:
        payload.update(
            {
                "errorMessage": "Gemini is temporarily unavailable.",
                "mistakeLine": "The Gemini model is currently under high demand and could not answer the roast request.",
                "fix": "Wait a moment and try again. If it keeps happening, retry later or switch to another supported model.",
                "roast": "The roast bot is stuck in a traffic jam of prompts. Give it a moment and it should get mean again.",
            }
        )
    elif exc.code == 404 or "not found for api version" in lowered or "not supported for generatecontent" in lowered:
        attempted_models = getattr(exc, "models_tried", []) or []
        payload.update(
            {
                "errorMessage": "Gemini model configuration failed.",
                "mistakeLine": "The configured Gemini model was not accepted by the API.",
                "fix": (
                    "Use a supported text model such as gemini-2.5-flash or gemini-2.5-flash-lite, "
                    "then restart Django and retry."
                ),
            }
        )
        if attempted_models:
            payload["mistakeLine"] = (
                "The Gemini API rejected every configured model candidate: "
                f"{', '.join(attempted_models)}."
            )
    elif exc.code in {401, 403} or "api key" in lowered or "permission" in lowered:
        payload.update(
            {
                "errorMessage": "Gemini authentication failed.",
                "mistakeLine": "The configured key was rejected by the Gemini API.",
                "fix": "Use a valid Google AI Studio Gemini key in .env and restart Django.",
            }
        )

    normalized = _normalize_payload(payload)
    normalized["details"] = details
    return normalized


def _build_prompt(code, language, roast_language):
    language_config = ROAST_LANGUAGE_RULES.get(roast_language, ROAST_LANGUAGE_RULES["english"])
    return f"""
You are CodeRoast AI, a funny senior code reviewer.
{language_config["instruction"]}

Analyze the following {language} code. Return ONLY valid JSON with these exact fields:
{{
  "hasError": true,
  "errorType": "syntax|logic|indent|missing|typo|general",
  "errorMessage": "short compiler-style error message",
  "mistakeLine": "one line describing the exact mistake simply",
  "roast": "2-3 sentence savage funny roast with emojis like skull, crying, fire, eyes mixed naturally, max 45 words",
  "fix": "short fix description",
  "fixCode": "corrected code snippet only"
}}

Rules:
- Return JSON only. No markdown fences. No explanation outside JSON.
- If the code looks correct, set hasError to false, errorType to "general", errorMessage to "No critical errors detected", and still provide a playful roast plus a small improvement in fix/fixCode.
- Use short, simple sentences and common words.
- The requested roast language is {language_config["label"]}.
- If the requested roast language is Hindi, write errorMessage, mistakeLine, roast, and fix in clear Hindi.
- If the requested roast language is Telugu, write errorMessage, mistakeLine, roast, and fix in clear Telugu.
- If the requested roast language is English, prefer clear Indian English style over slang-heavy US internet English.
- For English roasts, sound like a sharp Indian friend roasting another coder: casual, punchy, and local.
- mistakeLine must describe the exact mistake simply.
- fixCode must contain only corrected code.
- Keep roast under 45 words and include emojis naturally.
- Make the roast feel personal to THIS exact snippet, not generic.
- In the roast, mention at least one exact detail copied from the code, such as a variable name, function name, operator, keyword, literal, or missing symbol.
- If the main problem is syntax, directly mention the missing token or broken statement. Example: missing `:` after `def greet(name)`.
- If the main problem is logic, directly mention the wrong variable, wrong condition, wrong return value, or wrong index.
- Be harsher, more savage, and more confident when the code is broken. Roast the coding choice, not the human identity.
- For English roasts, you may use words like "bhai", "yaar", "bro", "arre", or "scene kya hai" if they fit the exact bug.
- Do not force those words into every roast, and do not repeat the same slang every time.
- Avoid repeating generic filler lines like "this code" or "nah" unless they truly fit.
- Vary tone and phrasing across requests so repeated runs do not sound templated.
- If there is a real bug, make the roast sting and tie it directly to that bug.
- Focus the joke on the mistake itself, like missing colon, undefined variable, broken loop, bad indentation, wrong return, or logic fail.
- Keep errorMessage, mistakeLine, and fix very clear and easy to understand for a beginner.
- Do not use vague roast lines. Bad example: "This code is broken 😂"
- Good roast style example: "You wrote `print(username)` after creating `user_name`. Even your variable is not ready to meet itself 😂"
- Good roast style example: "`def greet(name)` is standing without `:` like it forgot the entry ticket. Python rejected it at the door 🔥"
- Good Indian English roast example: "Bhai, `total = price * qty` likha and then returned `totals`. Yaar, even the variable gave up before runtime finished roasting you 💀"

Code:
```{language.lower()}
{code}
```
""".strip()


def _current_gemini_config():
    return settings.GOOGLE_AI_STUDIO_API_KEY, settings.GOOGLE_AI_MODEL


def _candidate_gemini_models(primary_model):
    configured_fallbacks = list(getattr(settings, "CODEROAST_GEMINI_FALLBACK_MODELS", ()) or ())
    ordered_models = [primary_model, *configured_fallbacks, *DEFAULT_GEMINI_FALLBACK_MODELS]
    unique_models = []
    for model_name in ordered_models:
        if model_name and model_name not in unique_models:
            unique_models.append(model_name)
    return unique_models


def _current_sarvam_config():
    return {
        "provider": (settings.CODEROAST_TTS_PROVIDER or "browser").strip().lower(),
        "api_key": settings.SARVAM_API_KEY.strip(),
        "model": (settings.SARVAM_TTS_MODEL or "bulbul:v3").strip(),
        "audio_codec": (settings.SARVAM_TTS_AUDIO_CODEC or "mp3").strip().lower(),
        "speakers": {
            "english": settings.SARVAM_TTS_ENGLISH_SPEAKER.strip(),
            "hindi": settings.SARVAM_TTS_HINDI_SPEAKER.strip(),
            "telugu": settings.SARVAM_TTS_TELUGU_SPEAKER.strip(),
        },
    }


def _current_cloudant_config():
    return {
        "enabled": bool(settings.CLOUDANT_ASSETS_ENABLED),
        "url": settings.CLOUDANT_URL.strip().rstrip("/"),
        "database": settings.CLOUDANT_DATABASE.strip(),
        "username": settings.CLOUDANT_USERNAME.strip(),
        "password": settings.CLOUDANT_PASSWORD.strip(),
        "bearer_token": settings.CLOUDANT_BEARER_TOKEN.strip(),
        "asset_group": (settings.CLOUDANT_ASSET_GROUP or "coderoast").strip(),
    }


def _cloudant_headers(cloudant_config):
    headers = {"Content-Type": "application/json"}
    if cloudant_config["bearer_token"]:
        headers["Authorization"] = f"Bearer {cloudant_config['bearer_token']}"
        return headers

    if cloudant_config["username"] and cloudant_config["password"]:
        raw_credentials = f"{cloudant_config['username']}:{cloudant_config['password']}".encode("utf-8")
        headers["Authorization"] = f"Basic {b64encode(raw_credentials).decode('ascii')}"
    return headers


def _cloudant_request(cloudant_config, path, payload):
    req = request.Request(
        f"{cloudant_config['url']}/{quote(cloudant_config['database'])}/{path.lstrip('/')}",
        data=json.dumps(payload).encode("utf-8"),
        headers=_cloudant_headers(cloudant_config),
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_cloudant_media_doc(doc):
    if not isinstance(doc, dict):
        return None

    name = str(doc.get("name") or doc.get("title") or "").strip()
    url = str(doc.get("url") or doc.get("assetUrl") or "").strip()
    if not name or not url:
        return None

    tags = doc.get("tags") or ["general"]
    if not isinstance(tags, list):
        tags = [str(tags)]
    clean_tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()]
    return {"name": name, "url": url, "tags": clean_tags or ["general"]}


def _normalize_cloudant_sfx_doc(doc):
    if not isinstance(doc, dict):
        return None

    label = str(doc.get("label") or doc.get("name") or "").strip()
    url = str(doc.get("url") or doc.get("assetUrl") or "").strip()
    bucket = str(doc.get("bucket") or "crowd").strip().lower()
    if not label or not url or bucket not in {"crowd", "evil", "cheer"}:
        return None
    return {"bucket": bucket, "clip": {"label": label, "url": url}}


def _fetch_cloudant_assets():
    cloudant_config = _current_cloudant_config()
    if not cloudant_config["enabled"]:
        return None

    if not cloudant_config["url"] or not cloudant_config["database"]:
        return {
            "enabled": False,
            "source": "local",
            "reason": "Cloudant is enabled but CLOUDANT_URL or CLOUDANT_DATABASE is missing.",
        }

    has_auth = cloudant_config["bearer_token"] or (
        cloudant_config["username"] and cloudant_config["password"]
    )
    if not has_auth:
        return {
            "enabled": False,
            "source": "local",
            "reason": "Cloudant credentials are missing.",
        }

    response_data = _cloudant_request(
        cloudant_config,
        "_find",
        {
            "selector": {
                "assetGroup": cloudant_config["asset_group"],
                "enabled": True,
                "assetType": {"$in": ["meme", "gif", "sfx"]},
            },
            "fields": ["assetType", "name", "title", "label", "url", "assetUrl", "tags", "bucket"],
            "limit": 200,
        },
    )
    docs = response_data.get("docs") or []
    memes = []
    gifs = []
    soundboard = {"crowd": [], "evil": [], "cheer": []}

    for doc in docs:
        asset_type = str(doc.get("assetType") or "").strip().lower()
        if asset_type == "meme":
            media = _normalize_cloudant_media_doc(doc)
            if media:
                memes.append(media)
        elif asset_type == "gif":
            media = _normalize_cloudant_media_doc(doc)
            if media:
                gifs.append(media)
        elif asset_type == "sfx":
            sound = _normalize_cloudant_sfx_doc(doc)
            if sound:
                soundboard[sound["bucket"]].append(sound["clip"])

    return {
        "enabled": bool(memes or gifs or any(soundboard.values())),
        "source": "cloudant",
        "assetGroup": cloudant_config["asset_group"],
        "memes": memes,
        "gifs": gifs,
        "soundboard": {"outro": soundboard},
    }


def _call_gemini_once(code, language, roast_language, api_key, model):
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": _build_prompt(code, language, roast_language)}]}],
            "generationConfig": {
                "temperature": 0.9,
                "responseMimeType": "application/json",
            },
        }
    ).encode("utf-8")

    last_exception = None
    for attempt, delay_seconds in enumerate((0, 1.2, 2.5), start=1):
        if delay_seconds:
            time.sleep(delay_seconds)

        req = request.Request(
            GEMINI_API_URL.format(model=model, api_key=api_key),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            last_exception = exc
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == 3:
                raise
        except error.URLError as exc:
            last_exception = exc
            if attempt == 3:
                raise

    if last_exception:
        raise last_exception
    raise RuntimeError("Gemini request failed before a response was produced.")


def _call_gemini(code, language, roast_language, api_key, primary_model):
    last_exception = None
    tried_models = []

    for model_name in _candidate_gemini_models(primary_model):
        tried_models.append(model_name)
        try:
            response_data = _call_gemini_once(code, language, roast_language, api_key, model_name)
            return _parse_roast_payload(response_data), model_name
        except error.HTTPError as exc:
            last_exception = exc
            setattr(last_exception, "models_tried", tried_models.copy())
            if exc.code not in (RETRYABLE_STATUS_CODES | {404}):
                raise
        except (error.URLError, ValueError, json.JSONDecodeError) as exc:
            last_exception = exc
            setattr(last_exception, "models_tried", tried_models.copy())

    if last_exception:
        raise last_exception
    raise RuntimeError("Gemini request failed before a response was produced.")


def _sarvam_mime_type(audio_codec):
    return {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "aac": "audio/aac",
        "opus": "audio/opus",
        "flac": "audio/flac",
        "pcm": "audio/pcm",
        "mulaw": "audio/basic",
        "alaw": "audio/basic",
    }.get(audio_codec, "audio/mpeg")


def _build_sarvam_tts_payload(text, roast_language):
    sarvam_config = _current_sarvam_config()
    if sarvam_config["provider"] != "sarvam" or not sarvam_config["api_key"] or not text.strip():
        return None

    language_code = SARVAM_LANGUAGE_CODES.get(roast_language, "en-IN")
    speaker = sarvam_config["speakers"].get(roast_language) or sarvam_config["speakers"].get("english")
    body = {
        "text": text.strip(),
        "target_language_code": language_code,
        "model": sarvam_config["model"],
        "output_audio_codec": sarvam_config["audio_codec"],
    }
    if speaker:
        body["speaker"] = speaker

    req = request.Request(
        SARVAM_TTS_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "api-subscription-key": sarvam_config["api_key"],
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    audio_chunks = response_data.get("audios") or []
    if not audio_chunks:
        raise ValueError("Sarvam TTS returned no audio.")

    audio_base64 = str(audio_chunks[0]).strip()
    b64decode(audio_base64, validate=True)
    return {
        "provider": "sarvam",
        "mode": "server_tts",
        "audioSrc": f"data:{_sarvam_mime_type(sarvam_config['audio_codec'])};base64,{audio_base64}",
        "speaker": speaker or "default",
        "languageCode": language_code,
        "model": sarvam_config["model"],
    }


def _parse_request_payload(request_obj):
    try:
        payload = json.loads(request_obj.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise ValueError("invalid_json")

    code = (payload.get("code") or "").strip()
    language = (payload.get("language") or "").strip()
    roast_language = (payload.get("roastLanguage") or "english").strip().lower()
    if roast_language not in ROAST_LANGUAGE_RULES:
        roast_language = "english"
    return code, language, roast_language


@require_http_methods(["GET", "OPTIONS"])
def assets(request):
    if request.method == "OPTIONS":
        return _json_response({"ok": True})

    try:
        payload = _fetch_cloudant_assets()
    except (error.HTTPError, error.URLError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "enabled": False,
            "source": "local",
            "reason": str(exc),
        }
    return _json_response(payload or {"enabled": False, "source": "local"})


@require_http_methods(["POST", "OPTIONS"])
def roast(request):
    if request.method == "OPTIONS":
        return _json_response({"ok": True})

    try:
        code, language, roast_language = _parse_request_payload(request)
    except ValueError:
        return _error_response(
            "Invalid JSON request body.",
            "The browser sent something the roast endpoint could not parse.",
            "Send a JSON payload with code and language.",
            status=400,
        )

    if not code or not language:
        return _error_response(
            "Missing code or language.",
            "CodeRoast AI needs both the source code and selected language.",
            "Fill the editor and choose a language before running.",
            status=400,
        )

    api_key, model = _current_gemini_config()
    if not api_key:
        return _error_response(
            "Gemini API key is not configured.",
            "The backend could not find GOOGLE_AI_STUDIO_API_KEY or GEMINI_API_KEY.",
            "Add the Gemini key to .env and restart Django.",
            status=500,
        )

    try:
        roast_payload, used_model = _call_gemini(code, language, roast_language, api_key, model)
        response_payload = _normalize_payload(roast_payload)
        response_payload["modelUsed"] = used_model

        try:
            tts_payload = _build_sarvam_tts_payload(response_payload.get("roast", ""), roast_language)
        except (error.HTTPError, error.URLError, ValueError, json.JSONDecodeError):
            tts_payload = None

        if tts_payload:
            response_payload["tts"] = tts_payload
        return _json_response(response_payload)
    except error.HTTPError as exc:
        return _json_response(_build_http_error_payload(exc), status=exc.code)
    except (error.URLError, ValueError, json.JSONDecodeError) as exc:
        fallback = _normalize_payload(
            {
                "errorMessage": "Gemini response parsing failed.",
                "mistakeLine": "The AI backend did not return valid roast JSON this time.",
                "fix": "Retry the request. If it keeps failing, verify the API key and model name.",
                "roast": "The roast cannon jammed mid-shot. Even the AI forgot its commas. Try the button again.",
                "fixCode": code,
            }
        )
        fallback["details"] = str(exc)
        return _json_response(fallback, status=502)
