"""Dashboard Kualitas Udara Beijing (PM2.5) - Streamlit.

Jalankan dari folder root submission:
    streamlit run dashboard/dashboard.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Kualitas Udara Beijing", page_icon="🌫️", layout="wide")

THRESH = 75
BLUE, LIGHT, ACCENT, GRAY = "#2F5D8A", "#A9C1D9", "#C8502E", "#6B7280"
DIR16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
AQI_BINS = [0, 35, 75, 115, 150, 250, np.inf]
AQI_LABELS = ["Sangat baik (0–35)", "Baik (35–75)", "Tercemar ringan (75–115)",
              "Tercemar sedang (115–150)", "Tercemar berat (150–250)", "Sangat berat (>250)"]
RAMP6 = ["#E3ECF5", "#C3D5E8", "#8FB0D2", "#5B88B8", "#2F5D8A", "#1B3A5C"]
# Koordinat PERKIRAAN lokasi distrik/stasiun (dataset tidak menyertakan koordinat)
COORD = {
    "Aotizhongxin": (39.982, 116.397), "Changping": (40.220, 116.230), "Dingling": (40.292, 116.220),
    "Dongsi": (39.929, 116.417), "Guanyuan": (39.929, 116.339), "Gucheng": (39.914, 116.184),
    "Huairou": (40.328, 116.628), "Nongzhanguan": (39.937, 116.461), "Shunyi": (40.127, 116.655),
    "Tiantan": (39.886, 116.407), "Wanliu": (39.987, 116.287), "Wanshouxigong": (39.878, 116.352)}

LAYOUT = dict(template="simple_white", margin=dict(l=10, r=10, t=50, b=10),
              font=dict(size=13), title_font=dict(size=15), hoverlabel=dict(font_size=13))


@st.cache_data
def load_data() -> pd.DataFrame:
    path = Path(__file__).parent / "main_data.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df["kategori"] = pd.cut(df["PM25"], bins=AQI_BINS, labels=AQI_LABELS, include_lowest=True)
    return df


df_all = load_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.title("Filter")
dmin, dmax = df_all["date"].min().date(), df_all["date"].max().date()
rng = st.sidebar.date_input("Rentang tanggal", value=(dmin, dmax), min_value=dmin, max_value=dmax)
stations_all = sorted(df_all["station"].unique())
sel = st.sidebar.multiselect("Stasiun", stations_all, default=stations_all)
st.sidebar.caption(f"Ambang PM2.5 harian: **{THRESH} µg/m³** (standar China Grade II).")

if isinstance(rng, tuple) and len(rng) == 2:
    d0, d1 = rng
else:  # pengguna baru memilih satu tanggal
    d0 = d1 = rng[0] if isinstance(rng, tuple) else rng

df = df_all[(df_all["date"].dt.date >= d0) & (df_all["date"].dt.date <= d1) & (df_all["station"].isin(sel))]

st.title("🌫️ Kualitas Udara Beijing: PM2.5")
st.caption("12 stasiun pemantau · Mar 2013 – Feb 2017 · rata-rata harian per stasiun")

if df["PM25"].dropna().empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah rentang tanggal atau pilih minimal satu stasiun.")
    st.stop()

# ---------------------------------------------------------------- KPI
by_st = df.groupby("station")["PM25"].mean()
monthly = df.assign(ym=df["date"].dt.to_period("M").dt.to_timestamp()).groupby("ym")["PM25"].mean()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rata-rata PM2.5", f"{df['PM25'].mean():.1f} µg/m³")
c2.metric(f"Hari > {THRESH} µg/m³", f"{(df['PM25'].dropna() > THRESH).mean() * 100:.1f}%")
c3.metric("Stasiun tertinggi", by_st.idxmax(), f"{by_st.max():.1f} µg/m³", delta_color="off")
worst = monthly.idxmax()
c4.metric("Bulan terburuk", f"{MONTHS[worst.month - 1]} {worst.year}", f"{monthly.max():.1f} µg/m³", delta_color="off")

tab1, tab2, tab3, tab4 = st.tabs(["① Tren & musim", "② Perbandingan stasiun", "③ Angin", "④ Kategori & peta"])

# ---------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Kapan PM2.5 melampaui ambang?")
    over = monthly[monthly > THRESH]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly.index, y=monthly.values, mode="lines", name="Rata-rata bulanan",
                             line=dict(color=BLUE, width=2.5), hovertemplate="%{x|%b %Y}: %{y:.1f} µg/m³<extra></extra>"))
    fig.add_trace(go.Scatter(x=over.index, y=over.values, mode="markers", name=f"Bulan > {THRESH}",
                             marker=dict(color=ACCENT, size=9, line=dict(color="white", width=1.5)),
                             hovertemplate="%{x|%b %Y}: %{y:.1f} µg/m³<extra></extra>"))
    fig.add_hline(y=THRESH, line_dash="dash", line_color=GRAY,
                  annotation_text="Ambang 75 µg/m³", annotation_position="bottom right")
    fig.update_layout(title="Rata-rata PM2.5 bulanan", yaxis_title="PM2.5 (µg/m³)", yaxis_rangemode="tozero",
                      legend=dict(orientation="h", y=1.1, x=0), **LAYOUT)
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    mo = df.groupby("month")["PM25"].mean().reindex(range(1, 13))
    fig = go.Figure(go.Bar(x=MONTHS, y=mo.values, marker_color=[ACCENT if v > THRESH else LIGHT for v in mo.values],
                           hovertemplate="%{x}: %{y:.1f} µg/m³<extra></extra>"))
    fig.add_hline(y=THRESH, line_dash="dash", line_color=GRAY)
    fig.update_layout(title="Rata-rata menurut bulan kalender", yaxis_title="PM2.5 (µg/m³)", **LAYOUT)
    left.plotly_chart(fig, width="stretch")

    order = ["Dingin", "Semi", "Panas", "Gugur"]
    se = df.groupby("season")["PM25"].agg(rata2="mean", over=lambda s: (s.dropna() > THRESH).mean() * 100).reindex(order)
    fig = go.Figure(go.Bar(x=order, y=se["rata2"], marker_color=[ACCENT if v > THRESH else LIGHT for v in se["rata2"]],
                           customdata=se["over"], hovertemplate="%{x}: %{y:.1f} µg/m³<br>%{customdata:.1f}% hari > 75<extra></extra>"))
    fig.add_hline(y=THRESH, line_dash="dash", line_color=GRAY)
    fig.update_layout(title="Rata-rata menurut musim", yaxis_title="PM2.5 (µg/m³)", **LAYOUT)
    right.plotly_chart(fig, width="stretch")
    st.info("Oranye = di atas ambang 75 µg/m³. Secara umum risiko tertinggi terjadi pada **Oktober–Maret**.")

# ---------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Stasiun mana yang paling tercemar?")
    stt = df.groupby("station")["PM25"].agg(rata2="mean", over=lambda s: (s.dropna() > THRESH).mean() * 100).sort_values("rata2")
    cols = [ACCENT if s == stt.rata2.idxmax() else BLUE if s == stt.rata2.idxmin() else LIGHT for s in stt.index]
    l, r = st.columns(2)
    fig = go.Figure(go.Bar(y=stt.index, x=stt["rata2"], orientation="h", marker_color=cols, text=stt["rata2"].round(1),
                           textposition="outside", hovertemplate="%{y}: %{x:.1f} µg/m³<extra></extra>"))
    fig.update_layout(title="Rata-rata PM2.5 (µg/m³)", xaxis_range=[0, stt["rata2"].max() * 1.15], **LAYOUT)
    l.plotly_chart(fig, width="stretch")
    fig = go.Figure(go.Bar(y=stt.index, x=stt["over"], orientation="h", marker_color=cols, text=stt["over"].round(1).astype(str) + "%",
                           textposition="outside", hovertemplate="%{y}: %{x:.1f}% hari<extra></extra>"))
    fig.update_layout(title=f"% hari PM2.5 > {THRESH} µg/m³", xaxis_range=[0, stt["over"].max() * 1.2],
                      yaxis_showticklabels=False, **LAYOUT)
    r.plotly_chart(fig, width="stretch")
    st.info("Oranye = tertinggi, biru tua = terendah dalam filter yang dipilih.")

# ---------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Bagaimana angin memengaruhi PM2.5?")
    w = df.dropna(subset=["PM25", "WSPM"]).copy()
    w["kelas"] = pd.cut(w["WSPM"], [0, 1, 2, 3, np.inf], right=False, labels=["< 1 m/s", "1–2 m/s", "2–3 m/s", "> 3 m/s"])
    wt = w.groupby("kelas", observed=True)["PM25"].agg(rata2="mean", over=lambda s: (s > THRESH).mean() * 100, n="size")
    l, r = st.columns([1, 1.5])
    fig = go.Figure(go.Bar(x=wt.index.astype(str), y=wt["rata2"], marker_color=["#C3D5E8", "#8FB0D2", "#5B88B8", "#2F5D8A"][: len(wt)],
                           text=wt["rata2"].round(0), textposition="outside", customdata=np.c_[wt["over"], wt["n"]],
                           hovertemplate="%{x}: %{y:.1f} µg/m³<br>%{customdata[0]:.1f}% hari > 75<br>n=%{customdata[1]:,} hari<extra></extra>"))
    fig.add_hline(y=THRESH, line_dash="dash", line_color=GRAY)
    fig.update_layout(title="PM2.5 menurut kecepatan angin", xaxis_title="Kecepatan angin", yaxis_title="PM2.5 (µg/m³)", **LAYOUT)
    l.plotly_chart(fig, width="stretch")

    d = df.dropna(subset=["PM25", "wd"])
    heavy = d[d["PM25"] > 150]
    allsh = d["wd"].value_counts(normalize=True).reindex(DIR16).fillna(0) * 100
    heavysh = heavy["wd"].value_counts(normalize=True).reindex(DIR16).fillna(0) * 100
    fig = go.Figure()
    fig.add_bar(x=DIR16, y=allsh, name="Semua hari", marker_color=LIGHT, hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
    fig.add_bar(x=DIR16, y=heavysh, name="Hari PM2.5 > 150", marker_color=ACCENT, hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
    fig.update_layout(title="Arah angin dominan: semua hari vs hari polusi berat", barmode="group",
                      yaxis_title="Porsi hari (%)", legend=dict(orientation="h", y=1.1, x=0), **LAYOUT)
    r.plotly_chart(fig, width="stretch")
    if len(wt) >= 2:
        lo, hi = wt["rata2"].iloc[0], wt["rata2"].iloc[-1]
        st.info(f"Angin paling lemah memiliki rata-rata {lo:.0f} µg/m³ vs {hi:.0f} µg/m³ pada angin paling kencang "
                f"(selisih {lo - hi:.0f} µg/m³). Hari polusi berat didominasi angin dari sektor timur–timur laut.")

# ---------------------------------------------------------------- tab 4
with tab4:
    st.subheader("Seberapa sering udara berada pada level berbahaya?")
    full = df[df["year"].between(2014, 2016)]
    if not full.empty:
        ct = pd.crosstab(full["year"], full["kategori"], normalize="index").reindex(columns=AQI_LABELS).fillna(0) * 100
        fig = go.Figure()
        for lab, c in zip(AQI_LABELS, RAMP6):
            fig.add_bar(y=ct.index.astype(str), x=ct[lab], name=lab, orientation="h", marker=dict(color=c, line=dict(color="white", width=1.5)),
                        hovertemplate="%{y}: %{x:.1f}%<extra>" + lab + "</extra>")
        fig.update_layout(barmode="stack", title="Komposisi kategori per tahun (tahun penuh 2014–2016)",
                          xaxis=dict(title="% hari", range=[0, 100]), yaxis=dict(autorange="reversed"),
                          legend=dict(orientation="h", y=-0.25, x=0), **LAYOUT)
        st.plotly_chart(fig, width="stretch")
    else:
        st.caption("Pilih rentang yang mencakup tahun 2014–2016 untuk melihat komposisi tahunan.")

    g = df.groupby("station")["PM25"].mean().reset_index(name="rata2")
    g["lat"] = g["station"].map(lambda s: COORD[s][0])
    g["lon"] = g["station"].map(lambda s: COORD[s][1])
    fig = px.scatter_map(g, lat="lat", lon="lon", size="rata2", color="rata2", hover_name="station",
                         hover_data={"rata2": ":.1f", "lat": False, "lon": False}, size_max=26, zoom=8.6,
                         color_continuous_scale="Blues", range_color=(50, 90), map_style="open-street-map",
                         title="Rata-rata PM2.5 per stasiun (lokasi perkiraan)")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=520, coloraxis_colorbar=dict(title="µg/m³"))
    st.plotly_chart(fig, width="stretch")
    st.caption("Koordinat stasiun adalah perkiraan lokasi distrik (dataset tidak menyertakan koordinat).")

st.caption("Sumber data: Beijing Multi-Site Air-Quality Data (PRSA). Dashboard dibuat sebagai bagian submission analisis data.")
