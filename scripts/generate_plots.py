import sys
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.time_utils import get_period_bounds_and_label

API = "http://127.0.0.1:8000"

# Mapa de nombres en español para campos y títulos
FIELD_LABELS = {
    'lpg': 'LPG',
    'co': 'CO',
    'smoke': 'Gas',
    'pm1_0': 'PM1.0',
    'pm2_5': 'PM2.5',
    'pm10': 'PM10',
    'intensity': 'Intensidad',
    'latency_ms': 'Latencia'
}

# ----- Funciones auxiliares -----

def fetch_all(sensor: str) -> pd.DataFrame:
    r = requests.get(f"{API}/{sensor}/all")
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame(data) if data else pd.DataFrame()


def filter_by_period(df: pd.DataFrame, start, end) -> pd.DataFrame:
    if df.empty:
        return df
    df['ts'] = pd.to_datetime(df['timestamp'])
    return df.loc[df['ts'].dt.date.between(start, end)]


def basic_stats(vals: list[float]) -> dict:
    return {
        'mean': np.mean(vals) if vals else None,
        'std':  np.std(vals, ddof=1) if len(vals)>1 else 0,
        'var':  np.var(vals, ddof=1) if len(vals)>1 else 0,
        'min':  np.min(vals) if vals else None,
        'max':  np.max(vals) if vals else None,
        'count': len(vals)
    }


def risk_prob(vals: list[float], U: float) -> float:
    return sum(v > U for v in vals) / len(vals) if vals else 0


def plot_hist_donut(vals, U, unit, label_fld, periodo_label):
    safe = [v for v in vals if v <= U]
    crit = [v for v in vals if v > U]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Distribución de {label_fld} ({periodo_label})", fontsize=16)

    # Histograma
    axes[0].hist(safe, bins=12, edgecolor='k', alpha=0.7, label='Seguro (≤ umbral)')
    axes[0].hist(crit, bins=12, edgecolor='k', alpha=0.7, label='Crítico (> umbral)')
    axes[0].axvline(U, linestyle='--', linewidth=2, label=f"Umbral = {U} {unit}")
    axes[0].set_xlabel(f"Valor ({unit})")
    axes[0].set_ylabel('Frecuencia')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].legend()

    # Donut
    wedges, texts, autotexts = axes[1].pie(
        [len(safe), len(crit)],
        labels=['Seguro', 'Crítico'],
        autopct='%1.1f%%', startangle=90,
        wedgeprops={'width': 0.5, 'edgecolor': 'w'}
    )
    axes[1].set_title(f"Proporción de {label_fld}")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def plot_timebar(df, field, start, end, periodo_label, unit):
    single_day = (start == end)
    df2 = df.copy()
    if single_day:
        df2['sub'] = df2['ts'].dt.hour
        xlabel = "Hora del día"
    else:
        df2['sub'] = df2['ts'].dt.date
        xlabel = "Fecha"

    grp = df2.groupby('sub')[field].mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(grp.index, grp.values, edgecolor='k', alpha=0.8)
    ax.set_title(f"Evolución de {FIELD_LABELS[field]} ({periodo_label})", fontsize=14)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"{FIELD_LABELS[field]} ({unit})")
    ax.grid(True, linestyle='--', alpha=0.5)

    if not single_day:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        fig.autofmt_xdate(rotation=45, ha='right')

    for x, v in zip(grp.index, grp.values):
        ax.text(x, v + max(grp.values)*0.02,
                f"{v:.1f} {unit}", ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.show()


def plot_anova_points(data_dict, field, periodo_labels):
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, periodo in enumerate(periodo_labels, start=1):
        vals = data_dict[periodo]
        ax.scatter([i]*len(vals), vals, alpha=0.7)
    ax.set_xticks(range(1, len(periodo_labels)+1))
    ax.set_xticklabels(periodo_labels, rotation=45, ha='right')
    ax.set_title(f"Comparativa ANOVA de {FIELD_LABELS[field]}", fontsize=14)
    ax.set_ylabel(f"{FIELD_LABELS[field]}")
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


# ----- Ejecutable principal -----

def main():
    periodo = sys.argv[1] if len(sys.argv)>1 else 'today'
    start, end, periodo_label = get_period_bounds_and_label(periodo)
    print(f"=== Reporte período: {periodo_label} ===")

    sensores = {
        'gas': [('lpg', 800.0, 'ppm'), ('co', 50.0, 'ppm'), ('smoke', 300.0, 'ppm')],
        'particle': [('pm1_0', None, 'µg/m³'), ('pm2_5', 35.0, 'µg/m³'), ('pm10', None, 'µg/m³')],
        'motion': [('intensity', None, '')],
        'camera': [('latency_ms', 200, 'ms')]
    }

    for sensor, campos in sensores.items():
        df_all = fetch_all(sensor)
        df = filter_by_period(df_all, start, end)
        if df.empty: continue

        for field, U, unit in campos:
            if field not in df: continue
            vals = df[field].tolist()
            st = basic_stats(vals)
            print(f"{FIELD_LABELS[field]}: Media={st['mean']:.2f}, Mín={st['min']:.2f}, Máx={st['max']:.2f}, N={st['count']}")
            if U is not None:
                print(f"Probabilidad > umbral: {risk_prob(vals, U):.2%}")

            if U is not None:
                plot_hist_donut(vals, U, unit, FIELD_LABELS[field], periodo_label)
            plot_timebar(df, field, start, end, periodo_label, unit)

    # ANOVA para latencia de cámara
    periodos = ['today', 'last7', 'month']
    grupos_cam = {}
    labels_cam = []
    for p in periodos:
        s, e, lbl = get_period_bounds_and_label(p)
        labels_cam.append(lbl)
        df_cam = filter_by_period(fetch_all('camera'), s, e)
        grupos_cam[lbl] = df_cam['latency_ms'].dropna().tolist()

    plot_anova_points(grupos_cam, 'latency_ms', labels_cam)

if __name__ == '__main__':
    main()