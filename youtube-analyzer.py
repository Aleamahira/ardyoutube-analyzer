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
import io

st.set_page_config(page_title="YouTube Analyzer", layout="wide")

st.title("📊 YouTube Analyzer - ATM Edition (All-in-One)")

# === Input API Keys ===
api_key = st.text_input("🔑 Masukkan YouTube API Key", type="password")
gemini_api_key = st.text_input("✨ (Opsional) Masukkan Gemini API Key", type="password")  # untuk fitur AI opsional

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
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    return requests.get(YOUTUBE_VIDEO_URL, params=params).json().get("items", [])

# === Analisis Video ===
if st.button("🔍 Analisis Video"):
    if not api_key:
        st.error("⚠️ Masukkan API Key dulu!")
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

        # === 1. Hasil Utama ===
        st.subheader("📈 Hasil Analisis Video")
        st.dataframe(df[["Judul","Channel","Views","VPH","Panjang Judul","Publish Time"]])

        # === 2. Thumbnail Preview ===
        st.subheader("🖼️ Preview Thumbnail & Link Video")
        for i, row in df.iterrows():
            st.markdown(f"### ▶️ [{row['Judul']}]({row['Video Link']})")
            st.image(row["Thumbnail"], width=300, caption=f"VPH: {row['VPH']}")
            st.markdown(f"[📥 Download Thumbnail]({row['Download Link']})")

        # === 3. CTR Proxy (Thumbnail Analysis) ===
        st.subheader("👁️ CTR Proxy (Thumbnail Analysis)")
        st.write("⚡ Warna & teks thumbnail berpengaruh pada CTR. Analisis lebih lanjut bisa ditambah OCR/warna dominan.")

        # === 4. Analisis Panjang Judul ===
        st.subheader("📏 Analisis Panjang Judul")
        avg_len = round(sum(title_lengths)/len(title_lengths),2)
        st.write(f"- Rata-rata panjang judul: **{avg_len} karakter**")
        st.write(f"- Terpendek: {min(title_lengths)} | Terpanjang: {max(title_lengths)}")
        st.write(f"- Rekomendasi: fokus di sekitar **{int(avg_len-5)}–{int(avg_len+10)} karakter**")

        # === 5. SEO-Friendly Titles ===
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

        # === 6. Tag Recommendation ===
        st.subheader("🏷️ Rekomendasi Tag")
        counter = Counter([t.lower() for t in all_tags if len(t) > 3])
        top_tags = [tag for tag,_ in counter.most_common(25)]
        st.write(", ".join(top_tags))

        # === 7. Word Cloud ===
        st.subheader("☁️ Word Cloud dari Judul & Tag")
        text_blob = " ".join(all_tags)
        if text_blob.strip():
            wc = WordCloud(width=800, height=400, background_color="white").generate(text_blob)
            fig, ax = plt.subplots(figsize=(10,5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

        # === 8. Channel Authority & Consistency ===
        st.subheader("📺 Data Channel (Authority & Consistency)")
        channel_stats = df.groupby("Channel").agg({
            "Views":"sum",
            "VPH":"mean",
            "Judul":"count"
        }).reset_index().rename(columns={"Judul":"Jumlah Video"})
        channel_stats["Authority Score"] = round(channel_stats["VPH"] * channel_stats["Jumlah Video"],2)
        st.dataframe(channel_stats)

        # === 9. Best Time to Upload (Heatmap) ===
        st.subheader("🕒 Best Time to Upload (Heatmap)")
        df["Publish Datetime"] = pd.to_datetime(df["Publish Time"])
        df["Hour"] = df["Publish Datetime"].dt.hour
        df["Day"] = df["Publish Datetime"].dt.day_name()
        heatmap_data = df.pivot_table(index="Day", columns="Hour", values="Judul", aggfunc="count").fillna(0)
        plt.figure(figsize=(12,6))
        sns.heatmap(heatmap_data, cmap="YlOrRd", linewidths=0.5, annot=True, fmt=".0f")
        plt.title("Distribusi Upload Video (Jam vs Hari)")
        st.pyplot(plt)

        # === 10. Video Performance Segmentation ===
        st.subheader("🔥 Video Performance Segmentation (Top 10% VPH)")
        threshold = df["VPH"].quantile(0.9)
        top_videos = df[df["VPH"] >= threshold]
        st.write(f"Menampilkan {len(top_videos)} video dengan VPH di atas {threshold:.2f}")
        st.dataframe(top_videos[["Judul","Channel","Views","VPH","Publish Time"]])

        # judul rekomendasi dari top video
        all_top_tags = []
        for title in top_videos["Judul"].tolist():
            all_top_tags.extend(title.split())
        unique_top_tags = list(set([t for t in all_top_tags if len(t) > 3]))
        st.subheader("📝 Judul dari Pola Video Top 10%")
        for i in range(5):
            st.write(f"{i+1}. {' '.join(random.sample(unique_top_tags, min(6,len(unique_top_tags)))).title()}")

        # === 11. Competitor Gap Finder ===
        st.subheader("🕵️ Competitor Gap Finder")
        freq_all = Counter([t.lower() for t in all_tags if len(t) > 3])
        freq_top = Counter([t.lower() for t in all_top_tags if len(t) > 3])
        gap_keywords = [tag for tag,count in freq_top.items() if freq_all[tag] <= 2]  # muncul di top, jarang di semua
        st.write("💡 Keyword unik dari video top, jarang dipakai lainnya:")
        st.write(", ".join(gap_keywords))

        # === 12. Trend Detector ===
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

        # === 13. Export CSV & Excel ===
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="youtube_vph_data.csv", mime="text/csv")

        # === 14. AI Assistant (opsional Gemini/GPT) ===
        if gemini_api_key:
            st.subheader("✨ AI Assistant (Gemini/GPT)")
            st.info("🚧 Belum diimplementasi penuh. Bisa dipakai untuk auto-generate judul, deskripsi, tag multi-bahasa.")
            # Di sini nanti tinggal ditambahkan call ke Gemini API
