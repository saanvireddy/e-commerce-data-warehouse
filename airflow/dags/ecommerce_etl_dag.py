"""
Apache Airflow DAG for E-Commerce Data Warehouse ETL Pipeline.
Scheduled to run daily at 2 AM UTC.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from extract import DataExtractor
from transform import TransformationPipeline
from load import LoadingPipeline
from validation import ValidationPipeline

# ============================================================================
# DEFAULT ARGUMENTS
# ============================================================================

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# ============================================================================
# DAG DEFINITION
# ============================================================================

dag = DAG(
    'ecommerce_etl_pipeline',
    default_args=default_args,
    description='E-Commerce Data Warehouse ETL Pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'ecommerce', 'data-warehouse'],
)

# ============================================================================
# PYTHON FUNCTIONS FOR TASKS
# ============================================================================

def extract_data(**context):
    """Extract data from APIs."""
    print("Starting data extraction...")
    
    try:
        extractor = DataExtractor()
        data = extractor.extract_all()
        
        # Push data to XCom for next task
        for table_name, df in data.items():
            context['ti'].xcom_push(key=f'{table_name}_rows', value=len(df))
            print(f"Extracted {len(df)} {table_name} records")
        
        print("Data extraction completed successfully")
        return True
    
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        raise

def transform_data(**context):
    """Transform extracted data."""
    print("Starting data transformation...")
    
    try:
        from extract import DataExtractor
        
        # Re-extract data for transformation
        extractor = DataExtractor()
        extracted_data = extractor.extract_all()
        
        # Transform data
        transform_pipeline = TransformationPipeline()
        transformed_data = transform_pipeline.transform_all(extracted_data)
        
        # Log stats
        for table_name, df in transformed_data.items():
            context['ti'].xcom_push(key=f'{table_name}_transformed_rows', value=len(df))
            print(f"Transformed {len(df)} {table_name} records")
        
        print("Data transformation completed successfully")
        return True
    
    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        raise

def load_data(**context):
    """Load data into warehouse."""
    print("Starting data loading...")
    
    try:
        from extract import DataExtractor
        from transform import TransformationPipeline
        
        # Extract and transform
        extractor = DataExtractor()
        extracted_data = extractor.extract_all()
        
        transform_pipeline = TransformationPipeline()
        transformed_data = transform_pipeline.transform_all(extracted_data)
        
        # Load data
        load_pipeline = LoadingPipeline()
        rows_loaded, errors = load_pipeline.load_all(transformed_data)
        
        context['ti'].xcom_push(key='rows_loaded', value=rows_loaded)
        context['ti'].xcom_push(key='load_errors', value=errors)
        
        print(f"Loaded {rows_loaded} rows with {errors} errors")
        print("Data loading completed successfully")
        return True
    
    except Exception as e:
        print(f"Error during loading: {str(e)}")
        raise

def validate_data(**context):
    """Validate loaded data."""
    print("Starting data validation...")
    
    try:
        validation_pipeline = ValidationPipeline()
        all_passed, results = validation_pipeline.validate_all()
        
        context['ti'].xcom_push(key='validation_passed', value=all_passed)
        context['ti'].xcom_push(key='validation_summary', value=str(results['summary']))
        
        print(f"Validation Results: {results['summary']}")
        
        if not all_passed:
            print("WARNING: Some validation checks failed")
        
        print("Data validation completed")
        return all_passed
    
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        raise

def log_summary(**context):
    """Log pipeline execution summary."""
    print("\n" + "=" * 80)
    print("ETL PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    
    ti = context['ti']
    
    # Retrieve values from previous tasks
    extract_products = ti.xcom_pull(key='products_rows', task_ids='extract')
    extract_customers = ti.xcom_pull(key='customers_rows', task_ids='extract')
    extract_orders = ti.xcom_pull(key='orders_rows', task_ids='extract')
    
    rows_loaded = ti.xcom_pull(key='rows_loaded', task_ids='load')
    errors = ti.xcom_pull(key='load_errors', task_ids='load')
    validation_passed = ti.xcom_pull(key='validation_passed', task_ids='validate')
    
    print(f"\nExtraction:")
    print(f"  Products: {extract_products or 'N/A'}")
    print(f"  Customers: {extract_customers or 'N/A'}")
    print(f"  Orders: {extract_orders or 'N/A'}")
    
    print(f"\nLoading:")
    print(f"  Total Rows Loaded: {rows_loaded or 'N/A'}")
    print(f"  Errors: {errors or 'N/A'}")
    
    print(f"\nValidation:")
    print(f"  Status: {'PASSED' if validation_passed else 'FAILED'}")
    
    print("\n" + "=" * 80)

# ============================================================================
# TASK DEFINITIONS
# ============================================================================

extract_task = PythonOperator(
    task_id='extract',
    python_callable=extract_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load',
    python_callable=load_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate',
    python_callable=validate_data,
    dag=dag,
)

summary_task = PythonOperator(
    task_id='log_summary',
    python_callable=log_summary,
    trigger_rule='all_done',  # Run even if previous tasks fail
    dag=dag,
)

# ============================================================================
# TASK DEPENDENCIES
# ============================================================================

extract_task >> transform_task >> load_task >> validate_task >> summary_task

# ============================================================================
# DAG DOCUMENTATION
# ============================================================================

dag.doc_md = """
## E-Commerce Data Warehouse ETL Pipeline

This DAG orchestrates the daily ETL process for the e-commerce data warehouse.

### Tasks:
1. **extract**: Extract data from APIs
2. **transform**: Clean and transform data
3. **load**: Load data into warehouse
4. **validate**: Perform data quality checks
5. **log_summary**: Log execution summary

### Schedule:
- Daily at 2:00 AM UTC
- Catchup disabled

### Success Criteria:
- All tasks must complete successfully
- Data validation must pass

### Contact:
- Owner: Data Engineering Team
- Email: admin@example.com

### Related Dashboards:
- Daily Metrics: [Link]
- Data Quality Metrics: [Link]
"""
