FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances depuis la racine
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code du dossier backend dans /app/backend
COPY ./backend /app/backend

# On se place dans /app/backend pour préserver la résolution des imports locaux
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]