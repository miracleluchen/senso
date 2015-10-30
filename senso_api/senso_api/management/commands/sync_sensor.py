# -*- coding: utf-8 -*-

import decimal
import logging
import time
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from senso_api import models, api_helpers
from senso_api import settings
from django.db.utils import OperationalError

logger = logging.getLogger("sync")

class Command(BaseCommand):

    def handle(self, *args, **options):

        while True:
            self.sync_sensor()
            time.sleep(settings.UPDATE_FREQUENCY)

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
                for key, value in feed.iteritems():
                    if key in field_dict:
                        sensor_name = field_dict[key]
                        models.HistoryFeeds.objects.create(
                            channel = channel,
                            sensor_id = sensor_dict[sensor_name],
                            value = value,
                            create_time = create_at
                        )
                        logger.info("create history data: %s, %s, %s, %s", channel.name, sensor_dict[sensor_name], value, create_at)

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



