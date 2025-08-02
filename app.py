from flask import Flask, jsonify, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, timedelta
from dashboard import weather_dashboard
from ai_weather import get_comprehensive_ai_analysis

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
    if state and country:
        location = f"{city},{state},{country}"
    elif state:
        location = f"{city},{state}"
    elif country:
        location = f"{city},{country}"
    else:
        location = city
    
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

def get_location_from_coords(lat, lon):
    """Get location name from coordinates using OpenWeatherMap Reverse Geocoding API"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return None, "OpenWeatherMap API key not configured"
    
    reverse_geocoding_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
    
    try:
        response = requests.get(reverse_geocoding_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None, f"Location not found for coordinates ({lat}, {lon})"
            
        location_data = data[0]
        return {
            'lat': lat,
            'lon': lon,
            'name': location_data['name'],
            'state': location_data.get('state', ''),
            'country': location_data['country']
        }, None
        
    except Exception as e:
        return None, f"Reverse geocoding error: {str(e)}"

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

@app.route('/api/weather/coords')
def get_weather_by_coords():
    """Get current weather and 5-day forecast for coordinates"""
    try:
        from flask import request
        
        # Get coordinates from query parameters
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Get location name from coordinates using reverse geocoding
        location, error = get_location_from_coords(lat, lon)
        if error:
            # If reverse geocoding fails, create a basic location object
            location = {
                'lat': lat,
                'lon': lon,
                'name': f'Location ({lat:.2f}, {lon:.2f})',
                'state': '',
                'country': ''
            }
        
        # Fetch current weather
        current_weather, error = fetch_current_weather(lat, lon)
        if error:
            return jsonify({'error': error}), 500
            
        # Fetch weather forecast
        forecast, error = fetch_weather_forecast(lat, lon)
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

@app.route('/api/search/locations')
def search_locations():
    """Search for locations using OpenWeatherMap Geocoding API"""
    try:
        from flask import request
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': True, 'locations': []})
        
        # Use the existing get_location_coords function but get multiple results
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenWeatherMap API key not configured'}), 500
        
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={api_key}"
        
        response = requests.get(geocoding_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        locations = []
        for location_data in data:
            locations.append({
                'lat': location_data['lat'],
                'lon': location_data['lon'],
                'name': location_data['name'],
                'state': location_data.get('state', ''),
                'country': location_data['country']
            })
        
        return jsonify({
            'success': True,
            'locations': locations
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/weather/location')
def get_weather_by_location():
    """Get weather for a specific location by coordinates"""
    try:
        from flask import request
        
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Get location name from coordinates
        location, error = get_location_from_coords(lat, lon)
        if error:
            location = {
                'lat': lat,
                'lon': lon,
                'name': f'Location ({lat:.2f}, {lon:.2f})',
                'state': '',
                'country': ''
            }
        
        # Fetch current weather
        current_weather, error = fetch_current_weather(lat, lon)
        if error:
            return jsonify({'error': error}), 500
            
        # Fetch weather forecast
        forecast, error = fetch_weather_forecast(lat, lon)
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

@app.route('/api/weather/search')
def get_weather_by_search():
    """Get weather for a location by search query"""
    try:
        from flask import request
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Get location coordinates from search query
        location, error = get_location_coords(query)
        if error:
            return jsonify({'error': f'Location not found: {query}'}), 404
        
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

@app.route('/api/ai/analyze')
def analyze_weather_with_ai():
    """Get AI-powered weather analysis"""
    try:
        from flask import request
        
        # Get parameters
        user_lat = request.args.get('user_lat')
        user_lon = request.args.get('user_lon')
        target_lat = request.args.get('target_lat')
        target_lon = request.args.get('target_lon')
        
        if not all([user_lat, user_lon, target_lat, target_lon]):
            return jsonify({'error': 'All coordinates are required'}), 400
        
        # Get user location name
        user_location, _ = get_location_from_coords(float(user_lat), float(user_lon))
        if not user_location:
            user_location = {
                'lat': float(user_lat),
                'lon': float(user_lon),
                'name': f'Location ({user_lat}, {user_lon})',
                'state': '',
                'country': ''
            }
        
        # Get target location name
        target_location, _ = get_location_from_coords(float(target_lat), float(target_lon))
        if not target_location:
            target_location = {
                'lat': float(target_lat),
                'lon': float(target_lon),
                'name': f'Location ({target_lat}, {target_lon})',
                'state': '',
                'country': ''
            }
        
        # Get weather data for target location
        current_weather, error = fetch_current_weather(target_lat, target_lon)
        if error:
            return jsonify({'error': error}), 500
            
        forecast, error = fetch_weather_forecast(target_lat, target_lon)
        if error:
            return jsonify({'error': error}), 500
        
        weather_data = {
            'current': current_weather,
            'forecast': forecast
        }
        
        # Get AI analysis
        ai_analysis = get_comprehensive_ai_analysis(user_location, target_location, weather_data)
        
        return jsonify({
            'success': True,
            'user_location': user_location,
            'target_location': target_location,
            'weather_data': weather_data,
            'ai_analysis': ai_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

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