"""
Data quality validation module for comprehensive data checks.
"""

import psycopg2
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from config import DB_CONFIG, DATA_QUALITY_CONFIG

logger = logging.getLogger(__name__)

class DataQualityValidator:
    """Perform data quality checks on warehouse data."""
    
    def __init__(self, db_config: Dict = None):
        self.db_config = db_config or DB_CONFIG
        self.connection = None
        self.checks_passed = 0
        self.checks_failed = 0
    
    def connect(self):
        """Connect to database."""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Connected to database for quality checks")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def check_null_values(self, table: str, columns: List[str]) -> Tuple[bool, str]:
        """
        Check for null values in specified columns.
        
        Args:
            table: Table name
            columns: List of column names to check
            
        Returns:
            Tuple of (passed, message)
        """
        try:
            cursor = self.connection.cursor()
            
            for column in columns:
                sql = f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
                cursor.execute(sql)
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    msg = f"NULL values found in {table}.{column}: {null_count}"
                    logger.warning(msg)
                    self.checks_failed += 1
                    cursor.close()
                    return False, msg
            
            msg = f"NULL check passed for {table}"
            self.checks_passed += 1
            cursor.close()
            return True, msg
        
        except psycopg2.Error as e:
            logger.error(f"Error in null check: {str(e)}")
            return False, str(e)
    
    def check_duplicate_keys(self, table: str, key_column: str) -> Tuple[bool, str]:
        """
        Check for duplicate keys.
        
        Args:
            table: Table name
            key_column: Key column to check
            
        Returns:
            Tuple of (passed, message)
        """
        try:
            cursor = self.connection.cursor()
            
            sql = f"""
            SELECT {key_column}, COUNT(*) as cnt
            FROM {table}
            GROUP BY {key_column}
            HAVING COUNT(*) > 1
            """
            
            cursor.execute(sql)
            duplicates = cursor.fetchall()
            
            if duplicates:
                dup_count = len(duplicates)
                msg = f"Duplicates found in {table}.{key_column}: {dup_count} duplicate values"
                logger.warning(msg)
                self.checks_failed += 1
                cursor.close()
                return False, msg
            
            msg = f"Duplicate check passed for {table}.{key_column}"
            self.checks_passed += 1
            cursor.close()
            return True, msg
        
        except psycopg2.Error as e:
            logger.error(f"Error in duplicate check: {str(e)}")
            return False, str(e)
    
    def check_referential_integrity(self, foreign_table: str, foreign_column: str,
                                   primary_table: str, primary_column: str) -> Tuple[bool, str]:
        """
        Check referential integrity between tables.
        
        Args:
            foreign_table: Table with foreign key
            foreign_column: Foreign key column
            primary_table: Referenced table
            primary_column: Primary key column
            
        Returns:
            Tuple of (passed, message)
        """
        try:
            cursor = self.connection.cursor()
            
            sql = f"""
            SELECT COUNT(*) FROM {foreign_table}
            WHERE {foreign_column} IS NOT NULL
            AND {foreign_column} NOT IN (SELECT {primary_column} FROM {primary_table})
            """
            
            cursor.execute(sql)
            orphan_count = cursor.fetchone()[0]
            
            if orphan_count > 0:
                msg = f"Referential integrity violation: {orphan_count} orphaned records in {foreign_table}"
                logger.warning(msg)
                self.checks_failed += 1
                cursor.close()
                return False, msg
            
            msg = f"Referential integrity check passed for {foreign_table}.{foreign_column}"
            self.checks_passed += 1
            cursor.close()
            return True, msg
        
        except psycopg2.Error as e:
            logger.error(f"Error in referential integrity check: {str(e)}")
            return False, str(e)
    
    def check_data_freshness(self, table: str, date_column: str, hours: int = 24) -> Tuple[bool, str]:
        """
        Check if data is recent (within specified hours).
        
        Args:
            table: Table name
            date_column: Date column to check
            hours: Number of hours for freshness
            
        Returns:
            Tuple of (passed, message)
        """
        try:
            cursor = self.connection.cursor()
            
            sql = f"""
            SELECT COUNT(*) FROM {table}
            WHERE {date_column} < CURRENT_TIMESTAMP - INTERVAL '{hours} hours'
            """
            
            cursor.execute(sql)
            stale_count = cursor.fetchone()[0]
            total_count = self._get_row_count(table)
            
            stale_percentage = (stale_count / total_count * 100) if total_count > 0 else 0
            
            if stale_percentage > 50:  # Alert if >50% data is stale
                msg = f"Data freshness issue in {table}: {stale_percentage:.1f}% stale data"
                logger.warning(msg)
                self.checks_failed += 1
                cursor.close()
                return False, msg
            
            msg = f"Data freshness check passed for {table}"
            self.checks_passed += 1
            cursor.close()
            return True, msg
        
        except psycopg2.Error as e:
            logger.error(f"Error in freshness check: {str(e)}")
            return False, str(e)
    
    def check_value_ranges(self, table: str, column: str, min_val: float, max_val: float) -> Tuple[bool, str]:
        """
        Check if values are within expected range.
        
        Args:
            table: Table name
            column: Column to check
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Tuple of (passed, message)
        """
        try:
            cursor = self.connection.cursor()
            
            sql = f"""
            SELECT COUNT(*) FROM {table}
            WHERE {column} < {min_val} OR {column} > {max_val}
            """
            
            cursor.execute(sql)
            out_of_range = cursor.fetchone()[0]
            
            if out_of_range > 0:
                msg = f"Range check failed for {table}.{column}: {out_of_range} values out of range [{min_val}, {max_val}]"
                logger.warning(msg)
                self.checks_failed += 1
                cursor.close()
                return False, msg
            
            msg = f"Range check passed for {table}.{column}"
            self.checks_passed += 1
            cursor.close()
            return True, msg
        
        except psycopg2.Error as e:
            logger.error(f"Error in range check: {str(e)}")
            return False, str(e)
    
    def get_table_stats(self, table: str) -> Dict:
        """Get statistics for a table."""
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # Row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats['row_count'] = cursor.fetchone()[0]
            
            # Null counts per column
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            
            stats['null_counts'] = {}
            for column in columns:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
                null_count = cursor.fetchone()[0]
                if null_count > 0:
                    stats['null_counts'][column] = null_count
            
            cursor.close()
            return stats
        
        except psycopg2.Error as e:
            logger.error(f"Error getting table stats: {str(e)}")
            return {}
    
    def _get_row_count(self, table: str) -> int:
        """Get row count for a table."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except psycopg2.Error:
            return 0

class ValidationPipeline:
    """Orchestrate comprehensive data quality validation."""
    
    def __init__(self, db_config: Dict = None):
        self.validator = DataQualityValidator(db_config)
    
    def validate_all(self) -> Tuple[bool, Dict]:
        """
        Run comprehensive data quality validation.
        
        Returns:
            Tuple of (all_passed, results_dict)
        """
        logger.info("=== STARTING DATA QUALITY VALIDATION ===")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'summary': {}
        }
        
        try:
            self.validator.connect()
            
            # Run null checks
            logger.info("Running null checks...")
            for table, columns in DATA_QUALITY_CONFIG['null_checks'].items():
                passed, message = self.validator.check_null_values(table, columns)
                results['checks'].append({
                    'check_type': 'null_check',
                    'table': table,
                    'passed': passed,
                    'message': message
                })
            
            # Run duplicate checks
            logger.info("Running duplicate checks...")
            for table in ['staging_orders', 'staging_customers', 'staging_products']:
                id_col = [col for col in DATA_QUALITY_CONFIG['unique_checks'].get(table, [])][0] if table in DATA_QUALITY_CONFIG['unique_checks'] else 'id'
                passed, message = self.validator.check_duplicate_keys(table, id_col)
                results['checks'].append({
                    'check_type': 'duplicate_check',
                    'table': table,
                    'passed': passed,
                    'message': message
                })
            
            # Run referential integrity checks
            logger.info("Running referential integrity checks...")
            checks = [
                ('fact_orders', 'customer_key', 'dim_customers', 'customer_key'),
                ('fact_orders', 'product_key', 'dim_products', 'product_key'),
            ]
            
            for fk_table, fk_col, pk_table, pk_col in checks:
                passed, message = self.validator.check_referential_integrity(
                    fk_table, fk_col, pk_table, pk_col
                )
                results['checks'].append({
                    'check_type': 'referential_integrity',
                    'table': fk_table,
                    'passed': passed,
                    'message': message
                })
            
            # Get summary
            results['summary'] = {
                'total_checks': len(results['checks']),
                'passed_checks': self.validator.checks_passed,
                'failed_checks': self.validator.checks_failed,
                'success_rate': round(self.validator.checks_passed / len(results['checks']) * 100, 2) if results['checks'] else 0
            }
            
            all_passed = results['summary']['failed_checks'] == 0
            
            logger.info(f"Validation completed: {results['summary']['passed_checks']}/{results['summary']['total_checks']} checks passed")
            
            return all_passed, results
        
        finally:
            self.validator.disconnect()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    pipeline = ValidationPipeline()
    all_passed, results = pipeline.validate_all()
    
    print("\n=== VALIDATION RESULTS ===")
    print(f"All Passed: {all_passed}")
    print(f"Summary: {results['summary']}")
