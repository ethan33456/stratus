import openai
import os
from datetime import datetime, timedelta
import json

def get_openai_client():
    """Get OpenAI client with API key from environment"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return openai.OpenAI(api_key=api_key)

def analyze_weather_context(user_location, target_location, weather_data):
    """
    Analyze weather context comparing user's location with target location
    Returns AI-generated insights about climate differences and local context
    """
    try:
        client = get_openai_client()
        
        # Prepare weather data for analysis
        current = weather_data.get('current', {})
        forecast = weather_data.get('forecast', {})
        daily = forecast.get('daily', [])
        
        # Build context prompt
        prompt = f"""
        You are a helpful weather assistant providing location-based weather insights.
        
        USER CONTEXT:
        - User's current location: {user_location.get('name', 'Unknown')}, {user_location.get('state', '')}, {user_location.get('country', '')}
        - User's coordinates: {user_location.get('lat', 'N/A')}, {user_location.get('lon', 'N/A')}
        
        TARGET LOCATION:
        - Location: {target_location.get('name', 'Unknown')}, {target_location.get('state', '')}, {target_location.get('country', '')}
        - Coordinates: {target_location.get('lat', 'N/A')}, {target_location.get('lon', 'N/A')}
        
        CURRENT WEATHER:
        - Temperature: {current.get('main', {}).get('temp', 'N/A')}°F
        - Feels like: {current.get('main', {}).get('feels_like', 'N/A')}°F
        - Humidity: {current.get('main', {}).get('humidity', 'N/A')}%
        - Wind speed: {current.get('wind', {}).get('speed', 'N/A')} mph
        - Weather description: {current.get('weather', [{}])[0].get('description', 'N/A')}
        
        5-DAY FORECAST:
        {json.dumps(daily[:3], indent=2)}
        
        Please provide:
        1. **Location Context**: How the target location's climate differs from the user's location
        2. **Weather Warnings**: Important weather considerations for someone from the user's location
        3. **Smart Suggestions**: Practical advice based on the weather forecast
        4. **Fun Facts**: Interesting weather or location facts
        
        Format your response as JSON with these keys:
        - "context_warnings": [array of warnings]
        - "suggestions": [array of suggestions]
        - "fun_facts": [array of fun facts]
        - "climate_comparison": "brief comparison text"
        
        Keep responses concise and practical. Focus on actionable insights.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful weather assistant that provides location-based weather insights and practical suggestions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        # Parse the response
        content = response.choices[0].message.content
        
        # Try to parse as JSON, fallback to structured text
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: create structured response from text
            return {
                "context_warnings": ["Weather conditions may differ from your usual climate"],
                "suggestions": ["Check local weather updates regularly"],
                "fun_facts": ["Weather patterns vary significantly by location"],
                "climate_comparison": "Climate differences may affect how weather feels",
                "raw_response": content
            }
            
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            "context_warnings": [],
            "suggestions": [],
            "fun_facts": [],
            "climate_comparison": "Unable to analyze climate differences",
            "error": str(e)
        }

def generate_weather_suggestions(weather_data, user_location):
    """
    Generate personalized weather suggestions based on forecast
    """
    try:
        client = get_openai_client()
        
        daily = weather_data.get('forecast', {}).get('daily', [])
        
        prompt = f"""
        Based on this 5-day weather forecast, provide practical suggestions for someone in {user_location.get('name', 'this location')}.
        
        FORECAST DATA:
        {json.dumps(daily, indent=2)}
        
        Provide 3-5 practical suggestions including:
        - Outdoor activity recommendations
        - Clothing suggestions
        - Timing for outdoor tasks
        - Weather-related precautions
        
        Format as JSON array of strings.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You provide practical weather-based suggestions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.6
        )
        
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return ["Check the weather before planning outdoor activities", "Dress appropriately for the conditions"]
            
    except Exception as e:
        print(f"Suggestions generation error: {e}")
        return ["Stay updated with local weather conditions"]

def create_weather_insights(weather_data, location_data):
    """
    Create interesting weather insights and fun facts
    """
    try:
        client = get_openai_client()
        
        current = weather_data.get('current', {})
        daily = weather_data.get('forecast', {}).get('daily', [])
        
        prompt = f"""
        Create 2-3 interesting weather facts or insights for {location_data.get('name', 'this location')}.
        
        WEATHER DATA:
        Current: {current.get('main', {}).get('temp', 'N/A')}°F, {current.get('main', {}).get('humidity', 'N/A')}% humidity
        Forecast: {len(daily)} days of data
        
        Focus on:
        - Interesting weather patterns
        - Local climate facts
        - Seasonal insights
        - Weather records or averages
        
        Format as JSON array of strings.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You provide interesting weather facts and insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return ["Weather patterns can vary significantly throughout the day"]
            
    except Exception as e:
        print(f"Weather insights error: {e}")
        return ["Weather conditions change throughout the day"]

def get_comprehensive_ai_analysis(user_location, target_location, weather_data):
    """
    Get comprehensive AI analysis including context, suggestions, and insights
    """
    try:
        # Get context analysis
        context_analysis = analyze_weather_context(user_location, target_location, weather_data)
        
        # Get suggestions
        suggestions = generate_weather_suggestions(weather_data, user_location)
        
        # Get insights
        insights = create_weather_insights(weather_data, target_location)
        
        return {
            "context_warnings": context_analysis.get("context_warnings", []),
            "suggestions": suggestions,
            "fun_facts": insights,
            "climate_comparison": context_analysis.get("climate_comparison", ""),
            "ai_generated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Comprehensive AI analysis error: {e}")
        return {
            "context_warnings": [],
            "suggestions": ["Check local weather updates"],
            "fun_facts": ["Weather patterns vary by location"],
            "climate_comparison": "Climate differences may affect weather perception",
            "ai_generated": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 