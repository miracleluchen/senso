# -*- coding: utf-8 -*-
import logging
import urllib

from senso_api import settings

logger = logging.getLogger('main')

def _send(number, text):
    params = {
        'text': settings.SMS_PREFIX + text.encode('utf-8'),
        'number': number,
        'source': settings.SMS_SOURCE,
        'wait': 1,
    }
    url = 'http://%s:%s/?%s' % (settings.SMS_SERVICE_HOST,
                                settings.SMS_SERVICE_PORT,
                                urllib.urlencode(params))
    if settings.SENT_SMS:
        serialized_data = urllib.urlopen(url).read()
        logger.info(u"sms:%s %s %s" % (number, text, serialized_data))
    else:
        logger.info(u"sms:%s %s" % (number, text))


def send_sms_alert(number, sensor, channel, min_value, max_value, value):
    compare = ''
    if value > max_value:
        compare = 'Above'
    elif value < min_value:
        compare = 'Below'
    text = 'Alert: %s in %s is %s the threshold (Threshold: %s to %s, Current: %s).' % (sensor, channel, compare, min_value, max_value, value)
    _send(number, text)
