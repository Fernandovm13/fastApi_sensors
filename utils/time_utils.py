import locale
from datetime import datetime, timedelta, time

locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')

def get_period_bounds_and_label(filter_type: str):
    """
    Ahora acepta tanto 'today'/'hoy', 'last7'/'ultimos7' y 'month'/'mes'.
    Devuelve (start_datetime, end_datetime, etiqueta_en_español).
    """
    today = datetime.today().date()

    ft = filter_type.lower()
    if ft in ('today', 'hoy'):
        start = datetime.combine(today, time.min)
        end   = datetime.combine(today, time.max)
        label = today.strftime('%d/%m/%Y')
    elif ft in ('last7', 'ultimos7', 'ultimos 7', 'últimos7', 'últimos 7'):
        start_date = today - timedelta(days=6)
        start = datetime.combine(start_date, time.min)
        end   = datetime.combine(today, time.max)
        label = f"{start_date.strftime('%d/%m/%Y')} – {today.strftime('%d/%m/%Y')}"
    elif ft in ('month', 'mes'):
        start_date = today.replace(day=1)
        start = datetime.combine(start_date, time.min)
        end   = datetime.combine(today, time.max)
        label = start_date.strftime('%B %Y').capitalize()
    else:
        raise ValueError(f"Tipo de filtro inválido: {filter_type!r}")
    return start, end, label