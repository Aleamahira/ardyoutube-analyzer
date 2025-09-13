import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from langdetect import detect
import numpy as np
from PIL import Image
import colorsys
import io

st.set_page_config(page_title="YouTube Analyzer", layout="wide")

st.title("📊 YouTube Analyzer - Competitor Research (Full Version)")

# Input API Key manual
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])
duration_filter = st.selectbox("⏱️ Durasi Video", ["Semua","Pendek (<5m)","Medium (5-20m)","Panjang (>20m)"])
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
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

def parse_duration(duration):
    h, m, s = 0, 0, 0
    if "H" in duration:
        h = int(duration.split("H")[0].replace("PT",""))
        duration = duration.split("H")[1]
    if "M" in duration:
        m = int(duration.split("M")[0].replace("PT","").replace("H",""))
        duration = duration.split("M")[1]
    if "S" in duration:
        s = int(duration.replace("S","").replace("PT",""))
    return h*3600 + m*60 + s

def get_dominant_color(url):
    try:
        img = Image.open(requests.get(url, stream=True).raw).resize((50,50))
        pixels = np.array(img).reshape(-1,3)
        avg = pixels.mean(axis=0)
        h, l, s = colorsys.rgb_to_hls(avg[0]/255, avg[1]/255, avg[2]/255)
        return (round(h*360), round(s*100), round(l*100))
    except:
        return None

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

        data, all_tags, title_lengths, publish_times = [], [], [], []

        for v in video_details:
            vid = v["id"]
            snippet = v["snippet"]
            stats = v["statistics"]
            details = v["contentDetails"]

            title = snippet["title"]
            channel = snippet["channelTitle"]
            thumb = snippet["thumbnails"]["high"]["url"]
            views = int(stats.get("viewCount", 0))
            published = snippet["publishedAt"]

            # Durasi
            duration = parse_duration(details["duration"])
            if duration_filter == "Pendek (<5m)" and duration > 300: continue
            if duration_filter == "Medium (5-20m)" and not (300 <= duration <= 1200): continue
            if duration_filter == "Panjang (>20m)" and duration < 1200: continue

            # Hitung umur video (jam)
            published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            age_hours = (datetime.now(timezone.utc) - published_time.replace(tzinfo=timezone.utc)).total_seconds()/3600
            vph = round(views / age_hours, 2) if age_hours > 0 else 0

            # Data tambahan
            title_lengths.append(len(title))
            publish_times.append(published_time)
            tags = snippet.get("tags", [])
            all_tags.extend(tags)
            all_tags.extend(title.split())

            dom_color = get_dominant_color(thumb)

            data.append([
                title, channel, views, vph, len(title),
                published_time.strftime("%Y-%m-%d %H:%M"),
                thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
                f"https://www.youtube.com/watch?v={vid}", duration, dom_color
            ])

        df = pd.DataFrame(data, columns=[
            "Judul","Channel","Views","VPH","Panjang Judul","Publish Time",
            "Thumbnail","Download Link","Video Link","Durasi (s)","Dominant Color"
        ])
        df = df.sort_values(by="VPH", ascending=False)

        # --- Data Channel Authority
        channel_stats = df.groupby("Channel").agg({
            "Views":"sum",
            "VPH":"mean",
            "Judul":"count"
        }).reset_index().rename(columns={"Judul":"Jumlah Video"})
        channel_stats["Authority Score"] = round(channel_stats["VPH"] * channel_stats["Jumlah Video"],2)

        # --- Rekomendasi Judul SEO-Friendly
        avg_len = round(sum(title_lengths)/len(title_lengths),2) if title_lengths else 50
        unique_tags = list(set([t for t in all_tags if len(t) > 3]))
        seo_titles = []
        for i in range(10):
            if len(unique_tags) >= 6:
                selected = random.sample(unique_tags, 6)
            else:
                selected = unique_tags
            new_title = " ".join(selected).title()
            if len(new_title) < avg_len-10:
                new_title += " Music Relaxation"
            seo_titles.append(new_title)

        # --- Rekomendasi Tag
        counter = Counter([t.lower() for t in all_tags if len(t) > 3])
        top_tags = [tag for tag,_ in counter.most_common(25)]

        # --- Export CSV
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("⬇️ Download CSV", csv, file_name="youtube_vph_data.csv", mime="text/csv")

        # --- Export Excel (.xlsx)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data Video")
            channel_stats.to_excel(writer, index=False, sheet_name="Data Channel")
            pd.DataFrame({"Rekomendasi Judul": seo_titles}).to_excel(writer, index=False, sheet_name="Rekomendasi Judul")
            pd.DataFrame({"Rekomendasi Tag": top_tags}).to_excel(writer, index=False, sheet_name="Rekomendasi Tag")
        excel_data = output.getvalue()

        st.download_button(
            label="⬇️ Download Excel (.xlsx)",
            data=excel_data,
            file_name="youtube_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
