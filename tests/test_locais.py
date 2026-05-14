"""
Testes de CRUD para o recurso /api/locais.

Cobre:
- Rejeição de acesso sem token JWT (401)
- Listagem inicial vazia
- Criação de local (201)
- Duplicidade de nome (409)
- Atualização (200)
- Exclusão (204)
- Recurso inexistente (404)
"""

import pytest


# ── Fixtures de módulo ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def local_criado(client, auth_headers) -> dict:
    """Cria um local uma vez para todo o módulo."""
    r = client.post(
        "/api/locais",
        json={"nome": "Filial Alpha", "descricao": "Sede principal de testes"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Testes de autenticação ────────────────────────────────────────────────────

def test_list_locais_sem_token_retorna_401(client):
    r = client.get("/api/locais")
    assert r.status_code == 401


def test_create_local_sem_token_retorna_401(client):
    r = client.post("/api/locais", json={"nome": "Sem Auth"})
    assert r.status_code == 401


# ── Testes de criação ─────────────────────────────────────────────────────────

def test_create_local_retorna_201(local_criado):
    """Fixture cria o local; este teste só valida o resultado."""
    assert local_criado["id"] > 0
    assert local_criado["nome"] == "Filial Alpha"
    assert local_criado["descricao"] == "Sede principal de testes"


def test_create_local_sem_descricao(client, auth_headers):
    r = client.post(
        "/api/locais",
        json={"nome": "Filial Beta"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["descricao"] is None


def test_create_local_nome_duplicado_retorna_409(client, auth_headers, local_criado):
    r = client.post(
        "/api/locais",
        json={"nome": local_criado["nome"]},
        headers=auth_headers,
    )
    assert r.status_code == 409


# ── Testes de listagem ────────────────────────────────────────────────────────

def test_list_locais_retorna_lista(client, auth_headers, local_criado):
    r = client.get("/api/locais", headers=auth_headers)
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]
    assert local_criado["id"] in ids


# ── Testes de atualização ─────────────────────────────────────────────────────

def test_update_local_retorna_200(client, auth_headers, local_criado):
    r = client.put(
        f"/api/locais/{local_criado['id']}",
        json={"nome": "Filial Alpha Atualizada"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Filial Alpha Atualizada"


def test_update_local_inexistente_retorna_404(client, auth_headers):
    r = client.put(
        "/api/locais/999999",
        json={"nome": "Não Existe"},
        headers=auth_headers,
    )
    assert r.status_code == 404


# ── Testes de exclusão ────────────────────────────────────────────────────────

def test_delete_local_retorna_204(client, auth_headers):
    """Cria e exclui um local dedicado para não afetar outros testes."""
    novo = client.post(
        "/api/locais",
        json={"nome": "Filial Para Deletar"},
        headers=auth_headers,
    )
    assert novo.status_code == 201
    local_id = novo.json()["id"]

    r = client.delete(f"/api/locais/{local_id}", headers=auth_headers)
    assert r.status_code == 204

    # Confirma que foi removido
    lista = client.get("/api/locais", headers=auth_headers)
    ids = [item["id"] for item in lista.json()]
    assert local_id not in ids


def test_delete_local_inexistente_retorna_404(client, auth_headers):
    r = client.delete("/api/locais/999999", headers=auth_headers)
    assert r.status_code == 404
