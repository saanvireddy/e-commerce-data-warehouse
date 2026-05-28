"""
Data loading module for loading data into PostgreSQL warehouse.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import logging
from typing import Dict, Tuple
from datetime import datetime
from config import DB_CONFIG

logger = logging.getLogger(__name__)

class DataLoader:
    """Load transformed data into PostgreSQL warehouse."""
    
    def __init__(self, db_config: Dict = None):
        self.db_config = db_config or DB_CONFIG
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info(f"Connected to database: {self.db_config['database']}")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def truncate_staging_tables(self):
        """Clear staging tables before loading."""
        try:
            cursor = self.connection.cursor()
            
            staging_tables = [
                'staging_orders',
                'staging_customers',
                'staging_products',
            ]
            
            for table in staging_tables:
                cursor.execute(f"TRUNCATE TABLE {table}")
                logger.info(f"Truncated table: {table}")
            
            self.connection.commit()
        
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Error truncating tables: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def load_to_staging(self, data: Dict[str, pd.DataFrame]) -> Tuple[int, int]:
        """
        Load data into staging tables.
        
        Args:
            data: Dictionary of DataFrames to load
            
        Returns:
            Tuple of (total_rows_loaded, total_errors)
        """
        logger.info("=== LOADING DATA TO STAGING TABLES ===")
        
        total_rows_loaded = 0
        total_errors = 0
        
        try:
            # Truncate staging tables
            self.truncate_staging_tables()
            
            # Load products
            if 'products' in data:
                rows, errors = self._load_dataframe_to_table(
                    data['products'], 
                    'staging_products'
                )
                total_rows_loaded += rows
                total_errors += errors
            
            # Load customers
            if 'customers' in data:
                rows, errors = self._load_dataframe_to_table(
                    data['customers'],
                    'staging_customers'
                )
                total_rows_loaded += rows
                total_errors += errors
            
            # Load orders
            if 'orders' in data:
                rows, errors = self._load_dataframe_to_table(
                    data['orders'],
                    'staging_orders'
                )
                total_rows_loaded += rows
                total_errors += errors
            
            logger.info(f"Loaded {total_rows_loaded} rows with {total_errors} errors")
            return total_rows_loaded, total_errors
        
        except Exception as e:
            logger.error(f"Error loading to staging: {str(e)}")
            raise
    
    def _load_dataframe_to_table(self, df: pd.DataFrame, table_name: str) -> Tuple[int, int]:
        """
        Load a DataFrame to a table.
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            
        Returns:
            Tuple of (rows_loaded, errors)
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {table_name}")
            return 0, 0
        
        try:
            cursor = self.connection.cursor()
            
            # Prepare data
            columns = list(df.columns)
            values = [tuple(row) for row in df.values]
            
            # Build INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # Execute batch insert
            execute_batch(cursor, insert_query, values, page_size=1000)
            
            self.connection.commit()
            
            rows_loaded = cursor.rowcount
            logger.info(f"Loaded {rows_loaded} rows to {table_name}")
            
            cursor.close()
            return rows_loaded, 0
        
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Error loading {table_name}: {str(e)}")
            return 0, len(df)
    
    def load_to_facts_and_dimensions(self) -> Tuple[int, int]:
        """
        Load data from staging tables to facts and dimensions.
        This step handles SCD transformations and dimension merging.
        
        Returns:
            Tuple of (total_rows_loaded, total_errors)
        """
        logger.info("=== LOADING DATA TO FACTS AND DIMENSIONS ===")
        
        total_rows_loaded = 0
        total_errors = 0
        
        try:
            cursor = self.connection.cursor()
            
            # Load dimensions (inserts or updates)
            sql_statements = [
                # Load products dimension (SCD Type 1)
                """
                INSERT INTO dim_products (product_id, title, category, price, rating, review_count, description)
                SELECT DISTINCT product_id, title, category, price, rating, review_count, description
                FROM staging_products
                ON CONFLICT (product_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    price = EXCLUDED.price,
                    rating = EXCLUDED.rating,
                    review_count = EXCLUDED.review_count,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                
                # Load customers dimension (SCD Type 2)
                """
                INSERT INTO dim_customers (customer_id, first_name, last_name, email, phone, city, state, country, zip_code, start_date, is_current)
                SELECT DISTINCT customer_id, first_name, last_name, email, phone, city, state, country, zip_code, CURRENT_DATE, TRUE
                FROM staging_customers
                WHERE customer_id NOT IN (SELECT customer_id FROM dim_customers WHERE is_current = TRUE)
                ON CONFLICT DO NOTHING;
                """,
                
                # Load fact table
                """
                INSERT INTO fact_orders (order_id, customer_key, product_key, date_key, quantity, amount, order_status, created_at)
                SELECT 
                    so.order_id,
                    dc.customer_key,
                    dp.product_key,
                    TO_CHAR(so.created_at, 'YYYYMMDD')::INT as date_key,
                    so.quantity,
                    so.amount,
                    so.status,
                    so.created_at
                FROM staging_orders so
                LEFT JOIN dim_customers dc ON so.customer_id = dc.customer_id AND dc.is_current = TRUE
                LEFT JOIN dim_products dp ON so.product_id = dp.product_id
                ON CONFLICT (order_id) DO NOTHING;
                """,
            ]
            
            for sql in sql_statements:
                cursor.execute(sql)
                total_rows_loaded += cursor.rowcount
            
            self.connection.commit()
            logger.info(f"Loaded {total_rows_loaded} rows to facts/dimensions")
            
            cursor.close()
            return total_rows_loaded, 0
        
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Error loading to facts/dimensions: {str(e)}")
            total_errors += 1
            return 0, total_errors
    
    def update_metrics(self):
        """Update daily metrics table."""
        logger.info("Updating daily metrics...")
        
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO daily_metrics (metric_date, total_orders, total_customers, total_revenue, avg_order_value, pipeline_status)
            SELECT 
                CURRENT_DATE,
                COUNT(DISTINCT fo.order_id),
                COUNT(DISTINCT fo.customer_key),
                SUM(fo.amount),
                AVG(fo.amount),
                'SUCCESS'
            FROM fact_orders fo
            WHERE DATE(fo.created_at) = CURRENT_DATE
            ON CONFLICT (metric_date) DO UPDATE SET
                total_orders = EXCLUDED.total_orders,
                total_customers = EXCLUDED.total_customers,
                total_revenue = EXCLUDED.total_revenue,
                avg_order_value = EXCLUDED.avg_order_value,
                pipeline_status = EXCLUDED.pipeline_status,
                processed_at = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(sql)
            self.connection.commit()
            
            logger.info("Daily metrics updated")
            cursor.close()
        
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Error updating metrics: {str(e)}")

class LoadingPipeline:
    """Orchestrate loading pipeline."""
    
    def __init__(self, db_config: Dict = None):
        self.loader = DataLoader(db_config)
    
    def load_all(self, transformed_data: Dict[str, pd.DataFrame]) -> Tuple[int, int]:
        """
        Execute complete loading pipeline.
        
        Args:
            transformed_data: Dictionary of transformed DataFrames
            
        Returns:
            Tuple of (total_rows_loaded, total_errors)
        """
        total_rows = 0
        total_errors = 0
        
        try:
            # Connect to database
            self.loader.connect()
            
            # Load to staging tables
            rows, errors = self.loader.load_to_staging(transformed_data)
            total_rows += rows
            total_errors += errors
            
            # Load to facts and dimensions
            rows, errors = self.loader.load_to_facts_and_dimensions()
            total_rows += rows
            total_errors += errors
            
            # Update metrics
            self.loader.update_metrics()
            
            logger.info(f"Loading pipeline completed: {total_rows} rows loaded, {total_errors} errors")
            return total_rows, total_errors
        
        finally:
            self.loader.disconnect()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test connection
    loader = DataLoader()
    try:
        loader.connect()
        logger.info("Database connection successful!")
        loader.disconnect()
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
