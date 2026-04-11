import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from gtts import gTTS
import os
import logging
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile
import wave
import io



def create_pdf(report_text):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    for line in report_text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))

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

# ---------------- ZONE FUNCTION ----------------
def get_india_climatic_zone(lat, lon):

    # 🏔️ Himalayan Region
    if lat >= 28:
        return "Himalayan Region", ["Landslide", "Flash Flood", "Avalanche"]

    # 🌊 West Coastal (Arabian Sea side)
    elif lat < 20 and 68 <= lon <= 76:
        return "West Coastal Region", ["Flood", "Cyclone", "Heavy Rainfall"]

    # 🌊 East Coastal (Bay of Bengal side)
    elif lat < 22 and 80 <= lon <= 92:
        return "East Coastal Region", ["Cyclone", "Storm Surge", "Flood"]

    # 🌵 Central / Interior India
    elif 20 <= lat <= 28:
        return "Central Interior Region", ["Heatwave", "Drought"]

    # 🌴 Southern Peninsula
    else:
        return "Southern Peninsula", ["Heatwave", "Moderate Rainfall"]

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
# place = st.text_input("Enter Place Name", place if 'place' in locals() else " ")

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

        zone, disasters = get_india_climatic_zone(lat, lon)

        # Weather API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation,temperature_2m"
        data = requests.get(url).json()

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
        is_raining = any(r > 0.5 for r in rain_data)

        # 🌊 Flood Risk Logic
        if rainfall > 10 or is_raining:
            flood_risk = "HIGH"
        elif rainfall > 5:
            flood_risk = "MEDIUM"
        elif rainfall > 1:
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


        # ---------------- MAS ACTIVATION ----------------
        if (flood_risk in ["HIGH","MEDIUM"] 
        or earthquake_risk in ["HIGH","MEDIUM"] ):

            st.subheader("🤖 Emergency Response System Activated")

            # 🏥 Hospitals
            hospitals = get_nearby_hospitals(lat, lon)
            st.subheader("🏥 Nearby Hospitals")

            if hospitals:
                for h in hospitals[:5]:
                    st.write(f"📍 Lat: {h['lat']}, Lon: {h['lon']}")
                    name = h.get("tags", {}).get("name", "Unnamed Hospital")
                    st.write(f"🏥 {name}")
            else:
                st.write("No hospitals found nearby")

            # 🚗 Route
            st.subheader("🚗 Safe Route")
            safe_lat = lat + 0.05
            safe_lon = lon + 0.05

            maps_url = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={safe_lat},{safe_lon}"

            st.subheader("🚗 Safe Evacuation Route")
            st.markdown(f"[🗺️ Open Route in Google Maps]({maps_url})")
            st.markdown(f"[Open Route in Google Maps]({maps_url})")

            # 🍞 Food
            food_places = get_food_places(lat, lon)
            st.subheader("🍞 Food Resources")

            if food_places:
                for f in food_places[:5]:
                    name = f.get("tags", {}).get("name", "Unnamed Place")
                    
                    lat_val = f.get("lat") or f.get("center", {}).get("lat")
                    lon_val = f.get("lon") or f.get("center", {}).get("lon")

                    st.write(f"📍 {lat_val}, {lon_val}")
                    st.write(f"🍽️ {name}")
            else:
                st.warning("⚠️ No food places found (try another location)")
        # ---------------- MAP ----------------
        st.subheader("🗺️ Location Map")
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.map(df)

        st.subheader("📄 Disaster Analysis Report")

        # STEP 1: Create base report
        report = f"""
        📍 Location: {district}, {state}, {country}
        📅 Date: {current_date} | ⏰ Time: {current_time}

        🌧️ Rainfall (6hr): {round(rainfall,2)} mm
        🌡️ Temperature: {temperature} °C
        💨 Wind Speed: {windspeed} km/h

        🌊 Flood Risk Status: {flood_risk}
        🌍 Earthquake Risk Status: {earthquake_risk}
        """

        # STEP 2: Add action text
        if flood_risk == "HIGH":
            report += "Immediate evacuation required."
        elif flood_risk == "MEDIUM":
            report += "Stay alert and monitor conditions."
        else:
            report += "No immediate risk."

        report += "\n🧠 Suggested Action:\n"

        # Priority: Earthquake > Flood
        if earthquake_risk == "HIGH":
            report += "🚨 High earthquake risk. Move to open safe areas immediately."
        elif earthquake_risk == "MEDIUM":
            report += "⚠️ Moderate earthquake activity. Stay alert and avoid unsafe structures."

        elif flood_risk == "HIGH":
            report += "🚨 High flood risk. Evacuate low-lying areas."
        elif flood_risk == "MEDIUM":
            report += "⚠️ Moderate flood risk. Stay alert."

        elif flood_risk == "LOW":
            report += "ℹ️ Low flood risk. Stay cautious."

        else:
            report += "✅ No immediate disaster risk. Safe conditions."

        report += f"\n\n⚠️ Trigger Source: "

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
        


        st.text_area("Report Summary", report, height=300)
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
        tts_text = re.sub(r'[^\x00-\x7F]+', '', report)  # Remove non-ASCII characters (emojis)
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