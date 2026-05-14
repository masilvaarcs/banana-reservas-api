"""
Testes de CRUD e regras de negócio para /api/reservas.

Cobre os requisitos funcionais do enunciado:
  RF-06  Listagem de reservas
  RF-07  Cadastro de reservas
  RF-08  Edição de reservas
  RF-09  Exclusão de reservas
  RF-10  Validação de choque de horários — CRÍTICO
  RF-11  Exclusão em lote (bônus)

Cada teste usa horários únicos para evitar interferência entre si.
"""

import pytest
from datetime import datetime, timezone


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dt(hour: int, minute: int = 0) -> str:
    """Gera datetime ISO 8601 no dia fixo 2099-06-15 para testes."""
    return datetime(2099, 6, 15, hour, minute, tzinfo=timezone.utc).isoformat()


# ── Fixtures de módulo ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def res_local(client, auth_headers) -> dict:
    r = client.post(
        "/api/locais",
        json={"nome": "Filial Reservas"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def res_sala(client, auth_headers, res_local) -> dict:
    r = client.post(
        "/api/salas",
        json={"nome": "Sala Reservas", "local_id": res_local["id"], "capacidade": 8},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _reserva_payload(local_id: int, sala_id: int, h_inicio: int, h_fim: int, **extra) -> dict:
    return {
        "local_id": local_id,
        "sala_id": sala_id,
        "inicio": _dt(h_inicio),
        "fim": _dt(h_fim),
        "responsavel": "Marcos Teste",
        **extra,
    }


# ── RF-06: Listagem ───────────────────────────────────────────────────────────

def test_list_reservas_retorna_lista(client, auth_headers):
    r = client.get("/api/reservas", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_reservas_sem_token_retorna_401(client):
    r = client.get("/api/reservas")
    assert r.status_code == 401


# ── RF-07: Cadastro ───────────────────────────────────────────────────────────

def test_create_reserva_simples_retorna_201(client, auth_headers, res_local, res_sala):
    payload = _reserva_payload(res_local["id"], res_sala["id"], 8, 9)
    r = client.post("/api/reservas", json=payload, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["responsavel"] == "Marcos Teste"
    assert body["cafe"] is False
    assert body["quantidade_pessoas"] is None


def test_create_reserva_com_cafe_retorna_201(client, auth_headers, res_local, res_sala):
    payload = _reserva_payload(
        res_local["id"], res_sala["id"], 9, 10,
        cafe=True, quantidade_pessoas=5,
    )
    r = client.post("/api/reservas", json=payload, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["cafe"] is True
    assert body["quantidade_pessoas"] == 5


def test_create_reserva_cafe_sem_quantidade_retorna_422(client, auth_headers, res_local, res_sala):
    """RF-07: Pydantic valida que café=True exige quantidade_pessoas."""
    payload = _reserva_payload(
        res_local["id"], res_sala["id"], 10, 11,
        cafe=True,
    )
    r = client.post("/api/reservas", json=payload, headers=auth_headers)
    assert r.status_code == 422


def test_create_reserva_fim_antes_inicio_retorna_422(client, auth_headers, res_local, res_sala):
    """RF-07: Data de fim deve ser posterior à de início."""
    payload = _reserva_payload(res_local["id"], res_sala["id"], 12, 11)  # fim < início
    r = client.post("/api/reservas", json=payload, headers=auth_headers)
    assert r.status_code == 422


def test_create_reserva_sala_de_outro_local_retorna_400(client, auth_headers, res_local, res_sala):
    """A sala informada precisa pertencer ao local informado."""
    outro_local = client.post(
        "/api/locais",
        json={"nome": "Filial Outro Local"},
        headers=auth_headers,
    ).json()
    payload = _reserva_payload(outro_local["id"], res_sala["id"], 14, 15)
    r = client.post("/api/reservas", json=payload, headers=auth_headers)
    assert r.status_code == 400


# ── RF-10: Choque de horários ─────────────────────────────────────────────────

def test_conflito_sobreposicao_total_retorna_409(client, auth_headers, res_local, res_sala):
    """
    RF-10: Reservar slot que está totalmente dentro de uma reserva existente
    deve retornar 409 com mensagem de conflito.
    """
    # Cria reserva base: 13:00–15:00
    base = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 13, 15),
        headers=auth_headers,
    )
    assert base.status_code == 201

    # Tenta criar 13:30–14:30 (dentro da base) → deve conflitar
    conflito = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 13, 14),
        headers=auth_headers,
    )
    assert conflito.status_code == 409
    body = conflito.json()
    assert "conflito" in body.get("error", "").lower() or "conflito" in body.get("detail", "").lower()


def test_conflito_sobreposicao_parcial_retorna_409(client, auth_headers, res_local, res_sala):
    """Reserva com início dentro e fim fora deve conflitar."""
    # Cria reserva base: 15:00–17:00
    client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 15, 17),
        headers=auth_headers,
    ).raise_for_status()

    # Tenta criar 16:00–18:00 (início dentro do slot existente) → 409
    r = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 16, 18),
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_sem_conflito_horario_adjacente_retorna_201(client, auth_headers, res_local, res_sala):
    """
    Reservas ADJACENTES (fim de uma == início da outra) NÃO são conflito:
    a condição de conflito é inicio_existente < novo_fim AND fim_existente > novo_inicio.
    Para adjacentes: fim_existente == novo_inicio → fim_existente > novo_inicio é False.
    """
    # Cria reserva: 17:00–18:00
    client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 17, 18),
        headers=auth_headers,
    ).raise_for_status()

    # Cria reserva adjacente: 18:00–19:00 → sem conflito
    r = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 18, 19),
        headers=auth_headers,
    )
    assert r.status_code == 201


def test_sem_conflito_sala_diferente_retorna_201(client, auth_headers, res_local):
    """Mesmo horário em salas diferentes não conflita."""
    outra_sala = client.post(
        "/api/salas",
        json={"nome": "Sala Paralela", "local_id": res_local["id"]},
        headers=auth_headers,
    ).json()

    # Cria reserva na sala original: 19:00–20:00 (pode já existir de outro teste)
    # Cria na sala diferente: mesmo horário → sem conflito
    r = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], outra_sala["id"], 19, 20),
        headers=auth_headers,
    )
    assert r.status_code == 201


# ── RF-08: Edição ─────────────────────────────────────────────────────────────

def test_update_reserva_retorna_200(client, auth_headers, res_local, res_sala):
    criada = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 20, 21),
        headers=auth_headers,
    ).json()

    r = client.put(
        f"/api/reservas/{criada['id']}",
        json={"responsavel": "Responsável Atualizado"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["responsavel"] == "Responsável Atualizado"


def test_update_reserva_nao_conflita_consigo_mesma(client, auth_headers, res_local, res_sala):
    """
    Ao editar uma reserva mantendo os mesmos horários, o sistema não deve
    reportar conflito com a própria reserva (ignore_reserva_id).
    """
    criada = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 21, 22),
        headers=auth_headers,
    ).json()

    r = client.put(
        f"/api/reservas/{criada['id']}",
        json={
            "inicio": _dt(21),
            "fim": _dt(22),
            "responsavel": "Mesmo Horário",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_update_reserva_inexistente_retorna_404(client, auth_headers):
    r = client.put(
        "/api/reservas/999999",
        json={"responsavel": "Ninguém"},
        headers=auth_headers,
    )
    assert r.status_code == 404


# ── RF-09: Exclusão individual ────────────────────────────────────────────────

def test_delete_reserva_retorna_204(client, auth_headers, res_local, res_sala):
    criada = client.post(
        "/api/reservas",
        json=_reserva_payload(res_local["id"], res_sala["id"], 22, 23),
        headers=auth_headers,
    ).json()

    r = client.delete(f"/api/reservas/{criada['id']}", headers=auth_headers)
    assert r.status_code == 204


def test_delete_reserva_inexistente_retorna_404(client, auth_headers):
    r = client.delete("/api/reservas/999999", headers=auth_headers)
    assert r.status_code == 404


# ── RF-11: Exclusão em lote (bônus) ──────────────────────────────────────────

def test_delete_em_lote_retorna_sucesso(client, auth_headers, res_local, res_sala):
    """RF-11 (bônus): exclui múltiplas reservas de uma vez."""
    ids = []
    for h in [2, 3]:  # Horas seguras no dia 2099-06-16 para não conflitar com outros testes
        inicio = datetime(2099, 6, 16, h, 0, tzinfo=timezone.utc)
        fim = datetime(2099, 6, 16, h + 1, 0, tzinfo=timezone.utc)
        payload = {
            "local_id": res_local["id"],
            "sala_id": res_sala["id"],
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "responsavel": "Lote Teste",
        }
        resp = client.post("/api/reservas", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        ids.append(resp.json()["id"])

    r = client.request(
        "DELETE",
        "/api/reservas/batch",
        json={"reserva_ids": ids},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["deleted_count"] == len(ids)
