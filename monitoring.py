import requests
import time
import streamlit as st
import folium
from streamlit.components.v1 import html
import pandas as pd
from datetime import datetime
import pyrebase

# Konfigurasi Firebase
config = {
    "apiKey": "AIzaSyCNYVKpsjyT5uUZuOZOGGwJe4eUOZOGGwJe4RcwwnVfFY",
    "authDomain": "mavis-da4e1.firebaseapp.com",
    "databaseURL": "https://mavis-da4e1-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "mavis-da4e1",
    "storageBucket": "mavis-da4e1.appspot.com",
    "messagingSenderId": "807554041548",
    "appId": "1:807554041548:web:ba403db2af0b3a935f6469",
    "measurementId": "G-FC8G3C7SLJ",
    "serviceAccount": "serviceAccount.json"
}

# Inisialisasi Firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage()

# Inisialisasi daftar untuk tabel
id, Latitude, Longitude, timestamp, cog, sog = ([] for _ in range(6))
gps_points = []

# Fungsi untuk list file di storage dan download file terbaru berdasarkan kata kunci
def list_files():
    all_files = []
    try:
        files = storage.child("images").list_files()  # List files in 'images' folder
        for file in files:
            all_files.append(file.name)
    except Exception as e:
        print("Error while listing files:", e)
    return all_files

def download_latest_file(keyword):
    files = list_files()
    if files:
        filtered_files = [file for file in files if keyword in file]
        if filtered_files:
            latest_file = filtered_files[-1]
            local_file_name = latest_file.split('/')[-1]
            storage.child(latest_file).download(local_file_name, local_file_name)
            return local_file_name
        else:
            print(f"No files found for keyword: {keyword}")
            return None
    else:
        print("No files available in storage.")
        return None

# Fungsi untuk membuat peta
def create_map(points):
    if len(points) > 0:
        center_lat = points[-1]["latitude"]
        center_lon = points[-1]["longitude"]
        zoom_level = 21
        
        gps_map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, max_zoom=25)
        
        coordinates = []
        for point in points:
            popup_content = f"Latitude: {point['latitude']}<br>Longitude: {point['longitude']}"
            folium.Marker(location=[point["latitude"], point["longitude"]], popup=popup_content).add_to(gps_map)
            coordinates.append((point["latitude"], point["longitude"]))
        
        if len(coordinates) > 1:
            folium.PolyLine(locations=coordinates, color="blue", weight=2.5, opacity=1).add_to(gps_map)
        
        display_map(gps_map)
    else:
        st.write("Tidak ada poin GPS untuk dipetakan.")

def display_map(folium_map):
    map_html = folium_map._repr_html_()
    html(map_html, height=680, width=680)

# Fungsi untuk fetch data dari Firebase
def fetch_data():
    try:
        data = db.child("maps").get()
        if data.each():
            items = [item.val() for item in data.each() if item.val() is not None]
            if items:
                latest_item = items[-1]
                gps_raw_int = latest_item.get("GPS_RAW_INT", {}).get("msg", {})
                
                gps_lat = float(gps_raw_int.get('lat', 0)) / 10e6
                gps_lon = float(gps_raw_int.get('lon', 0)) / 10e6
                gps_cog = float(gps_raw_int.get('cog', 0)) * 100
                gps_sog = float(gps_raw_int.get('vel', 0)) / 0.036
                
                if gps_lat is not None and gps_lon is not None:
                    gps_points.append({"latitude": gps_lat, "longitude": gps_lon})
                    new_data = [len(id) + 1, gps_lat, gps_lon, datetime.now().isoformat(), gps_cog, gps_sog]
                    
                    id.append(new_data[0])
                    Latitude.append(new_data[1])
                    Longitude.append(new_data[2])
                    timestamp.append(new_data[3])
                    return True, gps_sog, gps_cog
                else:
                    print("Invalid GPS data.")
                    return False, None, None
            else:
                print("No valid data found.")
                return False, None, None
        else:
            print("No data found.")
            return False, None, None
    except Exception as e:
        print(f"Error fetching data from Firebase: {e}")
        return False, None, None

# Fungsi untuk memperbarui tabel hanya 10 data pertama
def update_table():
    if len(id) > 10:
        return

    latest_data = pd.DataFrame({
        "ID": id[:10],
        "Latitude": Latitude[:10],
        "Longitude": Longitude[:10],
        "Timestamp": timestamp[:10],
    })
    
    table_placeholder.dataframe(latest_data, width=700)

# Set up the page layout
st.set_page_config(page_title="Monitoring Kapal", layout="wide")

# Custom style for the application
st.markdown(
    """
    <style>
        .header {
            background-color: #005EB8; 
            padding: 20px; 
            border-radius: 10px; 
            color: white; 
            text-align: center; 
        }
        .section {
            background-color: #E8F0FE; 
            padding: 15px; 
            border-radius: 10px; 
            margin-top: 10px;
        }
        .subheader {
            font-size: 1.5rem; 
            margin-bottom: 10px;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown('<div class="header"><h2>Mavis - Universitas Negeri Yogyakarta</h2></div>', unsafe_allow_html=True)

# Create columns for map and table
col1, col2 = st.columns(2)

with st.container():
    with col1:
        st.markdown('<div class="section"><h3 class="subheader">Lintasan : A</h3></div>', unsafe_allow_html=True)
        st.markdown('<div class="section"><h3 class="subheader">Position-Log :</h3></div>', unsafe_allow_html=True)

        st.subheader("Floating Ball Set")
        table_placeholder = st.empty()

        # Kolom untuk menampilkan gambar surface dan underwater
        foto1, foto2, video1 = st.columns(3)
        with foto1:
            st.markdown('<div class="section"><h3 class="subheader">Surface</h3></div>', unsafe_allow_html=True)
            surface_image_placeholder = st.empty()

        with foto2:
            st.markdown('<div class="section"><h3 class="subheader">Underwater</h3></div>', unsafe_allow_html=True)
            underwater_image_placeholder = st.empty()

        with video1:
            st.markdown('<div class="section"><h3 class="subheader">Live Stream</h3></div>', unsafe_allow_html=True)
            video_url = "https://www.youtube.com/watch?v=5MZo9otAWAw&list=PLlcDhwyfvStqCd7FVs5wvUIFAdTWVzfVt&index=2"
            st.video(video_url)

        st.markdown('<div class="section"><h3 class="subheader">Attitude Information : </h3></div>', unsafe_allow_html=True)
        sog_placeholder = st.empty()
        cog_placeholder = st.empty()

    with col2:
        st.markdown('<div class="section"><h3 class="subheader">Peta Lokasi Kapal</h3></div>', unsafe_allow_html=True)
        map_container = st.empty()

# Loop untuk polling data dan memperbarui tampilan
polling_interval = 1  # Polling data tiap 1 detik

while True:
    fetched, gps_sog, gps_cog = fetch_data()
    if fetched:
        update_table()
        sog_placeholder.text(f"Speed Over Ground (SOG): {gps_sog:.2f} Knot")
        cog_placeholder.text(f"Course Over Ground (COG): {gps_cog:.2f} Degrees")

    # Perbarui gambar Surface dan Underwater secara otomatis
    latest_surface_image = download_latest_file("permukaan")
    if latest_surface_image:
        surface_image_placeholder.image(latest_surface_image, width=210)

    latest_underwater_image = download_latest_file("dalam")
    if latest_underwater_image:
        underwater_image_placeholder.image(latest_underwater_image, width=210)

    # Perbarui peta dengan titik baru
    with map_container:
        create_map(gps_points)

    time.sleep(polling_interval)