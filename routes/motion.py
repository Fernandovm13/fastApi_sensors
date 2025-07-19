from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from services.stats_utils import compute_stats
from services.motion_service import create_motion, get_motion
from services.pdf_report import (
    build_pdf_report,
    generate_donut_plot,
    generate_line_plot,
    sample_points
)
from schemas.motion import MotionDataCreate, MotionDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/motion", tags=["motion"])

@router.post("/", response_model=MotionDataRead)
def add_motion(data: MotionDataCreate, db: Session = Depends(get_db)):
    return create_motion(db, data)

@router.get("/all", response_model=list[MotionDataRead])
def all_motion(db: Session = Depends(get_db)):
    return get_motion(db, datetime.min, datetime.max)

@router.get("/statistics/{filter_type}")
def motion_stats(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_motion(db, start, end)
    stats = compute_stats(records, ['intensity'])
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def motion_full_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_motion(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos de motion para este filtro")
    from services.report_utils import build_sensor_report
    report = build_sensor_report(records, ['intensity'], thresholds=None)
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def motion_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    # 1) Periodo
    start, end, label = get_period_bounds_and_label(filter_type)
    # 2) Registros crudos
    records = get_motion(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos para este periodo")

    # 3) Stats (sin umbral → todo seguro)
    fields = ['intensity']
    stats = compute_stats(records, fields)
    risk = {}  # no hay umbrales para motion

    # 4) Ordenar y muestrear
    sorted_recs = sorted(records, key=lambda r: r.timestamp)
    pts = [
        {'timestamp': r.timestamp, 'intensity': float(r.intensity)}
        for r in sorted_recs
    ]
    SAMPLE_COUNTS = {'today':8, 'last7':7, 'month':6}
    desired = SAMPLE_COUNTS.get(filter_type, len(pts))
    sampled = sample_points(pts, desired)

    # 5) Gráficas
    graphs = {}
    times = [p['timestamp'] for p in sampled]
    vals  = [p['intensity'] for p in sampled]
    # donut: todos seguros
    graphs["donut_intensity"] = generate_donut_plot(len(vals), 0, "Intensidad")
    graphs["line_intensity"]  = generate_line_plot(times, vals, "Intensidad")

    # 6) PDF
    pdf_bytes = build_pdf_report("Motion", label, stats, risk, graphs)
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=motion_report_{filter_type}.pdf"}
    )
