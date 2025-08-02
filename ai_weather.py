import openai
import os
from datetime import datetime, timedelta
import json
import re
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

def get_openai_client():
    """Get OpenAI client with API key from environment"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        raise ValueError("OPENAI_API_KEY environment variable not set")
    print(f"OpenAI API key found: {api_key[:10]}...")
    return openai.OpenAI(api_key=api_key)

def extract_json_from_response(content):
    """Extract JSON from AI response, handling various formats"""
    try:
        # First try direct JSON parsing
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from code blocks without language specifier
        json_match = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None

def analyze_weather_context(user_location, target_location, weather_data):
    """
    Analyze weather context comparing user's location with target location
    Returns AI-generated insights about climate differences and local context
    """
    try:
        print(f"Starting AI context analysis...")
        print(f"User location: {user_location}")
        print(f"Target location: {target_location}")
        
        client = get_openai_client()
        
        # Prepare weather data for analysis
        current = weather_data.get('current', {})
        forecast = weather_data.get('forecast', {})
        daily = forecast.get('daily', [])
        
        print(f"Weather data structure: current={bool(current)}, forecast={bool(forecast)}, daily_count={len(daily)}")
        
        # Build context prompt with explicit JSON formatting instructions
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

Please provide specific, actionable insights comparing the user's location with the target location. Consider climate differences, weather patterns, and practical advice.

IMPORTANT: Respond with ONLY a valid JSON object containing these exact keys:
- "context_warnings": [array of specific warnings about climate differences]
- "suggestions": [array of practical suggestions based on the weather]
- "fun_facts": [array of interesting weather or location facts]
- "climate_comparison": "brief comparison text"

Example response format:
{{
  "context_warnings": ["Arizona's dry heat may feel hotter than Missouri's humidity"],
  "suggestions": ["Stay hydrated in the dry climate", "Plan outdoor activities for early morning"],
  "fun_facts": ["Phoenix averages 330 sunny days per year"],
  "climate_comparison": "Arizona's desert climate differs significantly from Missouri's humid continental climate"
}}

Focus on specific, actionable insights that would help someone from the user's location understand the target location's weather.
"""
        
        print(f"Sending prompt to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful weather assistant that provides location-based weather insights and practical suggestions. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        # Parse the response
        content = response.choices[0].message.content
        print(f"OpenAI response received: {content[:200]}...")
        
        # Try to extract JSON from the response
        parsed_response = extract_json_from_response(content)
        if parsed_response:
            print(f"Successfully parsed JSON response: {parsed_response}")
            return parsed_response
        else:
            print(f"Failed to parse JSON from response: {content}")
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
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
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
        print(f"Generating weather suggestions for {user_location.get('name', 'unknown location')}")
        client = get_openai_client()
        
        daily = weather_data.get('forecast', {}).get('daily', [])
        print(f"Daily forecast count: {len(daily)}")
        
        prompt = f"""
Based on this 5-day weather forecast, provide practical suggestions for someone in {user_location.get('name', 'this location')}.

FORECAST DATA:
{json.dumps(daily, indent=2)}

Provide 3-5 specific, practical suggestions including:
- Outdoor activity recommendations
- Clothing suggestions
- Timing for outdoor tasks
- Weather-related precautions

IMPORTANT: Respond with ONLY a valid JSON array of strings.

Example response format:
["Stay hydrated in the dry climate", "Plan outdoor activities for early morning", "Bring sunscreen for UV protection"]

Focus on actionable, specific advice based on the actual weather data.
"""
        
        print(f"Sending suggestions prompt to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You provide practical weather-based suggestions. Always respond with valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.6
        )
        
        content = response.choices[0].message.content
        print(f"Suggestions response: {content[:200]}...")
        
        # Try to extract JSON array from the response
        parsed_suggestions = extract_json_from_response(content)
        if parsed_suggestions and isinstance(parsed_suggestions, list):
            print(f"Parsed suggestions: {parsed_suggestions}")
            return parsed_suggestions
        else:
            print(f"Failed to parse suggestions JSON: {content}")
            return ["Check the weather before planning outdoor activities", "Dress appropriately for the conditions"]
            
    except Exception as e:
        print(f"Suggestions generation error: {e}")
        import traceback
        traceback.print_exc()
        return ["Stay updated with local weather conditions"]

def create_weather_insights(weather_data, location_data):
    """
    Create interesting weather insights and fun facts
    """
    try:
        print(f"Creating weather insights for {location_data.get('name', 'unknown location')}")
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

IMPORTANT: Respond with ONLY a valid JSON array of strings.

Example response format:
["Phoenix averages 330 sunny days per year", "The city experiences monsoon season from July to September"]

Focus on specific, interesting facts about the location's weather patterns.
"""
        
        print(f"Sending insights prompt to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You provide interesting weather facts and insights. Always respond with valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        print(f"Insights response: {content[:200]}...")
        
        # Try to extract JSON array from the response
        parsed_insights = extract_json_from_response(content)
        if parsed_insights and isinstance(parsed_insights, list):
            print(f"Parsed insights: {parsed_insights}")
            return parsed_insights
        else:
            print(f"Failed to parse insights JSON: {content}")
            return ["Weather patterns can vary significantly throughout the day"]
            
    except Exception as e:
        print(f"Weather insights error: {e}")
        import traceback
        traceback.print_exc()
        return ["Weather conditions change throughout the day"]

def get_comprehensive_ai_analysis_async(user_location, target_location, weather_data):
    """
    Get comprehensive AI analysis asynchronously - returns immediately with loading state
    """
    def run_ai_analysis():
        """Run AI analysis in background thread"""
        try:
            print(f"Starting comprehensive AI analysis in background...")
            print(f"User location: {user_location}")
            print(f"Target location: {target_location}")
            
            # Get context analysis
            print("Getting context analysis...")
            context_analysis = analyze_weather_context(user_location, target_location, weather_data)
            
            # Get suggestions
            print("Getting weather suggestions...")
            suggestions = generate_weather_suggestions(weather_data, user_location)
            
            # Get insights
            print("Getting weather insights...")
            insights = create_weather_insights(weather_data, target_location)
            
            result = {
                "context_warnings": context_analysis.get("context_warnings", []),
                "suggestions": suggestions,
                "fun_facts": insights,
                "climate_comparison": context_analysis.get("climate_comparison", ""),
                "ai_generated": True,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Final AI analysis result: {result}")
            return result
            
        except Exception as e:
            print(f"Comprehensive AI analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "context_warnings": [],
                "suggestions": ["Check local weather updates"],
                "fun_facts": ["Weather patterns vary by location"],
                "climate_comparison": "Climate differences may affect weather perception",
                "ai_generated": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Start AI analysis in background thread
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(run_ai_analysis)
    
    # Return immediately with loading state
    return {
        "context_warnings": ["AI analysis in progress..."],
        "suggestions": ["Loading personalized suggestions..."],
        "fun_facts": ["Loading weather insights..."],
        "climate_comparison": "Analyzing climate differences...",
        "ai_generated": False,
        "loading": True,
        "future": future,
        "timestamp": datetime.now().isoformat()
    }

def get_comprehensive_ai_analysis(user_location, target_location, weather_data):
    """
    Get comprehensive AI analysis including context, suggestions, and insights
    """
    try:
        print(f"Starting comprehensive AI analysis...")
        print(f"User location: {user_location}")
        print(f"Target location: {target_location}")
        
        # Get context analysis
        print("Getting context analysis...")
        context_analysis = analyze_weather_context(user_location, target_location, weather_data)
        
        # Get suggestions
        print("Getting weather suggestions...")
        suggestions = generate_weather_suggestions(weather_data, user_location)
        
        # Get insights
        print("Getting weather insights...")
        insights = create_weather_insights(weather_data, target_location)
        
        result = {
            "context_warnings": context_analysis.get("context_warnings", []),
            "suggestions": suggestions,
            "fun_facts": insights,
            "climate_comparison": context_analysis.get("climate_comparison", ""),
            "ai_generated": True,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Final AI analysis result: {result}")
        return result
        
    except Exception as e:
        print(f"Comprehensive AI analysis error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "context_warnings": [],
            "suggestions": ["Check local weather updates"],
            "fun_facts": ["Weather patterns vary by location"],
            "climate_comparison": "Climate differences may affect weather perception",
            "ai_generated": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 