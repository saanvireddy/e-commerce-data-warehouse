{{
    config(
        materialized = 'view',
        tags = ['staging']
    )
}}

SELECT
    product_id,
    title,
    category,
    price,
    rating,
    review_count,
    description,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP as dbt_loaded_at
FROM
    {{ source('ecommerce', 'staging_products') }}
WHERE
    validation_status = 'PENDING' OR validation_status IS NULL
