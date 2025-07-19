from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from services.stats_utils import compute_stats
from services.particle_service import create_particle, get_particle
from services.pdf_report import (
    build_pdf_report,
    generate_donut_plot,
    generate_line_plot,
    sample_points
)
from schemas.particle import ParticleDataCreate, ParticleDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/particle", tags=["particle"])

@router.post("/", response_model=ParticleDataRead)
def add_particle(data: ParticleDataCreate, db: Session = Depends(get_db)):
    return create_particle(db, data)

@router.get("/all", response_model=list[ParticleDataRead])
def all_particles(db: Session = Depends(get_db)):
    return get_particle(db, datetime.min, datetime.max)

@router.get("/statistics/{filter_type}")
def particle_stats(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_particle(db, start, end)
    stats = compute_stats(records, ['pm1_0','pm2_5','pm10'])
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def particle_full_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_particle(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos de particle para este filtro")
    from services.report_utils import build_sensor_report
    report = build_sensor_report(
        records,
        ['pm1_0','pm2_5','pm10'],
        thresholds={'pm2_5':35.0}
    )
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def particle_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    # 1) Periodo
    start, end, label = get_period_bounds_and_label(filter_type)
    # 2) Datos
    records = get_particle(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos para este periodo")

    # 3) Stats + riesgo
    fields     = ['pm1_0','pm2_5','pm10']
    thresholds = {'pm2_5':35.0}
    stats = compute_stats(records, fields)
    cnt   = stats.get('count', 0)
    risk  = {
        f: (sum(float(getattr(r, f))>U for r in records)/cnt if cnt else 0)
        for f,U in thresholds.items()
    }

    # 4) Ordenar y muestrear
    sorted_recs = sorted(records, key=lambda r: r.timestamp)
    pts = [
        {'timestamp': r.timestamp,
         'pm1_0': float(r.pm1_0),
         'pm2_5': float(r.pm2_5),
         'pm10':  float(r.pm10)}
        for r in sorted_recs
    ]
    SAMPLE_COUNTS = {'today':8, 'last7':7, 'month':6}
    desired = SAMPLE_COUNTS.get(filter_type, len(pts))
    sampled = sample_points(pts, desired)

    # 5) Generar gráficas
    graphs = {}
    times = [p['timestamp'] for p in sampled]
    for f in fields:
        vals = [p[f] for p in sampled]
        safe = sum(v<=thresholds.get(f,float('inf')) for v in vals)
        crit = sum(v> thresholds.get(f,float('inf')) for v in vals)
        graphs[f"donut_{f}"] = generate_donut_plot(safe, crit, f.upper())
        graphs[f"line_{f}"]  = generate_line_plot(times, vals, f.upper())

    # 6) PDF
    pdf_bytes = build_pdf_report("Particle", label, stats, risk, graphs)
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=particle_report_{filter_type}.pdf"}
    )
