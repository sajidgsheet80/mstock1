from flask import Flask, render_template_string, request, session, flash, redirect, url_for, get_flashed_messages, jsonify
import requests
import hashlib
import logging
from datetime import datetime

app = Flask(__name__)
# It's crucial to change this secret key in a production environment
app.secret_key = 'a_very_secret_and_random_string'

# API Credentials - Replace with your actual credentials
API_KEY = 'DKqtPSHqUjyoLfBD+WAfbkMa8Jx2WEaIfbCaOQWbIx0='
API_SECRET = '<your_api_secret_here>'

# Base URL for API
# This is the correct base URL since 'session' endpoint works with it.
# The 404 errors are due to incorrect endpoint *paths* for your API version.
# You may need to find the correct paths for 'margins', 'positions', etc. from your specific API documentation.
BASE_URL = 'https://api.mstock.trade/openapi/typea'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# HTML Templates
# =============================

# Main template with tabular formatting
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mirae Asset Trading Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { padding: 8px; width: 100%; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        button.logout { background-color: #f44336; }
        button.logout:hover { background-color: #d32f2f; }
        button.squareoff-all { background-color: #FF5722; margin-bottom: 10px; }
        button.squareoff-all:hover { background-color: #E64A19; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .nav { margin-bottom: 20px; }
        .nav button { margin-right: 10px; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background-color: #dff0d8; color: #3c763d; }
        .error { background-color: #f2dede; color: #a94442; }
        .tabs { display: flex; border-bottom: 1px solid #ddd; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; background-color: #f1f1f1; border: 1px solid #ccc; border-bottom: none; margin-right: 5px; }
        .tab.active { background-color: white; border-bottom: 1px solid white; margin-bottom: -1px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-row { display: flex; gap: 20px; }
        .form-col { flex: 1; }
        .loading-indicator { text-align: center; padding: 20px; font-style: italic; color: #666; }
        .action-cell button { margin-right: 5px; }
        .notification { position: fixed; top: 20px; right: 20px; padding: 15px; border-radius: 4px; color: white; z-index: 1000; }
        .notification.success { background-color: #4CAF50; }
        .notification.error { background-color: #f44336; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-indicator.online { background-color: #4CAF50; }
        .status-indicator.offline { background-color: #f44336; }
        .status-indicator.updating { background-color: #FF9800; animation: pulse 1s infinite; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mirae Asset Trading Platform</h1>
        
        <!-- Flash Messages Block -->
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="message {{ category }}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        {% if not access_token %}
            <div class="tabs">
                <div class="tab active" onclick="showTab('login')">Login</div>
            </div>
            
            <div id="login" class="tab-content active">
                <h2>Step 1: Verify OTP</h2>
                {% if error %}
                    <div class="message error">{{ error }}</div>
                {% endif %}
                <form method="post">
                    <div class="form-group">
                        <label for="totp">Enter OTP:</label>
                        <input type="text" id="totp" name="totp" required>
                    </div>
                    <button type="submit">Verify OTP</button>
                </form>
            </div>
        {% else %}
            <div class="tabs">
                <div class="tab {% if active_tab == 'dashboard' %}active{% endif %}" onclick="showTab('dashboard')">Dashboard</div>
                <div class="tab {% if active_tab == 'place_order' %}active{% endif %}" onclick="showTab('place_order')">Place Order</div>
                <div class="tab {% if active_tab == 'order_book' %}active{% endif %}" onclick="showTab('order_book')">Order Book</div>
                <div class="tab {% if active_tab == 'positions' %}active{% endif %}" onclick="showTab('positions')">Positions (Live)</div>
                <div class="tab {% if active_tab == 'trades' %}active{% endif %}" onclick="showTab('trades')">Trades</div>
            </div>
            
            <div id="dashboard" class="tab-content {% if active_tab == 'dashboard' %}active{% endif %}">
                <h2>Dashboard</h2>
                <div class="message success">
                    <p><strong>Access Token:</strong> {{ access_token }}</p>
                    <p><strong>Login Time:</strong> {{ login_time }}</p>
                </div>
                
                <h3>Quick Actions</h3>
                <div class="nav">
                    <button onclick="showTab('place_order')">Place Order</button>
                    <button onclick="showTab('order_book')">View Orders</button>
                    <button onclick="showTab('positions')">View Positions</button>
                </div>
                
                <h3>Account Summary</h3>
                <table>
                    <tr>
                        <th>Segment</th>
                        <th>Margin Used</th>
                        <th>Margin Available</th>
                    </tr>
                    <tr>
                        <td>Equity</td>
                        <td>₹{{ margins.equity.used | default('N/A') }}</td>
                        <td>₹{{ margins.equity.available | default('N/A') }}</td>
                    </tr>
                    <tr>
                        <td>Commodity</td>
                        <td>₹{{ margins.commodity.used | default('N/A') }}</td>
                        <td>₹{{ margins.commodity.available | default('N/A') }}</td>
                    </tr>
                </table>
            </div>
            
            <div id="place_order" class="tab-content {% if active_tab == 'place_order' %}active{% endif %}">
                <h2>Place Order</h2>
                {% if order_response %}
                    <div class="message {% if 'error' in order_response %}error{% else %}success{% endif %}">
                        <h3>Order Response:</h3>
                        <pre>{{ order_response | safe }}</pre>
                    </div>
                {% endif %}
                
                <form method="post" action="/place_order">
                    <div class="form-row">
                        <div class="form-col">
                            <div class="form-group">
                                <label for="tradingsymbol">Symbol:</label>
                                <input type="text" id="tradingsymbol" name="tradingsymbol" value="NIFTY25" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="exchange">Exchange:</label>
                                <select id="exchange" name="exchange">
                                    <option value="NFO">NFO</option>
                                    <option value="NSE">NSE</option>
                                    <option value="BSE">BSE</option>
                                    <option value="MCX">MCX</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="transaction_type">Transaction Type:</label>
                                <select id="transaction_type" name="transaction_type">
                                    <option value="BUY">BUY</option>
                                    <option value="SELL">SELL</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="order_type">Order Type:</label>
                                <select id="order_type" name="order_type" onchange="togglePriceField()">
                                    <option value="LIMIT">LIMIT</option>
                                    <option value="MARKET">MARKET</option>
                                    <option value="SL">Stop Loss</option>
                                    <option value="SL-M">Stop Loss Market</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-col">
                            <div class="form-group">
                                <label for="quantity">Quantity:</label>
                                <input type="number" id="quantity" name="quantity" value="75" required>
                            </div>
                            
                            <div class="form-group" id="price_field">
                                <label for="price">Price:</label>
                                <input type="text" id="price" name="price" value="1">
                            </div>
                            
                            <div class="form-group" id="trigger_field" style="display:none;">
                                <label for="trigger_price">Trigger Price:</label>
                                <input type="text" id="trigger_price" name="trigger_price" value="0">
                            </div>
                            
                            <div class="form-group">
                                <label for="product">Product:</label>
                                <select id="product" name="product">
                                    <option value="CNC">CNC (Delivery)</option>
                                    <option value="NRML">NRML (Normal)</option>
                                    <option value="MIS">MIS (Intraday)NRML (Normal)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="validity">Validity:</label>
                                <select id="validity" name="validity">
                                    <option value="DAY">DAY</option>
                                    <option value="IOC">IOC</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="variety">Variety:</label>
                        <select id="variety" name="variety">
                            <option value="regular">Regular</option>
                            <option value="amo">AMO (After Market Order)</option>
                            <option value="iceberg">Iceberg</option>
                        </select>
                    </div>
                    
                    <button type="submit">Place Order</button>
                </form>
            </div>
            
            <div id="order_book" class="tab-content {% if active_tab == 'order_book' %}active{% endif %}">
                <h2>Order Book</h2>
                <button onclick="refreshOrderBook()">Refresh</button>
                
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Symbol</th>
                            <th>Exchange</th>
                            <th>Type</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Trigger Price</th>
                            <th>Status</th>
                            <th>Product</th>
                            <th>Validity</th>
                            <th>Order Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in orders %}
                        <tr>
                            <td>{{ order.oms_order_id }}</td>
                            <td>{{ order.trading_symbol }}</td>
                            <td>{{ order.exchange }}</td>
                            <td>{{ order.transaction_type }}</td>
                            <td>{{ order.quantity }}</td>
                            <td>{{ order.price }}</td>
                            <td>{{ order.trigger_price }}</td>
                            <td>{{ order.status }}</td>
                            <td>{{ order.product }}</td>
                            <td>{{ order.validity }}</td>
                            <td>{{ order.order_timestamp }}</td>
                            <td class="action-cell">
                                {% if order.status in ['pending', 'trigger pending', 'open'] %}
                                <button onclick="modifyOrder({{ order | tojson | safe }})" style="background-color:#2196F3;color:white;padding:5px 10px;border:none;border-radius:4px;cursor:pointer;">Modify</button>
                                <a href="{{ url_for('cancel_order', order_id=order.oms_order_id) }}" style="background-color:#f44336;color:white;padding:5px 10px;text-decoration:none;border-radius:4px;" onclick="return confirm('Are you sure you want to cancel this order?');">Cancel</a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div id="positions" class="tab-content {% if active_tab == 'positions' %}active{% endif %}">
                <h2>Net Positions (Live) 
                    <span id="status-indicator" class="status-indicator offline"></span>
                    <span id="status-text">Offline</span>
                </h2>
                <p>Positions are updated automatically every 5 seconds. Last update: <span id="last-update">Never</span></p>
                
                <button class="squareoff-all" onclick="squareOffAllPositions()">Square Off All Positions</button>
                
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Exchange</th>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Average Price</th>
                            <th>Last Price</th>
                            <th>P&L</th>
                            <th>P&L %</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="positions-tbody">
                        <!-- Initial positions will be rendered here by Flask -->
                        {% if positions %}
                            {% for position in positions %}
                            <tr>
                                <td>{{ position.trading_symbol }}</td>
                                <td>{{ position.exchange }}</td>
                                <td>{{ position.product }}</td>
                                <td>{{ position.quantity }}</td>
                                <td>{{ position.average_price }}</td>
                                <td>{{ position.last_price }}</td>
                                <td>{{ position.pnl }}</td>
                                <td>{{ position.pnl_percentage }}</td>
                                <td class="action-cell">
                                    <button onclick="squareOffPosition({{ position | tojson | safe }})" style="background-color:#FF9800;color:white;padding:5px 10px;border:none;border-radius:4px;cursor:pointer;">Square Off</button>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                        <tr>
                            <td colspan="9" style="text-align:center;">No open positions.</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
                <div id="positions-loading" class="loading-indicator" style="display: none;">Updating...</div>
            </div>
            
            <div id="trades" class="tab-content {% if active_tab == 'trades' %}active{% endif %}">
                <h2>Trade Book</h2>
                <button onclick="refreshTrades()">Refresh</button>
                
                <table>
                    <thead>
                        <tr>
                            <th>Trade ID</th>
                            <th>Order ID</th>
                            <th>Symbol</th>
                            <th>Exchange</th>
                            <th>Type</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Trade Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for trade in trades %}
                        <tr>
                            <td>{{ trade.trade_id }}</td>
                            <td>{{ trade.oms_order_id }}</td>
                            <td>{{ trade.trading_symbol }}</td>
                            <td>{{ trade.exchange }}</td>
                            <td>{{ trade.transaction_type }}</td>
                            <td>{{ trade.quantity }}</td>
                            <td>{{ trade.price }}</td>
                            <td>{{ trade.trade_timestamp }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 30px;">
                <form method="post" action="/logout">
                    <button type="submit" class="logout">Logout</button>
                </form>
            </div>
        {% endif %}
    </div>
    
    <script>
        let positionsInterval = null;
        let isUpdating = false;

        function showTab(tabName) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show the selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to the clicked tab
            event.target.classList.add('active');

            // Stop the live updates if we are leaving the positions tab
            if (tabName !== 'positions' && positionsInterval) {
                clearInterval(positionsInterval);
                positionsInterval = null;
                updateStatusIndicator('offline');
            }
            
            // Start live updates if we are entering the positions tab
            if (tabName === 'positions' && !positionsInterval) {
                // Initial fetch
                fetchAndUpdatePositions();
                // Set interval for subsequent fetches (every 5 seconds)
                positionsInterval = setInterval(fetchAndUpdatePositions, 5000);
            }
        }
        
        function togglePriceField() {
            const orderType = document.getElementById('order_type').value;
            const priceField = document.getElementById('price_field');
            const triggerField = document.getElementById('trigger_field');
            
            if (orderType === 'MARKET' || orderType === 'SL-M') {
                priceField.style.display = 'none';
            } else {
                priceField.style.display = 'block';
            }
            
            if (orderType === 'SL' || orderType === 'SL-M') {
                triggerField.style.display = 'block';
            } else {
                triggerField.style.display = 'none';
            }
        }

        function modifyOrder(orderDetails) {
            // Populate the form with the order's details
            document.getElementById('tradingsymbol').value = orderDetails.trading_symbol;
            document.getElementById('exchange').value = orderDetails.exchange;
            document.getElementById('transaction_type').value = orderDetails.transaction_type;
            document.getElementById('order_type').value = orderDetails.order_type;
            document.getElementById('quantity').value = orderDetails.quantity;
            document.getElementById('price').value = orderDetails.price;
            document.getElementById('trigger_price').value = orderDetails.trigger_price;
            document.getElementById('product').value = orderDetails.product;
            document.getElementById('validity').value = orderDetails.validity;
            document.getElementById('variety').value = orderDetails.variety || 'regular';
            
            // Switch to the place order tab
            showTab('place_order');
            // Ensure correct fields are shown/hidden
            togglePriceField();
        }

        function squareOffPosition(positionDetails) {
            // Determine the opposite transaction type
            const transactionType = parseInt(positionDetails.quantity) > 0 ? 'SELL' : 'BUY';
            const quantity = Math.abs(parseInt(positionDetails.quantity));

            // Populate the form to create an exit order
            document.getElementById('tradingsymbol').value = positionDetails.trading_symbol;
            document.getElementById('exchange').value = positionDetails.exchange;
            document.getElementById('transaction_type').value = transactionType;
            document.getElementById('quantity').value = quantity;
            document.getElementById('product').value = positionDetails.product;
            document.getElementById('order_type').value = 'MARKET'; // Use market order for quick exit
            document.getElementById('validity').value = 'DAY';
            document.getElementById('variety').value = 'regular';
            
            // Switch to the place order tab
            showTab('place_order');
            // Ensure correct fields are shown/hidden
            togglePriceField();
        }
        
        function squareOffAllPositions() {
            if (!confirm('Are you sure you want to square off all positions? This action cannot be undone.')) {
                return;
            }
            
            showNotification('Processing square off for all positions...', 'success');
            
            fetch('{{ url_for("squareoff_all") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(`Successfully squared off ${data.count} positions.`, 'success');
                    // Refresh positions after a short delay
                    setTimeout(() => {
                        fetchAndUpdatePositions();
                    }, 1000);
                } else {
                    showNotification(`Error: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to square off all positions. Please try again.', 'error');
            });
        }
        
        function updateStatusIndicator(status) {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            indicator.className = 'status-indicator';
            
            switch(status) {
                case 'online':
                    indicator.classList.add('online');
                    text.textContent = 'Online';
                    break;
                case 'updating':
                    indicator.classList.add('updating');
                    text.textContent = 'Updating';
                    break;
                case 'offline':
                default:
                    indicator.classList.add('offline');
                    text.textContent = 'Offline';
                    break;
            }
        }
        
        function updateLastUpdateTime() {
            const now = new Date();
            document.getElementById('last-update').textContent = now.toLocaleTimeString();
        }
        
        function showNotification(message, type) {
            // Remove any existing notifications
            const existingNotification = document.querySelector('.notification');
            if (existingNotification) {
                existingNotification.remove();
            }
            
            // Create new notification
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            // Add to DOM
            document.body.appendChild(notification);
            
            // Remove after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
        
        function refreshOrderBook() {
            window.location.href = '{{ url_for("order_book") }}';
        }
        
        function refreshPositions() {
            window.location.href = '{{ url_for("positions") }}';
        }
        
        function refreshTrades() {
            window.location.href = '{{ url_for("trades") }}';
        }
        
        // --- Live Positions Logic ---
        async function fetchAndUpdatePositions() {
            if (isUpdating) return; // Prevent multiple simultaneous updates
            
            const loadingIndicator = document.getElementById('positions-loading');
            const tbody = document.getElementById('positions-tbody');
            
            isUpdating = true;
            updateStatusIndicator('updating');
            
            try {
                loadingIndicator.style.display = 'block';
                console.log('Fetching positions...');
                
                const response = await fetch('{{ url_for("api_positions") }}');
                console.log('Response received:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const positions = await response.json();
                console.log('Positions data:', positions);

                // Clear existing rows
                tbody.innerHTML = '';

                // Handle the specific response structure with day and net properties
                let positionsArray = [];
                
                // Check for day positions
                if (positions && positions.day && Array.isArray(positions.day)) {
                    positionsArray = positionsArray.concat(positions.day);
                }
                
                // Check for net positions
                if (positions && positions.net && Array.isArray(positions.net)) {
                    positionsArray = positionsArray.concat(positions.net);
                }

                if (!positionsArray || positionsArray.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No open positions.</td></tr>';
                } else {
                    // Populate table with new data
                    positionsArray.forEach(position => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${position.trading_symbol || 'N/A'}</td>
                            <td>${position.exchange || 'N/A'}</td>
                            <td>${position.product || 'N/A'}</td>
                            <td>${position.quantity || 'N/A'}</td>
                            <td>${position.average_price || 'N/A'}</td>
                            <td>${position.last_price || 'N/A'}</td>
                            <td>${position.pnl || 'N/A'}</td>
                            <td>${position.pnl_percentage || 'N/A'}</td>
                            <td class="action-cell">
                                <button onclick="squareOffPosition(${JSON.stringify(position).replace(/"/g, '&quot;')})" style="background-color:#FF9800;color:white;padding:5px 10px;border:none;border-radius:4px;cursor:pointer;">Square Off</button>
                            </td>
                        `;
                    });
                }
                
                updateStatusIndicator('online');
                updateLastUpdateTime();
                
            } catch (error) {
                console.error("Error fetching live positions:", error);
                updateStatusIndicator('offline');
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color: red;">Failed to load positions: ${error.message}</td></tr>`;
                showNotification(`Failed to load positions: ${error.message}`, 'error');
            } finally {
                loadingIndicator.style.display = 'none';
                isUpdating = false;
            }
        }

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            togglePriceField();
        });
    </script>
</body>
</html>
"""

# =============================
# Helper Functions
# =============================

def get_headers():
    """Get common headers for API requests"""
    return {
        'X-Mirae-Version': '1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

def get_auth_headers(access_token):
    """Get headers with authentication token"""
    headers = get_headers()
    headers['Authorization'] = f'token {API_KEY}:{access_token}'
    return headers

def make_api_request(method, endpoint, access_token=None, data=None):
    """Make an API request with error handling"""
    url = f"{BASE_URL}/{endpoint}"
    headers = get_auth_headers(access_token) if access_token else get_headers()
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=data)
        else:
            return None, "Unsupported HTTP method"
        
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {url}: {str(e)}")
        return None, str(e)

def get_common_data(access_token):
    """
    Fetches data common to all logged-in pages, like margins.
    ACTION NEEDED: You must find the correct endpoint for 'margins' in your API documentation.
    """
    # *** CHANGE 'margins' HERE IF THE ENDPOINT IS DIFFERENT IN YOUR DOCS ***
    margins_data, _ = make_api_request('GET', 'margins', access_token)
    margins = {
        'equity': {'used': 'N/A', 'available': 'N/A'},
        'commodity': {'used': 'N/A', 'available': 'N/A'}
    }
    
    if margins_data and 'data' in margins_data:
        if 'equity' in margins_data['data']:
            margins['equity'] = margins_data['data']['equity']
        if 'commodity' in margins_data['data']:
            margins['commodity'] = margins_data['data']['commodity']
    
    return margins

# =============================
# Routes
# =============================

@app.route("/", methods=["GET", "POST"])
def index():
    access_token = session.get('access_token')
    error = None
    active_tab = 'dashboard'
    
    # Handle OTP verification
    if request.method == "POST" and not access_token:
        totp = request.form.get("totp", "").strip()
        if not totp:
            error = "OTP is required!"
        else:
            checksum = hashlib.sha256(f"{API_KEY}{totp}{API_SECRET}".encode()).hexdigest()
            data = {'api_key': API_KEY, 'totp': totp, 'checksum': checksum}
            
            response_data, error = make_api_request('POST', 'session/verifytotp', data=data)
            
            if not error and response_data.get("status") == "success":
                access_token = response_data["data"]["access_token"]
                session['access_token'] = access_token
                session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif not error:
                error = response_data.get("message", "Failed to generate session")
    
    # If logged in, get dashboard data
    if access_token:
        margins = get_common_data(access_token)
        
        return render_template_string(
            HTML_TEMPLATE,
            access_token=access_token,
            login_time=session.get('login_time'),
            error=error,
            active_tab=active_tab,
            margins=margins
        )
    
    return render_template_string(
        HTML_TEMPLATE,
        access_token=None,
        error=error
    )

@app.route("/place_order", methods=["POST"])
def place_order():
    access_token = session.get("access_token")
    if not access_token:
        flash("Please verify OTP first!", "error")
        return redirect(url_for('index'))
    
    # Gather form inputs
    form_data = {key: request.form[key] for key in request.form}
    variety = form_data.pop("variety", "regular")
    
    # Prepare data for API
    api_data = {
        'tradingsymbol': form_data.get('tradingsymbol'),
        'exchange': form_data.get('exchange'),
        'transaction_type': form_data.get('transaction_type'),
        'order_type': form_data.get('order_type'),
        'quantity': form_data.get('quantity'),
        'product': form_data.get('product'),
        'validity': form_data.get('validity'),
        'price': form_data.get('price', '0'),
        'trigger_price': form_data.get('trigger_price', '0')
    }
    
    response_data, error = make_api_request('POST', f'orders/{variety}', access_token, api_data)
    
    order_response = response_data if not error else {"error": error}
    
    margins = get_common_data(access_token)

    return render_template_string(
        HTML_TEMPLATE,
        access_token=access_token,
        login_time=session.get('login_time'),
        active_tab='place_order',
        order_response=order_response,
        margins=margins
    )

@app.route("/order_book")
def order_book():
    access_token = session.get("access_token")
    if not access_token:
        flash("Please verify OTP first!", "error")
        return redirect(url_for('index'))
    
    margins = get_common_data(access_token)
    # *** CHANGE 'orders' HERE IF THE ENDPOINT IS DIFFERENT IN YOUR DOCS ***
    response_data, error = make_api_request('GET', 'orders', access_token)
    orders = response_data.get('data', []) if not error else []
    
    return render_template_string(
        HTML_TEMPLATE,
        access_token=access_token,
        login_time=session.get('login_time'),
        active_tab='order_book',
        orders=orders,
        margins=margins
    )

@app.route("/cancel_order/<order_id>")
def cancel_order(order_id):
    access_token = session.get("access_token")
    if not access_token:
        flash("Please verify OTP first!", "error")
        return redirect(url_for('index'))

    response_data, error = make_api_request('POST', f'orders/regular/{order_id}', access_token)

    if error:
        flash(f"API request failed: {error}", "error")
    elif response_data and response_data.get("status") == "success":
        flash(f"Order {order_id} cancelled successfully.", "success")
    else:
        message = response_data.get("message", "Unknown error") if response_data else "Unknown error"
        flash(f"Failed to cancel order: {message}", "error")

    return redirect(url_for('order_book'))

@app.route("/positions")
def positions():
    access_token = session.get("access_token")
    if not access_token:
        flash("Please verify OTP first!", "error")
        return redirect(url_for('index'))
    
    margins = get_common_data(access_token)
    # *** CHANGE 'positions' HERE IF THE ENDPOINT IS DIFFERENT IN YOUR DOCS ***
    # Try using the full path you mentioned
    response_data, error = make_api_request('GET', 'portfolio/positions', access_token)
    
    # Handle the specific response structure with day and net properties
    positions = []
    if not error and response_data:
        # Check for day positions
        if 'day' in response_data and response_data['day']:
            if isinstance(response_data['day'], list):
                positions.extend(response_data['day'])
        
        # Check for net positions
        if 'net' in response_data and response_data['net']:
            if isinstance(response_data['net'], list):
                positions.extend(response_data['net'])
    
    return render_template_string(
        HTML_TEMPLATE,
        access_token=access_token,
        login_time=session.get('login_time'),
        active_tab='positions',
        positions=positions,
        margins=margins
    )

@app.route("/api/positions")
def api_positions():
    """API endpoint to return positions as JSON for live updates."""
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"error": "Unauthorized"}), 401

    # *** CHANGE 'positions' HERE IF THE ENDPOINT IS DIFFERENT IN YOUR DOCS ***
    # Try using the full path you mentioned
    response_data, error = make_api_request('GET', 'portfolio/positions', access_token)
    if error:
        return jsonify({"error": error}), 500
    
    # Return the full response structure to let frontend handle day and net positions
    return jsonify(response_data or {})

@app.route("/squareoff_all", methods=["POST"])
def squareoff_all():
    """Square off all open positions."""
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # Get all positions
    response_data, error = make_api_request('GET', 'portfolio/positions', access_token)
    if error:
        return jsonify({"success": False, "message": f"Failed to fetch positions: {error}"})
    
    # Handle the specific response structure with day and net properties
    positions = []
    if response_data:
        # Check for day positions
        if 'day' in response_data and response_data['day']:
            if isinstance(response_data['day'], list):
                positions.extend(response_data['day'])
        
        # Check for net positions
        if 'net' in response_data and response_data['net']:
            if isinstance(response_data['net'], list):
                positions.extend(response_data['net'])
    
    if not positions:
        return jsonify({"success": True, "count": 0, "message": "No positions to square off"})
    
    success_count = 0
    failed_positions = []
    
    for position in positions:
        try:
            # Determine the opposite transaction type
            quantity = int(position.get('quantity', 0))
            if quantity == 0:
                continue  # Skip positions with zero quantity
                
            transaction_type = 'SELL' if quantity > 0 else 'BUY'
            abs_quantity = abs(quantity)
            
            # Prepare order data
            order_data = {
                'tradingsymbol': position.get('trading_symbol'),
                'exchange': position.get('exchange'),
                'transaction_type': transaction_type,
                'order_type': 'MARKET',  # Use market order for quick exit
                'quantity': str(abs_quantity),
                'product': position.get('product'),
                'validity': 'DAY',
                'price': '0',
                'trigger_price': '0'
            }
            
            # Place the order
            order_response, order_error = make_api_request('POST', 'orders/regular', access_token, order_data)
            
            if order_error:
                failed_positions.append({
                    'symbol': position.get('trading_symbol'),
                    'error': order_error
                })
            else:
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error squaring off position {position.get('trading_symbol')}: {str(e)}")
            failed_positions.append({
                'symbol': position.get('trading_symbol'),
                'error': str(e)
            })
    
    if failed_positions:
        return jsonify({
            "success": False,
            "count": success_count,
            "message": f"Successfully squared off {success_count} positions. Failed for {len(failed_positions)} positions.",
            "failed_positions": failed_positions
        })
    else:
        return jsonify({
            "success": True,
            "count": success_count,
            "message": f"Successfully squared off all {success_count} positions."
        })

@app.route("/trades")
def trades():
    access_token = session.get("access_token")
    if not access_token:
        flash("Please verify OTP first!", "error")
        return redirect(url_for('index'))
    
    margins = get_common_data(access_token)
    # *** CHANGE 'trades' HERE IF THE ENDPOINT IS DIFFERENT IN YOUR DOCS ***
    response_data, error = make_api_request('GET', 'trades', access_token)
    trades = response_data.get('data', []) if not error else []
    
    return render_template_string(
        HTML_TEMPLATE,
        access_token=access_token,
        login_time=session.get('login_time'),
        active_tab='trades',
        trades=trades,
        margins=margins
    )

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return render_template_string(
        HTML_TEMPLATE,
        access_token=None,
        error=None
    )

# =============================
# Run Application
# =============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*60)
    print("🚀 Sajid Shaikh Algo Trading Bot - Nifty50 + Dual Broker")
    print("="*60)
    print(f"📍 Server: http://127.0.0.1:{port}")
    print("📝 Users stored in: users.txt")
    print("🔑 Credentials stored in: user_credentials.txt")
    print("="*60)
    print("\nmStock API Routes:")
    print("  POST /mstock/login - Authenticate with OTP")
    print("  POST /mstock/refresh_token - Refresh access token")
    print("  POST /mstock/logout - Logout from mStock")
    print("  GET  /mstock/status - Check authentication status")
    print("  GET  /mstock_auth - mStock authentication UI")
    print("  GET  /mstock_option_chain - mStock option chain view")
    print("\nFyers API Routes:")
    print("  GET  /fyers_auth - Fyers authentication UI")
    print("  GET  /fyers_login - Direct Fyers login")
    print("\nDual Broker Routes:")
    print("  POST /place_dual_order - Place order with both brokers")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
