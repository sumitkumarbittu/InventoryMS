# Inventory Management System

A comprehensive inventory management system built with Python Flask backend and HTML/CSS frontend, featuring advanced forecasting capabilities and real-time analytics.

## ⚡ Quick Start

**Want to get running immediately?** Follow these steps:

1. **Start MySQL**: `brew services start mysql` (macOS) or `sudo systemctl start mysql` (Linux)
2. **Setup Database**: 
   ```bash
   mysql -u root -p -e "CREATE DATABASE inventory_management; CREATE USER 'inventory_user'@'localhost' IDENTIFIED BY 'inventory_pass'; GRANT ALL PRIVILEGES ON inventory_management.* TO 'inventory_user'@'localhost'; FLUSH PRIVILEGES;"
   mysql -u inventory_user -pinventory_pass inventory_management < database_schema.sql
   ```
3. **Install Dependencies**: `pip install -r requirements.txt && pip install cryptography`
4. **Configure Environment**: `cp env.example .env` (credentials are already set)
5. **Run Application**: `source venv/bin/activate && python app.py`
6. **Open Browser**: Navigate to `http://localhost:5001`

**That's it!** You can now add vendors, warehouses, products, shipments, and orders through the web interface.

> **Note**: For detailed setup instructions and troubleshooting, see the full Installation & Setup section below.

## 🚀 Features

### Core Entities
- **Vendors (Suppliers)** - Manage supplier information, ratings, and performance tracking
- **Warehouses** - Track multiple warehouse locations with capacity management
- **Products/Stock** - Complete product catalog with stock levels across warehouses
- **Shipments** - Track both inbound and outbound shipments with carrier information
- **Orders** - Manage purchase orders and sales orders with payment tracking
- **Forecasting Data** - Historical sales data and demand predictions

### Key Functionalities
- **Vendor Management** - Add/update vendor details, track performance metrics
- **Warehouse Management** - Monitor capacity utilization and stock distribution
- **Inventory Tracking** - Real-time stock levels with reorder alerts
- **Shipment Management** - Track incoming and outgoing shipments
- **Advanced Forecasting** - Multiple forecasting algorithms (Moving Average, Exponential Smoothing, Trend Analysis, Seasonal, Ensemble)
- **Analytics & Reports** - Comprehensive dashboards with key performance indicators
- **Low Stock Alerts** - Automated notifications for products below reorder points

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework with template rendering
- **PyMySQL** - MySQL database connector
- **Pandas & NumPy** - Data processing
- **Scikit-learn** - Machine learning for forecasting
- **Matplotlib & Seaborn** - Data visualization

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with Flexbox and Grid
- **JavaScript (ES6+)** - Interactive functionality
- **Font Awesome** - Icons
- **Responsive Design** - Mobile-first approach

### Database
- **MySQL 8.0+** - Primary database

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- Git

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd InventoryMS
```

### 2. Database Setup

#### Start MySQL Service
```bash
# On macOS
brew services start mysql
# or if that fails, start manually:
mysqld_safe --user=mysql &

# On Linux
sudo systemctl start mysql
```

#### Create Database and User
```bash
# Connect to MySQL as root
mysql -u root -p

# Create database
CREATE DATABASE inventory_management;

# Create dedicated user (recommended)
CREATE USER 'inventory_user'@'localhost' IDENTIFIED BY 'inventory_pass';
GRANT ALL PRIVILEGES ON inventory_management.* TO 'inventory_user'@'localhost';
FLUSH PRIVILEGES;
exit
```

#### Import Database Schema
```bash
# Import the schema
mysql -u inventory_user -pinventory_pass inventory_management < database_schema.sql

# Add missing column for analytics (if needed)
mysql -u inventory_user -pinventory_pass inventory_management -e "ALTER TABLE orders ADD COLUMN actual_delivery DATE AFTER expected_delivery;"
```

### 3. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional required packages
pip install cryptography

# Create environment file
cp env.example .env

# Update .env with correct database credentials
# The .env file should contain:
# DB_HOST=localhost
# DB_USER=inventory_user
# DB_PASSWORD=inventory_pass
# DB_NAME=inventory_management
# DB_PORT=3306
```

### 4. Run the Application
```bash
# Start the Flask application
source venv/bin/activate
python app.py
```

The application will be available at `http://localhost:5001`

### 5. Verify Installation
```bash
# Test database connection
curl http://localhost:5001/api/v1/health

# Test API endpoints
curl http://localhost:5001/api/v1/vendors
```

## 📊 API Endpoints

### Vendors
- `GET /api/v1/vendors` - Get all vendors
- `POST /api/v1/vendors` - Create new vendor
- `PUT /api/v1/vendors/{id}` - Update vendor
- `DELETE /api/v1/vendors/{id}` - Delete vendor

### Warehouses
- `GET /api/v1/warehouses` - Get all warehouses
- `POST /api/v1/warehouses` - Create new warehouse
- `PUT /api/v1/warehouses/{id}` - Update warehouse
- `DELETE /api/v1/warehouses/{id}` - Delete warehouse

### Products
- `GET /api/v1/products` - Get all products
- `POST /api/v1/products` - Create new product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product
- `POST /api/v1/products/{id}/stock` - Update stock level

### Shipments
- `GET /api/v1/shipments` - Get all shipments
- `POST /api/v1/shipments` - Create new shipment
- `GET /api/v1/shipments/{id}` - Get shipment details

### Orders
- `GET /api/v1/orders` - Get all orders
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders/{id}` - Get order details

### Forecasting
- `POST /api/v1/forecast/generate` - Generate demand forecast
- `POST /api/v1/forecast/evaluate` - Evaluate forecast accuracy

### Analytics
- `GET /api/v1/analytics/dashboard` - Get dashboard data
- `GET /api/v1/analytics/low-stock` - Get low stock alerts
- `GET /api/v1/analytics/vendor-performance` - Get vendor performance
- `GET /api/v1/analytics/warehouse-utilization` - Get warehouse utilization

## 🎯 Usage

### Quick Start
1. **Start the application:**
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5001`

3. **Configure database:**
   Edit `.env` file with your MySQL credentials

### Features Overview

### 1. Dashboard
- View key metrics and KPIs
- Monitor low stock alerts
- Track warehouse utilization
- Analyze sales trends

### 2. Vendor Management
- Add and manage suppliers
- Track vendor performance
- Monitor delivery rates and ratings

### 3. Warehouse Management
- Set up multiple warehouse locations
- Monitor capacity utilization
- Track stock distribution

### 4. Product Management
- Create product catalog
- Set reorder points
- Track stock levels across warehouses
- Manage product categories

### 5. Shipment Tracking
- Track inbound shipments from vendors
- Monitor outbound deliveries
- Update shipment status
- Generate tracking reports

### 6. Order Management
- Create purchase orders
- Track order status
- Monitor payment terms
- Generate order reports

### 7. Demand Forecasting
- Generate demand predictions using multiple algorithms
- Evaluate forecast accuracy
- Compare different forecasting methods
- Export forecast data

### 8. Analytics & Reporting
- View comprehensive analytics dashboard
- Analyze vendor performance
- Monitor inventory turnover
- Track sales trends by category

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=inventory_user
DB_PASSWORD=inventory_pass
DB_NAME=inventory_management
DB_PORT=3306

# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True

# API Configuration
API_PREFIX=/api/v1
```

**Important**: Use the dedicated `inventory_user` instead of root for better security and stability.

### Database Configuration
The system uses MySQL as the primary database. Make sure to:
1. Create the database using the provided schema
2. Update connection credentials in the `.env` file
3. Ensure proper permissions for the database user
4. Start MySQL service before running the application

### Port Configuration
- **Application:** http://localhost:5001
- **API:** http://localhost:5001/api/v1

## 📈 Forecasting Methods

The system supports multiple forecasting algorithms:

1. **Moving Average** - Simple average of recent data points
2. **Exponential Smoothing** - Weighted average with more emphasis on recent data
3. **Trend Analysis** - Linear regression for trend identification
4. **Seasonal Analysis** - Accounts for seasonal patterns
5. **Ensemble Method** - Combines multiple methods for optimal accuracy

## 🚨 Low Stock Alerts

The system automatically monitors stock levels and provides alerts when:
- Products are out of stock
- Stock falls below reorder point
- Critical stock levels are reached

## 📊 Analytics Features

- **Executive Dashboard** - High-level KPIs and metrics
- **Vendor Performance** - Delivery rates, ratings, and sales analysis
- **Warehouse Utilization** - Capacity monitoring and optimization
- **Inventory Turnover** - Stock movement analysis
- **Sales Trends** - Revenue and quantity analysis by category
- **Cost Analysis** - Inventory valuation and profit margins

## 🔒 Security Features

- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Error handling and logging

## 🚀 Deployment

### Production Deployment
1. Set `DEBUG=False` in environment variables
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure reverse proxy (e.g., Nginx)
4. Set up SSL certificates
5. Configure production database

### Quick Start Script
```bash
# Make the startup script executable
chmod +x start.sh

# Run the startup script
./start.sh
```

### Manual Start
```bash
# Start MySQL service
brew services start mysql  # macOS
# or
sudo systemctl start mysql  # Linux

# Start the application
source venv/bin/activate
python app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues and Solutions

#### 1. MySQL Connection Issues
**Problem**: `Can't connect to MySQL server` or `Access denied`
```bash
# Solution 1: Start MySQL service
brew services start mysql  # macOS
sudo systemctl start mysql  # Linux

# Solution 2: Start MySQL manually
mysqld_safe --user=mysql &

# Solution 3: Check MySQL status
ps aux | grep mysql
```

#### 2. Database Schema Issues
**Problem**: `Unknown column` errors
```bash
# Add missing columns
mysql -u inventory_user -pinventory_pass inventory_management -e "ALTER TABLE orders ADD COLUMN actual_delivery DATE AFTER expected_delivery;"
```

#### 3. Port Already in Use
**Problem**: `Address already in use` on port 5001
```bash
# Kill existing processes
lsof -ti:5001 | xargs kill -9
# or
pkill -f "python app.py"
```

#### 4. Python Package Issues
**Problem**: `cryptography` package missing
```bash
# Install required packages
pip install cryptography
pip install -r requirements.txt
```

#### 5. Database Connection Stability
**Problem**: Connection lost during queries
- The application now includes automatic reconnection
- Check MySQL service is running: `brew services list | grep mysql`
- Verify database user permissions

#### 6. Frontend Not Loading
**Problem**: Blank page or JavaScript errors
- Check browser console for errors
- Verify Flask app is running: `curl http://localhost:5001`
- Check static files are accessible: `curl http://localhost:5001/static/css/style.css`

### Health Checks
```bash
# Check application health
curl http://localhost:5001/api/v1/health

# Test database connection
curl http://localhost:5001/api/v1/vendors

# Check frontend
curl http://localhost:5001/
```

### Logs and Debugging
- Flask logs are displayed in the terminal where you run `python app.py`
- Database connection issues are logged with ERROR level
- API requests are logged with INFO level
- Enable DEBUG=True in `.env` for detailed error messages

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the API endpoints
- Check the application logs for specific error messages

## 🔄 Updates

### Version 2.1.0 (Current)
- **Fixed Database Connection Issues** - Improved stability and automatic reconnection
- **Enhanced Error Handling** - Better error messages and logging
- **Updated Database Schema** - Added missing columns for full functionality
- **Improved Setup Instructions** - Comprehensive installation guide
- **Added Troubleshooting Section** - Common issues and solutions
- **Security Improvements** - Dedicated database user instead of root
- **Package Dependencies** - Added cryptography package for MySQL authentication

### Version 2.0.0
- **Converted to HTML/CSS frontend** - Simplified deployment and maintenance
- **Single-page application** - No build process required
- **Responsive design** - Works on all devices
- **Port 5001** - Updated default port configuration
- **Enhanced UI** - Modern, clean interface with animations
- **Full CRUD Operations** - All modal forms implemented and functional

### Version 1.0.0
- Initial release with core functionality
- Basic CRUD operations for all entities
- Forecasting capabilities
- Analytics dashboard
- React frontend with modern UI

## 🎨 Frontend Features

### Modern UI Components
- **Responsive Navigation** - Collapsible sidebar with smooth transitions
- **Card-based Layout** - Clean information display
- **Interactive Tables** - Sortable, searchable data tables
- **Status Badges** - Color-coded status indicators
- **Modal Forms** - Easy data entry and editing
- **Loading States** - User feedback during operations
- **Notifications** - Toast messages for user actions

### Design System
- **Color Palette** - Professional gradient scheme
- **Typography** - Clean, readable fonts
- **Spacing** - Consistent margin and padding
- **Animations** - Smooth hover effects and transitions
- **Icons** - Font Awesome icon library
- **Mobile-first** - Responsive design approach

---

**Note**: This is a comprehensive inventory management system designed for small to medium-sized businesses. The HTML/CSS frontend provides a simple, maintainable solution without complex build processes. For enterprise use, consider additional features like user authentication, role-based access control, and advanced reporting capabilities.
