import collections
import datetime
import decimal
import exceptions
import json
import logging
import traceback
from collections import OrderedDict
from decimal import Decimal, getcontext

from django.db import IntegrityError, transaction
from django.db.models import F
from django.db.utils import OperationalError
from django.shortcuts import HttpResponse
from django.utils.timezone import localtime, now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

import sms
import view_helpers
from senso_api import logic, models, settings

logger = logging.getLogger("main")

class ApiView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ApiView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        reply = view_helpers.ApiJsonReply()
        reply.set_resp(exceptions.ApiHttpMethodNotAllowed())
        return HttpResponse(
            unicode(reply),
            content_type='application/json')

    def post(self, request, *args, **kwargs):
        name = self.__class__.__name__
        logger.info('post begin: %s', name)

        self.api_reply = self.reply_class()

        try:
            api_request = self.request_class(request)
            self.api_reply = self.post_valid(api_request)
        except exceptions.ApiError as e:
            self.api_reply.set_resp(e)
            logger.error(traceback.format_exc())
        except:
            debug = traceback.format_exc()
            logger.error(debug)
            self.api_reply.set_resp(exceptions.ApiUnexpectedError(debug='internal error'))

        logger.info('post end: %s', name)
        return HttpResponse(
            unicode(self.api_reply),
            content_type='application/json')

    def check_client_ip(request):
        return True

class FetchChannelFeedsView(ApiView):
    request_class = view_helpers.FetchFeedRequest
    reply_class = view_helpers.FetchFeedReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()
        channel = api_request.cleaned_data['channel']
        result = api_request.cleaned_data['result']
        start = api_request.cleaned_data['start']
        end = api_request.cleaned_data['end']
        days = api_request.cleaned_data['days']

        ret_data = {'channel':{}, 'feeds':{}}
        try:
            channel = models.Channel.objects.using("slave").get(channel_id=channel)

            # process channel data
            sensor_setting = {}
            sensor_setting['name'] = channel.name
            sensor_setting['category'] = channel.category
            for sensor_data in models.AlertSetting.objects.using("slave").filter(channel=channel):
                sensor_setting[sensor_data.sensor.name] = str((sensor_data.value)) if sensor_data.value is not None else None
                sensor_setting['alert'] = sensor_data.abnormal >= settings.ALERT_LIMIT
                if sensor_data.sensor.id == 1:
                    sensor_setting['valid_from'] = logic.format_time(sensor_data.valid_from)
                    sensor_setting['valid_to'] = logic.format_time(sensor_data.valid_to)
                    sensor_setting['min_value'] = int(sensor_data.min_value)
                    sensor_setting['max_value'] = int(sensor_data.max_value)
                sensor_setting['updated_at'] = logic.format_date(sensor_data.update_time)
            ret_data['channel'].update(sensor_setting)

            # process feeds
            getcontext().prec = 3
            data_feeds = collections.defaultdict(lambda:0)
            datetime_filter = localtime(now()) - datetime.timedelta(days=1)
            for data in models.HistoryFeeds.objects.using("slave").filter(channel=channel, sensor_id=1, create_time__gt=datetime_filter):
                key = localtime(data.create_time).strftime("%Y%m%d%H")
                if data_feeds[key] == 0:
                    data_feeds[key] = data.value
                else:
                    data_feeds[key] = (data_feeds[key] + data.value) / 2

            ordered = OrderedDict(sorted(data_feeds.items(), key=lambda x:int(x[0]), reverse=True))

            horizen = []
            dataset = []
            for key, value in ordered.iteritems():
                horizen.insert(0, key[-2:]+":00")
                dataset.insert(0, str(value))
                if len(horizen) == 10:
                    break
            ret_data['feeds']['labels'] = horizen
            ret_data['feeds']['data'] = [dataset]

            api_reply.set_field("data", ret_data)
            return api_reply

        except models.Channel.DoesNotExist:
            raise exceptions.ApiChannelNotFound()

class ChannelListView(ApiView):
    request_class = view_helpers.EmptyRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()

        channels = []

        channel_setting_dict = collections.defaultdict(list)
        for alert in models.AlertSetting.objects.using("slave").all():
            setting_dict = collections.defaultdict(dict)
            setting_dict[alert.sensor.name]["max"] = str(alert.max_value)
            setting_dict[alert.sensor.name]["min"] = str((alert.min_value))
            setting_dict[alert.sensor.name]["from"] = logic.format_time(alert.valid_from)
            setting_dict[alert.sensor.name]["to"] = logic.format_time(alert.valid_to)
            setting_dict[alert.sensor.name]["value"] = str((alert.value))
            setting_dict[alert.sensor.name]["update_time"] = logic.format_date(alert.update_time)
            setting_dict[alert.sensor.name]["alert"] = alert.abnormal >= settings.ALERT_LIMIT
            # if setting_dict[alert.sensor.name]["alert"] and  alert.sensor_id == 1:
                # sms.send_sms_alert(settings.ALERT_NUMBER,
                                   # alert.sensor.name,
                                   # alert.channel.name,
                                   # alert.min_value,
                                   # alert.max_value,
                                   # alert.value)
            channel_setting_dict[alert.channel.id].append(setting_dict)

        for channel in models.Channel.objects.using("slave").all():
            channel_dict = {}
            channel_dict['name'] = channel.name
            channel_dict['api_key'] = channel.api_write_key
            channel_dict['category'] = channel.get_category_display()
            channel_dict['id'] = channel.channel_id
            channel_dict['status'] = channel_setting_dict[channel.id]

            channels.append(channel_dict)

        api_reply.set_field("data", channels)
        return api_reply

class ChannelCreateView(ApiView):
    request_class = view_helpers.ChannelRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()
        cleaned_data = api_request.cleaned_data

        name = cleaned_data['name']
        max_temp = cleaned_data['max_temp']
        min_temp = cleaned_data['min_temp']
        valid_from = cleaned_data['valid_from']
        valid_to = cleaned_data['valid_to']
        category = cleaned_data['category']
        channel = cleaned_data['channel']

        print api_request.cleaned_data
        try:
            cha = models.Channel.objects.get(channel_id=channel)
            try:
                with transaction.atomic():
                    models.Channel.objects.filter(channel_id=channel).update(
                        name = name,
                        category = category
                    )
                    models.AlertSetting.objects.filter(channel=cha, sensor_id=1).update(
                        min_value = min_temp,
                        max_value = max_temp,
                        valid_from = valid_from,
                        valid_to = valid_to
                    )
            except Exception as e:
                logger.error("update channel failed, Exception %s", e)
                raise exceptions.ApiUpdateChannelError("Database Error")

        except models.Channel.DoesNotExist:
            api_read_key = logic.generate_key()
            sensors = [sensor.id for sensor in models.Sensor.objects.all()]
            try:
                with transaction.atomic():
                    cha = models.Channel.objects.create(
                        name = name,
                        description = '',
                        category = category,
                        channel_id = channel,
                        api_write_key = '',
                        api_read_key = api_read_key
                    )

                    obj_list = []
                    for sensor in sensors[::-1]:
                        if sensor == 1:
                            max_value = max_temp
                            min_value = min_temp
                            value = 25
                        elif sensor == 2:
                            max_value = 80
                            min_value = 30
                            value = 50
                        elif sensor == 3:
                            max_value = 100
                            min_value = 0
                            value = 76
                        obj = models.AlertSetting(
                            channel = cha,
                            sensor_id = sensor,
                            min_value = min_value,
                            max_value = max_value,
                            valid_from = valid_from,
                            valid_to = valid_to,
                            value = value,
                            update_time = localtime(now())
                        )
                        obj_list.append(obj)
                    print obj_list
                    models.AlertSetting.objects.bulk_create(obj_list)
            except IntegrityError:
                logger.error("duplicate channel name, %s", name)
                raise exceptions.ApiCreateChannelError("Duplicated Name")
            except Exception as e:
                logger.error("create channel failed, exception: %s", e)
                raise exceptions.ApiCreateChannelError("Database Error")

        ret_data = {
            'name': name,
            'min_temp': str(min_temp),
            'max_temp': str(max_temp),
            'valid_from': logic.format_time(valid_from),
            'valid_to': logic.format_time(valid_to),
            'category': category
        }

        api_reply.set_field("data", ret_data)
        return api_reply


class ChannelDeleteView(ApiView):
    request_class = view_helpers.ChannelDeleteRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        channel = api_request.cleaned_data['channel']

        api_reply = self.reply_class()

        try:
            with transaction.atomic():
                models.AlertSetting.objects.filter(channel_id=channel).delete()
                models.HistoryFeeds.objects.filter(channel_id=channel).delete()
                models.Channel.objects.filter(channel_id=channel).delete()

        except Exception as e:
            logger.error("delete channel failed, exception: %s", e)
            raise exceptions.ApiDeleteChannelError("Database Error")

        return api_reply

def update_feed(request):
    channel_id = request.GET['key']
    temperature =  request.GET['field1']
    humidity =  request.GET.get('field2', None)
    haze =  request.GET.get('field3', None)

    value = decimal.Decimal(temperature)
    try:
        channel = models.Channel.objects.get(channel_id=channel_id)
        obj = models.HistoryFeeds.objects.create(channel=channel, sensor_id=1, value=temperature)
        currents = models.AlertSetting.objects.filter(channel=channel, sensor_id=1)
        if currents.exists():
            current = currents[0]
            create_at = localtime(now())
            if value > current.max_value or value < current.min_value:
                if current.abnormal == 0:
                    sms.send_sms_alert(settings.ALERT_NUMBER,
                                   current.sensor.name,
                                   current.channel.name,
                                   current.min_value,
                                   current.max_value,
                                   value)

                currents.update(value = value,
                                update_time = create_at,
                                abnormal=F("abnormal") + 1)
            else:
                try:
                    currents.update(value = value,
                                    update_time = create_at,
                                    abnormal = F("abnormal") - 1)
                except OperationalError:
                    currents.update(value = value,
                                    update_time = create_at,
                                    abnormal = 0)

        return HttpResponse(obj.id)
    except models.Channel.DoesNotExist:
        return HttpResponse("0")
