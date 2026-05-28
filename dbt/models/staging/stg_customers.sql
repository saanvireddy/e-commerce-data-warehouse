{{
    config(
        materialized = 'view',
        tags = ['staging']
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    state,
    country,
    zip_code,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP as dbt_loaded_at
FROM
    {{ source('ecommerce', 'staging_customers') }}
WHERE
    validation_status = 'PENDING' OR validation_status IS NULL
