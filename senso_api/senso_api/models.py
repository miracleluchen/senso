from django.db import models
from senso_api import settings

class Channel(models.Model):
    CATEGORY_OFFICE = 1
    CATEGORY_HOME = 2
    CATEGORY_CHOICES = (
        (CATEGORY_OFFICE, 'Office'),
        (CATEGORY_HOME, 'Home'),
    )
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100)
    category = models.IntegerField(choices=CATEGORY_CHOICES, default=CATEGORY_OFFICE)
    latitude = models.DecimalField(max_digits=10, decimal_places=5)
    longitude = models.DecimalField(max_digits=10, decimal_places=5)
    channel_id = models.IntegerField(unique=True)
    api_read_key = models.CharField(max_length=50)
    api_write_key = models.CharField(max_length=50)
    image_url = models.CharField(max_length=50)

    class Meta:
        db_table = 'channel_tab'


class Sensor(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'sensor_tab'

class AlertSetting(models.Model):
    channel = models.ForeignKey(Channel)
    sensor = models.ForeignKey(Sensor)
    min_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.TimeField()
    valid_to = models.TimeField()
    abnormal = models.PositiveIntegerField(default=0)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    update_time = models.DateTimeField()

    class Meta:
        db_table = 'config_tab'


class HistoryFeeds(models.Model):
    channel = models.ForeignKey(Channel)
    sensor = models.ForeignKey(Sensor)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'data_history_tab'





