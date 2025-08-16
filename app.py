from flask import Flask, jsonify, render_template_string, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, timedelta
from dashboard import weather_dashboard
from ai_weather import get_comprehensive_ai_analysis, get_comprehensive_ai_analysis_async
import threading
import time
from openai import OpenAI
import bcrypt
import secrets
import re
from functools import wraps

app = Flask(__name__)

# Store AI analysis futures
ai_futures = {}

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Authentication configuration
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
SESSION_DURATION_HOURS = 24  # Sessions expire after 24 hours

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

# Authentication utility functions
def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (3-20 characters, alphanumeric and underscore only)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Validate password strength (minimum 6 characters)"""
    return len(password) >= 6

def get_user_by_session_token(session_token):
    """Get user by session token"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        # Get active session and user info
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.created_at
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = %s 
            AND s.is_active = TRUE 
            AND s.expires_at > NOW()
        ''', (session_token,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return user
        
    except Exception as e:
        print(f"Error getting user by session token: {e}")
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get session token from request headers or cookies
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not session_token:
            session_token = request.cookies.get('session_token')
        
        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify session token
        user = get_user_by_session_token(session_token)
        if not user:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

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

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate input
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if not validate_username(username):
            return jsonify({'error': 'Username must be 3-20 characters, alphanumeric and underscore only'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_password(password):
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if username or email already exists
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check username
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Username already exists'}), 409
        
        # Check email
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already exists'}), 409
        
        # Hash password and create user
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id, username, email, created_at
        ''', (username, email, password_hash))
        
        new_user = cursor.fetchone()
        
        # Create session token
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
        ''', (new_user['id'], session_token, expires_at))
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = NOW() WHERE id = %s
        ''', (new_user['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Create response
        response = jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'id': new_user['id'],
                'username': new_user['username'],
                'email': new_user['email'],
                'created_at': new_user['created_at'].isoformat()
            },
            'session_token': session_token
        })
        
        # Set secure cookie
        response.set_cookie(
            'session_token', 
            session_token, 
            max_age=SESSION_DURATION_HOURS * 3600,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Login user and create session"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        # Determine if input is email or username
        is_email = '@' in username_or_email
        username_or_email = username_or_email.lower() if is_email else username_or_email
        
        # Get user from database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        if is_email:
            cursor.execute('SELECT id, username, email, password_hash, created_at FROM users WHERE email = %s AND is_active = TRUE', (username_or_email,))
        else:
            cursor.execute('SELECT id, username, email, password_hash, created_at FROM users WHERE username = %s AND is_active = TRUE', (username_or_email,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid username/email or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid username/email or password'}), 401
        
        # Create new session token
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
        
        # Deactivate old sessions for this user
        cursor.execute('UPDATE user_sessions SET is_active = FALSE WHERE user_id = %s', (user['id'],))
        
        # Create new session
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
        ''', (user['id'], session_token, expires_at))
        
        # Update last login
        cursor.execute('UPDATE users SET last_login = NOW() WHERE id = %s', (user['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Create response
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'].isoformat()
            },
            'session_token': session_token
        })
        
        # Set secure cookie
        response.set_cookie(
            'session_token', 
            session_token, 
            max_age=SESSION_DURATION_HOURS * 3600,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """Logout user and invalidate session"""
    try:
        # Get session token from request
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not session_token:
            session_token = request.cookies.get('session_token')
        
        if session_token:
            # Invalidate session in database
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE user_sessions SET is_active = FALSE WHERE session_token = %s', (session_token,))
                conn.commit()
                cursor.close()
                conn.close()
        
        # Create response
        response = jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        
        # Clear cookie
        response.delete_cookie('session_token')
        
        return response
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    return jsonify({
        'success': True,
        'user': {
            'id': request.current_user['id'],
            'username': request.current_user['username'],
            'email': request.current_user['email'],
            'created_at': request.current_user['created_at'].isoformat()
        }
    })

@app.route('/api/health')
def health_check():
    # Test the database connection
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
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        ''')
        
        # Create saved locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_locations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                lat DECIMAL(10, 8) NOT NULL,
                lon DECIMAL(11, 8) NOT NULL,
                state VARCHAR(100),
                country VARCHAR(100),
                display_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                last_accessed TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, lat, lon)
            );
        ''')
        
        # Create user sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            );
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_locations_user_id ON saved_locations(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Database initialized successfully with user tables'})
        
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

def fetch_weather_data(lat, lon):
    """Fetch all weather data using One Call API 3.0"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return None, "OpenWeatherMap API key not found"
        
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units=imperial&exclude=minutely"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"One Call API response: {data}")  # Debug
        
        # Process the data to match our expected format
        current_weather = {
            'main': {
                'temp': data['current']['temp'],
                'feels_like': data['current']['feels_like'],
                'humidity': data['current']['humidity'],
                'pressure': data['current']['pressure']
            },
            'weather': data['current']['weather'],
            'wind': {
                'speed': data['current']['wind_speed']
            },
            'visibility': data['current'].get('visibility', 10000),
            'clouds': {
                'all': data['current'].get('clouds', 0)
            },
            'sys': {
                'sunrise': data['current']['sunrise'],
                'sunset': data['current']['sunset']
            }
        }
        
        # Process hourly forecast (next 12 hours)
        hourly_forecasts = []
        for hour in data['hourly'][:12]:  # Get next 12 hours
            hourly_forecasts.append({
                'dt': hour['dt'],
                'temp': hour['temp'],
                'weather': hour['weather'],
                'pop': hour.get('pop', 0)  # Probability of precipitation
            })
        
        # Process daily forecast (8 days)
        daily_forecasts = []
        for day in data['daily'][:8]:  # Get 8 days
            daily_forecasts.append({
                'dt': day['dt'],
                'temp': {
                    'day': day['temp']['day'],
                    'min': day['temp']['min'],
                    'max': day['temp']['max']
                },
                'humidity': day['humidity'],
                'weather': day['weather'],
                'pop': day.get('pop', 0),  # Probability of precipitation
                'uvi': day.get('uvi', 0)   # UV index
            })
        
        forecast_data = {
            'hourly': hourly_forecasts,
            'daily': daily_forecasts
        }
        
        return {
            'current': current_weather,
            'forecast': forecast_data
        }, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error fetching weather data: {str(e)}"

@app.route('/api/weather/coords')
def get_weather_by_coords():
    """Get weather data for specific coordinates"""
    try:
        from flask import request
        
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Obtain location name
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
        
        # Fetch weather data
        weather_data, error = fetch_weather_data(lat, lon)
        if error:
            return jsonify({'error': error}), 500
            
        # Combine current weather and forecast
        combined_data = {
            'location': location,
            'current': weather_data['current'],
            'forecast': weather_data['forecast'],
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
        
        # Fetch weather data
        weather_data, error = fetch_weather_data(lat, lon)
        if error:
            return jsonify({'error': error}), 500
            
        # Combine current weather and forecast
        combined_data = {
            'location': location,
            'current': weather_data['current'],
            'forecast': weather_data['forecast'],
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
        
        # Fetch weather data
        weather_data, error = fetch_weather_data(location['lat'], location['lon'])
        if error:
            return jsonify({'error': error}), 500
            
        # Combine current weather and forecast
        combined_data = {
            'location': location,
            'current': weather_data['current'],
            'forecast': weather_data['forecast'],
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
        print(f"Fetching weather data for target location...")
        weather_data, error = fetch_weather_data(target_lat, target_lon)
        if error:
            print(f"Weather data error: {error}")
            return jsonify({'error': error}), 500
        
        # Extract current and forecast from the weather data
        current_weather = weather_data['current']
        forecast = weather_data['forecast']
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
        
        # Fetch weather data
        weather_data, error = fetch_weather_data(location['lat'], location['lon'])
        if error:
            return jsonify({'error': error}), 500
            
        # Combine current weather and forecast
        combined_data = {
            'location': location,
            'current': weather_data['current'],
            'forecast': weather_data['forecast'],
            'fetched_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': combined_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch weather: {str(e)}'}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """AI chatbot for weather and location questions"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        weather_context = data.get('weather_context', {})
        ai_insights = data.get('ai_insights', {})
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Check if OpenAI API key is available
        if not openai_client.api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Build context from weather data and AI insights
        context_parts = []
        
        # Add location context
        if weather_context.get('location'):
            loc = weather_context['location']
            context_parts.append(f"Current location: {loc.get('name', '')}, {loc.get('state', '')}, {loc.get('country', '')}")
        
        # Add current weather context
        if weather_context.get('current'):
            current = weather_context['current']
            temp = current.get('main', {}).get('temp', 'Unknown')
            feels_like = current.get('main', {}).get('feels_like', 'Unknown')
            description = current.get('weather', [{}])[0].get('description', 'Unknown')
            humidity = current.get('main', {}).get('humidity', 'Unknown')
            pressure = current.get('main', {}).get('pressure', 'Unknown')
            wind_speed = current.get('wind', {}).get('speed', 'Unknown')
            visibility = current.get('visibility', 'Unknown')
            clouds = current.get('clouds', {}).get('all', 'Unknown')
            sunrise = current.get('sys', {}).get('sunrise', 'Unknown')
            sunset = current.get('sys', {}).get('sunset', 'Unknown')
            
            context_parts.append(f"Current weather: {temp}°F (feels like {feels_like}°F), {description}")
            context_parts.append(f"Humidity: {humidity}%, Pressure: {pressure} hPa, Wind: {wind_speed} mph")
            context_parts.append(f"Visibility: {visibility/1000 if visibility != 'Unknown' else 'Unknown'} km, Cloud cover: {clouds}%")
            if sunrise != 'Unknown' and sunset != 'Unknown':
                sunrise_time = datetime.fromtimestamp(sunrise).strftime('%I:%M %p')
                sunset_time = datetime.fromtimestamp(sunset).strftime('%I:%M %p')
                context_parts.append(f"Sunrise: {sunrise_time}, Sunset: {sunset_time}")
        
        # Add detailed daily forecast context (today's data including UV index)
        if weather_context.get('forecast', {}).get('daily'):
            daily_forecast = weather_context['forecast']['daily']
            today = daily_forecast[0] if daily_forecast else None
            
            if today:
                uv_index = today.get('uvi', 'Unknown')
                pop = today.get('pop', 0) * 100 if today.get('pop') != 'Unknown' else 'Unknown'
                day_temp = today.get('temp', {}).get('day', 'Unknown')
                min_temp = today.get('temp', {}).get('min', 'Unknown')
                max_temp = today.get('temp', {}).get('max', 'Unknown')
                
                context_parts.append(f"Today's forecast: High {max_temp}°F, Low {min_temp}°F")
                context_parts.append(f"UV Index: {uv_index}, Chance of precipitation: {pop}%")
        
        # Add hourly forecast context
        if weather_context.get('forecast', {}).get('hourly'):
            hourly_forecast = weather_context['forecast']['hourly']
            context_parts.append(f"12-hour forecast: {len(hourly_forecast)} hours of detailed data available")
            
            # Add next few hours context
            if len(hourly_forecast) >= 3:
                next_hours = []
                for i, hour in enumerate(hourly_forecast[:3]):
                    hour_time = datetime.fromtimestamp(hour['dt']).strftime('%I %p')
                    hour_temp = hour.get('temp', 'Unknown')
                    hour_desc = hour.get('weather', [{}])[0].get('description', 'Unknown')
                    hour_pop = hour.get('pop', 0) * 100 if hour.get('pop') != 'Unknown' else 0
                    next_hours.append(f"{hour_time}: {hour_temp}°F, {hour_desc}, {hour_pop}% rain chance")
                context_parts.append(f"Next few hours: {'; '.join(next_hours)}")
        
        # Add extended daily forecast context
        if weather_context.get('forecast', {}).get('daily'):
            daily_forecast = weather_context['forecast']['daily']
            context_parts.append(f"8-day forecast: {len(daily_forecast)} days available")
            
            # Add next few days summary
            if len(daily_forecast) >= 4:
                upcoming_days = []
                for i, day in enumerate(daily_forecast[1:4]):  # Skip today, get next 3 days
                    day_date = datetime.fromtimestamp(day['dt']).strftime('%A')
                    day_high = day.get('temp', {}).get('max', 'Unknown')
                    day_low = day.get('temp', {}).get('min', 'Unknown')
                    day_desc = day.get('weather', [{}])[0].get('description', 'Unknown')
                    day_pop = day.get('pop', 0) * 100 if day.get('pop') != 'Unknown' else 0
                    upcoming_days.append(f"{day_date}: {day_high}°F/{day_low}°F, {day_desc}, {day_pop}% rain")
                context_parts.append(f"Upcoming days: {'; '.join(upcoming_days)}")
        
        # Add AI insights context
        if ai_insights.get('suggestions'):
            context_parts.append(f"AI suggestions: {'; '.join(ai_insights['suggestions'][:3])}")
        
        # Create system prompt
        system_prompt = f"""You are a helpful weather assistant chatbot. You can only answer questions related to weather and location information.

Current context:
{chr(10).join(context_parts)}

Guidelines:
- Only answer weather and location-related questions
- Use the provided context to give accurate, specific answers
- If asked about non-weather topics, politely redirect to weather questions
- Keep responses concise and helpful
- Reference specific data from the context when relevant"""

        # Make OpenAI API call
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        bot_response = response.choices[0].message.content.strip()
        
        return jsonify({
            'success': True,
            'response': bot_response
        })
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Sorry, I encountered an error. Please try again.'
        }), 500

if __name__ == '__main__':
    # Railway provides the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
