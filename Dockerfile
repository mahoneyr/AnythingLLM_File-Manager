# Use Python slim image
FROM python:3.12-slim as python-base

# Python env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    telnet \
    # deps for installing poetry
    curl \
    # deps for building python deps
    build-essential

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3 -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-dev

# `production` image used for runtime
FROM python-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# Use Python slim image
FROM python:3.12-slim

# Create directory for the app user
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .
COPY .env .env

# Create start.sh with proper line endings
RUN echo '#!/bin/bash\n\
echo "Starting Django server..."\n\
echo "Running migrations..."\n\
python manage.py migrate\n\
echo "Migrations completed"\n\
echo "Starting Django server..."\n\
python manage.py runserver 0.0.0.0:${PORT:-8010}' > start.sh && \
    chmod +x start.sh

# Create required directories
RUN mkdir -p /app/storage/media/charts/uploads \
    && mkdir -p /app/static \
    && mkdir -p /app/database \
    && chmod -R 777 /app/storage \
    && chmod -R 777 /app/static \
    && chmod -R 777 /app/database

# Create and switch to non-root user
RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app

USER django


# Command to run both qcluster and the server
CMD ["bash", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py qcluster & gunicorn main.wsgi:application --bind 0.0.0.0:${PORT:-8010}"]
