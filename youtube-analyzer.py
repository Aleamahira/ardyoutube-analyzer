import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
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
    2. Buat **Project Baru** (contoh: "YouTube Analyzer").  
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
    now = datetime.now(timezone.utc)
    one_year_ago = now - timedelta(days=365)  # 12 bulan terakhir

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": api_key,
        "publishedAfter": one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishedBefore": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
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

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key YouTube dulu!")
    elif not query:
        st.error("⚠️ Masukkan keyword niche!")
    else:
        videos = search_videos(query, max_results=max_results)
        video_ids = [v["id"]["videoId"] for v in videos if v.get("id", {}).get("videoId")]
        video_details = get_video_stats(video_ids)

        data, all_tags, title_lengths = [], [], []

        for v in video_details:
            vid = v["id"]
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})

            title = snippet.get("title", "")
            channel = snippet.get("channelTitle", "")
            thumbs = snippet.get("thumbnails", {})
            thumb = thumbs.get("high", {}).get("url") or thumbs.get("default", {}).get("url") or ""
            views = int(stats.get("viewCount", 0))
            published = snippet.get("publishedAt", "1970-01-01T00:00:00Z")

            # Hitung umur video (jam) & VPH (hanya sebagai metrik tambahan; bukan dasar "populer")
            try:
                published_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                published_time = datetime.now(timezone.utc)
            age_hours = max((datetime.now(timezone.utc) - published_time.replace(tzinfo=timezone.utc)).total_seconds()/3600, 0.0001)
            vph = round(views / age_hours, 2)

            title_lengths.append(len(title))
            tags = snippet.get("tags", [])
            if tags:
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

        # === Filter video valid (buang Views=0 atau VPH=0) ===
        if not df.empty:
            df = df[(df["Views"] > 0) & (df["VPH"] > 0)]

        # === Konfirmasi kebijakan metrik ===
        st.success("✅ Video Populer dihitung **hanya berdasarkan Views tertinggi** (bukan VPH). Rentang data: **12 bulan terakhir**.")

        if df.empty:
            st.warning("Tidak ada data video yang memenuhi kriteria saat ini.")
        else:
            # === Hasil Utama: Views Tertinggi ===
            st.subheader("👑 Video Populer (Views Tertinggi • 12 Bulan Terakhir)")
            df_views = df.sort_values(by="Views", ascending=False)
            st.dataframe(df_views[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

            # (Opsional) Tampilkan tabel VPH hanya sebagai referensi tambahan (bukan penentu populer)
            st.subheader("📎 Referensi Tambahan: VPH Tertinggi (Bukan Dasar Popularitas)")
            df_vph = df.sort_values(by="VPH", ascending=False)
            st.dataframe(df_vph[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

            # === Preview Thumbnail ===
            st.subheader("🖼️ Preview Thumbnail & Link Video")
            for _, row in df_views.iterrows():
                st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
                if row["Thumbnail"]:
                    st.image(row["Thumbnail"], width=300, caption=f"Views: {row['Views']} • VPH: {row['VPH']}")
                st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

            # === Panjang Judul ===
            st.subheader("📏 Analisis Panjang Judul")
            avg_len = round(sum(title_lengths)/len(title_lengths),2) if title_lengths else 0
            if avg_len > 0:
                st.write(f"- Rata-rata panjang judul: **{avg_len} karakter**")
                st.write(f"- Terpendek: {min(title_lengths)} | Terpanjang: {max(title_lengths)}")
                st.write(f"- Rekomendasi: fokus di sekitar **{int(avg_len-5)}–{int(avg_len+10)} karakter**")

            # === SEO-Friendly Titles ===
            st.subheader("📝 Rekomendasi Judul SEO-Friendly")
            unique_tags = list(set([t for t in all_tags if len(t) > 3]))
            seo_titles = []
            for _ in range(10):
                if unique_tags:
                    selected = random.sample(unique_tags, min(6,len(unique_tags)))
                    new_title = " ".join(selected).title()
                    if avg_len and len(new_title) < avg_len-10:
                        new_title += " Music Relaxation"
                    seo_titles.append(new_title)
            if seo_titles:
                for idx, title in enumerate(seo_titles, 1):
                    st.write(f"{idx}. {title}")
            else:
                st.info("Belum ada keyword yang cukup untuk membentuk judul SEO.")

            # === Tags ===
            st.subheader("🏷️ Rekomendasi Tag")
            counter = Counter([t.lower() for t in all_tags if len(t) > 3])
            top_tags = [tag for tag,_ in counter.most_common(25)]
            st.write(", ".join(top_tags) if top_tags else "Belum ada tag yang direkomendasikan.")

            # === Word Cloud ===
            st.subheader("☁️ Word Cloud dari Judul & Tag")
            text_blob = " ".join(all_tags)
            if text_blob.strip():
                wc = WordCloud(width=800, height=400, background_color="white").generate(text_blob)
                fig, ax = plt.subplots(figsize=(10,5))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

            # === Channel Authority (Views-based) ===
            st.subheader("📺 Channel Authority (Berbasis Views • 12 Bulan)")
            channel_stats = df.groupby("Channel").agg(
                Total_Views=("Views","sum"),
                Avg_Views=("Views","mean"),
                Jumlah_Video=("Judul","count")
            ).reset_index()
            channel_stats["Views_Authority_Score"] = channel_stats["Total_Views"]
            channel_stats = channel_stats.sort_values(by="Total_Views", ascending=False)
            st.dataframe(channel_stats)

            # === Heatmap Upload Time ===
            st.subheader("🕒 Best Time to Upload (Heatmap • Berdasarkan Frekuensi Upload)")
            if not df.empty:
                df["Publish Datetime"] = pd.to_datetime(df["Publish Time"])
                df["Hour"] = df["Publish Datetime"].dt.hour
                df["Day"] = df["Publish Datetime"].dt.day_name()
                day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                df["Day"] = pd.Categorical(df["Day"], categories=day_order, ordered=True)

                heatmap_data = df.pivot_table(
                    index="Day",
                    columns="Hour",
                    values="Judul",
                    aggfunc="count"
                ).fillna(0)

                if (heatmap_data.values.sum() > 0):
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
                else:
                    st.info("Data tidak cukup untuk membuat heatmap.")
            else:
                st.info("Data tidak cukup untuk membuat heatmap.")

            # === Top 10% Segmentation (berdasarkan Views) ===
            st.subheader("🔥 Video Performance Segmentation (Top 10% Views)")
            if not df.empty:
                threshold = df["Views"].quantile(0.9)
                top_videos = df[df["Views"] >= threshold]
                st.write(f"Menampilkan {len(top_videos)} video dengan Views di atas {threshold:.0f}")
                st.dataframe(top_videos[["Judul","Channel","Views","VPH","Publish Time"]])

                # Rekomendasi judul dari pola top 10% (Views)
                all_top_tags = []
                for title in top_videos["Judul"].tolist():
                    all_top_tags.extend(title.split())
                unique_top_tags = list(set([t for t in all_top_tags if len(t) > 3]))
                st.subheader("📝 Judul dari Pola Video Top 10% (Views)")
                for i in range(min(5, len(unique_top_tags))):
                    st.write(f"{i+1}. {' '.join(random.sample(unique_top_tags, min(6,len(unique_top_tags)))).title()}")

                # Competitor Gap Finder
                st.subheader("🕵️ Competitor Gap Finder")
                freq_all = Counter([t.lower() for t in all_tags if len(t) > 3])
                freq_top = Counter([t.lower() for t in all_top_tags if len(t) > 3])
                gap_keywords = [tag for tag,count in freq_top.items() if freq_all[tag] <= 2]
                st.write("💡 Keyword unik dari video top, jarang dipakai lainnya:")
                st.write(", ".join(gap_keywords) if gap_keywords else "Belum ditemukan keyword unik.")

            # === Trend Detector ===
            st.subheader("📊 Trend Detector (Google Trends)")
            try:
                pytrends = TrendReq(hl='en-US', tz=360)
                kw_list = [query]
                geo = region if region != "ALL" else ""  # fix ternary
                pytrends.build_payload(kw_list, cat=0, timeframe='today 3-m', geo=geo, gprop='')
                trend_data = pytrends.interest_over_time()
                if not trend_data.empty:
                    st.line_chart(trend_data[query])
                else:
                    st.info("Tidak ada data tren untuk keyword ini.")
            except Exception as e:
                st.warning(f"Gagal ambil data tren: {e}")

            # === Export CSV ===
            st.download_button("⬇️ Download CSV", df_views.to_csv(index=False), file_name="youtube_views_data.csv", mime="text/csv")
