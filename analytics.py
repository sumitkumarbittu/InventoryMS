import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models import db
import logging

class AnalyticsEngine:
    """Analytics engine for inventory management insights"""
    
    def __init__(self):
        self.db = db
    
    def get_low_stock_alerts(self):
        """Get low stock alerts with detailed information"""
        query = """
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            p.sku,
            p.reorder_point,
            sl.current_stock,
            sl.warehouse_id,
            w.name as warehouse_name,
            v.name as vendor_name,
            v.email as vendor_email,
            v.phone as vendor_phone,
            CASE 
                WHEN sl.current_stock = 0 THEN 'Out of Stock'
                WHEN sl.current_stock <= p.reorder_point * 0.5 THEN 'Critical'
                WHEN sl.current_stock <= p.reorder_point THEN 'Low'
                ELSE 'Normal'
            END as alert_level,
            ROUND((sl.current_stock::numeric / NULLIF(p.reorder_point, 0)) * 100, 2) as stock_percentage
        FROM products p
        JOIN stock_levels sl ON p.product_id = sl.product_id
        JOIN warehouses w ON sl.warehouse_id = w.warehouse_id
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        WHERE sl.current_stock <= p.reorder_point
        ORDER BY (sl.current_stock - p.reorder_point) ASC, p.name
        """
        return self.db.execute_query(query, fetch=True)
    
    def get_vendor_performance_analysis(self, months=12):
        """Analyze vendor performance metrics"""
        query = """
        SELECT 
            v.vendor_id,
            v.name as vendor_name,
            v.rating,
            COUNT(DISTINCT o.order_id) as total_orders,
            COALESCE(SUM(o.total_amount), 0) as total_sales,
            COALESCE(AVG(o.total_amount), 0) as avg_order_value,
            COUNT(DISTINCT CASE WHEN o.status = 'delivered' THEN o.order_id END) as delivered_orders,
            COUNT(DISTINCT CASE WHEN o.status = 'cancelled' THEN o.order_id END) as cancelled_orders,
            ROUND(COUNT(DISTINCT CASE WHEN o.status = 'delivered' THEN o.order_id END) * 100.0 / 
                  NULLIF(COUNT(DISTINCT o.order_id), 0), 2) as delivery_rate,
            ROUND(COUNT(DISTINCT CASE WHEN o.status = 'cancelled' THEN o.order_id END) * 100.0 / 
                  NULLIF(COUNT(DISTINCT o.order_id), 0), 2) as cancellation_rate,
            COUNT(DISTINCT p.product_id) as product_count,
            COALESCE(AVG(EXTRACT(EPOCH FROM (o.actual_delivery - o.order_date)) / 86400.0), 0) as avg_delivery_days
        FROM vendors v
        LEFT JOIN orders o ON v.vendor_id = o.vendor_id 
            AND o.order_date >= CURRENT_DATE - make_interval(months => %s)
        LEFT JOIN products p ON v.vendor_id = p.vendor_id
        GROUP BY v.vendor_id, v.name, v.rating
        ORDER BY total_sales DESC
        """
        return self.db.execute_query(query, (months,), fetch=True)
    
    def get_warehouse_utilization_analysis(self):
        """Analyze warehouse utilization and capacity"""
        query = """
        SELECT 
            w.warehouse_id,
            w.name as warehouse_name,
            w.location,
            w.capacity,
            w.current_utilization,
            ROUND((w.current_utilization::numeric / NULLIF(w.capacity, 0)) * 100, 2) as utilization_percentage,
            COUNT(DISTINCT sl.product_id) as unique_products,
            SUM(sl.current_stock) as total_stock,
            AVG(sl.current_stock) as avg_stock_per_product,
            CASE 
                WHEN (w.current_utilization / w.capacity) > 0.9 THEN 'Critical'
                WHEN (w.current_utilization / w.capacity) > 0.8 THEN 'High'
                WHEN (w.current_utilization / w.capacity) > 0.6 THEN 'Medium'
                ELSE 'Low'
            END as utilization_status
        FROM warehouses w
        LEFT JOIN stock_levels sl ON w.warehouse_id = sl.warehouse_id
        GROUP BY w.warehouse_id, w.name, w.location, w.capacity, w.current_utilization
        ORDER BY utilization_percentage DESC
        """
        return self.db.execute_query(query, fetch=True)
    
    def get_demand_vs_supply_analysis(self, months=6):
        """Analyze demand vs supply trends"""
        query = """
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            SUM(sl.current_stock) as total_current_stock,
            SUM(p.reorder_point) as total_reorder_point,
            COALESCE(SUM(sh.quantity_sold), 0) as total_demand,
            COALESCE(AVG(sh.quantity_sold), 0) as avg_monthly_demand,
            COALESCE(SUM(si.quantity), 0) as total_supply,
            CASE 
                WHEN COALESCE(SUM(sh.quantity_sold), 0) = 0 THEN 0
                ELSE ROUND((COALESCE(SUM(si.quantity), 0) / COALESCE(SUM(sh.quantity_sold), 0)) * 100, 2)
            END as supply_demand_ratio,
            CASE 
                WHEN SUM(sl.current_stock) = 0 THEN 'Out of Stock'
                WHEN SUM(sl.current_stock) < COALESCE(AVG(sh.quantity_sold), 0) THEN 'Understocked'
                WHEN SUM(sl.current_stock) > COALESCE(AVG(sh.quantity_sold), 0) * 2 THEN 'Overstocked'
                ELSE 'Balanced'
            END as stock_status
        FROM products p
        LEFT JOIN stock_levels sl ON p.product_id = sl.product_id
        LEFT JOIN sales_history sh ON p.product_id = sh.product_id 
            AND sh.sale_date >= CURRENT_DATE - make_interval(months => %s)
        LEFT JOIN shipment_items si ON p.product_id = si.product_id
        LEFT JOIN shipments s ON si.shipment_id = s.shipment_id 
            AND s.type = 'inbound' 
            AND s.shipment_date >= CURRENT_DATE - make_interval(months => %s)
        GROUP BY p.product_id, p.name, p.category
        HAVING total_current_stock > 0 OR total_demand > 0
        ORDER BY total_demand DESC
        """
        return self.db.execute_query(query, (months, months), fetch=True)
    
    def get_sales_trend_analysis(self, months=12):
        """Analyze sales trends by product and category"""
        query = """
        SELECT 
            to_char(sh.sale_date, 'YYYY-MM') as month, 
            p.category,
            COUNT(DISTINCT sh.product_id) as products_sold,
            SUM(sh.quantity_sold) as total_quantity,
            SUM(sh.total_revenue) as total_revenue,
            AVG(sh.quantity_sold) as avg_quantity_per_sale,
            AVG(sh.unit_price) as avg_unit_price
        FROM sales_history sh
        JOIN products p ON sh.product_id = p.product_id
        WHERE sh.sale_date >= CURRENT_DATE - make_interval(months => %s)
        GROUP BY to_char(sh.sale_date, 'YYYY-MM'), p.category
        ORDER BY month
        """
        return self.db.execute_query(query, (months,), fetch=True)
    
    def get_top_performing_products(self, months=6, limit=20):
        """Get top performing products by sales"""
        query = """
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            p.sku,
            SUM(sh.quantity_sold) as total_quantity_sold,
            SUM(sh.total_revenue) as total_revenue,
            AVG(sh.unit_price) as avg_unit_price,
            COUNT(DISTINCT sh.sale_date) as days_sold,
            ROUND(SUM(sh.quantity_sold) / COUNT(DISTINCT sh.sale_date), 2) as avg_daily_sales,
            SUM(sl.current_stock) as current_stock,
            p.reorder_point
        FROM products p
        LEFT JOIN sales_history sh ON p.product_id = sh.product_id 
            AND sh.sale_date >= CURRENT_DATE - make_interval(months => %s)
        LEFT JOIN stock_levels sl ON p.product_id = sl.product_id
        GROUP BY p.product_id, p.name, p.category, p.sku, p.reorder_point
        HAVING total_quantity_sold > 0
        ORDER BY total_revenue DESC
        LIMIT %s
        """
        return self.db.execute_query(query, (months, limit), fetch=True)
    
    def get_inventory_turnover_analysis(self, months=12):
        """Calculate inventory turnover rates"""
        query = """
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            COALESCE(SUM(sh.quantity_sold), 0) as total_sales,
            COALESCE(AVG(sl.current_stock), 0) as avg_inventory,
            CASE 
                WHEN COALESCE(AVG(sl.current_stock), 0) = 0 THEN 0
                ELSE ROUND(COALESCE(SUM(sh.quantity_sold), 0)::numeric / NULLIF(COALESCE(AVG(sl.current_stock), 0), 0), 2)
            END as turnover_rate,
            CASE 
                WHEN COALESCE(AVG(sl.current_stock), 0) = 0 THEN 0
                ELSE ROUND(365 / NULLIF(COALESCE(SUM(sh.quantity_sold), 0)::numeric / NULLIF(COALESCE(AVG(sl.current_stock), 0), 0), 0), 0)
            END as days_in_inventory
        FROM products p
        LEFT JOIN sales_history sh ON p.product_id = sh.product_id 
            AND sh.sale_date >= CURRENT_DATE - make_interval(months => %s)
        LEFT JOIN stock_levels sl ON p.product_id = sl.product_id
        GROUP BY p.product_id, p.name, p.category
        HAVING total_sales > 0
        ORDER BY turnover_rate DESC
        """
        return self.db.execute_query(query, (months,), fetch=True)
    
    def get_cost_analysis(self, months=6):
        """Analyze inventory costs and valuation"""
        query = """
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            p.unit_price,
            SUM(sl.current_stock) as total_stock,
            SUM(sl.current_stock * p.unit_price) as total_value,
            COALESCE(AVG(sh.unit_price), 0) as avg_selling_price,
            COALESCE(AVG(sh.unit_price) - p.unit_price, 0) as avg_profit_per_unit,
            COALESCE((AVG(sh.unit_price) - p.unit_price) / p.unit_price * 100, 0) as profit_margin_percent
        FROM products p
        LEFT JOIN stock_levels sl ON p.product_id = sl.product_id
        LEFT JOIN sales_history sh ON p.product_id = sh.product_id 
            AND sh.sale_date >= CURRENT_DATE - make_interval(months => %s)
        GROUP BY p.product_id, p.name, p.category, p.unit_price
        HAVING total_stock > 0
        ORDER BY total_value DESC
        """
        return self.db.execute_query(query, (months,), fetch=True)
    
    def get_shipment_performance_analysis(self, months=6):
        """Analyze shipment performance and delivery metrics"""
        query = """
        SELECT 
            s.shipment_id,
            s.type,
            s.status,
            w.name as warehouse_name,
            v.name as vendor_name,
            s.shipment_date,
            s.expected_delivery,
            s.actual_delivery,
            CASE 
                WHEN s.actual_delivery IS NOT NULL AND s.expected_delivery IS NOT NULL THEN
                    ROUND(EXTRACT(EPOCH FROM (s.actual_delivery - s.expected_delivery)) / 86400.0)
                ELSE NULL
            END as delivery_delay_days,
            COUNT(si.item_id) as item_count,
            SUM(si.total_price) as total_value,
            s.carrier
        FROM shipments s
        LEFT JOIN warehouses w ON s.warehouse_id = w.warehouse_id
        LEFT JOIN vendors v ON s.vendor_id = v.vendor_id
        LEFT JOIN shipment_items si ON s.shipment_id = si.shipment_id
        WHERE s.shipment_date >= CURRENT_DATE - make_interval(months => %s)
        GROUP BY s.shipment_id, s.type, s.status, w.name, v.name, s.shipment_date, 
                 s.expected_delivery, s.actual_delivery, s.carrier
        ORDER BY s.shipment_date DESC
        """
        return self.db.execute_query(query, (months,), fetch=True)
    
    def generate_executive_dashboard_data(self):
        """Generate comprehensive dashboard data for executives"""
        dashboard_data = {
            'low_stock_alerts': self.get_low_stock_alerts(),
            'vendor_performance': self.get_vendor_performance_analysis(6),
            'warehouse_utilization': self.get_warehouse_utilization_analysis(),
            'top_products': self.get_top_performing_products(6, 10),
            'inventory_turnover': self.get_inventory_turnover_analysis(12),
            'cost_analysis': self.get_cost_analysis(6),
            'shipment_performance': self.get_shipment_performance_analysis(6)
        }
        
        # Calculate summary metrics
        summary_metrics = self._calculate_summary_metrics(dashboard_data)
        dashboard_data['summary_metrics'] = summary_metrics
        
        return dashboard_data
    
    def _calculate_summary_metrics(self, dashboard_data):
        """Calculate summary metrics for dashboard"""
        try:
            # Total inventory value
            total_inventory_value = sum(item['total_value'] for item in dashboard_data['cost_analysis'])
            
            # Low stock count
            low_stock_count = len(dashboard_data['low_stock_alerts'])
            
            # Average warehouse utilization
            warehouse_util = dashboard_data['warehouse_utilization']
            avg_utilization = np.mean([w['utilization_percentage'] for w in warehouse_util]) if warehouse_util else 0
            
            # Total products
            total_products = len(dashboard_data['cost_analysis'])
            
            # Critical warehouse count
            critical_warehouses = len([w for w in warehouse_util if w['utilization_percentage'] > 90])
            
            # Average vendor rating
            vendor_perf = dashboard_data['vendor_performance']
            avg_vendor_rating = np.mean([v['rating'] for v in vendor_perf if v['rating']]) if vendor_perf else 0
            
            return {
                'total_inventory_value': round(total_inventory_value, 2),
                'low_stock_count': low_stock_count,
                'avg_warehouse_utilization': round(avg_utilization, 2),
                'total_products': total_products,
                'critical_warehouses': critical_warehouses,
                'avg_vendor_rating': round(avg_vendor_rating, 2)
            }
        except Exception as e:
            logging.error(f"Error calculating summary metrics: {str(e)}")
            return {}
