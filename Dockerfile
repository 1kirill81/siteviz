FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Сначала копируем зависимости для быстрой сборки кэша
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта
COPY . .

# Команда для запуска приложения внутри Docker
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]