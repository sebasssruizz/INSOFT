"""Autenticación endurecida: claims de Google y JWT. Todo con tokens simulados (sin red)."""
import base64
import json
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")
os.environ.setdefault("TEACHER_EMAILS", "")

import pytest
from fastapi.testclient import TestClient
from jose import JWTError, jwt

from app.auth import google as google_auth
from app.auth.jwt import create_access_token, decode_access_token
from app.core.config import Settings, settings
from app.main import app

CLIENT_ID = "1234-prueba.apps.googleusercontent.com"
AHORA = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def _claims(**cambios):
    base = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "exp": int((AHORA + timedelta(minutes=30)).timestamp()),
        "sub": "107000000000000000001",
        "email": "Estudiante.Ejemplo@Example.com",
        "email_verified": True,
        "name": "Estudiante Ejemplo",
        "picture": None,
    }
    base.update(cambios)
    return base


# ── Google: validación de claims ──────────────────────────────────────────────


def test_claims_validos_se_aceptan_y_normalizan_el_correo():
    usuario = google_auth.validar_claims_google(_claims(), CLIENT_ID, AHORA)
    assert usuario["email"] == "estudiante.ejemplo@example.com"
    assert usuario["google_id"] == "107000000000000000001"


@pytest.mark.parametrize("cambio", [
    {"iss": "https://evil.example.com"},
    {"aud": "otro-cliente.apps.googleusercontent.com"},
    {"exp": int((AHORA - timedelta(seconds=1)).timestamp())},
    {"email_verified": False},
    {"email_verified": "false"},
    {"email_verified": None},
    {"sub": ""},
])
def test_claims_invalidos_se_rechazan(cambio):
    with pytest.raises(ValueError):
        google_auth.validar_claims_google(_claims(**cambio), CLIENT_ID, AHORA)


def test_sin_fecha_de_expiracion_se_rechaza():
    info = _claims()
    del info["exp"]
    with pytest.raises(ValueError, match="expiración"):
        google_auth.validar_claims_google(info, CLIENT_ID, AHORA)


def test_sin_client_id_configurado_se_rechaza():
    with pytest.raises(ValueError, match="audiencia"):
        google_auth.validar_claims_google(_claims(), "", AHORA)


def test_verificacion_completa_falla_si_la_libreria_rechaza_el_token(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", CLIENT_ID)

    def _rechaza(*args, **kwargs):
        raise ValueError("Token used too late")

    monkeypatch.setattr(google_auth.google_id_token, "verify_oauth2_token", _rechaza)
    with pytest.raises(ValueError, match="inválido"):
        google_auth.verify_google_credential("token-simulado")


def test_verificacion_completa_aplica_las_reglas_de_negocio(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", CLIENT_ID)
    vigente = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    monkeypatch.setattr(google_auth.google_id_token, "verify_oauth2_token",
                        lambda *a, **k: _claims(email_verified=False, exp=vigente))
    with pytest.raises(ValueError, match="verificado"):
        google_auth.verify_google_credential("token-simulado")


# ── JWT: caducidad, firma, algoritmo, expiración configurable ─────────────────


def _firmar(payload, key=None, alg="HS256"):
    return jwt.encode(payload, key or settings.SECRET_KEY, algorithm=alg)


def test_token_valido_se_decodifica():
    token = create_access_token(42, "STUDENT")
    assert decode_access_token(token)["sub"] == "42"


def test_token_caducado_se_rechaza():
    pasado = datetime.now(timezone.utc) - timedelta(minutes=5)
    with pytest.raises(JWTError):
        decode_access_token(_firmar({"sub": "1", "role": "STUDENT", "exp": pasado}))


def test_token_sin_exp_se_rechaza():
    with pytest.raises(JWTError):
        decode_access_token(_firmar({"sub": "1", "role": "STUDENT"}))


def test_token_sin_sub_se_rechaza():
    futuro = datetime.now(timezone.utc) + timedelta(minutes=5)
    with pytest.raises(JWTError):
        decode_access_token(_firmar({"role": "STUDENT", "exp": futuro}))


def test_token_firmado_con_otra_clave_se_rechaza():
    futuro = datetime.now(timezone.utc) + timedelta(minutes=5)
    with pytest.raises(JWTError):
        decode_access_token(_firmar({"sub": "1", "exp": futuro}, key="otra-clave-no-es-la-buena"))


def test_token_alg_none_se_rechaza():
    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

    futuro = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': '1', 'exp': futuro})}."
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_expiracion_configurada_se_aplica(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    token = create_access_token(7, "TEACHER")
    exp = datetime.fromtimestamp(decode_access_token(token)["exp"], tz=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    assert timedelta(minutes=14) < delta <= timedelta(minutes=15)


@pytest.mark.parametrize("minutos", [0, 4, 60 * 24 * 31])
def test_expiracion_fuera_de_rango_impide_arrancar(minutos):
    with pytest.raises(RuntimeError, match="fuera de rango"):
        Settings(
            DEV_AUTH_ENABLED=True,
            SECRET_KEY="clave-de-prueba-suficientemente-larga-0123456789",
            ACCESS_TOKEN_EXPIRE_MINUTES=minutos,
        )


# ── Endpoint: 401 por sesión vencida o token inválido ─────────────────────────


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_endpoint_401_con_sesion_vencida_y_mensaje_estable(client):
    creado = client.post("/api/auth/dev", json={"email": "auth-end@example.com", "name": "A", "role": "STUDENT"})
    assert creado.status_code == 200, creado.text
    user_id = creado.json()["user"]["id"]

    pasado = datetime.now(timezone.utc) - timedelta(minutes=1)
    vencido = _firmar({"sub": str(user_id), "role": "STUDENT", "exp": pasado})
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {vencido}"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "No autenticado o token inválido."}
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_endpoint_200_con_token_vigente(client):
    creado = client.post("/api/auth/dev", json={"email": "auth-ok@example.com", "name": "B", "role": "STUDENT"})
    user_id = creado.json()["user"]["id"]
    token = create_access_token(user_id, "STUDENT")
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


def test_endpoint_401_si_el_usuario_ya_no_existe(client):
    token = create_access_token(999999, "STUDENT")
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
