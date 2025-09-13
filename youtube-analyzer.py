import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from langdetect import detect
from pytrends.request import TrendReq
import seaborn as sns
import google.generativeai as genai

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")
st.title("📊 YouTube Analyzer ( By Ardhan )")

# === Input API Keys ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

gemini_api_key = st.text_input(
    "✨ Masukkan Gemini API Key (Opsional)", 
    type="password", 
    help="Jika ingin generate judul & deskripsi otomatis dengan AI."
)
st.markdown(
    """
    👉 [Buat API Key Gemini di sini](https://aistudio.google.com/app/apikey)  
    (Login dengan akun Google Anda, lalu copy API Key dan tempel di atas)
    """
)

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

# === List kode negara YouTube + nama ===
YOUTUBE_REGIONS = {
    "ALL": "🌍 Global (Semua Negara)",
    "US": "🇺🇸 United States",
    "ID": "🇮🇩 Indonesia",
    "JP": "🇯🇵 Japan",
    "BR": "🇧🇷 Brazil",
    "IN": "🇮🇳 India",
    "DE": "🇩🇪 Germany",
    "GB": "🇬🇧 United Kingdom",
    "FR": "🇫🇷 France",
    "ES": "🇪🇸 Spain",
    "IT": "🇮🇹 Italy",
    "MX": "🇲🇽 Mexico",
    "KR": "🇰🇷 South Korea",
    "CA": "🇨🇦 Canada",
    "RU": "🇷🇺 Russia",
    "TR": "🇹🇷 Turkey",
    "VN": "🇻🇳 Vietnam",
    "PH": "🇵🇭 Philippines",
    "MY": "🇲🇾 Malaysia",
    "NG": "🇳🇬 Nigeria",
    "EG": "🇪🇬 Egypt",
    "SA": "🇸🇦 Saudi Arabia",
    "AE": "🇦🇪 United Arab Emirates",
    "TH": "🇹🇭 Thailand",
    "SG": "🇸🇬 Singapore",
    "ZA": "🇿🇦 South Africa",
}

# === Input Query ===
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
selected_regions = st.multiselect(
    "🌍 Pilih Negara Target (bisa lebih dari satu)",
    options=list(YOUTUBE_REGIONS.values()),
    default=["🌍 Global (Semua Negara)"]
)
region_codes = [code for code, name in YOUTUBE_REGIONS.items() if name in selected_regions]

video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])
max_results = st.slider("Jumlah video yang dianalisis per negara", 5, 50, 20)

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# === Fungsi Helper ===
def search_videos(query, max_results=10, regions=None):
    results = []
    if not regions or "ALL" in regions:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": "date",
            "key": api_key
        }
        res = requests.get(YOUTUBE_SEARCH_URL, params=params).json().get("items", [])
        for r in res:
            r["region"] = "ALL"
        results.extend(res)
    else:
        for region_code in regions:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": "date",
                "regionCode": region_code,
                "key": api_key
            }
            res = requests.get(YOUTUBE_SEARCH_URL, params=params).json().get("items", [])
            for r in res:
                r["region"] = region_code
            results.extend(res)
    return results

def get_video_stats(video_ids):
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

def generate_ai_content(prompt, model="gemini-1.5-flash"):
    try:
        response = genai.GenerativeModel(model).generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error: {e}"

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key YouTube dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        videos = search_videos(query, max_results=max_results, regions=region_codes)
        video_ids = [v["id"]["videoId"] for v in videos if "videoId" in v["id"]]
        video_details = get_video_stats(video_ids)

        data, all_tags, title_lengths = [], [], []

        for v in video_details:
            vid = v["id"]
            snippet = v["snippet"]
            stats = v["statistics"]
            region_code = next((item["region"] for item in videos if "videoId" in item["id"] and item["id"]["videoId"] == vid), "Unknown")

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
                f"https://www.youtube.com/watch?v={vid}",
                region_code
            ])

        df = pd.DataFrame(data, columns=[
            "Judul","Channel","Views","VPH","Panjang Judul","Publish Time",
            "Thumbnail","Download Link","Video Link","Region"
        ])
        df = df.sort_values(by="VPH", ascending=False)

        # === Filter Region ===
        st.subheader("🌍 Filter Hasil berdasarkan Region")
        available_regions = df["Region"].unique().tolist()
        selected_region_filter = st.multiselect("Pilih region untuk ditampilkan", available_regions, default=available_regions)
        filtered_df = df[df["Region"].isin(selected_region_filter)]

        # === Hasil Utama ===
        st.subheader("📈 Hasil Analisis Video")
        st.dataframe(filtered_df[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Region"]])
