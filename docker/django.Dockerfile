FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app

USER appuser