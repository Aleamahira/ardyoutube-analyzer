import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
from collections import Counter
import re

# ================== CONFIG & TITLE ==================
st.set_page_config(page_title="YouTube Trending Explorer", layout="wide")
st.title("🎬 YouTube Trending Explorer")
st.write("Riset konten: gabungkan Relevan, Views tertinggi, Terbaru, lalu sortir sesuai pilihan. Hitung VPH, tampilkan jam publish, rekomendasi judul, dan export CSV.")

# ================== SIDEBAR ==================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("YouTube Data API Key", st.session_state.api_key, type="password")
    max_per_order = st.slider("Jumlah per kategori (relevance/date/viewCount)", 5, 30, 15, 1)
    if st.button("Simpan"):
        st.session_state.api_key = api_key
        st.success("API Key berhasil disimpan!")

if not st.session_state.api_key:
    st.warning("⚠️ Masukkan API Key di sidebar untuk mulai")
    st.stop()

# ================== FORM INPUT ==================
with st.form("youtube_form"):
    keyword = st.text_input("Kata Kunci (mis. healing flute meditation)", placeholder="healing flute meditation")
    sort_option = st.selectbox("Tampilkan urut:", ["Paling Relevan", "Paling Banyak Ditonton", "Terbaru", "VPH Tertinggi"])
    submit = st.form_submit_button("🔍 Cari Video")

# ================== UTILITIES ==================
STOPWORDS = set("""
a an and the for of to in on with from by at as or & | - live official lyrics video music mix hour hours relax relaxing study sleep deep best new latest
""".split())

def iso8601_to_seconds(duration: str) -> int:
    # Examples: PT2H3M10S, PT45M, PT59S
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h*3600 + mi*60 + s

def fmt_duration(sec: int) -> str:
    if sec <= 0:
        return "-"
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def hitung_vph(views, publishedAt):
    try:
        published_time = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return 0.0
    hours = (datetime.now(timezone.utc) - published_time).total_seconds() / 3600
    return round(views / hours, 2) if hours > 0 else 0.0

def format_views(n: int) -> str:
    try:
        n = int(n)
    except:
        return str(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def format_rel_time(publishedAt):
    try:
        dt = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return "-"
    delta_days = (datetime.now(timezone.utc) - dt).days
    if delta_days < 1:
        return "Hari ini"
    elif delta_days < 30:
        return f"{delta_days} hari lalu"
    elif delta_days < 365:
        return f"{delta_days//30} bulan lalu"
    return f"{delta_days//365} tahun lalu"

def format_jam_utc(publishedAt):
    try:
        dt = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "-"

# ================== YOUTUBE API ==================
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def yt_search_ids(api_key, query, order, max_results):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": order,              # 'relevance' | 'viewCount' | 'date'
        "maxResults": max_results,
        "key": api_key
    }
    r = requests.get(SEARCH_URL, params=params).json()
    return [it["id"]["videoId"] for it in r.get("items", []) if it.get("id", {}).get("videoId")]

def yt_videos_detail(api_key, ids: list):
    if not ids:
        return []
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(ids),
        "key": api_key
    }
    r = requests.get(VIDEOS_URL, params=params).json()
    out = []
    for it in r.get("items", []):
        stats = it.get("statistics", {})
        snip  = it.get("snippet", {})
        det   = it.get("contentDetails", {})
        views = int(stats.get("viewCount", 0)) if stats.get("viewCount") else 0
        dur_s = iso8601_to_seconds(det.get("duration", ""))
        rec = {
            "id": it.get("id"),
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "publishedAt": snip.get("publishedAt", ""),
            "views": views,
            "thumbnail": (snip.get("thumbnails", {}).get("high") or snip.get("thumbnails", {}).get("default") or {}).get("url", ""),
            "duration_sec": dur_s,
            "duration": fmt_duration(dur_s),
        }
        rec["vph"] = hitung_vph(rec["views"], rec["publishedAt"])
        out.append(rec)
    return out

def get_combined_videos(api_key, query, max_per_order=15):
    # Ambil tiga kategori: relevance, viewCount, date
    orders = ["relevance", "viewCount", "date"]
    all_ids = []
    for od in orders:
        all_ids += yt_search_ids(api_key, query, od, max_per_order)

    # de-duplikat IDs
    uniq_ids = list(dict.fromkeys(all_ids))
    videos = yt_videos_detail(api_key, uniq_ids)
    return videos

# ================== SORTING ==================
def urutkan_video(data, mode):
    if mode == "Paling Banyak Ditonton":
        return sorted(data, key=lambda x: x["views"], reverse=True)
    elif mode == "Terbaru":
        return sorted(data, key=lambda x: x["publishedAt"], reverse=True)
    elif mode == "VPH Tertinggi":
        return sorted(data, key=lambda x: x["vph"], reverse=True)
    else:  # Paling Relevan (pakai hasil gabungan tanpa ubah, namun kita bisa prioritaskan relevansi ringan)
        return data

# ================== REKOMENDASI JUDUL (>=66 CHAR) ==================
def top_keywords_from_titles(titles, topk=8):
    words = []
    for t in titles:
        for w in re.split(r"[^\w]+", t.lower()):
            if len(w) >= 3 and w not in STOPWORDS and not w.isdigit():
                words.append(w)
    cnt = Counter(words)
    return [w for w,_ in cnt.most_common(topk)]

def derive_duration_phrase(videos):
    # Pilih durasi dominan: >=2 jam -> "3 Hours", >=1 jam -> "2 Hours", >=30m -> "1 Hour", else "30 Minutes"
    secs = [v["duration_sec"] for v in videos if v.get("duration_sec", 0) > 0]
    if not secs:
        return "3 Hours"
    avg = sum(secs)/len(secs)
    if avg >= 2*3600:
        return "3 Hours"
    elif avg >= 3600:
        return "2 Hours"
    elif avg >= 30*60:
        return "1 Hour"
    return "45 Minutes"

def ensure_len(s, min_len=66):
    if len(s) >= min_len:
        return s
    # tambahkan hook aman hingga 66+ karakter
    extra = " | Focus • Study • Relax • Deep Sleep"
    need = max(0, min_len - len(s))
    return (s + extra) if need <= len(extra) else (s + extra + " • Inner Peace & Calm")

def generate_titles(keyword_main: str, videos: list, titles_all: list):
    kw = keyword_main.strip()
    if not kw:
        kw = "Tibetan Healing Flute Meditation"

    # kata kunci tren dari hasil riset
    topk = top_keywords_from_titles(titles_all, topk=8)  # contoh: tibetan, healing, sleep, 432hz, meditation, deep
    k1 = (topk[0] if topk else "healing")
    k2 = (topk[1] if len(topk) > 1 else "sleep")
    dur_phrase = derive_duration_phrase(videos)

    # 3 pola:
    # 1) [Trigger/ Solusi] + [Keyword Utama] + [Tambahan Nilai/ Manfaat]
    t1 = f"Melt Stress & Heal Faster | {kw.title()} for Deep Relaxation, Sleep and Inner Peace"
    # 2) [Keyword Utama] + [Emosi/ Hasil] + [Target Audiens/ Situasi]
    t2 = f"{kw.title()} | Deep Calm and {k1.title()} Relief for {k2.title()} • Night Routine & Overthinking"
    # 3) [Angka/ Durasi/ Format] + [Keyword Utama] + [Hook Menarik]
    t3 = f"{dur_phrase} | {kw.title()} – Release Negativity, Cleanse Mind, Focus Better"

    # variasi tambahan memanfaatkan top keywords
    t4 = f"{kw.title()} • {k1.title()} {k2.title()} Therapy – Reduce Anxiety, Boost Serotonin, Gentle Breathing"
    t5 = f"{dur_phrase} Non-Stop • {kw.title()} – Stress Detox, Emotional Healing, Study & Work Flow"
    t6 = f"{kw.title()} for Total Reset – Calm Nerves, Soothe Thoughts, Fall Asleep Fast Tonight"

    candidates = [t1, t2, t3, t4, t5, t6]
    final = [ensure_len(t) for t in candidates]
    # unik & trim spasi ganda
    uniq = []
    seen = set()
    for tt in final:
        u = " ".join(tt.split())
        if u.lower() not in seen:
            uniq.append(u)
            seen.add(u.lower())
    return uniq[:6]

# ================== MAIN FLOW ==================
if submit:
    with st.spinner("Mengambil & menggabungkan data dari YouTube..."):
        videos_all = get_combined_videos(st.session_state.api_key, keyword, max_per_order=max_per_order)
        videos_sorted = urutkan_video(videos_all, sort_option)

    if not videos_all:
        st.error("❌ Tidak ada video ditemukan")
    else:
        st.success(f"{len(videos_all)} video terhimpun (gabungan Relevan + Views + Terbaru) • Menampilkan: {sort_option}")

        # ========== GRID HASIL ==========
        cols = st.columns(3)
        all_titles = []
        rows_for_csv = []

        for i, v in enumerate(videos_sorted):
            with cols[i % 3]:
                if v["thumbnail"]:
                    st.image(v["thumbnail"])
                st.markdown(f"**[{v['title']}]({'https://www.youtube.com/watch?v=' + v['id']})**")
                st.caption(v["channel"])

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f"<div style='background:#ff4b4b;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>👁 {format_views(v['views'])} views</div>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"<div style='background:#4b8bff;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⚡ {v['vph']} VPH</div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<div style='background:#4caf50;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⏱ {format_rel_time(v['publishedAt'])}</div>",
                        unsafe_allow_html=True,
                    )

                st.caption(f"📅 {format_jam_utc(v['publishedAt'])} • ⏳ {v.get('duration','-')}")

            all_titles.append(v["title"])
            rows_for_csv.append({
                "Judul": v["title"],
                "Panjang Judul": len(v["title"]),
                "Channel": v["channel"],
                "Views": v["views"],
                "VPH": v["vph"],
                "Tanggal (relatif)": format_rel_time(v["publishedAt"]),
                "Jam Publish (UTC)": format_jam_utc(v["publishedAt"]),
                "Durasi": v.get("duration","-"),
                "Link": f"https://www.youtube.com/watch?v={v['id']}"
            })

        # ========== REKOMENDASI JUDUL (OTOMATIS, >=66 KARAKTER) ==========
        st.subheader("💡 Rekomendasi Judul (otomatis, min 66 karakter)")
        rec_titles = generate_titles(keyword, videos_all, all_titles)
        for rt in rec_titles:
            st.text_input("Copy Judul", rt, key=f"rec_{hash(rt)%10_000_000}")

        # ========== TAG 500 KARAKTER (GABUNGAN SEMUA VIDEO) ==========
        st.subheader("🏷️ Rekomendasi Tag (gabungan semua judul, max 500 karakter)")
        uniq_words = []
        seen = set()
        for t in all_titles:
            for w in re.split(r"[^\w]+", t.lower()):
                w = w.strip()
                if len(w) >= 3 and w not in STOPWORDS and w not in seen:
                    uniq_words.append(w)
                    seen.add(w)
        tag_string = ", ".join(uniq_words)
        if len(tag_string) > 500:
            tag_string = tag_string[:497] + "..."
        st.code(tag_string, language="text")
        st.text_input("Copy Tag", tag_string, key="copy_tags")

        # ========== DOWNLOAD CSV ==========
        st.subheader("⬇️ Download Data")
        df = pd.DataFrame(rows_for_csv)
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="youtube_riset.csv",
            mime="text/csv"
        )
