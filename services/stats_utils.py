import pandas as pd

def compute_stats(records, fields):
    """
    Convierte a float cada valor Decimal antes de calcular mean/min/max.
    """
    # Convertimos DECIMAL a float para evitar errores de dtype
    df = pd.DataFrame([
        { field: float(getattr(r, field)) for field in fields }
        for r in records
    ])
    if df.empty:
        base = {f: {'mean': None, 'min': None, 'max': None} for f in fields}
        base['count'] = 0
        return base

    stats = {
        f: {
            'mean': float(df[f].mean()),
            'min':   float(df[f].min()),
            'max':   float(df[f].max())
        }
        for f in fields
    }
    stats['count'] = len(df)
    return stats
