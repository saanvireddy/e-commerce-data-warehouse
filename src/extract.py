"""
Data extraction module for fetching data from APIs and files.
"""

import requests
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from config import API_CONFIG, get_api_endpoint

logger = logging.getLogger(__name__)

class APIExtractor:
    """Extract data from REST APIs."""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        self.base_url = base_url or API_CONFIG['base_url']
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ECommerceETL/1.0'})
    
    def fetch_products(self) -> List[Dict[str, Any]]:
        """
        Fetch products from FakeStore API.
        
        Returns:
            List of product dictionaries
        """
        try:
            endpoint = get_api_endpoint('products')
            logger.info(f"Fetching products from {endpoint}")
            
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            products = response.json()
            logger.info(f"Successfully fetched {len(products)} products")
            
            return products
        
        except requests.RequestException as e:
            logger.error(f"Error fetching products: {str(e)}")
            raise
    
    def fetch_users(self) -> List[Dict[str, Any]]:
        """
        Fetch users from FakeStore API.
        
        Returns:
            List of user dictionaries
        """
        try:
            endpoint = get_api_endpoint('users')
            logger.info(f"Fetching users from {endpoint}")
            
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            users = response.json()
            logger.info(f"Successfully fetched {len(users)} users")
            
            return users
        
        except requests.RequestException as e:
            logger.error(f"Error fetching users: {str(e)}")
            raise
    
    def fetch_carts(self) -> List[Dict[str, Any]]:
        """
        Fetch carts (orders) from FakeStore API.
        
        Returns:
            List of cart dictionaries
        """
        try:
            endpoint = get_api_endpoint('carts')
            logger.info(f"Fetching carts from {endpoint}")
            
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            carts = response.json()
            logger.info(f"Successfully fetched {len(carts)} carts")
            
            return carts
        
        except requests.RequestException as e:
            logger.error(f"Error fetching carts: {str(e)}")
            raise
    
    def close(self):
        """Close session."""
        self.session.close()

class DataExtractor:
    """Main data extraction orchestrator."""
    
    def __init__(self):
        self.api = APIExtractor()
    
    def extract_products(self) -> pd.DataFrame:
        """Extract and transform products data."""
        logger.info("=== EXTRACTING PRODUCTS ===")
        
        try:
            products = self.api.fetch_products()
            
            # Transform to DataFrame
            df = pd.DataFrame(products)
            
            # Rename columns to match staging table
            df = df.rename(columns={
                'id': 'product_id',
                'title': 'title',
                'price': 'price',
                'category': 'category',
                'description': 'description',
                'rating': 'rating',  # This is a nested dict, will handle in transform
            })
            
            # Handle rating (nested structure)
            if 'rating' in df.columns and isinstance(df['rating'].iloc[0], dict):
                df['rating'] = df['rating'].apply(lambda x: x.get('rate', 0) if isinstance(x, dict) else x)
                df['review_count'] = df['rating'].apply(lambda x: x.get('count', 0) if isinstance(x, dict) else 0)
            
            logger.info(f"Extracted {len(df)} products")
            return df
        
        except Exception as e:
            logger.error(f"Error extracting products: {str(e)}")
            raise
    
    def extract_customers(self) -> pd.DataFrame:
        """Extract and transform customers data."""
        logger.info("=== EXTRACTING CUSTOMERS ===")
        
        try:
            users = self.api.fetch_users()
            
            # Transform to DataFrame
            df = pd.DataFrame(users)
            
            # Flatten nested address
            if 'address' in df.columns:
                df['city'] = df['address'].apply(lambda x: x.get('city', '') if isinstance(x, dict) else '')
                df['zip_code'] = df['address'].apply(lambda x: x.get('zipcode', '') if isinstance(x, dict) else '')
            
            # Rename columns to match staging table
            df = df.rename(columns={
                'id': 'customer_id',
                'username': 'first_name',  # Simplified mapping
                'email': 'email',
                'phone': 'phone',
            })
            
            # Add missing columns
            df['last_name'] = ''
            df['state'] = ''
            df['country'] = 'USA'
            
            # Select only needed columns
            columns = ['customer_id', 'first_name', 'last_name', 'email', 'phone', 
                      'city', 'state', 'country', 'zip_code']
            df = df[[col for col in columns if col in df.columns]]
            
            logger.info(f"Extracted {len(df)} customers")
            return df
        
        except Exception as e:
            logger.error(f"Error extracting customers: {str(e)}")
            raise
    
    def extract_orders(self) -> pd.DataFrame:
        """Extract and transform orders data."""
        logger.info("=== EXTRACTING ORDERS ===")
        
        try:
            carts = self.api.fetch_carts()
            
            # Transform carts to orders (flatten)
            orders = []
            for cart in carts:
                user_id = cart.get('userId')
                products = cart.get('products', [])
                date = cart.get('date', datetime.now().isoformat())
                
                for i, product in enumerate(products):
                    order = {
                        'order_id': f"{user_id}_{len(orders) + i}",  # Generate unique order ID
                        'customer_id': user_id,
                        'product_id': product.get('productId'),
                        'quantity': product.get('quantity', 1),
                        'amount': product.get('quantity', 1) * 100,  # Placeholder amount
                        'status': 'completed',
                        'created_at': date,
                    }
                    orders.append(order)
            
            df = pd.DataFrame(orders)
            
            # Ensure order_id is integer
            df['order_id'] = df['order_id'].astype(str).str.extract('(\d+)')[0].astype(int)
            
            logger.info(f"Extracted {len(df)} orders")
            return df
        
        except Exception as e:
            logger.error(f"Error extracting orders: {str(e)}")
            raise
    
    def extract_all(self) -> Dict[str, pd.DataFrame]:
        """Extract all data sources."""
        logger.info("Starting data extraction...")
        
        try:
            data = {
                'products': self.extract_products(),
                'customers': self.extract_customers(),
                'orders': self.extract_orders(),
            }
            
            logger.info("Data extraction completed successfully")
            return data
        
        finally:
            self.api.close()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    extractor = DataExtractor()
    data = extractor.extract_all()
    
    for key, df in data.items():
        print(f"\n{key.upper()} (Shape: {df.shape})")
        print(df.head())
