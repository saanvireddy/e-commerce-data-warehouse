"""
Configuration management for E-Commerce Data Warehouse ETL pipeline.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_CONFIG: Dict[str, Any] = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ecommerce_warehouse'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
}

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_CONFIG: Dict[str, Any] = {
    'base_url': os.getenv('API_BASE_URL', 'https://fakestoreapi.com'),
    'timeout': int(os.getenv('API_TIMEOUT', 30)),
    'retries': int(os.getenv('API_RETRIES', 3)),
    'endpoints': {
        'products': '/products',
        'carts': '/carts',
        'users': '/users',
    }
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_CONFIG: Dict[str, Any] = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'logs/etl.log',
}

# ============================================================================
# ETL CONFIGURATION
# ============================================================================

ETL_CONFIG: Dict[str, Any] = {
    'batch_size': int(os.getenv('BATCH_SIZE', 1000)),
    'chunk_size': int(os.getenv('CHUNK_SIZE', 5000)),
    'staging_tables': [
        'staging_orders',
        'staging_customers',
        'staging_products',
    ],
    'fact_tables': [
        'fact_orders',
    ],
    'dimension_tables': [
        'dim_customers',
        'dim_products',
        'dim_dates',
    ],
}

# ============================================================================
# DATA QUALITY CONFIGURATION
# ============================================================================

DATA_QUALITY_CONFIG: Dict[str, Any] = {
    'null_checks': {
        'staging_orders': ['order_id', 'customer_id', 'product_id', 'amount'],
        'staging_customers': ['customer_id', 'email'],
        'staging_products': ['product_id', 'title', 'price'],
    },
    'range_checks': {
        'staging_orders': {
            'quantity': (1, 1000),
            'amount': (0, 100000),
        },
        'staging_products': {
            'price': (0, 10000),
            'rating': (0, 5),
        },
    },
    'unique_checks': {
        'staging_orders': ['order_id'],
        'staging_customers': ['customer_id'],
        'staging_products': ['product_id'],
    },
}

# ============================================================================
# SCHEDULE CONFIGURATION
# ============================================================================

SCHEDULE_CONFIG: Dict[str, Any] = {
    'daily_run_time': os.getenv('DAILY_RUN_TIME', '02:00'),
    'timezone': os.getenv('TIMEZONE', 'UTC'),
    'alerting_email': os.getenv('ALERT_EMAIL', 'admin@example.com'),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db_connection_string() -> str:
    """Generate PostgreSQL connection string."""
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

def get_api_endpoint(endpoint_name: str) -> str:
    """Get full API endpoint URL."""
    base_url = API_CONFIG['base_url'].rstrip('/')
    endpoint = API_CONFIG['endpoints'].get(endpoint_name, '')
    return f"{base_url}{endpoint}"

def log_config() -> None:
    """Log configuration for debugging."""
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info(f"API Base URL: {API_CONFIG['base_url']}")
    logger.info(f"Log Level: {LOG_CONFIG['level']}")
    logger.info(f"ETL Batch Size: {ETL_CONFIG['batch_size']}")

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> bool:
    """Validate configuration is complete."""
    required_fields = [
        ('DB_CONFIG', DB_CONFIG.get('host')),
        ('API_CONFIG', API_CONFIG.get('base_url')),
    ]
    
    for config_name, value in required_fields:
        if not value:
            logger.error(f"Missing configuration: {config_name}")
            return False
    
    logger.info("Configuration validation passed")
    return True

if __name__ == '__main__':
    # Test configuration
    import logging
    logging.basicConfig(level=logging.INFO)
    
    validate_config()
    log_config()
    print(f"DB Connection String: {get_db_connection_string()}")
    print(f"Products Endpoint: {get_api_endpoint('products')}")
