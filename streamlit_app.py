from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- memastikan folder src/ ada di Python path ---
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from foreca_dashboard.data import (  
    DataPaths,
    compute_monthly,
    date_min_max,
    ensure_continuous_daily_series,
    filter_date_range,
    load_sales_daily,
    load_sales_daily_by_product,
)
from foreca_dashboard.charts import (  
    style,
    fig_daily_trend,
    fig_month_weekday_heatmap,
    fig_monthly_trend,
    fig_pareto_curve,
    fig_top10_products_barh,
    fig_weekday_boxplot,
)


st.set_page_config(page_title="Foreca Dashboard", layout="wide")
style()

paths = DataPaths(root=ROOT)
ORDER_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@st.cache_data
def load_all():
    daily = load_sales_daily(paths.sales_daily)
    by_prod = load_sales_daily_by_product(paths.sales_daily_by_product)
    return daily, by_prod


def format_idr(x: float) -> str:
    try:
        return "Rp" + f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return str(x)


daily_full, daily_by_product = load_all()

st.title("Foreca — Dashboard Analisis Penjualan UMKM")
st.caption("Capstone ID: CC26-PSU041")
st.info(
    "Catatan interpretasi: pada data ini, hari tanpa transaksi dianggap bernilai 0 (gap=0). "
    "Jika dianggap sebagai data hilang, pipeline preprocessing perlu diubah.",
)

# --- Sidebar filters ---
st.sidebar.header("Filter")
min_dt, max_dt = date_min_max(daily_full)
min_d = min_dt.date()
max_d = max_dt.date()

date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_d, max_d

produk_list = sorted(daily_by_product["Jenis Produk"].dropna().unique().tolist())
produk = st.sidebar.selectbox("Produk", options=["All"] + produk_list, index=0)

# --- Apply filters ---
if produk == "All":
    df_daily = filter_date_range(daily_full, start_date, end_date)
else:
    dfp = daily_by_product[daily_by_product["Jenis Produk"] == produk].copy()
    dfp = filter_date_range(dfp, start_date, end_date)
    df_daily = ensure_continuous_daily_series(dfp, start=start_date, end=end_date)

# --- Header metrics ---
total_rev = float(df_daily["Total"].sum())
hari_total = int(len(pd.date_range(pd.to_datetime(start_date), pd.to_datetime(end_date), freq="D")))
hari_zero = int((df_daily["Total"] == 0).sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total revenue", format_idr(total_rev))
col2.metric("Total hari", f"{hari_total}")
col3.metric("Hari tanpa transaksi", f"{hari_zero} ({(hari_zero / max(hari_total, 1)):.1%})")
if produk == "All":
    col4.metric("Produk unik (global)", f"{daily_by_product['Jenis Produk'].nunique()}")
else:
    col4.metric("Produk dipilih", produk)

if produk == "All":
    # KPI tambahan dari Pareto
    prod_rev = (
        filter_date_range(daily_by_product, start_date, end_date)
        .groupby("Jenis Produk")["Total"]
        .sum()
        .sort_values(ascending=False)
    )
    prod_rev_all = prod_rev.reset_index()
    prod_rev_all.columns = ["Jenis Produk", "Total"]
    prod_rev_all["share"] = prod_rev_all["Total"] / prod_rev_all["Total"].sum()
    prod_rev_all["cum_share"] = prod_rev_all["share"].cumsum()
    n80 = int((prod_rev_all["cum_share"] <= 0.8).sum()) + 1
    st.caption(f"≈80% revenue ditutup oleh sekitar {n80} produk (periode terfilter).")

st.divider()

# --- Trend charts ---
left, right = st.columns(2)
if produk == "All":
    monthly = compute_monthly(df_daily)
else:
    tmp = df_daily.copy()
    tmp["Bulan"] = tmp["Tanggal"].dt.to_period("M").astype(str)
    monthly = tmp.groupby("Bulan", as_index=False)["Total"].sum()
    monthly["Bulan_dt"] = pd.to_datetime(monthly["Bulan"] + "-01")
    monthly = monthly.sort_values("Bulan_dt")

with left:
    st.subheader("Tren bulanan")
    st.pyplot(fig_monthly_trend(monthly), clear_figure=True)

with right:
    st.subheader("Tren harian")
    st.pyplot(fig_daily_trend(df_daily), clear_figure=True)

# --- Product section (only All) ---
if produk == "All":
    st.divider()
    st.subheader("Produk (kontribusi revenue)")

    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(fig_top10_products_barh(prod_rev), clear_figure=True)
    with c2:
        st.pyplot(fig_pareto_curve(prod_rev_all), clear_figure=True)

# --- Time pattern ---
st.divider()
st.subheader("Pola waktu (deskriptif)")
left, right = st.columns(2)
with left:
    st.pyplot(fig_weekday_boxplot(df_daily, ORDER_DAYS), clear_figure=True)
with right:
    if produk == "All":
        st.pyplot(fig_month_weekday_heatmap(df_daily, ORDER_DAYS), clear_figure=True)
        st.caption("Pola weekday tidak selalu konsisten antar bulan; sebagian lonjakan bisa dipengaruhi order besar (event).")
    else:
        st.caption("Heatmap bulan×weekday hanya ditampilkan untuk mode All agar lebih stabil secara agregasi.")

# --- Spike table ---
st.divider()
st.subheader("Hari dengan revenue tertinggi")
top_days = df_daily.sort_values("Total", ascending=False).head(10)[["Tanggal", "Total"]].copy()
top_days["Tanggal"] = pd.to_datetime(top_days["Tanggal"]).dt.date
top_days["Total"] = top_days["Total"].map(format_idr)
st.dataframe(top_days, width="stretch")

if produk == "All":
    st.subheader("Drill-down produk pada 3 hari teratas")
    peak_days = pd.to_datetime(df_daily.sort_values("Total", ascending=False).head(3)["Tanggal"]).tolist()
    drill = (
        daily_by_product[daily_by_product["Tanggal"].isin(peak_days)]
        .groupby(["Tanggal", "Jenis Produk"], as_index=False)["Total"]
        .sum()
        .sort_values(["Tanggal", "Total"], ascending=[True, False])
    )
    drill["Tanggal"] = drill["Tanggal"].dt.date
    drill["Total"] = drill["Total"].map(format_idr)
    st.dataframe(drill.head(30), width="stretch")
