import pandas as pd

def build_sensor_report(records, fields, thresholds=None):
    """
    Devuelve un dict con:
      - stats: { field: {mean, std, var, min, max}, count }
      - risk:  { field: probabilidad de > umbral }
      - timeseries: { field: [ {x: iso, y: val}, ... ] }
    """
    df = pd.DataFrame([
        {f: float(getattr(r, f)) for f in fields}
        | {'timestamp': getattr(r, 'timestamp')}
        for r in records
    ])
    if df.empty:
        return {'stats': {}, 'risk': {}, 'timeseries': {}, 'count': 0}

    stats = {
        f: {
            'mean': float(df[f].mean()),
            'std':  float(df[f].std(ddof=1)),
            'var':  float(df[f].var(ddof=1)),
            'min':  float(df[f].min()),
            'max':  float(df[f].max()),
        }
        for f in fields
    }
    stats['count'] = int(len(df))

    risk = {}
    if thresholds:
        for f, U in thresholds.items():
            risk[f] = float(df[f].gt(U).sum() / len(df))

    df = df.sort_values('timestamp')
    timeseries = {
        f: [
            {'x': ts.isoformat(), 'y': float(v)}
            for ts, v in zip(df['timestamp'], df[f])
        ]
        for f in fields
    }

    return {'stats': stats, 'risk': risk, 'timeseries': timeseries}
