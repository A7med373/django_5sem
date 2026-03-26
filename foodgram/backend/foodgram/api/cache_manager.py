import os
import redis
import json

class CacheManager:
    def __init__(self):
        # ТЗ: Получает env
        host = os.environ.get('REDIS_HOST', '127.0.0.1')
        port = int(os.environ.get('REDIS_PORT', 6379))
        password = os.environ.get('REDIS_PASSWORD', None)

        # ТЗ: Подключается к redis
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True # Чтобы данные возвращались как строки, а не байты
        )

    # ТЗ: Умеет записывать данные в кэш + работает с TTL
    def set(self, key, value, ttl=3600):
        # Превращаем словари/списки в JSON-строку для хранения в Redis
        json_value = json.dumps(value)
        self.client.set(key, json_value, ex=ttl)

    # ТЗ: Умеет читать данные из кэша
    def get(self, key):
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    # ТЗ: Умеет проверять наличие ключа в кэше
    def exists(self, key):
        return self.client.exists(key) > 0