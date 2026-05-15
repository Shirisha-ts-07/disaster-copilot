import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from reportlab.platypus import Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from gtts import gTTS
import os
import logging
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile
import wave
import io
import pydeck as pdk
import json
import urllib.request
from crewai import Agent, Task, Crew
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import random
import heapq

def dijkstra(graph, start, end):
    queue = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {}

    while queue:
        cost, node = heapq.heappop(queue)

        if node == end:
            break

        for neighbor, weight in graph[node]:
            new_cost = cost + weight

            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous[neighbor] = node
                heapq.heappush(queue, (new_cost, neighbor))

    # Reconstruct path
    path = []
    current = end
    while current in previous:
        path.insert(0, current)
        current = previous[current]

    path.insert(0, start)
    return path



def generate_resources(risk_level):
    if risk_level == "HIGH":
        beds = random.randint(0, 20)
        ambulances = random.randint(0, 3)
    elif risk_level == "MEDIUM":
        beds = random.randint(10, 40)
        ambulances = random.randint(2, 6)
    else:
        beds = random.randint(30, 80)
        ambulances = random.randint(5, 10)

    return beds, ambulances
def load_world_map():
    url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def generate_country_risk():
    return {
        "Indonesia": "HIGH",
        "India": "MEDIUM",
        "United States of America": "LOW"
    }


def get_color(risk):
    if risk == "HIGH":
        return [255, 0, 0, 120]
    elif risk == "MEDIUM":
        return [255, 255, 0, 120]
    else:
        return [0, 255, 0, 120]



def create_pdf(report_text, rain_data=None, temp_data=None, hospitals=None):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []

    # ---------- TITLE ----------
    content.append(Paragraph("<b>DISASTER ANALYSIS REPORT</b>", styles["Title"]))
    content.append(Spacer(1, 15))

    # ---------- REPORT TEXT ----------
    content.append(Paragraph(report_text, styles["Normal"]))
    content.append(Spacer(1, 15))

    # ---------- RAIN GRAPH ----------
    if rain_data is not None and len(rain_data) > 0:
        plt.figure()
        plt.plot(rain_data)
        plt.title("Rainfall Forecast")
        plt.xlabel("Hours")
        plt.ylabel("mm")
        plt.grid()
        plt.savefig("rain.png")
        plt.close()

        content.append(Paragraph("<b>Rainfall Analysis</b>", styles["Heading2"]))
        content.append(Spacer(1, 10))
        content.append(Image("rain.png", width=400, height=200))

    # ---------- TEMP GRAPH ----------
    if temp_data is not None and len(temp_data) > 0:
        plt.figure()
        plt.plot(temp_data)
        plt.title("Temperature Forecast")
        plt.xlabel("Hours")
        plt.ylabel("°C")
        plt.grid()
        plt.savefig("temp.png")
        plt.close()

        content.append(Spacer(1, 15))
        content.append(Paragraph("<b>Temperature Analysis</b>", styles["Heading2"]))
        content.append(Spacer(1, 10))
        content.append(Image("temp.png", width=400, height=200))

    # ---------- HOSPITAL TABLE ----------
    if hospitals:
        content.append(Spacer(1, 20))
        content.append(Paragraph("<b>Nearby Medical Resources</b>", styles["Heading2"]))
        content.append(Spacer(1, 10))

        table_data = [["Hospital", "Beds", "Ambulances"]]

        for h in hospitals[:5]:
            name = h.get("tags", {}).get("name", "Hospital")
            beds = "Varies"
            ambulances = "Available"

            table_data.append([name, beds, ambulances])

        table = Table(table_data)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        content.append(table)

    doc.build(content)

    with open("report.pdf", "rb") as f:
        return f.read()


def setup_logger():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        filename="disaster_copilot.log",
        filemode="a",
    )


def log_info(msg):
    st.write(f"ℹ️ {msg}")
    logging.info(msg)


def log_error(msg, exc=None):
    st.error(f"❌ {msg}")
    if exc:
        logging.exception(msg)
    else:
        logging.error(msg)


setup_logger()



st.set_page_config(page_title="Disaster Copilot", layout="wide")


st.title("🌍 Disaster Copilot Dashboard")
st.markdown("Real-time disaster risk analysis using weather intelligence")
now = datetime.datetime.now()

current_date = now.strftime("%d %B %Y")
current_time = now.strftime("%I:%M %p")
st.markdown(f"📅 Date: {current_date} | ⏰ Time: {current_time}")
st.subheader("🌍 Live Disaster Risk Map")

st.info("💡 View high-risk zones (red) and enter a location below to analyze")




# ---------------- MAP SECTION ----------------


# ---------------- ZONE FUNCTION ----------------
def get_global_climatic_zone(lat, lon):

    # 🌍 POLAR REGION
    if abs(lat) >= 66:
        return "Polar Region", ["Extreme Cold", "Blizzards", "Ice Storms"]

    # ❄️ TEMPERATE REGION
    elif 35 <= abs(lat) < 66:
        return "Temperate Region", ["Storms", "Floods", "Wildfires"]

    # 🌴 TROPICAL REGION
    elif 23 <= abs(lat) < 35:
        return "Subtropical Region", ["Cyclones", "Heatwaves", "Drought"]

    # 🌧️ EQUATORIAL REGION
    else:
        return "Equatorial Region", ["Heavy Rainfall", "Floods", "Landslides"]
# ---------------- GEOLOCATION ----------------
def get_coordinates(place):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={place}"
    response = requests.get(geo_url).json()

    if "results" in response:
        result = response["results"][0]

        lat = result["latitude"]
        lon = result["longitude"]

        district = result.get("name", "Unknown")
        state = result.get("admin1", "Unknown")
        country = result.get("country", "Unknown")

        return lat, lon, district, state, country

    return None, None, None, None, None




def get_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    data = requests.get(url).json()
    return data["features"]

from math import radians, cos, sin, sqrt, atan2

def is_near(lat1, lon1, lat2, lon2, threshold_km=1000):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c <= threshold_km


def get_volcano_alerts():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except:
        return []

    volcano_events = []

    for event in data.get("features", []):
        place = event["properties"].get("place", "").lower()

        if "volcano" in place or "mount" in place:
            volcano_events.append(event)

    return volcano_events
def build_live_risk_points():
    points = []

    earthquakes = get_earthquakes()

    for eq in earthquakes:
        coords = eq["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]

        mag = eq["properties"].get("mag", 0) or 0

        if mag >= 5:
            color = [255, 0, 0]      # HIGH
        elif mag >= 3:
            color = [255, 255, 0]    # MEDIUM
        else:
            color = [0, 255, 0]      # LOW

        points.append({
            "lat": lat,
            "lon": lon,
            "color": color,
            "size": 50000 + mag * 20000
        })

    return pd.DataFrame(points)

def get_country_risk_from_earthquakes():
    earthquakes = get_earthquakes()
    country_risk = {}

    for eq in earthquakes:
        place = eq["properties"]["place"]
        mag = eq["properties"].get("mag", 0) or 0

        if "," in place:
            country = place.split(",")[-1].strip()
        else:
            country = "Unknown"

        if country not in country_risk:
            country_risk[country] = 0

        country_risk[country] += mag

    # convert to color directly
    country_color = {}

    for country, score in country_risk.items():
        if score > 20:
            country_color[country] = [255, 0, 0, 150]   # RED
        elif score > 10:
            country_color[country] = [255, 255, 0, 150] # YELLOW
        else:
            country_color[country] = [0, 255, 0, 100]   # GREEN

    return country_color
world_map = load_world_map()
country_colors = get_country_risk_from_earthquakes()

# attach color to each country
for feature in world_map["features"]:
    country_name = feature["properties"]["name"]
    feature["properties"]["color"] = country_colors.get(
        country_name, [0, 255, 0, 80]
    )

geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    world_map,
    get_fill_color="properties.color",
    pickable=True,
    stroked=True,
    filled=True,
)

view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1.5,
)

st.pydeck_chart(pdk.Deck(
    layers=[geojson_layer],
    initial_view_state=view_state
))
def get_fallback_resources():
    return {
        "hospitals": [
            "Government Hospital",
            "District Health Center",
            "Primary Health Clinic"
        ],
        "food": [
            "Community Shelter Kitchen",
            "Relief Camp Food Center",
            "Local Grocery Store"
        ]
    }


       
# ---------------- MAS FUNCTIONS ----------------




def get_nearby_hospitals(lat, lon):
    query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:50000,{lat},{lon});
      node["amenity"="clinic"](around:50000,{lat},{lon});
      node["amenity"="pharmacy"](around:50000,{lat},{lon});
    );
    out;
    """
    url = "https://overpass-api.de/api/interpreter"
    response = requests.get(url, params={"data": query})
    return response.json().get("elements", []) if response.status_code == 200 else []


import random

def generate_ambulance_data(hospitals):
    ambulance_data = []

    for h in hospitals[:3]:
        name = h.get("tags", {}).get("name", "Hospital")

        ambulances = random.randint(2, 10)
        dispatched = random.randint(1, ambulances)

        ambulance_data.append({
            "name": name,
            "total": ambulances,
            "dispatched": dispatched
        })

    return ambulance_data


def get_food_places(lat, lon):
    query = f"""
    [out:json];
    (
      node["amenity"~"restaurant|cafe|fast_food"](around:30000,{lat},{lon});
      way["amenity"~"restaurant|cafe|fast_food"](around:30000,{lat},{lon});
      relation["amenity"~"restaurant|cafe|fast_food"](around:30000,{lat},{lon});
    );
    out center;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    response = requests.get(url, params={"data": query})
    
    if response.status_code == 200:
        return response.json().get("elements", [])
    return []


# ---------------- INPUT ----------------
place = st.text_input("Enter Place Name")


# ---------------- BUTTON ----------------
if st.button("Analyze Risk"):
    earthquake_risk = "NONE"

    lat, lon, district, state, country = get_coordinates(place)

    if lat is None:
        st.error("Place not found ❌")
    else:
        st.success(
    f"📍 {district}, {state}, {country} (Lat: {lat}, Lon: {lon})"
)

        zone, disasters = get_global_climatic_zone(lat, lon)

        # Weather API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation,temperature_2m"
        data = requests.get(url).json()

        # ---------------- PREDICTION LOGIC ----------------

        # 🌧️ Flood Prediction (Future Rain Safe)
        if "hourly" in data and "precipitation" in data["hourly"]:
            rain_full = data["hourly"]["precipitation"]

            if len(rain_full) >= 12:
                future_rain = sum(rain_full[:12])
            else:
                future_rain = sum(rain_full)
        else:
            future_rain = 0

        if future_rain > 30:
            flood_risk = "HIGH"
            flood_prediction = "HIGH"
        elif future_rain > 15:
            flood_risk = "MEDIUM"
            flood_prediction = "MEDIUM"
        elif future_rain > 5:
            flood_risk = "LOW"
            flood_prediction = "LOW"
        else:
            flood_risk = "NO FLOOD RISK"
            flood_prediction = "NO RISK"
        weather = data["current_weather"]

        temperature = weather["temperature"]
        windspeed = weather["windspeed"]
        rain_data = data["hourly"]["precipitation"][:6]
        rain_data = data["hourly"]["precipitation"][:6]

        # Better detection
        rainfall = max(rain_data)

        # fallback if all zeros
        if rainfall == 0:
            rainfall = sum(rain_data)

        # EXTRA: detect rain using probability pattern
        is_raining = any(r > 0.5 for r in rain_data)   # take highest rainfall instead of sum

        

        # ---------------- LOCATION + WEATHER ----------------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📍 Location Info")
            st.write("Zone:", zone)
            st.write("Disasters:", disasters)

        with col2:
            st.subheader("🌤️ Weather Info")
            st.write("Temperature:", temperature, "°C")
            st.write("Wind Speed:", windspeed, "km/h")

        # ---------------- GRAPHS ----------------
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("📈 Rainfall Trend")
            st.subheader("📈 Rainfall Trend (Next 24 Hours)")

            rain_data = data["hourly"]["precipitation"][:24]

            plt.figure()
            plt.plot(rain_data)
            plt.xlabel("Time (Hours)")
            plt.ylabel("Rainfall (mm)")
            plt.title("Rainfall Forecast")
            plt.grid()
            st.pyplot(plt)

        with col4:
            st.subheader("🌡️ Temperature Trend")
            st.subheader("🌡️ Temperature Trend (Next 24 Hours)")

            temp_data = data["hourly"]["temperature_2m"][:24]

            plt.figure()
            plt.plot(temp_data)
            plt.xlabel("Time (Hours)")
            plt.ylabel("Temperature (°C)")
            plt.title("Temperature Forecast")
            plt.grid()
            st.pyplot(plt)


        # ---------------- DASHBOARD ----------------
        st.subheader("🌍 Weather Dashboard")

        col5, col6, col7 = st.columns(3)

        col5.metric("🌧️ Rainfall (6hr)", f"{round(rainfall,2)} mm")
        col6.metric("🌡️ Temperature", f"{temperature} °C")
        col7.metric("💨 Wind Speed", f"{windspeed} km/h")
        st.subheader("🌧️ Rain Status")

        if is_raining:
            st.success("🌧️ Rain detected in forecast")
        else:
            st.info("☁️ No rain detected")

        # ---------------- FLOOD RISK ----------------
        risk_score = (rainfall * 0.7) + (windspeed * 0.3)

                # 🌧️ Improved Rain Detection
        rain_data = data["hourly"]["precipitation"][:6]

        rainfall = max(rain_data)

        if rainfall == 0:
            rainfall = sum(rain_data)

        # detect rain presence
        # 🌊 Improved Flood Risk Logic

        if rainfall > 20:
            flood_risk = "HIGH"
        elif rainfall > 10:
            flood_risk = "MEDIUM"
        elif rainfall > 2:
            flood_risk = "LOW"
        else:
            flood_risk = "NO FLOOD RISK"

        
        st.subheader("🌊 Flood Risk Status")
        st.write("Risk Score:", round(risk_score, 2))

        if flood_risk == "HIGH":
            st.error("🚨 HIGH FLOOD RISK")
        elif flood_risk == "MEDIUM":
            st.warning("⚠️ MEDIUM FLOOD RISK")
        elif flood_risk == "LOW":
            st.warning("✅ LOW FLOOD RISK")
        else:
            st.success("✅ NO FLOOD RISK")

        st.subheader("🌍 Earthquake Alerts")

        # st.subheader("🌧️ Rain Status")

        # if is_raining:
            # st.success("🌧️ Rain detected in forecast")
        # else:
            # st.info("☁️ No rain detected")

        earthquakes = get_earthquakes()

        earthquake_risk = "NONE"   # ✅ default
        best_eq = None
        max_magnitude = 0

        for eq in earthquakes:
            coords = eq["geometry"]["coordinates"]
            eq_lon, eq_lat = coords[0], coords[1]

            magnitude = eq["properties"]["mag"]
            place_name = eq["properties"]["place"]

            # ✅ Filter by distance
            if is_near(lat, lon, eq_lat, eq_lon):

                # ✅ Pick strongest earthquake only
                if magnitude > max_magnitude:
                    max_magnitude = magnitude
                    best_eq = (place_name, magnitude)

        # ✅ SHOW ONLY ONE RESULT
        if best_eq:
            place_name, magnitude = best_eq
        # 🌍 Earthquake Prediction (FIXED)

            if best_eq:
                if magnitude >= 6:
                    earthquake_prediction = "HIGH"
                elif magnitude >= 4:
                    earthquake_prediction = "MEDIUM"
                else:
                    earthquake_prediction = "LOW"
            else:
                earthquake_prediction = "LOW"

            st.write(f"📍 Location: {place_name}")
            st.write(f"📊 Magnitude: {magnitude}")

            if magnitude >= 6:
                earthquake_risk = "HIGH"
                st.error("🚨 HIGH EARTHQUAKE RISK")

            elif magnitude >= 4:
                earthquake_risk = "MEDIUM"
                st.warning("⚠️ MODERATE EARTHQUAKE")

            else:
                earthquake_risk = "LOW"
                st.success("🟢 LOW IMPACT EARTHQUAKE")

        else:
            earthquake_risk = "NONE"
            st.success("✅ No recent earthquakes nearby")

        # 🌍 Earthquake Prediction
        nearby_quakes = [
        eq for eq in earthquakes
            if is_near(lat, lon,
                    eq["geometry"]["coordinates"][1],
                    eq["geometry"]["coordinates"][0])
            and eq["properties"]["mag"] >= 4
        ]

        if len(nearby_quakes) > 3:
            earthquake_prediction = "HIGH"
        elif len(nearby_quakes) > 1:
            earthquake_prediction = "MEDIUM"
        else:
            earthquake_prediction = "LOW"

        # ---------------- VOLCANO ALERT ----------------

        st.subheader("🌋 Volcano Alerts")

        volcanoes = get_volcano_alerts()
        nearby_volcanoes = []

        # check nearby volcanoes (within 500 km)
        for v in volcanoes:
            coords = v["geometry"]["coordinates"]
            v_lon, v_lat = coords[0], coords[1]

            if is_near(lat, lon, v_lat, v_lon, threshold_km=500):
                nearby_volcanoes.append(v)

        volcano_risk = "NONE"

        # show result
        if nearby_volcanoes:
            for v in nearby_volcanoes[:3]:
                place_name = v["properties"]["place"]
                mag = v["properties"]["mag"]

                st.write(f"🌋 {place_name}")
                st.write(f"Activity Level: {mag}")

            volcano_risk = "HIGH"
            st.error("🚨 VOLCANIC ACTIVITY DETECTED")

        else:
            st.success("✅ No volcanic activity detected nearby")
        # 🌋 Volcano Prediction
        # 🌋 Volcano Prediction (FIXED)

        if len(nearby_volcanoes) > 2:
            volcano_prediction = "HIGH"
        elif len(nearby_volcanoes) > 0:
            volcano_prediction = "MEDIUM"
        else:
            volcano_prediction = "LOW"

        if any("marapi" in v["properties"]["place"].lower() for v in volcanoes):
            volcano_risk = "HIGH"

        st.subheader("🔮 Disaster Prediction")

        st.write("🌊 Flood Prediction:", flood_prediction)
        st.write("🌍 Earthquake Prediction:", earthquake_prediction)
        st.write("🌋 Volcano Prediction:", volcano_prediction)


        if earthquake_risk == "HIGH" or volcano_risk == "HIGH":
            overall_risk = "HIGH"
        elif flood_risk == "MEDIUM":
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"


        # ---------------- MAS ACTIVATION ----------------
        if (flood_risk in ["HIGH","MEDIUM"] 
            or earthquake_risk in ["HIGH","MEDIUM"]
            or volcano_risk == "HIGH"):

                st.subheader("🤖 Emergency Response System Activated")

                # 🏥 Hospitals
                hospitals = get_nearby_hospitals(lat, lon)
                st.subheader("🏥 Nearby Hospitals")

                fallback = get_fallback_resources()
                for h in hospitals[:5]:
                    name = h.get("tags", {}).get("name", "Unnamed Hospital")

                    beds, ambulances = generate_resources(flood_risk)

                    st.write(f"🏥 {name}")
                    st.write(f"🛏️ Beds Available: {beds}")
                    import random

                    dispatched = random.randint(1, ambulances)

                    st.write(f"🚑 Available: {ambulances}")
                    st.write(f"🚨 Dispatched: {dispatched}")
                    st.write("📍 Route: Hospital → Disaster Location")
                    st.write("---")

                else:
                    st.warning(" Hospitals found → showing emergency options")

                    for h in fallback["hospitals"]:
                        beds, ambulances = generate_resources(overall_risk)

                        st.write(f"🏥 {h}")
                        st.write(f"🛏️ Beds Available: {beds}")
                        st.write(f"🚑 Ambulances Available: {ambulances}")
                        st.write("---")

                st.subheader("🚑 Ambulance Dispatch System")

                ambulance_info = generate_ambulance_data(hospitals)

                for a in ambulance_info:
                    st.write(f"🏥 {a['name']}")
                    st.write(f"🚑 Total Ambulances: {a['total']}")
                    st.write(f"🚨 Dispatched: {a['dispatched']}")

               # 🚗 Route
                #st.subheader("🚗 Safe Evacuation Route")
                safe_lat = lat + 0.05
                safe_lon = lon + 0.05

                for h in hospitals[:3]:
                    lat_h = h.get("lat")
                    lon_h = h.get("lon")

                    if lat_h and lon_h:
                        maps_url = f"https://www.google.com/maps/dir/{lat_h},{lon_h}/{lat},{lon}"

                        st.markdown(f"[🚑 View Ambulance Route from {h.get('tags', {}).get('name','Hospital')}]({maps_url})")

                # --------- SAFE ROUTE GRAPH --------

                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={safe_lat},{safe_lon}"

                # st.subheader("🚗 Safe Evacuation Route")
                #st.markdown(f"[🗺️ Open Route in Google Maps]({maps_url})")
                # st.markdown(f"[Open Route in Google Maps]({maps_url})")





                safe_lat = lat + 0.05
                safe_lon = lon + 0.05

                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={safe_lat},{safe_lon}"

                st.subheader("🚗 Safe Evacuation Route (Google Maps)")
                st.markdown(f"[🗺️ Open Route in Google Maps]({maps_url})")


                # ---------------- DIJKSTRA ROUTE ----------------
                st.subheader("🧠 Smart Safe Route")

                # Risk-based weight
                if flood_risk == "HIGH":
                    danger_weight = 100
                else:
                    danger_weight = 20

                # Graph (simple model)
                graph = {
                    "Start": [("SafeZone1", 5), ("DangerZone", danger_weight)],
                    "SafeZone1": [("SafeZone2", 5)],
                    "DangerZone": [("SafeZone2", danger_weight)],
                    "SafeZone2": []
                }

                # Run algorithm
                safe_path = dijkstra(graph, "Start", "SafeZone2")

                # Show result
                st.success(" → ".join(safe_path))
            

                # 🍞 Food
                food_places = get_food_places(lat, lon)
                st.subheader("🍞 Food Resources")

                if food_places:
                    for f in food_places[:5]:
                        name = f.get("tags", {}).get("name", "Unnamed Place")
                        st.write(f"🍽️ {name}")
                else:
                    st.warning(" Food data → showing emergency food sources")

                    for f in fallback["food"]:
                        st.write(f"🍞 {f}")
        # ---------------- MAP ----------------
        st.subheader("🗺️ Location Map")
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.map(df)

        st.subheader("📄 Disaster Analysis Report")

        # STEP 1: Create base report
        report = f"""
        <b>DISASTER ANALYSIS REPORT</b><br/><br/>

        <b>1. Location Details</b><br/>
        Location: {district}, {state}, {country}<br/>
        Date: {current_date}<br/>
        Time: {current_time}<br/><br/>

        <b>2. Weather Information</b><br/>
        Rainfall (6hr): {round(rainfall,2)} mm<br/>
        Temperature: {temperature} °C<br/>
        Wind Speed: {windspeed} km/h<br/><br/>

        <b>3. Risk Assessment</b><br/>
        Flood Risk: {flood_risk}<br/>
        Earthquake Risk: {earthquake_risk}<br/>
        Volcano Risk: {volcano_risk}<br/><br/>

        <b>4. Predictions</b><br/>
        Flood Prediction: {flood_prediction}<br/>
        Earthquake Prediction: {earthquake_prediction}<br/>
        Volcano Prediction: {volcano_prediction}<br/><br/>
        """
       

        # STEP 2: Add action text
        if flood_risk == "HIGH":
            report += "Immediate evacuation required."
        elif flood_risk == "MEDIUM":
            report += "Stay alert and monitor conditions."
        else:
            report += "No immediate risk.<br/>"

        report += "<b>5. Suggested Action</b><br/>"

        # Priority: Earthquake > Flood
        if earthquake_risk == "HIGH":
            report += " High earthquake risk. Move to open safe areas immediately.<br/>"
        elif earthquake_risk == "MEDIUM":
            report += "Moderate earthquake activity. Stay alert and avoid unsafe structures.<br/>"

        elif flood_risk == "HIGH":
            report += " High flood risk. Evacuate low-lying areas.<br/>"
        elif flood_risk == "MEDIUM":
            report += " Moderate flood risk. Stay alert.<br/>"

        elif flood_risk == "LOW":
            report += "ℹ Low flood risk. Stay cautious.<br/>"

        else:
            report += "No immediate disaster risk. Safe conditions.<br/>"

        report += "<br/><b>6. Trigger Source</b><br/>"

        if earthquake_risk in ["HIGH", "MEDIUM"]:
            report += "Earthquake Activity"
        elif flood_risk == "HIGH":
            report += "Flood Risk"
        else:
            report += "No Threat"

        # STEP 3: Add hospitals safely
        

        if 'hospitals' in locals() and hospitals:
            report += "\n\n🏥 Nearby Hospitals:\n"
            for h in hospitals[:3]:
                name = h.get("tags", {}).get("name:en") or h.get("tags", {}).get("name", "Unnamed")
                report += f"- {name}\n"
            else:
                report += "No data available\n"
        # STEP 4: Display report
        


        # st.text_area("Report Summary", report, height=300)

        # SAFETY: make sure variables exist
        try:
            pdf = create_pdf(report, rain_data, temp_data, hospitals)
        except:
            pdf = create_pdf(report)

        st.download_button(
            label="📄 Download PDF Report",
            data=pdf,
            file_name="disaster_report.pdf",
            mime="application/pdf"
        )


        from io import BytesIO
        import re

        # Create a text-only version for TTS (remove emojis)
        # Remove non-ASCII characters (emojis)
        import re

        # Remove HTML tags
        clean_text = re.sub(r'<.*?>', '', report)

        # Remove emojis / special chars
        clean_text = re.sub(r'[^\x00-\x7F]+', '', clean_text)

        tts_text = clean_text.strip()
        tts_text = tts_text.strip()

        try:
            tts = gTTS(tts_text)
            mp3_buf = BytesIO()
            tts.write_to_fp(mp3_buf)
            mp3_buf.seek(0)
            audio_data = mp3_buf.read()
            # Check if it starts with MP3 header
            if audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3') or audio_data.startswith(b'\xff\xf2'):
                log_info("Audio data appears to be valid MP3")
            else:
                log_info("Audio data may not be valid MP3")
            
            # Save to file for debugging
            with open("debug_audio.mp3", "wb") as f:
                f.write(audio_data)
            # log_info("Audio saved to debug_audio.mp3")
            
            # Play audio with correct MIME type
            st.audio(audio_data, format="audio/mpeg")
            
            # log_info("Audio played successfully")
            
            # Also provide download button
            st.download_button(
                label="🎵 Download Audio Report",
                data=audio_data,
                file_name="disaster_audio_report.mp3",
                mime="audio/mpeg"
            )
        except Exception as e:
            log_error(f"Error generating or playing audio: {str(e)}", exc=e)
