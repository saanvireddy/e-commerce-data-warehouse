{{
    config(
        materialized = 'view',
        tags = ['staging']
    )
}}

SELECT
    order_id,
    customer_id,
    product_id,
    quantity,
    amount,
    status,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP as dbt_loaded_at
FROM
    {{ source('ecommerce', 'staging_orders') }}
WHERE
    validation_status = 'PENDING' OR validation_status IS NULL
