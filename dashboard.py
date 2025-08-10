from flask import render_template_string

def weather_dashboard():
    """Render the weather dashboard with HTML, CSS, and JavaScript"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stratus Weather Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #131333 0%, #030712 50%, #233449 100%);
            min-height: 100vh;
            color: #e8e8e8;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #fff, #fff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
            color: #b8b8b8;
        }

        .search-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            z-index: 99999;
            position: relative;
            margin-bottom: 20px;
        }

        .search-form {
            display: flex;
            gap: 10px;
        }

        .search-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.05);
            color: #e8e8e8;
            transition: all 0.3s ease;
        }

        .search-input:focus {
            outline: none;
            border-color: #667eea;
            background: rgba(255, 255, 255, 0.1);
        }

        .search-input::placeholder {
            color: #888;
        }

        .search-button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }

        .search-button:hover {
            transform: translateY(-2px);
        }

        #current-location-btn {
            padding: 12px 20px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }

        #current-location-btn:hover {
            transform: translateY(-2px);
        }

        .autocomplete-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: rgba(30, 30, 50, 0.95);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-top: none;
            border-radius: 0 0 10px 10px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            backdrop-filter: blur(10px);
        }

        .autocomplete-item {
            padding: 12px 15px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: background-color 0.2s ease;
        }

        .autocomplete-item:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }

        .autocomplete-item:last-child {
            border-bottom: none;
        }

        .location-name {
            font-weight: 600;
            color: #e8e8e8;
        }

        .location-details {
            font-size: 14px;
            color: #b8b8b8;
            margin-top: 2px;
        }

        .forecast-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .forecast-header {
            text-align: center;
            margin-bottom: 25px;
        }

        .forecast-header h3 {
            font-size: 1.5rem;
            color: #e8e8e8;
            margin-bottom: 5px;
        }

        #location-display {
            font-size: 1.1rem;
            color: #b8b8b8;
        }

        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            max-width: 100%;
        }

        @media (min-width: 900px) {
            .forecast-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        .forecast-day {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .forecast-day:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.08);
        }

        .day-name {
            font-weight: 600;
            color: #e8e8e8;
            margin-bottom: 10px;
        }

        .day-temp {
            font-size: 1.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }

        .day-description {
            font-size: 0.9rem;
            color: #b8b8b8;
            text-transform: capitalize;
        }

        .weather-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .weather-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .weather-card:hover {
            transform: translateY(-5px);
        }

        .current-weather {
            text-align: center;
        }

        .temperature {
            font-size: 3rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 10px;
        }

        .weather-description {
            font-size: 1.2rem;
            color: #b8b8b8;
            margin-bottom: 20px;
            text-transform: capitalize;
        }

        .weather-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }

        .detail-item {
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .detail-label {
            font-size: 0.9rem;
            color: #b8b8b8;
            margin-bottom: 5px;
        }

        .detail-value {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e8e8e8;
        }

        .ai-insights {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin-top: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .ai-insights h3 {
            text-align: center;
            font-size: 1.5rem;
            color: #e8e8e8;
            margin-bottom: 25px;
        }

        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }

        .insight-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .insight-section h4 {
            font-size: 1.1rem;
            color: #e8e8e8;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .insight-list {
            list-style: none;
        }

        .insight-list li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            padding-left: 20px;
            color: #b8b8b8;
        }

        .insight-list li:last-child {
            border-bottom: none;
        }

        .insight-list li:before {
            content: "•";
            color: #667eea;
            font-weight: bold;
            position: absolute;
            left: 0;
        }

        .climate-comparison {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            font-size: 1.1rem;
            margin-top: 20px;
        }

        .ai-loading {
            text-align: center;
            padding: 20px;
            color: #b8b8b8;
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error-message {
            background: rgba(220, 53, 69, 0.2);
            color: #ff6b6b;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            border: 1px solid rgba(220, 53, 69, 0.3);
        }

        .hourly-forecast-header {
            text-align: center;
             margin-bottom: 15px;
             font-weight: 600;
             font-size: 1.2rem;
        }

        .hourly-scroll {
            overflow-x: auto;
            padding-bottom: 8px;
        }

        .hourly-grid {
            display: flex;
            gap: 15px;
            padding: 0 5px;
        }

        .hourly-item {
            flex: 0 0 auto;
            min-width: 110px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
            backdrop-filter: blur(6px);
            transition:
            transform 0.2s ease,
            background 0.2s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease;
        }

        .hourly-item:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.08);          
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            cursor: default; 
        }
        
        .hourly-item:focus-visible {
            outline: none;
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.10);
            border-color: rgba(102,126,234,0.6);           
            box-shadow: 0 0 0 2px rgba(102,126,234,0.25);
        }

        .hourly-item .hourly-time {
            font-size: 0.9rem;
            font-weight: 600;
            opacity: 0.95;
            margin-bottom: 4px;
        }
        
        .hourly-item .hourly-temp {
            font-size: 1.1rem;
            font-weight: 700;
            color: #667eea;                                  
            margin: 4px 0;
        }
        .hourly-item .hourly-condition {
            font-size: 0.85rem;
            color: #b8b8b8;
            text-transform: capitalize;
        }

        .hourly-item img {
            width: 40px;
            height: 40px;
            margin: 5px 0;
            opacity: 0.9;
        }

        .hourly-item .time {
            font-size: 0.9rem;
            font-weight: 500;
        }

        .hourly-item .temp {
         font-size: 1rem;
         font-weight: 600;
        }

        .hourly-scroll::-webkit-scrollbar {
            height: 8px; /* thickness of horizontal bar */
        }

        .hourly-scroll::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }

        .hourly-scroll::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            transition: background 0.2s ease;
        }

        .hourly-scroll::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.6);
        }

        .hourly-scroll {
            scrollbar-color: rgba(255, 255, 255, 0.3) rgba(255, 255, 255, 0.05);
            scrollbar-width: thin;
            overflow-y: visible;
            padding-top: 3px;
            margin-bottom: 10px;
        }
        .hourly-forecast-container{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
        }

        .chatbot-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin-top: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .chatbot-container h3 {
            text-align: center;
            font-size: 1.5rem;
            color: #e8e8e8;
            margin-bottom: 20px;
        }

        .chat-messages {
            height: 300px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background: rgba(255, 255, 255, 0.02);
        }

        .chat-message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }

        .chat-message.user {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
        }

        .message-avatar.user {
            background: #667eea;
            color: white;
        }

        .message-avatar.bot {
            background: #28a745;
            color: white;
        }

        .message-content {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            color: #e8e8e8;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .message-content.user {
            background: rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.3);
        }

        .message-content.bot {
            background: rgba(40, 167, 69, 0.2);
            border-color: rgba(40, 167, 69, 0.3);
        }

        .chat-input-container {
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            font-size: 14px;
            background: rgba(255, 255, 255, 0.05);
            color: #e8e8e8;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            outline: none;
            border-color: #667eea;
            background: rgba(255, 255, 255, 0.1);
        }

        .chat-input::placeholder {
            color: #888;
        }

        .chat-send-btn {
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }

        .chat-send-btn:hover {
            transform: translateY(-2px);
        }

        .chat-send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .chat-welcome {
            text-align: center;
            color: #b8b8b8;
            font-style: italic;
            padding: 20px;
        }

        @media (max-width: 768px) {
            .weather-grid {
                grid-template-columns: 1fr;
            }
            
            .search-form {
                flex-direction: column;
            }
            
            .forecast-grid {
                grid-template-columns: 1fr;
            }
            
            .insights-grid {
                grid-template-columns: 1fr;
            }

            .chat-messages {
                height: 250px;
            }

            .message-content {
                max-width: 90%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Stratus Weather</h1>
            <p>Your intelligent weather companion</p>
        </div>

        <div class="search-container">
            <form id="search-form" class="search-form">
                <input type="text" id="search-input" class="search-input" placeholder="Search for a location..." autocomplete="off">
                <button type="submit" class="search-button">Search</button>
                <button type="button" id="current-location-btn">📍 My Location</button>
            </form>
            <div id="autocomplete-dropdown" class="autocomplete-dropdown"></div>
        </div>

        <div class="hourly-forecast-container">
            <div class="hourly-forecast-header">
                <h3>12-Hour Forecast</h3>
            </div>
            <div id="hourly-forecast-content">
                <div class="loading-spinner"></div>
                <p>Loading hourly forecast...</p>
            </div>
        </div>

        <div class="weather-grid">
            <div class="weather-card current-weather">
                <div id="current-weather-content">
                    <div class="loading-spinner"></div>
                    <p>Loading current weather...</p>
                </div>
            </div>
            
            <div class="weather-card">
                <div id="weather-details-content">
                    <div class="loading-spinner"></div>
                    <p>Loading weather details...</p>
                </div>
            </div>
        </div>

        <div class="forecast-container">
            <div class="forecast-header">
                <h3>8-Day Forecast</h3>
                <p id="location-display">Detecting your location...</p>
            </div>
            <div id="forecast-content">
                <div class="loading-spinner"></div>
                <p>Loading forecast...</p>
            </div>
        </div>

        <div class="ai-insights">
            <h3>AI Weather Insights</h3>
            <div id="ai-content">
                <div class="ai-loading">
                    <div class="loading-spinner"></div>
                    <p>AI analysis will appear here once you select a location...</p>
                </div>
            </div>
        </div>

        <div class="chatbot-container">
            <h3>Weather Assistant</h3>
            <div id="chat-messages" class="chat-messages">
                <div class="chat-welcome">
                    Hi! I'm your weather assistant. Ask me anything about the current weather, forecast, or location! 
                    <br><br>
                    <em>Try asking: "Should I bring an umbrella today?" or "What's the weather like tomorrow?"</em>
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" id="chat-input" class="chat-input" placeholder="Ask me about the weather..." maxlength="200">
                <button id="chat-send-btn" class="chat-send-btn">Send</button>
            </div>
        </div>
    </div>

    <script>
        let userCurrentLocation = null;
        let searchTimeout = null;
        let currentAnalysisId = null;
        let currentWeatherData = null;
        let currentAIInsights = null;
        let lastViewedLocation = null;

        // DOM elements
        const searchInput = document.getElementById('search-input');
        const searchForm = document.getElementById('search-form');
        const autocompleteDropdown = document.getElementById('autocomplete-dropdown');
        const currentLocationBtn = document.getElementById('current-location-btn');
        const chatInput = document.getElementById('chat-input');
        const chatSendBtn = document.getElementById('chat-send-btn');
        const chatMessages = document.getElementById('chat-messages');

        // Event listeners
        searchInput.addEventListener('input', handleSearchInput);
        searchInput.addEventListener('focus', handleSearchInput);
        searchForm.addEventListener('submit', searchLocation);
        currentLocationBtn.addEventListener('click', loadCurrentLocation);
        chatSendBtn.addEventListener('click', sendChatMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });

        // Hide autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
                hideAutocomplete();
            }
        });

        // localStorage utility functions
        function saveLastViewedLocation(location, isCurrentLocation = false) {
            try {
                const locationData = {
                    ...location,
                    isCurrentLocation: isCurrentLocation,
                    timestamp: Date.now()
                };
                localStorage.setItem('stratus_last_location', JSON.stringify(locationData));
                lastViewedLocation = locationData;
                console.log('Saved location to localStorage:', locationData);
            } catch (error) {
                console.error('Error saving location to localStorage:', error);
            }
        }

        function getLastViewedLocation() {
            try {
                const saved = localStorage.getItem('stratus_last_location');
                if (saved) {
                    const locationData = JSON.parse(saved);
                    // Check if saved location is less than 24 hours old
                    const hoursSinceLastSave = (Date.now() - locationData.timestamp) / (1000 * 60 * 60);
                    if (hoursSinceLastSave < 24) {
                        console.log('Retrieved saved location:', locationData);
                        return locationData;
                    } else {
                        // Clear old saved location
                        localStorage.removeItem('stratus_last_location');
                        console.log('Cleared old saved location (>24 hours)');
                    }
                }
            } catch (error) {
                console.error('Error retrieving saved location:', error);
            }
            return null;
        }

        function handleSearchInput() {
            const query = searchInput.value.trim();
            
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            if (query.length < 2) {
                hideAutocomplete();
                return;
            }
            
            searchTimeout = setTimeout(() => {
                searchLocations(query);
            }, 300);
        }

        async function searchLocations(query) {
            try {
                const response = await fetch(`/api/search/locations?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    showAutocomplete(data.locations);
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        }

        function showAutocomplete(locations) {
            if (locations.length === 0) {
                hideAutocomplete();
                return;
            }
            
            autocompleteDropdown.innerHTML = locations.map(location => `
                <div class="autocomplete-item" data-lat="${location.lat}" data-lon="${location.lon}">
                    <div class="location-name">${location.name}</div>
                    <div class="location-details">${location.state ? location.state + ', ' : ''}${location.country}</div>
                </div>
            `).join('');
            
            autocompleteDropdown.style.display = 'block';
            
            // Add click listeners
            autocompleteDropdown.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('click', () => {
                    const lat = item.dataset.lat;
                    const lon = item.dataset.lon;
                    loadWeatherForLocation({ lat: parseFloat(lat), lon: parseFloat(lon) });
                    hideAutocomplete();
                    searchInput.value = '';
                });
            });
        }

        function hideAutocomplete() {
            autocompleteDropdown.style.display = 'none';
        }

        function searchLocation(event) {
            event.preventDefault();
            const query = searchInput.value.trim();
            
            if (query) {
                loadWeatherForQuery(query);
                hideAutocomplete();
            }
        }

        async function loadCurrentLocation() {
            searchInput.value = '';
            hideAutocomplete();
            
            try {
                // Show loading state
                document.getElementById('current-weather-content').innerHTML = '<div class="loading-spinner"></div><p>Detecting your location...</p>';
                document.getElementById('weather-details-content').innerHTML = '<div class="loading-spinner"></div><p>Loading weather details...</p>';
                document.getElementById('hourly-forecast-content').innerHTML = '<div class="loading-spinner"></div><p>Loading hourly forecast...</p>';
                document.getElementById('forecast-content').innerHTML = '<div class="loading-spinner"></div><p>Loading forecast...</p>';
                
                // Force get current position (ignore saved locations)
                const position = await getCurrentPosition();
                userCurrentLocation = { lat: position.coords.latitude, lon: position.coords.longitude };
                
                // Load weather for current location
                await loadWeatherForLocation(userCurrentLocation);
                
            } catch (error) {
                console.error('Error getting current location:', error);
                showError('Unable to get your current location. Please allow location access or search for a city.');
            }
        }

        async function loadWeather() {
            try {
                // Show loading state
                document.getElementById('current-weather-content').innerHTML = '<div class="loading-spinner"></div><p>Loading weather...</p>';
                document.getElementById('weather-details-content').innerHTML = '<div class="loading-spinner"></div><p>Loading weather details...</p>';
                document.getElementById('hourly-forecast-content').innerHTML = '<div class="loading-spinner"></div><p>Loading hourly forecast...</p>';
                document.getElementById('forecast-content').innerHTML = '<div class="loading-spinner"></div><p>Loading forecast...</p>';
                
                // Check for saved location first
                const savedLocation = getLastViewedLocation();
                
                if (savedLocation && !savedLocation.isCurrentLocation) {
                    // Load saved location (non-current location)
                    console.log('Loading saved location:', savedLocation.name);
                    await loadWeatherForLocation(savedLocation);
                    return;
                }
                
                // Try to get current position for user location
                try {
                    const position = await getCurrentPosition();
                    userCurrentLocation = { lat: position.coords.latitude, lon: position.coords.longitude };
                    
                    if (savedLocation && savedLocation.isCurrentLocation) {
                        // User was viewing their current location, load it again
                        console.log('Loading current location (from saved preference)');
                        await loadWeatherForLocation(userCurrentLocation);
                    } else {
                        // No saved location preference, load current location
                        console.log('Loading current location (default)');
                        await loadWeatherForLocation(userCurrentLocation);
                    }
                    
                } catch (locationError) {
                    console.error('Error getting current location:', locationError);
                    
                    if (savedLocation && !savedLocation.isCurrentLocation) {
                        // Fallback to saved location if current location fails
                        await loadWeatherForLocation(savedLocation);
                    } else {
                        // Fallback to St. Louis if everything fails
                        await loadWeatherForQuery('St. Louis, MO');
                    }
                }
                
            } catch (error) {
                console.error('Error in loadWeather:', error);
                // Final fallback to St. Louis
                await loadWeatherForQuery('St. Louis, MO');
            }
        }

        function getCurrentPosition() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation not supported'));
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    timeout: 10000,
                    enableHighAccuracy: true
                });
            });
        }

        async function loadWeatherForLocation(location) {
            try {
                const response = await fetch(`/api/weather/location?lat=${location.lat}&lon=${location.lon}`);
                const data = await response.json();
                
                if (data.success) {
                    displayWeather(data.data);
                    
                    // Save this location as the last viewed
                    const isCurrentLocation = userCurrentLocation && 
                        Math.abs(location.lat - userCurrentLocation.lat) < 0.01 && 
                        Math.abs(location.lon - userCurrentLocation.lon) < 0.01;
                    
                    saveLastViewedLocation(data.data.location, isCurrentLocation);
                    
                    // Start async AI analysis
                    await ensureUserLocationAndStartAI(data.data.location);
                }
            } catch (error) {
                console.error('Error loading weather:', error);
                showError('Failed to load weather data');
            }
        }

        async function loadWeatherForQuery(query) {
            try {
                const response = await fetch(`/api/weather/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    displayWeather(data.data);
                    
                    // Save this location as the last viewed
                    const isCurrentLocation = userCurrentLocation && 
                        Math.abs(data.data.location.lat - userCurrentLocation.lat) < 0.01 && 
                        Math.abs(data.data.location.lon - userCurrentLocation.lon) < 0.01;
                    
                    saveLastViewedLocation(data.data.location, isCurrentLocation);
                    
                    // Start async AI analysis
                    await ensureUserLocationAndStartAI(data.data.location);
                }
            } catch (error) {
                console.error('Error loading weather:', error);
                showError('Failed to load weather data');
            }
        }

        function displayWeather(data) {
            const current = data.current;
            const forecast = data.forecast;
            const location = data.location;
            
            // Store weather data for chatbot context
            currentWeatherData = data;
            
            // Update location display
            document.getElementById('location-display').textContent = 
                `${location.name}${location.state ? ', ' + location.state : ''}, ${location.country}`;
            
            // Display current weather
            const currentWeatherContent = document.getElementById('current-weather-content');
            currentWeatherContent.innerHTML = `
                <div class="temperature">${Math.round(current.main.temp)}°F</div>
                <div class="weather-description">${current.weather[0].description}</div>
                <div class="weather-details">
                    <div class="detail-item">
                        <div class="detail-label">Feels Like</div>
                        <div class="detail-value">${Math.round(current.main.feels_like)}°F</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Humidity</div>
                        <div class="detail-value">${current.main.humidity}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Wind Speed</div>
                        <div class="detail-value">${current.wind.speed} mph</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Pressure</div>
                        <div class="detail-value">${current.main.pressure} hPa</div>
                    </div>
                </div>
            `;
            
                         // Display weather details in the second card
             const weatherDetailsContent = document.getElementById('weather-details-content');
             weatherDetailsContent.innerHTML = `
                 <h3 style="text-align: center; margin-bottom: 20px; color: #e8e8e8;">Weather Details</h3>
                 <div class="weather-details">
                     <div class="detail-item">
                         <div class="detail-label">Visibility</div>
                         <div class="detail-value">${(current.visibility / 1000).toFixed(1)} km</div>
                     </div>
                     <div class="detail-item">
                         <div class="detail-label">Cloud Cover</div>
                         <div class="detail-value">${current.clouds?.all || 0}%</div>
                     </div>
                     <div class="detail-item">
                         <div class="detail-label">Chance of Rain</div>
                         <div class="detail-value">${Math.round((forecast.daily[0]?.pop || 0) * 100)}%</div>
                     </div>
                     <div class="detail-item">
                         <div class="detail-label">UV Index</div>
                         <div class="detail-value">${(forecast.daily[0]?.uvi || 0).toFixed(1)}</div>
                     </div>
                     <div class="detail-item">
                         <div class="detail-label">Sunrise</div>
                         <div class="detail-value">${new Date(current.sys.sunrise * 1000).toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}</div>
                     </div>
                     <div class="detail-item">
                         <div class="detail-label">Sunset</div>
                         <div class="detail-value">${new Date(current.sys.sunset * 1000).toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}</div>
                     </div>
                 </div>
             `;
            
            // Display hourly forecast (12 hours)
            const hourlyForecastContent = document.getElementById('hourly-forecast-content');
            if (forecast && forecast.hourly) {
                hourlyForecastContent.innerHTML = `
                    <div class="hourly-scroll">
                        <div class="hourly-grid">
                            ${forecast.hourly.map(hour => {
                                const hourDate = new Date(hour.dt * 1000);
                                const timeString = hourDate.toLocaleTimeString('en-US', { hour: 'numeric', hour12: true });
                                return `
                                    <div class="hourly-item">
                                        <div class="hourly-time">${timeString}</div>
                                        <div class="hourly-temp">${Math.round(hour.temp)}°F</div>
                                        <div class="hourly-condition">${hour.weather[0].description}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            }

            // Display forecast (8 days)
            const forecastContent = document.getElementById('forecast-content');
            if (forecast && forecast.daily) {
                forecastContent.innerHTML = `
                    <div class="forecast-grid">
                        ${forecast.daily.map((day, index) => {
                            // Get the day name based on the actual date
                            const today = new Date();
                            const forecastDate = new Date(today);
                            forecastDate.setDate(today.getDate() + index);
                            const dayName = forecastDate.toLocaleDateString('en-US', { weekday: 'short' });
                            return `
                                <div class="forecast-day">
                                    <div class="day-name">${dayName}</div>
                                    <div class="day-temp">${Math.round(day.temp.day)}°F</div>
                                    <div class="day-description">${day.weather[0].description}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
        }

        async function ensureUserLocationAndStartAI(targetLocation) {
            try {
                // If userCurrentLocation is not set, try to get it
                if (!userCurrentLocation) {
                    try {
                        const position = await getCurrentPosition();
                        userCurrentLocation = { lat: position.coords.latitude, lon: position.coords.longitude };
                        console.log('Got user location for AI analysis:', userCurrentLocation);
                    } catch (error) {
                        console.log('Could not get user location for AI analysis, using target location as user location');
                        // If we can't get user location, use the target location as both (for local insights)
                        userCurrentLocation = targetLocation;
                    }
                }
                
                // Now start AI analysis
                await startAIAnalysis(userCurrentLocation, targetLocation);
                
            } catch (error) {
                console.error('Error in ensureUserLocationAndStartAI:', error);
                document.getElementById('ai-content').innerHTML = `
                    <div class="error-message">
                        AI analysis temporarily unavailable
                    </div>
                `;
            }
        }

        async function startAIAnalysis(userLocation, targetLocation) {
            try {
                // Show loading state for AI
                document.getElementById('ai-content').innerHTML = `
                    <div class="ai-loading">
                        <div class="loading-spinner"></div>
                        <p>🤖 AI is analyzing weather patterns and climate differences...</p>
                    </div>
                `;
                
                console.log('Starting AI analysis with user:', userLocation, 'target:', targetLocation);
                
                // Start async AI analysis
                const response = await fetch(`/api/ai/analyze?user_lat=${userLocation.lat}&user_lon=${userLocation.lon}&target_lat=${targetLocation.lat}&target_lon=${targetLocation.lon}`);
                const data = await response.json();
                
                console.log('AI analysis response:', data);
                
                if (data.success) {
                    currentAnalysisId = data.analysis_id;
                    // Poll for results
                    pollAIResults();
                } else {
                    throw new Error(data.error || 'AI analysis failed');
                }
            } catch (error) {
                console.error('Error starting AI analysis:', error);
                document.getElementById('ai-content').innerHTML = `
                    <div class="error-message">
                        AI analysis temporarily unavailable: ${error.message}
                    </div>
                `;
            }
        }

        async function pollAIResults() {
            if (!currentAnalysisId) return;
            
            try {
                const response = await fetch(`/api/ai/result/${currentAnalysisId}`);
                const data = await response.json();
                
                if (data.success && data.completed) {
                    displayAIInsights(data.result);
                    currentAnalysisId = null;
                } else {
                    // Poll again in 2 seconds
                    setTimeout(pollAIResults, 2000);
                }
            } catch (error) {
                console.error('Error polling AI results:', error);
                document.getElementById('ai-content').innerHTML = `
                    <div class="error-message">
                        AI analysis failed to complete
                    </div>
                `;
            }
        }

        function displayAIInsights(aiAnalysis) {
            const aiContent = document.getElementById('ai-content');
            
            // Store AI insights for chatbot context
            currentAIInsights = aiAnalysis;
            
            aiContent.innerHTML = `
                <div class="insights-grid">
                    <div class="insight-section">
                        <h4>Location Context</h4>
                        <ul class="insight-list">
                            ${aiAnalysis.context_warnings && aiAnalysis.context_warnings.length > 0 
                                ? aiAnalysis.context_warnings.map(warning => `<li>${warning}</li>`).join('')
                                : '<li>No specific warnings for this location</li>'
                            }
                        </ul>
                    </div>
                    
                    <div class="insight-section">
                        <h4>Smart Suggestions</h4>
                        <ul class="insight-list">
                            ${Array.isArray(aiAnalysis.suggestions) && aiAnalysis.suggestions.length > 0
                                ? aiAnalysis.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')
                                : '<li>Stay updated with local weather conditions</li>'
                            }
                        </ul>
                    </div>
                    
                    <div class="insight-section">
                        <h4>Fun Facts</h4>
                        <ul class="insight-list">
                            ${Array.isArray(aiAnalysis.fun_facts) && aiAnalysis.fun_facts.length > 0
                                ? aiAnalysis.fun_facts.map(fact => `<li>${fact}</li>`).join('')
                                : '<li>Weather conditions change throughout the day</li>'
                            }
                        </ul>
                    </div>
                </div>
                
                <div class="climate-comparison">
                    ${aiAnalysis.climate_comparison || 'Unable to analyze climate differences'}
                </div>
            `;
        }

        function showError(message) {
            document.getElementById('current-weather-content').innerHTML = `
                <div class="error-message">${message}</div>
            `;
        }

        // Chatbot functions
        async function sendChatMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Disable input while sending
            chatInput.disabled = true;
            chatSendBtn.disabled = true;
            
            // Add user message to chat
            addChatMessage(message, 'user');
            chatInput.value = '';
            
            try {
                // Send message to chatbot API with context
                const response = await fetch('/api/chatbot', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        weather_context: currentWeatherData || {},
                        ai_insights: currentAIInsights || {}
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addChatMessage(data.response, 'bot');
                } else {
                    addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                addChatMessage('Sorry, I am having trouble connecting. Please try again.', 'bot');
            } finally {
                // Re-enable input
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                chatInput.focus();
            }
        }
        
        function addChatMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = `message-avatar ${sender}`;
            avatar.textContent = sender === 'user' ? '👤' : '🤖';
            
            const content = document.createElement('div');
            content.className = `message-content ${sender}`;
            content.textContent = message;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
            
            // Remove welcome message if it exists
            const welcomeMsg = chatMessages.querySelector('.chat-welcome');
            if (welcomeMsg && sender === 'user') {
                welcomeMsg.remove();
            }
            
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Load weather on page load
        loadWeather();
    </script>
</body>
</html>
    ''') 
