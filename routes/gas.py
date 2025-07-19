from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import traceback

from services.stats_utils import compute_stats
from services.gas_service import create_gas, get_gas
from services.pdf_report import (
    build_pdf_report,
    generate_donut_plot,
    generate_line_plot,
    sample_points
)
from schemas.gas import GasDataCreate, GasDataRead
from db.connection import get_db
from utils.time_utils import get_period_bounds_and_label

router = APIRouter(prefix="/gas", tags=["gas"])

@router.post("/", response_model=GasDataRead)
def add_gas(data: GasDataCreate, db: Session = Depends(get_db)):
    return create_gas(db, data)

@router.get("/all", response_model=list[GasDataRead])
def all_gas(db: Session = Depends(get_db)):
    return get_gas(db, datetime.min, datetime.max)

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
    from services.report_utils import build_sensor_report
    report = build_sensor_report(records, ['lpg','co','smoke'], {'lpg':800,'co':50,'smoke':300})
    return {'label': label, **report}

@router.get("/pdf/{filter_type}")
def gas_pdf_report(filter_type: str, db: Session = Depends(get_db)):
    try:
        # 1) Rango y etiqueta
        start, end, label = get_period_bounds_and_label(filter_type)

        # 2) Registros
        records = get_gas(db, start, end)
        if not records:
            raise HTTPException(404, "No hay datos para este periodo")

        # 3) Estadísticas + riesgo
        fields     = ['lpg','co','smoke']
        thresholds = {'lpg':800.0,'co':50.0,'smoke':300.0}
        stats = compute_stats(records, fields)
        cnt   = stats.get('count', 0)
        risk  = {
            f: (sum(float(getattr(r, f))>U for r in records)/cnt if cnt else 0)
            for f, U in thresholds.items()
        }

        # 4) Ordenar y muestrear
        sorted_recs = sorted(records, key=lambda r: r.timestamp)
        pts = [
            {'timestamp': r.timestamp, **{f: float(getattr(r,f)) for f in fields}}
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
            safe = sum(v<=thresholds[f] for v in vals)
            crit = sum(v> thresholds[f] for v in vals)
            graphs[f"donut_{f}"] = generate_donut_plot(safe, crit, f.upper())
            graphs[f"line_{f}"]  = generate_line_plot(times, vals, f.upper())

        # 6) Construir y devolver PDF
        pdf_bytes = build_pdf_report("Gas", label, stats, risk, graphs)
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=gas_report_{filter_type}.pdf"}
        )

    except HTTPException:
        # Dejar pasar 404
        raise
    except Exception as e:
        # Loguea el stacktrace en la consola
        traceback.print_exc()
        # Devuelve un 500 con detalle para que puedas ver el mensaje en el front
        raise HTTPException(500, f"Error generando PDF: {e}")
