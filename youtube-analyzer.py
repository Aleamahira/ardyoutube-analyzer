import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
from collections import Counter
import re

# ================== CONFIG ==================
st.set_page_config(page_title="YouTube Trending Explorer", layout="wide")
st.title("🎬 YouTube Trending Explorer")

# ================== SIDEBAR ==================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("YouTube Data API Key", st.session_state.api_key, type="password")
    max_per_order = st.slider("Jumlah per kategori (relevance/date/viewCount)", 5, 30, 15, 1)
    region = st.text_input("Kode Negara (mis. US, ID, ALL)", "US")
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
STOPWORDS = set("a an and the for of to in on with from by at as or & | - live official lyrics video music mix hour hours relax relaxing study sleep deep best new latest".split())

def iso8601_to_seconds(duration: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not m: return 0
    h, mi, s = (int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0))
    return h*3600 + mi*60 + s

def fmt_duration(sec: int) -> str:
    if sec <= 0: return "-"
    h, m, s = sec//3600, (sec%3600)//60, sec%60
    return f"{h}:{m:02d}:{s:02d}" if h>0 else f"{m}:{s:02d}"

def hitung_vph(views, publishedAt):
    try:
        published_time = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except: return 0.0
    hours = (datetime.now(timezone.utc) - published_time).total_seconds()/3600
    return round(views/hours,2) if hours>0 else 0.0

def format_views(n: int) -> str:
    try: n=int(n)
    except: return str(n)
    if n>=1_000_000: return f"{n/1_000_000:.1f}M"
    if n>=1_000: return f"{n/1_000:.1f}K"
    return str(n)

def format_rel_time(publishedAt):
    try: dt=datetime.strptime(publishedAt,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except: return "-"
    d=(datetime.now(timezone.utc)-dt).days
    if d<1: return "Hari ini"
    if d<30: return f"{d} hari lalu"
    if d<365: return f"{d//30} bulan lalu"
    return f"{d//365} tahun lalu"

def format_jam_utc(publishedAt):
    try: dt=datetime.strptime(publishedAt,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc); return dt.strftime("%Y-%m-%d %H:%M UTC")
    except: return "-"

# ================== API ==================
SEARCH_URL="https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL="https://www.googleapis.com/youtube/v3/videos"

def yt_search_ids(api_key, query, order, max_results):
    params={"part":"snippet","q":query,"type":"video","order":order,"maxResults":max_results,"key":api_key}
    r=requests.get(SEARCH_URL,params=params).json()
    return [it["id"]["videoId"] for it in r.get("items",[]) if it.get("id",{}).get("videoId")]

def yt_videos_detail(api_key, ids:list):
    if not ids: return []
    params={"part":"statistics,snippet,contentDetails","id":",".join(ids),"key":api_key}
    r=requests.get(VIDEOS_URL,params=params).json()
    out=[]
    for it in r.get("items",[]):
        stats,snip,det=it.get("statistics",{}),it.get("snippet",{}),it.get("contentDetails",{})
        views=int(stats.get("viewCount",0)) if stats.get("viewCount") else 0
        dur_s=iso8601_to_seconds(det.get("duration",""))
        rec={"id":it.get("id"),"title":snip.get("title",""),"channel":snip.get("channelTitle",""),
             "publishedAt":snip.get("publishedAt",""),"views":views,
             "thumbnail":(snip.get("thumbnails",{}).get("high") or snip.get("thumbnails",{}).get("default") or {}).get("url",""),
             "duration_sec":dur_s,"duration":fmt_duration(dur_s)}
        rec["vph"]=hitung_vph(rec["views"],rec["publishedAt"])
        out.append(rec)
    return out

def get_combined_videos(api_key, query, max_per_order=15):
    orders=["relevance","viewCount","date"]
    all_ids=[]
    for od in orders: all_ids+=yt_search_ids(api_key,query,od,max_per_order)
    uniq_ids=list(dict.fromkeys(all_ids))
    return yt_videos_detail(api_key,uniq_ids)

def get_trending(api_key, region="US", max_results=15):
    params={"part":"snippet,statistics,contentDetails","chart":"mostPopular","regionCode":region,"maxResults":max_results,"key":api_key}
    r=requests.get(VIDEOS_URL,params=params).json()
    return yt_videos_detail(api_key,[it["id"] for it in r.get("items",[])])

# ================== MAIN ==================
if submit:
    if not keyword.strip():
        st.info("📈 Menampilkan video trending (YouTube Most Popular)")
        videos_all=get_trending(st.session_state.api_key, region=region, max_results=max_per_order)
    else:
        st.info("🔎 Riset video berdasarkan kata kunci & gabungan Relevan/Views/Terbaru")
        videos_all=get_combined_videos(st.session_state.api_key, keyword, max_per_order=max_per_order)

    videos_sorted=videos_all if sort_option=="Paling Relevan" else (
        sorted(videos_all,key=lambda x:x["views"],reverse=True) if sort_option=="Paling Banyak Ditonton" else
        sorted(videos_all,key=lambda x:x["publishedAt"],reverse=True) if sort_option=="Terbaru" else
        sorted(videos_all,key=lambda x:x["vph"],reverse=True))

    if not videos_all:
        st.error("❌ Tidak ada video ditemukan")
    else:
        st.success(f"{len(videos_all)} video ditemukan")
        cols=st.columns(3)
        all_titles=[]; rows_for_csv=[]
        for i,v in enumerate(videos_sorted):
            with cols[i%3]:
                if v["thumbnail"]: st.image(v["thumbnail"])
                st.markdown(f"**[{v['title']}]({'https://www.youtube.com/watch?v='+v['id']})**")
                st.caption(v["channel"])
                c1,c2,c3=st.columns(3)
                with c1: st.markdown(f"<div style='background:#ff4b4b;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>👁 {format_views(v['views'])} views</div>",unsafe_allow_html=True)
                with c2: st.markdown(f"<div style='background:#4b8bff;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⚡ {v['vph']} VPH</div>",unsafe_allow_html=True)
                with c3: st.markdown(f"<div style='background:#4caf50;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⏱ {format_rel_time(v['publishedAt'])}</div>",unsafe_allow_html=True)
                st.caption(f"📅 {format_jam_utc(v['publishedAt'])} • ⏳ {v.get('duration','-')}")
            all_titles.append(v["title"])
            rows_for_csv.append({
                "Judul": v["title"], "Panjang Judul": len(v["title"]),
                "Channel": v["channel"], "Views": v["views"], "VPH": v["vph"],
                "Tanggal (relatif)": format_rel_time(v["publishedAt"]),
                "Jam Publish (UTC)": format_jam_utc(v["publishedAt"]),
                "Durasi": v.get("duration","-"),
                "Link": f"https://www.youtube.com/watch?v={v['id']}"
            })
        # download csv
        st.subheader("⬇️ Download Data")
        df=pd.DataFrame(rows_for_csv)
        csv_data=df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV",data=csv_data,file_name="youtube_riset.csv",mime="text/csv")
