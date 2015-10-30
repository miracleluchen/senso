import exceptions
import json
import logging

import requests

from senso_api import logic, settings, models

logger = logging.getLogger("main")

API_KEY = 'JFJAANQN3HVBXEUB'
URL_DOMAIN = 'https://api.thingspeak.com/'

# sensor data api
URL_FETCH_FEED = 'channels/%s/feeds.json?key=%s'

# channel api
URL_CHANNEL_ADD = 'channels.json'
URL_CHANNEL_UPDATE = ''
URL_CHANNEL_DELETE = 'channels/%s.json?key=%s'
URL_CHANNEL_LIST = 'channels.json?api_key=%s' % API_KEY


def http_call(url, request_data=None, host=URL_DOMAIN, timeout=60, http_method="post"):
    request_url = host + url

    logger.info("Http request: %s, %s, data: %s", request_url, http_method, request_data)

    try:
        if http_method == "get":
            resp = requests.get(request_url, timeout=timeout)
        elif http_method == "delete":
            resp = requests.delete(request_url)
        elif http_method == 'put':
            resp = requests.put(request_url)
        else:
            resp = requests.post(request_url, data=request_data, timeout=timeout)

        logger.info("Http request reply: %s", resp.text)

        return resp.json()

    except Exception as e:
        logger.error("Http request fail: %s, %s, data: %s, error:%s", request_url, http_method,
                     request_data, e)
        raise exceptions.ApiUnexpectedError("Http failed.")

def get_data_feeds(channel, api_key, start=None, end=None, days=None, results=None, latest=False):
    url = URL_FETCH_FEED % (channel, api_key)

    optional = '&timezone=Asia/Singapore'
    if not latest:
        optional = '&median=10'
    if start is not None:
        optional += '&start=' + start.strftime("%Y%m%d %H:%M:%S")
    if end is not None:
        optional += '&end=' + end.strftime("%Y%m%d %H:%M:%S")
    if days is not None:
        optional += '&days=' + str(days)
    if results is not None:
        optional += '&results=' + str(results)

    url += optional
    return http_call(url, http_method="get")

def get_channel_list():
    url = URL_CHANNEL_LIST
    channels = http_call(url, http_method="get")
    # sync database
    for channel in channels:
        channel.pop('api_keys')
        channel.pop('username')
        channel.pop('tags')

    return channels

def create_channel(name):
    url = URL_CHANNEL_ADD
    request_data = {
        "api_key": API_KEY,
        "name": name,
    }
    for sensor in models.Sensor.objects.using('slave').all():
        request_data.update({"field%s" % sensor.id: sensor.name})

    channel = http_call(url, request_data)
    return channel

def update_channel_info():
    pass

def delete_channel(channel):
    url = URL_CHANNEL_DELETE % (channel, API_KEY)
    res = http_call(url, http_method="delete")
    return res

def add_channel_sensor():
    pass

def update_channel_sensor():
    pass
