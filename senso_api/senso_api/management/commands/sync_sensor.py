# -*- coding: utf-8 -*-

import datetime
import decimal
import logging
import random
import time

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.db.utils import OperationalError

from senso_api import api_helpers, models, settings

logger = logging.getLogger("sync")

URL = 'http://10.2.64.115/update/?key=%s&field1=%s'

class Command(BaseCommand):

    def handle(self, *args, **options):

        while True:
            # self.sync_sensor()
            self.update_feeds()
            time.sleep(settings.UPDATE_FREQUENCY)

    def update_feeds(self):
        for channel in models.Channel.objects.using("slave").all():
            if channel.channel_id == 63235:
                continue
            temp = random.uniform(24,27)
            temp = "%.1f" % temp
            logger.info("update temperature for channel %s, value %s", channel.name, temp)
            requests.get(URL % (channel.channel_id, temp))

    def sync_sensor(self):
        sensor_dict = {}
        for sensor in models.Sensor.objects.using("slave").all():
            sensor_dict[sensor.name] = sensor.id

        for channel in models.Channel.objects.using("slave").all():
            logger.info("------------------------")
            feed_data = api_helpers.get_data_feeds(channel.channel_id, channel.api_read_key, results=1, latest=True)
            logger.info("sync channel %s, data: %s", channel.name, feed_data)
            field_dict = {}
            if 'channel' in feed_data:
                for key, value in feed_data['channel'].iteritems():
                    if key.startswith("field"):
                        field_dict[key] = value

            if 'feeds' in feed_data and len(feed_data['feeds']) > 0:
                feed = feed_data['feeds'][0]
                create_at = feed['created_at']
                entry_id = feed['entry_id']
                for key, value in feed.iteritems():
                    if key in field_dict:
                        sensor_name = field_dict[key]
                        try:
                            models.HistoryFeeds.objects.create(
                                channel = channel,
                                sensor_id = sensor_dict[sensor_name],
                                value = value,
                                create_time = create_at,
                                last_entry_id = entry_id
                            )
                            logger.info("create history data: %s, %s, %s, %s", channel.name, sensor_dict[sensor_name], value, create_at)
                        except Exception as e:
                            logger.info("fetch data failed, %s, %s, %s, %s", channel.name, sensor_dict[sensor_name], value, create_at)
                            continue

                        if not value:
                            continue

                        value = decimal.Decimal(value)
                        currents = models.AlertSetting.objects.filter(
                            channel = channel,
                            sensor_id = sensor_dict[sensor_name]
                        )
                        if not currents.exists():
                            continue

                        current = currents[0]

                        if value > current.max_value or value < current.min_value:
                            currents.update(value = value, update_time = create_at, abnormal = F("abnormal") + 1)
                        else:
                            try:
                                currents.update(value = value, update_time = create_at, abnormal = F("abnormal") - 1)
                            except OperationalError:
                                currents.update(value = value, update_time = create_at, abnormal = 0)

            else:
                logger.info("no feed data found!")

            logger.info("======================")

