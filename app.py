from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from database import db
from models import Vendor, Warehouse, Product, Shipment, Order, ForecastingData
from forecasting import ForecastingEngine
from analytics import AnalyticsEngine
from config import Config
import logging
from datetime import datetime, date
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize engines
forecasting_engine = ForecastingEngine()
analytics_engine = AnalyticsEngine()

# Database connection
if not db.connect():
    logger.error("Failed to connect to database")

# ==================== VENDOR MANAGEMENT ====================

@app.route(f'{Config.API_PREFIX}/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors with statistics"""
    try:
        vendors = Vendor.get_vendors_with_stats()
        return jsonify({'success': True, 'data': vendors})
    except Exception as e:
        logger.error(f"Error getting vendors: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get specific vendor by ID"""
    try:
        vendor = Vendor.get_by_id('vendors', 'vendor_id', vendor_id)
        if vendor:
            performance = Vendor.get_vendor_performance(vendor_id)
            return jsonify({'success': True, 'data': vendor, 'performance': performance})
        return jsonify({'success': False, 'error': 'Vendor not found'}), 404
    except Exception as e:
        logger.error(f"Error getting vendor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/vendors', methods=['POST'])
def create_vendor():
    """Create new vendor"""
    try:
        data = request.get_json()
        required_fields = ['name', 'contact_person', 'email', 'phone']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        vendor_id = Vendor.create('vendors', data)
        return jsonify({'success': True, 'data': {'vendor_id': vendor_id}}), 201
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/vendors/<int:vendor_id>', methods=['PUT'])
def update_vendor(vendor_id):
    """Update vendor"""
    try:
        data = request.get_json()
        result = Vendor.update('vendors', 'vendor_id', vendor_id, data)
        if result > 0:
            return jsonify({'success': True, 'message': 'Vendor updated successfully'})
        return jsonify({'success': False, 'error': 'Vendor not found'}), 404
    except Exception as e:
        logger.error(f"Error updating vendor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/vendors/<int:vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    """Delete vendor"""
    try:
        result = Vendor.delete('vendors', 'vendor_id', vendor_id)
        if result > 0:
            return jsonify({'success': True, 'message': 'Vendor deleted successfully'})
        return jsonify({'success': False, 'error': 'Vendor not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting vendor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== WAREHOUSE MANAGEMENT ====================

@app.route(f'{Config.API_PREFIX}/warehouses', methods=['GET'])
def get_warehouses():
    """Get all warehouses with utilization data"""
    try:
        warehouses = Warehouse.get_warehouse_utilization()
        return jsonify({'success': True, 'data': warehouses})
    except Exception as e:
        logger.error(f"Error getting warehouses: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/warehouses/<int:warehouse_id>', methods=['GET'])
def get_warehouse(warehouse_id):
    """Get specific warehouse by ID"""
    try:
        warehouse = Warehouse.get_by_id('warehouses', 'warehouse_id', warehouse_id)
        if warehouse:
            return jsonify({'success': True, 'data': warehouse})
        return jsonify({'success': False, 'error': 'Warehouse not found'}), 404
    except Exception as e:
        logger.error(f"Error getting warehouse: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/warehouses', methods=['POST'])
def create_warehouse():
    """Create new warehouse"""
    try:
        data = request.get_json()
        required_fields = ['name', 'location', 'capacity']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        warehouse_id = Warehouse.create('warehouses', data)
        return jsonify({'success': True, 'data': {'warehouse_id': warehouse_id}}), 201
    except Exception as e:
        logger.error(f"Error creating warehouse: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/warehouses/<int:warehouse_id>', methods=['PUT'])
def update_warehouse(warehouse_id):
    """Update warehouse"""
    try:
        data = request.get_json()
        result = Warehouse.update('warehouses', 'warehouse_id', warehouse_id, data)
        if result > 0:
            return jsonify({'success': True, 'message': 'Warehouse updated successfully'})
        return jsonify({'success': False, 'error': 'Warehouse not found'}), 404
    except Exception as e:
        logger.error(f"Error updating warehouse: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== PRODUCT MANAGEMENT ====================

@app.route(f'{Config.API_PREFIX}/products', methods=['GET'])
def get_products():
    """Get all products with stock information"""
    try:
        products = Product.get_products_with_stock()
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product by ID"""
    try:
        product = Product.get_by_id('products', 'product_id', product_id)
        if product:
            return jsonify({'success': True, 'data': product})
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/products', methods=['POST'])
def create_product():
    """Create new product"""
    try:
        data = request.get_json()
        required_fields = ['name', 'category', 'unit_price', 'vendor_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        product_id = Product.create('products', data)
        return jsonify({'success': True, 'data': {'product_id': product_id}}), 201
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product"""
    try:
        data = request.get_json()
        result = Product.update('products', 'product_id', product_id, data)
        if result > 0:
            return jsonify({'success': True, 'message': 'Product updated successfully'})
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/products/<int:product_id>/stock', methods=['POST'])
def update_product_stock():
    """Update product stock level"""
    try:
        data = request.get_json()
        product_id = request.view_args['product_id']
        warehouse_id = data.get('warehouse_id')
        quantity = data.get('quantity')
        operation = data.get('operation', 'add')
        
        if not all([warehouse_id, quantity]):
            return jsonify({'success': False, 'error': 'Missing warehouse_id or quantity'}), 400
        
        result = Product.update_stock(product_id, warehouse_id, quantity, operation)
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SHIPMENT MANAGEMENT ====================

@app.route(f'{Config.API_PREFIX}/shipments', methods=['GET'])
def get_shipments():
    """Get all shipments with details"""
    try:
        shipments = Shipment.get_shipments_with_details()
        return jsonify({'success': True, 'data': shipments})
    except Exception as e:
        logger.error(f"Error getting shipments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/shipments/<int:shipment_id>', methods=['GET'])
def get_shipment(shipment_id):
    """Get specific shipment with items"""
    try:
        shipment = Shipment.get_by_id('shipments', 'shipment_id', shipment_id)
        if shipment:
            items = Shipment.get_shipment_items(shipment_id)
            return jsonify({'success': True, 'data': shipment, 'items': items})
        return jsonify({'success': False, 'error': 'Shipment not found'}), 404
    except Exception as e:
        logger.error(f"Error getting shipment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/shipments', methods=['POST'])
def create_shipment():
    """Create new shipment with items"""
    try:
        data = request.get_json()
        shipment_data = data.get('shipment')
        items_data = data.get('items', [])
        
        if not shipment_data:
            return jsonify({'success': False, 'error': 'Missing shipment data'}), 400
        
        required_fields = ['type', 'warehouse_id']
        for field in required_fields:
            if field not in shipment_data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        shipment_id = Shipment.create_shipment_with_items(shipment_data, items_data)
        return jsonify({'success': True, 'data': {'shipment_id': shipment_id}}), 201
    except Exception as e:
        logger.error(f"Error creating shipment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ORDER MANAGEMENT ====================

@app.route(f'{Config.API_PREFIX}/orders', methods=['GET'])
def get_orders():
    """Get all orders with details"""
    try:
        orders = Order.get_orders_with_details()
        return jsonify({'success': True, 'data': orders})
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific order with items"""
    try:
        order = Order.get_by_id('orders', 'order_id', order_id)
        if order:
            items = Order.get_order_items(order_id)
            return jsonify({'success': True, 'data': order, 'items': items})
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/orders', methods=['POST'])
def create_order():
    """Create new order with items"""
    try:
        data = request.get_json()
        order_data = data.get('order')
        items_data = data.get('items', [])
        
        if not order_data:
            return jsonify({'success': False, 'error': 'Missing order data'}), 400
        
        required_fields = ['vendor_id', 'order_type', 'order_date']
        for field in required_fields:
            if field not in order_data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        order_id = Order.create_order_with_items(order_data, items_data)
        return jsonify({'success': True, 'data': {'order_id': order_id}}), 201
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== FORECASTING ====================

@app.route(f'{Config.API_PREFIX}/forecast/generate', methods=['POST'])
def generate_forecast():
    """Generate demand forecast for a product"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        warehouse_id = data.get('warehouse_id')
        periods = data.get('periods', 12)
        method = data.get('method', 'ensemble')
        
        if not all([product_id, warehouse_id]):
            return jsonify({'success': False, 'error': 'Missing product_id or warehouse_id'}), 400
        
        forecast_data, message = forecasting_engine.generate_forecast(
            product_id, warehouse_id, periods, method
        )
        
        if forecast_data:
            # Save forecast to database
            for forecast in forecast_data:
                ForecastingData.save_forecast(forecast)
            
            return jsonify({'success': True, 'data': forecast_data, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/forecast/evaluate', methods=['POST'])
def evaluate_forecast():
    """Evaluate forecast accuracy"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        warehouse_id = data.get('warehouse_id')
        method = data.get('method', 'ensemble')
        
        if not all([product_id, warehouse_id]):
            return jsonify({'success': False, 'error': 'Missing product_id or warehouse_id'}), 400
        
        metrics, message = forecasting_engine.evaluate_forecast_accuracy(
            product_id, warehouse_id, method
        )
        
        if metrics:
            return jsonify({'success': True, 'data': metrics, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f"Error evaluating forecast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ANALYTICS & REPORTS ====================

@app.route(f'{Config.API_PREFIX}/analytics/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get executive dashboard data"""
    try:
        dashboard_data = analytics_engine.generate_executive_dashboard_data()
        return jsonify({'success': True, 'data': dashboard_data})
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/low-stock', methods=['GET'])
def get_low_stock_alerts():
    """Get low stock alerts"""
    try:
        alerts = analytics_engine.get_low_stock_alerts()
        return jsonify({'success': True, 'data': alerts})
    except Exception as e:
        logger.error(f"Error getting low stock alerts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/vendor-performance', methods=['GET'])
def get_vendor_performance():
    """Get vendor performance analysis"""
    try:
        months = request.args.get('months', 12, type=int)
        performance = analytics_engine.get_vendor_performance_analysis(months)
        return jsonify({'success': True, 'data': performance})
    except Exception as e:
        logger.error(f"Error getting vendor performance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/warehouse-utilization', methods=['GET'])
def get_warehouse_utilization():
    """Get warehouse utilization analysis"""
    try:
        utilization = analytics_engine.get_warehouse_utilization_analysis()
        return jsonify({'success': True, 'data': utilization})
    except Exception as e:
        logger.error(f"Error getting warehouse utilization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/demand-supply', methods=['GET'])
def get_demand_supply_analysis():
    """Get demand vs supply analysis"""
    try:
        months = request.args.get('months', 6, type=int)
        analysis = analytics_engine.get_demand_vs_supply_analysis(months)
        return jsonify({'success': True, 'data': analysis})
    except Exception as e:
        logger.error(f"Error getting demand-supply analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/sales-trends', methods=['GET'])
def get_sales_trends():
    """Get sales trend analysis"""
    try:
        months = request.args.get('months', 12, type=int)
        trends = analytics_engine.get_sales_trend_analysis(months)
        return jsonify({'success': True, 'data': trends})
    except Exception as e:
        logger.error(f"Error getting sales trends: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/top-products', methods=['GET'])
def get_top_products():
    """Get top performing products"""
    try:
        months = request.args.get('months', 6, type=int)
        limit = request.args.get('limit', 20, type=int)
        products = analytics_engine.get_top_performing_products(months, limit)
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        logger.error(f"Error getting top products: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route(f'{Config.API_PREFIX}/analytics/inventory-turnover', methods=['GET'])
def get_inventory_turnover():
    """Get inventory turnover analysis"""
    try:
        months = request.args.get('months', 12, type=int)
        turnover = analytics_engine.get_inventory_turnover_analysis(months)
        return jsonify({'success': True, 'data': turnover})
    except Exception as e:
        logger.error(f"Error getting inventory turnover: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

# ==================== HEALTH CHECK ====================

@app.route(f'{Config.API_PREFIX}/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        if db.connection:
            db.execute_query("SELECT 1")
            db_status = 'connected'
        else:
            db_status = 'disconnected'
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)
