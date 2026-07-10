from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from enum import Enum
from datetime import datetime


class StatusPedido(str, Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    EM_SEPARACAO = "EM_SEPARACAO"
    ENVIADO = "ENVIADO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


TRANSICOES_VALIDAS = {
    StatusPedido.PENDENTE: [StatusPedido.PAGO, StatusPedido.CANCELADO],
    StatusPedido.PAGO: [StatusPedido.EM_SEPARACAO, StatusPedido.CANCELADO],
    StatusPedido.EM_SEPARACAO: [StatusPedido.ENVIADO],
    StatusPedido.ENVIADO: [StatusPedido.ENTREGUE],
    StatusPedido.ENTREGUE: [],
    StatusPedido.CANCELADO: [],
}


class Produto(BaseModel):
    nome: str
    quantidade: int
    valor_unitario: float

    @field_validator("quantidade")
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v

    @field_validator("valor_unitario")
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("Valor unitário deve ser maior que zero")
        return v


class PedidoEntrada(BaseModel):
    nome_cliente: str
    email_cliente: EmailStr
    produtos: List[Produto]

    @field_validator("produtos")
    def pelo_menos_um_produto(cls, v):
        if not v:
            raise ValueError("O pedido deve ter pelo menos um produto")
        return v


class AtualizarStatus(BaseModel):
    status: StatusPedido


class Pedido(BaseModel):
    id: str
    nome_cliente: str
    email_cliente: str
    produtos: List[Produto]
    valor_total: float
    status: StatusPedido
    criado_em: datetime
    atualizado_em: datetime
    ativo: bool = True
