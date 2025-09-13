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

# === Konfigurasi Awal ===
st.set_page_config(page_title="YouTube Analyzer By Ardhan", layout="wide")

st.title("📊 YouTube Analyzer By Ardhan - ATM Edition (All-in-One)")

# === Input API Key YouTube ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")

# Tombol untuk ambil API Key
if st.button("📥 Ambil API Key YouTube"):
    st.markdown("""
    👉 [Klik di sini untuk buat API Key YouTube](https://console.cloud.google.com/apis/credentials)  

    **Langkah Singkat untuk Pemula:**  
    1. Login ke [Google Cloud Console](https://console.cloud.google.com/) dengan akun Google.  
    2. Buat **Project Baru** (misalnya: "YouTube Analyzer").  
    3. Aktifkan **YouTube Data API v3** di menu Library.  
    4. Buka menu **Credentials** → klik **Create API Key**.  
    5. Copy API Key dan tempelkan di atas.  
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
    return requests.get(YOUTUBE_SEARCH_URL, params=params).json().get("items", [])

def get_video_stats(video_ids):
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
        video_ids = [v["id"]["videoId"] for v in videos]
        video_details = get_video_stats(video_ids)

        data, all_tags, title_lengths = [], [], []

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
                f"https://www.youtube.com/watch?v={vid}"
            ])

        df = pd.DataFrame(data, columns=[
            "Judul","Channel","Views","VPH","Panjang Judul","Publish Time",
            "Thumbnail","Download Link","Video Link"
        ])
        df = df.sort_values(by="VPH", ascending=False)

        # === Hasil Utama ===
        st.subheader("📈 Hasil Analisis Video")
        st.dataframe(df[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

        # === Preview Thumbnail ===
        st.subheader("🖼️ Preview Thumbnail & Link Video")
        for i, row in df.iterrows():
            st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
            st.image(row["Thumbnail"], width=300, caption=f"VPH: {row['VPH']}")
            st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

        # === Panjang Judul ===
        st.subheader("📏 Analisis Panjang Judul")
        avg_len = round(sum(title_lengths)/len(title_lengths),2)
        st.write(f"- Rata-rata panjang judul: **{avg_len} karakter**")
        st.write(f"- Terpendek: {min(title_lengths)} | Terpanjang: {max(title_lengths)}")
        st.write(f"- Rekomendasi: fokus di sekitar **{int(avg_len-5)}–{int(avg_len+10)} karakter**")

        # === SEO-Friendly Titles ===
        st.subheader("📝 Rekomendasi Judul SEO-Friendly")
        unique_tags = list(set([t for t in all_tags if len(t) > 3]))
        seo_titles = []
        for i in range(10):
            selected = random.sample(unique_tags, min(6,len(unique_tags)))
            new_title = " ".join(selected).title()
            if len(new_title) < avg_len-10:
                new_title += " Music Relaxation"
            seo_titles.append(new_title)
        for idx,title in enumerate(seo_titles,1):
            st.write(f"{idx}. {title}")

        # === Tags ===
        st.subheader("🏷️ Rekomendasi Tag")
        counter = Counter([t.lower() for t in all_tags if len(t) > 3])
        top_tags = [tag for tag,_ in counter.most_common(25)]
        st.write(", ".join(top_tags))

        # === Word Cloud ===
        st.subheader("☁️ Word Cloud dari Judul & Tag")
        text_blob = " ".join(all_tags)
        if text_blob.strip():
            wc = WordCloud(width=800, height=400, background_color="white").generate(text_blob)
            fig, ax = plt.subplots(figsize=(10,5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

        # === Channel Authority ===
        st.subheader("📺 Data Channel (Authority & Consistency)")
        channel_stats = df.groupby("Channel").agg({
            "Views":"sum",
            "VPH":"mean",
            "Judul":"count"
        }).reset_index().rename(columns={"Judul":"Jumlah Video"})
        channel_stats["Authority Score"] = round(channel_stats["VPH"] * channel_stats["Jumlah Video"],2)
        st.dataframe(channel_stats)

        # === Heatmap Upload Time (User Friendly) ===
        st.subheader("🕒 Best Time to Upload (Heatmap)")

        df["Publish Datetime"] = pd.to_datetime(df["Publish Time"])
        df["Hour"] = df["Publish Datetime"].dt.hour
        df["Day"] = df["Publish Datetime"].dt.day_name()

        # Urutan hari agar rapi
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        df["Day"] = pd.Categorical(df["Day"], categories=day_order, ordered=True)

        heatmap_data = df.pivot_table(
            index="Day",
            columns="Hour",
            values="Judul",
            aggfunc="count"
        ).fillna(0)

        plt.figure(figsize=(14,6))
        sns.heatmap(
            heatmap_data,
            cmap="YlGnBu",
            linewidths=0.5,
            annot=True,
            fmt=".0f",
            cbar_kws={'label': 'Jumlah Video Diupload'}
        )
        plt.title("📊 Waktu Upload Populer (Hari vs Jam)", fontsize=14, pad=20)
        plt.xlabel("Jam (0 = Tengah Malam, 23 = 11 Malam)")
        plt.ylabel("Hari")
        st.pyplot(plt)

        # Tambahan keterangan untuk pemula
        st.markdown("""
✅ **Cara Membaca Heatmap**  
- Warna **lebih gelap/biru tua** = lebih banyak video kompetitor upload di jam tersebut.  
- Angka di dalam kotak = jumlah video yang diupload.  
- Cari jam/hari dengan warna **paling pekat** → itulah waktu paling sering dipakai untuk upload.  

💡 **Tips untuk Pemula**  
- Upload di jam **ramai (warna pekat)** untuk mengikuti tren.  
- Upload di jam **sepi (warna terang)** jika ingin lebih menonjol dibanding kompetitor.
""")

        # === Top 10% Segmentation ===
        st.subheader("🔥 Video Performance Segmentation (Top 10% VPH)")
        threshold = df["VPH"].quantile(0.9)
        top_videos = df[df["VPH"] >= threshold]
        st.write(f"Menampilkan {len(top_videos)} video dengan VPH di atas {threshold:.2f}")
        st.dataframe(top_videos[["Judul","Channel","Views","VPH","Publish Time"]])

        # Rekomendasi judul dari pola top 10%
        all_top_tags = []
        for title in top_videos["Judul"].tolist():
            all_top_tags.extend(title.split())
        unique_top_tags = list(set([t for t in all_top_tags if len(t) > 3]))
        st.subheader("📝 Judul dari Pola Video Top 10%")
        for i in range(5):
            st.write(f"{i+1}. {' '.join(random.sample(unique_top_tags, min(6,len(unique_top_tags)))).title()}")

        # === Competitor Gap Finder ===
        st.subheader("🕵️ Competitor Gap Finder")
        freq_all = Counter([t.lower() for t in all_tags if len(t) > 3])
        freq_top = Counter([t.lower() for t in all_top_tags if len(t) > 3])
        gap_keywords = [tag for tag,count in freq_top.items() if freq_all[tag] <= 2]
        st.write("💡 Keyword unik dari video top, jarang dipakai lainnya:")
        st.write(", ".join(gap_keywords))

        # === Trend Detector ===
        st.subheader("📊 Trend Detector (Google Trends)")
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            kw_list = [query]
            geo = region if region != "ALL" else ""
            pytrends.build_payload(kw_list, cat=0, timeframe='today 3-m', geo=geo, gprop='')
            trend_data = pytrends.interest_over_time()
            if not trend_data.empty:
                st.line_chart(trend_data[query])
            else:
                st.info("Tidak ada data tren untuk keyword ini.")
        except Exception as e:
            st.warning(f"Gagal ambil data tren: {e}")

        # === Export CSV ===
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="youtube_vph_data.csv", mime="text/csv")
