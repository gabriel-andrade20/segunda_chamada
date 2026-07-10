from fastapi import FastAPI
from app.routes import pedidos

app = FastAPI(
    title="API de Pedidos",
    description="Gerenciamento completo do ciclo de vida de pedidos",
    version="1.0.0",
)

app.include_router(pedidos.router, prefix="/pedidos", tags=["pedidos"])
