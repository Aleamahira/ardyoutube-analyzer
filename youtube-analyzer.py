import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
import random

st.set_page_config(page_title="YouTube Analyzer", layout="wide")

st.title("📊 YouTube Analyzer - VPH & SEO Title Generator")

# Input API Key manual
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])
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
    if region != "ALL":
        params["regionCode"] = region
    if video_type == "Live":
        params["eventType"] = "live"
    return requests.get(YOUTUBE_SEARCH_URL, params=params).json().get("items", [])

def get_video_stats(video_ids):
    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

# 🔍 Tombol Analisis
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
        all_tags = []
        title_lengths = []

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

            # Kumpulkan panjang judul
            title_lengths.append(len(title))

            # Kumpulkan tags (jika ada)
            tags = snippet.get("tags", [])
            all_tags.extend(tags)
            all_tags.extend(title.split())

            data.append([
                title, channel, views, vph, len(title),
                published_time.strftime("%Y-%m-%d %H:%M"),
                thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
            ])

        df = pd.DataFrame(data, columns=["Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Thumbnail","Download Link"])
        df = df.sort_values(by="VPH", ascending=False)

        st.subheader("📈 Hasil Analisis Video")
        st.dataframe(df[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

        st.subheader("🖼️ Preview Thumbnail & Download")
        for i, row in df.iterrows():
            st.image(row["Thumbnail"], width=300, caption=f"{row['Judul']} | VPH: {row['VPH']}")
            st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

        # Analisis panjang judul
        st.subheader("📏 Analisis Panjang Judul")
        avg_len = round(sum(title_lengths)/len(title_lengths),2)
        st.write(f"- Rata-rata panjang judul: **{avg_len} karakter**")
        st.write(f"- Terpendek: {min(title_lengths)} | Terpanjang: {max(title_lengths)}")
        st.write(f"- Rekomendasi: fokus di sekitar **{int(avg_len-5)}–{int(avg_len+10)} karakter**")

        # Generate judul SEO-friendly
        st.subheader("📝 Rekomendasi Judul SEO-Friendly")
        unique_tags = list(set([t for t in all_tags if len(t) > 3]))
        seo_titles = []
        for i in range(10):
            selected = random.sample(unique_tags, min(5,len(unique_tags)))
            new_title = " ".join(selected).title()
            # pastikan panjang sesuai range rata-rata
            if len(new_title) < avg_len-10:
                new_title += " Music Relaxation"
            seo_titles.append(new_title)

        for idx,title in enumerate(seo_titles,1):
            st.write(f"{idx}. {title}")

        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="youtube_vph_data.csv", mime="text/csv")
