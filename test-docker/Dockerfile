# Image de base Python
FROM python:3.11-slim

# Dossier de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .

# Port exposé
EXPOSE 5000

# Commande de démarrage
CMD ["python", "app.py"]
