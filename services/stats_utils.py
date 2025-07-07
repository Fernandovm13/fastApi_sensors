import pandas as pd

def compute_stats(records, fields):
    df = pd.DataFrame([r.dict() for r in records])
    if df.empty:
        return {f: {'mean': None, 'min': None, 'max': None} for f in fields} | {'count': 0}

    stats = {f: {
        'mean': df[f].mean(),
        'min': df[f].min(),
        'max': df[f].max()
    } for f in fields}
    stats['count'] = len(df)
    return stats