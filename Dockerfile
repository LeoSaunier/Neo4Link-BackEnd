FROM python:3.11-slim

WORKDIR /app

# Copie des dépendances depuis la racine
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du contenu du dossier backend/ directement dans /app
COPY ./backend /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]