"""Verificación de tokens de Google OAuth en el backend.

El frontend obtiene un ID token con Google Identity Services y lo envía aquí.
El backend lo verifica en dos capas:

1. Criptográfica: `verify_oauth2_token` comprueba la firma contra las claves
   públicas de Google y la expiración.
2. Reglas de negocio: `validar_claims_google` exige emisor, audiencia (nuestro
   client id), expiración, identificador de usuario y correo **verificado**.
   Sin el correo verificado no se puede vincular una cuenta existente por email.
"""
from datetime import datetime, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings

# Emisores válidos de los ID tokens de Google.
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def validar_claims_google(info: dict, client_id: str, ahora: datetime | None = None) -> dict:
    """Valida los claims de un ID token ya verificado criptográficamente.

    Lanza ValueError con un mensaje claro si algo no cumple. Devuelve los datos
    mínimos del usuario. Pura: no hace red ni lee configuración.
    """
    ahora = ahora or datetime.now(timezone.utc)

    if info.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError("Token de Google inválido: emisor no reconocido.")
    if not client_id or info.get("aud") != client_id:
        raise ValueError("Token de Google inválido: audiencia distinta de este backend.")

    try:
        expira = int(info["exp"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Token de Google inválido: sin fecha de expiración.") from exc
    if expira <= int(ahora.timestamp()):
        raise ValueError("Token de Google expirado.")

    if not info.get("sub") or not info.get("email"):
        raise ValueError("El token de Google no contiene la información mínima requerida.")
    if info.get("email_verified") not in (True, "true"):
        raise ValueError("Tu correo de Google no está verificado.")

    return {
        "google_id": str(info["sub"]),
        "email": str(info["email"]).lower(),
        "name": info.get("name") or str(info["email"]).split("@")[0],
        "profile_image": info.get("picture"),
    }


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
    except Exception as exc:  # token expirado, audiencia inválida, firma incorrecta, red, etc.
        raise ValueError(f"Token de Google inválido: {exc}") from exc

    return validar_claims_google(info, settings.GOOGLE_CLIENT_ID)
