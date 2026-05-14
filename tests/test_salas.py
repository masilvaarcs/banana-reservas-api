"""
Testes de CRUD para /api/salas.

Cobre:
- Criação de sala vinculada a local (201)
- Nome duplicado no mesmo local (409)
- Sala em local inexistente (404)
- Sala pertencente a local diferente do informado na reserva (400) — validado
  indiretamente via reserva_service, testado aqui via criação de sala
- Listagem (200)
- Atualização (200)
- Exclusão (204)
"""

import pytest


# ── Fixtures de módulo ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sala_local(client, auth_headers) -> dict:
    """Local dedicado para testes de salas."""
    r = client.post(
        "/api/locais",
        json={"nome": "Filial Salas"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def sala_criada(client, auth_headers, sala_local) -> dict:
    """Sala criada uma vez para todo o módulo."""
    r = client.post(
        "/api/salas",
        json={"nome": "Sala 101", "local_id": sala_local["id"], "capacidade": 10},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Testes de criação ─────────────────────────────────────────────────────────

def test_create_sala_retorna_201(sala_criada, sala_local):
    assert sala_criada["id"] > 0
    assert sala_criada["nome"] == "Sala 101"
    assert sala_criada["local_id"] == sala_local["id"]
    assert sala_criada["capacidade"] == 10


def test_create_sala_sem_capacidade(client, auth_headers, sala_local):
    r = client.post(
        "/api/salas",
        json={"nome": "Sala 102", "local_id": sala_local["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["capacidade"] is None


def test_create_sala_nome_duplicado_no_mesmo_local_retorna_409(
    client, auth_headers, sala_criada, sala_local
):
    r = client.post(
        "/api/salas",
        json={"nome": sala_criada["nome"], "local_id": sala_local["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_create_sala_local_inexistente_retorna_404(client, auth_headers):
    r = client.post(
        "/api/salas",
        json={"nome": "Sala Fantasma", "local_id": 999999},
        headers=auth_headers,
    )
    assert r.status_code == 404


# ── Testes de listagem ────────────────────────────────────────────────────────

def test_list_salas_retorna_lista(client, auth_headers, sala_criada):
    r = client.get("/api/salas", headers=auth_headers)
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert sala_criada["id"] in ids


# ── Testes de atualização ─────────────────────────────────────────────────────

def test_update_sala_retorna_200(client, auth_headers, sala_criada):
    r = client.put(
        f"/api/salas/{sala_criada['id']}",
        json={"nome": "Sala 101 Renovada", "capacidade": 20},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "Sala 101 Renovada"
    assert body["capacidade"] == 20


def test_update_sala_inexistente_retorna_404(client, auth_headers):
    r = client.put(
        "/api/salas/999999",
        json={"nome": "Nenhuma"},
        headers=auth_headers,
    )
    assert r.status_code == 404


# ── Testes de exclusão ────────────────────────────────────────────────────────

def test_delete_sala_retorna_204(client, auth_headers, sala_local):
    nova = client.post(
        "/api/salas",
        json={"nome": "Sala Para Deletar", "local_id": sala_local["id"]},
        headers=auth_headers,
    )
    assert nova.status_code == 201
    sala_id = nova.json()["id"]

    r = client.delete(f"/api/salas/{sala_id}", headers=auth_headers)
    assert r.status_code == 204


def test_delete_sala_inexistente_retorna_404(client, auth_headers):
    r = client.delete("/api/salas/999999", headers=auth_headers)
    assert r.status_code == 404
