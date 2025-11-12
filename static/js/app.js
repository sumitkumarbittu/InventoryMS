// API Configuration
const API_BASE_URL = 'http://localhost:5001/api/v1';

// Global state
let currentData = {
    vendors: [],
    warehouses: [],
    products: [],
    shipments: [],
    orders: [],
    analytics: null
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    loadDashboardData();
    loadAllData();
    
    // Set dashboard as default active section
    const dashboardSection = document.getElementById('dashboard');
    const dashboardLink = document.querySelector('[data-section="dashboard"]');
    if (dashboardSection && dashboardLink) {
        dashboardSection.classList.add('active');
        dashboardLink.classList.add('active');
    }
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const targetSection = this.getAttribute('data-section');
            const section = document.getElementById(targetSection);
            if (section) {
                section.classList.add('active');
                
                // Load section-specific data
                loadSectionData(targetSection);
            }
        });
    });
}

// Load section-specific data
function loadSectionData(section) {
    switch(section) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'vendors':
            loadVendors();
            break;
        case 'warehouses':
            // If warehouses data is already loaded, just update the display
            if (currentData.warehouses && currentData.warehouses.length > 0) {
                updateWarehousesCards();
            } else {
                loadWarehouses();
            }
            break;
        case 'products':
            loadProducts();
            break;
        case 'shipments':
            loadShipments();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'forecasting':
            loadForecastingData();
            break;
    }
}

// API Helper Functions
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Error connecting to server', 'error');
        return { success: false, error: error.message };
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 4000;
        animation: slideIn 0.3s ease;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Loading spinner
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

// Dashboard Functions
async function loadDashboardData() {
    showLoading();
    try {
        const response = await apiCall('/analytics/dashboard');
        if (response.success) {
            currentData.analytics = response.data;
            updateDashboardCards();
            updateLowStockTable();
            updateTopProductsTable();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    } finally {
        hideLoading();
    }
}

function updateDashboardCards() {
    const summary = currentData.analytics?.summary_metrics || {};
    
    document.getElementById('totalValue').textContent = `$${summary.total_inventory_value?.toLocaleString() || '0'}`;
    document.getElementById('totalProducts').textContent = summary.total_products || '0';
    document.getElementById('lowStockCount').textContent = summary.low_stock_count || '0';
    document.getElementById('warehouseCount').textContent = currentData.warehouses.length || '0';
}

function updateLowStockTable() {
    const alerts = currentData.analytics?.low_stock_alerts || [];
    const tbody = document.getElementById('lowStockTableBody');
    
    tbody.innerHTML = alerts.slice(0, 10).map(alert => `
        <tr>
            <td>${alert.product_name}</td>
            <td>${alert.warehouse_name}</td>
            <td>${alert.current_stock}</td>
            <td>${alert.reorder_point}</td>
            <td><span class="badge badge-${getAlertBadgeClass(alert.alert_level)}">${alert.alert_level}</span></td>
        </tr>
    `).join('');
}

function updateTopProductsTable() {
    const products = currentData.analytics?.top_products || [];
    const tbody = document.getElementById('topProductsTableBody');
    
    tbody.innerHTML = products.slice(0, 10).map(product => `
        <tr>
            <td>${product.product_name}</td>
            <td>${product.category}</td>
            <td>$${product.total_revenue?.toLocaleString() || '0'}</td>
            <td>${product.total_quantity_sold || '0'}</td>
        </tr>
    `).join('');
}

function getAlertBadgeClass(level) {
    switch(level) {
        case 'Out of Stock':
        case 'Critical':
            return 'danger';
        case 'Low':
            return 'warning';
        default:
            return 'info';
    }
}

// Load all data
async function loadAllData() {
    try {
        const [vendorsRes, warehousesRes, productsRes, shipmentsRes, ordersRes] = await Promise.all([
            apiCall('/vendors'),
            apiCall('/warehouses'),
            apiCall('/products'),
            apiCall('/shipments'),
            apiCall('/orders')
        ]);
        
        if (vendorsRes.success) currentData.vendors = vendorsRes.data;
        if (warehousesRes.success) {
            currentData.warehouses = warehousesRes.data;
        }
        if (productsRes.success) currentData.products = productsRes.data;
        if (shipmentsRes.success) currentData.shipments = shipmentsRes.data;
        if (ordersRes.success) currentData.orders = ordersRes.data;
        // Refresh dashboard cards (e.g., warehouseCount) after base datasets load
        try { updateDashboardCards(); } catch (e) {}
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Vendors Functions
async function loadVendors() {
    showLoading();
    try {
        const response = await apiCall('/vendors');
        if (response.success) {
            currentData.vendors = response.data;
            updateVendorsTable();
        }
    } catch (error) {
        console.error('Error loading vendors:', error);
    } finally {
        hideLoading();
    }
}

function updateVendorsTable() {
    const tbody = document.getElementById('vendorsTableBody');
    
    tbody.innerHTML = currentData.vendors.map(vendor => `
        <tr>
            <td>${vendor.name}</td>
            <td>${vendor.contact_person || 'N/A'}</td>
            <td>${vendor.email || 'N/A'}</td>
            <td>${vendor.phone || 'N/A'}</td>
            <td>${renderStars(vendor.rating)}</td>
            <td>
                <button class="btn btn-secondary" onclick="editVendor(${vendor.vendor_id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="deleteVendor(${vendor.vendor_id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderStars(rating) {
    // Convert string rating to number
    const numRating = parseFloat(rating) || 0;
    const stars = [];
    const fullStars = Math.floor(numRating);
    const hasHalfStar = numRating % 1 !== 0;
    
    for (let i = 0; i < fullStars; i++) {
        stars.push('<i class="fas fa-star" style="color: #ffc107;"></i>');
    }
    
    if (hasHalfStar) {
        stars.push('<i class="fas fa-star-half-alt" style="color: #ffc107;"></i>');
    }
    
    const emptyStars = 5 - Math.ceil(numRating);
    for (let i = 0; i < emptyStars; i++) {
        stars.push('<i class="far fa-star" style="color: #ddd;"></i>');
    }
    
    return stars.join('') + ` <span style="margin-left: 5px;">${numRating.toFixed(1)}</span>`;
}

// Warehouses Functions
async function loadWarehouses() {
    showLoading();
    try {
        const response = await apiCall('/warehouses');
        if (response.success) {
            currentData.warehouses = response.data;
            updateWarehousesCards();
        }
    } catch (error) {
        console.error('Error loading warehouses:', error);
    } finally {
        hideLoading();
    }
}

function updateWarehousesCards() {
    const container = document.getElementById('warehousesContainer');
    
    if (!container) {
        console.error('Warehouses container not found');
        return;
    }
    
    container.innerHTML = currentData.warehouses.map(warehouse => `
        <div class="card warehouse-card">
            <div class="card-icon">
                <i class="fas fa-warehouse"></i>
            </div>
            <div class="card-content">
                <div class="card-header">
                    <h3>${warehouse.name}</h3>
                    <div class="card-actions">
                        <button class="btn btn-secondary btn-sm" onclick="editWarehouse(${warehouse.warehouse_id})" title="Edit Warehouse">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteWarehouse(${warehouse.warehouse_id})" title="Delete Warehouse">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <p style="color: #7f8c8d; margin: 5px 0;">${warehouse.location}</p>
                <p style="color: #2c3e50; font-size: 1.2rem; font-weight: 600; margin: 10px 0;">
                    ${warehouse.utilization_percentage?.toFixed(1) || '0'}% Utilization
                </p>
                <div style="background: #e1e5e9; height: 8px; border-radius: 4px; margin: 10px 0;">
                    <div style="
                        background: ${getUtilizationColor(warehouse.utilization_percentage)};
                        height: 100%;
                        width: ${Math.min(warehouse.utilization_percentage || 0, 100)}%;
                        border-radius: 4px;
                        transition: width 0.3s ease;
                    "></div>
                </div>
                <p style="color: #7f8c8d; font-size: 0.9rem;">
                    ${warehouse.current_utilization || 0} / ${warehouse.capacity || 0} capacity
                </p>
                <div class="warehouse-details">
                    <small style="color: #7f8c8d;">
                        ${warehouse.manager_name ? `Manager: ${warehouse.manager_name}` : ''}
                        ${warehouse.manager_contact ? ` | ${warehouse.manager_contact}` : ''}
                    </small>
                </div>
            </div>
        </div>
    `).join('');
}

function getUtilizationColor(utilization) {
    if (utilization >= 90) return '#dc3545';
    if (utilization >= 80) return '#fd7e14';
    if (utilization >= 60) return '#ffc107';
    return '#28a745';
}

// Products Functions
async function loadProducts() {
    showLoading();
    try {
        const response = await apiCall('/products');
        if (response.success) {
            currentData.products = response.data;
            updateProductsTable();
        }
    } catch (error) {
        console.error('Error loading products:', error);
    } finally {
        hideLoading();
    }
}

function updateProductsTable() {
    const tbody = document.getElementById('productsTableBody');
    
    tbody.innerHTML = currentData.products.map(product => `
        <tr>
            <td>${product.name}</td>
            <td><span class="badge badge-info">${product.category}</span></td>
            <td>${product.sku || 'N/A'}</td>
            <td>$${product.unit_price}</td>
            <td><span class="badge badge-${getStockStatusClass(product)}">${getStockStatus(product)}</span></td>
            <td>${product.reorder_point}</td>
            <td>
                <button class="btn btn-secondary" onclick="editProduct(${product.product_id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="deleteProduct(${product.product_id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getStockStatus(product) {
    const stockByWarehouse = product.stock_by_warehouse;
    if (!stockByWarehouse) return 'No Stock';
    
    const stocks = stockByWarehouse.split(';').map(s => {
        const [warehouse, stock] = s.split(':');
        return parseInt(stock);
    });
    
    const minStock = Math.min(...stocks);
    if (minStock <= product.reorder_point) {
        return 'Low Stock';
    }
    return 'In Stock';
}

function getStockStatusClass(product) {
    const status = getStockStatus(product);
    return status === 'Low Stock' ? 'warning' : 'success';
}

// Shipments Functions
async function loadShipments() {
    showLoading();
    try {
        const response = await apiCall('/shipments');
        if (response.success) {
            currentData.shipments = response.data;
            updateShipmentsTable();
        }
    } catch (error) {
        console.error('Error loading shipments:', error);
    } finally {
        hideLoading();
    }
}

function updateShipmentsTable() {
    const tbody = document.getElementById('shipmentsTableBody');
    
    tbody.innerHTML = currentData.shipments.map(shipment => `
        <tr>
            <td>${shipment.tracking_number || 'N/A'}</td>
            <td><span class="badge badge-${shipment.type === 'inbound' ? 'success' : 'info'}">${shipment.type}</span></td>
            <td><span class="badge badge-${getStatusBadgeClass(shipment.status)}">${shipment.status}</span></td>
            <td>${shipment.warehouse_name}</td>
            <td>${shipment.vendor_name || shipment.customer_name || 'N/A'}</td>
            <td>${shipment.carrier || 'N/A'}</td>
            <td>${shipment.shipment_date ? new Date(shipment.shipment_date).toLocaleDateString() : 'N/A'}</td>
            <td>
                <button class="btn btn-secondary" onclick="viewShipment(${shipment.shipment_id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'delivered': return 'success';
        case 'in_transit': return 'info';
        case 'pending': return 'warning';
        case 'cancelled': return 'danger';
        default: return 'info';
    }
}

// Orders Functions
async function loadOrders() {
    showLoading();
    try {
        const response = await apiCall('/orders');
        if (response.success) {
            currentData.orders = response.data;
            updateOrdersTable();
        }
    } catch (error) {
        console.error('Error loading orders:', error);
    } finally {
        hideLoading();
    }
}

function updateOrdersTable() {
    const tbody = document.getElementById('ordersTableBody');
    
    tbody.innerHTML = currentData.orders.map(order => `
        <tr>
            <td>#${order.order_id}</td>
            <td><span class="badge badge-${order.order_type === 'purchase' ? 'info' : 'success'}">${order.order_type}</span></td>
            <td><span class="badge badge-${getStatusBadgeClass(order.status)}">${order.status}</span></td>
            <td>${order.vendor_name}</td>
            <td>${order.order_date ? new Date(order.order_date).toLocaleDateString() : 'N/A'}</td>
            <td>$${order.total_amount?.toLocaleString() || '0'}</td>
            <td><span class="badge badge-${getPaymentStatusClass(order.payment_status)}">${order.payment_status}</span></td>
            <td>
                <button class="btn btn-secondary" onclick="viewOrder(${order.order_id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getPaymentStatusClass(status) {
    switch(status) {
        case 'paid': return 'success';
        case 'partial': return 'warning';
        case 'pending': return 'danger';
        default: return 'info';
    }
}

// Analytics Functions
async function loadAnalytics() {
    showLoading();
    try {
        const response = await apiCall('/analytics/dashboard');
        if (response.success) {
            currentData.analytics = response.data;
            updateVendorPerformanceTable();
            updateInventoryTurnoverTable();
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    } finally {
        hideLoading();
    }
}

function updateVendorPerformanceTable() {
    const performance = currentData.analytics?.vendor_performance || [];
    const tbody = document.getElementById('vendorPerformanceTableBody');
    
    tbody.innerHTML = performance.map(vendor => `
        <tr>
            <td>${vendor.vendor_name}</td>
            <td>${renderStars(vendor.rating)}</td>
            <td>${vendor.total_orders}</td>
            <td>$${vendor.total_sales?.toLocaleString() || '0'}</td>
            <td>${vendor.delivery_rate?.toFixed(1) || '0'}%</td>
        </tr>
    `).join('');
}

function updateInventoryTurnoverTable() {
    const turnover = currentData.analytics?.inventory_turnover || [];
    const tbody = document.getElementById('inventoryTurnoverTableBody');
    
    tbody.innerHTML = turnover.slice(0, 10).map(item => `
        <tr>
            <td>${item.product_name}</td>
            <td>${item.category}</td>
            <td>${item.turnover_rate}x</td>
            <td>${item.days_in_inventory} days</td>
        </tr>
    `).join('');
}

// Forecasting Functions
async function loadForecastingData() {
    // Load products and warehouses for dropdowns
    const productSelect = document.getElementById('forecastProduct');
    const warehouseSelect = document.getElementById('forecastWarehouse');
    
    productSelect.innerHTML = '<option value="">Select Product</option>' + 
        currentData.products.map(p => `<option value="${p.product_id}">${p.name}</option>`).join('');
    
    warehouseSelect.innerHTML = '<option value="">Select Warehouse</option>' + 
        currentData.warehouses.map(w => `<option value="${w.warehouse_id}">${w.name}</option>`).join('');
}

async function generateForecast() {
    const productId = document.getElementById('forecastProduct').value;
    const warehouseId = document.getElementById('forecastWarehouse').value;
    const method = document.getElementById('forecastMethod').value;
    const periods = document.getElementById('forecastPeriods').value;
    
    if (!productId || !warehouseId) {
        showNotification('Please select both product and warehouse', 'warning');
        return;
    }
    
    showLoading();
    try {
        const response = await apiCall('/forecast/generate', 'POST', {
            product_id: parseInt(productId),
            warehouse_id: parseInt(warehouseId),
            periods: parseInt(periods),
            method: method
        });
        
        if (response.success) {
            displayForecastResults(response.data);
            showNotification('Forecast generated successfully', 'success');
        } else {
            showNotification(response.error || 'Failed to generate forecast', 'error');
        }
    } catch (error) {
        console.error('Error generating forecast:', error);
        showNotification('Error generating forecast', 'error');
    } finally {
        hideLoading();
    }
}

function displayForecastResults(forecastData) {
    const resultsDiv = document.getElementById('forecastResults');
    const chartDiv = document.getElementById('forecastChart');
    const tableDiv = document.getElementById('forecastTable');
    
    // Show results
    resultsDiv.style.display = 'block';
    
    // Create simple chart visualization
    chartDiv.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <h4>Forecast Trend</h4>
            <div style="display: flex; align-items: end; justify-content: center; height: 200px; gap: 5px;">
                ${forecastData.map((item, index) => `
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        width: 20px;
                        height: ${(item.predicted_demand / Math.max(...forecastData.map(f => f.predicted_demand))) * 150}px;
                        border-radius: 2px;
                        position: relative;
                    " title="Period ${index + 1}: ${item.predicted_demand} units">
                    </div>
                `).join('')}
            </div>
            <p style="color: #7f8c8d; margin-top: 10px;">Predicted Demand by Period</p>
        </div>
    `;
    
    // Create forecast table
    tableDiv.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Period</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                    <th>Predicted Demand</th>
                    <th>Confidence Level</th>
                </tr>
            </thead>
            <tbody>
                ${forecastData.map((item, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${new Date(item.period_start).toLocaleDateString()}</td>
                        <td>${new Date(item.period_end).toLocaleDateString()}</td>
                        <td>${item.predicted_demand} units</td>
                        <td>${item.confidence_level.toFixed(1)}%</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Modal Functions
function showModal(title, content) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modalOverlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
}

// Modal content generators
function showVendorModal() {
    const content = `
        <form id="vendorForm">
            <div class="form-group">
                <label>Vendor Name *</label>
                <input type="text" class="form-control" id="vendorName" required>
            </div>
            <div class="form-group">
                <label>Contact Person *</label>
                <input type="text" class="form-control" id="vendorContact" required>
            </div>
            <div class="form-group">
                <label>Email *</label>
                <input type="email" class="form-control" id="vendorEmail" required>
            </div>
            <div class="form-group">
                <label>Phone *</label>
                <input type="tel" class="form-control" id="vendorPhone" required>
            </div>
            <div class="form-group">
                <label>Address</label>
                <textarea class="form-control" id="vendorAddress" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>Rating (0-5)</label>
                <input type="number" class="form-control" id="vendorRating" min="0" max="5" step="0.1" value="0">
            </div>
            <div class="form-group">
                <label>Product Categories</label>
                <input type="text" class="form-control" id="vendorCategories" placeholder="e.g., Electronics, Office Supplies">
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Vendor</button>
            </div>
        </form>
    `;
    
    showModal('Add New Vendor', content);
    
    // Add form submission handler
    document.getElementById('vendorForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const vendorData = {
            name: document.getElementById('vendorName').value,
            contact_person: document.getElementById('vendorContact').value,
            email: document.getElementById('vendorEmail').value,
            phone: document.getElementById('vendorPhone').value,
            address: document.getElementById('vendorAddress').value,
            rating: parseFloat(document.getElementById('vendorRating').value),
            product_categories: document.getElementById('vendorCategories').value
        };
        
        const response = await apiCall('/vendors', 'POST', vendorData);
        if (response.success) {
            showNotification('Vendor created successfully', 'success');
            closeModal();
            loadVendors();
        } else {
            showNotification(response.error || 'Failed to create vendor', 'error');
        }
    });
}

// Warehouse Modal
function showWarehouseModal() {
    const content = `
        <form id="warehouseForm">
            <div class="form-group">
                <label>Warehouse Name *</label>
                <input type="text" class="form-control" id="warehouseName" required>
            </div>
            <div class="form-group">
                <label>Location *</label>
                <input type="text" class="form-control" id="warehouseLocation" required>
            </div>
            <div class="form-group">
                <label>Capacity *</label>
                <input type="number" class="form-control" id="warehouseCapacity" required min="1">
            </div>
            <div class="form-group">
                <label>Manager</label>
                <input type="text" class="form-control" id="warehouseManager">
            </div>
            <div class="form-group">
                <label>Phone</label>
                <input type="tel" class="form-control" id="warehousePhone">
            </div>
            <div class="form-group">
                <label>Address</label>
                <textarea class="form-control" id="warehouseAddress" rows="3"></textarea>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Warehouse</button>
            </div>
        </form>
    `;
    
    showModal('Add New Warehouse', content);
    
    // Add form submission handler
    document.getElementById('warehouseForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const warehouseData = {
            name: document.getElementById('warehouseName').value,
            location: document.getElementById('warehouseLocation').value,
            capacity: parseInt(document.getElementById('warehouseCapacity').value),
            manager_name: document.getElementById('warehouseManager').value,
            manager_contact: document.getElementById('warehousePhone').value,
            address: document.getElementById('warehouseAddress').value
        };
        
        const response = await apiCall('/warehouses', 'POST', warehouseData);
        if (response.success) {
            showNotification('Warehouse created successfully', 'success');
            closeModal();
            loadWarehouses();
        } else {
            showNotification(response.error || 'Failed to create warehouse', 'error');
        }
    });
}

// Product Modal
function showProductModal() {
    const content = `
        <form id="productForm">
            <div class="form-group">
                <label>Product Name *</label>
                <input type="text" class="form-control" id="productName" required>
            </div>
            <div class="form-group">
                <label>Category *</label>
                <input type="text" class="form-control" id="productCategory" required>
            </div>
            <div class="form-group">
                <label>SKU</label>
                <input type="text" class="form-control" id="productSku">
            </div>
            <div class="form-group">
                <label>Unit Price *</label>
                <input type="number" class="form-control" id="productPrice" required min="0" step="0.01">
            </div>
            <div class="form-group">
                <label>Vendor *</label>
                <select class="form-control" id="productVendor" required>
                    <option value="">Select Vendor</option>
                    ${currentData.vendors.map(v => `<option value="${v.vendor_id}">${v.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Reorder Point</label>
                <input type="number" class="form-control" id="productReorderPoint" min="0" value="10">
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea class="form-control" id="productDescription" rows="3"></textarea>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Product</button>
            </div>
        </form>
    `;
    
    showModal('Add New Product', content);
    
    // Add form submission handler
    document.getElementById('productForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const productData = {
            name: document.getElementById('productName').value,
            category: document.getElementById('productCategory').value,
            sku: document.getElementById('productSku').value,
            unit_price: parseFloat(document.getElementById('productPrice').value),
            vendor_id: parseInt(document.getElementById('productVendor').value),
            reorder_point: parseInt(document.getElementById('productReorderPoint').value),
            description: document.getElementById('productDescription').value
        };
        
        const response = await apiCall('/products', 'POST', productData);
        if (response.success) {
            showNotification('Product created successfully', 'success');
            closeModal();
            loadProducts();
        } else {
            showNotification(response.error || 'Failed to create product', 'error');
        }
    });
}

// Shipment Modal
function showShipmentModal() {
    const content = `
        <form id="shipmentForm">
            <div class="form-group">
                <label>Shipment Type *</label>
                <select class="form-control" id="shipmentType" required>
                    <option value="">Select Type</option>
                    <option value="inbound">Inbound</option>
                    <option value="outbound">Outbound</option>
                </select>
            </div>
            <div class="form-group">
                <label>Warehouse *</label>
                <select class="form-control" id="shipmentWarehouse" required>
                    <option value="">Select Warehouse</option>
                    ${currentData.warehouses.map(w => `<option value="${w.warehouse_id}">${w.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Tracking Number</label>
                <input type="text" class="form-control" id="shipmentTracking">
            </div>
            <div class="form-group">
                <label>Carrier</label>
                <input type="text" class="form-control" id="shipmentCarrier">
            </div>
            <div class="form-group">
                <label>Status</label>
                <select class="form-control" id="shipmentStatus">
                    <option value="pending">Pending</option>
                    <option value="in_transit">In Transit</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>
            <div class="form-group">
                <label>Shipment Date</label>
                <input type="date" class="form-control" id="shipmentDate">
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Shipment</button>
            </div>
        </form>
    `;
    
    showModal('Add New Shipment', content);
    
    // Add form submission handler
    document.getElementById('shipmentForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const typeVal = document.getElementById('shipmentType').value;
        const warehouseVal = document.getElementById('shipmentWarehouse').value;
        if (!typeVal || !warehouseVal) {
            showNotification('Please select shipment type and warehouse', 'warning');
            return;
        }

        const whId = parseInt(warehouseVal);
        if (Number.isNaN(whId)) {
            showNotification('Invalid warehouse selected', 'error');
            return;
        }

        const shipmentData = {
            shipment: {
                type: typeVal,
                warehouse_id: whId,
                tracking_number: document.getElementById('shipmentTracking').value,
                carrier: document.getElementById('shipmentCarrier').value,
                status: document.getElementById('shipmentStatus').value,
                shipment_date: document.getElementById('shipmentDate').value
            },
            items: [] // For now, empty items array
        };
        
        const response = await apiCall('/shipments', 'POST', shipmentData);
        if (response.success) {
            showNotification('Shipment created successfully', 'success');
            closeModal();
            loadShipments();
        } else {
            showNotification(response.error || 'Failed to create shipment', 'error');
        }
    });
}

// Order Modal
function showOrderModal() {
    const content = `
        <form id="orderForm">
            <div class="form-group">
                <label>Order Type *</label>
                <select class="form-control" id="orderType" required>
                    <option value="">Select Type</option>
                    <option value="purchase">Purchase Order</option>
                    <option value="sales">Sales Order</option>
                </select>
            </div>
            <div class="form-group">
                <label>Vendor *</label>
                <select class="form-control" id="orderVendor" required>
                    <option value="">Select Vendor</option>
                    ${currentData.vendors.map(v => `<option value="${v.vendor_id}">${v.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Order Date *</label>
                <input type="date" class="form-control" id="orderDate" required>
            </div>
            <div class="form-group">
                <label>Status</label>
                <select class="form-control" id="orderStatus">
                    <option value="pending">Pending</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="shipped">Shipped</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>
            <div class="form-group">
                <label>Payment Status</label>
                <select class="form-control" id="orderPaymentStatus">
                    <option value="pending">Pending</option>
                    <option value="partial">Partial</option>
                    <option value="paid">Paid</option>
                </select>
            </div>
            <div class="form-group">
                <label>Total Amount</label>
                <input type="number" class="form-control" id="orderAmount" min="0" step="0.01">
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea class="form-control" id="orderNotes" rows="3"></textarea>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Order</button>
            </div>
        </form>
    `;
    
    showModal('Add New Order', content);
    
    // Add form submission handler
    document.getElementById('orderForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const orderData = {
            order: {
                vendor_id: parseInt(document.getElementById('orderVendor').value),
                order_type: document.getElementById('orderType').value,
                order_date: document.getElementById('orderDate').value,
                status: document.getElementById('orderStatus').value,
                payment_status: document.getElementById('orderPaymentStatus').value,
                total_amount: parseFloat(document.getElementById('orderAmount').value) || 0,
                notes: document.getElementById('orderNotes').value
            },
            items: [] // For now, empty items array
        };
        
        const response = await apiCall('/orders', 'POST', orderData);
        if (response.success) {
            showNotification('Order created successfully', 'success');
            closeModal();
            loadOrders();
        } else {
            showNotification(response.error || 'Failed to create order', 'error');
        }
    });
}

// Warehouse CRUD operations
function editWarehouse(warehouseId) {
    const warehouse = currentData.warehouses.find(w => w.warehouse_id === warehouseId);
    if (!warehouse) {
        showNotification('Warehouse not found', 'error');
        return;
    }
    
    const content = `
        <form id="editWarehouseForm">
            <div class="form-group">
                <label>Warehouse Name *</label>
                <input type="text" class="form-control" id="editWarehouseName" value="${warehouse.name}" required>
            </div>
            <div class="form-group">
                <label>Location *</label>
                <input type="text" class="form-control" id="editWarehouseLocation" value="${warehouse.location}" required>
            </div>
            <div class="form-group">
                <label>Capacity *</label>
                <input type="number" class="form-control" id="editWarehouseCapacity" value="${warehouse.capacity}" required min="1">
            </div>
            <div class="form-group">
                <label>Manager</label>
                <input type="text" class="form-control" id="editWarehouseManager" value="${warehouse.manager_name || ''}">
            </div>
            <div class="form-group">
                <label>Phone</label>
                <input type="tel" class="form-control" id="editWarehousePhone" value="${warehouse.manager_contact || ''}">
            </div>
            <div class="form-group">
                <label>Address</label>
                <textarea class="form-control" id="editWarehouseAddress" rows="3">${warehouse.address || ''}</textarea>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Update Warehouse</button>
            </div>
        </form>
    `;
    
    showModal('Edit Warehouse', content);
    
    // Add form submission handler
    document.getElementById('editWarehouseForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const warehouseData = {
            name: document.getElementById('editWarehouseName').value,
            location: document.getElementById('editWarehouseLocation').value,
            capacity: parseInt(document.getElementById('editWarehouseCapacity').value),
            manager_name: document.getElementById('editWarehouseManager').value,
            manager_contact: document.getElementById('editWarehousePhone').value,
            address: document.getElementById('editWarehouseAddress').value
        };
        
        const response = await apiCall(`/warehouses/${warehouseId}`, 'PUT', warehouseData);
        if (response.success) {
            showNotification('Warehouse updated successfully', 'success');
            closeModal();
            loadWarehouses();
        } else {
            showNotification(response.error || 'Failed to update warehouse', 'error');
        }
    });
}

function deleteWarehouse(warehouseId) {
    const warehouse = currentData.warehouses.find(w => w.warehouse_id === warehouseId);
    if (!warehouse) {
        showNotification('Warehouse not found', 'error');
        return;
    }
    
    if (confirm(`Are you sure you want to delete warehouse "${warehouse.name}"? This action cannot be undone.`)) {
        apiCall(`/warehouses/${warehouseId}`, 'DELETE')
            .then(response => {
                if (response.success) {
                    showNotification('Warehouse deleted successfully', 'success');
                    loadWarehouses();
                } else {
                    showNotification(response.error || 'Failed to delete warehouse', 'error');
                }
            })
            .catch(error => {
                showNotification('Error deleting warehouse', 'error');
                console.error('Delete warehouse error:', error);
            });
    }
}

// Placeholder functions for edit/delete operations
function editVendor(id) {
    showNotification('Edit vendor functionality coming soon', 'info');
}

function deleteVendor(id) {
    if (confirm('Are you sure you want to delete this vendor?')) {
        showNotification('Delete vendor functionality coming soon', 'info');
    }
}

function editProduct(id) {
    showNotification('Edit product functionality coming soon', 'info');
}

function deleteProduct(id) {
    if (confirm('Are you sure you want to delete this product?')) {
        showNotification('Delete product functionality coming soon', 'info');
    }
}

function viewShipment(id) {
    showNotification('View shipment functionality coming soon', 'info');
}

function viewOrder(id) {
    showNotification('View order functionality coming soon', 'info');
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
