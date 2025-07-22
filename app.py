from flask import Flask, jsonify, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db_connection():
    """Get database connection using Railway's DATABASE_URL"""
    database_url = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL environment variable: {database_url}")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        return None
        
    try:
        print("Attempting to connect to database...")
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        print("Database connection successful!")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        print(f"Error type: {type(e)}")
        return None

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to Stratus Weather App!', 
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health_check():
    # Test database connection
    db_status = 'disconnected'
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1;')
            cursor.fetchone()
            cursor.close()
            conn.close()
            db_status = 'connected'
    except Exception as e:
        print(f"Health check db error: {e}")
    
    return jsonify({
        'status': 'healthy', 
        'service': 'stratus-api',
        'database': db_status
    })

@app.route('/api/init-db')
def init_database():
    """Initialize database with basic schema"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Could not connect to database'}), 500
            
        cursor = conn.cursor()
        
        # Create locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                lat DECIMAL(10, 8) NOT NULL,
                lon DECIMAL(11, 8) NOT NULL,
                country VARCHAR(100),
                state VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(lat, lon)
            );
        ''')
        
        # Create weather forecasts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id SERIAL PRIMARY KEY,
                location_id INTEGER REFERENCES locations(id),
                forecast_date DATE NOT NULL,
                weather_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(location_id, forecast_date)
            );
        ''')
        
        # Create AI summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_summaries (
                id SERIAL PRIMARY KEY,
                location_id INTEGER REFERENCES locations(id),
                forecast_date DATE NOT NULL,
                summary_text TEXT NOT NULL,
                summary_data JSONB,
                ai_provider VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL
            );
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Database initialized successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Database initialization failed: {str(e)}'}), 500

def get_location_coords(city, state=None, country='US'):
    """Get coordinates for a city using OpenWeatherMap Geocoding API"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return None, "OpenWeatherMap API key not configured"
    
    # Build location string
    location = f"{city}"
    if state:
        location += f",{state}"
    if country:
        location += f",{country}"
    
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
    
    try:
        response = requests.get(geocoding_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None, f"Location not found: {location}"
            
        location_data = data[0]
        return {
            'lat': location_data['lat'],
            'lon': location_data['lon'],
            'name': location_data['name'],
            'state': location_data.get('state', ''),
            'country': location_data['country']
        }, None
        
    except Exception as e:
        return None, f"Geocoding error: {str(e)}"

def fetch_current_weather(lat, lon):
    """Fetch current weather from OpenWeatherMap"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return None, "OpenWeatherMap API key not configured"
    
    # Use Current Weather API (free tier)
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    
    try:
        response = requests.get(weather_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data, None
        
    except Exception as e:
        return None, f"Current weather API error: {str(e)}"

def fetch_weather_forecast(lat, lon):
    """Fetch 5-day weather forecast from OpenWeatherMap"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return None, "OpenWeatherMap API key not configured"
    
    # Use 5 Day / 3 Hour Forecast API (free tier)
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    
    try:
        response = requests.get(forecast_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format the forecast data to mimic daily forecasts
        daily_forecasts = []
        current_day = None
        day_data = {}
        
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).date()
            
            if current_day != date:
                # Save previous day if exists
                if day_data:
                    daily_forecasts.append(day_data)
                
                # Start new day
                current_day = date
                day_data = {
                    'dt': item['dt'],
                    'date': date.isoformat(),
                    'weather': item['weather'],
                    'temp': {
                        'min': item['main']['temp'],
                        'max': item['main']['temp'],
                        'day': item['main']['temp']
                    },
                    'humidity': item['main']['humidity'],
                    'pressure': item['main']['pressure'],
                    'wind_speed': item['wind']['speed'],
                    'wind_deg': item['wind'].get('deg', 0),
                    'clouds': item['clouds']['all'],
                    'pop': item.get('pop', 0) * 100  # Convert to percentage
                }
            else:
                # Update min/max for the day
                day_data['temp']['min'] = min(day_data['temp']['min'], item['main']['temp'])
                day_data['temp']['max'] = max(day_data['temp']['max'], item['main']['temp'])
        
        # Add the last day
        if day_data:
            daily_forecasts.append(day_data)
        
        # Format the complete forecast data
        formatted_forecast = {
            'location': {'lat': lat, 'lon': lon},
            'daily': daily_forecasts[:5],  # 5-day forecast
            'timezone': 'America/Chicago',  # Default timezone
            'fetched_at': datetime.now().isoformat()
        }
        
        return formatted_forecast, None
        
    except Exception as e:
        return None, f"Weather API error: {str(e)}"

@app.route('/api/weather/stlouis')
def get_stlouis_weather():
    """Get current weather and 5-day forecast for St. Louis, MO"""
    try:
        # Get St. Louis coordinates
        location, error = get_location_coords("St. Louis", "MO", "US")
        if error:
            return jsonify({'error': error}), 400
        
        # Fetch current weather
        current_weather, error = fetch_current_weather(location['lat'], location['lon'])
        if error:
            return jsonify({'error': error}), 500
            
        # Fetch weather forecast
        forecast, error = fetch_weather_forecast(location['lat'], location['lon'])
        if error:
            return jsonify({'error': error}), 500
        
        # Combine current weather and forecast
        combined_data = {
            'location': location,
            'current': current_weather,
            'forecast': forecast,
            'fetched_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': combined_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch weather: {str(e)}'}), 500

@app.route('/dashboard')
def weather_dashboard():
    """Simple frontend dashboard for St. Louis weather"""
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stratus Weather - St. Louis Forecast</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            min-height: 100vh;
            color: #2d3436;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .current-weather {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .current-temp {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .temp-display {
            font-size: 4rem;
            font-weight: bold;
            color: #74b9ff;
            margin-bottom: 10px;
        }
        
        .weather-desc {
            font-size: 1.5rem;
            color: #636e72;
            text-transform: capitalize;
        }
        
        .weather-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .detail-item {
            text-align: center;
            padding: 15px;
            background: rgba(116, 185, 255, 0.1);
            border-radius: 10px;
        }
        
        .detail-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #0984e3;
        }
        
        .detail-label {
            font-size: 0.9rem;
            color: #636e72;
            margin-top: 5px;
        }
        
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .day-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .day-card:hover {
            transform: translateY(-5px);
        }
        
        .day-name {
            font-weight: bold;
            color: #2d3436;
            margin-bottom: 10px;
        }
        
        .day-icon {
            width: 50px;
            height: 50px;
            margin: 10px auto;
        }
        
        .day-temps {
            margin-top: 10px;
        }
        
        .high-temp {
            font-size: 1.2rem;
            font-weight: bold;
            color: #e17055;
        }
        
        .low-temp {
            font-size: 1rem;
            color: #74b9ff;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2rem;
            margin: 50px 0;
        }
        
        .error {
            background: #ff6b6b;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }
        
        .section-title {
            color: white;
            font-size: 1.5rem;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌤️ Stratus Weather</h1>
            <p>5-Day Forecast for St. Louis, Missouri</p>
        </div>
        
        <div id="loading" class="loading">
            ⏳ Loading weather data...
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <div id="weather-content" style="display: none;">
            <!-- Current Weather -->
            <div class="current-weather">
                <div class="current-temp">
                    <div id="current-temp" class="temp-display">--°</div>
                    <div id="current-desc" class="weather-desc">Loading...</div>
                </div>
                
                <div class="weather-details">
                    <div class="detail-item">
                        <div id="feels-like" class="detail-value">--°</div>
                        <div class="detail-label">Feels Like</div>
                    </div>
                    <div class="detail-item">
                        <div id="humidity" class="detail-value">--%</div>
                        <div class="detail-label">Humidity</div>
                    </div>
                    <div class="detail-item">
                        <div id="wind-speed" class="detail-value">-- mph</div>
                        <div class="detail-label">Wind Speed</div>
                    </div>
                    <div class="detail-item">
                        <div id="uv-index" class="detail-value">--</div>
                        <div class="detail-label">UV Index</div>
                    </div>
                </div>
            </div>
            
            <!-- 5-Day Forecast -->
            <h2 class="section-title">📅 5-Day Forecast</h2>
            <div id="forecast-grid" class="forecast-grid">
                <!-- Forecast cards will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        // Function to format day names
        function getDayName(timestamp) {
            const date = new Date(timestamp * 1000);
            const today = new Date();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            if (date.toDateString() === today.toDateString()) {
                return 'Today';
            } else if (date.toDateString() === tomorrow.toDateString()) {
                return 'Tomorrow';
            } else {
                return date.toLocaleDateString('en-US', { weekday: 'short' });
            }
        }
        
        // Function to get weather icon URL
        function getIconUrl(iconCode) {
            return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        }
        
        // Load weather data
        async function loadWeather() {
            try {
                const response = await fetch('/api/weather/stlouis');
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load weather data');
                }
                
                displayWeather(data);
                
            } catch (error) {
                console.error('Weather loading error:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = `Error: ${error.message}`;
            }
        }
        
        function displayWeather(data) {
            const weatherData = data.data;
            const current = weatherData.current;
            const daily = weatherData.forecast.daily;
            
            // Update current weather
            document.getElementById('current-temp').textContent = Math.round(current.main.temp) + '°F';
            document.getElementById('current-desc').textContent = current.weather[0].description;
            document.getElementById('feels-like').textContent = Math.round(current.main.feels_like) + '°F';
            document.getElementById('humidity').textContent = current.main.humidity + '%';
            document.getElementById('wind-speed').textContent = Math.round(current.wind.speed) + ' mph';
            document.getElementById('uv-index').textContent = 'N/A'; // UV index not available in current weather API
            
            // Create forecast cards
            const forecastGrid = document.getElementById('forecast-grid');
            forecastGrid.innerHTML = '';
            
            daily.forEach((day, index) => {
                const dayCard = document.createElement('div');
                dayCard.className = 'day-card';
                
                dayCard.innerHTML = `
                    <div class="day-name">${getDayName(day.dt)}</div>
                    <img src="${getIconUrl(day.weather[0].icon)}" alt="${day.weather[0].description}" class="day-icon">
                    <div class="day-temps">
                        <div class="high-temp">${Math.round(day.temp.max)}°</div>
                        <div class="low-temp">${Math.round(day.temp.min)}°</div>
                    </div>
                `;
                
                forecastGrid.appendChild(dayCard);
            });
            
            // Show content and hide loading
            document.getElementById('loading').style.display = 'none';
            document.getElementById('weather-content').style.display = 'block';
        }
        
        // Load weather when page loads
        window.addEventListener('load', loadWeather);
    </script>
</body>
</html>
    '''
    return render_template_string(html_template)

if __name__ == '__main__':
    # Railway provides the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 