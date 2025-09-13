import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import random
from collections import Counter

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")

st.markdown("""
    <style>
    h1 {font-size: 38px !important;}
    h2, h3, h4 {font-size: 26px !important;}
    p, li, div, span {font-size: 18px !important;}
    .stDataFrame, .stMarkdown, .stTable {font-size: 18px !important;}
    .big-title {font-size: 30px !important; font-weight: 700; color: #d32f2f; margin-top: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 YouTube Analyzer By Ardhan - Judul & Tag Rekomendasi")

# === Fungsi Copy ke Clipboard via JS ===
def copy_to_clipboard(text, key):
    safe_text = text.replace('"', '\\"')
    js_code = f"""
    <script>
    function copyText{key}() {{
        navigator.clipboard.writeText("{safe_text}");
        alert("📋 '{safe_text[:40]}...' berhasil disalin!");
    }}
    </script>
    <button onclick="copyText{key}()" style="background:#e0f2fe;padding:6px 12px;border-radius:8px;border:1px solid #38bdf8;cursor:pointer;font-size:15px;margin-bottom:6px;">
        📋 Salin
    </button>
    """
    st.markdown(js_code, unsafe_allow_html=True)

# === Input API Key YouTube ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

query = st.text_input("🎯 Masukkan niche/keyword (contoh: Healing Flute)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
max_fetch = st.slider("Jumlah maksimum video yang diambil", 50, 200, 100, step=50)

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

def search_videos(query, total_results=100):
    collected, page_token = [], None
    while len(collected) < total_results:
        need = min(50, total_results - len(collected))
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": need,
            "order": "relevance",  # mix lama + baru
            "key": api_key
        }
        if region != "ALL":
            params["regionCode"] = region
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(YOUTUBE_SEARCH_URL, params=params).json()
        items = resp.get("items", [])
        collected.extend(items)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return collected[:total_results]

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
    """Tentukan apakah video adalah Shorts (durasi < 60 detik)"""
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
        items = search_videos(query, total_results=max_fetch)
        if not items:
            st.warning("⚠️ Tidak ada hasil dari API.")
        else:
            video_ids = [it.get("id", {}).get("videoId") for it in items if it.get("id", {}).get("videoId")]
            details = get_video_stats(video_ids)

            data = []
            for v in details:
                try:
                    vid = v["id"]
                    snip = v.get("snippet", {})
                    stats = v.get("statistics", {})
                    content = v.get("contentDetails", {})

                    title = snip.get("title", "")
                    channel = snip.get("channelTitle", "")
                    views = int(stats.get("viewCount", 0))
                    published = snip.get("publishedAt", None)
                    duration = content.get("duration")

                    if not published:
                        continue

                    # Abaikan Shorts
                    if is_shorts(duration):
                        continue

                    published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
                    vph = round(views / age_hours, 2) if age_hours > 0 else 0

                    data.append([
                        title, channel, views, vph, len(title),
                        published_time, f"https://www.youtube.com/watch?v={vid}"
                    ])
                except Exception:
                    continue

            if not data:
                st.warning("⚠️ Tidak ada video valid.")
            else:
                df = pd.DataFrame(data, columns=[
                    "Judul","Channel","Views","VPH","Panjang Judul","Publish Datetime","Video Link"
                ])

                # 1) Views tertinggi → filter 9 bulan terakhir
                cutoff = datetime.now(timezone.utc) - timedelta(days=270)
                df_views = df[df["Publish Datetime"] >= cutoff].sort_values(by="Views", ascending=False).head(10)

                # 2) VPH tertinggi → tanpa batas waktu
                df_vph = df.sort_values(by="VPH", ascending=False).head(10)

                # 3) Gabungkan
                combined = pd.concat([df_views, df_vph]).drop_duplicates().reset_index(drop=True)

                # 4) Buat rekomendasi judul baru
                avg_len = int(combined["Panjang Judul"].mean()) if not combined.empty else 60
                words = " ".join(combined["Judul"].tolist()).split()
                unique_words = list(set([w for w in words if len(w) > 3]))

                rekom = []
                for _ in range(10):
                    sampled = random.sample(unique_words, min(len(unique_words), 6))
                    new_title = " ".join(sampled).title()
                    if len(new_title) < avg_len - 5:
                        new_title += " Music Relaxation"
                    rekom.append(new_title)

                st.markdown('<p class="big-title">📝 Rekomendasi Judul (Gabungan Views & VPH)</p>', unsafe_allow_html=True)
                st.write(f"📏 Rata-rata panjang judul kompetitor: **{avg_len} karakter**")

                for i, title in enumerate(rekom, 1):
                    st.markdown(f"**{i}. {title}**")
                    copy_to_clipboard(title, f"title{i}")

                # 5) Tag relevan
                st.markdown('<p class="big-title">🏷️ Tag Rekomendasi</p>', unsafe_allow_html=True)
                terms_all = [t.lower() for t in " ".join(combined["Judul"].tolist()).split() if len(t) > 3]
                freq = Counter(terms_all)
                top_tags = [tag for tag, _ in freq.most_common(20)]

                if top_tags:
                    # Tampilkan tag per item
                    for i, tag in enumerate(top_tags, 1):
                        st.markdown(f"- {tag}")
                        copy_to_clipboard(tag, f"tag{i}")

                    # Tombol salin semua tag sekaligus
                    all_tags_str = ", ".join(top_tags)
                    st.markdown("### 📋 Salin Semua Tag")
                    copy_to_clipboard(all_tags_str, "alltags")
                else:
                    st.info("Belum ada tag relevan yang bisa ditampilkan.")
