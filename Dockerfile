# Cambiamos a 3.6 para evitar el RuntimeError de Django 1.10
FROM python:3.6-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# SQLite no necesita grandes librerías de sistema, simplificamos:
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . /app/

# Exponemos el puerto de Django
EXPOSE 8000

# Comando para ejecutar migraciones y subir el server automáticamente
CMD ["sh", "/app/entrypoint.sh"]