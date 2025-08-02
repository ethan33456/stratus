from flask import render_template_string

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
        .search-bar {
            position: absolute;
            top: 10px;
            right: 20px;
            display: flex;
            gap: 5px;
        }

        .search-bar input[type="text"] {
            padding: 6px 10px;
            border-radius: 5px;
            border: none;
            font-size: 1rem;
        }

        .search-bar button:hover {
            background: #74b9ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Stratus Weather</h1>
            <p id="location-display">Detecting your location...</p>
            <form id="search-form" class="search-bar" onsubmit="searchCity(event)">
            <input type="text" id="city-input" placeholder="Search city" required>
            </form>
        </div>
        
        <div id="loading" class="loading">
            <div id="loading-message">⏳ Detecting your location...</div>
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
        function getDayName(timestamp, index) {
            const date = new Date(timestamp * 1000);
            const today = new Date();
            
            // Get just the date part (YYYY-MM-DD) for comparison
            const dateStr = date.toISOString().split('T')[0];
            const todayStr = today.toISOString().split('T')[0];
            
            if (dateStr === todayStr) {
                return 'Today';
            } else {
                // For subsequent days, calculate the correct day name based on index
                const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const todayIndex = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
                const targetIndex = (todayIndex + index) % 7;
                return daysOfWeek[targetIndex];
            }
        }
        
        // Function to get weather icon URL
        function getIconUrl(iconCode) {
            return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        }
        
        // Get user's location and load weather data
        async function loadWeather() {
            try {
                // Update loading message
                document.getElementById('loading-message').textContent = '⏳ Detecting your location...';
                
                // Try to get user's location
                const position = await getCurrentPosition();
                const { latitude, longitude } = position.coords;
                
                // Update loading message
                document.getElementById('loading-message').textContent = '⏳ Loading weather data...';
                
                // Load weather for user's location
                const response = await fetch(`/api/weather/coords?lat=${latitude}&lon=${longitude}`);
                
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
                
                // If location detection fails, fall back to St. Louis
                try {
                    console.log('Falling back to St. Louis weather...');
                    document.getElementById('loading-message').textContent = '⏳ Loading St. Louis weather...';
                    const fallbackResponse = await fetch('/api/weather/stlouis');
                    
                    if (!fallbackResponse.ok) {
                        throw new Error(`HTTP ${fallbackResponse.status}: ${fallbackResponse.statusText}`);
                    }
                    
                    const fallbackData = await fallbackResponse.json();
                    
                    if (!fallbackData.success) {
                        throw new Error(fallbackData.error || 'Failed to load fallback weather data');
                    }
                    
                    displayWeather(fallbackData);
                    
                } catch (fallbackError) {
                    console.error('Fallback weather loading error:', fallbackError);
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error').style.display = 'block';
                    document.getElementById('error').textContent = `Error: ${fallbackError.message}`;
                }
            }
        }
        
        // Get user's current position
        function getCurrentPosition() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation is not supported by this browser'));
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        resolve(position);
                    },
                    (error) => {
                        reject(new Error('Unable to get your location'));
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000 // 5 minutes
                    }
                );
            });
        }
        
        function displayWeather(data) {
            const weatherData = data.data;
            const current = weatherData.current;
            const daily = weatherData.forecast.daily;
            const location = weatherData.location;
            
            // Update location display
            const locationDisplay = document.getElementById('location-display');
            if (location && location.name) {
                let locationText = `5-Day Forecast for ${location.name}`;
                if (location.state) {
                    locationText += `, ${location.state}`;
                }
                if (location.country) {
                    locationText += `, ${location.country}`;
                }
                locationDisplay.textContent = locationText;
            } else {
                locationDisplay.textContent = '5-Day Forecast for Your Location';
            }
            
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
                    <div class="day-name">${getDayName(day.dt, index)}</div>
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
