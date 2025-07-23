# routes/correlation.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import math
import io

from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label
from services.motion_service import get_motion
from services.camera_service import get_camera
from services.pdf_report import PDF, generate_line_plot, generate_scatter_line_plot

router = APIRouter(prefix="/correlation", tags=["correlation"])


@router.get("/{filter_type}")
def motion_camera_correlation(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)

    mot = get_motion(db, start, end)
    cam = get_camera(db, start, end)
    if not mot or not cam:
        raise HTTPException(404, "No hay datos suficientes para correlación")

    # Construir y mergear DataFrames
    df_m = pd.DataFrame([
        {'timestamp': r.timestamp, 'intensity': float(r.intensity)}
        for r in mot
    ]).sort_values('timestamp')
    df_c = pd.DataFrame([
        {'timestamp': r.timestamp, 'photo': 1}
        for r in cam
    ]).sort_values('timestamp')

    df = pd.merge_asof(
        df_m, df_c,
        on='timestamp',
        tolerance=pd.Timedelta('1s'),
        direction='nearest'
    ).fillna({'photo': 0})
    df['photo'] = df['photo'].astype(int)

    def clean(v):
        return None if v is None or (isinstance(v, float) and math.isnan(v)) else v

    # Calcular estadísticas 
    raw_stats = {
        'mean_intensity': df['intensity'].mean(),
        'std_intensity':  df['intensity'].std(ddof=1),
        'mean_photos':    df['photo'].mean(),
        'std_photos':     df['photo'].std(ddof=1),
    }
    stats = {k: clean(v) for k, v in raw_stats.items()}

    # Preparar puntos para la gráfica
    points = [
        {
            'timestamp': ts.isoformat(),
            'intensity': inten,
            'photo':     ph
        }
        for ts, inten, ph in zip(df['timestamp'], df['intensity'], df['photo'])
    ]

    return {
        'label':  label,
        'stats':  stats,
        'points': points
    }


@router.get("/pdf/{filter_type}")
def correlation_pdf(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)


    label_clean = label.replace("–", "-").replace("—", "-")

    mot = get_motion(db, start, end)
    cam = get_camera(db, start, end)
    if not mot or not cam:
        raise HTTPException(404, "No hay datos suficientes para PDF")

    df_m = pd.DataFrame([{'timestamp': r.timestamp, 'intensity': float(r.intensity)} for r in mot]) \
             .sort_values('timestamp')
    df_c = pd.DataFrame([{'timestamp': r.timestamp, 'photo': 1} for r in cam]) \
             .sort_values('timestamp')
    df = pd.merge_asof(
        df_m, df_c,
        on='timestamp',
        tolerance=pd.Timedelta('1s'),
        direction='nearest'
    ).fillna({'photo': 0})
    df['photo'] = df['photo'].astype(int)

    # Estadísticas
    mean_i = df['intensity'].mean()
    std_i  = df['intensity'].std(ddof=1)
    mean_p = df['photo'].mean()
    std_p  = df['photo'].std(ddof=1)

    # Gráficas
    buf_m    = generate_line_plot(df['timestamp'], df['intensity'], "Movimiento")
    buf_c    = generate_line_plot(df['timestamp'], df['photo'],     "Fotos Cámara")
    buf_corr = generate_scatter_line_plot(
        x=df['timestamp'],
        y1=df['intensity'],
        y2=df['photo'],
        label1="Intensidad",
        label2="Fotos"
    )

    # Construir PDF
    pdf = PDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.title = f"Reporte Correlación - {label_clean}"
    pdf.add_page()

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(3)

    # Periodo
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Periodo: {label_clean}", ln=True)
    pdf.ln(5)

    # Estadísticas
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Estadísticas", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Media intensidad: {mean_i:.2f}", ln=True)
    pdf.cell(0, 6, f"Desv. estándar intensidad: {std_i:.2f}", ln=True)
    pdf.cell(0, 6, f"Media fotos: {mean_p:.2f}", ln=True)
    pdf.cell(0, 6, f"Desv. estándar fotos: {std_p:.2f}", ln=True)
    pdf.ln(5)

    # Gráfica 1
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1) Movimiento", ln=True)
    pdf.add_image_bytes(buf_m)

    # Gráfica 2
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2) Cámara", ln=True)
    pdf.add_image_bytes(buf_c)

    # Gráfica 3
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3) Correlación", ln=True)
    pdf.add_image_bytes(buf_corr)

    # Salida
    out = io.BytesIO()
    out.write(pdf.output(dest='S').encode('latin-1', 'ignore'))
    out.seek(0)
    return StreamingResponse(
        out,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=correlation_{filter_type}.pdf"}
    )