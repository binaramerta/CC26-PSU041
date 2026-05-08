from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class DataPaths:
    root: Path

    @property
    def sales_daily(self) -> Path:
        return self.root / "sales_daily.csv"

    @property
    def sales_daily_by_product(self) -> Path:
        return self.root / "sales_daily_by_product.csv"

    @property
    def sales_daily_features(self) -> Path:
        return self.root / "sales_daily_features.csv"

    @property
    def transaksi_clean(self) -> Path:
        return self.root / "transaksi_clean.csv"


def _parse_date(df: pd.DataFrame, col: str = "Tanggal") -> pd.DataFrame:
    out = df.copy()
    out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def load_sales_daily(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _parse_date(df, "Tanggal")
    return df


def load_sales_daily_by_product(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _parse_date(df, "Tanggal")
    return df


def load_sales_daily_features(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _parse_date(df, "Tanggal")
    return df


def load_transaksi_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Tanggal" in df.columns:
        df = _parse_date(df, "Tanggal")
    return df


def filter_date_range(
    df: pd.DataFrame, start: Optional[object], end: Optional[object], date_col: str = "Tanggal"
) -> pd.DataFrame:
    if start is None or end is None:
        return df.copy()

    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    mask = (df[date_col] >= start_dt) & (df[date_col] <= end_dt)
    return df.loc[mask].copy()


def compute_monthly(df_daily: pd.DataFrame) -> pd.DataFrame:
    out = df_daily.copy()
    out["Bulan"] = out["Tanggal"].dt.to_period("M").astype(str)
    m = out.groupby("Bulan", as_index=False)["Total"].sum()
    m["Bulan_dt"] = pd.to_datetime(m["Bulan"] + "-01")
    m = m.sort_values("Bulan_dt")
    return m


def ensure_continuous_daily_series(
    df: pd.DataFrame,
    start: object,
    end: object,
    date_col: str = "Tanggal",
    value_col: str = "Total",
) -> pd.DataFrame:
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)

    full_days = pd.DataFrame({date_col: pd.date_range(start_dt, end_dt, freq="D")})
    agg = df.groupby(date_col, as_index=False)[value_col].sum().sort_values(date_col)
    out = full_days.merge(agg, on=date_col, how="left").fillna({value_col: 0})
    out["Hari"] = out[date_col].dt.day_name()
    return out


def date_min_max(df: pd.DataFrame, date_col: str = "Tanggal") -> Tuple[pd.Timestamp, pd.Timestamp]:
    return (pd.to_datetime(df[date_col].min()), pd.to_datetime(df[date_col].max()))

