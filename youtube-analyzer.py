import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
import seaborn as sns

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")

# CSS untuk perbesar tulisan
st.markdown("""
    <style>
    h1 {font-size: 40px !important;}
    h2, h3, h4 {font-size: 28px !important;}
    p, li, div, span {font-size: 18px !important;}
    .stDataFrame, .stMarkdown, .stTable {font-size: 18px !important;}
    .big-title {font-size: 32px !important; font-weight: bold; color: #d32f2f;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 YouTube Analyzer By Ardhan")

# === Input API Key YouTube ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

# Tombol untuk ambil API Key
if st.button("📥 Ambil API Key YouTube"):
    st.markdown("""
    👉 [Klik di sini untuk buat API Key YouTube](https://console.cloud.google.com/apis/credentials)  

    **Langkah Singkat untuk Pemula:**  
    1. Login ke [Google Cloud Console](https://console.cloud.google.com/) dengan akun Google.  
    2. Buat **Project Baru** (misalnya: "YouTube Analyzer").  
    3. Aktifkan **YouTube Data API v3** di menu Library.  
    4. Buka menu **Credentials** → klik **Create API Key**.  
    5. Copy API Key dan tempelkan di atas.  
    """)

# === Input Query ===
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])
max_results = st.slider("Jumlah video yang dianalisis", 5, 50, 20)

# === Pilihan Rentang Waktu ===
st.subheader("⏳ Pilih Rentang Waktu Analisis")
time_filter = st.selectbox("Rentang Waktu", ["24 Jam", "7 Hari", "1 Bulan", "3 Bulan", "6 Bulan", "All"])

def get_time_limit(choice):
    now = datetime.now(timezone.utc)
    if choice == "24 Jam":
        return now - timedelta(days=1)
    elif choice == "7 Hari":
        return now - timedelta(days=7)
    elif choice == "1 Bulan":
        return now - timedelta(days=30)
    elif choice == "3 Bulan":
        return now - timedelta(days=90)
    elif choice == "6 Bulan":
        return now - timedelta(days=180)
    return None  # untuk All

time_limit = get_time_limit(time_filter)

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# === Fungsi Helper ===
def search_videos(query, max_results=10):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": api_key
    }
    if region != "ALL":
        params["regionCode"] = region
    if video_type == "Live":
        params["eventType"] = "live"
    return requests.get(YOUTUBE_SEARCH_URL, params=params).json().get("items", [])

def get_video_stats(video_ids):
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key YouTube dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        videos = search_videos(query, max_results=max_results)
        video_ids = [v["id"]["videoId"] for v in videos]
        video_details = get_video_stats(video_ids)

        data, all_tags, title_lengths = [], [], []

        for v in video_details:
            vid = v["id"]
            snippet = v["snippet"]
            stats = v["statistics"]

            title = snippet["title"]
            channel = snippet["channelTitle"]
            thumb = snippet["thumbnails"]["high"]["url"]
            views = int(stats.get("viewCount", 0))
            published = snippet["publishedAt"]

            # Hitung umur video (jam)
            published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            age_hours = (datetime.now(timezone.utc) - published_time.replace(tzinfo=timezone.utc)).total_seconds()/3600
            vph = round(views / age_hours, 2) if age_hours > 0 else 0

            title_lengths.append(len(title))
            tags = snippet.get("tags", [])
            all_tags.extend(tags)
            all_tags.extend(title.split())

            data.append([
                title, channel, views, vph, len(title),
                published_time.strftime("%Y-%m-%d %H:%M"),
                published_time,
                thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
                f"https://www.youtube.com/watch?v={vid}"
            ])

        df = pd.DataFrame(data, columns=[
            "Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Publish Datetime",
            "Thumbnail","Download Link","Video Link"
        ])

        # === Filter Berdasarkan Rentang Waktu ===
        if time_limit:
            df = df[df["Publish Datetime"] >= time_limit]

        # Hanya tampilkan VPH > 0
        df = df[df["VPH"] > 0]

        # Urutkan berdasarkan VPH tertinggi
        df = df.sort_values(by="VPH", ascending=False)

        # === Hasil Utama ===
        st.markdown('<p class="big-title">📈 Hasil Analisis Video</p>', unsafe_allow_html=True)
        if df.empty:
            st.warning("⚠️ Tidak ada video sesuai filter waktu & VPH > 0.")
        else:
            st.dataframe(df[["Judul","Channel","Views","VPH","Publish Time"]], use_container_width=True)

            # === Preview Thumbnail ===
            st.subheader("🖼️ Preview Thumbnail & Link Video")
            for i, row in df.iterrows():
                st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
                st.image(row["Thumbnail"], width=400, caption=f"VPH: {row['VPH']}")
                st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

            # === Info VPH Tertinggi ===
            st.subheader("🔥 Video dengan VPH Tertinggi (dipush algoritma)")
            top_video = df.iloc[0]
            st.success(f"📌 **{top_video['Judul']}** | Channel: {top_video['Channel']} | VPH: {top_video['VPH']}")
