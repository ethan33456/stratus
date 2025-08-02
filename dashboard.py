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
        .search-container {
            position: relative;
            margin: 20px auto;
            max-width: 400px;
        }

        .search-form {
            display: flex;
            gap: 10px;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            padding: 10px 20px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }

        .search-input {
            flex: 1;
            border: none;
            background: transparent;
            font-size: 1rem;
            outline: none;
            color: #2d3436;
        }

        .search-input::placeholder {
            color: #636e72;
        }

        .search-button {
            background: #74b9ff;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.3s ease;
        }

        .search-button:hover {
            background: #0984e3;
        }

        .autocomplete-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }

        .autocomplete-item {
            padding: 12px 20px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s ease;
        }

        .autocomplete-item:hover {
            background: #f8f9fa;
        }

        .autocomplete-item:last-child {
            border-bottom: none;
        }

        .location-name {
            font-weight: bold;
            color: #2d3436;
        }

        .location-details {
            font-size: 0.8rem;
            color: #636e72;
            margin-top: 2px;
        }

        .current-location-btn {
            background: rgba(255, 255, 255, 0.9);
            color: #2d3436;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-top: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .current-location-btn:hover {
            background: rgba(255, 255, 255, 1);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .ai-insights {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }

        .ai-insights h3 {
            color: #2d3436;
            font-size: 1.3rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }

        .insight-section {
            background: rgba(116, 185, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            border-left: 4px solid #74b9ff;
        }

        .insight-section h4 {
            color: #0984e3;
            font-size: 1rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .insight-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .insight-list li {
            color: #2d3436;
            font-size: 0.9rem;
            margin-bottom: 6px;
            padding-left: 15px;
            position: relative;
        }

        .insight-list li:before {
            content: "•";
            color: #74b9ff;
            font-weight: bold;
            position: absolute;
            left: 0;
        }

        .climate-comparison {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            border-radius: 10px;
            padding: 12px;
            margin-top: 15px;
            color: #2d3436;
            font-size: 0.9rem;
            font-style: italic;
        }

        .ai-loading {
            text-align: center;
            color: #636e72;
            font-style: italic;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Stratus Weather</h1>
            <p id="location-display">Detecting your location...</p>
        </div>
        
        <div class="search-container">
            <form id="search-form" class="search-form" onsubmit="searchLocation(event)">
                <input 
                    type="text" 
                    id="search-input" 
                    class="search-input" 
                    placeholder="Search for a city..." 
                    autocomplete="off"
                >
                <button type="submit" class="search-button">Search</button>
            </form>
            <div id="autocomplete-dropdown" class="autocomplete-dropdown"></div>
            <button id="current-location-btn" class="current-location-btn" onclick="loadCurrentLocation()">
                📍 My Location
            </button>
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
            
            <!-- AI Insights -->
            <div id="ai-insights" class="ai-insights" style="display: none;">
                <h3>🤖 AI Weather Insights</h3>
                <div id="ai-loading" class="ai-loading">
                    ⏳ Analyzing weather patterns and generating insights...
                </div>
                <div id="ai-content" style="display: none;">
                    <div class="insights-grid">
                        <div class="insight-section">
                            <h4>⚠️ Location Context</h4>
                            <ul id="context-warnings" class="insight-list">
                                <!-- Context warnings will be inserted here -->
                            </ul>
                        </div>
                        <div class="insight-section">
                            <h4>💡 Smart Suggestions</h4>
                            <ul id="suggestions" class="insight-list">
                                <!-- Suggestions will be inserted here -->
                            </ul>
                        </div>
                        <div class="insight-section">
                            <h4>🎯 Fun Facts</h4>
                            <ul id="fun-facts" class="insight-list">
                                <!-- Fun facts will be inserted here -->
                            </ul>
                        </div>
                    </div>
                    <div id="climate-comparison" class="climate-comparison">
                        <!-- Climate comparison will be inserted here -->
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
                
                // Store user's current location for AI analysis
                userCurrentLocation = { lat: latitude, lon: longitude };
                
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
                
                // Get AI insights (same location, so minimal analysis)
                const aiAnalysis = await getAIInsights(userCurrentLocation, userCurrentLocation);
                displayAIInsights(aiAnalysis);
                
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
                    
                    // Hide AI insights for fallback
                    document.getElementById('ai-insights').style.display = 'none';
                    
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
        
        // Search and autocomplete functionality
        let searchTimeout;
        const searchInput = document.getElementById('search-input');
        const autocompleteDropdown = document.getElementById('autocomplete-dropdown');
        
        // Add event listeners for search input
        searchInput.addEventListener('input', handleSearchInput);
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.length > 0) {
                showAutocomplete();
            }
        });
        
        // Close autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                hideAutocomplete();
            }
        });
        
        // Handle search input changes
        function handleSearchInput() {
            const query = searchInput.value.trim();
            
            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Hide autocomplete if query is empty
            if (query.length === 0) {
                hideAutocomplete();
                return;
            }
            
            // Debounce the search
            searchTimeout = setTimeout(() => {
                searchLocations(query);
            }, 300);
        }
        
        // Search for locations
        async function searchLocations(query) {
            try {
                const response = await fetch(`/api/search/locations?q=${encodeURIComponent(query)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success && data.locations.length > 0) {
                    showAutocomplete(data.locations);
                } else {
                    hideAutocomplete();
                }
                
            } catch (error) {
                console.error('Search error:', error);
                hideAutocomplete();
            }
        }
        
        // Show autocomplete dropdown
        function showAutocomplete(locations = []) {
            if (locations.length === 0) {
                hideAutocomplete();
                return;
            }
            
            autocompleteDropdown.innerHTML = '';
            
            locations.forEach(location => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.innerHTML = `
                    <div class="location-name">${location.name}</div>
                    <div class="location-details">${location.state ? location.state + ', ' : ''}${location.country}</div>
                `;
                
                item.addEventListener('click', () => {
                    searchInput.value = location.name;
                    hideAutocomplete();
                    loadWeatherForLocation(location);
                });
                
                autocompleteDropdown.appendChild(item);
            });
            
            autocompleteDropdown.style.display = 'block';
        }
        
        // Hide autocomplete dropdown
        function hideAutocomplete() {
            autocompleteDropdown.style.display = 'none';
        }
        
        // Handle form submission
        function searchLocation(event) {
            event.preventDefault();
            const query = searchInput.value.trim();
            
            if (query.length === 0) {
                return;
            }
            
            hideAutocomplete();
            
            // Try to search for the location
            searchLocations(query).then(() => {
                // If autocomplete is shown, the user can click on a result
                // If not, we'll try to load weather for the entered text
                if (autocompleteDropdown.style.display === 'none') {
                    loadWeatherForQuery(query);
                }
            });
        }
        
        // Load weather for a specific location
        async function loadWeatherForLocation(location) {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('weather-content').style.display = 'none';
                document.getElementById('loading-message').textContent = `⏳ Loading weather for ${location.name}...`;
                
                const response = await fetch(`/api/weather/location?lat=${location.lat}&lon=${location.lon}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load weather data');
                }
                
                displayWeather(data);
                
                // Get AI insights if user location is available
                if (userCurrentLocation) {
                    const aiAnalysis = await getAIInsights(userCurrentLocation, location);
                    displayAIInsights(aiAnalysis);
                } else {
                    // Hide AI insights if no user location
                    document.getElementById('ai-insights').style.display = 'none';
                }
                
            } catch (error) {
                console.error('Weather loading error:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = `Error: ${error.message}`;
            }
        }
        
        // Load weather for a search query
        async function loadWeatherForQuery(query) {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('weather-content').style.display = 'none';
                document.getElementById('loading-message').textContent = `⏳ Loading weather for ${query}...`;
                
                const response = await fetch(`/api/weather/search?q=${encodeURIComponent(query)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load weather data');
                }
                
                displayWeather(data);
                
                // Get AI insights if user location is available
                if (userCurrentLocation) {
                    const targetLocation = data.data.location;
                    const aiAnalysis = await getAIInsights(userCurrentLocation, targetLocation);
                    displayAIInsights(aiAnalysis);
                } else {
                    // Hide AI insights if no user location
                    document.getElementById('ai-insights').style.display = 'none';
                }
                
            } catch (error) {
                console.error('Weather loading error:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = `Error: ${error.message}`;
            }
        }
        
        // Store user's current location for AI analysis
        let userCurrentLocation = null;
        
        // Load current location weather
        function loadCurrentLocation() {
            // Clear search input
            searchInput.value = '';
            hideAutocomplete();
            
            // Reload weather for current location
            loadWeather();
        }
        
        // Get AI analysis for weather
        async function getAIInsights(userLocation, targetLocation) {
            try {
                const response = await fetch(`/api/ai/analyze?user_lat=${userLocation.lat}&user_lon=${userLocation.lon}&target_lat=${targetLocation.lat}&target_lon=${targetLocation.lon}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to get AI analysis');
                }
                
                return data.ai_analysis;
                
            } catch (error) {
                console.error('AI analysis error:', error);
                return null;
            }
        }
        
        // Display AI insights
        function displayAIInsights(aiAnalysis) {
            const aiInsights = document.getElementById('ai-insights');
            const aiLoading = document.getElementById('ai-loading');
            const aiContent = document.getElementById('ai-content');
            
            if (!aiAnalysis) {
                aiInsights.style.display = 'none';
                return;
            }
            
            // Show AI insights section
            aiInsights.style.display = 'block';
            aiLoading.style.display = 'none';
            aiContent.style.display = 'block';
            
            // Display context warnings
            const contextWarnings = document.getElementById('context-warnings');
            contextWarnings.innerHTML = '';
            if (aiAnalysis.context_warnings && aiAnalysis.context_warnings.length > 0) {
                aiAnalysis.context_warnings.forEach(warning => {
                    const li = document.createElement('li');
                    li.textContent = warning;
                    contextWarnings.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No specific warnings for this location';
                contextWarnings.appendChild(li);
            }
            
            // Display suggestions
            const suggestions = document.getElementById('suggestions');
            suggestions.innerHTML = '';
            if (aiAnalysis.suggestions && aiAnalysis.suggestions.length > 0) {
                aiAnalysis.suggestions.forEach(suggestion => {
                    const li = document.createElement('li');
                    li.textContent = suggestion;
                    suggestions.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'Check local weather updates regularly';
                suggestions.appendChild(li);
            }
            
            // Display fun facts
            const funFacts = document.getElementById('fun-facts');
            funFacts.innerHTML = '';
            if (aiAnalysis.fun_facts && aiAnalysis.fun_facts.length > 0) {
                aiAnalysis.fun_facts.forEach(fact => {
                    const li = document.createElement('li');
                    li.textContent = fact;
                    funFacts.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'Weather patterns vary by location';
                funFacts.appendChild(li);
            }
            
            // Display climate comparison
            const climateComparison = document.getElementById('climate-comparison');
            if (aiAnalysis.climate_comparison) {
                climateComparison.textContent = aiAnalysis.climate_comparison;
            } else {
                climateComparison.textContent = 'Climate differences may affect how weather feels';
            }
        }
        
        // Load weather when page loads
        window.addEventListener('load', loadWeather);
    </script>
</body>
</html>
    '''
    return render_template_string(html_template) 
