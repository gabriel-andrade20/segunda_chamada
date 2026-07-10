import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PEDIDO_EXEMPLO = {
    "id": "pedido-001",
    "nome_cliente": "Ana Lima",
    "email_cliente": "ana@email.com",
    "produtos": [{"nome": "Notebook", "quantidade": 1, "valor_unitario": 3500.0}],
    "valor_total": 3500.0,
    "status": "PENDENTE",
    "criado_em": datetime.utcnow(),
    "atualizado_em": datetime.utcnow(),
    "ativo": True,
}

PEDIDO_PAGO = {**PEDIDO_EXEMPLO, "id": "pedido-002", "status": "PAGO"}
PEDIDO_ENVIADO = {**PEDIDO_EXEMPLO, "id": "pedido-003", "status": "ENVIADO"}
PEDIDO_INATIVO = {**PEDIDO_EXEMPLO, "id": "pedido-004", "ativo": False}

ENTRADA_VALIDA = {
    "nome_cliente": "Ana Lima",
    "email_cliente": "ana@email.com",
    "produtos": [{"nome": "Notebook", "quantidade": 1, "valor_unitario": 3500.0}],
}


@pytest.fixture
def client():
    mock_col = MagicMock()
    mock_col.find.return_value = [PEDIDO_EXEMPLO]
    mock_col.find_one.return_value = PEDIDO_EXEMPLO

    import app.database as db
    db.colecao_pedidos = mock_col

    from app.main import app
    with patch("app.routes.pedidos.colecao_pedidos", mock_col):
        with patch("app.routes.pedidos.notificar_criacao"):
            with patch("app.routes.pedidos.notificar_atualizacao"):
                with patch("app.routes.pedidos.notificar_cancelamento"):
                    with patch("app.routes.pedidos.notificar_exclusao"):
                        yield TestClient(app), mock_col


def test_cadastro_valido(client):
    c, _ = client
    resp = c.post("/pedidos/", json=ENTRADA_VALIDA)
    assert resp.status_code == 201
    body = resp.json()
    assert body["nome_cliente"] == "Ana Lima"
    assert body["status"] == "PENDENTE"
    assert "id" in body


def test_cadastro_sem_produtos(client):
    c, _ = client
    resp = c.post("/pedidos/", json={**ENTRADA_VALIDA, "produtos": []})
    assert resp.status_code == 422


def test_cadastro_email_invalido(client):
    c, _ = client
    resp = c.post("/pedidos/", json={**ENTRADA_VALIDA, "email_cliente": "nao-e-email"})
    assert resp.status_code == 422


def test_cadastro_quantidade_zero(client):
    c, _ = client
    entrada = {**ENTRADA_VALIDA, "produtos": [{"nome": "X", "quantidade": 0, "valor_unitario": 10.0}]}
    resp = c.post("/pedidos/", json=entrada)
    assert resp.status_code == 422


def test_calculo_valor_total(client):
    c, _ = client
    entrada = {
        "nome_cliente": "Carlos",
        "email_cliente": "carlos@email.com",
        "produtos": [
            {"nome": "Produto A", "quantidade": 2, "valor_unitario": 50.0},
            {"nome": "Produto B", "quantidade": 3, "valor_unitario": 100.0},
        ],
    }
    resp = c.post("/pedidos/", json=entrada)
    assert resp.status_code == 201
    assert resp.json()["valor_total"] == 400.0


def test_listar_pedidos(client):
    c, _ = client
    resp = c.get("/pedidos/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_filtrar_por_status(client):
    c, mock_col = client
    mock_col.find.return_value = [PEDIDO_EXEMPLO]
    resp = c.get("/pedidos/?status=PENDENTE")
    assert resp.status_code == 200


def test_buscar_por_id(client):
    c, _ = client
    resp = c.get("/pedidos/pedido-001")
    assert resp.status_code == 200
    assert resp.json()["id"] == "pedido-001"


def test_buscar_id_inexistente(client):
    c, mock_col = client
    mock_col.find_one.return_value = None
    resp = c.get("/pedidos/nao-existe")
    assert resp.status_code == 404


def test_atualizacao_valida(client):
    c, mock_col = client
    mock_col.find_one.return_value = PEDIDO_EXEMPLO
    resp = c.patch("/pedidos/pedido-001/status", json={"status": "PAGO"})
    assert resp.status_code == 200


def test_atualizacao_invalida(client):
    c, mock_col = client
    mock_col.find_one.return_value = PEDIDO_EXEMPLO
    resp = c.patch("/pedidos/pedido-001/status", json={"status": "ENTREGUE"})
    assert resp.status_code == 400


def test_cancelar_pedido_pendente(client):
    c, mock_col = client
    mock_col.find_one.return_value = PEDIDO_EXEMPLO
    resp = c.patch("/pedidos/pedido-001/cancelar")
    assert resp.status_code == 200


def test_cancelar_pedido_enviado(client):
    c, mock_col = client
    mock_col.find_one.return_value = PEDIDO_ENVIADO
    resp = c.patch("/pedidos/pedido-003/cancelar")
    assert resp.status_code == 400


def test_exclusao_logica(client):
    c, mock_col = client
    mock_col.find_one.return_value = PEDIDO_EXEMPLO
    resp = c.delete("/pedidos/pedido-001")
    assert resp.status_code == 200
    mock_col.update_one.assert_called_once()
    args = mock_col.update_one.call_args[0]
    assert args[1]["$set"]["ativo"] is False


def test_pedido_inativo_nao_retorna(client):
    c, mock_col = client
    mock_col.find_one.return_value = None
    resp = c.get("/pedidos/pedido-004")
    assert resp.status_code == 404
