import sys
import requests
import pandas as pd
import statistics
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

API = "http://127.0.0.1:8000"

# Umbrales críticos por sensor
U_LPG      = 800.0    # ppm
U_CO       = 50.0     # ppm
U_SMOKE    = 300.0    # ppm
U_PM25     = 35.0     # µg/m³
U_LATENCY  = 200      # ms

def fetch_all(sensor: str) -> pd.DataFrame:
    """Descarga todo el histórico de un endpoint /<sensor>/all"""
    try:
        resp = requests.get(f"{API}/{sensor}/all")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] al obtener '{sensor}': {e}")
        return pd.DataFrame()

def filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filtra por 'today', 'last7', 'month' o 'lastmonth'."""
    if df.empty or 'timestamp' not in df:
        return df
    df['ts'] = pd.to_datetime(df['timestamp'])
    today = datetime.today().date()

    if period == 'today':
        mask = df['ts'].dt.date == today
    elif period == 'last7':
        start = today - timedelta(days=6)
        mask = df['ts'].dt.date.between(start, today)
    elif period == 'month':
        start = today.replace(day=1)
        mask = df['ts'].dt.date.between(start, today)
    elif period == 'lastmonth':
        first_current = today.replace(day=1)
        last_prev = first_current - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        mask = df['ts'].dt.date.between(first_prev, last_prev)
    else:
        mask = df['ts'].dt.date == today  # fallback
    return df.loc[mask]

def compute_basic_stats(vals: list[float]) -> dict:
    """Calcula media, std, min, max y percentiles 25/50/75."""
    return {
        'mean': statistics.mean(vals),
        'std': statistics.stdev(vals) if len(vals) > 1 else 0,
        'min': min(vals),
        'max': max(vals),
        'p25': np.percentile(vals, 25),
        'p50': np.percentile(vals, 50),
        'p75': np.percentile(vals, 75),
        'count': len(vals)
    }

def compute_risk_probability(vals: list[float], threshold: float) -> float:
    """Calcula P(valor > threshold)."""
    n = len(vals)
    if n == 0:
        return 0.0
    count = sum(1 for v in vals if v > threshold)
    return count / n

def print_stats(name: str, stats: dict):
    """Imprime las estadísticas de forma ordenada."""
    print(f"\n{name}:")
    print(f"  Media = {stats['mean']:.2f}")
    print(f"  Std   = {stats['std']:.2f}")
    print(f"  Min   = {stats['min']:.2f}")
    print(f"  Max   = {stats['max']:.2f}")
    print(f"  P25   = {stats['p25']:.2f}")
    print(f"  P50   = {stats['p50']:.2f}")
    print(f"  P75   = {stats['p75']:.2f}")

def print_probability(name: str, prob: float):
    """Imprime la probabilidad de riesgo."""
    print(f"  P(riesgo {name}) = {prob:.2%}")

def plot_hist_and_pie(vals: list[float], threshold: float, color: str,
                     xlabel: str, title_hist: str, title_pie: str):
    """Dibuja histograma con umbral y pie chart de seguro vs crítico."""
    n = len(vals)
    risk_n = sum(v>threshold for v in vals)
    safe_n = n - risk_n

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,3))
    # Histograma
    ax1.hist(vals, bins=10, color=color, edgecolor='k', alpha=0.7)
    ax1.axvline(threshold, color='red', linestyle='--', label=f"Umbral {threshold}")
    ax1.set_title(title_hist)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel("Frecuencia")
    ax1.legend()

    # Pie chart
    ax2.pie([safe_n, risk_n],
            labels=["Seguro","Crítico"],
            autopct="%1.1f%%",
            colors=["lightgreen","salmon"])
    ax2.set_title(title_pie)

    plt.tight_layout()
    plt.show()

def main():
    period = sys.argv[1] if len(sys.argv)>1 else "today"
    print(f"=== Reporte periodo: {period} ===")

    # 1) Gas: LPG, CO, Smoke
    df_g = fetch_all("gas"); df_g = filter_by_period(df_g, period)
    for field, U, color, label, xlabel in [
        ('lpg',   U_LPG,   'skyblue', "Gas - LPG",   "LPG (ppm)"),
        ('co',    U_CO,    'orange',  "Gas - CO",    "CO (ppm)"),
        ('smoke', U_SMOKE, 'gray',    "Gas - Smoke", "Smoke (ppm)"),
    ]:
        if field in df_g and not df_g.empty:
            vals = df_g[field].tolist()
            stats = compute_basic_stats(vals)
            print_stats(label, stats)
            prob = compute_risk_probability(vals, U)
            print_probability(label, prob)
            plot_hist_and_pie(vals, U, color, xlabel,
                              f"Histograma {label} ({period})",
                              f"P(riesgo) {label} ({period})")

    # 2) Partículas: PM2.5
    df_p = fetch_all("particle"); df_p = filter_by_period(df_p, period)
    if 'pm2_5' in df_p and not df_p.empty:
        vals = df_p['pm2_5'].tolist()
        stats = compute_basic_stats(vals)
        print_stats("PM2.5", stats)
        prob = compute_risk_probability(vals, U_PM25)
        print_probability("PM2.5", prob)
        plot_hist_and_pie(vals, U_PM25, 'lightcoral', "PM2.5 (µg/m³)",
                          f"Histograma PM2.5 ({period})",
                          f"P(riesgo) PM2.5 ({period})")

    # 3) Movimiento
    df_m = fetch_all("motion"); df_m = filter_by_period(df_m, period)
    if 'motion_detected' in df_m and not df_m.empty:
        vals = df_m['motion_detected'].astype(int).tolist()
        prob = compute_risk_probability(vals, 0.5)  # P(movimiento=true)
        print(f"\nMovimiento: P(movimiento)= {prob:.2%}")
        plt.figure(figsize=(4,3))
        plt.pie([1-prob, prob],
                labels=["No mov","Mov"],
                autopct="%1.1f%%",
                colors=["lightgray","steelblue"])
        plt.title(f"Detección Movimiento ({period})")
        plt.show()

    # 4) Cámara: Latencia
    df_c = fetch_all("camera"); df_c = filter_by_period(df_c, period)
    if 'latency_ms' in df_c and not df_c.empty:
        vals = df_c['latency_ms'].tolist()
        stats = compute_basic_stats(vals)
        print_stats("Latencia Cámara", stats)
        prob = compute_risk_probability(vals, U_LATENCY)
        print_probability("Latencia Cámara", prob)
        plot_hist_and_pie(vals, U_LATENCY, 'lightgreen', "ms",
                          f"Histograma Latencia ({period})",
                          f"P(latencia alta) ({period})")

if __name__ == "__main__":
    main()
