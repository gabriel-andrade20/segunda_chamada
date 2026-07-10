from fastapi import APIRouter, HTTPException, Query
from app.models import PedidoEntrada, Pedido, AtualizarStatus, StatusPedido, TRANSICOES_VALIDAS
from app.database import colecao_pedidos
from app.mensageria import notificar_criacao, notificar_atualizacao, notificar_cancelamento, notificar_exclusao
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()


def montar_pedido(dados: PedidoEntrada) -> dict:
    valor_total = sum(p.quantidade * p.valor_unitario for p in dados.produtos)
    agora = datetime.utcnow()
    return {
        "id": str(uuid.uuid4()),
        "nome_cliente": dados.nome_cliente,
        "email_cliente": dados.email_cliente,
        "produtos": [p.model_dump() for p in dados.produtos],
        "valor_total": valor_total,
        "status": StatusPedido.PENDENTE,
        "criado_em": agora,
        "atualizado_em": agora,
        "ativo": True,
    }


@router.post(
    "/",
    response_model=Pedido,
    status_code=201,
    summary="Cadastrar pedido",
    responses={201: {"description": "Pedido criado com sucesso"}},
)
def criar_pedido(dados: PedidoEntrada):
    pedido = montar_pedido(dados)
    colecao_pedidos.insert_one({**pedido})
    notificar_criacao(pedido)
    return pedido


@router.get(
    "/",
    response_model=List[Pedido],
    summary="Listar pedidos",
    responses={200: {"description": "Lista de pedidos ativos"}},
)
def listar_pedidos(status: Optional[StatusPedido] = Query(default=None)):
    filtro = {"ativo": True}
    if status:
        filtro["status"] = status
    pedidos = list(colecao_pedidos.find(filtro, {"_id": 0}))
    return pedidos


@router.get(
    "/{pedido_id}",
    response_model=Pedido,
    summary="Buscar pedido por ID",
    responses={404: {"description": "Pedido não encontrado"}},
)
def buscar_pedido(pedido_id: str):
    pedido = colecao_pedidos.find_one({"id": pedido_id, "ativo": True}, {"_id": 0})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


@router.patch(
    "/{pedido_id}/status",
    response_model=Pedido,
    summary="Atualizar status do pedido",
    responses={
        400: {"description": "Transição de status inválida"},
        404: {"description": "Pedido não encontrado"},
    },
)
def atualizar_status(pedido_id: str, body: AtualizarStatus):
    pedido = colecao_pedidos.find_one({"id": pedido_id, "ativo": True}, {"_id": 0})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    status_atual = StatusPedido(pedido["status"])
    novo_status = body.status

    if novo_status not in TRANSICOES_VALIDAS[status_atual]:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível mudar de {status_atual} para {novo_status}",
        )

    agora = datetime.utcnow()
    colecao_pedidos.update_one(
        {"id": pedido_id},
        {"$set": {"status": novo_status, "atualizado_em": agora}},
    )
    pedido["status"] = novo_status
    pedido["atualizado_em"] = agora

    notificar_atualizacao(pedido)
    return pedido


@router.patch(
    "/{pedido_id}/cancelar",
    response_model=Pedido,
    summary="Cancelar pedido",
    responses={
        400: {"description": "Pedido não pode ser cancelado"},
        404: {"description": "Pedido não encontrado"},
    },
)
def cancelar_pedido(pedido_id: str):
    pedido = colecao_pedidos.find_one({"id": pedido_id, "ativo": True}, {"_id": 0})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    status_atual = StatusPedido(pedido["status"])
    if StatusPedido.CANCELADO not in TRANSICOES_VALIDAS[status_atual]:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido com status {status_atual} não pode ser cancelado",
        )

    agora = datetime.utcnow()
    colecao_pedidos.update_one(
        {"id": pedido_id},
        {"$set": {"status": StatusPedido.CANCELADO, "atualizado_em": agora}},
    )
    pedido["status"] = StatusPedido.CANCELADO
    pedido["atualizado_em"] = agora

    notificar_cancelamento(pedido)
    return pedido


@router.delete(
    "/{pedido_id}",
    summary="Excluir pedido (soft delete)",
    responses={
        200: {"description": "Pedido excluído com sucesso"},
        404: {"description": "Pedido não encontrado"},
    },
)
def excluir_pedido(pedido_id: str):
    pedido = colecao_pedidos.find_one({"id": pedido_id, "ativo": True}, {"_id": 0})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    agora = datetime.utcnow()
    colecao_pedidos.update_one(
        {"id": pedido_id},
        {"$set": {"ativo": False, "atualizado_em": agora}},
    )
    pedido["ativo"] = False
    pedido["atualizado_em"] = agora

    notificar_exclusao(pedido)
    return {"mensagem": "Pedido excluído com sucesso"}
