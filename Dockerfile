FROM python:3.12-slim

WORKDIR /app

# НЕОБХІДНІ СИСТЕМНІ ЗАЛЕЖНОСТІ
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаємо Flask як модуль
CMD ["python", "-m", "app.app"]
