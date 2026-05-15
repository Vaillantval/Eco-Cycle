FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Dépendances système (PostgreSQL, Pillow)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Code source
COPY . /app/

# Collecte des fichiers statiques au build (WhiteNoise)
# Les variables sans valeur réelle sont acceptées ici — collectstatic ne touche pas la DB ni les médias
RUN python manage.py collectstatic --noinput

# Railway injecte $PORT dynamiquement — EXPOSE est indicatif
EXPOSE 8080
