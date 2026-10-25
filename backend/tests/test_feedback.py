"""PQRS y adaptación Nielsen: persistencia, permisos, validación y exportación.

Solo SQLite temporal de conftest; ningún proveedor remoto ni base real.
"""
import csv
import io
import os
from uuid import uuid4

os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["TEACHER_EMAILS"] = ""
os.environ["FEEDBACK_REVIEWER_EMAILS"] = "reviewer@example.com, student@example.com"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.main import app
from app.database.session import SessionLocal
from app.models.feedback import Feedback, UsabilityEvaluation
from app.models.user import User
from app.api.routes.ai import limiter


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def accounts(client):
    limiter.reset()
    result = {}
    for alias, role in (("reviewer", "TEACHER"), ("teacher", "TEACHER"), ("student", "STUDENT"), ("peer", "STUDENT")):
        response = client.post('/api/auth/dev', json={"email": f"{alias}@example.com", "name": alias, "role": role})
        assert response.status_code == 200
        result[alias] = {"Authorization": f"Bearer {response.json()['access_token']}"}
    limiter.reset()
    return result


def evaluation(**updates):
    return {"submission_id": str(uuid4()), "version": "insoft-nielsen-v1",
            "respuestas": {f"h{i:02d}": 4 if i < 10 else None for i in range(1, 11)},
            "pagina": "/courses/1/subtopics/2", "comentario": "=un ejemplo de comentario", **updates}


def test_pqrs_persists_owner_and_trims_text(client, accounts):
    result = client.post('/api/feedback', headers=accounts['student'], json={
        "tipo": "Sugerencia", "categoria": "Asistente de IA", "comentario": "  Una sugerencia educativa.  ", "pagina": "/dashboard"})
    assert result.status_code == 201, result.text
    with SessionLocal() as db:
        item = db.get(Feedback, result.json()['id'])
        assert item.comentario == "Una sugerencia educativa."
        assert db.get(User, item.user_id).email == 'student@example.com'
    assert set(result.json()) == {'id', 'creado_en'}


def test_evaluation_retries_count_once_and_do_not_overwrite(client, accounts):
    payload = evaluation()
    first = client.post('/api/feedback/evaluations', headers=accounts['student'], json=payload)
    second = client.post('/api/feedback/evaluations', headers=accounts['student'], json={**payload, 'comentario': 'otro texto'})
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(UsabilityEvaluation).where(UsabilityEvaluation.submission_id == payload['submission_id'])) == 1
        row = db.get(UsabilityEvaluation, first.json()['id'])
        assert row.respuestas['h10'] is None
        assert row.comentario == payload['comentario']
    assert client.post('/api/feedback/evaluations', headers=accounts['peer'], json=payload).status_code == 409


@pytest.mark.parametrize('updates', [
    {'version': 'inventada'}, {'user_id': 99}, {'respuestas': {'h01': 4}},
    {'respuestas': {f'h{i:02d}': None for i in range(1, 11)}},
    *[{'respuestas': {f'h{i:02d}': bad for i in range(1, 11)}} for bad in [0, 6, True, '4', 2.5]],
    {'pagina': 'https://example.com'}, {'pagina': '//example.com'},
    {'pagina': '/dashboard?token=private'}, {'pagina': '/dashboard#private'},
    {'comentario': 'x' * 2001},
])
def test_invalid_evaluations_rejected(client, accounts, updates):
    response = client.post('/api/feedback/evaluations', headers=accounts['student'], json=evaluation(**updates))
    assert response.status_code == 422, response.text


def test_auth_and_explicit_reviewer_permission(client, accounts):
    assert client.post('/api/feedback/evaluations', json=evaluation()).status_code == 401
    assert client.post('/api/feedback', json={}).status_code == 401
    assert client.get('/api/feedback/export.csv').status_code == 401
    for alias in ('peer', 'teacher'):
        assert client.get('/api/feedback/access', headers=accounts[alias]).json() == {'can_review': False}
        assert client.get('/api/feedback/export.csv', headers=accounts[alias]).status_code == 403
    assert client.get('/api/feedback/access', headers=accounts['reviewer']).json() == {'can_review': True}
    assert client.get('/api/feedback/access', headers=accounts['student']).json() == {'can_review': True}


def test_csv_no_account_pii_and_safe_spreadsheet_cells(client, accounts):
    client.post('/api/feedback/evaluations', headers=accounts['student'], json=evaluation())
    response = client.get('/api/feedback/export.csv', headers=accounts['reviewer'])
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert '@example.com' not in response.text
    rows = list(csv.DictReader(io.StringIO(response.text.lstrip('\ufeff'))))
    survey = next(row for row in rows if row['tipo_registro'] == 'evaluacion')
    assert survey['h01'] == '4' and survey['h10'] == ''
    assert survey['comentario'].startswith("'=")
    assert survey['participante'].startswith('P')


def test_submission_rate_limited(client, accounts):
    for _ in range(5):
        assert client.post('/api/feedback/evaluations', headers=accounts['peer'], json=evaluation()).status_code == 201
    assert client.post('/api/feedback/evaluations', headers=accounts['peer'], json=evaluation()).status_code == 429


def test_private_list_students_allowed_only_by_explicit_permission(client, accounts):
    assert client.get('/api/feedback/review').status_code == 401
    assert client.get('/api/feedback/review', headers=accounts['peer']).status_code == 403
    assert client.get('/api/feedback/review', headers=accounts['teacher']).status_code == 403
    for kind in ('pqrs', 'evaluacion'):
        response = client.get('/api/feedback/review', params={'kind': kind, 'limit': 1}, headers=accounts['student'])
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        assert len(response.json()['items']) <= 1
        assert '@example.com' not in response.text
        assert 'user_id' not in response.text
    assert client.get('/api/feedback/review?limit=51', headers=accounts['student']).status_code == 422
    assert client.get('/api/feedback/review?offset=-1', headers=accounts['student']).status_code == 422
    assert client.get('/api/feedback/review?kind=otro', headers=accounts['student']).status_code == 422
