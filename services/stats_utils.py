import pandas as pd

def compute_stats(records, fields):
    """
    Convierte DECIMAL a float y calcula mean, std, var, min, max, count.
    """
    df = pd.DataFrame([
        { field: float(getattr(r, field)) for field in fields }
        for r in records
    ])
    if df.empty:
        base = {
            f: {'mean': None, 'std': None, 'var': None, 'min': None, 'max': None}
            for f in fields
        }
        base['count'] = 0
        return base

    stats = {
        f: {
            'mean': float(df[f].mean()),
            'std':   float(df[f].std(ddof=1)),
            'var':   float(df[f].var(ddof=1)),
            'min':   float(df[f].min()),
            'max':   float(df[f].max()),
        }
        for f in fields
    }
    stats['count'] = int(len(df))
    return stats