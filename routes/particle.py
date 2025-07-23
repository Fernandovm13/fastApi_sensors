import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from services.stats_utils import compute_stats
from services.particle_service import create_particle, get_particle
from services.pdf_report import (
    sample_points,
    generate_donut_plot,
    generate_line_plot,
    build_pdf_report
)
from schemas.particle import ParticleDataCreate, ParticleDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/particle", tags=["particle"])

# Umbrales para riesgo
THRESHOLDS = {'pm1_0': None, 'pm2_5': 35.0, 'pm10': 50.0}
JOINT_PAIRS = [('pm1_0','pm2_5'), ('pm1_0','pm10'), ('pm2_5','pm10')]

@router.post("/", response_model=ParticleDataRead)
def add_particle(data: ParticleDataCreate, db: Session = Depends(get_db)):
    return create_particle(db, data)

@router.get("/statistics/{filter_type}")
def particle_stats(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_particle(db, start, end)
    stats = compute_stats(records, list(THRESHOLDS.keys()))
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def particle_full_report(filter_type: str, db: Session = Depends(get_db)):
    # Obtener datos
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_particle(db, start, end)
    if not records:
        raise HTTPException(status_code=404, detail="No hay datos de particle para este filtro")

    fields = list(THRESHOLDS.keys())
    stats = compute_stats(records, fields)

    # Muestreo equiespaciado
    sorted_recs = sorted(records, key=lambda r: r.timestamp)
    points = []
    for r in sorted_recs:
        iso_ts = r.timestamp.isoformat()
        label_ts = r.timestamp.strftime('%d/%m %H:%M')
        point = {'ts_iso': iso_ts, 'ts_label': label_ts}
        for f in fields:
            point[f] = float(getattr(r, f))
        points.append(point)

    SAMPLE_COUNTS = {'today': 8, 'last7': 7, 'month': 6}
    desired = SAMPLE_COUNTS.get(filter_type.lower(), len(points))
    sampled = sample_points(points, desired)

    # Construir listas de tiempos y series
    times_iso = [p['ts_iso'] for p in sampled]
    times_label = [p['ts_label'] for p in sampled]
    series = {f: [p[f] for p in sampled] for f in fields}

    # Riesgo individual
    risk = {f: sum(v > THRESHOLDS[f] for v in series[f]) / len(series[f])
            for f in fields if THRESHOLDS[f] is not None}

    # Riesgo conjunto
    for f1, f2 in JOINT_PAIRS:
        key = f"{f1}_AND_{f2}"
        joint_vals = []
        for i in range(len(times_iso)):
            v1, v2 = series[f1][i], series[f2][i]
            cond1 = True if THRESHOLDS[f1] is None else (v1 > THRESHOLDS[f1])
            cond2 = True if THRESHOLDS[f2] is None else (v2 > THRESHOLDS[f2])
            joint_vals.append(1 if (cond1 and cond2) else 0)
        series[key] = joint_vals
        risk[key] = sum(joint_vals) / len(joint_vals) if joint_vals else 0

    return {
        'label': label,
        'stats': stats,
        'risk': risk,
        'times_iso': times_iso,
        'times_label': times_label,
        'series': series
    }

@router.get("/pdf/{filter_type}")
def particle_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    report = particle_full_report(filter_type, db)

    # Parse ISO timestamps back to datetime for PDF plots
    times_dt = [datetime.fromisoformat(ts) for ts in report['times_iso']]

    # Reconstruir buffers de imagen para PDF
    raw_graphs = {}
    for f in THRESHOLDS.keys():
        vals = report['series'][f]
        U = THRESHOLDS[f]
        safe = sum(v <= U for v in vals) if U is not None else len(vals)
        crit = sum(v > U for v in vals) if U is not None else 0
        raw_graphs[f"donut_{f}"] = generate_donut_plot(safe, crit, f.upper())
        raw_graphs[f"line_{f}"]  = generate_line_plot(times_dt, vals, f.upper())

    for f1, f2 in JOINT_PAIRS:
        key = f"{f1}_AND_{f2}"
        vals = report['series'][key]
        count = sum(vals)
        safe = len(vals) - count
        raw_graphs[f"donut_{key}"] = generate_donut_plot(safe, count, f"{f1.upper()} & {f2.upper()}")
        raw_graphs[f"line_{key}"]  = generate_line_plot(times_dt, vals, f"{f1.upper()} & {f2.upper()}")

    pdf_bytes = build_pdf_report(
        "Particle",
        report['label'],
        report['stats'],
        report['risk'],
        raw_graphs
    )

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=particle_report_{filter_type}.pdf"}
    )
