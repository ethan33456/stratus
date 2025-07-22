from flask import Flask, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor

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

if __name__ == '__main__':
    # Railway provides the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 