# routes/gas.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

import pandas as pd

from services.stats_utils import compute_stats
from services.gas_service import create_gas, get_gas
from services.particle_service import get_particle  # para probabilidad conjunta
from services.report_utils import build_sensor_report
from schemas.gas import GasDataCreate, GasDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

# utilidades para PDF
default_import = None
from services.pdf_report import sample_points, generate_donut_plot, generate_line_plot, build_pdf_report

router = APIRouter(prefix="/gas", tags=["gas"])

@router.post("/", response_model=GasDataRead)
def add_gas(data: GasDataCreate, db: Session = Depends(get_db)):
    return create_gas(db, data)

@router.get("/statistics/{filter_type}")
def gas_stats(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_gas(db, start, end)
    stats = compute_stats(records, ['lpg', 'co', 'smoke'])
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def gas_full_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_gas(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos de gas para este filtro")
    report = build_sensor_report(
        records,
        ['lpg', 'co', 'smoke'],
        thresholds={'lpg': 800.0, 'co': 50.0, 'smoke': 300.0}
    )
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def gas_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    gas_recs = get_gas(db, start, end)
    if not gas_recs:
        raise HTTPException(404, "No hay datos de gas para este periodo")

    # parámetros
    fields = ['lpg', 'co', 'smoke']
    thresholds = {'lpg': 800.0, 'co': 50.0, 'smoke': 300.0}

    # estadísticas individuales
    stats = compute_stats(gas_recs, fields)
    cnt = stats.get('count', 0)
    risk = {f: (sum(float(getattr(r, f)) > U for r in gas_recs) / cnt if cnt else 0)
            for f, U in thresholds.items()}

    # preparar muestreo de gas
    sorted_gas = sorted(gas_recs, key=lambda r: r.timestamp)
    pts = [{'timestamp': r.timestamp, **{f: float(getattr(r, f)) for f in fields}} for r in sorted_gas]
    SAMPLE_COUNTS = {'today': 8, 'last7': 7, 'month': 6}
    desired = SAMPLE_COUNTS.get(filter_type.lower(), len(pts))
    sampled = sample_points(pts, desired)

    # generar gráficas individuales
    graphs = {}
    times = [p['timestamp'] for p in sampled]
    for f in fields:
        vals = [p[f] for p in sampled]
        safe = sum(v <= thresholds[f] for v in vals)
        crit = sum(v > thresholds[f] for v in vals)
        graphs[f'donut_{f}'] = generate_donut_plot(safe, crit, f.upper())
        graphs[f'line_{f}'] = generate_line_plot(times, vals, f.upper())

    # intentar probabilidad conjunta si hay datos de partículas
    part_recs = get_particle(db, start, end)
    if part_recs:
        # DataFrame de muestras de gas
        df_gas = pd.DataFrame(sampled)
        # DataFrame de todas partículas, ordenado
        df_part = pd.DataFrame([{'timestamp': r.timestamp, 'pm2_5': float(r.pm2_5)} for r in part_recs])
        df_part.sort_values('timestamp', inplace=True)
        # merge_asof para emparejar
        df_joint = pd.merge_asof(df_gas.sort_values('timestamp'), df_part,
                                  on='timestamp', tolerance=pd.Timedelta('1s'), direction='nearest')
        joint_pts = df_joint.dropna().to_dict('records')
        # calcular probabilidad conjunta
        U_lpg = thresholds['lpg']
        U_pm = 35.0
        n_joint = len(joint_pts)
        p_joint = sum((p['lpg'] > U_lpg and p['pm2_5'] > U_pm) for p in joint_pts) / n_joint if n_joint else 0
        risk['P(lpg>800 & pm2.5>35)'] = p_joint
        # gráfico donut conjunta
        safe_j = n_joint - sum((p['lpg'] > U_lpg and p['pm2_5'] > U_pm) for p in joint_pts)
        crit_j = n_joint - safe_j
        graphs['donut_joint'] = generate_donut_plot(safe_j, crit_j, 'LPG & PM2.5')

    # construir y devolver PDF
    pdf_bytes = build_pdf_report('Gas', label, stats, risk, graphs)
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=gas_report_{filter_type}.pdf"}
    )
