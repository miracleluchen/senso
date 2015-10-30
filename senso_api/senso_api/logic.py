from django.utils.timezone import localtime

DATE_FORMAT = '%H:%M%p %d %b %Y'

def format_date(dt):
    if dt:
        return localtime(dt).strftime(DATE_FORMAT)
    return None
