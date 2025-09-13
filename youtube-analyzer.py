import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")

st.markdown("""
    <style>
    h1 {font-size: 40px !important;}
    h2, h3, h4 {font-size: 28px !important;}
    p, li, div, span {font-size: 18px !important;}
    .stDataFrame, .stMarkdown, .stTable {font-size: 18px !important;}
    .big-title {font-size: 32px !important; font-weight: 800; color: #d32f2f; margin-top: 8px;}
    .pill {display:inline-block; padding:6px 10px; border-radius:999px; background:#eef2ff; border:1px solid #c7d2fe; margin-right:6px; margin-bottom:6px; font-size:16px;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 YouTube Analyzer By Ardhan - ATM Edition (All-in-One)")

# === Input API Key ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])

# Input jumlah video
fetch_count = st.number_input("Jumlah video yang dianalisis", min_value=5, max_value=50, value=10, step=1)

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

def search_videos(query, max_results=50):
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
    if not video_ids:
        return []
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

def is_shorts(duration_iso):
    if not duration_iso:
        return False
    d = duration_iso.replace('PT','')
    minutes, seconds = 0, 0
    if 'M' in d:
        parts = d.split('M')
        minutes = int(parts[0]) if parts[0] else 0
        d = parts[1] if len(parts) > 1 else ''
    if 'S' in d:
        seconds = int(d.replace('S','')) if d.replace('S','') else 0
    total = minutes * 60 + seconds
    return total > 0 and total < 60

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key YouTube dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        items = search_videos(query, max_results=50)  # ambil sebanyak mungkin (maks 50)
        if not items:
            st.warning("⚠️ Tidak ada hasil dari API. Coba keyword lain.")
        else:
            # Ambil hanya sesuai input user
            items = items[:fetch_count]

            video_ids = [it.get("id", {}).get("videoId") for it in items if it.get("id", {}).get("videoId")]
            details = get_video_stats(video_ids)

            data, all_terms, title_lengths = [], [], []

            for v in details:
                try:
                    vid = v["id"]
                    snip = v.get("snippet", {})
                    stats = v.get("statistics", {})
                    content = v.get("contentDetails", {})

                    title = snip.get("title", "")
                    channel = snip.get("channelTitle", "")
                    thumb = snip.get("thumbnails", {}).get("high", {}).get("url", "")
                    views = int(stats.get("viewCount", 0))
                    published = snip.get("publishedAt", None)
                    duration = content.get("duration")

                    if video_type == "Shorts" and not is_shorts(duration):
                        continue
                    if video_type == "Reguler" and is_shorts(duration):
                        continue

                    if not published:
                        continue

                    published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
                    vph = round(views / age_hours, 2) if age_hours > 0 else 0

                    title_lengths.append(len(title))
                    all_terms.extend([w for w in title.split() if len(w) > 2])

                    data.append([
                        title, channel, views, vph, len(title),
                        published_time.strftime("%Y-%m-%d %H:%M"),
                        published_time,
                        thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
                        f"https://www.youtube.com/watch?v={vid}"
                    ])
                except:
                    continue

            df = pd.DataFrame(data, columns=[
                "Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Publish Datetime",
                "Thumbnail","Download Link","Video Link"
            ])

            # Hanya video dengan VPH > 0
            df = df[df["VPH"] > 0]

            # Urutkan berdasarkan VPH tertinggi
            df = df.sort_values(by="VPH", ascending=False).reset_index(drop=True)

            # Pastikan hasil final = fetch_count (atau warning kalau kurang)
            if len(df) < fetch_count:
                st.warning(f"⚠️ Hanya {len(df)} video yang bisa dianalisis (VPH > 0). Target: {fetch_count}")

            st.markdown('<p class="big-title">📈 Hasil Analisis Video</p>', unsafe_allow_html=True)
            st.dataframe(df[["Judul","Channel","Views","VPH","Publish Time"]], use_container_width=True)

            # === Top Judul
            st.subheader("🏆 Judul Populer (VPH Tertinggi)")
            for i, row in df.iterrows():
                st.markdown(f"**{i+1}. [{row['Judul']}]({row['Video Link']})**  \n"
                            f"Channel: `{row['Channel']}` • VPH: **{row['VPH']}**")

            # === Rekomendasi Judul
            st.subheader("📝 Rekomendasi Judul untuk Channel Anda")
            top10 = df.head(min(10, len(df)))
            avg_len = int(top10["Panjang Judul"].mean()) if not top10.empty else 60
            top_terms = " ".join(top10["Judul"].tolist()).split()
            unique_words = list(set([w for w in top_terms if len(w) > 3]))

            rekom = []
            for _ in range(5):
                sampled = random.sample(unique_words, min(len(unique_words), 6))
                new_title = " ".join(sampled).title()
                if len(new_title) < avg_len - 5:
                    new_title += " Music Relaxation"
                rekom.append(new_title)

            st.write(f"📏 Rata-rata panjang judul kompetitor: **{avg_len} karakter**")
            for i, title in enumerate(rekom, 1):
                st.write(f"{i}. {title}")
