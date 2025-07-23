from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from services.stats_utils import compute_stats
from services.motion_service import create_motion, get_motion
from services.report_utils import build_sensor_report
from schemas.motion import MotionDataCreate, MotionDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/motion", tags=["motion"])

@router.post("/", response_model=MotionDataRead)
def add_motion(data: MotionDataCreate, db: Session = Depends(get_db)):
    return create_motion(db, data)

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
    report = build_sensor_report(records, ['intensity'], thresholds=None)
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def motion_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_motion(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos para este periodo")

    fields = ['intensity']
    stats = compute_stats(records, fields)
    risk = {}

    from services.pdf_report import sample_points, generate_donut_plot, generate_line_plot, build_pdf_report
    sorted_recs = sorted(records, key=lambda r: r.timestamp)
    pts = [{'timestamp': r.timestamp, 'intensity': float(r.intensity)} for r in sorted_recs]

    SAMPLE_COUNTS = {'today': 8, 'last7': 7, 'month': 6}
    desired = SAMPLE_COUNTS.get(filter_type.lower(), len(pts))
    sampled = sample_points(pts, desired)

    times = [p['timestamp'] for p in sampled]
    vals  = [p['intensity'] for p in sampled]
    graphs = {
        "donut_intensity": generate_donut_plot(len(vals), 0, "Intensidad"),
        "line_intensity": generate_line_plot(times, vals, "Intensidad")
    }

    pdf_bytes = build_pdf_report("Motion", label, stats, risk, graphs)
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=motion_report_{filter_type}.pdf"}
    )
