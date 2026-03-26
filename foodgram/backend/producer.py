import pika
import hvac
import json
import os

# --- 1. НАСТРОЙКИ VAULT ---
VAULT_URL = "http://127.0.0.1:8200"
VAULT_TOKEN = "hvs.6Gu0OMLN5S9UDnnBS3Bo6bqs"


def get_rabbitmq_creds_from_vault():
    print("Подключаемся к Vault...")
    client = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN)

    response = client.secrets.kv.v2.read_secret_version(
        mount_point='kv',
        path='foodgram/rabbitmq',
        raise_on_deleted_version=True
    )
    creds = response['data']['data']
    return creds['rabbitmq-user'], creds['rabbitmq-password']


def send_task_to_rabbitmq():
    # Получаем логин и пароль из Vault
    rmq_user, rmq_password = get_rabbitmq_creds_from_vault()

    # --- 2. ПОДКЛЮЧЕНИЕ К RABBITMQ ---
    print("Подключаемся к RabbitMQ...")
    credentials = pika.PlainCredentials(rmq_user, rmq_password)
    # Используем localhost, так как у нас работает minikube tunnel
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # --- 3. СОЗДАНИЕ EXCHANGE ---
    # ТЗ: Создает exchange, Тип - direct, Exchange должен быть durable
    exchange_name = 'foodgram_tasks'
    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type='direct',
        durable=True
    )

    # --- 4. ФОРМИРОВАНИЕ И ОТПРАВКА СООБЩЕНИЯ ---
    # ТЗ: В сообщении должны быть alias API и параметры запроса
    # Давай отправим задачу на получение калорийности томата
    task_message = {
        "api_alias": "spoonacular_api",
        "params": {
            "query": "tomato"
        }
    }

    # ТЗ: Сообщение должно быть durable (delivery_mode=2)
    properties = pika.BasicProperties(
        delivery_mode=2,  # Делает сообщение персистентным (сохраняется на диск)
    )

    # Отправляем сообщение
    # routing_key 'nutrition' определяет, в какую очередь попадет сообщение
    channel.basic_publish(
        exchange=exchange_name,
        routing_key='nutrition',
        body=json.dumps(task_message),
        properties=properties
    )

    print(f" [x] Отправлена задача: {task_message}")
    connection.close()


if __name__ == "__main__":
    send_task_to_rabbitmq()
