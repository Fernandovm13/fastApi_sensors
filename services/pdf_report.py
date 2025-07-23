import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.title = ""

    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, self.title, ln=True, align="C")
        self.ln(5)

    def add_image_bytes(self, img_buf: io.BytesIO, w: float = 180):
        tmp = tempfile.gettempdir()
        path = os.path.join(tmp, f"{datetime.now().timestamp()}.png")
        with open(path, "wb") as f:
            f.write(img_buf.getbuffer())
        self.image(path, w=w)
        self.ln(5)

def generate_donut_plot(safe_count: int, crit_count: int, field_label: str):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.pie(
        [safe_count, crit_count],
        labels=['Seguro', 'Crítico'],
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(width=0.5)
    )
    ax.set_title(f"{field_label} (%)", fontsize=12)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='PNG', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_line_plot(timestamps, values, field_label: str):
    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(timestamps, values, marker='o', linestyle='-', alpha=0.8)
    ax.set_title(f"Evolución {field_label}", fontsize=12)
    ax.set_xlabel("Fecha / Hora")
    ax.set_ylabel(field_label)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    fig.autofmt_xdate(rotation=45, ha='right')
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='PNG', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def sample_points(points: list[dict], count: int) -> list[dict]:
    """
    Toma 'count' puntos equiespaciados de la lista 'points',
    incluyendo siempre el primer y el último punto.
    Si hay menos de 'count', devuelve todos.
    """
    n = len(points)
    if n <= count or count <= 1:
        return points
    step = (n - 1) / (count - 1)
    indices = [int(round(i * step)) for i in range(count)]
    indices = sorted(set(indices))
    return [points[i] for i in indices]

def build_pdf_report(sensor_name, label, stats, risk, graphs):
    label_clean = label.replace('–', '-')

    pdf = PDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.title = f"Reporte {sensor_name} - {label_clean}"
    pdf.add_page()

    # 1) Cabecera con fecha de generación
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(3)

    # 2) Estadísticas y riesgo
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1) Estadísticas y riesgo", ln=True)
    pdf.set_font("Arial", "", 11)
    for fld, v in stats.items():
        if fld == 'count':
            pdf.cell(0, 6, f"Total registros: {v}", ln=True)
        else:
            rl = f"{risk.get(fld, 0)*100:.1f}%"
            pdf.cell(
                0, 6,
                f"{fld}: media={v['mean']:.2f}, min={v['min']:.2f}, max={v['max']:.2f}, riesgo={rl}",
                ln=True
            )
    pdf.ln(3)

    # 2) Gráficas individuales
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2) Gráficas", ln=True)
    pdf.set_font("Arial", "", 11)
    for key, buf in graphs.items():
        if key == 'donut_joint':
            continue
        w = 90 if key.startswith("donut_") else 180
        pdf.add_image_bytes(buf, w=w)
    pdf.ln(3)

    # 3) Probabilidad conjunta (si existe)
    if 'P(lpg>800 & pm2.5>35)' in risk:
        joint_pct = risk['P(lpg>800 & pm2.5>35)'] * 100
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "3) Probabilidad conjunta", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"LPG>800 & PM2.5>35: {joint_pct:.1f}%", ln=True)
        pdf.ln(3)
        # gráfico donut de probabilidad conjunta
        pdf.add_image_bytes(graphs.get('donut_joint'), w=90)
        pdf.ln(3)

 
    out = io.BytesIO()
    out.write(pdf.output(dest='S').encode('latin-1', 'ignore'))
    out.seek(0)
    return out


def generate_scatter_line_plot(x, y1, y2, label1, label2):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y1, marker='o', linestyle='-', label=label1)
    ax.scatter(x, y2, marker='s', s=30, label=label2)
    ax.set_xlabel("Fecha / Hora")
    ax.legend()
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf