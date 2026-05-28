"""
Data transformation module for cleaning and preparing data.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transform and clean raw extracted data."""
    
    @staticmethod
    def transform_products(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform products data.
        
        Args:
            df: Raw products DataFrame
            
        Returns:
            Transformed DataFrame ready for loading
        """
        logger.info("Transforming products data...")
        
        df = df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['product_id'])
        
        # Handle missing values
        df['description'] = df['description'].fillna('')
        df['rating'] = df['rating'].fillna(0)
        df['review_count'] = df['review_count'].fillna(0)
        
        # Type conversions
        df['product_id'] = df['product_id'].astype(int)
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
        df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0).astype(int)
        
        # Add metadata
        df['created_at'] = datetime.now()
        df['updated_at'] = datetime.now()
        
        # Ensure required columns
        required_cols = ['product_id', 'title', 'category', 'price', 'rating', 
                        'review_count', 'description', 'created_at', 'updated_at']
        df = df[[col for col in required_cols if col in df.columns]]
        
        logger.info(f"Transformed {len(df)} products")
        return df
    
    @staticmethod
    def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform customers data.
        
        Args:
            df: Raw customers DataFrame
            
        Returns:
            Transformed DataFrame ready for loading
        """
        logger.info("Transforming customers data...")
        
        df = df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['customer_id'])
        
        # Handle missing values
        df['first_name'] = df['first_name'].fillna('Unknown').str.strip()
        df['last_name'] = df['last_name'].fillna('').str.strip()
        df['email'] = df['email'].fillna('').str.strip()
        df['phone'] = df['phone'].fillna('').str.strip()
        df['city'] = df['city'].fillna('').str.strip()
        df['state'] = df['state'].fillna('').str.strip()
        df['country'] = df['country'].fillna('USA').str.strip()
        df['zip_code'] = df['zip_code'].fillna('').str.strip()
        
        # Type conversions
        df['customer_id'] = df['customer_id'].astype(int)
        
        # Add metadata
        df['created_at'] = datetime.now()
        df['updated_at'] = datetime.now()
        
        # Ensure required columns
        required_cols = ['customer_id', 'first_name', 'last_name', 'email', 'phone',
                        'city', 'state', 'country', 'zip_code', 'created_at', 'updated_at']
        df = df[[col for col in required_cols if col in df.columns]]
        
        logger.info(f"Transformed {len(df)} customers")
        return df
    
    @staticmethod
    def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform orders data.
        
        Args:
            df: Raw orders DataFrame
            
        Returns:
            Transformed DataFrame ready for loading
        """
        logger.info("Transforming orders data...")
        
        df = df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['order_id'])
        
        # Handle missing values
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1).astype(int)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        df['status'] = df['status'].fillna('pending').str.lower()
        
        # Type conversions
        df['order_id'] = df['order_id'].astype(int)
        df['customer_id'] = df['customer_id'].astype(int)
        df['product_id'] = df['product_id'].astype(int)
        
        # Parse dates
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').fillna(datetime.now())
        
        # Remove negative or zero amounts (data quality issue)
        df = df[df['amount'] > 0]
        
        # Add metadata
        df['updated_at'] = datetime.now()
        
        # Ensure required columns
        required_cols = ['order_id', 'customer_id', 'product_id', 'quantity', 'amount',
                        'status', 'created_at', 'updated_at']
        df = df[[col for col in required_cols if col in df.columns]]
        
        logger.info(f"Transformed {len(df)} orders")
        return df
    
    @staticmethod
    def perform_eda(data: Dict[str, pd.DataFrame]) -> None:
        """
        Perform exploratory data analysis and log findings.
        
        Args:
            data: Dictionary of DataFrames
        """
        logger.info("=== DATA QUALITY SUMMARY ===")
        
        for table_name, df in data.items():
            logger.info(f"\n{table_name.upper()}")
            logger.info(f"  Rows: {len(df)}")
            logger.info(f"  Columns: {len(df.columns)}")
            logger.info(f"  Null values:\n{df.isnull().sum()}")
            
            # Check for duplicates
            if len(df) > 0:
                id_col = [col for col in df.columns if col.endswith('_id')]
                if id_col:
                    dup_count = df[id_col].duplicated().sum()
                    logger.info(f"  Duplicates: {dup_count}")
    
    @staticmethod
    def get_transform_summary(original: Dict[str, pd.DataFrame], 
                             transformed: Dict[str, pd.DataFrame]) -> Dict:
        """
        Generate summary of transformation.
        
        Args:
            original: Original data
            transformed: Transformed data
            
        Returns:
            Summary dictionary
        """
        summary = {}
        
        for key in original.keys():
            orig_rows = len(original[key])
            trans_rows = len(transformed[key])
            
            summary[key] = {
                'original_rows': orig_rows,
                'transformed_rows': trans_rows,
                'rows_removed': orig_rows - trans_rows,
                'removal_rate': round((orig_rows - trans_rows) / orig_rows * 100, 2) if orig_rows > 0 else 0
            }
        
        return summary

class TransformationPipeline:
    """Orchestrate data transformation pipeline."""
    
    def __init__(self):
        self.transformer = DataTransformer()
    
    def transform_all(self, extracted_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Transform all extracted data.
        
        Args:
            extracted_data: Dictionary of raw DataFrames
            
        Returns:
            Dictionary of transformed DataFrames
        """
        logger.info("=== STARTING TRANSFORMATION PIPELINE ===")
        
        try:
            transformed_data = {
                'products': self.transformer.transform_products(extracted_data['products']),
                'customers': self.transformer.transform_customers(extracted_data['customers']),
                'orders': self.transformer.transform_orders(extracted_data['orders']),
            }
            
            # Perform EDA
            self.transformer.perform_eda(transformed_data)
            
            # Log summary
            summary = self.transformer.get_transform_summary(extracted_data, transformed_data)
            logger.info("\n=== TRANSFORMATION SUMMARY ===")
            for table, stats in summary.items():
                logger.info(f"{table}: {stats['original_rows']} -> {stats['transformed_rows']} "
                           f"({stats['rows_removed']} removed, {stats['removal_rate']}%)")
            
            logger.info("Transformation pipeline completed successfully")
            return transformed_data
        
        except Exception as e:
            logger.error(f"Error in transformation pipeline: {str(e)}")
            raise

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    sample_products = pd.DataFrame([
        {'product_id': 1, 'title': 'Product 1', 'price': 29.99, 'category': 'Electronics', 'rating': 4.5},
        {'product_id': 2, 'title': 'Product 2', 'price': None, 'category': 'Home', 'rating': 3.0},
    ])
    
    transformer = DataTransformer()
    transformed = transformer.transform_products(sample_products)
    print(transformed)
