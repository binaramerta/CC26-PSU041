from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import PercentFormatter


def style() -> None:
    sns.set_theme(style="whitegrid")


def fig_monthly_trend(monthly: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=monthly, x="Bulan_dt", y="Total", marker="o", linewidth=2.0, ax=ax)
    ax.set_title("Tren Pendapatan Bulanan")
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Total")
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


def fig_daily_trend(daily_full: pd.DataFrame):
    tmp = daily_full.sort_values("Tanggal").copy()
    tmp["Rolling7"] = tmp["Total"].rolling(7, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=tmp, x="Tanggal", y="Total", linewidth=1.0, label="Total harian", ax=ax)
    sns.lineplot(data=tmp, x="Tanggal", y="Rolling7", linewidth=2.2, label="Rolling mean 7 hari", ax=ax)
    ax.set_title("Tren Pendapatan Harian (Series Lengkap)")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Total")
    fig.tight_layout()
    return fig


def fig_top10_products_barh(prod_rev: pd.Series):
    top10 = prod_rev.head(10).sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    top10.plot(kind="barh", ax=ax, color="#2ca02c")
    ax.set_title("Top 10 Produk berdasarkan Total Revenue")
    ax.set_xlabel("Total Revenue")
    fig.tight_layout()
    return fig


def fig_pareto_curve(prod_rev_all: pd.DataFrame):
    x = np.arange(1, len(prod_rev_all) + 1)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(x, prod_rev_all["cum_share"], marker="o", linewidth=2)
    ax.axhline(0.8, color="red", linestyle="--", label="80%")
    ax.set_title("Pareto Revenue: Kumulatif Share per Urutan Produk")
    ax.set_xlabel("Urutan produk (descending revenue)")
    ax.set_ylabel("Kumulatif share")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    return fig


def fig_weekday_boxplot(daily_full: pd.DataFrame, order: Sequence[str]):
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.boxplot(data=daily_full, x="Hari", y="Total", order=list(order), ax=ax)
    ax.set_title("Distribusi Revenue per Weekday")
    ax.set_xlabel("Hari")
    ax.set_ylabel("Total")
    fig.tight_layout()
    return fig


def fig_month_weekday_heatmap(daily_full: pd.DataFrame, order: Sequence[str]):
    heat = daily_full.copy()
    heat["Bulan"] = heat["Tanggal"].dt.to_period("M").astype(str)

    pivot = heat.pivot_table(values="Total", index="Bulan", columns="Hari", aggfunc="mean").reindex(columns=list(order))
    # sort index chronologically if possible
    try:
        idx_dt = pd.to_datetime(pivot.index + "-01")
        pivot = pivot.iloc[np.argsort(idx_dt.values)]
    except Exception:
        pass

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(pivot, cmap="YlGnBu", ax=ax)
    ax.set_title("Rata-rata Revenue per Bulan × Weekday")
    ax.set_xlabel("Hari")
    ax.set_ylabel("Bulan")
    fig.tight_layout()
    return fig

