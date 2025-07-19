import pandas as pd

def sample_points(points: list[dict], count: int) -> list[dict]:
    n = len(points)
    if n <= count:
        return points
    step = n / count
    return [points[int(i * step)] for i in range(count)]


def build_sensor_report(records, fields, thresholds=None):
    df = pd.DataFrame([
        {f: getattr(r, f) for f in fields} | {'timestamp': getattr(r, 'timestamp')}
        for r in records
    ])
    if df.empty:
        return {'stats': {}, 'risk': {}, 'timeseries': {}, 'count': 0}
    stats = {f: {'mean': float(df[f].mean()), 'min': float(df[f].min()), 'max': float(df[f].max())}
             for f in fields}
    stats['count'] = int(len(df))
    risk = {}
    if thresholds:
        for f, U in thresholds.items():
            above = df[f].gt(U).sum()
            risk[f] = float(above / len(df))
    df = df.sort_values('timestamp')
    timeseries = {f: [{'x': ts.isoformat(), 'y': float(v)}
                      for ts, v in zip(df['timestamp'], df[f])]
                  for f in fields}
    return {'stats': stats, 'risk': risk, 'timeseries': timeseries}
