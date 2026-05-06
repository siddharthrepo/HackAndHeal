FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

# Daphne (ASGI) so Django Channels websockets work.
CMD ["sh", "-c", "python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 chikitsa360.asgi:application"]
