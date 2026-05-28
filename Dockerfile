FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    AIRFLOW_HOME=/airflow

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Create airflow directory
RUN mkdir -p /airflow/dags /airflow/logs /airflow/plugins

# Copy application code
COPY src/ /app/src/
COPY airflow/ /airflow/

# Set permissions
RUN chmod -R 755 /app /airflow

# Expose port for Airflow webserver
EXPOSE 8080

# Default command
CMD ["/bin/bash"]
