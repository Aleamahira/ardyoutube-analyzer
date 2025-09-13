import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
from collections import Counter
import re

# ================== APP CONFIG ==================
st.set_page_config(page_title="YouTube Trending Explorer", layout="wide")
st.title("🎬 YouTube Trending Explorer")

# ================== YOUTUBE REGIONS (regionCode) ==================
YOUTUBE_REGIONS = {
    "Global (US default)": "US",
    "Argentina":"AR","Australia":"AU","Austria":"AT","Bahrain":"BH","Bangladesh":"BD","Belgium":"BE","Bolivia":"BO",
    "Bosnia and Herzegovina":"BA","Brazil":"BR","Bulgaria":"BG","Canada":"CA","Chile":"CL","Colombia":"CO",
    "Costa Rica":"CR","Croatia":"HR","Cyprus":"CY","Czech Republic":"CZ","Denmark":"DK","Dominican Republic":"DO",
    "Ecuador":"EC","Egypt":"EG","El Salvador":"SV","Estonia":"EE","Finland":"FI","France":"FR","Germany":"DE",
    "Greece":"GR","Guatemala":"GT","Honduras":"HN","Hong Kong":"HK","Hungary":"HU","Iceland":"IS","India":"IN",
    "Indonesia":"ID","Iraq":"IQ","Ireland":"IE","Israel":"IL","Italy":"IT","Jamaica":"JM","Japan":"JP","Jordan":"JO",
    "Kenya":"KE","Kuwait":"KW","Latvia":"LV","Lebanon":"LB","Libya":"LY","Liechtenstein":"LI","Lithuania":"LT",
    "Luxembourg":"LU","Malaysia":"MY","Malta":"MT","Mexico":"MX","Montenegro":"ME","Morocco":"MA","Nepal":"NP",
    "Netherlands":"NL","New Zealand":"NZ","Nicaragua":"NI","Nigeria":"NG","North Macedonia":"MK","Norway":"NO",
    "Oman":"OM","Pakistan":"PK","Panama":"PA","Paraguay":"PY","Peru":"PE","Philippines":"PH","Poland":"PL",
    "Portugal":"PT","Puerto Rico":"PR","Qatar":"QA","Romania":"RO","Russia":"RU","Saudi Arabia":"SA","Senegal":"SN",
    "Serbia":"RS","Singapore":"SG","Slovakia":"SK","Slovenia":"SI","South Africa":"ZA","South Korea":"KR","Spain":"ES",
    "Sri Lanka":"LK","Sweden":"SE","Switzerland":"CH","Taiwan":"TW","Tanzania":"TZ","Thailand":"TH","Tunisia":"TN",
    "Turkey":"TR","Uganda":"UG","Ukraine":"UA","United Arab Emirates":"AE","United Kingdom":"GB","United States":"US",
    "Uruguay":"UY","Venezuela":"VE","Vietnam":"VN","Zimbabwe":"ZW"
}

# ================== SIDEBAR ==================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("YouTube Data API Key", st.session_state.api_key, type="password")
    max_per_order = st.slider("Jumlah video per kategori (relevance/date/viewCount)", 5, 30, 15, 1)
    region_name = st.selectbox("Pilih Negara (regionCode)", list(YOUTUBE_REGIONS.keys()))
    region = YOUTUBE_REGIONS[region_name]
    if st.button("Simpan"):
        st.session_state.api_key = api_key
        st.success("API Key berhasil disimpan!")

if not st.session_state.api_key:
    st.warning("⚠️ Masukkan API Key di sidebar untuk mulai")
    st.stop()

# ================== FORM INPUT ==================
with st.form("youtube_form"):
    keyword = st.text_input("Kata Kunci (kosongkan untuk Trending)", placeholder="healing flute meditation")
    sort_option = st.selectbox("Urutkan:", ["Paling Relevan", "Paling Banyak Ditonton", "Terbaru", "VPH Tertinggi"])
    submit = st.form_submit_button("🔍 Cari Video")

# ================== UTILITIES ==================
STOPWORDS = set("""
a an and the for of to in on with from by at as or & | - live official lyrics lyric audio video music mix hour hours non-stop nonstop relaxing relax study sleep deep best new latest 4k 8k
""".split())

def iso8601_to_seconds(duration: str) -> int:
    # PT2H3M10S / PT45M / PT59S
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
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"

def hitung_vph(views, publishedAt):
    try:
        t = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return 0.0
    hrs = (datetime.now(timezone.utc) - t).total_seconds() / 3600
    return round(views / hrs, 2) if hrs > 0 else 0.0

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
    except:
        return "-"
    d = (datetime.now(timezone.utc) - dt).days
    if d < 1: return "Hari ini"
    if d < 30: return f"{d} hari lalu"
    if d < 365: return f"{d//30} bulan lalu"
    return f"{d//365} tahun lalu"

def format_jam_utc(publishedAt):
    try:
        dt = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        return "-"

# ================== API CALLS ==================
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def yt_search_ids(api_key, query, order, max_results):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": order,  # relevance | viewCount | date
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
        snip = it.get("snippet", {})
        stats = it.get("statistics", {})
        det = it.get("contentDetails", {})
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
            "duration": fmt_duration(dur_s)
        }
        rec["vph"] = hitung_vph(rec["views"], rec["publishedAt"])
        out.append(rec)
    return out

def get_combined_videos(api_key, query, max_per_order=15):
    orders = ["relevance", "viewCount", "date"]
    all_ids = []
    for od in orders:
        all_ids += yt_search_ids(api_key, query, od, max_per_order)
    uniq_ids = list(dict.fromkeys(all_ids))
    return yt_videos_detail(api_key, uniq_ids)

def get_trending(api_key, region="US", max_results=15):
    # mostPopular returns items directly; fetch IDs then detail for uniform fields
    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": api_key
    }
    r = requests.get(VIDEOS_URL, params=params).json()
    ids = [it["id"] for it in r.get("items", [])]
    return yt_videos_detail(api_key, ids)

# ================== SORTING ==================
def sort_videos(data, mode):
    if mode == "Paling Banyak Ditonton":
        return sorted(data, key=lambda x: x["views"], reverse=True)
    if mode == "Terbaru":
        return sorted(data, key=lambda x: x["publishedAt"], reverse=True)
    if mode == "VPH Tertinggi":
        return sorted(data, key=lambda x: x["vph"], reverse=True)
    return data  # Paling Relevan

# ================== REKOMENDASI JUDUL (≥66 chars) ==================
def top_keywords_from_titles(titles, topk=8):
    words = []
    for t in titles:
        for w in re.split(r"[^\w]+", t.lower()):
            if len(w) >= 3 and w not in STOPWORDS and not w.isdigit():
                words.append(w)
    cnt = Counter(words)
    return [w for w, _ in cnt.most_common(topk)]

def derive_duration_phrase(videos):
    secs = [v["duration_sec"] for v in videos if v.get("duration_sec", 0) > 0]
    if not secs:
        return "3 Hours"
    avg = sum(secs) / len(secs)
    if avg >= 2*3600: return "3 Hours"
    if avg >= 3600:   return "2 Hours"
    if avg >= 30*60:  return "1 Hour"
    return "45 Minutes"

def ensure_len(s, min_len=66):
    if len(s) >= min_len:
        return s
    pad = " | Focus • Study • Relax • Deep Sleep"
    need = min_len - len(s)
    return s + (pad if need <= len(pad) else pad + " • Inner Peace & Calm")

def generate_titles(keyword_main: str, videos: list, titles_all: list):
    kw = keyword_main.strip() or "Tibetan Healing Flute Meditation"
    topk = top_keywords_from_titles(titles_all, topk=8)
    k1 = (topk[0] if topk else "healing").title()
    k2 = (topk[1] if len(topk) > 1 else "sleep").title()
    dur = derive_duration_phrase(videos)

    # 3 pola yang diminta:
    t1 = f"Melt Stress & Heal Faster | {kw.title()} for Deep Relaxation, Sleep and Inner Peace"
    t2 = f"{kw.title()} | Deep Calm and {k1} Relief for {k2} • Night Routine & Overthinking"
    t3 = f"{dur} | {kw.title()} – Release Negativity, Cleanse Mind, Focus Better"

    # variasi tambahan:
    t4 = f"{kw.title()} • {k1} {k2} Therapy – Reduce Anxiety, Boost Serotonin, Gentle Breathing"
    t5 = f"{dur} Non-Stop • {kw.title()} – Stress Detox, Emotional Healing, Study & Work Flow"
    t6 = f"{kw.title()} for Total Reset – Calm Nerves, Soothe Thoughts, Fall Asleep Fast Tonight"

    cands = [t1, t2, t3, t4, t5, t6]
    final = []
    seen = set()
    for t in cands:
        tt = ensure_len(" ".join(t.split()))
        if tt.lower() not in seen:
            final.append(tt)
            seen.add(tt.lower())
    return final[:6]

# ================== MAIN ==================
if submit:
    # ambil data
    if not keyword.strip():
        st.info(f"📈 Menampilkan video trending di {region_name}")
        videos_all = get_trending(st.session_state.api_key, region=region, max_results=max_per_order)
    else:
        st.info(f"🔎 Riset keyword: **{keyword}** (gabungan relevance + viewCount + date)")
        videos_all = get_combined_videos(st.session_state.api_key, keyword, max_per_order=max_per_order)

    if not videos_all:
        st.error("❌ Tidak ada video ditemukan")
    else:
        videos_sorted = sort_videos(videos_all, sort_option)
        st.success(f"{len(videos_all)} video terhimpun • Menampilkan urut: {sort_option}")

        # grid tampilan
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
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown(
                        f"<div style='background:#4b8bff;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⚡ {v['vph']} VPH</div>",
                        unsafe_allow_html=True
                    )
                with c3:
                    st.markdown(
                        f"<div style='background:#4caf50;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⏱ {format_rel_time(v['publishedAt'])}</div>",
                        unsafe_allow_html=True
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
                "Durasi": v.get("duration", "-"),
                "Link": f"https://www.youtube.com/watch?v={v['id']}"
            })

        # ========== REKOMENDASI JUDUL ==========
        st.subheader("💡 Rekomendasi Judul (otomatis, min 66 karakter)")
        rec_titles = generate_titles(keyword, videos_all, all_titles)
        for idx, rt in enumerate(rec_titles, 1):
            st.text_input(f"Copy Judul {idx}", rt, key=f"rec_{idx}")

        # ========== TAG 500 KARAKTER (GABUNGAN SEMUA VIDEO) ==========
        st.subheader("🏷️ Rekomendasi Tag (gabungan semua judul, max 500 karakter)")
        uniq_words, seenw = [], set()
        for t in all_titles:
            for w in re.split(r"[^\w]+", t.lower()):
                w = w.strip()
                if len(w) >= 3 and w not in STOPWORDS and w not in seenw:
                    uniq_words.append(w)
                    seenw.add(w)
        tag_string = ", ".join(uniq_words)
        if len(tag_string) > 500:
            tag_string = tag_string[:497] + "..."
        st.code(tag_string, language="text")
        st.text_input("Copy Tag", tag_string, key="copy_tag")

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
