"""Verificación de tokens de Google OAuth en el backend.

El frontend obtiene un ID token con Google Identity Services y lo envía aquí.
El backend lo verifica criptográficamente contra Google; nunca confía en los
datos que envíe el cliente sin verificar.
"""
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


def verify_google_credential(credential: str) -> dict:
    """Verifica un ID token de Google y devuelve la información básica del usuario.

    Lanza ValueError si el token no es válido.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID no está configurado en el backend.")

    try:
        info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:  # token expirado, audiencia inválida, firma incorrecta, etc.
        raise ValueError(f"Token de Google inválido: {exc}") from exc

    if not info.get("sub") or not info.get("email"):
        raise ValueError("El token de Google no contiene la información mínima requerida.")

    return {
        "google_id": info["sub"],
        "email": info["email"].lower(),
        "name": info.get("name") or info["email"].split("@")[0],
        "profile_image": info.get("picture"),
    }
