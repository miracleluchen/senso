from django.utils.timezone import localtime
import uuid
DATE_FORMAT = '%H:%M%p %d %b %Y'
TIME_FORMAT = '%H:%M:%S %Z%z'

def format_date(dt):
    if dt:
        return localtime(dt).strftime(DATE_FORMAT)
    return None


def format_time(dt):
    if dt:
        time_str = dt.strftime('%H:%M:%S')
        date_str = "Thu Jan 01 1970 %s" % time_str
        return "%s GMT+0800 (SGT)" % date_str
    return None


def generate_key():
    return uuid.uuid4().hex
