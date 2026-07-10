# Pedidos API

Esse projeto faz parte da migração de uma arquitetura monolítica para microsserviços. A ideia aqui é cuidar do ciclo de vida completo dos pedidos — desde a criação até a entrega ou cancelamento — propagando cada evento de forma assíncrona para outros sistemas da empresa.

## Como rodar

Com o Docker instalado, sobe tudo com um único comando:

```bash
docker compose up --build
```

Serviços disponíveis:

| Serviço         | URL                          |
|-----------------|------------------------------|
| API             | http://localhost:8000        |
| Documentação    | http://localhost:8000/docs   |
| Mongo Express   | http://localhost:8081        |
| RabbitMQ        | http://localhost:15672       |

## Endpoints

| Método | Rota                        | Descrição                  |
|--------|-----------------------------|----------------------------|
| POST   | /pedidos/                   | Criar pedido               |
| GET    | /pedidos/                   | Listar pedidos             |
| GET    | /pedidos/{id}               | Buscar por ID              |
| GET    | /pedidos/?status=PAGO       | Filtrar por status         |
| PATCH  | /pedidos/{id}/status        | Atualizar status           |
| PATCH  | /pedidos/{id}/cancelar      | Cancelar pedido            |
| DELETE | /pedidos/{id}               | Excluir (soft delete)      |

## Status e transições

```
PENDENTE → PAGO → EM_SEPARACAO → ENVIADO → ENTREGUE
PENDENTE → CANCELADO
PAGO → CANCELADO
```

## Testes

```bash
pip install -r requirements.txt
pytest tests/
```

## Stack

- **FastAPI** — framework da API
- **MongoDB** — persistência dos pedidos
- **Mongo Express** — interface visual do banco
- **RabbitMQ** — filas de mensagens
- **Kafka + Zookeeper** — streaming de eventos
- **Docker** — tudo containerizado
