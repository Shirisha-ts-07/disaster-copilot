# 🌍 Disaster Copilot Dashboard

A real-time disaster management system that analyzes weather and earthquake data to predict risks and provide emergency response.

---

## 🚀 Features

- 🌧️ Rainfall and weather analysis  
- 🌊 Flood risk prediction  
- 🌍 Earthquake detection (location-based)  
- 🏥 Nearby hospitals detection  
- 🍞 Food resource availability  
- 🚗 Safe evacuation route using Google Maps  
- 📊 Data visualization (graphs)  
- 📄 PDF report generation  
- 🔊 Voice output of report  

---

## 🛠️ Technologies Used

- Python  
- Streamlit  
- Open-Meteo API (Weather)  
- USGS API (Earthquake data)  
- OpenStreetMap (Overpass API)  
- Matplotlib  

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/disaster-copilot.git
cd disaster-copilot
```

## Run

On macOS or Linux, activate the project environment, install dependencies if needed, and start the dashboard:

```bash
source dis_env/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run disaster_dashboard.py
```