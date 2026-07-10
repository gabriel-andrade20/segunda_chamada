import pika
import json
import os
from kafka import KafkaProducer
from datetime import datetime

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")


def publicar_rabbitmq(fila: str, mensagem: dict):
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=fila, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=fila,
            body=json.dumps(mensagem, default=str),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception:
        pass


def publicar_kafka(topico: str, tipo_evento: str, payload: dict):
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        evento = {
            "tipo": tipo_evento,
            "timestamp": datetime.utcnow().isoformat(),
            "dados": payload,
        }
        producer.send(topico, value=evento)
        producer.flush()
        producer.close()
    except Exception:
        pass


def notificar_criacao(pedido: dict):
    mensagem_rabbit = {
        "id": pedido["id"],
        "cliente": pedido["nome_cliente"],
        "valor_total": pedido["valor_total"],
        "status": pedido["status"],
    }
    publicar_rabbitmq("pedidos_criados", mensagem_rabbit)
    publicar_kafka("pedidos-eventos", "PEDIDO_CRIADO", pedido)


def notificar_atualizacao(pedido: dict):
    mensagem_rabbit = {
        "id": pedido["id"],
        "cliente": pedido["nome_cliente"],
        "valor_total": pedido["valor_total"],
        "status": pedido["status"],
    }
    publicar_rabbitmq("pedidos_atualizados", mensagem_rabbit)
    publicar_kafka("pedidos-eventos", "PEDIDO_ATUALIZADO", pedido)


def notificar_cancelamento(pedido: dict):
    mensagem_rabbit = {
        "id": pedido["id"],
        "cliente": pedido["nome_cliente"],
        "valor_total": pedido["valor_total"],
        "status": pedido["status"],
    }
    publicar_rabbitmq("pedidos_cancelados", mensagem_rabbit)
    publicar_kafka("pedidos-eventos", "PEDIDO_CANCELADO", pedido)


def notificar_exclusao(pedido: dict):
    mensagem_rabbit = {
        "id": pedido["id"],
        "cliente": pedido["nome_cliente"],
        "valor_total": pedido["valor_total"],
        "status": pedido["status"],
    }
    publicar_rabbitmq("pedidos_excluidos", mensagem_rabbit)
    publicar_kafka("pedidos-eventos", "PEDIDO_EXCLUIDO", pedido)
