from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from services.stats_utils import compute_stats
from services.camera_service import create_camera, get_camera
from services.report_utils import build_sensor_report
from schemas.camera import CameraDataCreate, CameraDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/camera", tags=["camera"])

@router.post("/", response_model=CameraDataRead)
def add_capture(data: CameraDataCreate, db: Session = Depends(get_db)):
    return create_camera(db, data)

@router.get("/statistics/{filter_type}")
def camera_stats(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_camera(db, start, end)
    stats = compute_stats(records, ['latency_ms'])
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def camera_full_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_camera(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos de cámara para este filtro")
    report = build_sensor_report(records, ['latency_ms'], thresholds={'latency_ms': 200.0})
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def camera_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_camera(db, start, end)
    if not records:
        raise HTTPException(404, "No hay datos para este periodo")

    fields = ['latency_ms']
    thresholds = {'latency_ms': 200.0}
    stats = compute_stats(records, fields)
    cnt = stats.get('count', 0)
    risk = {f: (sum(float(getattr(r, f)) > U for r in records)/cnt if cnt else 0)
            for f, U in thresholds.items()}

    from services.pdf_report import sample_points, generate_donut_plot, generate_line_plot, build_pdf_report
    sorted_recs = sorted(records, key=lambda r: r.timestamp)
    pts = [{'timestamp': r.timestamp, 'latency_ms': float(r.latency_ms)} for r in sorted_recs]

    SAMPLE_COUNTS = {'today': 8, 'last7': 7, 'month': 6}
    desired = SAMPLE_COUNTS.get(filter_type.lower(), len(pts))
    sampled = sample_points(pts, desired)

    graphs = {}
    times = [p['timestamp'] for p in sampled]
    vals  = [p['latency_ms'] for p in sampled]
    safe = sum(v <= thresholds['latency_ms'] for v in vals)
    crit = sum(v > thresholds['latency_ms'] for v in vals)
    graphs["donut_latency_ms"] = generate_donut_plot(safe, crit, "Latencia")
    graphs["line_latency_ms"]  = generate_line_plot(times, vals, "Latencia")

    pdf_bytes = build_pdf_report("Cámara", label, stats, risk, graphs)
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=camera_report_{filter_type}.pdf"}
    )
