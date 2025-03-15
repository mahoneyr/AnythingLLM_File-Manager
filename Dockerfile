# Use Python slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8010

# Create directory for the app user
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/

# Copy requirements first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .


# Create required directories and set permissions
RUN mkdir -p /app/storage/media/charts/uploads \
    && mkdir -p /app/static \
    && mkdir -p /app/database

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Running migrations..."\n\
python manage.py makemigrations\n\
python manage.py migrate\n\
echo "Migrations completed"\n\
echo "Starting Django Q Cluster..."\n\
python manage.py qcluster &\n\
Q_PID=$!\n\
echo "Starting Django server..."\n\
python manage.py runserver 0.0.0.0:${PORT} &\n\
DJANGO_PID=$!\n\
trap "kill $Q_PID $DJANGO_PID" SIGTERM SIGINT\n\
wait $Q_PID $DJANGO_PID' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Create and switch to non-root user
RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app \
    && chmod -R 777 /app/storage \
    && chmod -R 777 /app/static \
    && chmod -R 777 /app/database

USER django

# Command to run the entrypoint script
CMD ["/app/entrypoint.sh"]
