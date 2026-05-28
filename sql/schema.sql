-- ============================================================================
-- E-COMMERCE DATA WAREHOUSE SCHEMA
-- Star Schema with Fact and Dimension Tables
-- ============================================================================

-- Enable required extensions
-- CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- ============================================================================
-- STAGING TABLES (Raw data from sources)
-- ============================================================================

CREATE TABLE IF NOT EXISTS staging_orders (
    staging_order_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS staging_customers (
    staging_customer_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    zip_code VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS staging_products (
    staging_product_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL UNIQUE,
    title VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    review_count INT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'PENDING'
);

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Date Dimension (SCD Type 1)
CREATE TABLE IF NOT EXISTS dim_dates (
    date_id INT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Dimension (SCD Type 2 - Slowly Changing Dimension)
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    zip_code VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, start_date)
);

-- Product Dimension (SCD Type 1)
CREATE TABLE IF NOT EXISTS dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id INT NOT NULL UNIQUE,
    title VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    review_count INT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FACT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_orders (
    fact_order_key SERIAL PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    customer_key INT NOT NULL,
    product_key INT NOT NULL,
    date_key INT NOT NULL,
    quantity INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    order_status VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_customer FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    CONSTRAINT fk_product FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    CONSTRAINT fk_date FOREIGN KEY (date_key) REFERENCES dim_dates(date_id)
);

-- ============================================================================
-- INDEXES for Query Performance
-- ============================================================================

-- Fact table indexes
CREATE INDEX idx_fact_orders_customer_key ON fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product_key ON fact_orders(product_key);
CREATE INDEX idx_fact_orders_date_key ON fact_orders(date_key);
CREATE INDEX idx_fact_orders_created_at ON fact_orders(created_at);
CREATE INDEX idx_fact_orders_amount ON fact_orders(amount);

-- Dimension table indexes
CREATE INDEX idx_dim_customers_customer_id ON dim_customers(customer_id);
CREATE INDEX idx_dim_customers_is_current ON dim_customers(is_current);
CREATE INDEX idx_dim_products_product_id ON dim_products(product_id);
CREATE INDEX idx_dim_products_category ON dim_products(category);

-- Staging table indexes
CREATE INDEX idx_staging_orders_customer_id ON staging_orders(customer_id);
CREATE INDEX idx_staging_orders_product_id ON staging_orders(product_id);
CREATE INDEX idx_staging_customers_email ON staging_customers(email);
CREATE INDEX idx_staging_products_category ON staging_products(category);

-- ============================================================================
-- DATA QUALITY AUDIT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_quality_audit (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    check_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- PASS, FAIL, WARNING
    row_count INT,
    error_message TEXT,
    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id UUID DEFAULT uuid_generate_v4()
);

-- ============================================================================
-- METRICS/SUMMARY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_metrics (
    metric_date DATE PRIMARY KEY,
    total_orders INT DEFAULT 0,
    total_customers INT DEFAULT 0,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    avg_order_value DECIMAL(10, 2) DEFAULT 0,
    new_customers INT DEFAULT 0,
    top_category VARCHAR(100),
    pipeline_status VARCHAR(50) DEFAULT 'PENDING',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GRANTS (if using different users)
-- ============================================================================

-- Uncomment and modify as needed
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO etl_user;
-- GRANT INSERT, UPDATE, DELETE ON staging_orders, staging_customers, staging_products TO etl_user;
-- GRANT ALL PRIVILEGES ON fact_orders, dim_customers, dim_products, dim_dates TO etl_user;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE fact_orders IS 'Central fact table containing order transactions. Each row represents one order line item.';
COMMENT ON TABLE dim_customers IS 'Customer dimension with SCD Type 2 tracking. Multiple rows per customer for historical changes.';
COMMENT ON TABLE dim_products IS 'Product dimension with SCD Type 1. One row per product with latest information.';
COMMENT ON TABLE dim_dates IS 'Date dimension for time-series analysis. One row per day.';

COMMENT ON COLUMN fact_orders.customer_key IS 'Foreign key to dim_customers';
COMMENT ON COLUMN fact_orders.product_key IS 'Foreign key to dim_products';
COMMENT ON COLUMN fact_orders.date_key IS 'Foreign key to dim_dates';
COMMENT ON COLUMN dim_customers.is_current IS 'Flag indicating if this is the current version (Type 2 SCD)';
COMMENT ON COLUMN dim_customers.start_date IS 'Start date of this version (Type 2 SCD)';
COMMENT ON COLUMN dim_customers.end_date IS 'End date of this version (Type 2 SCD)';

-- ============================================================================
-- INITIAL DATE DIMENSION POPULATION
-- ============================================================================

-- Generate dates for next 2 years
INSERT INTO dim_dates (date_id, date, year, quarter, month, day, day_of_week, day_name, month_name, is_weekend, is_holiday)
SELECT 
    TO_CHAR(date_series, 'YYYYMMDD')::INT as date_id,
    date_series::DATE as date,
    EXTRACT(YEAR FROM date_series)::INT as year,
    CEIL(EXTRACT(MONTH FROM date_series)::INT / 3)::INT as quarter,
    EXTRACT(MONTH FROM date_series)::INT as month,
    EXTRACT(DAY FROM date_series)::INT as day,
    EXTRACT(DOW FROM date_series)::INT as day_of_week,
    TO_CHAR(date_series, 'Day') as day_name,
    TO_CHAR(date_series, 'Month') as month_name,
    EXTRACT(DOW FROM date_series) IN (0, 6) as is_weekend,
    FALSE as is_holiday
FROM (
    SELECT CURRENT_DATE + INTERVAL '1 day' * i as date_series
    FROM GENERATE_SERIES(0, 730) i
) date_range
ON CONFLICT (date) DO NOTHING;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
