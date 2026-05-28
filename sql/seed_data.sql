-- ============================================================================
-- SAMPLE SEED DATA FOR TESTING
-- ============================================================================

-- Insert sample customers
INSERT INTO staging_customers (customer_id, first_name, last_name, email, phone, city, state, country, zip_code, created_at)
VALUES
    (1, 'John', 'Smith', 'john.smith@example.com', '555-0101', 'New York', 'NY', 'USA', '10001', CURRENT_TIMESTAMP - INTERVAL '90 days'),
    (2, 'Sarah', 'Johnson', 'sarah.johnson@example.com', '555-0102', 'Los Angeles', 'CA', 'USA', '90001', CURRENT_TIMESTAMP - INTERVAL '60 days'),
    (3, 'Michael', 'Williams', 'michael.williams@example.com', '555-0103', 'Chicago', 'IL', 'USA', '60601', CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (4, 'Emily', 'Brown', 'emily.brown@example.com', '555-0104', 'Houston', 'TX', 'USA', '77001', CURRENT_TIMESTAMP - INTERVAL '15 days'),
    (5, 'David', 'Jones', 'david.jones@example.com', '555-0105', 'Phoenix', 'AZ', 'USA', '85001', CURRENT_TIMESTAMP - INTERVAL '7 days')
ON CONFLICT (customer_id) DO NOTHING;

-- Insert sample products
INSERT INTO staging_products (product_id, title, category, price, rating, review_count, description, created_at)
VALUES
    (1, 'Premium Wireless Headphones', 'Electronics', 79.99, 4.5, 1250, 'High-quality wireless headphones with noise cancellation', CURRENT_TIMESTAMP - INTERVAL '180 days'),
    (2, 'Stainless Steel Water Bottle', 'Home & Kitchen', 34.99, 4.7, 890, 'Durable insulated water bottle keeps drinks hot or cold', CURRENT_TIMESTAMP - INTERVAL '150 days'),
    (3, 'Cotton T-Shirt', 'Clothing', 19.99, 4.3, 2100, 'Comfortable everyday cotton t-shirt', CURRENT_TIMESTAMP - INTERVAL '120 days'),
    (4, 'Portable Phone Charger', 'Electronics', 24.99, 4.6, 3450, 'Fast charging power bank with LED display', CURRENT_TIMESTAMP - INTERVAL '90 days'),
    (5, 'Yoga Mat', 'Sports & Outdoors', 29.99, 4.4, 1560, 'Non-slip exercise yoga mat with carrying strap', CURRENT_TIMESTAMP - INTERVAL '60 days'),
    (6, 'Desk Lamp', 'Home & Kitchen', 39.99, 4.5, 780, 'LED desk lamp with adjustable brightness', CURRENT_TIMESTAMP - INTERVAL '45 days'),
    (7, 'USB-C Cable', 'Electronics', 9.99, 4.2, 5200, 'Durable fast charging USB-C cable', CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (8, 'Coffee Maker', 'Home & Kitchen', 89.99, 4.6, 2340, 'Programmable coffee maker with thermal carafe', CURRENT_TIMESTAMP - INTERVAL '15 days')
ON CONFLICT (product_id) DO NOTHING;

-- Insert sample orders (from various dates)
INSERT INTO staging_orders (order_id, customer_id, product_id, quantity, amount, status, created_at)
VALUES
    (101, 1, 1, 1, 79.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '60 days'),
    (102, 2, 2, 2, 69.98, 'completed', CURRENT_TIMESTAMP - INTERVAL '55 days'),
    (103, 1, 3, 3, 59.97, 'completed', CURRENT_TIMESTAMP - INTERVAL '50 days'),
    (104, 3, 4, 1, 24.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '45 days'),
    (105, 2, 5, 1, 29.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '40 days'),
    (106, 4, 1, 1, 79.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '35 days'),
    (107, 5, 6, 2, 79.98, 'completed', CURRENT_TIMESTAMP - INTERVAL '30 days'),
    (108, 3, 7, 5, 49.95, 'completed', CURRENT_TIMESTAMP - INTERVAL '25 days'),
    (109, 1, 2, 1, 34.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '20 days'),
    (110, 4, 8, 1, 89.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '15 days'),
    (111, 2, 1, 1, 79.99, 'completed', CURRENT_TIMESTAMP - INTERVAL '10 days'),
    (112, 5, 3, 2, 39.98, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
    (113, 3, 4, 3, 74.97, 'pending', CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (114, 1, 5, 1, 29.99, 'pending', CURRENT_TIMESTAMP - INTERVAL '1 days')
ON CONFLICT (order_id) DO NOTHING;

-- Verify data loaded
SELECT 'staging_customers' as table_name, COUNT(*) as row_count FROM staging_customers
UNION ALL
SELECT 'staging_products', COUNT(*) FROM staging_products
UNION ALL
SELECT 'staging_orders', COUNT(*) FROM staging_orders;
