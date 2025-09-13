import streamlit as st
import requests
from datetime import datetime, timezone
import pyperclip

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
    sort_option = st.selectbox("Urutkan:", ["Paling Relevan", "Paling Banyak Ditonton", "Terbaru", "VPH Tertinggi"])
    submit = st.form_submit_button("🔍 Cari Video")

# === Fungsi Hitung VPH ===
def hitung_vph(views, publishedAt):
    published_time = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
    return round(views / hours, 2) if hours > 0 else 0

# === Panggil API YouTube ===
def get_youtube_videos(api_key, query, max_results=15):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key
    }
    r = requests.get(url, params=params).json()

    videos = []
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
    else:  # relevan (default API)
        return data

# === Jalankan pencarian ===
if submit:
    with st.spinner("Mengambil data dari YouTube..."):
        videos = get_youtube_videos(st.session_state.api_key, keyword)
        videos = urutkan_video(videos, sort_option)

    if not videos:
        st.error("❌ Tidak ada video ditemukan")
    else:
        st.success(f"{len(videos)} video ditemukan")

        # === Tampilkan Video + Copy Judul ===
        cols = st.columns(3)
        all_titles = []
        for i, v in enumerate(videos):
            with cols[i % 3]:
                st.image(v["thumbnail"])
                st.markdown(f"**[{v['title']}]({'https://www.youtube.com/watch?v=' + v['id']})**")
                st.caption(f"{v['channel']} • {v['views']:,} views • {round(v['vph'])} VPH")
                if st.button(f"📋 Copy Judul {i+1}", key=f"copy_{i}"):
                    pyperclip.copy(v["title"])
                    st.success("Judul berhasil dicopy!")
            all_titles.append(v["title"])

        # === Rekomendasi Judul ===
        st.subheader("💡 Rekomendasi Judul untuk Dipakai")
        for r in all_titles[:5]:
            st.write(f"- {r}")

        # === Auto Tag 500 karakter ===
        st.subheader("🏷️ Rekomendasi Tag (Max 500 karakter)")
        # gabungkan semua kata dari judul
        kata_unik = []
        for t in all_titles:
            for w in t.split():
                w = w.lower().strip("|,.-")
                if w not in kata_unik:
                    kata_unik.append(w)

        tag_string = ", ".join(kata_unik)
        if len(tag_string) > 500:
            tag_string = tag_string[:497] + "..."

        st.code(tag_string, language="text")

        if st.button("📋 Copy Tag"):
            pyperclip.copy(tag_string)
            st.success("Tag berhasil dicopy!")
