import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# ================== CONFIG ==================
st.set_page_config(page_title="YouTube Trending Explorer", layout="wide")
st.title("🎬 YouTube Trending Explorer")

# ================== YOUTUBE REGION LIST ==================
YOUTUBE_REGIONS = {
    "Global (US default)": "US",
    "Argentina": "AR","Australia": "AU","Austria": "AT","Bahrain": "BH","Bangladesh": "BD","Belgium": "BE",
    "Bolivia": "BO","Bosnia and Herzegovina": "BA","Brazil": "BR","Bulgaria": "BG","Canada": "CA","Chile": "CL",
    "Colombia": "CO","Costa Rica": "CR","Croatia": "HR","Cyprus": "CY","Czech Republic": "CZ","Denmark": "DK",
    "Dominican Republic": "DO","Ecuador": "EC","Egypt": "EG","El Salvador": "SV","Estonia": "EE","Finland": "FI",
    "France": "FR","Germany": "DE","Greece": "GR","Guatemala": "GT","Honduras": "HN","Hong Kong": "HK",
    "Hungary": "HU","Iceland": "IS","India": "IN","Indonesia": "ID","Iraq": "IQ","Ireland": "IE","Israel": "IL",
    "Italy": "IT","Jamaica": "JM","Japan": "JP","Jordan": "JO","Kenya": "KE","Kuwait": "KW","Latvia": "LV",
    "Lebanon": "LB","Libya": "LY","Liechtenstein": "LI","Lithuania": "LT","Luxembourg": "LU","Malaysia": "MY",
    "Malta": "MT","Mexico": "MX","Montenegro": "ME","Morocco": "MA","Nepal": "NP","Netherlands": "NL",
    "New Zealand": "NZ","Nicaragua": "NI","Nigeria": "NG","North Macedonia": "MK","Norway": "NO","Oman": "OM",
    "Pakistan": "PK","Panama": "PA","Paraguay": "PY","Peru": "PE","Philippines": "PH","Poland": "PL",
    "Portugal": "PT","Puerto Rico": "PR","Qatar": "QA","Romania": "RO","Russia": "RU","Saudi Arabia": "SA",
    "Senegal": "SN","Serbia": "RS","Singapore": "SG","Slovakia": "SK","Slovenia": "SI","South Africa": "ZA",
    "South Korea": "KR","Spain": "ES","Sri Lanka": "LK","Sweden": "SE","Switzerland": "CH","Taiwan": "TW",
    "Tanzania": "TZ","Thailand": "TH","Tunisia": "TN","Turkey": "TR","Uganda": "UG","Ukraine": "UA",
    "United Arab Emirates": "AE","United Kingdom": "GB","United States": "US","Uruguay": "UY","Venezuela": "VE",
    "Vietnam": "VN","Zimbabwe": "ZW"
}

# ================== SIDEBAR ==================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("YouTube Data API Key", st.session_state.api_key, type="password")
    max_per_order = st.slider("Jumlah video per kategori", 5, 30, 15, 1)
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
def hitung_vph(views, publishedAt):
    try:
        published_time = datetime.strptime(publishedAt,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except: return 0.0
    hours=(datetime.now(timezone.utc)-published_time).total_seconds()/3600
    return round(views/hours,2) if hours>0 else 0.0

def format_views(n):
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
VIDEOS_URL="https://www.googleapis.com/youtube/v3/videos"

def yt_videos_detail(api_key, ids:list):
    if not ids: return []
    params={"part":"statistics,snippet,contentDetails","id":",".join(ids),"key":api_key}
    r=requests.get(VIDEOS_URL,params=params).json()
    out=[]
    for it in r.get("items",[]):
        stats,snip=it.get("statistics",{}),it.get("snippet",{})
        views=int(stats.get("viewCount",0)) if stats.get("viewCount") else 0
        rec={"id":it.get("id"),"title":snip.get("title",""),"channel":snip.get("channelTitle",""),
             "publishedAt":snip.get("publishedAt",""),"views":views,
             "thumbnail":(snip.get("thumbnails",{}).get("high") or {}).get("url","")}
        rec["vph"]=hitung_vph(rec["views"],rec["publishedAt"])
        out.append(rec)
    return out

def get_trending(api_key, region="US", max_results=15):
    params={"part":"snippet,statistics","chart":"mostPopular","regionCode":region,"maxResults":max_results,"key":api_key}
    r=requests.get(VIDEOS_URL,params=params).json()
    return yt_videos_detail(api_key,[it["id"] for it in r.get("items",[])])

# ================== MAIN ==================
if submit:
    if not keyword.strip():
        st.info(f"📈 Menampilkan video trending di {region_name}")
        videos_all=get_trending(st.session_state.api_key, region=region, max_results=max_per_order)
    else:
        st.warning("🔎 Mode riset keyword belum diaktifkan di snippet ini.")
        videos_all=[]

    if not videos_all:
        st.error("❌ Tidak ada video ditemukan")
    else:
        st.success(f"{len(videos_all)} video ditemukan")
        cols=st.columns(3)
        rows_for_csv=[]
        for i,v in enumerate(videos_all):
            with cols[i%3]:
                if v["thumbnail"]: st.image(v["thumbnail"])
                st.markdown(f"**[{v['title']}]({'https://www.youtube.com/watch?v='+v['id']})**")
                st.caption(v["channel"])
                c1,c2,c3=st.columns(3)
                with c1: st.markdown(f"<div style='background:#ff4b4b;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>👁 {format_views(v['views'])} views</div>",unsafe_allow_html=True)
                with c2: st.markdown(f"<div style='background:#4b8bff;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⚡ {v['vph']} VPH</div>",unsafe_allow_html=True)
                with c3: st.markdown(f"<div style='background:#4caf50;color:white;padding:4px 8px;border-radius:6px;display:inline-block'>⏱ {format_rel_time(v['publishedAt'])}</div>",unsafe_allow_html=True)
                st.caption(f"📅 {format_jam_utc(v['publishedAt'])}")
            rows_for_csv.append({
                "Judul": v["title"], "Channel": v["channel"],
                "Views": v["views"], "VPH": v["vph"],
                "Tanggal (relatif)": format_rel_time(v["publishedAt"]),
                "Jam Publish (UTC)": format_jam_utc(v["publishedAt"]),
                "Link": f"https://www.youtube.com/watch?v={v['id']}"
            })
        # download csv
        st.subheader("⬇️ Download Data")
        df=pd.DataFrame(rows_for_csv)
        csv_data=df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV",data=csv_data,file_name="youtube_trending.csv",mime="text/csv")
