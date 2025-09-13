import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Trending Explorer", layout="wide")

st.title("🎬 YouTube Trending Explorer")
st.write("Temukan video trending dan populer dari seluruh dunia")

# === Input API Key ===
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("YouTube Data API Key", st.session_state.api_key, type="password")
    if st.button("Simpan"):
        st.session_state.api_key = api_key
        st.success("API Key berhasil disimpan!")

if not st.session_state.api_key:
    st.warning("⚠️ Masukkan API Key di sidebar untuk mulai")
    st.stop()

# === Form Input ===
with st.form("youtube_form"):
    keyword = st.text_input("Kata Kunci", placeholder="healing flute meditation")
    periode = st.selectbox("Periode", ["Semua Waktu", "Hari Ini", "Minggu Ini", "Bulan Ini", "12 Bulan Terakhir"])
    negara = st.text_input("Negara (kode 2 huruf, contoh: US, ID, IN)", "US")
    tipe_video = st.radio("Tipe Video", ["Semua", "Regular", "Short", "Live"])
    sort_option = st.selectbox("Urutkan:", ["Paling Relevan", "Paling Banyak Ditonton", "Terbaru", "VPH Tertinggi"])
    submit = st.form_submit_button("🔍 Cari Video")

# === Fungsi Hitung VPH ===
def hitung_vph(views, publishedAt):
    published_time = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
    return round(views / hours, 2) if hours > 0 else 0

# === Ambil Video ===
def get_youtube_videos(api_key, query, region, periode, tipe, max_results=15):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "key": api_key
    }

    if query.strip():
        params["q"] = query
    if region and region.lower() != "worldwide":
        params["regionCode"] = region.upper()

    # === Filter periode ===
    now = datetime.utcnow()
    if periode == "Hari Ini":
        params["publishedAfter"] = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif periode == "Minggu Ini":
        params["publishedAfter"] = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif periode == "Bulan Ini":
        params["publishedAfter"] = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif periode == "12 Bulan Terakhir":
        params["publishedAfter"] = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # === Filter tipe video ===
    if tipe == "Short":
        params["videoDuration"] = "short"
    elif tipe == "Regular":
        params["videoDuration"] = "long"
    elif tipe == "Live":
        params["eventType"] = "live"

    r = requests.get(url, params=params).json()
    video_ids = [item["id"]["videoId"] for item in r.get("items", [])]

    if not video_ids:
        return []

    stats_url = "https://www.googleapis.com/youtube/v3/videos"
    stats_params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": api_key
    }
    stats_r = requests.get(stats_url, params=stats_params).json()

    videos = []
    for item in stats_r.get("items", []):
        vid = {
            "id": item["id"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "publishedAt": item["snippet"]["publishedAt"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        }
        vid["vph"] = hitung_vph(vid["views"], vid["publishedAt"])
        videos.append(vid)

    return videos

# === Sorting ===
def urutkan_video(data, mode):
    if mode == "Paling Banyak Ditonton":
        return sorted(data, key=lambda x: x["views"], reverse=True)
    elif mode == "Terbaru":
        return sorted(data, key=lambda x: x["publishedAt"], reverse=True)
    elif mode == "VPH Tertinggi":
        return sorted(data, key=lambda x: x["vph"], reverse=True)
    else:  # relevan
        return data

# === Jalankan pencarian ===
if submit:
    with st.spinner("Mengambil data dari YouTube..."):
        videos = get_youtube_videos(st.session_state.api_key, keyword, negara, periode, tipe_video)
        videos = urutkan_video(videos, sort_option)

    if not videos:
        st.error("❌ Tidak ada video ditemukan. Coba ganti kata kunci / periode / negara.")
    else:
        st.success(f"{len(videos)} video ditemukan")

        cols = st.columns(3)
        for i, v in enumerate(videos):
            with cols[i % 3]:
                st.image(v["thumbnail"])
                st.markdown(f"**[{v['title']}]({'https://www.youtube.com/watch?v=' + v['id']})**")
                st.caption(f"{v['channel']} • {v['views']:,} views • {round(v['vph'])} VPH")

        st.subheader("💡 Rekomendasi Judul untuk Dipakai")
        rekomendasi = [v["title"] for v in videos[:5]]
        for r in rekomendasi:
            st.text(r)
            st.download_button("📋 Salin Judul", r, file_name="judul.txt", mime="text/plain")
