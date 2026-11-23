# Image officielle Python légère (Debian slim)
FROM python:3.11-slim

# Empêche Python d'écrire des fichiers .pyc et force l'affichage immédiat des logs dans Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie et installation des dépendances en premier (optimise le cache des couches Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du reste du code source de l'application
COPY . .

# Exposition du port de l'API
EXPOSE 8000

# Démarrage du serveur Uvicorn en mode production/conteneur
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]