import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Pruebas inferenciales
from scipy.stats import ttest_ind, f_oneway
import statsmodels.stats.multicomp as mc

# Ajustes globales de estilo para fuentes y legibilidad
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

API = "http://127.0.0.1:8000"

# Umbrales críticos
U_LPG      = 800.0    # ppm
U_CO       = 50.0     # ppm
U_SMOKE    = 300.0    # ppm
U_PM25     = 35.0     # µg/m³
U_LATENCY  = 200      # ms

def fetch_all(sensor: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{API}/{sensor}/all")
        r.raise_for_status()
        data = r.json()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except:
        return pd.DataFrame()

def filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    if df.empty or 'timestamp' not in df:
        return df
    df['ts'] = pd.to_datetime(df['timestamp'])
    today = datetime.today().date()
    if period == 'today':
        mask = df['ts'].dt.date == today
    elif period == 'last7':
        mask = df['ts'].dt.date.between(today - timedelta(days=6), today)
    elif period == 'month':
        mask = df['ts'].dt.date.between(today.replace(day=1), today)
    elif period == 'lastmonth':
        end_prev = today.replace(day=1) - timedelta(days=1)
        start_prev = end_prev.replace(day=1)
        mask = df['ts'].dt.date.between(start_prev, end_prev)
    else:
        mask = df['ts'].dt.date == today
    return df.loc[mask]

def basic_stats(vals):
    return {
        'mean': np.mean(vals),
        'std':  np.std(vals, ddof=1) if len(vals)>1 else 0,
        'var':  np.var(vals, ddof=1) if len(vals)>1 else 0,
        'min':  np.min(vals),
        'max':  np.max(vals),
        'p25':  np.percentile(vals,25),
        'p50':  np.percentile(vals,50),
        'p75':  np.percentile(vals,75),
        'count': len(vals)
    }

def risk_prob(vals, U):
    return sum(v>U for v in vals)/len(vals) if vals else 0

def plot_hist_donut(vals, U, xlabel, title_hist, title_donut):
    safe = [v for v in vals if v <= U]
    crit = [v for v in vals if v > U]
    fig, (axh, axd) = plt.subplots(1,2,figsize=(14,5))

    # Histograma con unidad anotada
    axh.hist(safe, bins=12, color='#2ca02c', edgecolor='k', alpha=0.8, label='Seguro (≤ U)')
    axh.hist(crit, bins=12, color='#d62728', edgecolor='k', alpha=0.8, label='Crítico (> U)')
    axh.axvline(U, color='r', linestyle='--', linewidth=2, label=f"Umbral = {U} {xlabel}")
    axh.set_xlabel(f"Valor ({xlabel})")
    axh.set_ylabel("Frecuencia")
    axh.set_title(title_hist)
    axh.legend(title="Estado")
    axh.text(0.98, 0.95, f"Unidad: {xlabel}", transform=axh.transAxes,
             fontsize=11, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Gráfico donut
    wedges, texts, autotexts = axd.pie(
        [len(safe), len(crit)],
        labels=["Seguro","Crítico"],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=dict(width=0.5, edgecolor='w'),
        colors=['#98df8a','#ff9896']
    )
    axd.set_title(title_donut)
    axd.legend(wedges, ["Seguro","Crítico"], title="Estado",
               loc="center left", bbox_to_anchor=(1,0.5))
    axd.text(0.5, -0.15, f"Medida en {xlabel}", ha='center', va='top', transform=axd.transAxes)

    plt.tight_layout()
    plt.show()

def plot_timebar(df, field, period, unit, title):
    if df.empty: return
    df2 = df.copy()
    if period == 'today':
        df2['sub'] = df2['ts'].dt.hour
        xlabel = "Hora"
    else:
        df2['sub'] = df2['ts'].dt.date
        xlabel = "Fecha"

    grp = df2.groupby('sub')[field].mean()
    plt.figure(figsize=(10,4))
    bars = plt.bar(grp.index, grp.values, color='#1f77b4', edgecolor='k', alpha=0.8)
    plt.xlabel(xlabel)
    plt.ylabel(f"{field} ({unit})")
    plt.title(title)

    # Anotaciones con unidad
    for i, v in enumerate(grp.values):
        plt.text(grp.index[i], v + max(grp.values)*0.02,
                 f"{v:.1f} {unit}", ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.show()

def t_test(group1, group2, label1, label2):
    if len(group1)>1 and len(group2)>1:
        t, p = ttest_ind(group1, group2, equal_var=False)
        sig = "Significativo" if p<0.05 else "No significativo"
        print(f"t-test {label1} vs {label2}: t={t:.2f}, p={p:.3f} → {sig}")
    else:
        print(f"No suficientes datos para t-test entre {label1} y {label2}.")

def anova_tukey(data_dict, field):
    groups = [v for v in data_dict.values() if len(v)>1]
    if len(groups)>=3:
        F, p = f_oneway(*groups)
        sig = "Diferencias" if p<0.05 else "Sin diferencias"
        print(f"ANOVA {field}: F={F:.2f}, p={p:.3f} → {sig}")
        df = pd.concat([pd.DataFrame({field:v,'grupo':k}) for k,v in data_dict.items() if len(v)>1])
        tuk = mc.pairwise_tukeyhsd(df[field], df['grupo'], alpha=0.05)
        print(tuk.summary())
    else:
        print(f"No hay suficientes grupos para ANOVA en {field}.")

def main():
    period = sys.argv[1] if len(sys.argv)>1 else "today"
    print(f"=== Reporte periodo: {period} ===")

    # --- 1) Estadísticas + gráficos por sensor ---
    # Gas
    dg = filter_by_period(fetch_all("gas"), period)
    for fld, U, unit, title_lbl in [
        ("lpg", U_LPG, "ppm", "LPG"),
        ("co", U_CO, "ppm", "CO"),
        ("smoke", U_SMOKE, "ppm", "Smoke")
    ]:
        if fld in dg and not dg.empty:
            vals = dg[fld].tolist()
            st = basic_stats(vals)
            print(f"\nGas {title_lbl}: Media={st['mean']:.2f}, Var={st['var']:.2f}, Std={st['std']:.2f}, N={st['count']}")
            print(f" Min={st['min']:.2f}, Max={st['max']:.2f}, P25={st['p25']:.2f}, Med={st['p50']:.2f}, P75={st['p75']:.2f}")
            print(f" P({fld}>U) = {risk_prob(vals,U):.2%}")
            plot_hist_donut(
                vals, U, unit,
                f"Hist Gas {title_lbl} ({period})",
                f"Donut Gas {title_lbl} ({period})"
            )
            plot_timebar(
                dg, fld, period, unit,
                f"Gas {title_lbl} vs tiempo ({period})"
            )

    # Partículas PM2.5
    dp = filter_by_period(fetch_all("particle"), period)
    if 'pm2_5' in dp and not dp.empty:
        vals = dp['pm2_5'].tolist()
        st = basic_stats(vals)
        print(f"\nPM2.5: Media={st['mean']:.2f}, Var={st['var']:.2f}, Std={st['std']:.2f}, N={st['count']}")
        print(f" Min={st['min']:.2f}, Max={st['max']:.2f}, P25={st['p25']:.2f}, Med={st['p50']:.2f}, P75={st['p75']:.2f}")
        print(f" P(pm2_5>U) = {risk_prob(vals,U_PM25):.2%}")
        plot_hist_donut(
            vals, U_PM25, "µg/m³",
            f"Hist PM2.5 ({period})",
            f"Donut PM2.5 ({period})"
        )
        plot_timebar(
            dp, 'pm2_5', period, "µg/m³",
            f"PM2.5 vs tiempo ({period})"
        )

    # Movimiento
    dm = filter_by_period(fetch_all("motion"), period)
    if 'motion_detected' in dm and not dm.empty:
        dm['val'] = dm['motion_detected'].astype(int)
        rp = dm['val'].mean()
        print(f"\nMovimiento: P(detect)={rp:.2%}, N={len(dm)}")

        # Preparamos los últimos 10 timestamps de detección
        eventos = (
            dm.loc[dm['motion_detected'], 'ts']
              .sort_values()
              .tail(10)
              .dt.strftime('%Y-%m-%d %H:%M')
              .tolist()
        )

        # Dibujamos el pie chart y la tabla lateral
        fig, axes = plt.subplots(1, 2, figsize=(12, 6), dpi=100)
        fig.subplots_adjust(wspace=0.4)

        # 1) Pie chart
        wedges, _, _ = axes[0].pie(
            [1 - rp, rp],
            labels=["No mov", "Mov"],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor='k'),
            # Nota: no especificamos colores según instrucciones generales
        )
        axes[0].set_title(f"Movimiento ({period})", pad=20)
        axes[0].legend(
            wedges,
            ["No mov", "Mov"],
            title="Detección",
            loc="center left",
            bbox_to_anchor=(1, 0.5)
        )

        # 2) Tabla o mensaje con los últimos 10 registros
        axes[1].axis('off')
        axes[1].set_title("Últimos 10 movimientos", pad=20)

        if eventos:
            cell_text = [[ts] for ts in eventos]
            table = axes[1].table(
                cellText=cell_text,
                colLabels=["Timestamp"],
                cellLoc='center',
                loc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
        else:
            axes[1].text(
                0.5, 0.5,
                "No hay eventos de movimiento\nen el periodo seleccionado",
                ha='center', va='center',
                fontsize=12,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8)
            )

        plt.tight_layout()
        plt.show()


    # Cámara
    dc = filter_by_period(fetch_all("camera"), period)
    if 'latency_ms' in dc and not dc.empty:
        vals = dc['latency_ms'].tolist()
        st = basic_stats(vals)
        print(f"\nLatencia Cámara: Media={st['mean']:.2f}, Var={st['var']:.2f}, Std={st['std']:.2f}, N={st['count']}")
        print(f" Min={st['min']:.2f}, Max={st['max']:.2f}, P25={st['p25']:.2f}, Med={st['p50']:.2f}, P75={st['p75']:.2f}")
        print(f" P(lat>U) = {risk_prob(vals,U_LATENCY):.2%}")
        plot_hist_donut(
            vals, U_LATENCY, "ms",
            f"Hist Latencia ({period})",
            f"Donut Latencia ({period})"
        )
        plot_timebar(
            dc, 'latency_ms', period, "ms",
            f"Latencia vs tiempo ({period})"
        )

    # --- 2) Pruebas inferenciales ---
    print("\n=== PRUEBAS INFERENCIALES ===")
    g_today = filter_by_period(fetch_all("gas"), 'today')['lpg'].tolist()
    g_7     = filter_by_period(fetch_all("gas"), 'last7')['lpg'].tolist()
    t_test(g_today, g_7, "LPG hoy", "LPG últimos 7d")

    p_m    = filter_by_period(fetch_all("particle"), 'month')['pm2_5'].tolist()
    p_lm   = filter_by_period(fetch_all("particle"), 'lastmonth')['pm2_5'].tolist()
    t_test(p_m, p_lm, "PM2.5 mes actual", "PM2.5 mes anterior")

    c_periods = {
        'Hoy':  filter_by_period(fetch_all("camera"), 'today')['latency_ms'].tolist(),
        '7d':   filter_by_period(fetch_all("camera"), 'last7')['latency_ms'].tolist(),
        'Mes':  filter_by_period(fetch_all("camera"), 'month')['latency_ms'].tolist(),
    }
    anova_tukey(c_periods, 'latency_ms')

    # --- 3) Gráficas de inferencia ---
    print("\n=== GRÁFICAS DE INFERENCIA ===")
    if g_today and g_7:
        df1 = pd.DataFrame({'lpg':g_today,'periodo':'Hoy'})
        df2 = pd.DataFrame({'lpg':g_7,'periodo':'Últimos 7 días'})
        df_c = pd.concat([df1,df2])
        fig, ax = plt.subplots(figsize=(8,5))
        bp = df_c.boxplot(column='lpg', by='periodo', ax=ax, patch_artist=True, grid=True)
        for patch, color in zip(ax.artists, ['#1f77b4','#2ca02c']):
            patch.set_facecolor(color)
        plt.suptitle("")
        ax.set_title("LPG: Hoy vs Últimos 7 días")
        ax.set_ylabel("ppm")
        plt.tight_layout()
        plt.show()

    if p_m and p_lm:
        means = [np.mean(p_m), np.mean(p_lm)]
        errs  = [
            np.std(p_m, ddof=1)/np.sqrt(len(p_m)),
            np.std(p_lm, ddof=1)/np.sqrt(len(p_lm))
        ]
        labels = ['Mes actual','Mes anterior']
        x = np.arange(len(labels))
        plt.figure(figsize=(8,5))
        plt.bar(x, means, yerr=errs, capsize=6, edgecolor='k', alpha=0.8)
        plt.xticks(x, labels)
        plt.ylabel("PM2.5 (µg/m³)")
        plt.title("Comparativa PM2.5 con error estándar")
        for xi, m, e in zip(x, means, errs):
            plt.text(xi, m + e + max(errs)*0.02, f"{m:.1f} µg/m³", ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
