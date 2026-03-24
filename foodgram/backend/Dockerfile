# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

RUN python -m pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY foodgram/ .
COPY ../data /app/data

# Запускаем приложение
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]