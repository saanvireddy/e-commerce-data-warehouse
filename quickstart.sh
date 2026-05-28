#!/bin/bash

# Quick Start Script for E-Commerce Data Warehouse

set -e  # Exit on error

echo "=========================================="
echo "E-Commerce Data Warehouse Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo ""
echo "[1/4] Creating .env file from .env.example..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file. Please update values if needed."
else
    echo "✓ .env file already exists"
fi

echo ""
echo "[2/4] Creating logs directory..."
mkdir -p logs
echo "✓ Logs directory ready"

echo ""
echo "[3/4] Building Docker images..."
docker-compose build
echo "✓ Docker images built successfully"

echo ""
echo "[4/4] Starting services..."
docker-compose up -d
echo "✓ Services started"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Airflow Web UI: http://localhost:8080"
echo "   Username: airflow"
echo "   Password: airflow"
echo ""
echo "📦 PostgreSQL: localhost:5432"
echo "   User: postgres"
echo "   Password: postgres"
echo "   Database: ecommerce_warehouse"
echo ""
echo "🚀 To run the ETL pipeline:"
echo "   docker-compose exec airflow-webserver bash"
echo "   python /app/src/main.py --mode full"
echo ""
echo "📖 For detailed instructions, see README.md"
echo ""
