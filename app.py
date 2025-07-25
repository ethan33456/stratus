from flask import Flask, jsonify, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, timedelta
from dashboard import weather_dashboard

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
    """Homepage - displays the weather dashboard"""
    return weather_dashboard()

@app.route('/api')
def api_home():
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



if __name__ == '__main__':
    # Railway provides the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 