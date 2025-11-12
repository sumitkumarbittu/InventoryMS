-- Inventory Management System Database Schema
-- PostgreSQL Database Creation Script

-- Create database (if not exists - handled by createdb command)
-- CREATE DATABASE inventory_management;

-- Use the database
\c inventory_management;

-- 1. Vendors (Suppliers) Table
CREATE TABLE vendors (
    vendor_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    rating DECIMAL(3,2) DEFAULT 0.00 CHECK (rating >= 0 AND rating <= 5),
    product_categories TEXT,
    payment_terms VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Warehouses Table
CREATE TABLE warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    address TEXT,
    capacity INT NOT NULL,
    current_utilization INT DEFAULT 0,
    manager_name VARCHAR(255),
    manager_contact VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Products/Stock Table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    unit_price DECIMAL(10,2) NOT NULL,
    vendor_id INT,
    sku VARCHAR(100) UNIQUE,
    unit_of_measure VARCHAR(50) DEFAULT 'pieces',
    reorder_point INT DEFAULT 10,
    is_perishable BOOLEAN DEFAULT FALSE,
    expiry_days INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL
);

-- 4. Stock Levels Table (Many-to-many relationship between products and warehouses)
CREATE TABLE stock_levels (
    stock_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    current_stock INT DEFAULT 0,
    reserved_stock INT DEFAULT 0,
    available_stock INT GENERATED ALWAYS AS (current_stock - reserved_stock) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    UNIQUE KEY unique_product_warehouse (product_id, warehouse_id)
);

-- 5. Shipments Table
CREATE TABLE shipments (
    shipment_id INT PRIMARY KEY AUTO_INCREMENT,
    type ENUM('inbound', 'outbound') NOT NULL,
    warehouse_id INT NOT NULL,
    vendor_id INT,
    customer_name VARCHAR(255),
    carrier VARCHAR(255),
    tracking_number VARCHAR(100),
    status ENUM('pending', 'in_transit', 'delivered', 'cancelled') DEFAULT 'pending',
    shipment_date DATE,
    expected_delivery DATE,
    actual_delivery DATE,
    total_value DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL
);

-- 6. Shipment Items Table (Many-to-many relationship between shipments and products)
CREATE TABLE shipment_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    shipment_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- 7. Orders/Purchase Orders Table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id INT NOT NULL,
    order_type ENUM('purchase', 'sale') NOT NULL,
    order_date DATE NOT NULL,
    expected_delivery DATE,
    status ENUM('pending', 'confirmed', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(12,2) DEFAULT 0,
    payment_terms VARCHAR(100),
    payment_status ENUM('pending', 'partial', 'paid') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE CASCADE
);

-- 8. Order Items Table
CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- 9. Forecasting Data Table
CREATE TABLE forecasting_data (
    forecast_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    actual_demand INT,
    predicted_demand INT,
    forecast_method ENUM('moving_average', 'exponential_smoothing', 'trend_analysis') NOT NULL,
    confidence_level DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON DELETE CASCADE
);

-- 10. Historical Sales Data Table
CREATE TABLE sales_history (
    sale_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    sale_date DATE NOT NULL,
    quantity_sold INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_revenue DECIMAL(12,2) GENERATED ALWAYS AS (quantity_sold * unit_price) STORED,
    customer_type ENUM('retail', 'wholesale', 'online') DEFAULT 'retail',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_vendors_name ON vendors(name);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_vendor ON products(vendor_id);
CREATE INDEX idx_stock_levels_product ON stock_levels(product_id);
CREATE INDEX idx_stock_levels_warehouse ON stock_levels(warehouse_id);
CREATE INDEX idx_shipments_type ON shipments(type);
CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_orders_vendor ON orders(vendor_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_sales_history_date ON sales_history(sale_date);
CREATE INDEX idx_forecasting_product_warehouse ON forecasting_data(product_id, warehouse_id);

-- Views for common queries
CREATE VIEW low_stock_products AS
SELECT 
    p.product_id,
    p.name,
    p.category,
    p.reorder_point,
    sl.current_stock,
    sl.warehouse_id,
    w.name as warehouse_name,
    v.name as vendor_name
FROM products p
JOIN stock_levels sl ON p.product_id = sl.product_id
JOIN warehouses w ON sl.warehouse_id = w.warehouse_id
LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE sl.current_stock <= p.reorder_point;

CREATE VIEW warehouse_utilization AS
SELECT 
    w.warehouse_id,
    w.name,
    w.capacity,
    w.current_utilization,
    ROUND((w.current_utilization / w.capacity) * 100, 2) as utilization_percentage
FROM warehouses w;

-- Insert sample data
INSERT INTO vendors (name, contact_person, email, phone, address, rating, product_categories) VALUES
('TechSupply Co.', 'John Smith', 'john@techsupply.com', '+1-555-0101', '123 Tech Street, Silicon Valley, CA', 4.5, 'Electronics, Computer Parts'),
('Office Solutions Ltd.', 'Sarah Johnson', 'sarah@officesolutions.com', '+1-555-0102', '456 Business Ave, New York, NY', 4.2, 'Office Supplies, Furniture'),
('Industrial Parts Inc.', 'Mike Wilson', 'mike@industrialparts.com', '+1-555-0103', '789 Industrial Blvd, Detroit, MI', 4.8, 'Industrial Equipment, Tools');

INSERT INTO warehouses (name, location, address, capacity, manager_name, manager_contact) VALUES
('Main Warehouse', 'New York', '100 Warehouse St, New York, NY', 10000, 'Alice Brown', '+1-555-0201'),
('West Coast Hub', 'Los Angeles', '200 Storage Ave, Los Angeles, CA', 8000, 'Bob Davis', '+1-555-0202'),
('East Coast Distribution', 'Miami', '300 Distribution Rd, Miami, FL', 6000, 'Carol Green', '+1-555-0203');

INSERT INTO products (name, category, unit_price, vendor_id, sku, reorder_point, is_perishable) VALUES
('Laptop Computer', 'Electronics', 999.99, 1, 'LAP-001', 5, FALSE),
('Office Chair', 'Furniture', 299.99, 2, 'CHAIR-001', 10, FALSE),
('Industrial Drill', 'Tools', 199.99, 3, 'DRILL-001', 8, FALSE),
('Printer Paper', 'Office Supplies', 24.99, 2, 'PAPER-001', 50, FALSE),
('Fresh Produce Box', 'Food', 15.99, 1, 'PRODUCE-001', 20, TRUE);

-- Insert stock levels
INSERT INTO stock_levels (product_id, warehouse_id, current_stock) VALUES
(1, 1, 15), (1, 2, 8), (1, 3, 12),
(2, 1, 25), (2, 2, 18), (2, 3, 22),
(3, 1, 12), (3, 2, 6), (3, 3, 9),
(4, 1, 100), (4, 2, 75), (4, 3, 60),
(5, 1, 30), (5, 2, 25), (5, 3, 35);
