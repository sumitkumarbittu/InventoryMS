from database import db
from datetime import datetime, date
import logging

class BaseModel:
    """Base model class with common database operations"""
    
    @classmethod
    def get_all(cls, table_name, limit=None, offset=None):
        """Get all records from table"""
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def get_by_id(cls, table_name, id_field, record_id):
        """Get record by ID"""
        query = f"SELECT * FROM {table_name} WHERE {id_field} = %s"
        return db.execute_query(query, (record_id,), fetch=True)
    
    @classmethod
    def create(cls, table_name, data):
        """Create new record"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return db.execute_query(query, list(data.values()))
    
    @classmethod
    def update(cls, table_name, id_field, record_id, data):
        """Update record by ID"""
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_field} = %s"
        params = list(data.values()) + [record_id]
        return db.execute_query(query, params)
    
    @classmethod
    def delete(cls, table_name, id_field, record_id):
        """Delete record by ID"""
        query = f"DELETE FROM {table_name} WHERE {id_field} = %s"
        return db.execute_query(query, (record_id,))

class Vendor(BaseModel):
    """Vendor model"""
    
    @classmethod
    def get_vendors_with_stats(cls):
        """Get vendors with performance statistics"""
        query = """
        SELECT v.*, 
               COUNT(DISTINCT p.product_id) as product_count,
               COUNT(DISTINCT o.order_id) as order_count,
               COALESCE(SUM(o.total_amount), 0) as total_sales
        FROM vendors v
        LEFT JOIN products p ON v.vendor_id = p.vendor_id
        LEFT JOIN orders o ON v.vendor_id = o.vendor_id
        GROUP BY v.vendor_id
        ORDER BY v.name
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def get_vendor_performance(cls, vendor_id):
        """Get vendor performance metrics"""
        query = """
        SELECT 
            v.name,
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(o.total_amount), 0) as total_sales,
            COALESCE(AVG(o.total_amount), 0) as avg_order_value,
            COUNT(DISTINCT CASE WHEN o.status = 'delivered' THEN o.order_id END) as delivered_orders,
            ROUND(COUNT(DISTINCT CASE WHEN o.status = 'delivered' THEN o.order_id END) * 100.0 / 
                  NULLIF(COUNT(DISTINCT o.order_id), 0), 2) as delivery_rate
        FROM vendors v
        LEFT JOIN orders o ON v.vendor_id = o.vendor_id
        WHERE v.vendor_id = %s
        GROUP BY v.vendor_id, v.name
        """
        return db.execute_query(query, (vendor_id,), fetch=True)

class Warehouse(BaseModel):
    """Warehouse model"""
    
    @classmethod
    def get_warehouse_utilization(cls):
        """Get warehouse utilization data"""
        query = """
        SELECT w.*, 
               COUNT(DISTINCT sl.product_id) as unique_products,
               SUM(sl.current_stock) as total_stock,
               ROUND((w.current_utilization / w.capacity) * 100, 2) as utilization_percentage
        FROM warehouses w
        LEFT JOIN stock_levels sl ON w.warehouse_id = sl.warehouse_id
        GROUP BY w.warehouse_id
        ORDER BY utilization_percentage DESC
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def update_utilization(cls, warehouse_id):
        """Update warehouse utilization based on current stock"""
        query = """
        UPDATE warehouses w
        SET current_utilization = (
            SELECT COALESCE(SUM(sl.current_stock), 0)
            FROM stock_levels sl
            WHERE sl.warehouse_id = w.warehouse_id
        )
        WHERE w.warehouse_id = %s
        """
        return db.execute_query(query, (warehouse_id,))

class Product(BaseModel):
    """Product model"""
    
    @classmethod
    def get_products_with_stock(cls):
        """Get products with current stock levels"""
        query = """
        SELECT p.*, 
               v.name as vendor_name,
               GROUP_CONCAT(
                   CONCAT(w.name, ':', sl.current_stock) 
                   SEPARATOR ';'
               ) as stock_by_warehouse
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        LEFT JOIN stock_levels sl ON p.product_id = sl.product_id
        LEFT JOIN warehouses w ON sl.warehouse_id = w.warehouse_id
        GROUP BY p.product_id
        ORDER BY p.name
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def get_low_stock_products(cls):
        """Get products with low stock"""
        query = """
        SELECT p.*, sl.current_stock, sl.warehouse_id, w.name as warehouse_name
        FROM products p
        JOIN stock_levels sl ON p.product_id = sl.product_id
        JOIN warehouses w ON sl.warehouse_id = w.warehouse_id
        WHERE sl.current_stock <= p.reorder_point
        ORDER BY (sl.current_stock - p.reorder_point) ASC
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def update_stock(cls, product_id, warehouse_id, quantity_change, operation='add'):
        """Update product stock level"""
        if operation == 'add':
            query = """
            INSERT INTO stock_levels (product_id, warehouse_id, current_stock)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            current_stock = current_stock + %s
            """
            params = (product_id, warehouse_id, quantity_change, quantity_change)
        else:  # subtract
            query = """
            UPDATE stock_levels 
            SET current_stock = GREATEST(0, current_stock - %s)
            WHERE product_id = %s AND warehouse_id = %s
            """
            params = (quantity_change, product_id, warehouse_id)
        
        result = db.execute_query(query, params)
        
        # Update warehouse utilization
        Warehouse.update_utilization(warehouse_id)
        
        return result

class Shipment(BaseModel):
    """Shipment model"""
    
    @classmethod
    def get_shipments_with_details(cls):
        """Get shipments with product details"""
        query = """
        SELECT s.*, 
               w.name as warehouse_name,
               v.name as vendor_name,
               COUNT(si.item_id) as item_count,
               COALESCE(SUM(si.total_price), 0) as total_value
        FROM shipments s
        LEFT JOIN warehouses w ON s.warehouse_id = w.warehouse_id
        LEFT JOIN vendors v ON s.vendor_id = v.vendor_id
        LEFT JOIN shipment_items si ON s.shipment_id = si.shipment_id
        GROUP BY s.shipment_id
        ORDER BY s.shipment_date DESC
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def get_shipment_items(cls, shipment_id):
        """Get items in a shipment"""
        query = """
        SELECT si.*, p.name as product_name, p.sku
        FROM shipment_items si
        JOIN products p ON si.product_id = p.product_id
        WHERE si.shipment_id = %s
        """
        return db.execute_query(query, (shipment_id,), fetch=True)
    
    @classmethod
    def create_shipment_with_items(cls, shipment_data, items_data):
        """Create shipment with items"""
        try:
            # Create shipment
            shipment_id = cls.create('shipments', shipment_data)
            
            # Add items
            for item in items_data:
                item['shipment_id'] = shipment_id
                cls.create('shipment_items', item)
                
                # Update stock if inbound shipment
                if shipment_data['type'] == 'inbound':
                    Product.update_stock(
                        item['product_id'], 
                        shipment_data['warehouse_id'], 
                        item['quantity'], 
                        'add'
                    )
            
            return shipment_id
        except Exception as e:
            logging.error(f"Error creating shipment: {str(e)}")
            raise e

class Order(BaseModel):
    """Order model"""
    
    @classmethod
    def get_orders_with_details(cls):
        """Get orders with vendor and item details"""
        query = """
        SELECT o.*, 
               v.name as vendor_name,
               COUNT(oi.item_id) as item_count,
               COALESCE(SUM(oi.total_price), 0) as calculated_total
        FROM orders o
        LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        ORDER BY o.order_date DESC
        """
        return db.execute_query(query, fetch=True)
    
    @classmethod
    def get_order_items(cls, order_id):
        """Get items in an order"""
        query = """
        SELECT oi.*, p.name as product_name, p.sku
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
        """
        return db.execute_query(query, (order_id,), fetch=True)
    
    @classmethod
    def create_order_with_items(cls, order_data, items_data):
        """Create order with items"""
        try:
            # Create order
            order_id = cls.create('orders', order_data)
            
            # Add items
            total_amount = 0
            for item in items_data:
                item['order_id'] = order_id
                item_total = item['quantity'] * item['unit_price']
                item['total_price'] = item_total
                total_amount += item_total
                cls.create('order_items', item)
            
            # Update order total
            cls.update('orders', 'order_id', order_id, {'total_amount': total_amount})
            
            return order_id
        except Exception as e:
            logging.error(f"Error creating order: {str(e)}")
            raise e

class ForecastingData(BaseModel):
    """Forecasting model"""
    
    @classmethod
    def get_sales_history(cls, product_id, warehouse_id, months=12):
        """Get sales history for forecasting"""
        query = """
        SELECT DATE_FORMAT(sale_date, '%Y-%m') as month, 
               SUM(quantity_sold) as total_quantity
        FROM sales_history
        WHERE product_id = %s AND warehouse_id = %s
        AND sale_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
        GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        ORDER BY month
        """
        return db.execute_query(query, (product_id, warehouse_id, months), fetch=True)
    
    @classmethod
    def save_forecast(cls, forecast_data):
        """Save forecasting data"""
        return cls.create('forecasting_data', forecast_data)
    
    @classmethod
    def get_forecast_history(cls, product_id, warehouse_id):
        """Get forecast history for a product"""
        query = """
        SELECT * FROM forecasting_data
        WHERE product_id = %s AND warehouse_id = %s
        ORDER BY period_start DESC
        """
        return db.execute_query(query, (product_id, warehouse_id), fetch=True)
