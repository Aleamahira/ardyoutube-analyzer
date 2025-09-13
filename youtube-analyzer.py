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
    .metrics .metric {display:inline-block; margin-right:18px;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 YouTube Analyzer By Ardhan")

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
query = st.text_input("🎯 Masukkan niche/keyword (contoh: Music)")
region = st.selectbox("🌍 Negara Target", ["ALL","US","ID","JP","BR","IN","DE","GB","FR","ES"])
video_type = st.selectbox("🎥 Jenis Video", ["Semua","Reguler","Shorts","Live"])

# Jumlah permintaan ke API (maks 50 sesuai batas YouTube Search API)
fetch_count = st.slider("Jumlah video yang dianalisis (request ke API)", 5, 50, 20)

# === API endpoints ===
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# === Fungsi Helper ===
def search_videos(query, max_results=10):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": int(max_results),  # pastikan integer
        "order": "date",
        "key": api_key
    }
    if region != "ALL":
        params["regionCode"] = region
    if video_type == "Live":
        params["eventType"] = "live"
    # NOTE: API belum punya filter resmi "Shorts"; kalau perlu, saring berdasar durasi di bawah.
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
    # Shorts (umumnya) durasi < 60 detik
    # duration_iso contoh: "PT45S", "PT1M2S", "PT2M"
    if not duration_iso:
        return False
    d = duration_iso.replace('PT','')
    minutes = 0
    seconds = 0
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
        # 1) Ambil daftar video (sesuai fetch_count)
        items = search_videos(query, max_results=fetch_count)
        requested = fetch_count
        retrieved_from_api = len(items)

        if not items:
            st.warning("⚠️ Tidak ada hasil dari API untuk keyword ini. Coba ganti keyword atau tambah jumlah video.")
        else:
            video_ids = [it.get("id", {}).get("videoId") for it in items if it.get("id", {}).get("videoId")]
            # 2) Ambil detail
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

                    # Filter jenis video (Reguler/Shorts) jika dipilih
                    if video_type == "Shorts" and not is_shorts(duration):
                        continue
                    if video_type == "Reguler" and is_shorts(duration):
                        continue
                    # "Semua" → tak ada filter

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
                except Exception:
                    continue

            raw_valid = len(data)

            if not data:
                st.warning("⚠️ Tidak ada data video yang valid untuk dianalisis.")
            else:
                df = pd.DataFrame(data, columns=[
                    "Judul","Channel","Views","VPH","Panjang Judul","Publish Time","Publish Datetime",
                    "Thumbnail","Download Link","Video Link"
                ])

                # 3) Hanya video dengan VPH > 0 (sedang punya trafik)
                df = df[df["VPH"] > 0]

                # 4) Urutkan berdasarkan VPH tertinggi
                df = df.sort_values(by="VPH", ascending=False).reset_index(drop=True)

                final_count = len(df)

                # METRICS ringkas
                st.markdown("<div class='metrics'>", unsafe_allow_html=True)
                st.markdown(f"<span class='metric'>🧪 Diminta: <b>{requested}</b></span>", unsafe_allow_html=True)
                st.markdown(f"<span class='metric'>📥 Diterima API: <b>{retrieved_from_api}</b></span>", unsafe_allow_html=True)
                st.markdown(f"<span class='metric'>✅ Valid (sebelum filter VPH): <b>{raw_valid}</b></span>", unsafe_allow_html=True)
                st.markdown(f"<span class='metric'>🔥 Final (VPH > 0): <b>{final_count}</b></span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<p class="big-title">📈 Hasil Analisis Video (VPH Tertinggi)</p>', unsafe_allow_html=True)

                if df.empty:
                    st.warning("⚠️ Tidak ada video dengan VPH > 0.")
                else:
                    # Slider Top-N untuk kontrol tampilan (benar-benar membatasi yang ditampilkan)
                    max_top = max(1, min(final_count, 50))
                    top_n = st.slider("Tampilkan Top-N berdasarkan VPH", 1, max_top, min(10, max_top))
                    view_df = df.head(top_n)

                    # Tabel Utama (Top-N)
                    st.dataframe(view_df[["Judul","Channel","Views","VPH","Publish Time"]], use_container_width=True)

                    # Top-N Judul (VPH Tertinggi)
                    st.subheader("🏆 Top Judul (VPH Tertinggi)")
                    for i, row in view_df.iterrows():
                        st.markdown(f"**{i+1}. [{row['Judul']}]({row['Video Link']})**  \n"
                                    f"Channel: `{row['Channel']}` • VPH: **{row['VPH']}** • Publish: {row['Publish Time']}")

                    # === Rekomendasi Judul (gabung dari 10 VPH tertinggi, atau kurang jika data <10)
                    st.subheader("📝 Rekomendasi Judul untuk Channel Anda")
                    base_top = df.head(min(10, final_count)).reset_index(drop=True)
                    avg_len = int(base_top["Panjang Judul"].mean()) if not base_top.empty else 60

                    top_terms_str = " ".join(base_top["Judul"].tolist())
                    top_words = [w for w in top_terms_str.split() if len(w) > 3]
                    unique_words = list(set(top_words))

                    rekom = []
                    if unique_words:
                        for _ in range(5):
                            sampled = random.sample(unique_words, min(len(unique_words), 6))
                            new_title = " ".join(sampled).title()
                            # Sesuaikan panjang kira-kira mendekati rata-rata kompetitor
                            if len(new_title) < avg_len - 5:
                                new_title += " Music Relaxation"
                            rekom.append(new_title)

                    st.write(f"📏 Rata-rata panjang judul kompetitor (Top 10): **{avg_len} karakter**")
                    if rekom:
                        for i, title in enumerate(rekom, 1):
                            st.write(f"{i}. {title}")
                    else:
                        st.info("Belum cukup kata untuk menghasilkan rekomendasi judul.")

                    # Preview Thumbnail (Top-N sama seperti tabel)
                    st.subheader("🖼️ Preview Thumbnail & Link Video (Sesuai Top-N)")
                    for i, row in view_df.iterrows():
                        st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
                        if row["Thumbnail"]:
                            st.image(row["Thumbnail"], width=420, caption=f"VPH: {row['VPH']}")
                        st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

                    # Kata Populer di seluruh hasil final (opsional)
                    st.subheader("🧠 Kata Populer di Judul Kompetitor")
                    terms_all = [t.lower() for t in df["Judul"].str.split().sum() if len(t) > 3]
                    if terms_all:
                        freq = Counter(terms_all)
                        top_terms = freq.most_common(20)
                        st.markdown("".join([f"<span class='pill'>{k} • {v}x</span>" for k,v in top_terms]), unsafe_allow_html=True)

                    # Word Cloud dari judul final
                    if terms_all:
                        st.subheader("☁️ Word Cloud Judul")
                        try:
                            wc = WordCloud(width=900, height=500, background_color="white").generate(" ".join(terms_all))
                            fig, ax = plt.subplots(figsize=(12,6))
                            ax.imshow(wc, interpolation="bilinear")
                            ax.axis("off")
                            st.pyplot(fig)
                        except Exception:
                            st.info("WordCloud tidak bisa dibuat di lingkungan ini.")

                    # Heatmap waktu upload (tanpa filter waktu)
                    st.subheader("🕒 Best Time to Upload (Heatmap)")
                    df_hm = df.copy()
                    df_hm["Hour"] = df_hm["Publish Datetime"].dt.hour
                    df_hm["Day"] = df_hm["Publish Datetime"].dt.day_name()
                    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                    df_hm["Day"] = pd.Categorical(df_hm["Day"], categories=day_order, ordered=True)

                    heatmap_data = df_hm.pivot_table(index="Day", columns="Hour", values="Judul", aggfunc="count").fillna(0)

                    if not heatmap_data.empty:
                        plt.figure(figsize=(16,7))
                        sns.heatmap(
                            heatmap_data, cmap="YlGnBu", linewidths=0.5,
                            annot=True, fmt=".0f", cbar_kws={'label': 'Jumlah Video Diupload'}
                        )
                        plt.title("📊 Distribusi Upload (Hari vs Jam)", fontsize=18, pad=20)
                        plt.xlabel("Jam (0 = Tengah Malam, 23 = 11 Malam)", fontsize=14)
                        plt.ylabel("Hari", fontsize=14)
                        st.pyplot(plt)
                        st.markdown("✅ **Cara baca**: kotak paling gelap = kompetitor paling banyak upload di jam/harinya.")

                    # Channel Authority
                    st.subheader("📺 Channel Authority")
                    ch = df.groupby("Channel").agg({"Views":"sum", "VPH":"mean", "Judul":"count"}).reset_index()
                    ch = ch.rename(columns={"Judul":"Jumlah Video"})
                    ch["Authority Score"] = (ch["VPH"] * ch["Jumlah Video"]).round(2)
                    st.dataframe(ch.sort_values("Authority Score", ascending=False), use_container_width=True)

                    # Export CSV (hasil final)
                    st.download_button(
                        "⬇️ Download CSV (VPH > 0, urut tertinggi)",
                        df.to_csv(index=False),
                        file_name="youtube_vph_top.csv",
                        mime="text/csv"
                    )
