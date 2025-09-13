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

# CSS: perbesar tulisan & heading penting
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

# === Input API Key YouTube ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

# Tombol cepat ambil API Key
if st.button("📥 Ambil API Key YouTube"):
    st.markdown("""
    👉 [Klik di sini untuk buat API Key YouTube](https://console.cloud.google.com/apis/credentials)

    **Langkah Singkat untuk Pemula:**
    1) Login ke **Google Cloud Console**.  
    2) Buat **Project Baru** (misal: *YouTube Analyzer*).  
    3) Buka **Library** → aktifkan **YouTube Data API v3**.  
    4) Buka **Credentials** → **Create Credentials** → **API Key**.  
    5) Copy API Key dan tempelkan ke kolom di atas.
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
    # Catatan: YouTube API belum menyediakan filter resmi "Shorts" di endpoint Search
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

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key YouTube dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        videos = search_videos(query, max_results=max_results)
        if not videos:
            st.warning("⚠️ Tidak ada hasil dari API untuk keyword ini. Coba ganti keyword atau tambah jumlah video.")
        else:
            video_ids = [v["id"]["videoId"] for v in videos if v.get("id", {}).get("videoId")]
            video_details = get_video_stats(video_ids)

            data, all_terms, title_lengths = [], [], []

            for v in video_details:
                try:
                    vid = v["id"]
                    snip = v["snippet"]
                    stats = v.get("statistics", {})

                    title = snip.get("title", "")
                    channel = snip.get("channelTitle", "")
                    thumb = snip.get("thumbnails", {}).get("high", {}).get("url", "")
                    views = int(stats.get("viewCount", 0))
                    published = snip.get("publishedAt", None)

                    # Published time (UTC)
                    if published:
                        published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    else:
                        continue  # skip jika tidak ada tanggal

                    # Umur video (jam)
                    age_hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
                    vph = round(views / age_hours, 2) if age_hours > 0 else 0

                    title_lengths.append(len(title))

                    # Kumpulkan kata dari title (untuk "judul populer" / kata populer)
                    title_words = [w for w in title.split() if len(w) > 2]
                    all_terms.extend(title_words)

                    data.append([
                        title, channel, views, vph, len(title),
                        published_time.strftime("%Y-%m-%d %H:%M"),
                        published_time,
                        thumb, f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
                        f"https://www.youtube.com/watch?v={vid}"
                    ])
                except Exception:
                    # Lewati item yang tidak lengkap
                    continue

            if not data:
                st.warning("⚠️ Tidak ada data video yang valid untuk dianalisis.")
            else:
                df = pd.DataFrame(data, columns=[
                    "Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Publish Datetime",
                    "Thumbnail","Download Link","Video Link"
                ])

                # Hanya tampilkan yang VPH > 0 (sedang punya trafik)
                df = df[df["VPH"] > 0]

                # Urutkan berdasarkan VPH tertinggi
                df = df.sort_values(by="VPH", ascending=False)

                st.markdown('<p class="big-title">📈 Hasil Analisis Video (VPH Tertinggi)</p>', unsafe_allow_html=True)

                if df.empty:
                    st.warning("⚠️ Tidak ada video dengan VPH > 0.")
                else:
                    # Tabel ringkas utama
                    st.dataframe(
                        df[["Judul","Channel","Views","VPH","Publish Time"]],
                        use_container_width=True
                    )

                    # Top 10 Judul (VPH Tertinggi) — “judul populer”
                    st.subheader("🏆 Top 10 Judul (VPH Tertinggi)")
                    top10 = df.head(10).reset_index(drop=True)
                    for i, row in top10.iterrows():
                        st.markdown(f"**{i+1}. [{row['Judul']}]({row['Video Link']})**  \n"
                                    f"Channel: `{row['Channel']}` • VPH: **{row['VPH']}** • Publish: {row['Publish Time']}")

                    # Preview Thumbnail (Top 12 agar tidak terlalu panjang)
                    st.subheader("🖼️ Preview Thumbnail & Link Video (Top 12)")
                    for i, row in df.head(12).iterrows():
                        st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
                        if row["Thumbnail"]:
                            st.image(row["Thumbnail"], width=420, caption=f"VPH: {row['VPH']}")
                        st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

                    # Kata Populer di Judul (membantu ide judul)
                    st.subheader("🧠 Kata Populer di Judul")
                    terms = [t.lower() for t in all_terms if len(t) > 3]
                    if terms:
                        freq = Counter(terms)
                        top_terms = freq.most_common(20)
                        if top_terms:
                            st.markdown("".join([f"<span class='pill'>{k} • {v}x</span>" for k,v in top_terms]), unsafe_allow_html=True)

                    # Word Cloud Judul (opsional visual cepat)
                    if terms:
                        st.subheader("☁️ Word Cloud dari Judul")
                        try:
                            wc = WordCloud(width=900, height=500, background_color="white").generate(" ".join(terms))
                            fig, ax = plt.subplots(figsize=(12,6))
                            ax.imshow(wc, interpolation="bilinear")
                            ax.axis("off")
                            st.pyplot(fig)
                        except Exception:
                            st.info("WordCloud tidak dapat digenerate di lingkungan ini.")

                    # Heatmap waktu upload (tanpa filter waktu)
                    st.subheader("🕒 Best Time to Upload (Heatmap)")
                    df_hm = df.copy()
                    df_hm["Hour"] = df_hm["Publish Datetime"].dt.hour
                    df_hm["Day"] = df_hm["Publish Datetime"].dt.day_name()
                    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                    df_hm["Day"] = pd.Categorical(df_hm["Day"], categories=day_order, ordered=True)

                    heatmap_data = df_hm.pivot_table(
                        index="Day",
                        columns="Hour",
                        values="Judul",
                        aggfunc="count"
                    ).fillna(0)

                    if not heatmap_data.empty:
                        plt.figure(figsize=(16,7))
                        sns.heatmap(
                            heatmap_data,
                            cmap="YlGnBu",
                            linewidths=0.5,
                            annot=True,
                            fmt=".0f",
                            cbar_kws={'label': 'Jumlah Video Diupload'}
                        )
                        plt.title("📊 Distribusi Upload (Hari vs Jam)", fontsize=18, pad=20)
                        plt.xlabel("Jam (0 = Tengah Malam, 23 = 11 Malam)", fontsize=14)
                        plt.ylabel("Hari", fontsize=14)
                        st.pyplot(plt)
                        st.markdown("""
✅ **Cara membaca**: kotak paling gelap = paling banyak kompetitor upload di jam/harinya.  
Gunakan jam ramai untuk *ikut arus*, atau jam sepi untuk *lebih menonjol* dibanding kompetitor.
                        """)
                    else:
                        st.info("Belum cukup data untuk membuat heatmap.")

                    # Channel Authority (opsional insight channel)
                    st.subheader("📺 Channel Authority (ringkas)")
                    ch = df.groupby("Channel").agg({"Views":"sum", "VPH":"mean", "Judul":"count"}).reset_index()
                    ch = ch.rename(columns={"Judul":"Jumlah Video"})
                    ch["Authority Score"] = (ch["VPH"] * ch["Jumlah Video"]).round(2)
                    st.dataframe(ch.sort_values("Authority Score", ascending=False), use_container_width=True)

                    # Export CSV
                    st.download_button(
                        "⬇️ Download CSV (VPH > 0, diurutkan tertinggi)",
                        df.to_csv(index=False),
                        file_name="youtube_vph_top.csv",
                        mime="text/csv"
                    )
