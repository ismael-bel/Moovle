# 1. On part d'une version légère de Python
FROM python:3.11-slim

# 2. On crée un dossier de travail dans le conteneur
WORKDIR /app

# 3. On copie les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. On copie tout ton code
COPY . .

# 5. Variable d'environnement pour que Python s'affiche direct dans les logs
ENV PYTHONUNBUFFERED=1

# 6. Streamlit tourne sur le port 8080 par défaut dans Cloud Run
EXPOSE 8080

# 7. La commande de lancement
CMD streamlit run app.py --server.port 8080 --server.address 0.0.0.0