from datetime import datetime, timedelta, time

def get_period_bounds_and_label(filter_type: str):
    today = datetime.today().date()
    if filter_type == 'today':
        start = datetime.combine(today, time.min)
        end   = datetime.combine(today, time.max)
        label = today.strftime('%d/%m/%Y')
    elif filter_type == 'last7':
        start_date = today - timedelta(days=6)
        start = datetime.combine(start_date, time.min)
        end   = datetime.combine(today, time.max)
        label = f"{start_date.strftime('%d/%m/%Y')} – {today.strftime('%d/%m/%Y')}"
    elif filter_type == 'month':
        start_date = today.replace(day=1)
        start = datetime.combine(start_date, time.min)
        end   = datetime.combine(today, time.max)
        label = start_date.strftime('%B %Y')
    else:
        raise ValueError(f"Invalid filter type: {filter_type}")
    return start, end, label
