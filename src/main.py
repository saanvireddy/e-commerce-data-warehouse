"""
Main ETL orchestration script.
Coordinates extraction, transformation, loading, and validation.
"""

import logging
import argparse
import sys
from datetime import datetime
from typing import Dict

from extract import DataExtractor
from transform import TransformationPipeline
from load import LoadingPipeline
from validation import ValidationPipeline
from config import validate_config, log_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ETLPipeline:
    """Main ETL pipeline orchestrator."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.status = 'PENDING'
        self.error_message = None
    
    def run_full_pipeline(self) -> bool:
        """
        Run complete ETL pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info(f"STARTING ETL PIPELINE: {self.start_time}")
        logger.info("=" * 80)
        
        try:
            # Validate configuration
            if not validate_config():
                raise Exception("Configuration validation failed")
            
            log_config()
            
            # EXTRACT
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: EXTRACT")
            logger.info("=" * 80)
            
            extractor = DataExtractor()
            extracted_data = extractor.extract_all()
            
            # TRANSFORM
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: TRANSFORM")
            logger.info("=" * 80)
            
            transform_pipeline = TransformationPipeline()
            transformed_data = transform_pipeline.transform_all(extracted_data)
            
            # LOAD
            logger.info("\n" + "=" * 80)
            logger.info("STEP 3: LOAD")
            logger.info("=" * 80)
            
            load_pipeline = LoadingPipeline()
            rows_loaded, errors = load_pipeline.load_all(transformed_data)
            
            # VALIDATE
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: VALIDATE")
            logger.info("=" * 80)
            
            validation_pipeline = ValidationPipeline()
            validation_passed, validation_results = validation_pipeline.validate_all()
            
            # Summary
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            if validation_passed:
                self.status = 'SUCCESS'
                logger.info("\n" + "=" * 80)
                logger.info(f"ETL PIPELINE COMPLETED SUCCESSFULLY")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info(f"Rows Loaded: {rows_loaded}")
                logger.info(f"Validation: PASSED")
                logger.info("=" * 80)
                return True
            else:
                self.status = 'WARNING'
                logger.warning("\n" + "=" * 80)
                logger.warning(f"ETL PIPELINE COMPLETED WITH VALIDATION WARNINGS")
                logger.warning(f"Validation Results: {validation_results['summary']}")
                logger.warning("=" * 80)
                return True  # Still return True since data was loaded
        
        except Exception as e:
            self.status = 'FAILED'
            self.error_message = str(e)
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            logger.error("\n" + "=" * 80)
            logger.error(f"ETL PIPELINE FAILED")
            logger.error(f"Duration: {duration:.2f} seconds")
            logger.error(f"Error: {self.error_message}")
            logger.error("=" * 80)
            
            return False
    
    def run_extract_only(self) -> bool:
        """Run only extraction step."""
        logger.info("Running EXTRACT step only...")
        
        try:
            extractor = DataExtractor()
            data = extractor.extract_all()
            
            for table_name, df in data.items():
                logger.info(f"{table_name}: {len(df)} rows extracted")
            
            logger.info("Extract step completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Extract step failed: {str(e)}")
            return False
    
    def run_transform_only(self, use_sample_data: bool = True) -> bool:
        """Run only transformation step."""
        logger.info("Running TRANSFORM step only...")
        
        try:
            import pandas as pd
            
            # Create sample data if needed
            if use_sample_data:
                logger.info("Using sample data for transformation")
                sample_data = {
                    'products': pd.DataFrame([
                        {'product_id': 1, 'title': 'Test Product', 'price': 29.99, 'category': 'Electronics', 'rating': 4.5, 'review_count': 100},
                    ]),
                    'customers': pd.DataFrame([
                        {'customer_id': 1, 'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com', 'phone': '555-1234', 'city': 'NYC', 'state': 'NY', 'country': 'USA', 'zip_code': '10001'},
                    ]),
                    'orders': pd.DataFrame([
                        {'order_id': 1, 'customer_id': 1, 'product_id': 1, 'quantity': 2, 'amount': 59.98, 'status': 'completed', 'created_at': '2024-01-01'},
                    ]),
                }
            
            transform_pipeline = TransformationPipeline()
            transformed_data = transform_pipeline.transform_all(sample_data)
            
            logger.info("Transform step completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Transform step failed: {str(e)}")
            return False
    
    def run_validate_only(self) -> bool:
        """Run only validation step."""
        logger.info("Running VALIDATE step only...")
        
        try:
            validation_pipeline = ValidationPipeline()
            validation_passed, results = validation_pipeline.validate_all()
            
            logger.info(f"Validation Results: {results['summary']}")
            return validation_passed
        
        except Exception as e:
            logger.error(f"Validation step failed: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """Get pipeline execution status."""
        return {
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            'error_message': self.error_message
        }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='E-Commerce Data Warehouse ETL Pipeline')
    parser.add_argument(
        '--mode',
        choices=['full', 'extract', 'transform', 'validate'],
        default='full',
        help='ETL mode to run'
    )
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Use sample data for transform-only mode'
    )
    
    args = parser.parse_args()
    
    pipeline = ETLPipeline()
    
    if args.mode == 'full':
        success = pipeline.run_full_pipeline()
    elif args.mode == 'extract':
        success = pipeline.run_extract_only()
    elif args.mode == 'transform':
        success = pipeline.run_transform_only(args.sample_data)
    elif args.mode == 'validate':
        success = pipeline.run_validate_only()
    else:
        logger.error(f"Unknown mode: {args.mode}")
        success = False
    
    # Log final status
    logger.info(f"\nFinal Status: {pipeline.get_status()}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
