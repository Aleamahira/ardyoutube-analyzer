import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="YouTube Analyzer", layout="wide")

st.title("📊 YouTube Analyzer - VPH & Trending Detector")

# Input API Key manual
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
max_results = st.slider("Jumlah video yang dianalisis", 5, 50, 20)

# API endpoints
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

def search_videos(query, max_results=10):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": api_key
    }
    r = requests.get(YOUTUBE_SEARCH_URL, params=params).json()
    return r.get("items", [])

def get_video_stats(video_ids):
    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": api_key
    }
    r = requests.get(YOUTUBE_VIDEO_URL, params=params).json()
    return r.get("items", [])

# 🔍 Tombol hanya 1
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        videos = search_videos(query, max_results=max_results)
        video_ids = [v["id"]["videoId"] for v in videos]

        video_details = get_video_stats(video_ids)

        data = []
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
            age_hours = (datetime.now(timezone.utc) - published_time.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            vph = round(views / age_hours, 2) if age_hours > 0 else 0

            data.append([title, channel, views, vph, thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"])

        df = pd.DataFrame(data, columns=["Judul", "Channel", "Views", "VPH", "Thumbnail", "Download Link"])
        df = df.sort_values(by="VPH", ascending=False)

        st.subheader("📈 Hasil Analisis")
        st.dataframe(df[["Judul", "Channel", "Views", "VPH"]])

        st.subheader("🖼️ Preview Thumbnail & Download")
        for i, row in df.iterrows():
            st.image(row["Thumbnail"], width=300, caption=f"{row['Judul']} | VPH: {row['VPH']}")
            st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="youtube_vph_data.csv", mime="text/csv")
