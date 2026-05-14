"""
Testes do endpoint de health check.
Verifica que a API responde sem autenticação e retorna o status esperado.
"""


def test_health_returns_ok(client):
    r = client.get("/api/health")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "banana-reservas-api"


def test_health_does_not_require_auth(client):
    """Health check deve ser acessível sem token JWT."""
    r = client.get("/api/health")
    assert r.status_code == 200
