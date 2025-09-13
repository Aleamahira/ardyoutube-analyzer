import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from langdetect import detect
from pytrends.request import TrendReq
import seaborn as sns

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")

st.title("📊 YouTube Analyzer By Ardhan - ATM Edition (All-in-One)")

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

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# === Fungsi Helper ===
def search_videos(query, max_results=10):
    now = datetime.now(timezone.utc)
    one_year_ago = now - timedelta(days=365)  # batas 12 bulan terakhir

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": api_key,
        "publishedAfter": one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishedBefore": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
                thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
                f"https://www.youtube.com/watch?v={vid}"
            ])

        df = pd.DataFrame(data, columns=[
            "Judul","Channel","Views","VPH","Panjang Judul","Publish Time",
            "Thumbnail","Download Link","Video Link"
        ])
        df = df.sort_values(by="VPH", ascending=False)

        # === Hasil Utama ===
        st.subheader("📈 Hasil Analisis Video")
        st.dataframe(df[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

        # (semua fitur analisis lain tetap sama seperti kode kamu barusan…)
        # Thumbnail preview, rekomendasi judul SEO, tags, word cloud,
        # channel authority, heatmap, top 10% segmentation, gap finder,
        # trend detector, dan download CSV.
