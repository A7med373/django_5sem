import pika
import hvac
import json
import sys
import os
import requests

from foodgram.api.cache_manager import CacheManager

# Инициализируем наш кэш
cache = CacheManager()

# --- НАСТРОЙКИ VAULT ---
VAULT_URL = "http://127.0.0.1:8200"
VAULT_TOKEN = "hvs.6Gu0OMLN5S9UDnnBS3Bo6bqs"  # Твой токен


def get_rabbitmq_creds_from_vault():
    client = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN)
    response = client.secrets.kv.v2.read_secret_version(mount_point='kv', path='foodgram/rabbitmq')
    creds = response['data']['data']
    return creds['rabbitmq-user'], creds['rabbitmq-password']


def get_api_key_from_vault(api_alias):
    """ТЗ: Получает чувствительные данные для задачи из vault"""
    client = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN)
    response = client.secrets.kv.v2.read_secret_version(mount_point='kv', path='foodgram/external_apis')
    keys = response['data']['data']

    # Сопоставляем alias из сообщения с ключом в Vault
    if api_alias == "spoonacular_api":
        return keys.get('spoonacular_key')
    elif api_alias == "translation_api":
        return keys.get('yandex_ai')
    return None


def process_nutrition_task(params, api_key):
    """Функция обработки задачи Spoonacular (поиск калорий) с кэшированием"""
    query = params.get('query', 'apple')

    # Создаем уникальный ключ для кэша на основе запроса
    cache_key = f"api_spoonacular_{query}"

    # ТЗ: Если есть данные в кэше - отдаем из кэша
    if cache.exists(cache_key):
        print(f"[CACHE HIT] Отдаем данные для '{query}' из Redis!")
        return cache.get(cache_key)

    # ТЗ: Если нет - вычисляем (делаем запрос)
    print(f"[CACHE MISS] Делаем РЕАЛЬНЫЙ запрос к Spoonacular API для: {query}")
    url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()

        # ТЗ: ...и складываем в кэш (например, на 1 час = 3600 сек)
        cache.set(cache_key, data, ttl=3600)
    except Exception as e:
        data = {"error": str(e)}

    # ТЗ: ...возвращаем вычисленное
    return data

def callback(ch, method, properties, body):
    """ТЗ: Создает callback. Исходя из данных решает какую функцию выполнять"""
    message = json.loads(body)
    print(f"\n[x] Получено сообщение: {message}")

    api_alias = message.get("api_alias")
    params = message.get("params", {})

    # 1. Достаем ключ из Vault
    api_key = get_api_key_from_vault(api_alias)

    if not api_key:
        print(f"[!] Ключ для {api_alias} не найден в Vault!")
    else:
        # 2. Решаем, какую функцию выполнять
        result_data = {}
        if api_alias == "spoonacular_api":
            result_data = process_nutrition_task(params, api_key)
        elif api_alias == "translation_api":
            # Здесь могла бы быть логика Yandex AI
            print("[*] Выполняем задачу перевода через Yandex AI...")
            result_data = {"status": "translated mock", "params": params}
        else:
            print("[!] Неизвестный API alias")

        # 3. Сохраняем в JSON-файл (как требует ТЗ)
        filename = f"result_{api_alias}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=4)
        print(f"[*] Результат сохранен в файл: {filename}")

    # 4. Отправляем подтверждение (acknowledgement), что задача выполнена
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("[x] Задача успешно обработана и удалена из очереди (ACK отправлен).")


def start_consumer(queue_name):
    # ТЗ: Получает данные для подключения к брокеру из vault
    rmq_user, rmq_password = get_rabbitmq_creds_from_vault()

    # Подключаемся к брокеру
    credentials = pika.PlainCredentials(rmq_user, rmq_password)
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    exchange_name = 'foodgram_tasks'

    # Убеждаемся, что обменник существует
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)

    # ТЗ: Создает очередь для конкретной задачи (durable=True)
    channel.queue_declare(queue=queue_name, durable=True)

    # ТЗ: Связывает exchange и очередь (биндинг)
    # Предполагаем, что routing_key совпадает с именем очереди без суффикса '_queue'
    routing_key = queue_name.replace('_queue', '')
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

    # ТЗ: Связывает callback и обработку сообщений
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print(f" [*] Ожидание сообщений в очереди '{queue_name}'. Для выхода нажмите CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    # ТЗ: Получает из CLI информацию о том, какую очередь слушает
    if len(sys.argv) < 2:
        print("Использование: python consumer.py <имя_очереди>")
        print("Пример: python consumer.py nutrition_queue")
        sys.exit(1)

    target_queue = sys.argv[1]
    start_consumer(target_queue)