# Foodgram — сервис рецептов и покупок

**Foodgram** — это веб-приложение, где пользователи могут делиться рецептами, формировать список покупок, подписываться на других авторов и сохранять любимые блюда в избранное. Платформа удобна для ведения личной коллекции рецептов и планирования покупок.

---

## 🔧 Технологии проекта

- **Backend:** Python 3.10, Django, Django REST Framework  
- **Frontend:** React  
- **База данных:** PostgreSQL  
- **Веб-сервер:** Nginx  
- **Контейнеризация:** Docker, Docker Compose  
- **Документация:** ReDoc

---

## 📌 Возможности

- Регистрация и аутентификация через JWT
- Публикация и редактирование рецептов
- Добавление рецептов в избранное
- Подписка на других пользователей
- Фильтрация по тегам
- Автоматическое формирование списка покупок
- Экспорт списка продуктов

---

## 📚 Документация API

После запуска доступна по адресу:

```
/api/docs/redoc.html
```

---

## 🚀 Быстрый запуск без Docker

1. Клонируйте проект:

```bash
git clone https://github.com/yourname/cookbook.git
cd cookbook/backend
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

3. Примените миграции и запустите сервер:

```bash
python manage.py migrate
python manage.py runserver
```

---

## ⚙️ Развёртывание в Docker

1. Перейдите в директорию infra:

```bash
cd infra
```

2. Убедитесь, что переменные окружения указаны в `.env` или в `docker-compose.yml`:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=your_domain,localhost,127.0.0.1
```

3. Запустите сборку и контейнеры:

```bash
docker-compose up -d --build
```

4. Выполните миграции и настройку:

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic --no-input
```

5. Импортируйте базовые данные:

```bash
docker-compose exec backend python manage.py import_data
```

---

## 🧪 Тестирование

```bash
docker-compose exec backend pytest
```


