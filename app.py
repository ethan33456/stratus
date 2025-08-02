from flask import Flask, jsonify, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, timedelta
from dashboard import weather_dashboard
from ai_weather import get_comprehensive_ai_analysis, get_comprehensive_ai_analysis_async
import threading
import time

app = Flask(__name__)

# Store AI analysis futures
ai_futures = {}

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
                created_at TIMESTAMP DEFAULT NOW()
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
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return None, "OpenWeatherMap API key not found"
        
        # Build query
        query_parts = [city]
        if state:
            query_parts.append(state)
        if country:
            query_parts.append(country)
        
        query = ','.join(query_parts)
        
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return None, f"No coordinates found for {query}"
        
        location = data[0]
        return {
            'name': location.get('name', city),
            'lat': location.get('lat'),
            'lon': location.get('lon'),
            'state': location.get('state', state),
            'country': location.get('country', country)
        }, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error getting coordinates: {str(e)}"

def get_location_from_coords(lat, lon):
    """Get location name from coordinates using OpenWeatherMap Reverse Geocoding API"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return None, "OpenWeatherMap API key not found"
        
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return None, f"No location found for coordinates ({lat}, {lon})"
        
        location = data[0]
        return {
            'name': location.get('name', 'Unknown'),
            'lat': lat,
            'lon': lon,
            'state': location.get('state', ''),
            'country': location.get('country', '')
        }, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error getting location: {str(e)}"

def fetch_current_weather(lat, lon):
    """Fetch current weather data from OpenWeatherMap API"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return None, "OpenWeatherMap API key not found"
        
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json(), None
        
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error fetching current weather: {str(e)}"

def fetch_weather_forecast(lat, lon):
    """Fetch 5-day weather forecast from OpenWeatherMap API"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return None, "OpenWeatherMap API key not found"
        
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Process forecast data to get daily forecasts
        daily_forecasts = []
        current_date = None
        daily_data = {}
        
        for item in data.get('list', []):
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if date != current_date:
                if current_date and daily_data:
                    daily_forecasts.append(daily_data)
                
                current_date = date
                daily_data = {
                    'dt': item['dt'],
                    'temp': {
                        'day': item['main']['temp'],
                        'min': item['main']['temp_min'],
                        'max': item['main']['temp_max']
                    },
                    'humidity': item['main']['humidity'],
                    'weather': item['weather']
                }
            else:
                # Update min/max temperatures for the same day
                daily_data['temp']['min'] = min(daily_data['temp']['min'], item['main']['temp_min'])
                daily_data['temp']['max'] = max(daily_data['temp']['max'], item['main']['temp_max'])
        
        # Add the last day
        if daily_data:
            daily_forecasts.append(daily_data)
        
        return {
            'daily': daily_forecasts[:5]  # Return 5 days
        }, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error fetching forecast: {str(e)}"

@app.route('/api/weather/coords')
def get_weather_by_coords():
    """Get weather data for specific coordinates"""
    try:
        from flask import request
        
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Get location name
        location, error = get_location_from_coords(lat, lon)
        if error:
            print(f"Location lookup error: {error}")
            location = {
                'name': f'Location ({lat}, {lon})',
                'lat': float(lat),
                'lon': float(lon),
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
            return jsonify({'error': 'Search query is required'}), 400
        
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenWeatherMap API key not found'}), 500
        
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        locations = response.json()
        
        # Format locations for frontend
        formatted_locations = []
        for loc in locations:
            formatted_locations.append({
                'name': loc.get('name', ''),
                'state': loc.get('state', ''),
                'country': loc.get('country', ''),
                'lat': loc.get('lat'),
                'lon': loc.get('lon')
            })
        
        return jsonify({
            'success': True,
            'locations': formatted_locations
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/weather/location')
def get_weather_by_location():
    """Get weather data for a specific location (used by autocomplete selection)"""
    try:
        from flask import request
        
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Get location name
        location, error = get_location_from_coords(lat, lon)
        if error:
            print(f"Location lookup error: {error}")
            location = {
                'name': f'Location ({lat}, {lon})',
                'lat': float(lat),
                'lon': float(lon),
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
    """Get weather data for a location based on search query"""
    try:
        from flask import request
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Get coordinates for the search query
        location, error = get_location_coords(query)
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

@app.route('/api/ai/analyze')
def analyze_weather_with_ai():
    """Get AI-powered weather analysis - starts async analysis"""
    try:
        from flask import request
        
        # Get parameters
        user_lat = request.args.get('user_lat')
        user_lon = request.args.get('user_lon')
        target_lat = request.args.get('target_lat')
        target_lon = request.args.get('target_lon')
        
        print(f"AI analyze called with: user_lat={user_lat}, user_lon={user_lon}, target_lat={target_lat}, target_lon={target_lon}")
        
        if not all([user_lat, user_lon, target_lat, target_lon]):
            return jsonify({'error': 'All coordinates are required'}), 400
        
        # Get user location name
        print(f"Getting user location from coords: {user_lat}, {user_lon}")
        user_location, _ = get_location_from_coords(float(user_lat), float(user_lon))
        if not user_location:
            user_location = {
                'lat': float(user_lat),
                'lon': float(user_lon),
                'name': f'Location ({user_lat}, {user_lon})',
                'state': '',
                'country': ''
            }
        print(f"User location: {user_location}")
        
        # Get target location name
        print(f"Getting target location from coords: {target_lat}, {target_lon}")
        target_location, _ = get_location_from_coords(float(target_lat), float(target_lon))
        if not target_location:
            target_location = {
                'lat': float(target_lat),
                'lon': float(target_lon),
                'name': f'Location ({target_lat}, {target_lon})',
                'state': '',
                'country': ''
            }
        print(f"Target location: {target_location}")
        
        # Get weather data for target location
        print(f"Fetching current weather for target location...")
        current_weather, error = fetch_current_weather(target_lat, target_lon)
        if error:
            print(f"Current weather error: {error}")
            return jsonify({'error': error}), 500
            
        print(f"Fetching forecast for target location...")
        forecast, error = fetch_weather_forecast(target_lat, target_lon)
        if error:
            print(f"Forecast error: {error}")
            return jsonify({'error': error}), 500
        
        weather_data = {
            'current': current_weather,
            'forecast': forecast
        }
        print(f"Weather data structure: current={bool(current_weather)}, forecast={bool(forecast)}")
        
        # Start async AI analysis
        print(f"Starting async AI analysis...")
        ai_analysis = get_comprehensive_ai_analysis_async(user_location, target_location, weather_data)
        
        # Store the future for later retrieval (don't include in response)
        analysis_id = f"{user_lat}_{user_lon}_{target_lat}_{target_lon}_{int(time.time())}"
        
        # Start the actual AI analysis in background
        def run_ai_analysis():
            try:
                print(f"Running AI analysis in background for {analysis_id}")
                result = get_comprehensive_ai_analysis(user_location, target_location, weather_data)
                ai_futures[analysis_id] = result
                print(f"AI analysis completed for {analysis_id}")
            except Exception as e:
                print(f"Background AI analysis error: {e}")
                ai_futures[analysis_id] = {
                    "context_warnings": [],
                    "suggestions": ["AI analysis failed"],
                    "fun_facts": ["Unable to generate insights"],
                    "climate_comparison": "Analysis unavailable",
                    "ai_generated": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Start background thread
        import threading
        thread = threading.Thread(target=run_ai_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'user_location': user_location,
            'target_location': target_location,
            'weather_data': weather_data,
            'ai_analysis': ai_analysis
        })
        
    except Exception as e:
        print(f"AI analyze endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/ai/result/<analysis_id>')
def get_ai_analysis_result(analysis_id):
    """Get the result of an async AI analysis"""
    try:
        if analysis_id not in ai_futures:
            return jsonify({'error': 'Analysis ID not found'}), 404
        
        result = ai_futures[analysis_id]
        
        # Check if analysis is complete (has ai_generated field)
        if isinstance(result, dict) and 'ai_generated' in result:
            # Analysis is complete, clean up
            completed_result = ai_futures.pop(analysis_id)
            return jsonify({
                'success': True,
                'result': completed_result,
                'completed': True
            })
        else:
            return jsonify({
                'success': True,
                'completed': False,
                'message': 'Analysis still in progress'
            })
            
    except Exception as e:
        print(f"AI result endpoint error: {e}")
        return jsonify({'error': f'Failed to get AI result: {str(e)}'}), 500

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