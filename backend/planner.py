import os
import requests
import re
import json
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta
import google.generativeai as genai

load_dotenv()

planner_bp = Blueprint("planner", __name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")  # Or pro

@planner_bp.route('/generate-itinerary', methods=['POST'])
def generate_itinerary():
    try:
        # Step 0: Parse request
        data = request.get_json()
        source = data['source']
        destination = data['destination']
        start_date_str = data['date']
        num_days = int(data.get('days', 1))
        interests = data['interests']
        budget = data['budget']
        people = int(data.get('people', 1))
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        weather_api = os.getenv("WEATHER_API_KEY")
        ors_api = os.getenv("ORS_API_KEY")

        # Step 1: Weather (up to 10 days)
        weather_days = min(num_days, 10)
        weather_url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api}&q={destination}&days={weather_days}&aqi=no&alerts=no"
        weather_response = requests.get(weather_url).json()

        if "forecast" not in weather_response:
            return jsonify({"error": "Weather data not found"}), 400

        weather_data = {}
        for day in weather_response["forecast"]["forecastday"]:
            date_key = day["date"]
            weather_data[date_key] = {
                "description": day["day"]["condition"]["text"],
                "temperature": day["day"]["avgtemp_c"]
            }

        # Fill in all required dates
        all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)]
        weather_output = {}
        for date in all_dates:
            if date in weather_data:
                weather_output[date] = weather_data[date]
            else:
                weather_output[date] = {"note": "Weather data not available for this date"}

        # Step 2: Coordinates
        def get_coordinates(location):
            geo_url = f"https://api.openrouteservice.org/geocode/search?api_key={ors_api}&text={location}"
            geo_data = requests.get(geo_url).json()
            return geo_data["features"][0]["geometry"]["coordinates"]

        src_coords = get_coordinates(source)
        dest_coords = get_coordinates(destination)

        # Step 3: Distance and duration
        route_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": ors_api,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [src_coords, dest_coords]
        }

        route_data = requests.post(route_url, headers=headers, json=body).json()
        route_summary = route_data["routes"][0]["summary"]

        travel = {
            "distance_km": round(route_summary["distance"] / 1000, 2),
            "duration_min": round(route_summary["duration"] / 60)
        }

        # Step 4: Gemini Prompt
        interests_str = ", ".join(interests)
        prompt = (
            f"Create a detailed {num_days}-day travel itinerary for a group of {people} people visiting {destination} from {source}. "
            f"The trip starts on {start_date.strftime('%B %d, %Y')} and the budget is {budget}. "
            f"Their interests include: {interests_str}.\n\n"
            f"Each day should contain 4-6 time slots with realistic, location-specific activities. "
            f"Respond strictly in JSON format ONLY. Return an array where each element has:\n"
            f"- 'date' (YYYY-MM-DD)\n"
            f"- 'plan': list of objects with 'time' and 'activity'\n"
            f"Do NOT add any explanations, comments, or text outside the JSON."
        )

        gemini_response = model.generate_content(prompt)
        raw_response = gemini_response.text.strip()

        # Step 4.5: Clean wrapped JSON
        match = re.search(r'```(?:json)?\s*(.*?)```', raw_response, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = raw_response

        try:
            itinerary_data = json.loads(cleaned)
        except json.JSONDecodeError:
            print("Gemini raw response:\n", raw_response)
            return jsonify({"error": "Gemini response was not valid JSON"}), 500

        # Step 5: Return Output
        output = {
            "weather": weather_output,
            "travel": travel,
            "days": num_days,
            "itinerary": itinerary_data
        }

        return jsonify(output)

    except Exception as e:
        print("Planner error:", e)
        return jsonify({"error": str(e)}), 500
